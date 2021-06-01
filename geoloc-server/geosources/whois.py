# -*- coding: utf-8 -*-
"""

    geosources.whois
    ~~~~~~

    This module has been developed to be request the online available WhoIS information about an IP address.
    It handles caching for WhoIS information.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import traceback
###remove-me-later-muz######remove-me-later-muz###import ormsettings as DJANGO_SETTINGS   # don't remove
###remove-me-later-muz######remove-me-later-muz###from django.db import models
from ppstore.models import IP_WHOIS_INFORMATION
from ppstore.models import Hints_AS_INFO
###remove-me-later-muz###from ipwhois import IPWhois
from geosources import geolocation as geo_location_services

def to_string(x):
    if x is None:
        return ''
    return str(x.encode('unicode-escape'))


def to_int(x):
    if x is None:
        return -1
    return x


def in_cache(ip_address):
    existing_ips = IP_WHOIS_INFORMATION.objects.filter(ip=ip_address)
    if existing_ips.count() == 0:
        return False
    return True


def save_whois_informantion_to_model(curTestInstance, ip_address):
    try:
        whois_model = IP_WHOIS_INFORMATION(ip=ip_address,
            asn=curTestInstance['asn'],
            asn_cidr_bgp=curTestInstance['asn_cidr_bgp'],
            asn_country=curTestInstance['ASCountry'],
            asn_registry=curTestInstance['asn_registry'],
            isp=curTestInstance['isp'],
            isp_country=curTestInstance['ISPCountry'],
            isp_city=curTestInstance['isp_city'],
            isp_region=curTestInstance['isp_region'])
        whois_model.save()
    except:
        print "Whois IP already exists, probably."


def get_whois_information(ip_address):
    cur_test_instance = {'asn': to_int(-1),
                       'asn_registry': to_string(""),
                       'asn_cidr_bgp': to_string(""),
                       'isp': to_string(""),
                       'isp_city': to_string(""),
                       'isp_region': to_string(""),
                       'ASCountry': to_string(""),
                       'ISPCountry': to_string(""),
                       'as_name': to_string(""),
                       'num_as_in_org': to_int(-1),
                       'num_ipv4_prefix_in_org': to_int(-1),
                       'num_ipv4_ip_in_org': to_int(-1),
                       'realcountry': to_string("")}

    #use whois info to get AS and ISP info

    #cached
    existing_ips = IP_WHOIS_INFORMATION.objects.filter(ip=ip_address)
    if existing_ips.count() > 0:
        #print "Cached WhoIS"
        existing_ip = existing_ips[0]
        cur_test_instance['asn'] = to_int(existing_ip.asn)
        cur_test_instance['asn_registry'] = to_string(existing_ip.asn_registry)
        cur_test_instance['asn_cidr_bgp'] = to_string(existing_ip.asn_cidr_bgp)
        cur_test_instance['isp'] = to_string(existing_ip.isp)
        cur_test_instance['isp_city'] = to_string(existing_ip.isp_city)
        cur_test_instance['isp_region'] = to_string(existing_ip.isp_region)
        cur_test_instance['ASCountry'] = to_string(existing_ip.asn_country)
        cur_test_instance['ISPCountry'] = to_string(existing_ip.isp_country)

        #use whois info to get AS and ISP info
        cur_test_instance['num_as_in_org'] = to_int(-1)
        cur_test_instance['num_ipv4_prefix_in_org'] = to_int(-1)
        cur_test_instance['num_ipv4_ip_in_org'] = to_int(-1)

        whois_as_info = Hints_AS_INFO.objects.filter(as_number=cur_test_instance['asn'])
        if whois_as_info.count() > 0:
            whois_as_info = whois_as_info[0]
            cur_test_instance['num_as_in_org'] = whois_as_info.num_as_in_org
            cur_test_instance['num_ipv4_prefix_in_org'] = whois_as_info.num_ipv4_prefix_in_org
            cur_test_instance['num_ipv4_ip_in_org'] = whois_as_info.num_ipv4_ip_in_org
            cur_test_instance['as_name'] = to_string(whois_as_info.as_name)
        return cur_test_instance

    # not cached
    ip_whois_result = get_whois_and_save(ip_address)
    if ip_whois_result is None:
        return cur_test_instance
    return ip_whois_result


def get_whois_and_save(ip_address):
    cur_test_instance = {}
    whoisinfo = get_whois_information_online(ip_address)
    if not whoisinfo:
        return None
    try:
        for k in whoisinfo:
            try:
                cur_test_instance[k] = to_string(whoisinfo[k])
            except:
                cur_test_instance[k] = to_int(whoisinfo[k])
        cur_test_instance['asn'] = to_int(cur_test_instance['asn'])
        cur_test_instance['ASCountry'] = geo_location_services.convert_country_code_to_name_nodict(cur_test_instance['ASCountry'])
        cur_test_instance['ISPCountry'] = geo_location_services.convert_country_code_to_name_nodict(cur_test_instance['ISPCountry'])
        cur_test_instance['isp_region'] = geo_location_services.convert_state_code_to_name(cur_test_instance['isp_region'])
        # get extended whois info
        whois_as_info = Hints_AS_INFO.objects.filter(as_number=cur_test_instance['asn'])
        if whois_as_info.count() > 0:
            whois_as_info = whois_as_info[0]
            cur_test_instance['num_as_in_org'] = whois_as_info.num_as_in_org
            cur_test_instance['num_ipv4_prefix_in_org'] = whois_as_info.num_ipv4_prefix_in_org
            cur_test_instance['num_ipv4_ip_in_org'] = whois_as_info.num_ipv4_ip_in_org
        save_whois_informantion_to_model(cur_test_instance, ip_address)
    except:
        traceback.print_exc()
        return None
    return cur_test_instance


def parse_whois_ip_information(ip, ip_object):
    asn = None
    asn_cidr_bgp = None
    asn_country = None
    asn_registry = None
    isp = None
    isp_country = None
    isp_city = None
    isp_region = None
    try:
        if 'asn' in ip_object:
            asn = int(ip_object['asn'])
    except:
        asn = -1
    if 'asn_cidr' in ip_object:
        asn_cidr_bgp = ip_object['asn_cidr']
    if 'asn_country_code' in ip_object:
        asn_country = ip_object['asn_country_code']
    if 'asn_registry' in ip_object:
        asn_registry = ip_object['asn_registry']
    subIPObject = ip_object['nets'][0]
    if 'country' in subIPObject:
        isp_country = subIPObject['country']
    if 'state' in subIPObject:
        isp_region = subIPObject['state']
    if 'city' in subIPObject:
        isp_city = subIPObject['city']
    if 'name' in subIPObject:
        isp = subIPObject['name']
    whois_information_dict = {"asn": asn,
                              "asn_registry": asn_registry,
                              "isp": isp, "isp_city": isp_city,
                              "isp_region": isp_region,
                              "ISPCountry": isp_country,
                              "ASCountry": asn_country,
                              "asn_cidr_bgp": asn_cidr_bgp}
    return whois_information_dict


def get_whois_information_online(ip_address):
    #print LOADED_CLASSIFIERS
    try:
        ip_obj = IPWhois(ip_address)
        ip_object = ip_obj.lookup()
        whois_information_dict = parse_whois_ip_information(ip_address, ip_object)
    except Exception, e:
        #print e
        #traceback.print_exc()
        whois_information_dict = {}
    return whois_information_dict



