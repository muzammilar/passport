# -*- coding: utf-8 -*-
"""

    ppcore.system.online
    ~~~~~~~~~~~~~~

    This module looks up the cached measurements
    and schedule new ones on cache failure while the
    webserver is running.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import ppnamespace
import ppmeasurements.util as util_traceroutes
from ppmeasurements import traceroute
import socket
from ppcore.system import rttintersect
from ppcore.system import utils as util_geoloc_system
import configs.system


def sort_on_hop_number(predictions_list):
    predictions_list.sort(key=lambda k:k['hop'])


def get_predictions_traceroute(traceroute):
    #return a list and make sure to sort on the hop number, use above function
    raise Exception('Function not Implemented!')


def get_predictions_ip_address(ip_address, hostname='',hop_number=0):
    # see if the address is valid ipv4
    predictions_dict = {'ip': ip_address,
                        'hop': hop_number,
                        'hostname': hostname,
                        'area': [],
                        'classifier': [],
                        'combined': [],
                        'overall': [],
                        'error': False,
                        'error_type': '',
                        'status': 'running'}
    if not util_traceroutes.is_valid_ip(ip_address):
        predictions_dict['ip'] = ip_address[:20] #keep only first 20 letters.
        predictions_dict['error'] = True
        predictions_dict['error_type'] = 'Invalid IPv4 Address'
        predictions_dict['status'] = 'finished'
        return predictions_dict
    err, err_val = util_traceroutes.ip_address_to_ignore(ip_address)
    if err:
        predictions_dict['error'] = True
        predictions_dict['status'] = 'finished'
        predictions_dict['error_type'] = err_val
        predictions_dict['overall'].append("-")
        return predictions_dict
    #print >> sys.stderr, "not private"
    # see if the ip address is in the cache
    success = util_geoloc_system.get_system_predictions(predictions_dict)
    #print >> sys.stderr, success    
    if success:
        predictions_dict['status'] = 'finished'
    else:
        try:
            if hostname == '':
                hostname = socket.gethostbyaddr(ip_address)[0]
        except:
            hostname = ''
        ppnamespace.QUEUE_IPS_LOOKUP.put((ip_address, hostname))
    # in case we're not sure about the country
    if len(predictions_dict['overall']) > configs.system.ONLINE_GEOLOCATION_MAX_COUNTRIES_ALLOWED:
        del predictions_dict['overall'][:]
        predictions_dict['overall'].append(configs.system.ONLINE_GEOLOCATION_UNKNOWN_COUNTRY)
        predictions_dict['error'] = True
        predictions_dict['error_type'] = "Failed to narrow down the list of countries."
    return predictions_dict


def perform_measurement_prediction_ip_address(ip_address, hostname='',hop_number=0):
    # TODO: READ HOSTNAMES FILE TOO!
    # perform new measurements and return the result
    traceroute.get_geolocation_sources_info((ip_address, hostname))
    #print  >>sys.stderr, ip_address
    area_cntry = rttintersect.get_ip_rtt_intersection(ip_address, ppnamespace.country_polygon_dict,
                                                      ppnamespace.src_info_dict, ppnamespace.router_aliases_dict)
    ppnamespace.area[ip_address] = area_cntry
    cls_cntry = util_geoloc_system.perform_pred_classifier(ip_address, hostname, ppnamespace.LOADED_CLASSIFIERS)
    ppnamespace.classifier[ip_address] = cls_cntry
    # do an overall thing
    ppnamespace.combined[ip_address] = [x for x in cls_cntry if x.lower() in [y.lower() for y in area_cntry]]
    cmbnd_cntry = ppnamespace.combined[ip_address]
    # save to database and structures
    # you don't have anything from ground truth since it's already loaded in offline system
    if len(area_cntry)== 1:
        ppnamespace.overall[ip_address] = area_cntry[:]
    elif len(area_cntry)== 0:
        ppnamespace.overall[ip_address] = cls_cntry[:]
    else:
        if len(cmbnd_cntry) == 0 and len(area_cntry) <= len(cls_cntry):
            ppnamespace.overall[ip_address] = area_cntry[:]
        else:
            ppnamespace.overall[ip_address] = cmbnd_cntry[:]



