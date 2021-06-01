# -*- coding: utf-8 -*-
"""

    ppmeasurements.traceroute
    ~~~~~~~~~~~~~~

    This module uses the the revtr server to perform traceroute measurements,
    then calls ping measurement and geolocation sources module
    (to get geosource predictions) for all the hops in a traceroutes.

    :author: Ceridwen Driskill, Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import _strptime
import requests
import json
import time
import os
import datetime
import configs.traceroutes
from pputils import ip_int_to_string
from ppmeasurements.util import is_private_ip
import ppmeasurements.util as util
import random
import socket
import traceback
from ppmeasurements import ping
import csv
from multiprocessing import Manager, Pool, Process
import socket
import configs.pings
import requests
from threading import Thread
import geosources.ipinfo as ip_info
import geosources.geolocation as geo_sources_module

# other imports
###remove-me-later-muz###import ormsettings as DJANGO_SETTINGS   # don't remove
###remove-me-later-muz###from django.db import models

import ppmeasurements.util as util_traceroutes

import pputils
import configs.intersection
import ppnamespace

import configs.system
import geosources.geolocation
import geosources
import geosources.ddec
import netaddr as ipaddress
from intervaltree import Interval, IntervalTree
import signal
import sys
from geosources import whois

"""
# function: get_traceroutes([(source_ip, dest_ip)...], revtr=?)
# Input: list of source, destination ip pairs, revtr=True to perform reverse traceroutes
# Output: list of dictionaries {'src': source ip, 'dst': dest ip, 'src_name': source hostname (if it could be found),
# 'dst_name': dest hostname (if it could be found), 'completed': true or false, 'revtr': true or false,
# 'hops': [{'hop': hop index, 'ip': hop ip, 'hostname': ip hostname (if it could be found)]}

To actually use this code, just use from perform_traceroute import get_traceroutes.
Output files are stored as /traceroutes/fwdtr or revtr/source hostname/dest hostname/YYYYMMDDhhmmss.json
Raw json is also stored as YYYYMMDDhhmmss_raw.json
"""


REVTR_KEY = {'Revtr-Key': configs.traceroutes.KEY}
TRACE_KEY = {'Api-Key': configs.traceroutes.KEY}

def get_revtr_vps():
    response = requests.get(configs.traceroutes.SOURCES_URL, headers=REVTR_KEY)
    if response.status_code != 200:
        return []
    return [str(addr['ip']) for addr in response.json()['srcs']]


def get_geolocation_sources_info(ip_hostname_tuple):
    ip_str,x_hostname=ip_hostname_tuple
    # do pings
    t1 = Thread(target=(ping.get_pings_measurements), args=(ip_str,))
    t1.start()
    # do geosources
    try:
        if not whois.in_cache(ip_str):
            whois.get_whois_and_save(ip_str)
    except:
        traceback.print_exc()
    try:
        if not geosources.geolocation.in_cache(ip_str):
            geosources.geolocation.get_inaccurate_locations(ip_str)
    except:
        traceback.print_exc()
    if not x_hostname:
        t1.join()    
        return
    try: # slightly untested.
        if not geosources.ddec.in_cache(x_hostname):
            geosources.ddec.request_ddec_country(x_hostname)
    except:
        traceback.print_exc()
    # join pings thread
    t1.join()


def post_processing_geosources(traceroutes):
    ip_hostname_tuple_list = []
    for traceroute in traceroutes:
        if 'hops' in traceroute:
            for hop in traceroute['hops']:
                ip = ''
                hostname = ''                
                if 'hostname' in hop:
                    hostname = hop['hostname']   
                if 'ip' in hop:
                    ip = hop['ip']   
                    ip_hostname_tuple_list.append((ip, hostname))
    # open processes and get other data.
    process_pool = Pool(configs.traceroutes.MAX_URLS_PER_COUNTRY)
    ip_hostname_tuple_input = tuple(ip_hostname_tuple_list)
    process_pool.map(get_geolocation_sources_info,ip_hostname_tuple_input)
    try:
        process_pool.close()
        process_pool.join()
        del process_pool
    except:
        pass


def get_traceroute_to_destination(dest,cntry):
    #dest,cntry = data_tuple
    vps = ping.get_fwd_nodes()
    src_dst_pairs = [(src,dest) for src in vps]
    get_traceroutes(src_dst_pairs, False, cntry)
    revtr_vps = get_revtr_vps()
    src_dst_pairs = [(src,dest) for src in revtr_vps]
    get_traceroutes(src_dst_pairs, True, cntry)
    get_traceroutes(src_dst_pairs, False, cntry)


def get_traceroute_to_destination_country(cntry):
    requests.packages.urllib3.disable_warnings()
    #process_pool = Pool(configs.traceroutes.MAX_URLS_PER_COUNTRY)
    dst_addresses = set()
    addresses = util.get_destination_node_list(cntry,configs.traceroutes.MAX_URLS_PER_COUNTRY**3)
    counter = 0
    for addr in addresses:
        if len(dst_addresses) >= configs.traceroutes.MAX_URLS_PER_COUNTRY:
            break
        try:
            addr = socket.gethostbyname(addr)
            #print addr
            mm_dbip = geo_sources_module.get_geosources_maxmind_db_ip(addr)
            mm_dbip = pputils.get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND, mm_dbip)
            #print addr_info['country']
            if mm_dbip.lower() != cntry.lower():
                print "IP appears to be in a different country. Expected:",cntry, "Found:",mm_dbip
                continue
            dst_addresses.add((addr,cntry))
        except:
            #traceback.print_exc()  
            continue
        counter += 1
    dst_addresses_tuple=tuple(dst_addresses)
    print("Starting Pool for Country: {}".format(cntry))
    print("Trace: IP addresses to ping: {}".format(len(dst_addresses_tuple)))
    print [x[0] for x in dst_addresses_tuple]    

    process_pool = []
    for dst_addresses in dst_addresses_tuple:    
        p = Process(target=get_traceroute_to_destination, args=dst_addresses)
        p.daemon = False
        process_pool.append(p)

    for process in process_pool:
        process.start()

    for process in process_pool:
        process.join()


# wrapper method for only performing a single traceroute rather than a batch
def get_traceroute(source, dest, revtr=False,dst_cntry_name=None):
    return get_traceroutes([(source, dest)], revtr)


def get_all_completed_traceroutes_all():
    requests.packages.urllib3.disable_warnings()
    get_all_completed_traceroutes(revtr=False)
    get_all_completed_traceroutes(revtr=True)


def get_all_completed_traceroutes(revtr=False):
    process_pool = []
    ignore_uri = []
    result_uri_list = load_results_uri(revtr)
    counter = 0
    for result_uri in result_uri_list:
        if result_uri in ignore_uri:
            continue
        p = Thread(target=(get_all_completed_traceroutes_for_single_uri), args=(result_uri, revtr,))
        p.daemon = False
        process_pool.append(p)
        counter += 1
        if counter >= configs.traceroutes.MAX_URLS_PER_COUNTRY:
            for process in process_pool:
                process.start()
            for process in process_pool:
                process.join()
            counter = 0
            process_pool = []
        with open('temp_ignore_list.txt','a') as f:
            f.write("'")
            f.write(result_uri)
            f.write("'")
            f.write(",")
    for process in process_pool:
        process.start()
    for process in process_pool:
        process.join()


def get_all_completed_traceroutes_for_single_uri(result_uri, revtr=False):
    print "Working on URI:",result_uri
    traceroutes = []
    routes_tag = ('revtrs' if revtr else 'traceroutes')
    tries = 0
    sleep_time_min = configs.traceroutes.SLEEP_TIME * 0.5
    while tries < 1:
        sleep_time_in_iteration = sleep_time_min + random.random() * configs.traceroutes.SLEEP_TIME
        time.sleep(sleep_time_in_iteration)
        tries += 1
        try:
            response = requests.get(result_uri, headers=(REVTR_KEY if revtr else TRACE_KEY))
            if response.status_code != 200:
                #print "Status", response.status_code, "for:", ip
                #print "Status", response.text, "for:", ip, result_uri
                continue
            #print response.json()
            #if response.json(): return
            if routes_tag in response.text:
                response_data = response.json()
                for trace in response_data[routes_tag]:
                    if revtr:
                        src = trace['src']
                        dst = trace['dst']
                    else:
                        src = ip_int_to_string(trace['src'])
                        dst = ip_int_to_string(trace['dst'])
                    mm_dbip = geo_sources_module.get_geosources_maxmind_db_ip(dst)
                    dst_cntry_name= pputils.get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND,
                                                                           mm_dbip)
                    
                    result = {}
                    result['src'] = src
                    result['dst'] = dst
                    try:
                        src_name = socket.gethostbyaddr(src)[0]
                        result['src_name'] = src_name
                    except:
                        pass
                    try:
                        dst_name = socket.gethostbyaddr(dst)[0]
                        result['dst_name'] = dst_name
                    except:
                        pass
                    complete = False
                    if revtr and 'path' in trace:
                        hops = []
                        path_len = len(trace['path'])
                        first_hop = ''

                        last_hop = ''
                        for i in range(path_len):
                            hop = trace['path'][i]
                            if 'hop' in hop:
                                if i == 0:
                                    first_hop = hop['hop']
                                if i == path_len - 1:
                                    last_hop = hop['hop']
                                hop_data = {'hop': i,
                                            'ip': hop['hop']}
                                try:
                                    hostname = socket.gethostbyaddr(ip)[0]
                                    hop_data['hostname'] = hostname
                                except:
                                    pass
                                hops.append(hop_data)
                        if first_hop == dst and last_hop == src:
                            complete = True
                        result['hops'] = hops
                    elif not revtr and 'hops' in trace:
                        hops = []
                        for hop in trace['hops']:
                            if 'addr' in hop and 'probe_ttl' in hop:
                                ip = ip_int_to_string(hop['addr'])
                                hop_data = {'hop': hop['probe_ttl'],
                                            'ip': ip_int_to_string(hop['addr'])}
                                try:
                                    hostname = socket.gethostbyaddr(ip)[0]
                                    hop_data['hostname'] = hostname
                                except:
                                    pass
                                hops.append(hop_data)
                                if ip == dst:
                                    complete = True
                        result['hops'] = hops
                    result['complete'] = complete
                    result['revtr'] = revtr
                    result['dst_cntry_name'] = dst_cntry_name
                    trace['result_url'] = result_uri
                    save_trace(src, dst, result, trace, revtr)
                    print "Saved:", src, 'to ', dst, 'in ',dst_cntry_name
                    traceroutes.append(result)
                post_processing_geosources(traceroutes)
                return traceroutes
        except:
            print "Exception while performing traceroutes"
            traceback.print_exc()
            return traceroutes
    print "Max tries reached for traceroutes"
    return traceroutes


# returns a list of dictionaries of the form {'src': source ip, 'dst': dest ip,
# 'src_name': source hostname (if it could be found), 'dst_name': dest hostname (if it could be found),
# 'completed': true or false, 'revtr': true or false,
# 'hops': [{'hop': hop index, 'ip': hop ip, 'hostname': ip hostname (if it could be found)]}
def get_traceroutes(source_dest_pairs, revtr=False,dst_cntry_name=None):
    """
    # function: get_traceroutes(, revtr=?)
# Input: ,
# Output:

    :param source_dest_pairs: list of source, destination ip pairs. [(source_ip, dest_ip)...]
    :param revtr: boolean: revtr=True to perform reverse traceroutes, else ignore.
    :param dst_cntry_name: string. The country that as destination to be performing mr
    :return:
    list of dictionaries {'src': source ip, 'dst': dest ip, 'src_name': source hostname (if it could be found),
    'dst_name': dest hostname (if it could be found), 'completed': true or false, 'revtr': true or false,
    'hops': [{'hop': hop index, 'ip': hop ip, 'hostname': ip hostname (if it could be found)]}
    """
    # suppress https warnings
    requests.packages.urllib3.disable_warnings()
    # if it's private, ignore it
    pairs = set()
    for pair in source_dest_pairs:
        if is_private_ip(pair[0]) or is_private_ip(pair[1]):
            continue
        pairs.add(pair)

    traceroutes = []
    routes_tag = ('revtrs' if revtr else 'traceroutes')
    to_perfom = []
    for pair in pairs:
        existing = get_existing_trace(pair[0], pair[1], revtr)
        if existing is None:
            to_perfom.append({'src': pair[0],
                              'dst': pair[1],
                              'staleness': configs.traceroutes.STALENESS})
        else:
            traceroutes.append(existing)

    if not to_perfom:
        return traceroutes
    request_obj = {routes_tag: to_perfom}
    #print request_obj
    response = requests.post((configs.traceroutes.REVTR_URL if revtr else configs.traceroutes.TRACE_URL),
                             headers=(REVTR_KEY if revtr else TRACE_KEY),
                             data=json.dumps(request_obj))
    if response.status_code != 200:
        print "Initial Status", response.text, "for revtr:", revtr
        print "Status", response.text 
        return traceroutes
    try:
        response_data = response.json()
    except:
        print "Initial Exception for traceroutes"
        traceback.print_exc()
        return traceroutes
    result_uri = response_data['result_uri' if revtr else 'results']

    save_results_uri(result_uri, revtr)

    tries = 0
    sleep_time_min = configs.traceroutes.SLEEP_TIME * 0.5
    while tries < configs.traceroutes.MAX_TRIES:
        sleep_time_in_iteration = sleep_time_min + random.random() * configs.traceroutes.SLEEP_TIME
        sleep_time_in_iteration *= configs.traceroutes.TIME_FACTOR_REVTR
        time.sleep(sleep_time_in_iteration)
        tries += 1
        try:
            response = requests.get(result_uri, headers=(REVTR_KEY if revtr else TRACE_KEY))
            if response.status_code != 200:
                #print "Status", response.status_code, "for:", ip
                #print "Status", response.text, "for:", ip, result_uri
                continue
            #print response.json()
            #if response.json(): return
            if routes_tag in response.text:
                response_data = response.json()
                for trace in response_data[routes_tag]:
                    if revtr:
                        src = trace['src']
                        dst = trace['dst']
                    else:
                        src = ip_int_to_string(trace['src'])
                        dst = ip_int_to_string(trace['dst'])
                    if (src, dst) not in pairs:
                        continue
                    result = {}
                    result['src'] = src
                    result['dst'] = dst
                    try:
                        src_name = socket.gethostbyaddr(src)[0]
                        result['src_name'] = src_name
                    except:
                        pass
                    try:
                        dst_name = socket.gethostbyaddr(dst)[0]
                        result['dst_name'] = dst_name
                    except:
                        pass
                    complete = False
                    if revtr and 'path' in trace:
                        hops = []
                        path_len = len(trace['path'])
                        first_hop = ''
                        last_hop = ''
                        for i in range(path_len):
                            hop = trace['path'][i]
                            if 'hop' in hop:
                                if i == 0:
                                    first_hop = hop['hop']
                                if i == path_len - 1:
                                    last_hop = hop['hop']
                                hop_data = {'hop': i,
                                            'ip': hop['hop']}
                                try:
                                    hostname = socket.gethostbyaddr(ip)[0]
                                    hop_data['hostname'] = hostname
                                except:
                                    pass
                                hops.append(hop_data)
                        if first_hop == dst and last_hop == src:
                            complete = True
                        result['hops'] = hops
                    elif not revtr and 'hops' in trace:
                        hops = []
                        for hop in trace['hops']:
                            if 'addr' in hop and 'probe_ttl' in hop:
                                ip = ip_int_to_string(hop['addr'])
                                hop_data = {'hop': hop['probe_ttl'],
                                            'ip': ip_int_to_string(hop['addr'])}
                                try:
                                    hostname = socket.gethostbyaddr(ip)[0]
                                    hop_data['hostname'] = hostname
                                except:
                                    pass
                                hops.append(hop_data)
                                if ip == dst:
                                    complete = True
                        result['hops'] = hops
                    result['complete'] = complete
                    result['revtr'] = revtr
                    result['dst_cntry_name'] = dst_cntry_name
                    trace['result_url'] = result_uri
                    save_trace(src, dst, result, trace, revtr)
                    #print "Saved:", src, ' ', dst
                    traceroutes.append(result)
                post_processing_geosources(traceroutes)
                return traceroutes
        except:
            print "Exception while performing traceroutes"
            traceback.print_exc()
            return traceroutes
    print "Max tries reached for traceroutes"
    return traceroutes


# saves the results uri to /traceroutes/results_url/fwdtr or revtr/YYYYMMDDhhmmss_results_url.txt
def save_results_uri(result_uri, revtr=False):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ip_dir = os.path.join(cur_dir, configs.traceroutes.TRACE_DIR,configs.traceroutes.RESULTS_URL_DIR,
                          (configs.traceroutes.REV_DIR if revtr else configs.traceroutes.FWD_DIR))
    if not os.path.exists(ip_dir):
        os.makedirs(ip_dir)
    file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S_result_url') + '.txt'
    with open(os.path.join(ip_dir, file_name), 'wb') as f:
        f.write(result_uri)


def load_results_uri(revtr=False):
    uri_list=[]
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ip_dir = os.path.join(cur_dir, configs.traceroutes.TRACE_DIR,configs.traceroutes.RESULTS_URL_DIR,
                          (configs.traceroutes.REV_DIR if revtr else configs.traceroutes.FWD_DIR))
    for file_name in os.listdir(ip_dir):
        file_datetime = datetime.datetime.strptime(file_name.split("_")[0],"%Y%m%d%H%M%S")
        if (datetime.datetime.now() - file_datetime).days > 3:
            continue
        with open(os.path.join(ip_dir, file_name), 'rb') as f:
            content = f.read()
            uri = content.split('\n')[0]
            uri_list.append(uri)
    return uri_list


# saves a traceroute and its raw json data to /traceroutes/fwdtr or revtr/source ip/dest ip/YYYYMMDDhhmmss.json
# saves raw json as YYYYMMDDhhmmss_raw.json
def save_trace(source, dest, trace, raw_response, revtr=False):
  cur_dir = os.path.dirname(os.path.abspath(__file__))
  trace_dir = os.path.join(cur_dir, configs.traceroutes.TRACE_DIR,
                        (configs.traceroutes.REV_DIR if revtr else configs.traceroutes.FWD_DIR),
                        source, dest)
  file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json'
  file_name_raw = file_name.split('.')[0] + "_raw.json"
  if not os.path.exists(trace_dir):
      os.makedirs(trace_dir)
  with open(os.path.join(trace_dir, file_name), 'wb') as f:
      f.write(json.dumps(trace))
  with open(os.path.join(trace_dir, file_name_raw), 'wb') as f:
      f.write(json.dumps(raw_response))


# returns None if not in cache/stale
# returns {} if empty but in cache
# differentiate between then using "is None" or "is not None"
def get_existing_trace(source, dest, revtr=False):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        trace_dir = os.path.join(cur_dir, configs.traceroutes.TRACE_DIR,
                                 (configs.traceroutes.REV_DIR if revtr else configs.traceroutes.FWD_DIR),
                                 source, dest)
        file_name = max(os.listdir(trace_dir))
        file_date = file_name.split('.')[0]
        file_date = file_date.split('_raw')[0]
        file_date_obj = datetime.datetime.strptime(file_date,'%Y%m%d%H%M%S')
        if (datetime.datetime.now() - file_date_obj).days > configs.traceroutes.MAX_TRACE_AGE:
            return None
        file_name = file_date + ".json"
        with open(os.path.join(trace_dir, file_name), 'r') as f:
            #print "Cached Trace"
            return json.loads(f.read())
    except:
        #traceback.print_exc()
        return None


def main_execution():
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND)
    pputils.read_values_to_geo_sources()
    # do pings for this ip, get hostname information, validate destination using ipinfo
    dest_countries = util.get_all_countries()
    #dest_countries = ["Pakistan"]
    
    ignore_list = []
    for dest_cntry in dest_countries:
        if dest_cntry in ignore_list:
            continue
        print "Dest Country:", dest_cntry
        get_traceroute_to_destination_country(dest_cntry)
        with open('temp_ignore_list.txt','a') as f:
            f.write("'")
            f.write(dest_cntry)
            f.write("'")
            f.write(",")

def main_execution_read_only():
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND)
    pputils.read_values_to_geo_sources()
    # do pings for this ip, get hostname information, validate destination using ipinfo
    get_all_completed_traceroutes_all()


if __name__ == '__main__':
    print get_traceroute(ip_int_to_string(2915894249), ip_int_to_string(2732273692), True)
