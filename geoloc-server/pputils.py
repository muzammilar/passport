# -*- coding: utf-8 -*-
"""

    pputils.py
    ~~~~~~~~~~~~~~

    This module contains utility functions extensively used in Passport

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

###remove-me-later-muz######remove-me-later-muz###import ormsettings as DJANGO_SETTINGS
from ppstore.models import Hints_country_codes
from ppstore.models import Hints_country_lat_long
from ppstore.models import Hints_world_cities_pop_maxmind_geolite
import random
import os
import csv
import configs.system
import ppnamespace
import netaddr as ipaddress
from intervaltree import IntervalTree

def get_country_name_from_lat_lon(lat, lon):
    """
    Gets the coutnry name for a speicific latitude and longitude pair using the database

    :param lat: A float from -90 to 90 containing latitude
    :param lon: A float from -180 to 180 containing longitude
    :return: The country name for that lat-lon pair
    """
    not_found = True
    error_diff = 0.001
    multfactor = 5
    loc = None
    # incrementally incrase the error difference until a country is found
    while not_found:  #get some random country.
        if error_diff > 1:
            return None
        try:
            loc_tup_list = Hints_world_cities_pop_maxmind_geolite.objects.filter(
                latitude__gte=lat - error_diff, latitude__lte=lat + error_diff,
                longitude__gte=lon - error_diff/2.0, longitude__lte=lon + error_diff/2.0)
            loc = loc_tup_list[0]
            not_found = False
            #print "Found!", error_diff
        except:
                not_found = True
                error_diff = error_diff * multfactor
    if loc is None:
        return ""
    return loc.country


def get_country_name_from_iso_code(data_dict, country_code):
    """
    Returns the Passport-statndard coutnry name from a given country code (fast)

    :param data_dict: Dictionary containing mappy of ISO-2 country codes to country names
    :param country_code: the country code (two characters capitalized)
    :return: The country name if found, otherwise the original country code (string)
    """
    try:
        country_nm = data_dict[str(country_code)]
        return str(country_nm)
    except:
        return str(country_code)


def get_country_name_from_code(country_name):
    """
    Returns the Passport-statndard coutnry name from a given country code using a database (slow)

    :param country_name: the country code (two characters capitalized)
    :return: The country name if found, otherwise the original country code (string)
    """
    cntry = Hints_country_codes.objects.filter(iso_two_code__iexact=country_name)
    if cntry.count() == 0:
        return country_name
    country_name = cntry[0].country
    return country_name


def get_country_name_iso_code_dict(data_dict):
    """
    Loads all the country codes and their respective names into a dictionary

    :param data_dict: An empty dictionary {}
    :return: A dictionary containing {"AA": "Country Name", ....} with two-letter keys and country names as values
    """

    countries = Hints_country_codes.objects.all()
    for cntry in countries:
        data_dict[cntry.iso_two_code.upper()] = cntry.country
    return data_dict


def get_country_continent_dict():
    """ Returns a dictionary that maps a country name (not code) to a continent"""
    data_dict = {}
    countries = Hints_country_codes.objects.all()
    for cntry in countries:
        data_dict[cntry.country] = cntry.continent
    return data_dict


def get_country_lat_lon_dict():
    """
    Returns a dictionary that maps a country a single lat-lon point (though countries are borders this function returns
    a single point in the country)

    :return: A dictionary containing
        {"country 1":
              {"lat": 1.0, "lon": 1.0}
         ....
        }
    """

    cntry_lat_db = Hints_country_lat_long.objects.all()
    lat_long_dict = {}
    for entry in cntry_lat_db:
        lat_lon = {'lat':entry.latitude, 'lon':entry.longitude}
        lat_long_dict[entry.country] = lat_lon
    return lat_long_dict


def ip_string_to_int(ipstr):
    """ Convert a string IPv4 address to integer"""
    if ipstr == '':
        return 0
    if len(ipstr) > 15: # max len of ipv4 in string (could be less)
        #print "Damn:", ipstr
        return 0 
    parts = ipstr.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + \
                                            (int(parts[2]) << 8) + int(parts[3])


def ip_int_to_string(ipint):
    """Convert an integer to a string IPv4 address"""
    if ipint > 4294967295: #255.255.255.255
        return ''
    x4 = ipint % 256
    ipint = ipint >> 8
    x3 = ipint % 256
    ipint = ipint >> 8
    x2 = ipint % 256
    ipint = ipint >> 8
    x1 = ipint % 256
    return str(x1) + "." + str(x2) + "." + str(x3) + "." + str(x4)


def get_random_color():
    """
    Get a random color value as a string

    :return: A color value as a string
    """
    r = lambda: random.randint(0,255)  # lambda function
    color = '#%02X%02X%02X' % (r(),r(),r())
    return color


def read_values_to_geo_sources():
    """
    Load all the LOCAL geolcation sources (Maxmind, DBIP and IP2Location) into the memory
    """
    filepath = os.path.join(configs.system.PROJECT_ROOT, configs.system.DIR_DATA,
                                                   configs.system.SRC_MAXMIND_LOC_INFO)
    maxmind_loc_id = {}
    with open(filepath, "rb") as mmfile:
        csvreader = csv.reader(mmfile)
        for line in csvreader:
            x1 = int(line[0])
            maxmind_loc_id[x1] = get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT, line[4])

    filepath = os.path.join(configs.system.PROJECT_ROOT, configs.system.DIR_DATA,
                                                           configs.system.SRC_MAXMIND)
    ppnamespace.MAXMIND_INTERVAL_TREE = IntervalTree()
    with open(filepath, "rb") as mmfile:
        csvreader = csv.reader(mmfile)
        for line in csvreader:
            prf = ipaddress.IPNetwork(unicode(line[0]))
            try:
                cntry = maxmind_loc_id[int(line[1])]
            except:
                cntry = ''
            try:
                x1 = prf.first
                x2 = prf.last
                ppnamespace.MAXMIND_INTERVAL_TREE[x1:x2] = get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT,
                                                                                          cntry)
            except:
                x1 = line[0].split('/')[0]
                x = ip_string_to_int(x1)
                ppnamespace.MAXMIND_DICT[x] = get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT, cntry)
    print "Loaded Maxmind"

    # read dbip
    filepath = os.path.join(configs.system.PROJECT_ROOT, configs.system.DIR_DATA,
                                                               configs.system.SRC_DBIP)
    ppnamespace.DBIP_INTERVAL_TREE = IntervalTree()
    with open(filepath, "rb") as dbipfile:
        csvreader = csv.reader(dbipfile)
        for line in csvreader:
            x1 = ip_string_to_int(line[0])
            x2 = ip_string_to_int(line[1]) + 1
            ppnamespace.DBIP_INTERVAL_TREE[x1:x2] = get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT,
                                                                                   line[2])
    print "Loaded DBIP"

    filepath = os.path.join(configs.system.PROJECT_ROOT, configs.system.DIR_DATA,
                                                       configs.system.SRC_IP2LOCATION)
    ppnamespace.IP2LOCATION_INTERVAL_TREE = IntervalTree()
    with open(filepath, "rb") as ip2locfile:
        csvreader = csv.reader(ip2locfile)
        for line in csvreader:
            x1 = int(line[0])
            x2 = int(line[1]) + 1
            ppnamespace.IP2LOCATION_INTERVAL_TREE[x1:x2] = get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT,
                                                                                          line[2])
    print "Loaded IP2Location"


