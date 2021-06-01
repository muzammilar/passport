# -*- coding: utf-8 -*-
"""

    geosources.geolocation
    ~~~~~~~~~~~~~~~~~~~

    A module to connect and collect information from geolocation sources.
    This module contains the main functions to check and acquire information from all the
    geolocation sources and check for cache. It primarily contains the code for Maxmind,
    DBIP and IP2Location and calls the functions for EurekAPI and IPInfo. It also contain
    so utility functions.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from datetime import datetime
from ppstore.models import Hints_country_codes
from ppstore.models import Hints_state_codes
from ppstore.models import Hints_world_cities_pop_maxmind_geolite
from ppstore.models import Hints_country_lat_long
from ppstore.models import Loc_Source_DB_IP
from ppstore.models import Loc_Source_EUREKAPI
from ppstore.models import Loc_Source_IP2LOCATION
from ppstore.models import Loc_Source_IPINFO_IO
from ppstore.models import Loc_Source_MAXMIND_GEOLITE_CITY
from geosources import eurekapi
from geosources import ipinfo
from threading import Thread
import ppnamespace
import pputils


def convert_country_code_to_name(country_name, country_names_dict, skip):
    # first check
    if country_name is None:
        return ''
    country_name = country_name.split(',')[0]
    if str(country_name) in country_names_dict:
        return country_names_dict[country_name]
    if skip:  # don't skip for db_ip, ip_info, maxmind
        return country_name
    # second check was to
    return convert_country_code_to_name_nodict(country_name)


def convert_country_code_to_name_nodict(country_name):
    cntry = Hints_country_codes.objects.filter(iso_two_code__iexact=country_name)
    if cntry.count() == 0:
        return country_name
    country_name = cntry[0].country
    return country_name


def convert_state_code_to_name(st_name):  # maxmind only
    st = Hints_state_codes.objects.filter(ansi__iexact=st_name)
    if st.count() > 0:
        return st[0].state
    st = Hints_state_codes.objects.filter(uscg__iexact=st_name)
    if st.count() > 0:
        return st[0].state
    return st_name


def get_lat_lon_country_only(country1):
    lat = None
    lon = None
    x = Hints_country_lat_long.objects.filter(country=country1)
    if x.count() == 0:
        return lat, lon
    x = x[0]
    lat = x.latitude
    lon = x.longitude
    return lat, lon



def get_lat_lon_with_state(country1, region1):
    lat = None
    lon = None
    x = Hints_world_cities_pop_maxmind_geolite.objects.filter(country__iexact=country1,
        region__iexact=region1)
    if x.count() == 0:
        return lat, lon
    x = x[0]
    lat = x.latitude
    lon = x.longitude
    return lat, lon


def get_lat_lon_with_city(country1, city1):
    lat = None
    lon = None
    x = Hints_world_cities_pop_maxmind_geolite.objects.filter(country__iexact=country1,
        city__iexact=city1)
    if x.count() == 0:
        return lat, lon
    x = x[0]
    lat = x.latitude
    lon = x.longitude
    return lat, lon


def get_lat_lon_with_city_and_state(country1, region1, city1):
    lat = None
    lon = None
    x = Hints_world_cities_pop_maxmind_geolite.objects.filter(country__iexact=country1,
        city__iexact=city1, region__iexact=region1)
    if x.count() == 0:
        return lat, lon
    x = x[0]
    lat = x.latitude
    lon = x.longitude
    return lat, lon


def get_lat_lon_coordinates(country, region, city):  # ip2location, maxmind
    lat, lon = get_lat_lon_with_city_and_state(country, region, city)
    if lat is None or lon is None:
        lat, lon = get_lat_lon_with_city(country, city)
    if lat is None or lon is None:
        lat, lon = get_lat_lon_with_state(country, region)
    if lat is None or lon is None:
        lat, lon = get_lat_lon_country_only(country)
    return lat, lon


def save_ip2location_model(data, country_names_dict):
    cntry = ''
    cntry = convert_country_code_to_name(data[1], country_names_dict, True)
    reg = data[2]
    cit = data[3]
    lat, lon = float(data[6]), float(data[7])
    try:
        ip2lc = Loc_Source_IP2LOCATION(ip=data[0], country=cntry, region=reg,
            city=cit, isp=data[4], Time=datetime.now(), latitude=lat,
            longitude=lon)
        ip2lc.save()
    except:
        print "Error saving IP2Location. It may already exist"
    return cntry


def save_eurekapi_model(data, country_names_dict):
    cntry = ''
    cntry = convert_country_code_to_name(data[1], country_names_dict, True)
    try:
        eapi = Loc_Source_EUREKAPI(ip=data[0], country=cntry, region=data[2],
            city=data[3], isp=data[4], organization=data[5],
            Time=datetime.now(), latitude=float(data[6]),
            longitude=float(data[7]))
        eapi.save()
    except:
        print "Error saving EurekAPI. It may already exist"
    return cntry


def save_dbip_model(data, country_names_dict):
    cntry = ''
    cntry = convert_country_code_to_name(data[1], country_names_dict, False)
    lat, lon = float(data[6]), float(data[7])
    try:
        dbIp = Loc_Source_DB_IP(ip=data[0], country=cntry, region=data[2],
            city=data[3], isp=data[4], organization=data[5],
            Time=datetime.now(), latitude=float(data[6]),
            longitude=float(data[7]))
        dbIp.save()
    except:
        print "Error saving DBIP. It may already exist"
    return cntry


def save_ipinfo_model(data, country_names_dict):
    cntry = ''
    cntry = convert_country_code_to_name(data[1], country_names_dict, False)
    postalCode = 0
    lat = float(data[6])
    lon = float(data[7])
    try:
        ipinfo = Loc_Source_IPINFO_IO(ip=data[0], country=cntry, region=data[2],
            city=data[3], postal_code=postalCode, organization=data[5],
            Time=datetime.now(), latitude=lat, longitude=lon)
        ipinfo.save()
    except:
        print "Error saving IPInfo. It may already exist"
    return cntry


def save_maxmind_model(data, country_names_dict):
    cntry = ''
    cntry = convert_country_code_to_name(str(data[1]), country_names_dict, False)
    reg = convert_state_code_to_name(data[2])
    cit = data[3]
    lat, lon = float(data[6]), float(data[7])
    postalCode = 0
    aCode = 0
    try:
        mm = Loc_Source_MAXMIND_GEOLITE_CITY(ip=data[0], country=cntry,
            region=reg, area_code=aCode,
            city=cit, postal_code=postalCode,
            Time=datetime.now(), latitude=lat,
            longitude=lon)
        mm.save()
    except:
        print "Error saving Maxmind. It may already exist"
    return cntry


def in_cache(ip_address):
    loc_dict = {}
    db_ip_cache = Loc_Source_DB_IP.objects.filter(ip=ip_address)
    if db_ip_cache.count() == 0:
        return False
    return True


def try_cache(ip_address):
    loc_dict = {}
    db_ip_cache = Loc_Source_DB_IP.objects.filter(ip=ip_address)
    if db_ip_cache.count() == 0:
        return None
    print "Cached GeoSource"
    loc_dict['ipinfo_country'] = ''
    loc_dict['ip2location_country'] = ''
    loc_dict['maxmind_country'] = ''
    loc_dict['eurekapi_country'] = ''
    db_ip_cache = db_ip_cache[0]
    loc_dict['db_ip_country'] = db_ip_cache.country
    src_cache = Loc_Source_IPINFO_IO.objects.filter(ip=ip_address)
    if src_cache.count() > 0:
        loc_dict['ipinfo_country'] = src_cache[0].country
    src_cache = Loc_Source_IP2LOCATION.objects.filter(ip=ip_address)
    if src_cache.count() > 0:
        loc_dict['ip2location_country'] = src_cache[0].country
    src_cache = Loc_Source_EUREKAPI.objects.filter(ip=ip_address)
    if src_cache.count() > 0:
        loc_dict['eurekapi_country'] = src_cache[0].country
    src_cache = Loc_Source_MAXMIND_GEOLITE_CITY.objects.filter(ip=ip_address)
    if src_cache.count() > 0:
        loc_dict['maxmind_country'] = src_cache[0].country
    return loc_dict


def get_geosources_maxmind_db_ip(ip_address):
    ip_int = pputils.ip_string_to_int(ip_address)
    #dbip
    temp = ppnamespace.DBIP_INTERVAL_TREE[ip_int]
    max_val = float('inf')
    cntry = ''
    for val in temp:
        if val.end - val.begin < max_val:
            max_val = val.end - val.begin
            cntry = val.data
    dbip_cntry_val = cntry
    if not cntry == "":
        try:
            mm = Loc_Source_DB_IP(ip=ip_address, country=cntry,
                Time=datetime.now())
            mm.save()
        except:
            #print "Error saving DBIP. It may already exist"
            pass
    #maxmind
    cntry = ''
    if ip_int in ppnamespace.MAXMIND_DICT:
        cntry = ppnamespace.MAXMIND_DICT[ip_int]
    else:
        temp = ppnamespace.MAXMIND_INTERVAL_TREE[ip_int]
        max_val = float('inf')
        cntry = ''
        for val in temp:
            if val.end - val.begin < max_val:
                max_val = val.end - val.begin
                cntry = val.data
    mm_cntry_val = cntry
    if not cntry == "":
        try:
            mm = Loc_Source_MAXMIND_GEOLITE_CITY(ip=ip_address, country=cntry,
                Time=datetime.now())
            mm.save()
        except:
            #print "Error saving MaxMind. It may already exist"
            pass
    # compare both    
    if dbip_cntry_val.lower() == mm_cntry_val.lower():
        return dbip_cntry_val
    if len(mm_cntry_val) == 0:
        return dbip_cntry_val
    if len(dbip_cntry_val) == 0:
        return mm_cntry_val    
    return ''


def get_other_geo_sources(ip_address, loc_sc_dict):
    ip_int = pputils.ip_string_to_int(ip_address)
    #ip2location
    temp = ppnamespace.IP2LOCATION_INTERVAL_TREE[ip_int]
    max_val = float('inf')
    cntry = ''
    for val in temp:
        if val.end - val.begin < max_val:
            max_val = val.end - val.begin
            cntry = val.data
    loc_sc_dict['ip2location_country'] = cntry
    if not cntry == "":
        try:
            mm = Loc_Source_IP2LOCATION(ip=ip_address, country=cntry,
                Time=datetime.now())
            mm.save()
        except:
            #print "Error saving IP2Location. It may already exist"
            pass

    #dbip
    temp = ppnamespace.DBIP_INTERVAL_TREE[ip_int]
    max_val = float('inf')
    cntry = ''
    for val in temp:
        if val.end - val.begin < max_val:
            max_val = val.end - val.begin
            cntry = val.data
    loc_sc_dict['db_ip_country'] = cntry
    if not cntry == "":
        try:
            mm = Loc_Source_DB_IP(ip=ip_address, country=cntry,
                Time=datetime.now())
            mm.save()
        except:
            #print "Error saving DBIP. It may already exist"
            pass

    #maxmind
    cntry = ''
    if ip_int in ppnamespace.MAXMIND_DICT:
        cntry = ppnamespace.MAXMIND_DICT[ip_int]
    else:
        temp = ppnamespace.MAXMIND_INTERVAL_TREE[ip_int]
        max_val = float('inf')
        cntry = ''
        for val in temp:
            if val.end - val.begin < max_val:
                max_val = val.end - val.begin
                cntry = val.data
    loc_sc_dict['maxmind_country'] = cntry
    if not cntry == "":
        try:
            mm = Loc_Source_MAXMIND_GEOLITE_CITY(ip=ip_address, country=cntry,
                Time=datetime.now())
            mm.save()
        except:
            #print "Error saving MaxMind. It may already exist"
            pass


def get_inaccurate_locations(ip_address, skip_cache=False):
    cached_result = None
    if not skip_cache:
        cached_result = try_cache(ip_address)
    if cached_result is not None:
        return cached_result
    country_names_dict = {'Aland Islands': 'Finland', 'Aland Island': 'Finland',
        'viet nam': 'Vietnam', 'Viet Nam': 'Vietnam',
        'Korea, Republic Of': 'South Korea',
        'Korea, Republic of': 'South Korea',
        'Iran, Islamic Republic Of': 'Iran',
        'Iran, Islamic Republic of': 'Iran',
        'Taiwan, Province Of China': 'Taiwan', 'Russian Federation': 'Russia'}
    loc_sc_dict = {'db_ip_country': '', 'ipinfo_country': '',
        'ip2location_country': '', 'maxmind_country': '',
        'eurekapi_country': ''}
    # start eurekapi
    t1 = Thread(target=(eurekapi.get_info), args=(ip_address, loc_sc_dict,))
    t1.start()
    # start ipinfo
    t2 = Thread(target=(ipinfo.get_info), args=(ip_address, loc_sc_dict,))
    t2.start()
    # look into others, don't save them
    get_other_geo_sources(ip_address, loc_sc_dict)
    # join eurekapi
    t1.join()
    # join ipinfo
    t2.join()
    return loc_sc_dict


if __name__ == "__main__":
    get_inaccurate_locations("1.1.1.1")
