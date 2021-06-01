# -*- coding: utf-8 -*-
"""

    ppstore.traindata
    ~~~~~~

    This module has been developed to be used as wrapper to read the ground truth
    training data as well as reading the data stored in the local database from
    multiple geolocation services. This is the primary module to read the training
    dataset for the classifiers, and read the cached information about an
    IP address (hostname, country predicted by geolocation services,
    WhoIS information, etc) from the database.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""


import json
import urllib2
import requests
###remove-me-later-muz######remove-me-later-muz###import ormsettings as DJANGO_SETTINGS   # don't remove
###remove-me-later-muz######remove-me-later-muz###from django.db import models
###remove-me-later-muz###from django.db.models import Q
from django.db.models import Count as databaseCount

from ppstore.models import DDEC_Hostname
from ppstore.models import Hints_DDEC_Location_Lat_Long
from ppstore.models import IP_WHOIS_INFORMATION
from ppstore.models import Hints_AS_INFO
from ppstore.models import Loc_Source_DB_IP
from ppstore.models import Loc_Source_EUREKAPI
from ppstore.models import Loc_Source_IP2LOCATION
from ppstore.models import Loc_Source_IPINFO_IO
from ppstore.models import Loc_Source_MAXMIND_GEOLITE_CITY
from ppstore.models import CLASSIFIER_DATA_TRAIN
from ppstore.models import CLASSIFIER_DATA_TRAIN_OPENIPMAP
from ppstore.models import CLASSIFIER_DATA_TRAIN_GROUND
from ppmeasurements.util import is_private_ip

# change this code to connect to the database directly.
# this function either gets data from the database or the server. and returns a python object.


def to_string(x):
    if x is None:
        return ''
    return str(x.encode('unicode-escape'))


def to_int(x):
    if x is None:
        return -1
    return x


# legacy function. It has been depricated.
def get_training_data_all():
    cls_hosts = CLASSIFIER_DATA_TRAIN.objects.all()
    training_data = []
    for cur_host in cls_hosts:
        cur_train_instance = {'ip': to_string(cur_host.ip),
                              'asn': to_int(cur_host.asn),
                              'asn_registry': to_string(cur_host.asn_registry),
                              'isp': to_string(cur_host.isp),
                              'isp_city': to_string(cur_host.isp_city),
                              'isp_region': to_string(cur_host.isp_region),
                              'DDECCountry': to_string(cur_host.DDECcountry),
                              'ASCountry': to_string(cur_host.AScountry),
                              'ISPCountry': to_string(cur_host.ISPcountry),
                              'db_ip_country': to_string(cur_host.db_ip_country),
                              'eurekapi_country': to_string(cur_host.eurekapi_country),
                              'ip2location_country': to_string(cur_host.ip2location_country),
                              'ipinfo_country': to_string(cur_host.ipinfo_country),
                              'maxmind_country': to_string(cur_host.maxmind_country),
                              'as_name': to_string(cur_host.as_name),
                              'num_as_in_org': to_int(cur_host.num_as_in_org),
                              'num_ipv4_prefix_in_org': to_int(cur_host.num_ipv4_prefix_in_org),
                              'num_ipv4_ip_in_org': to_int(cur_host.num_ipv4_ip_in_org),
                              'realcountry': to_string(cur_host.realcountry)}
        #cur_train_instance['asn_cidr_bgp'] = getString(cur_host.asn_cidr_bgp)
        #cur_train_instance['hostname'] = getString(cur_host.hostname)
        training_data.append(cur_train_instance)
    return training_data


def get_training_data_all_openipmap():
    return  get_training_data_all_table(CLASSIFIER_DATA_TRAIN_OPENIPMAP)


def get_training_data_all_ground():
    return get_training_data_all_table(CLASSIFIER_DATA_TRAIN_GROUND)


def get_training_data_all_table(TABLE_NAME):
    cls_hosts = TABLE_NAME.objects.all()
    training_data = []
    for cur_host in cls_hosts:
        cur_train_instance = {'ip': to_string(cur_host.ip),
                              'asn': to_int(cur_host.asn),
                              'asn_registry': to_string(cur_host.asn_registry),
                              'isp': to_string(cur_host.isp),
                              'isp_city': to_string(cur_host.isp_city),
                              'isp_region': to_string(cur_host.isp_region),
                              'DDECCountry': to_string(cur_host.DDECcountry),
                              'ASCountry': to_string(cur_host.AScountry),
                              'ISPCountry': to_string(cur_host.ISPcountry),
                              'db_ip_country': to_string(cur_host.db_ip_country),
                              'eurekapi_country': to_string(cur_host.eurekapi_country),
                              'ip2location_country': to_string(cur_host.ip2location_country),
                              'ipinfo_country': to_string(cur_host.ipinfo_country),
                              'maxmind_country': to_string(cur_host.maxmind_country),
                              'as_name': to_string(cur_host.as_name),
                              'num_as_in_org': to_int(cur_host.num_as_in_org),
                              'num_ipv4_prefix_in_org': to_int(cur_host.num_ipv4_prefix_in_org),
                              'num_ipv4_ip_in_org': to_int(cur_host.num_ipv4_ip_in_org),
                              'realcountry': to_string(cur_host.realcountry)}
        #cur_train_instance['asn_cidr_bgp'] = getString(cur_host.asn_cidr_bgp)
        #cur_train_instance['hostname'] = getString(cur_host.hostname)
        training_data.append(cur_train_instance)
    return training_data



def get_training_data_country(country_info):
    country = country_info["country"]
    cls_hosts = CLASSIFIER_DATA_TRAIN.objects.filter(realcountry__iexact=country)

    training_data = []
    for cur_host in cls_hosts:
        cur_train_instance = {'ip': to_string(cur_host.ip),
                              'asn': to_int(cur_host.asn),
                              'asn_registry': to_string(cur_host.asn_registry),
                              'isp': to_string(cur_host.isp),
                              'isp_city': to_string(cur_host.isp_city),
                              'isp_region': to_string(cur_host.isp_region),
                              'DDECCountry': to_string(cur_host.DDECcountry),
                              'ASCountry': to_string(cur_host.AScountry),
                              'ISPCountry': to_string(cur_host.ISPcountry),
                              'db_ip_country': to_string(cur_host.db_ip_country),
                              'eurekapi_country': to_string(cur_host.eurekapi_country),
                              'ip2location_country': to_string(cur_host.ip2location_country),
                              'ipinfo_country': to_string(cur_host.ipinfo_country),
                              'maxmind_country': to_string(cur_host.maxmind_country),
                              'as_name': to_string(cur_host.as_name),
                              'num_as_in_org': to_int(cur_host.num_as_in_org),
                              'num_ipv4_prefix_in_org': to_int(cur_host.num_ipv4_prefix_in_org),
                              'num_ipv4_ip_in_org': to_int(cur_host.num_ipv4_ip_in_org),
                              'realcountry': to_string(cur_host.realcountry)}
        #cur_train_instance['asn_cidr_bgp'] = getString(cur_host.asn_cidr_bgp)
        #cur_train_instance['hostname'] = getString(cur_host.hostname)
        training_data.append(cur_train_instance)
    return training_data


def get_all_countries():
    country_count_hsts = CLASSIFIER_DATA_TRAIN.objects.all().values(
        'realcountry').annotate(total=databaseCount('realcountry'))
    country_count_list = []
    for cntry in country_count_hsts:
        if cntry['realcountry'] == '':
            continue
        cc_dict = {"country": cntry['realcountry'],
            "count": cntry['total']}
        country_count_list.append(cc_dict)
    #print "Total Train Countries: ", len(country_count_list)
    return country_count_list

def get_ground_truth_all():
    cls_hosts = CLASSIFIER_DATA_TRAIN.objects.all()
    real_dict = {}
    for cur_host in cls_hosts:
        ip_addr = to_string(cur_host.ip)
        if is_private_ip(ip_addr):
            continue
        realcountry = to_string(cur_host.realcountry)
        real_dict[ip_addr] = realcountry
    return real_dict


def get_all_test_data():
    # this funciton is incomplete and doesn't work
    testing_data = []
    all_hsts = []
    for cur_hst in all_hsts:
        ip_str = cur_hst.ip
        hst_nm = cur_hst.hostname
        cur_train_instance = {}
        cur_train_instance['ip'] = ip_str
        try:
            host_objs = DDEC_Hostname.objects.filter(hostname=hst_nm)
            loc = host_objs[0].location
            x = Hints_DDEC_Location_Lat_Long.objects.filter(location=loc)
            cur_train_instance['DDECCountry'] = to_string(x.country)
        except:
            cur_train_instance['DDECCountry'] = to_string('')
        try:
            cur_train_instance['db_ip_country'] = Loc_Source_DB_IP.objects.filter(ip=ip_str)[0].country
        except:
            cur_train_instance['db_ip_country'] = ''
        try:
            cur_train_instance['ipinfo_country'] = Loc_Source_IPINFO_IO.objects.filter(ip=ip_str)[0].country
        except:
            cur_train_instance['ipinfo_country'] = ''
        try:
            cur_train_instance['eurekapi_country'] = Loc_Source_EUREKAPI.objects.filter(ip=ip_str)[0].country
        except:
            cur_train_instance['eurekapi_country'] = ''
        try:
            cur_train_instance['ip2location_country'] = Loc_Source_IP2LOCATION.objects.filter(ip=ip_str)[0].country
        except:
            cur_train_instance['ip2location_country'] = ''
        try:
            cur_train_instance['maxmind_country'] = Loc_Source_MAXMIND_GEOLITE_CITY.objects.filter(ip=ip_str)[0].country
        except:
            cur_train_instance['maxmind_country'] = ''
        asn_num = -1
        try:
            ip_object = IP_WHOIS_INFORMATION.objects.filter(ip=ip_str)[0]
            asn_num = ip_object.asn
            cur_train_instance['asn'] = ip_object.asn
            cur_train_instance['asn_registry'] = ip_object.asn_registry
            cur_train_instance['isp'] = ip_object.isp
            cur_train_instance['isp_city'] = ip_object.isp_city
            cur_train_instance['isp_region'] = ip_object.isp_region
            cur_train_instance['ISPCountry'] = ip_object.isp_country
            cur_train_instance['ASCountry'] = ip_object.asn_country
        except:
            cur_train_instance['asn_registry'] = ''
            cur_train_instance['isp'] = ''
            cur_train_instance['isp_city'] = ''
            cur_train_instance['isp_region'] = ''
            cur_train_instance['ISPCountry'] = ''
            cur_train_instance['ASCountry'] = ''
            cur_train_instance['asn'] = -1

        try:
            asn_object = Hints_AS_INFO.objects.filter(as_number=asn_num)[0]
            cur_train_instance['as_name'] = asn_object.as_name
            cur_train_instance['num_as_in_org'] = asn_object.num_as_in_org
            cur_train_instance['num_ipv4_prefix_in_org'] = asn_object.num_ipv4_prefix_in_org
            cur_train_instance['num_ipv4_ip_in_org'] = asn_object.num_ipv4_ip_in_org
        except:
            cur_train_instance['as_name'] = ''
            cur_train_instance['num_as_in_org'] = -1
            cur_train_instance['num_ipv4_prefix_in_org'] = -1
            cur_train_instance['num_ipv4_ip_in_org'] = -1
        testing_data.append(cur_train_instance)
    return testing_data


def get_test_data(ip_str,host_name=''):
    hst_nm = host_name
    cur_train_instance = {}
    cur_train_instance['ip'] = ip_str
    try:
        host_objs = DDEC_Hostname.objects.filter(hostname=hst_nm)
        loc = host_objs[0].location
        x = Hints_DDEC_Location_Lat_Long.objects.filter(location=loc)
        cur_train_instance['DDECCountry'] = to_string(x.country)
    except:
        cur_train_instance['DDECCountry'] = to_string('')
    try:
        cur_train_instance['db_ip_country'] = Loc_Source_DB_IP.objects.filter(ip=ip_str)[0].country
    except:
        cur_train_instance['db_ip_country'] = ''
    try:
        cur_train_instance['ipinfo_country'] = Loc_Source_IPINFO_IO.objects.filter(ip=ip_str)[0].country
    except:
        cur_train_instance['ipinfo_country'] = ''
    try:
        cur_train_instance['eurekapi_country'] = Loc_Source_EUREKAPI.objects.filter(ip=ip_str)[0].country
    except:
        cur_train_instance['eurekapi_country'] = ''
    try:
        cur_train_instance['ip2location_country'] = Loc_Source_IP2LOCATION.objects.filter(ip=ip_str)[0].country
    except:
        cur_train_instance['ip2location_country'] = ''
    try:
        cur_train_instance['maxmind_country'] = Loc_Source_MAXMIND_GEOLITE_CITY.objects.filter(ip=ip_str)[0].country
    except:
        cur_train_instance['maxmind_country'] = ''
    asn_num = -1
    try:
        ip_object = IP_WHOIS_INFORMATION.objects.filter(ip=ip_str)[0]
        asn_num = ip_object.asn
        cur_train_instance['asn'] = ip_object.asn
        cur_train_instance['asn_registry'] = ip_object.asn_registry
        cur_train_instance['isp'] = ip_object.isp
        cur_train_instance['isp_city'] = ip_object.isp_city
        cur_train_instance['isp_region'] = ip_object.isp_region
        cur_train_instance['ISPCountry'] = ip_object.isp_country
        cur_train_instance['ASCountry'] = ip_object.asn_country
    except:
        cur_train_instance['asn_registry'] = ''
        cur_train_instance['isp'] = ''
        cur_train_instance['isp_city'] = ''
        cur_train_instance['isp_region'] = ''
        cur_train_instance['ISPCountry'] = ''
        cur_train_instance['ASCountry'] = ''
        cur_train_instance['asn'] = -1

    try:
        asn_object = Hints_AS_INFO.objects.filter(as_number=asn_num)[0]
        cur_train_instance['as_name'] = asn_object.as_name
        cur_train_instance['num_as_in_org'] = asn_object.num_as_in_org
        cur_train_instance['num_ipv4_prefix_in_org'] = asn_object.num_ipv4_prefix_in_org
        cur_train_instance['num_ipv4_ip_in_org'] = asn_object.num_ipv4_ip_in_org
    except:
        cur_train_instance['as_name'] = ''
        cur_train_instance['num_as_in_org'] = -1
        cur_train_instance['num_ipv4_prefix_in_org'] = -1
        cur_train_instance['num_ipv4_ip_in_org'] = -1
    return cur_train_instance
