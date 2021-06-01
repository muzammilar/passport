# -*- coding: utf-8 -*-
"""

    ppcore.system.rttintersect
    ~~~~~~~~~~~~~~

     This module contains the code for the Speed of Light based intersection
     of the ping measurements from different vantage points, handling aliases,
     returning a possible location where a router lies according to the SoL
     constraints.


    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from ppmeasurements import ping
from ppcore.system import utils as util_geoloc_system
import world.geography
import configs.intersection
import pputils as utils
import geosources.ipinfo as ip_info
from ppcore.intersectalgo import get_box
from ppcore import ppbox
import ppnamespace

def get_ip_rtt_intersection(ip_str, country_polygon_dict, src_info_dict, router_aliases_dict):
    intesection_box = get_box_from_rtt_intersection(ip_str, src_info_dict, router_aliases_dict)
    if intesection_box is None:
        return []
    return get_area_pred_countries_single_box(intesection_box, country_polygon_dict)    


def get_area_pred_countries_single_box(ip_bx, country_polygon_dict):
    ip_address = ip_bx['ip']
    area_results = world.geography.detect_region(country_polygon_dict,
                                                 ip_bx['lat_bottom_left'], ip_bx['lon_bottom_left'],
                                                 ip_bx['lat_top_right'], ip_bx['lon_top_right'])
    return [country_tuple[0] for country_tuple in area_results]


def get_box_from_rtt_intersection(ip, src_info_dict, router_aliases_dict):
    ip_int = utils.ip_int_to_string(ip)
    min_pings = ping.get_existing_pings(ip)
    hop_ip = ip_int
    if not min_pings:
        return None
    hop_src_dict = {}
    for src in min_pings:
        src_ip_int = utils.ip_string_to_int(src)
        if src_ip_int not in src_info_dict:
            src_info = ip_info.get_info_cached(src)
            with ppnamespace.WRITE_LOCK_SRC_INFO:
                src_info_dict[src_ip_int] = src_info
        entry_rtt = min_pings[src]
        if entry_rtt > configs.intersection.SPEED_MAX_RTT:
            continue
        if src_ip_int in hop_src_dict:
            hop_src_dict[src_ip_int] = min(entry_rtt,hop_src_dict[src_ip_int])
        else:
            hop_src_dict[src_ip_int] = entry_rtt 
    if not hop_src_dict:
        return None

    # get a list of boxes from srcs
    srcs_dict = hop_src_dict
    # get a list of boxes from landmarks
    boxes = []
    #print srcs_dict
    for src_ip_int in srcs_dict:
        # get min rtt
        min_rtt = srcs_dict[src_ip_int]
        # create a box.
        src = src_info_dict[src_ip_int]
        if src["latitude"] == 0:
            continue
        if src["country"] in util_geoloc_system.USELESS_PREDICTED_COUNTRIES:
            continue
        src_lat = src["latitude"]
        src_lon = src["longitude"]
        bx = get_box(src_lat, src_lon, min_rtt)
        boxes.append(bx)
        # sort the boxes on area so that smallest boxes are chosen first
    boxes.sort()  #the sort function is in the geo_code_box
    #print boxes
    # instersect the boxes
    try:
        box = ppbox.intersect_boxes(boxes)
    except:
        return None
    if box is not None:
        # save this intersection coordinates,
        # the number of sources it saw, number of intersections.
        box_info = {'ip': utils.ip_int_to_string(ip_int),
                            'lat_bottom_left': box.y1,
                            'lon_bottom_left': box.x1,
                            'lat_top_right': box.y2,
                            'lon_top_right': box.x2, 'num_boxes': len(boxes)}
        return box_info 
    boxes.sort()
    # instersect the boxes
    try:
        box = ppbox.intersect_boxes_second(boxes)
    except:
        return None
    if box is not None:
        # save this intersection coordinates,
        # the number of sources it saw, number of intersections.
        box_info = {'ip': utils.ip_int_to_string(ip_int),
                            'lat_bottom_left': box.y1,
                            'lon_bottom_left': box.x1,
                            'lat_top_right': box.y2,
                            'lon_top_right': box.x2, 'num_boxes': len(boxes)}
        return box_info
    return None
