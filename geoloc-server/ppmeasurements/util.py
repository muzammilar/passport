# -*- coding: utf-8 -*-
"""

    ppmeasurements.util
    ~~~~~~~~~~~~~~

    This module contains utility functions for parsing information,
    checking for non-global IP address, convert traceroutes to machine-readable
    structures, etc.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import json
import trparse
import socket
import datetime
import time
###remove-me-later-muz###import ormsettings as DJANGO_SETTINGS
from ppstore.models import Hints_country_codes
import os
import csv
import pputils
import ipaddress

"""
Sample JSON:
    {"source": "127.0.1.1", "destName": "8.8.8.8", "destIP": "8.8.8.8", "resolvers": ["8.8.8.8"],
     "type": "Input_DNS_Resolver", "startTime": 1472651763386, "timestamp": 1472651763632, "entries": [
        {"rtt": [0.231, 0.213, 0.242], "router": ["129.10.113.1", null, null], "routerName": ["unknown", null, null],
         "numRouters": 1},
        {"rtt": [2.21, 2.389, 2.733], "router": ["129.10.110.2", null, null], "routerName": ["unknown", null, null],
         "numRouters": 1},
        {"rtt": [0.963, 0.951, 0.951], "router": ["10.2.29.52", null, null], "routerName": ["unknown", null, null],
         "numRouters": 1},
        {"rtt": [1.465, 1.518, 1.505], "router": ["10.2.29.33", null, null], "routerName": ["unknown", null, null],
         "numRouters": 1},
        {"rtt": [1.554, 1.544, 1.489], "router": ["10.2.29.230", null, null], "routerName": ["unknown", null, null],
         "numRouters": 1}, {"rtt": [4.289, 4.469, 4.513], "router": ["207.210.142.101", null, null],
                            "routerName": ["nox1sumgw1-neu-cps.nox.org.", null, null], "numRouters": 1},
        {"rtt": [31.826, 31.246, 31.229], "router": ["198.71.47.61", null, null],
         "routerName": ["et-10-0-0.122.rtr.eqch.net.internet2.edu.", null, null], "numRouters": 1},
        {"rtt": [31.204, 30.928, 31.072], "router": ["74.125.49.146", null, null],
         "routerName": ["unknown", null, null], "numRouters": 1},
        {"rtt": [31.263, 31.251, 31.791], "router": ["209.85.143.154", "209.85.242.133", "209.85.254.120"],
         "routerName": ["unknown", "unknown", "unknown"], "numRouters": 3},
        {"rtt": [31.787, 31.628, 31.447], "router": ["209.85.243.163", "209.85.241.47", null],
         "routerName": ["unknown", "unknown", null], "numRouters": 2},
        {"rtt": [40.979, 41.171, 40.825], "router": ["209.85.247.4", "216.239.47.121", "209.85.247.4"],
         "routerName": ["unknown", "unknown", "unknown"], "numRouters": 3},
        {"rtt": [40.97, 45.834, 45.785], "router": ["72.14.234.81", "216.239.62.13", "209.85.248.89"],
         "routerName": ["unknown", "unknown", "unknown"], "numRouters": 3},
        {"rtt": [-1.0, -1.0, -1.0], "router": ["unknown", "unknown", "unknown"],
         "routerName": ["unknown", "unknown", "unknown"], "numRouters": 3},
        {"rtt": [40.757, 41.006, 40.924], "router": ["8.8.8.8", null, null],
         "routerName": ["google-public-dns-a.google.com.", null, null], "numRouters": 1}]}
"""

def is_private_ip(ip_address_str):

    try:
        ip_addr = ipaddress.IPv4Address(unicode(ip_address_str))
        return not ip_addr.is_global
    except:
        #traceback.print_exc()
        return True  # if it fails, ignore it

def ip_address_to_ignore(ip_address_str):
    try:
        ip_addr = ipaddress.IPv4Address(unicode(ip_address_str))
        if ip_addr.is_multicast:
            return True, "Multicast IPv4 Address"  # if it fails, ignore it
        if ip_addr.is_private:
            return True, "Private IPv4 address"  # if it fails, ignore it
        if ip_addr.is_loopback:
            return True, "Loopback IPv4 address"  # if it fails, ignore it
        if ip_addr.is_reserved:
            return True, "Reserved IPv4 address"  # if it fails, ignore it
        if ip_addr.is_link_local:
            return True, "Link Local IPv4 address"  # if it fails, ignore it
        if not ip_addr.is_global:
            return True, "Not Global IPv4 address"  # if it fails, ignore it
        return False, ""
    except:
        #traceback.print_exc()
        return True, "error_parsing_IPv4_address"  # if it fails, ignore it


def is_valid_ip(ip_address_str):
    try:
        ip_addr = ipaddress.IPv4Address(unicode(ip_address_str))
        return True 
    except:
        return False


def get_all_countries():
    country_info = Hints_country_codes.objects.all()
    country_names = []
    for cntry in country_info:
        country_names.append(cntry.country)
    return country_names


def from_ripe_atlas_to_server_json(ripe_data):
    pass


def no_more_hops(idx, max_hop_id, hops_to_remove):
    while idx <= max_hop_id:
        if idx not in hops_to_remove:
            return False
        idx += 1
    return True


def from_traceroute_to_server_json(tracert_dict):
    tracert = ''.join(tracert_dict["result"])
    traceroute_list = trparse.loads(tracert)
    datetime_object = datetime.datetime.strptime(tracert_dict["time"],
                                                            '%Y-%m-%d %H:%M:%S')
    start_time = time.mktime(datetime_object.timetuple())
    start_time = int(start_time * 1000)  # milliseconds
    timestamp = start_time + 200
    dest_ip = traceroute_list.dest_ip
    dest_name = traceroute_list.dest_name
    try:
        source = socket.gethostbyname(tracert_dict["src"])
    except:
        source = "127.0.0.1"
    server_object_dict = {}
    server_object_dict["source"] = source
    server_object_dict["destName"] = dest_name
    server_object_dict["destIP"] = dest_ip
    server_object_dict["resolvers"] = ["8.8.8.8"]
    server_object_dict["type"] = "Input_DNS_Resolver"
    server_object_dict["startTime"] = start_time
    server_object_dict["timestamp"] = timestamp
    entries = []

    #print traceroute_list.hops[13].idx
    # get useless hops
    hops_to_remove = []
    max_hop_id = 0
    for hop in traceroute_list.hops:
        num_no_ip = 0
        max_hop_id = max(max_hop_id, hop. idx)
        for probe in hop.probes:
            if probe.ip is None:
                num_no_ip += 1
        if num_no_ip == len(hop.probes):
            hops_to_remove.append(hop.idx)

    # create a list of entries
    for hop in traceroute_list.hops:
        entry = {}
        rtt = []
        router = []
        router_name = []
        num_routers = 0
        if hop.idx in hops_to_remove and no_more_hops(hop.idx, max_hop_id,
                                                                hops_to_remove):
            continue
        for probe in hop.probes:
            if probe.ip is None:
                router.append("unknown")
                router_name.append("unknown")
                rtt.append(-1.0)
                continue
            router.append(probe.ip)
            if probe.name is None:
                router_name.append("unknown")
            elif probe.name == probe.ip:
                router_name.append("unknown")
            else:
                router_name.append(probe.name)
            if probe.rtt is None:
                rtt.append(-1.0)
            else:
                rtt.append(probe.rtt)
        num_routers = len(set(router))
        entry["rtt"] = rtt
        entry["routerName"] = router_name
        entry["router"] = router
        entry["numRouters"] = num_routers
        entries.append(entry)
    server_object_dict["entries"] = entries
    return server_object_dict


def test_from_traceroute_to_server_json():
    sample = '{"dest": "www.army.cz", "src": "planetlab1.pop-mg.rnp.br", "revtr": false, ' \
             '"result": ["traceroute to www.army.cz (194.50.64.66), 30 hops max, 60 byte packets\n", " 1  * * *\n", ' \
             '" 2  couve.pop-mg.rnp.br (200.131.0.2)  10.109 ms  10.169 ms  10.276 ms\n", ' \
             '" 3  mg-lanmg.bkb.rnp.br (200.143.253.161)  0.215 ms  0.239 ms  0.219 ms\n", ' \
             '" 4  mg2-mg.bkb.rnp.br (200.143.253.226)  0.260 ms  0.251 ms  0.237 ms\n", ' \
             '" 5  ce-mg-oi.bkb.rnp.br (200.143.252.142)  39.712 ms  39.735 ms  39.726 ms\n", ' \
             '" 6  38.88.165.73 (38.88.165.73)  111.078 ms  111.284 ms 200.143.253.149 (200.143.253.149)  39.679 ms\n", ' \
             '" 7  mia1-ce-nau.bkb.rnp.br (200.143.252.38)  105.981 ms  105.976 ms  105.962 ms\n", ' \
             '" 8  38.88.165.73 (38.88.165.73)  106.555 ms  106.245 ms ash-bb4-link.telia.net (62.115.141.78)  141.574 ms\n", ' \
             '" 9  mai-b1-link.telia.net (213.248.75.1)  135.050 ms  135.035 ms  135.055 ms\n", ' \
             '"10  ash-bb4-link.telia.net (62.115.141.76)  132.028 ms ash-bb4-link.telia.net (62.115.141.127)  136.701 ms win-bb2-link.telia.net (62.115.136.137)  248.548 ms\n", ' \
             '"11  ffm-bb2-link.telia.net (80.91.246.63)  226.158 ms ffm-bb2-link.telia.net (62.115.141.109)  233.696 ms ffm-bb2-link.telia.net (213.155.135.58)  226.039 ms\n", ' \
             '"12  win-bb2-link.telia.net (213.155.137.101)  243.289 ms o2czech-ic-315302-prag-b3.c.telia.net (213.248.92.138)  250.948 ms win-bb2-link.telia.net (62.115.134.215)  241.527 ms\n", ' \
             '"13  prag-b3-link.telia.net (80.91.249.128)  244.451 ms prag-b3-link.telia.net (213.155.132.183)  244.265 ms 194.228.190.194 (194.228.190.194)  252.704 ms\n", ' \
             '"14  194.228.190.154 (194.228.190.154)  252.354 ms  252.369 ms  254.261 ms\n", "15  194.228.190.194 (194.228.190.194)  247.988 ms  247.535 ms *\n", ' \
             '"16  * * *\n", "17  * * *\n", "18  * * *\n", "19  * * *\n", "20  * * *\n", "21  * * *\n", "22  * * *\n", ' \
             '"23  * * *\n", "24  * * *\n", "25  * * *\n", "26  * * *\n", "27  * * *\n", "28  * * *\n", "29  * * *\n", ' \
             '"30  * * *\n"], "time": "2016-05-23 00:32:50"}'
    tracert_dict = json.loads(sample, strict=False)
    print from_traceroute_to_server_json(tracert_dict)


def test_from_ripe_atlas_to_server_json():
    pass


def traceroute_to_python_dict(tracert_dict, traceroute_id):
    tracert = ''.join(tracert_dict["result"])
    traceroute_list = trparse.loads(tracert)
    dest_ip = traceroute_list.dest_ip
    dest_name = traceroute_list.dest_name
    try:
        source = socket.gethostbyname(tracert_dict["src"])
    except:
        source = "127.0.0.1"
    server_object_dict = {}
    server_object_dict['traceroute_id'] = traceroute_id
    server_object_dict["src"] = source
    server_object_dict["dst"] = dest_name
    server_object_dict["src_ip_int"] = pputils.ip_string_to_int(source)
    server_object_dict["dst"] = dest_name
    server_object_dict["dst_ip"] = dest_ip
    server_object_dict["dst_ip_int"] = pputils.ip_string_to_int(dest_ip)
    entries = []

    #print traceroute_list.hops[13].idx
    # get useless hops
    hops_to_remove = []
    max_hop_id = 0
    for hop in traceroute_list.hops:
        num_no_ip = 0
        max_hop_id = max(max_hop_id, hop.idx)
        for probe in hop.probes:
            if probe.ip is None:
                num_no_ip += 1
        if num_no_ip == len(hop.probes):
            hops_to_remove.append(hop.idx)

    # create a list of entries
    for hop in traceroute_list.hops:        
        num_routers = 0
        if hop.idx in hops_to_remove and no_more_hops(hop.idx, max_hop_id,
                                                                hops_to_remove):
            continue
        for probe in hop.probes:
            entry = {}
            # none
            if probe.ip is None:
                continue
            # private
            if is_private_ip(probe.ip):
                continue
            entry["ip"] = pputils.ip_string_to_int(probe.ip)
            if entry["ip"] is None or entry["ip"] == 0:
                continue
            # src and destination
            if entry["ip"] == server_object_dict["src_ip_int"] or entry["ip"] == server_object_dict["dst_ip_int"]:
                continue
            if probe.name is None or probe.name == probe.ip:
                entry["hostname"] = None
            else:
                entry["hostname"] = probe.name
            entry["rtt"] = probe.rtt
            entries.append(entry)
    server_object_dict["entries"] = entries
    return server_object_dict


def get_traceroutes_from_file(f_path, traceroute_id):
    with open(f_path, "rB") as trace_file:
        tracert_dict = json.load(trace_file, strict=False)
        try:
            return traceroute_to_python_dict(tracert_dict, traceroute_id)        
        except:
            #traceback.print_exc()
            #exit(1)
            return None


def get_destination_node_list(country,max_count):
    FILE_ABS_PATH = os.path.abspath(__file__)
    CUR_DIR = os.path.dirname(FILE_ABS_PATH)
    f_name = "country_websites.csv"
    try:
        f = open(os.path.join(CUR_DIR, f_name), "rb")
    except:
        return []
    csv_reader = csv.reader(f)
    nodes_list = []
    counter = 0
    for row in csv_reader:
        if row[1]==country:
            url = row[2]
            #if '.gov' in url or '.edu' in url:
            nodes_list.append(url)
            #else:
            #    continue
            counter += 1
            if counter >= max_count:
                return nodes_list
    return nodes_list


def traceroute_string_to_list(tracert_data_string):
    try:
        traceroute_list = trparse.loads(tracert_data_string)
        return True, traceroute_list
    except:
        return False, None
        
if __name__ == "__main__":
    #test_from_traceroute_to_server_json()
    pass

