# -*- coding: utf-8 -*-
"""

    ppmeasurements.ripeatlas
    ~~~~~~~~~~~~~~

    This module contains the code for reading the meta data dumps from
    Ripe Atlas, downloading relevant measurements (traceroutes and pings),
    parsing these dumps, etc.


    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import configs.traceroutes
import bz2
import os
from ripe.atlas.cousteau import AtlasResultsRequest
import traceback
from datetime import datetime
from multiprocessing import Process,Manager
import ppnamespace
import geosources.geolocation as geo_sources_module
import geosources.geolocation
import geosources
from geosources import whois
import geosources.ddec as ddec
import requests
import pputils
import ppmeasurements.util as util_traceroutes
import json

def get_directories():
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    ripe_data_dir = os.path.join(cur_dir, configs.traceroutes.RIPE_PARENT_FOLDER,
                configs.traceroutes.RIPE_DATA_FOLDER)
    ripe_nodes_dir = os.path.join(cur_dir, configs.traceroutes.RIPE_PARENT_FOLDER,
                configs.traceroutes.RIPE_NODE_FOLDER)
    ripe_traceroutes_dir = os.path.join(cur_dir, configs.traceroutes.RIPE_PARENT_FOLDER,
                configs.traceroutes.RIPE_TRACEROUTES_FOLDER)
    ripe_pings_dir = os.path.join(cur_dir, configs.traceroutes.RIPE_PARENT_FOLDER,
                configs.traceroutes.RIPE_PINGS_FOLDER)
    ripe_raw_dir = os.path.join(cur_dir, configs.traceroutes.RIPE_PARENT_FOLDER,
                configs.traceroutes.RIPE_RAW_FOLDER)
    return cur_dir, ripe_data_dir, ripe_nodes_dir, ripe_traceroutes_dir, ripe_pings_dir, ripe_raw_dir 


def create_traceroute_meta_file(read_file_name, directory):
    write_file_name = read_file_name + configs.traceroutes.RELAVENT_TRACES_FILE_SUFFIX
    out_file_path = os.path.join(directory, write_file_name)
    file_path = os.path.join(directory, read_file_name)
    counter = 0
    counter_trace = 0
    counter_ping = 0
    with open(out_file_path, 'w') as out_file:
        with bz2.BZ2File(file_path, "r") as data_file:
            for line in data_file:
                counter += 1
                try:
                    json_data = json.loads(line)
                    if 'type' in json_data and 'name' in json_data['type'] and \
                            (json_data['type']['name'].lower() == 'traceroute' or json_data['type']['name'].lower() == 'ping'):
                        if 'start_time' in json_data:
                            trace_date_start = datetime.fromtimestamp(json_data['start_time'])
                            if trace_date_start > configs.traceroutes.START_DATE_DATA and trace_date_start < configs.traceroutes.END_DATE_DATA:
                                out_file.write(line)
                                if json_data['type']['name'].lower() == 'traceroute':
                                    counter_trace += 1
                                else:
                                    counter_ping += 1
                except:
                    #traceback.print_exc()
                    pass
                if counter % 1000 == 0:
                    print "Lines processed:", counter, "| Traceroutes processed:", counter_trace,  "| Pings processed:", counter_ping 
    print "Lines processed:", counter, "| Traceroutes processed:", counter_trace,  "| Pings processed:", counter_ping


def download_results_for_file(read_file_name, get_fresh_copy=True):
    counter = 0
    num_threads_max = configs.traceroutes.RIPE_MAX_PROC_INIT_PROCESSING
    thread_counter = 0
    thread_pool = []
    cur_dir, ripe_data_dir, ripe_nodes_dir, ripe_traceroutes_dir, ripe_pings_dir, ripe_raw_dir = get_directories()
    file_path = os.path.join(ripe_data_dir, read_file_name)
    statuses_useful = ("Forced to Stop", "Stopped", 'Archived','Specified','Ongoing', 'Scheduled')
    with open(file_path, 'r') as read_file:
        for line in read_file:
            counter += 1
            #if counter < 87027:
            #    continue
            #if counter < 84664:
            #    continue
            print "Filename:",read_file_name,"  | Lines processed:", counter
            x = json.loads(line)
            if x['status']['name'] not in statuses_useful:
                continue 
            if get_fresh_copy:
                p = Process(target=get_data_save, args=(line,))
            else:
                p = Process(target=get_data_from_cache_save_update, args=(line,))
            p.daemon = False
            thread_pool.append(p)
            thread_counter += 1
            # start all threads
            if thread_counter >= num_threads_max:
                for process in thread_pool:
                    process.start()
                for process in thread_pool:
                    process.join()
                thread_pool = []
                thread_counter = 0
                #break
    # close pool    
    for process in thread_pool:
        process.start()
    for process in thread_pool:
        process.join()
    thread_pool = []


def get_result_general(line):
    json_meta_data = json.loads(line)
    kwargs = {
        "msm_id": json_meta_data["msm_id"],
        "start": json_meta_data["start_time"],
        "stop": json_meta_data["stop_time"],
    }

    is_success, results = AtlasResultsRequest(**kwargs).create()
    return is_success, results, json_meta_data
    

def get_save_data_traceroute(result,json_meta_data):
    if 'result' in result:
        for result_hops in result['result']:
            if 'result' in result_hops:
                for hop_info in result_hops['result']:
                    if 'from' in hop_info:
                        ip = hop_info['from']     
                        #hostname = socket.gethostbyaddr(ip)[0]
                        #hop_info['hostname'] = hostname
                        #print hostname
                        hostname = ''
                        #print "Traceroute IP:", ip
                        get_ip_information_for_analysis(ip,hostname)


def get_save_data_ping(result,json_meta_data):
    if 'dst_addr' not in result:
        return
    ip = result['dst_addr']
    hostname = ''
    #print "Ping IP:", ip
    get_ip_information_for_analysis(ip,hostname)


def get_ip_information_for_analysis(ip,hostname):
    ip_str =ip
    x_hostname = hostname
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
         return
    try: # slightly untested.
        if not ddec.in_cache(x_hostname):
            ddec.request_ddec_country(x_hostname)
    except:
        traceback.print_exc()


def save_result_dump_raw(results,json_meta_data):
    cur_dir, ripe_data_dir, ripe_nodes_dir, ripe_traceroutes_dir, ripe_pings_dir, ripe_raw_dir = get_directories()
    write_file_path = os.path.join(ripe_raw_dir, str(json_meta_data["msm_id"]))
    with open(write_file_path,'w') as write_file:
        json.dump(results,write_file)


def load_result_dump_raw(json_meta_data):
    cur_dir, ripe_data_dir, ripe_nodes_dir, ripe_traceroutes_dir, ripe_pings_dir, ripe_raw_dir = get_directories()
    read_file_path = os.path.join(ripe_raw_dir, str(json_meta_data["msm_id"]))
    if not os.path.exists(read_file_path):
        return False, None
    try:
        with open(read_file_path,'r') as read_file:
            return True, json.load(read_file)
    except:
        traceback.print_exc()
        return False, None        


def load_cached_results(line):
    json_meta_data = json.loads(line)
    in_cache, results = load_result_dump_raw(json_meta_data)
    is_success = in_cache
    return in_cache, is_success, results, json_meta_data


def get_data_save(line):
    in_cache, is_success, results, json_meta_data = load_cached_results(line)
    if not in_cache:
        #return
        is_success, results, json_meta_data = get_result_general(line)
    if not is_success:
        return
    for result in results:        
        if result['af'] == 6:
            continue
        if result['msm_name'] == 'Traceroute':
            get_save_data_traceroute(result,json_meta_data)
        if result['msm_name'] == 'Ping':
            get_save_data_ping(result,json_meta_data)
    if not in_cache:
        save_result_dump_raw(results,json_meta_data)


def get_data_from_cache_save_update(line):
    in_cache, is_success, results, json_meta_data = load_cached_results(line)
    if not in_cache:
        return
    if not is_success:
        return
    for result in results:        
        if result['af'] == 6:
            continue
        if result['msm_name'] == 'Traceroute':
            get_save_data_traceroute(result,json_meta_data)
        if result['msm_name'] == 'Ping':
            get_save_data_ping(result,json_meta_data)
    save_result_dump_raw(results,json_meta_data)


def create_traceroute_results_from_meta_data(get_fresh_copy = True):
    requests.packages.urllib3.disable_warnings()
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND)
    pputils.read_values_to_geo_sources()

    cur_dir, ripe_data_dir, ripe_nodes_dir, ripe_traceroutes_dir, ripe_pings_dir, ripe_raw_dir = get_directories()
    for file_name in os.listdir(ripe_data_dir):
        if not file_name.endswith(configs.traceroutes.RELAVENT_TRACES_FILE_SUFFIX):
            continue
        download_results_for_file(file_name, get_fresh_copy)


def create_traceroute_meta_data_from_raw_dump():
    cur_dir, ripe_data_dir, ripe_nodes_dir, ripe_traceroutes_dir, ripe_pings_dir, ripe_raw_dir = get_directories()
    for file_name_bzip2 in os.listdir(ripe_data_dir):
        if not file_name_bzip2.endswith('.bz2'):
            continue
        create_traceroute_meta_file(file_name_bzip2, ripe_data_dir)


def get_min_rtt_data_ping(result,return_data_dict):
    if 'dst_addr' in result and 'min' in result and result['min']>0 and 'prb_id' in result:
        ip = result['dst_addr']
        hostname = ''
        if 'hostname' in result:
            hostname = result['hostname']
        ip_int = pputils.ip_string_to_int(ip)
        if ip_int <= 0:
            return return_data_dict
        if ip_int not in return_data_dict:
            return_data_dict[ip_int] = {}
            ip_dict = return_data_dict[ip_int]
            ip_dict["srcs"] = {}
            ip_dict['hostname'] = hostname
        ip_dict = return_data_dict[ip_int]
        probe = result['prb_id']
        if probe in ip_dict["srcs"]:
            ip_dict["srcs"][probe] = min(ip_dict["srcs"][probe],result['min'])
        else:
            ip_dict["srcs"][probe] = result['min']            
    return return_data_dict


def get_min_rtt_data_traceroute(result,return_data_dict):
    if 'prb_id' not in result:
        return return_data_dict    
    if 'result' not in result:
        return return_data_dict
    for result_hops in result['result']:
        if 'result' in result_hops:
            for hop_info in result_hops['result']:
                if 'rtt' not in hop_info:
                    hop_info['rtt'] = 1500  # extremely large rtt
                if 'from' in hop_info:
                    ip = hop_info['from']
                else:
                    continue
                if util_traceroutes.is_private_ip(ip):
                    continue
                hostname = ''
                if 'hostname' in hop_info:
                    hostname = hop_info['hostname']
                # process the hop
                ip_int = pputils.ip_string_to_int(ip)
                if ip_int not in return_data_dict:
                    return_data_dict[ip_int] = {}
                    ip_dict = return_data_dict[ip_int]
                    ip_dict["srcs"] = {}
                    ip_dict['hostname'] = hostname
                ip_dict = return_data_dict[ip_int]
                probe = result['prb_id']
                if probe in ip_dict["srcs"]:
                    ip_dict["srcs"][probe] = min(ip_dict["srcs"][probe],hop_info['rtt'])
                else:
                    ip_dict["srcs"][probe] = hop_info['rtt']
    return return_data_dict


def load_results_file(file_id, return_data_dict, meta_info_dict):
    # handle traceroutes and pings
    # only return something like {ip: {'rtts':{dict of min rtt from all probes}, 'hostname':''}}
    # this ip address is an integer
    print "IPs:", len(return_data_dict), "| Traceroutes:", meta_info_dict["traces"], "| Pings:", meta_info_dict["pings"] 
    file_id_dict = {"msm_id":file_id}
    in_cache, results = load_result_dump_raw(file_id_dict)
    if not in_cache:
        return return_data_dict
    for result in results:        
        if result['af'] == 6:
            continue
        if result['msm_name'] == 'Traceroute':
            meta_info_dict["traces"] += 1
            return_data_dict = get_min_rtt_data_traceroute(result,return_data_dict)
        if result['msm_name'] == 'Ping':
            meta_info_dict["pings"] += 1
            return_data_dict = get_min_rtt_data_ping(result,return_data_dict)
    return return_data_dict



def predict_ripe_traceroutes(file_id, overall_predictions_dict, output_file_bz2_handle, src_info_dict, ripe_hostname_dict, no_pred_set, all_ips_set):
    file_id_dict = {"msm_id":file_id}
    in_cache, results = load_result_dump_raw(file_id_dict)
    if not in_cache:
        return 0
    traceroutes_in_file = 0
    for result in results:        
        if result['af'] == 6:
            continue
        if result['msm_name'] != 'Traceroute':
            continue
        if 'prb_id' not in result:
            continue
        if 'result' not in result:
                continue
        prb_id = result['prb_id']
        try:
            src_info = src_info_dict[prb_id]
            src_country = src_info["country_name_full"]
        except:
            traceback.print_exc()
            continue
        traceroutes_in_file += 1
        result["probe_country"] = src_country
        for result_hops in result['result']:
            if 'result' in result_hops:
                for hop_info in result_hops['result']:
                    if 'from' in hop_info:
                        ip = hop_info['from']
                        all_ips_set.add(ip)
                    else:
                        hop_info['predictions'] = []
                        continue
                    if util_traceroutes.is_private_ip(ip):
                        hop_info['predictions'] = []
                        continue
                    ip_int = pputils.ip_string_to_int(ip)
                    if ip_int in ripe_hostname_dict:
                        hop_info['hostname'] = ripe_hostname_dict[ip_int]
                    else:
                        hop_info['hostname'] = ''
                    # process the hop
                    if ip not in overall_predictions_dict:
                        #print "No predictions for:", ip
                        no_pred_set.add(ip)
                        rtt = -1
                        if 'rtt' in hop_info:
                            rtt = hop_info['rtt']
                        print ip, hop_info['hostname'], "| RTT:", rtt 
                        hop_info['predictions'] = []
                        continue
                    hop_info['predictions'] = overall_predictions_dict[ip]
                    #print hop_info
        output_file_bz2_handle.write(json.dumps(result))
        output_file_bz2_handle.write('\n')  
    return traceroutes_in_file


def main_function():
    # you need to have files in data (for metadata) and nodes (for probes) folder 
    # and then modify dates in the configs.traceroutes.
    create_traceroute_meta_data_from_raw_dump()
    create_traceroute_results_from_meta_data()
    # loading results.    




# sample ping result
"""
    [{'af': 4, 'prb_id': 23267, 'result': [{'rtt': 77.290275}, {'rtt': 77.156325}, {'rtt': 77.27759}], 'ttl': 46,
      'avg': 77.2413966667, 'size': 48, 'from': '176.58.8.10', 'proto': 'ICMP', 'timestamp': 1493510406, 'dup': 0,
      'type': 'ping', 'sent': 3, 'msm_id': 8317926, 'fw': 4760, 'max': 77.290275, 'step': 240,
      'src_addr': '176.58.8.10', 'rcvd': 3, 'msm_name': 'Ping', 'lts': 40, 'dst_name': '77.46.134.189',
      'min': 77.156325, 'group_id': 8317926, 'dst_addr': '77.46.134.189'}]
"""


#Sample traceroute result
"""
    [{u'lts': 1, u'size': 48, u'group_id': 8221392, u'from': u'212.203.44.150', u'dst_name': u'197.225.242.16',
      u'fw': 4760, u'proto': u'ICMP', u'af': 4, u'msm_name': u'Traceroute', u'prb_id': 21245, u'result': [{u'result': [
            {u'rtt': 1.756, u'ttl': 64, u'from': u'192.168.178.1', u'size': 28},
            {u'rtt': 0.341, u'ttl': 64, u'from': u'192.168.178.1', u'size': 28},
            {u'rtt': 0.282, u'ttl': 64, u'from': u'192.168.178.1', u'size': 28}], u'hop': 1}, {u'result': [
            {u'rtt': 3.171, u'ttl': 63, u'from': u'100.64.48.1', u'size': 28},
            {u'rtt': 1.072, u'ttl': 63, u'from': u'100.64.48.1', u'size': 28},
            {u'rtt': 3.031, u'ttl': 63, u'from': u'100.64.48.1', u'size': 28}], u'hop': 2}, {u'result': [
            {u'rtt': 1.919, u'ttl': 62, u'from': u'212.203.33.198', u'size': 28},
            {u'rtt': 1.59, u'ttl': 62, u'from': u'212.203.33.198', u'size': 28},
            {u'rtt': 1.544, u'ttl': 62, u'from': u'212.203.33.198', u'size': 28}], u'hop': 3}, {u'result': [
            {u'rtt': 1.761, u'ttl': 61, u'from': u'77.109.134.149', u'size': 28},
            {u'rtt': 1.597, u'ttl': 61, u'from': u'77.109.134.149', u'size': 28},
            {u'rtt': 1.637, u'ttl': 61, u'from': u'77.109.134.149', u'size': 28}], u'hop': 4}, {u'result': [
            {u'rtt': 1.542, u'ttl': 251, u'from': u'62.115.148.48', u'size': 28},
            {u'rtt': 1.536, u'ttl': 251, u'from': u'62.115.148.48', u'size': 28},
            {u'rtt': 1.53, u'ttl': 251, u'from': u'62.115.148.48', u'size': 28}], u'hop': 5}, {u'result': [
            {u'rtt': 10.414, u'ttl': 248, u'from': u'62.115.142.104', u'size': 68},
            {u'rtt': 10.209, u'ttl': 248, u'from': u'62.115.142.104', u'size': 68},
            {u'rtt': 10.339, u'ttl': 248, u'from': u'62.115.142.104', u'size': 68}], u'hop': 6}, {u'result': [
            {u'rtt': 10.121, u'ttl': 247, u'from': u'62.115.116.160', u'size': 28},
            {u'rtt': 17.611, u'ttl': 247, u'from': u'62.115.116.160', u'size': 28},
            {u'rtt': 10.132, u'ttl': 247, u'from': u'62.115.116.160', u'size': 28}], u'hop': 7}, {u'result': [
            {u'rtt': 18.14, u'ttl': 245, u'from': u'213.248.82.41', u'size': 28},
            {u'rtt': 20.838, u'ttl': 245, u'from': u'213.248.82.41', u'size': 28},
            {u'rtt': 21.915, u'ttl': 245, u'from': u'213.248.82.41', u'size': 28}], u'hop': 8}, {u'result': [
            {u'ttl': 240, u'rtt': 26.931, u'icmpext': {u'rfc4884': 0, u'version': 2, u'obj': [
                {u'type': 1, u'mpls': [{u's': 1, u'ttl': 1, u'exp': 0, u'label': 419191}], u'class': 1}]},
             u'from': u'195.219.87.10', u'size': 140}, {u'ttl': 240, u'rtt': 26.752,
                                                        u'icmpext': {u'rfc4884': 0, u'version': 2, u'obj': [{u'type': 1,
                                                                                                             u'mpls': [{
                                                                                                                           u's': 1,
                                                                                                                           u'ttl': 1,
                                                                                                                           u'exp': 0,
                                                                                                                           u'label': 419191}],
                                                                                                             u'class': 1}]},
                                                        u'from': u'195.219.87.10', u'size': 140},
            {u'ttl': 240, u'rtt': 26.727, u'icmpext': {u'rfc4884': 0, u'version': 2, u'obj': [
                {u'type': 1, u'mpls': [{u's': 1, u'ttl': 1, u'exp': 0, u'label': 419191}], u'class': 1}]},
             u'from': u'195.219.87.10', u'size': 140}], u'hop': 9}, {u'result': [{u'ttl': 241, u'rtt': 27.659,
                                                                                  u'icmpext': {u'rfc4884': 0,
                                                                                               u'version': 2, u'obj': [
                                                                                          {u'type': 1, u'mpls': [
                                                                                              {u's': 1, u'ttl': 1,
                                                                                               u'exp': 0,
                                                                                               u'label': 537112}],
                                                                                           u'class': 1}]},
                                                                                  u'from': u'80.231.153.50',
                                                                                  u'size': 140},
                                                                                 {u'ttl': 241, u'rtt': 30.108,
                                                                                  u'icmpext': {u'rfc4884': 0,
                                                                                               u'version': 2, u'obj': [
                                                                                          {u'type': 1, u'mpls': [
                                                                                              {u's': 1, u'ttl': 1,
                                                                                               u'exp': 0,
                                                                                               u'label': 537112}],
                                                                                           u'class': 1}]},
                                                                                  u'from': u'80.231.153.50',
                                                                                  u'size': 140},
                                                                                 {u'ttl': 241, u'rtt': 26.959,
                                                                                  u'icmpext': {u'rfc4884': 0,
                                                                                               u'version': 2, u'obj': [
                                                                                          {u'type': 1, u'mpls': [
                                                                                              {u's': 1, u'ttl': 1,
                                                                                               u'exp': 0,
                                                                                               u'label': 537112}],
                                                                                           u'class': 1}]},
                                                                                  u'from': u'80.231.153.50',
                                                                                  u'size': 140}], u'hop': 10}, {
                                                                                                              u'result': [
                                                                                                                  {
                                                                                                                      u'ttl': 245,
                                                                                                                      u'rtt': 26.977,
                                                                                                                      u'icmpext': {
                                                                                                                          u'rfc4884': 0,
                                                                                                                          u'version': 2,
                                                                                                                          u'obj': [
                                                                                                                              {
                                                                                                                                  u'type': 1,
                                                                                                                                  u'mpls': [
                                                                                                                                      {
                                                                                                                                          u's': 1,
                                                                                                                                          u'ttl': 1,
                                                                                                                                          u'exp': 0,
                                                                                                                                          u'label': 622480}],
                                                                                                                                  u'class': 1}]},
                                                                                                                      u'from': u'80.231.154.143',
                                                                                                                      u'size': 140},
                                                                                                                  {
                                                                                                                      u'ttl': 245,
                                                                                                                      u'rtt': 26.821,
                                                                                                                      u'icmpext': {
                                                                                                                          u'rfc4884': 0,
                                                                                                                          u'version': 2,
                                                                                                                          u'obj': [
                                                                                                                              {
                                                                                                                                  u'type': 1,
                                                                                                                                  u'mpls': [
                                                                                                                                      {
                                                                                                                                          u's': 1,
                                                                                                                                          u'ttl': 1,
                                                                                                                                          u'exp': 0,
                                                                                                                                          u'label': 622480}],
                                                                                                                                  u'class': 1}]},
                                                                                                                      u'from': u'80.231.154.143',
                                                                                                                      u'size': 140},
                                                                                                                  {
                                                                                                                      u'ttl': 245,
                                                                                                                      u'rtt': 27.019,
                                                                                                                      u'icmpext': {
                                                                                                                          u'rfc4884': 0,
                                                                                                                          u'version': 2,
                                                                                                                          u'obj': [
                                                                                                                              {
                                                                                                                                  u'type': 1,
                                                                                                                                  u'mpls': [
                                                                                                                                      {
                                                                                                                                          u's': 1,
                                                                                                                                          u'ttl': 1,
                                                                                                                                          u'exp': 0,
                                                                                                                                          u'label': 622480}],
                                                                                                                                  u'class': 1}]},
                                                                                                                      u'from': u'80.231.154.143',
                                                                                                                      u'size': 140}],
                                                                                                              u'hop': 11},
                                                                                                          {u'result': [{
                                                                                                                           u'rtt': 26.616,
                                                                                                                           u'ttl': 244,
                                                                                                                           u'from': u'80.231.130.30',
                                                                                                                           u'size': 28},
                                                                                                                       {
                                                                                                                           u'rtt': 26.478,
                                                                                                                           u'ttl': 244,
                                                                                                                           u'from': u'80.231.130.30',
                                                                                                                           u'size': 28},
                                                                                                                       {
                                                                                                                           u'rtt': 26.697,
                                                                                                                           u'ttl': 244,
                                                                                                                           u'from': u'80.231.130.30',
                                                                                                                           u'size': 28}],
                                                                                                           u'hop': 12},
                                                                                                          {u'result': [{
                                                                                                                           u'x': u'*'},
                                                                                                                       {
                                                                                                                           u'x': u'*'},
                                                                                                                       {
                                                                                                                           u'x': u'*'}],
                                                                                                           u'hop': 13},
                                                                                                          {u'result': [{
                                                                                                                           u'rtt': 257.743,
                                                                                                                           u'ttl': 246,
                                                                                                                           u'from': u'197.226.230.1',
                                                                                                                           u'size': 68},
                                                                                                                       {
                                                                                                                           u'rtt': 254.256,
                                                                                                                           u'ttl': 246,
                                                                                                                           u'from': u'197.226.230.1',
                                                                                                                           u'size': 68},
                                                                                                                       {
                                                                                                                           u'rtt': 254.934,
                                                                                                                           u'ttl': 246,
                                                                                                                           u'from': u'197.226.230.1',
                                                                                                                           u'size': 68}],
                                                                                                           u'hop': 14},
                                                                                                          {u'result': [{
                                                                                                                           u'ttl': 245,
                                                                                                                           u'rtt': 257.394,
                                                                                                                           u'ittl': 0,
                                                                                                                           u'from': u'196.20.188.106',
                                                                                                                           u'size': 52},
                                                                                                                       {
                                                                                                                           u'ttl': 245,
                                                                                                                           u'rtt': 255.655,
                                                                                                                           u'ittl': 0,
                                                                                                                           u'from': u'196.20.188.106',
                                                                                                                           u'size': 52},
                                                                                                                       {
                                                                                                                           u'ttl': 245,
                                                                                                                           u'rtt': 254.783,
                                                                                                                           u'ittl': 0,
                                                                                                                           u'from': u'196.20.188.106',
                                                                                                                           u'size': 52}],
                                                                                                           u'hop': 15},
                                                                                                          {u'result': [{
                                                                                                                           u'rtt': 256.644,
                                                                                                                           u'ttl': 244,
                                                                                                                           u'from': u'197.225.242.16',
                                                                                                                           u'size': 48},
                                                                                                                       {
                                                                                                                           u'rtt': 256.632,
                                                                                                                           u'ttl': 244,
                                                                                                                           u'from': u'197.225.242.16',
                                                                                                                           u'size': 48},
                                                                                                                       {
                                                                                                                           u'rtt': 256.302,
                                                                                                                           u'ttl': 244,
                                                                                                                           u'from': u'197.225.242.16',
                                                                                                                           u'size': 48}],
                                                                                                           u'hop': 16}],
      u'timestamp': 1493006705, u'src_addr': u'192.168.178.11', u'paris_id': 1, u'endtime': 1493006721,
      u'type': u'traceroute', u'dst_addr': u'197.225.242.16', u'msm_id': 8221392}]

"""


