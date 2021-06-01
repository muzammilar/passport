# -*- coding: utf-8 -*-
"""

    geosources.ipinfo
    ~~~~~~~~~~~~~~~~~

    This module contains the function to connect to the online API for IPInfo and
    save the data retrieved.


    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import time
from datetime import datetime
import json
import urllib2 as urlopenner
import ppnamespace
###remove-me-later-muz###import ormsettings as DJANGO_SETTINGS
from ppstore.models import Loc_Source_IPINFO_IO
import traceback
import pputils
import configs.traceroutes

def save_ipinfo_model(data):
    cntry = ''
    try:
        cntry = pputils.get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT,
                                                       data["country"])
        try:
            cntry = pputils.get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND,
                                                           cntry)
        except:
            pass
        ipinfo = Loc_Source_IPINFO_IO(ip=data["ip"], country=cntry,
            region=data["region"], city=data["city"], organization=data["org"],
            Time=datetime.now(), latitude=data["latitude"],
            longitude=data["longitude"],
            hostname=data["hostname"])
        ipinfo.save()
    except:
        print "Error saving IPInfo. It may already exist"
        #traceback.print_exc()
    return cntry


def transform_data_to_ipinfo_standard(obj):
    data = {}
    keys = ["ip", "country", "region", "city", "org", "hostname", "loc"]
    for key in keys:
        if key in obj:
            data[key] = obj[key]
        else:
            data[key] = ""
        try:
            data["postal"] = int(obj["postal"])
        except:
            data["postal"] = 0
    data["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        x = data["loc"].split(",")
        data["latitude"] = float(x[0])
        data["longitude"] = float(x[1])
    except:
        data["latitude"] = 0
        data["longitude"] = 0
    return data


def try_cache_ip_info(ip_address):
    loc_dict = {}
    ip_info_cache = Loc_Source_IPINFO_IO.objects.filter(ip=ip_address)
    if ip_info_cache.count() == 0:
        return None
    ip_info_instance = ip_info_cache[0]
    loc_dict["ip"] = ip_info_instance.ip
    loc_dict["country"] = ip_info_instance.country
    loc_dict["region"] = ip_info_instance.region
    loc_dict["city"] = ip_info_instance.city
    loc_dict["org"] = ip_info_instance.organization
    loc_dict["hostname"] = ip_info_instance.hostname
    loc_dict["loc"] = ""
    loc_dict["postal"] = 0
    loc_dict["timestamp"] = ip_info_instance.Time
    loc_dict["latitude"] = ip_info_instance.latitude
    loc_dict["longitude"] = ip_info_instance.longitude
    return loc_dict


def get_info(ip_address, loc_src_dict):
    try:
        search_address = "http://ipinfo.io/" + ip_address + "/json?token=" + configs.traceroutes.IPINFO_IO_TOKEN
        retrieved_json = urlopenner.urlopen(search_address).read()
        unstructured_data = json.loads(retrieved_json)
        data = transform_data_to_ipinfo_standard(unstructured_data)
        cntry = save_ipinfo_model(data)
        loc_src_dict['ipinfo_country'] = cntry
        return cntry
    except:
        #print "Error Accessing IPInfo site!"
        loc_src_dict['ipinfo_country'] = ''
        return ''

def get_info_object(ip_address):
    try:
        search_address = "http://ipinfo.io/" + ip_address + "/json?token=" + configs.traceroutes.IPINFO_IO_TOKEN
        retrieved_json = urlopenner.urlopen(search_address).read()
        unstructured_data = json.loads(retrieved_json)
        data = transform_data_to_ipinfo_standard(unstructured_data)
        cntry = save_ipinfo_model(data)
        return data
    except:
        traceback.print_exc()
        return None


def get_info_cached(ip_address):
    if type(ip_address) is int:
        ip_address = pputils.ip_int_to_string(ip_address)
    info = try_cache_ip_info(ip_address)
    if info is None:
        return get_info_object(ip_address)
    return info

if __name__ == "__main__":
    #parseHTML("")
    get_info("154.235.123.1")
