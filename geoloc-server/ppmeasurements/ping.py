# -*- coding: utf-8 -*-
"""

    ppmeasurements.ping
    ~~~~~~~~~~~~~~

    This module uses the the revtr server  to perform ping measurements
    from all (or some) the available vantage points and returns cached results.

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
import configs.pings
from pputils import ip_int_to_string
from ppmeasurements.util import is_private_ip
import random
import traceback



"""
# function: get_pings_measurements(ip)
# Input: string ip address
# Output: dictionary {src: rtt} where src is the string ip address of the measurement source, and rtt is the 
#       minimum rtt recorded for a ping from that src to the ip address given to the function.


To actually use this code, just use from perform_pings import get_pings_measurements. 
Right now the files are named as YYYYMMDD.json because I'm only using day granularity for the difference between 
an old measurement and the current date. The current configuration allows a ping measurement to last a month 
before doing a new one.
"""

def get_fwd_nodes():
    response = requests.get(configs.pings.SOURCES_URL, headers=configs.pings.KEY)
    if response.status_code != 200:
        return []
    #print response.json()
    return [str(addr['IP']) for addr in response.json()['VPS']]


# returns a dictionary of the form {src: rtt} where src is the dotted quad string
# representation of the source ip address for the measurement, and rtt is the
# minimum rtt in milliseconds of the ping from that src to the given destination
# ip address
def get_pings_measurements(ip):
    """
    Performs a ping measurement to an IP or returns cached result

    :param ip: string ip address
    :return: dictionary {src: rtt} where src is the string ip address of the measurement source, and rtt is the
       minimum rtt recorded for a ping from that src to the ip address given to the function.
    """
    # suppress https warnings
    requests.packages.urllib3.disable_warnings()
    # if it's private, ignore it
    if is_private_ip(ip):
        return {}
    min_pings = get_existing_pings(ip)
   
    if min_pings is not None:
        return min_pings
    min_pings = {}
    pings_to_perfom = []
    vantage_points = get_fwd_nodes()
    for vantage_point in vantage_points:
        pings_to_perfom.append({'src': vantage_point,
                                'dst': ip,
                                'count': configs.pings.PING_COUNT})
    pings_request_obj = {'pings': pings_to_perfom}

    response = requests.post(configs.pings.PING_URL, headers=configs.pings.KEY,
                             data=json.dumps(pings_request_obj))
    if response.status_code != 200:
        #print "Initial Status", response.text, "for:", ip
        return min_pings
    try:
        response_data = response.json()
    except:
        print "Initial Exception for:",ip
        traceback.print_exc()
        return min_pings
    result_uri = response_data['results']

    save_results_uri(ip,result_uri)

    tries = 0
    sleep_time_min = configs.pings.SLEEP_TIME * 0.5
    while tries < configs.pings.MAX_TRIES:
        sleep_time_in_iteration = sleep_time_min + random.random() * configs.pings.SLEEP_TIME
        time.sleep(sleep_time_in_iteration)
        tries += 1
        try:
            response = requests.get(result_uri, headers=configs.pings.KEY)
            if response.status_code != 200:
                print "Status", response.status_code, "for:", ip
                #print "Status", response.text, "for:", ip, result_uri
                # add an extra try for bad code
                return
            #print response.json()
            if 'pings' in response.text:
                response_data = response.json()
                for ping in response_data['pings']:
                    src = ip_int_to_string(ping['src'])
                    dst_int = ping['dst']
                    #print src,ping['src']
                    if src=='':
                        continue
                    if 'responses' in ping:
                        pings_responses_from_dst = []
                        for ping_response in ping['responses']:
                            if 'from' in ping_response and ping_response['from']==dst_int and 'rtt' in ping_response:
                                pings_responses_from_dst.append(ping_response['rtt']/1000.00) #rtt is in microsecs
                        if len(pings_responses_from_dst) > 0:    
                            min_ping_measured = min(pings_responses_from_dst)
                            min_pings[src] = min_ping_measured                        
                response_data["result_url"] = result_uri
                save_pings(ip, min_pings,response_data)
                print "Saved:", ip
                return min_pings
        except:
            print "Exception for:",ip
            traceback.print_exc()
            return min_pings
    print "Max tries for:", ip
    return min_pings


def save_results_uri(ip,result_uri):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ip_dir = os.path.join(cur_dir, configs.pings.PINGS_DIR,configs.pings.RESULTS_URL_DIR )
    with open(os.path.join(ip_dir, ip), 'wb') as f:
        f.write(result_uri)
    

def get_data_using_results_uri(ip):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ip_dir = os.path.join(cur_dir, configs.pings.PINGS_DIR,configs.pings.RESULTS_URL_DIR )
    tries = 0
    with open(os.path.join(ip_dir, ip), 'rb') as f:
        #print "File opened!"
        uri = f.readlines()[0]
        uri = uri.split('\r')[0]
        uri = uri.split('\n')[0]
        result_uri = uri
        #print result_uri
        sleep_time_min = configs.pings.SLEEP_TIME * 0.5
        min_pings={}
        while tries < configs.pings.MAX_TRIES:
            sleep_time_in_iteration = sleep_time_min + random.random() * configs.pings.SLEEP_TIME
            #time.sleep(sleep_time_in_iteration)
            tries += 1
            try:
                response = requests.get(result_uri, headers=configs.pings.KEY)
                if response.status_code != 200:
                    #print "Status", response.status_code, "for:", ip
                    #print "Status", response.text, "for:", ip, result_uri
                    # add an extra try for bad code
                    return
                #print response.json()
                if 'pings' in response.text:
                    response_data = response.json()
                    for ping in response_data['pings']:
                        src = ip_int_to_string(ping['src'])
                        dst_int = ping['dst']
                        #print src,ping['src']
                        if src=='':
                            continue
                        if 'responses' in ping:
                            pings_responses_from_dst = []
                            for ping_response in ping['responses']:
                                if 'from' in ping_response and ping_response['from']==dst_int and 'rtt' in ping_response:
                                    pings_responses_from_dst.append(ping_response['rtt']/1000.00) #rtt is in microsecs
                            if len(pings_responses_from_dst) > 0:    
                                min_ping_measured = min(pings_responses_from_dst)
                                min_pings[src] = min_ping_measured                        
                    response_data["result_url"] = result_uri
                    save_pings(ip, min_pings,response_data)
                    #print "Saved:", ip
                    return min_pings
            except:
                #print "Exception for:",ip
                #traceback.print_exc()
                return min_pings
        #print "Max tries for:", ip
        return min_pings



#takes a list of ip addresses
#returns nothing, saves pings to the disk, use the  get_existing_pings(ip) function
def get_pings_measurements_list(ip_list):
    # suppress https warnings
    requests.packages.urllib3.disable_warnings()
    # if it's private, ignore it
    ips_to_lookup = []
    ips_ignore = []
    ip_results_uri = {}
    for ip in ip_list:
        if is_private_ip(ip):
            ips_ignore.append(ip)
        min_pings = get_existing_pings(ip)
        if min_pings:
            ips_ignore.append(ip)
        min_pings = {}

    print "IPs to look up:", len(ip_list) - len(ips_ignore)
    vantage_points = get_fwd_nodes()
    for ip in ip_list:
        if ip in ips_ignore:
            continue
        pings_to_perfom = []
        for vantage_point in vantage_points:
            pings_to_perfom.append({'src': vantage_point,
                                    'dst': ip,
                                    'count': configs.pings.PING_COUNT})
        pings_request_obj = {'pings': pings_to_perfom}

        try:
            response = requests.post(configs.pings.PING_URL, headers=configs.pings.KEY,
                                     data=json.dumps(pings_request_obj))
            if response.status_code != 200:
                ips_ignore.append(ip)
                continue
            response_data = response.json()
        except:
            #traceback.print_exc()
            ips_ignore.append(ip)
            continue
        result_uri = response_data['results']
        ip_results_uri[ip] = result_uri
    #print "Got results URI"
    #print "IPs to look up:", len(ip_list) - len(ips_ignore)
    tries = 0
    sleep_time_min = configs.pings.SLEEP_TIME * 0.5
    sleep_time_max = configs.pings.SLEEP_TIME * 1.5
    sleep_time_delta = sleep_time_max - sleep_time_min    
    while tries < configs.pings.MAX_TRIES:
        sleep_time_in_iteration = sleep_time_min + random.random() * sleep_time_delta
        time.sleep(sleep_time_in_iteration)
        tries += 1
        print "Try number:", tries
        print datetime.datetime.now()
        for ip in ip_list:
            if ip in ips_ignore:
                continue
            time.sleep(sleep_time_in_iteration/100.0)
            result_uri = ip_results_uri[ip]
            try:
                response = requests.get(result_uri, headers=configs.pings.KEY)
                if response.status_code != 200:
                    continue
                if 'pings' in response.text:
                    response_data = response.json()
                    for ping in response_data['pings']:
                        src = ip_int_to_string(ping['src'])
                        dst_int = ping['dst']
                        if src=='':
                            continue
                        if 'responses' in ping:
                            pings_responses_from_dst = []
                            for ping_response in ping['responses']:
                                if 'from' in ping_response and ping_response['from']==dst_int and 'rtt' in ping_response:
                                    pings_responses_from_dst.append(ping_response['rtt']/1000.00) #rtt is in microsecs
                            if len(pings_responses_from_dst) > 0:    
                                min_ping_measured = min(pings_responses_from_dst)
                                min_pings[src] = min_ping_measured                        
                    response_data["result_url"] = result_uri
                    save_pings(ip, min_pings,response_data)
                    ips_ignore.append(ip)
            except:
                #traceback.print_exc()
                continue
    

# returns None if not in cache/stale
# returns {} if empty but in cache
# differentiate between then using "is None" or "is not None"
def get_existing_pings(ip):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        ip_dir = os.path.join(cur_dir, configs.pings.PINGS_DIR, '/'.join(ip.split('.')))
        file_name = max(os.listdir(ip_dir))
        file_date = file_name.split('.')[0]
        file_date = file_date.split('_raw')[0]
        file_date_obj = datetime.datetime.strptime(file_date,'%Y%m%d%H%M%S')
        if (datetime.datetime.now() - file_date_obj).days > configs.pings.MAX_PING_AGE:
            return None
        file_name = file_date + ".json"
        with open(os.path.join(ip_dir, file_name), 'r') as f:
            return json.loads(f.read())
    except:
        #traceback.print_exc()
        return None


def save_pings(ip, pings, raw_response):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ip_dir = os.path.join(cur_dir, configs.pings.PINGS_DIR, '/'.join(ip.split('.')))
    file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json'
    file_name_raw = file_name.split('.')[0] + "_raw.json"
    if not os.path.exists(ip_dir):
        os.makedirs(ip_dir)
    with open(os.path.join(ip_dir, file_name), 'wb') as f:
        f.write(json.dumps(pings))
    with open(os.path.join(ip_dir, file_name_raw), 'wb') as f:
        f.write(json.dumps(raw_response))


if __name__ == '__main__':
    print get_pings_measurements('127.0.0.1')
