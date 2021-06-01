# -*- coding: utf-8 -*-
"""

    geosources.eurekapi
    ~~~~~~~~~~~~~~~~~~~

    This module contains the function to connect to the online API for EurekAPI and save the data retrieved.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import time
from datetime import datetime
import json
import urllib2 as urlopenner
import pputils
###remove-me-later-muz###import ormsettings as DJANGO_SETTINGS
from ppstore.models import Loc_Source_EUREKAPI
import ppnamespace
import configs.traceroutes

def save_eurekapi_model(data):
    cntry = ''
    if not data:
        return cntry
    try:
        cntry = pputils.get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT,
                                                       data["country_code_iso3166alpha2"])
        try:
            cntry = pputils.get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND,
                                                           cntry)
        except:
            pass
        eapi = Loc_Source_EUREKAPI(ip=data["ip_address"], country=cntry,
            region=data["region_name"],
            city='', isp='', organization='',
            Time=datetime.now(), latitude=0.0, longitude=0.0)
        eapi.save()
    except:
        print "Error saving EurekAPI. It may already exist"
    return cntry


def transform_to_structured_data(obj):
    data = {}
    # if query status is okay.
    if obj["query_status"]["query_status_code"] != "OK":
        return {}
    keys = ["country_code_iso3166alpha2", "country_name", "region_name"]
    data["ip_address"] = obj["ip_address"]
    for key in keys:
        obj_data = obj["geolocation_data"]
        if key in obj_data:
            data[key] = obj_data[key]
        else:
            data[key] = ""
    data["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')
    return data


# You don't need locks: Here's why: https://stackoverflow.com/questions/1312331/using-a-global-dictionary-with-threads-in-python
def get_info(ip_address, loc_src_dict):
    try:
        cntry = ''
        search_address = "http://api.apigurus.com/iplocation/v1.8/locateip?key=" + \
                         configs.traceroutes.EUREKAPI_KEY + "&ip=" + ip_address + "&format=JSON"
        retrieved_json = urlopenner.urlopen(search_address).read()
        unstructured_data = json.loads(retrieved_json)
        #print unstructured_data
        data = transform_to_structured_data(unstructured_data)
        cntry = save_eurekapi_model(data)
        loc_src_dict['eurekapi_country'] = cntry
        return cntry
    except:
        #traceback.print_exc()
        #print "Error Accessing EurekAPI Site!"
        loc_src_dict['eurekapi_country'] = ''
        return ''


if __name__ == "__main__":
    get_info("154.235.123.1")
