# -*- coding: utf-8 -*-
"""

    geosources.ddec
    ~~~~~~

    This module has been developed to convert a hostname to a country. It takes a hostname, request ddec.caida.org
    for the location, translates this location into system readable location using Google Maps API and our internal
    database.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from string import Template
import urllib2 as urlopenner
import json
import traceback
import requests
from bs4 import BeautifulSoup
from geosources import geolocation
###remove-me-later-muz###import ormsettings as DJANGO_SETTINGS
#local files
import configs.system

# django models
from ppstore.models import Hints_DDEC_Location_Lat_Long
from ppstore.models import DDEC_Hostname


###############################################################
### Google Location Stuff
###############################################################

#####################################
use_api_key=True
base_url_no_key=Template('https://maps.googleapis.com/maps/api/geocode/json?address=$address')
base_url = Template('https://maps.googleapis.com/maps/api/geocode/json?address=$address&key=$key')
places_api_error= "error_message"
global current_api_key
current_api_key = [""]
current_api_key_index=-1
#####################################

##########################################################
# user functions
##########################################################


def in_cache(x_hostname):
    try:
        x_ddec_country_dic = ddec_get_hostname_location(x_hostname)
        if 'country' in x_ddec_country_dic:
            x_ddec_country = x_ddec_country_dic['country']
            return x_ddec_country
        return None
    except:
        x_ddec_country = None
        traceback.print_exc()
    return x_ddec_country


def request_ddec_country(x_hostname):
    try:
        ddec_hostname_dict = search_ddec([x_hostname])
        #print ddec_hostname_dict
        ddec_add_hostname_location(ddec_hostname_dict)
        x_ddec_country_dic = ddec_get_hostname_location(x_hostname)
        x_ddec_country = x_ddec_country_dic['country']
    except:
        x_ddec_country = ''
        #traceback.print_exc()
    return x_ddec_country


def search_and_store_ddec_hostnames(hostnames_list):
    ddec_hostname_dict = search_ddec(hostnames_list)
    ddec_add_hostname_location(ddec_hostname_dict)

##########################################################
# internal function
##########################################################

def change_api_key(current_api_key_index):
    current_api_key.pop()
    current_api_key_index += 1
    if current_api_key_index >= len(configs.system.GOOGLE_MAP_API_KEYS):
        current_api_key.append("")
    else:
        current_api_key.append(configs.system.GOOGLE_MAP_API_KEYS[current_api_key_index])
    return current_api_key_index


def extract_transform_location_information(address_object, loc):
    address_result = address_object["results"]
    city = ''
    region = ''
    country = ''
    lat = None
    lon = None
    ne_lat = None
    sw_lat = None
    ne_long = None
    sw_long = None
    for x in range(len(address_result[0]["address_components"])):
        addr_component = address_result[0]["address_components"][x]
        typ = addr_component["types"]
        if "locality" in typ:
            city = addr_component["long_name"]
        if "administrative_area_level_1" in typ:
            region = addr_component["long_name"]
        if "country" in typ:
            country = addr_component["long_name"]
    if "geometry" in address_result[0]:
        geometry = address_result[0]["geometry"]
        if "location" in geometry:
            location = geometry["location"]
            lat = location['lat']
            lon = location['lng']
        if "bounds" in geometry:
            bounds = geometry["bounds"]
            if "northeast" in bounds:
                location = bounds["northeast"]
                ne_lat = location['lat']
                ne_long = location['lng']
            if "southwest" in bounds:
                location = bounds["southwest"]
                sw_lat = location['lat']
                sw_long = location['lng']
    return lat, lon, city, region, country, ne_lat, ne_long, sw_lat, sw_long, loc


def search_place_machine_readable(loc, current_api_key_index):
    try:
        loc2 = urlopenner.quote(loc.encode('utf8'))
        if use_api_key:
            current_url = base_url.substitute(address=loc2, key=current_api_key[0]);
        else:
            current_url = base_url_no_key.substitute(address=loc2);
        retrieved_json = urlopenner.urlopen(current_url,timeout = configs.system.EXTERNAL_TIMEOUT).read();
        search_result = json.loads(retrieved_json)
        if search_result["status"] != "OK":
            print "Status Message: " + search_result["status"]
            if search_result["status"]=="OVER_QUERY_LIMIT" or search_result["status"]=="REQUEST_DENIED":
                current_api_key_index = change_api_key(current_api_key_index)
                if current_api_key[0] == "":
                    print "API Keys Exhausted"
                    return None
                return search_place_machine_readable(loc)
            if places_api_error in search_result.keys():
                print "Error: " + search_result[places_api_error]
                print "Location: " + loc
            return None
        return extract_transform_location_information(search_result, loc)
    except Exception, e:
        print e
        traceback.print_exc()
        print "\n\n Contnuing the script..."


def update_ddec_location_lat_lon(new_location, location_tuple):
    try:
        ddec_loc = Hints_DDEC_Location_Lat_Long(location=new_location,
                                                latitude=location_tuple[0], longitude=location_tuple[1],
                                                city=location_tuple[2],
                                                region=location_tuple[3], country=location_tuple[4],
                                                ne_lat=location_tuple[5], ne_lon=location_tuple[6],
                                                sw_lat=location_tuple[7], sw_lon=location_tuple[8])
        #print "Saving "+ ddec_loc
        ddec_loc.save()
    except:
        print "DDEC Location already exists"


def update_ddec_locations_table(hst, loc, lat, lon):
    ddec_entery = DDEC_Hostname(hostname=hst,
                                location=loc,
                                latitude=lat,
                                longitude=lon)
    #print "Saving "+ ddec_entery
    ddec_entery.save()


def ddec_add_hostname_location(ddec_hostname_dict):
    current_api_key_index=-1
    current_api_key_index = change_api_key(current_api_key_index)
    current_known_locations = [x.location for x in Hints_DDEC_Location_Lat_Long.objects.all()]
    ddec_hostname_locations=[]
    for k in ddec_hostname_dict:
        for v in ddec_hostname_dict[k]:
            ddec_hostname_locations.append(v)
    new_locations_list = [x for x in ddec_hostname_locations if x not in current_known_locations]
    for new_location in new_locations_list:
        location_tuple = search_place_machine_readable(" ".join(new_location.split(".")), current_api_key_index)
        if location_tuple is None:
            location_tuple = get_location_manual(new_location)  # get my manual location. cos Google API failed :(
        if location_tuple is None:
            continue
        update_ddec_location_lat_lon(new_location, location_tuple)
        for k in ddec_hostname_dict:
            if new_location in ddec_hostname_dict[k]:
                update_ddec_locations_table(k, new_location, location_tuple[0], location_tuple[1])
                break


def get_location_manual(loc):
    city = ''
    region = ''
    country = ''
    lat = None
    lon = None
    ne_lat = None
    sw_lat = None
    ne_long = None
    sw_long = None
    x = loc.split(',')
    loc_list = []
    for i in x:
        lc = i.split(' ')
        for j in lc:
            if len(j) > 0:
                loc_list.append(j)
    len_loc_list = len(loc_list)
    print loc_list
    if len_loc_list > 3:
        print "Something went wrong with: ", loc_list
        return None
    if len_loc_list == 3:
        city = loc_list[0]
        region = loc_list[1]
        country = loc_list[2]
        country = geolocation.convert_country_code_to_name(country, {}, False)
        region = geolocation.convert_state_code_to_name(region)
        lat, lon = geolocation.get_lat_lon_coordinates(country, region, city)
        if country.lower() == 'usa':
            country = "United States"
        if country.lower() == 'snge':
            country = "Singapore"
        return lat, lon, city, region, country, ne_lat, ne_long, sw_lat, sw_long, loc
    if len_loc_list == 2:
        city = loc_list[0]
        region = loc_list[1]
        country = loc_list[1]
        country = geolocation.convert_country_code_to_name(country, {}, False)
        region = geolocation.convert_state_code_to_name(region)
        lat, lon = geolocation.get_lat_lon_with_city(country, city)
        country = "United States"
        if lat is None:
            lat, lon = geolocation.get_lat_lon_with_city_and_state(country, region, city)
        return lat, lon, city, region, country, ne_lat, ne_long, sw_lat, sw_long, loc
    return None


def ddec_get_hostname_location(hst_nm):
    loc_obj = {}
    # empty hostname
    if len(hst_nm) == 0:
        return loc_obj
    # trailing .
    if hst_nm=='':
        return loc_obj
    if hst_nm is None:
        return loc_obj
    if hst_nm[-1] == '.':
        hst_nm2 = hst_nm[:-1]
    else:
        hst_nm2 = hst_nm
    all_hosts = DDEC_Hostname.objects.filter(hostname=hst_nm2)
    if all_hosts.count() == 0:
        return loc_obj
    e_hst = all_hosts[0]
    s2 = Hints_DDEC_Location_Lat_Long.objects.filter(location=e_hst.location)
    if s2.count() == 0:
        return loc_obj
    s = s2[0]
    loc_obj['hostname'] = hst_nm
    loc_obj['location'] = e_hst.location
    loc_obj['latitude'] = s.latitude
    loc_obj['longitude'] = s.longitude
    loc_obj['country'] = s.country
    return loc_obj

###############################################################
### DDEC Website
###############################################################


def parse_html_get_ddec_location_dict(returned_html):
    host_name_location_dict = {}
    soup = BeautifulSoup(returned_html, 'html.parser')
    tables = soup.findAll('table')
    if tables == []:
        return host_name_location_dict
    table = tables[0]
    rows = table.findAll('tr')
    for row in rows[2:]:
        cols = row.findAll('td')
        hostname = ''
        location = ''
        for col in cols:
            hostname_list = col.findAll('span', {'class': 'val_hostname'})
            if hostname_list != []:
                hostname = hostname_list[0].text
            location_list = col.findAll('span', {'class': 'decode'})
            if location_list != []:
                loc_span = col.findAll('span')[-1]
                location = loc_span.text
                if location == '':
                    continue
                break
            location_list = col.findAll('span', {'class': 'val_loc'})
            if location_list != []:
                loc_span = location_list[-1]
                location = loc_span.text
                if location == '':
                    continue
                break
        add_to_dict_append_value_to_list(host_name_location_dict,
             hostname, location)
    if '' in host_name_location_dict:
        del(host_name_location_dict[''])
    return host_name_location_dict


def add_to_dict_append_value_to_list(mydict, key, val):
    val_list = []
    if len(val) < 4:
        return mydict
    if key in mydict:
        val_list = mydict[key]
    val_list.append(val)
    mydict[key] = val_list
    return mydict


def search_ddec(dns_hostname_lst):
    dns_hostname_lst = [x for x in dns_hostname_lst if x != '']
    dns_hostname_lst2 = []
    for hst_nm in dns_hostname_lst:
        if hst_nm[-1] == '.':
            dns_hostname_lst2.append(hst_nm[:-1])
        else:
            dns_hostname_lst2.append(hst_nm)
    dns_hostname_lst = dns_hostname_lst2
    current_known_hostnames = [x.hostname for x in DDEC_Hostname.objects.all()]
    new_hostnames_list = [x for x in dns_hostname_lst if x not in current_known_hostnames]
    dns_hostname_lst = new_hostnames_list
    dns_hostname = "\n".join(dns_hostname_lst)
    s = requests.Session()
    s.headers.update({'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0'})
    ddec_search_url = "http://ddec.caida.org/search.pl"
    s.headers.update({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
    s.headers.update({'Accept-Language': 'en-US,en;q=0.5'})
    s.headers.update({'Accept-Encoding': 'gzip, deflate'})
    s.headers.update({'Connection': 'keep-alive'})
    post_data = {'type': (None, 'hostnames'),
                 'hostnames': (None, dns_hostname),
                 'domain': (None, ''),
                 'rsname': (None, ''),
                 'pattype': (None, 'hostpat'),
                 '.submit': (None, 'Submit')}
    #post_data['.cgifields']=(None,'pattype')
    s.headers.update({'Host': 'ddec.caida.org'})
    s.headers.update({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
    s.headers.update({'Referer': 'http://ddec.caida.org/search.pl'})
    #s.headers.update({'Referer': 'http://ddec.caida.org/search.pl'})
    r = s.post(ddec_search_url, files=post_data)
    return parse_html_get_ddec_location_dict(r.text)
