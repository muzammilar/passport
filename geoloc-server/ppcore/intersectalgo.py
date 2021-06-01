# -*- coding: utf-8 -*-
"""

    ppcore.intersectalgo
    ~~~~~~~~~~~~~~

    (Deprecated) This module is used to create intersection box (geodesic) and contains a
    the intersection algorithm. This module contains a class for the geodesic boxes
    created in the Passport System and the region (in terms of lat-long) predicted
    by the intersection of multiple such boxes as well as calculating the area of
    these boxes.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

###remove-me-later-muz######remove-me-later-muz###import ormsettings as DJANGO_SETTINGS   # don't remove
###remove-me-later-muz######remove-me-later-muz###from django.db import models

from ppstore.models import Hints_world_cities_pop_maxmind_geolite

###remove-me-later-muz###from georoute.geo_namespaces import Box

from ppcore import ppbox

import ppmeasurements.util as util_traceroutes

import geosources.ipinfo as ip_info

import traceback
import os
from datetime import datetime

import pputils
import configs.intersection
import configs.system
import ppnamespace
from multiprocessing import Manager
import routerinfo.aliases as router_alias_package

###remove-me-later-muz###import geopy
###remove-me-later-muz###from geopy.distance import GreatCircleDistance
###remove-me-later-muz###from geopy.distance import great_circle


# muz, change this function, make it more.. accurate.
def get_box_old(src_lat, src_lon, min_rtt):
    # we assume that no submarine cables are near the polar ice caps,
    # plus SOL fails at poles.
    rad = min_rtt * configs.system.PROPAGATION_SPEED / 2
    x1 = src_lon - rad
    y1 = max(-89.999, src_lat - rad)
    x2 = src_lon + rad
    y2 = min(89.999, src_lat + rad)
    box = ppbox.Box(x1, y1, x2, y2)
    return box


def get_box(src_lat, src_lon, min_rtt):
    # we assume that no submarine cables are near the polar ice caps,
    # plus SOL fails at poles.
    distance_travelled = min_rtt * configs.intersection.SPEED_LIGHT * configs.intersection.SPEED_LIGHT_FACTOR / 2.00 # div by 2 so that we get half of rtt
    origin = geopy.Point(src_lat, src_lon)
    origin_point = (src_lat, src_lon)
    top_point = (89.999, src_lon)
    bottom_point = (-89.999, src_lon)
    bearing_list = [0, 45, 90, 135, 180, 225, 270, 315]
    x1_list = [270, 225, 315]  # you might wanna add 0 and 180, same for all below
    y1_list = [225, 180, 135]  # you might wanna add 270 and 90, same for all below
    x2_list = [90, 45, 135]  # you might wanna add 0 and 180, same for all below
    y2_list = [0, 315, 45 ]  # you might wanna add 270 and 90, same for all below
    destintation_dict = {}
    # add these to the dictionary.
    for bearing in bearing_list:
        destination = GreatCircleDistance(kilometers=distance_travelled).destination(origin, bearing)
        destintation_dict[bearing] = destination
    #
    temp_list = [destintation_dict[x].longitude + 360 for x in x1_list]
    x1 = min(temp_list) -360
    temp_list = [destintation_dict[x].longitude + 360 for x in x2_list]
    x2 = max(temp_list) -360
    if great_circle(bottom_point, origin_point).km < distance_travelled:
        y1 = -89.999
    else:
        temp_list = [destintation_dict[x].latitude for x in y1_list]
        y1 = min(temp_list)
    if great_circle(top_point, origin_point).km < distance_travelled:
        y2 = 89.999
    else:
        temp_list = [destintation_dict[x].latitude for x in y2_list]
        y2 = max(temp_list)

    box = ppbox.Box(x1, y1, x2, y2)
    return box


def get_country_from_lat_long(latitude1, longitude1):
    not_found = True
    error_diff = 0.1
    multfactor = 2
    while not_found:  #get some random country.
        try:
            loc_tup_list = Hints_world_cities_pop_maxmind_geolite.objects.filter(
                latitude__gte=latitude1 - error_diff, latitude__lte=latitude1 + error_diff,
                longitude__gte=longitude1 - error_diff, longitude__lte=longitude1 + error_diff)
            loc = loc_tup_list[0]
            not_found = False
        except:
                not_found = True
                error_diff = error_diff * multfactor
    return loc.country


###############################################################################
# new code
# reads all the traceroutes.
# for now forget the landmarks: Todo
def speed_constraints():
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    # global structures
    hop_info_dict = {}
    src_info_dict = {} # also contains landmarks.
    landmark_info_dict = {}
    hop_to_src_dict = {} # an ip to a list of dicts that have the source # hop:source
    all_traceroutes = []
    basic_stats_cron = {}
    ips_unique = set()

    begin_time = datetime.now()

    FILE_ABS_PATH = os.path.abspath(__file__)
    CUR_DIR = os.path.dirname(FILE_ABS_PATH)
    traceroute_data_parent_folder = os.path.join(CUR_DIR,
                                                 configs.intersection.traceroute_pkg_folder,
                                                 configs.intersection.traceroute_folder)
    # read all the aliases
    router_aliases_dict = router_alias_package.get_router_aliases()
    # read all the landmarks from the database
    # to do

    # read all the traceroute
    traceroute_id = 0
    for folder_name in os.listdir(traceroute_data_parent_folder):
        if folder_name in configs.intersection.ignore_files:
            continue
        folder_path = os.path.join(traceroute_data_parent_folder, folder_name)
        if not os.path.isdir(folder_path):
            continue
        for f_name in os.listdir(folder_path):
            if f_name in configs.intersection.ignore_files:
                continue
            f_path = os.path.join(traceroute_data_parent_folder,
                folder_path, f_name)
            traceroute_info = util_traceroutes.get_traceroutes_from_file(f_path,traceroute_id)
            if traceroute_info is None:
                continue
            src_ip_int = traceroute_info["src_ip_int"]
            # add traceroute to a list of traceroutes.
            #if src_ip_int not in all_traceroutes:
            #    all_traceroutes[src_ip_int] = []
            #all_traceroutes[src_ip_int].append(traceroute_info)

            all_traceroutes.append(traceroute_info)
            traceroute_id += 1

            # add the source to the sources list
            if src_ip_int not in src_info_dict:
                src_info = ip_info.get_info_cached(traceroute_info["src"])
                src_info_dict[src_ip_int] = src_info
            # read all the enteries
            landmarks_list = []
            for entry in traceroute_info["entries"]:
                if entry['rtt'] is None:
                    continue
                # if rtt > threshhold, this measurement might be useless.
                if entry['rtt'] > configs.intersection.SPEED_MAX_RTT:
                    continue
                hop_ip = entry['ip']
                ips_unique.add(hop_ip)
                # if it's a landmark add it to the database,
                # then add it to landmarks list and then continue
                # todo
                # continue

                # otherwise
                # check for aliases and translate to a single alias
                if hop_ip in router_aliases_dict:
                    hop_ip = router_aliases_dict[hop_ip]
                # add to hop_to_source
                if hop_ip not in hop_to_src_dict:
                    hop_to_src_dict[hop_ip] = {}
                if src_ip_int not in hop_to_src_dict[hop_ip]:
                    hop_to_src_dict[hop_ip][src_ip_int] = []
                hop_to_src_dict[hop_ip][src_ip_int].append(entry['rtt'])
                # add to hop_to_landmark with new distances
                # for all the landmarks in the list
                # todo

    print "Time taken to load all the traceroutes:", str(datetime.now() - begin_time)
    second_time = datetime.now()

    basic_stats_cron['ip_intersection_box_list'] = []
    ip_intersection_box_list = basic_stats_cron['ip_intersection_box_list']
    basic_stats_cron['ip_no_intersection_list'] = []
    ip_no_intersection_list = basic_stats_cron['ip_no_intersection_list']

    exception_counter = 0
    # get all the intersections
    for hop in hop_to_src_dict:
        # get a list of boxes from srcs
        srcs_dict = hop_to_src_dict[hop]
        # get a list of boxes from landmarks
        boxes = []
        #print srcs_dict
        for src_ip_int in srcs_dict:
            # get min rtt
            rtt_list = srcs_dict[src_ip_int]
            min_rtt = min(rtt_list)
            # create a box.
            src = src_info_dict[src_ip_int]
            if src["latitude"] == 0:
                continue
            src_lat = src["latitude"]
            src_lon = src["longitude"]
            bx = get_box(src_lat, src_lon, min_rtt)
            boxes.append(bx)
        # sort the boxes on area so that smallest boxes are chosen first
        boxes.sort()  #the sort function is in the geo_code_box
        # instersect the boxes
        try:
            box = ppbox.intersect_boxes(boxes)
        except:
            print "Box Intersection Failed"
            traceback.print_exc()
            exception_counter += 1
        ip = hop
        if box is None:
            no_box_info = {'ip': pputils.ip_int_to_string(ip),
                            'lat_bottom_left': -89.9,
                            'lon_bottom_left': -179.9,
                            'lat_top_right': 89.9,
                            'lon_top_right': 179.9, 'num_boxes': len(boxes)}
            boxes_info_list = [{'lat_bottom_left': box.y1,
                'lon_bottom_left': box.x1,
                'lat_top_right': box.y2,
                'lon_top_right': box.x2} for box in boxes]
            no_box_info['boxes'] = boxes_info_list
            ip_no_intersection_list.append(no_box_info)
            continue
        # save this intersection coordinates,
        # the number of sources it saw, number of intersections.
        box_info = {'ip': pputils.ip_int_to_string(ip),
                            'lat_bottom_left': box.y1,
                            'lon_bottom_left': box.x1,
                            'lat_top_right': box.y2,
                            'lon_top_right': box.x2, 'num_boxes': len(boxes)}
        ip_intersection_box_list.append(box_info)

    print "Time taken for Intersections:", str(datetime.now() - second_time)
    print "Total time:", str(datetime.now() - begin_time)
    print "Total number of exceptions for box intersections:", exception_counter
    second_time = datetime.now()

    basic_stats_cron['num_sources'] = len(src_info_dict)
    basic_stats_cron['num_hops_total'] = len(hop_to_src_dict)
    basic_stats_cron['num_hops_total_ip'] = len(ips_unique)
    basic_stats_cron['num_traceroutes_total'] = len(all_traceroutes)
    basic_stats_cron['num_intesections'] = len(ip_intersection_box_list)
    basic_stats_cron['num_no_intersections'] = len(ip_no_intersection_list)
    # dump the output in a file, with telling the source(sol, cls, both)
    return basic_stats_cron


def speed_constraints_with_rtt_analysis():
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    # global structures
    hop_info_dict = {}
    src_info_dict = {} # also contains landmarks.
    landmark_info_dict = {}
    hop_to_src_dict = {} # an ip to a list of dicts that have the source # hop:source
    all_traceroutes = []
    basic_stats_cron = {}
    ips_unique = set()
    analysis_hops_pings = []
    analysis_rtt_range = []
    analysis_rtt_max = []
    analysis_rtt_min = []
    begin_time = datetime.now()

    FILE_ABS_PATH = os.path.abspath(__file__)
    CUR_DIR = os.path.dirname(FILE_ABS_PATH)
    traceroute_data_parent_folder = os.path.join(CUR_DIR, configs.intersection.traceroute_pkg_folder,
                                                 configs.intersection.traceroute_folder)
    # read all the aliases
    router_aliases_dict = router_alias_package.get_router_aliases()
    # read all the landmarks from the database
    # to do

    # read all the traceroute
    traceroute_id = 0
    for folder_name in os.listdir(traceroute_data_parent_folder):
        if folder_name in configs.intersection.ignore_files:
            continue
        folder_path = os.path.join(traceroute_data_parent_folder, folder_name)
        if not os.path.isdir(folder_path):
            continue
        for f_name in os.listdir(folder_path):
            if f_name in configs.intersection.ignore_files:
                continue
            f_path = os.path.join(traceroute_data_parent_folder, folder_path, f_name)
            traceroute_info = util_traceroutes.get_traceroutes_from_file(f_path,traceroute_id)
            if traceroute_info is None:
                continue
            src_ip_int = traceroute_info["src_ip_int"]
            # add traceroute to a list of traceroutes.
            #if src_ip_int not in all_traceroutes:
            #    all_traceroutes[src_ip_int] = []
            #all_traceroutes[src_ip_int].append(traceroute_info)

            all_traceroutes.append(traceroute_info)
            traceroute_id += 1

            # add the source to the sources list
            if src_ip_int not in src_info_dict:
                src_info = ip_info.get_info_object(traceroute_info["src"])
                src_info_dict[src_ip_int] = src_info
            # read all the enteries
            landmarks_list = []
            for entry in traceroute_info["entries"]:
                if entry['rtt'] is None:
                    continue
                hop_ip = entry['ip']
                # if it's a landmark add it to the database, then add it to landmarks list and then continue
                # todo
                # continue

                # otherwise
                # check for aliases and translate to a single alias
                if hop_ip in router_aliases_dict:
                    hop_ip = router_aliases_dict[hop_ip]
                # add to hop_to_source
                if hop_ip not in hop_to_src_dict:
                    hop_to_src_dict[hop_ip] = {}
                if src_ip_int not in hop_to_src_dict[hop_ip]:
                    hop_to_src_dict[hop_ip][src_ip_int] = []
                hop_to_src_dict[hop_ip][src_ip_int].append(entry['rtt'])
                # add to hop_to_landmark with new distances for all the landmarks in the list
                # todo

    print "Time taken to load all the traceroutes:", str(datetime.now() - begin_time)
    second_time = datetime.now()

    basic_stats_cron['ip_intersection_box_list'] = []
    ip_intersection_box_list = basic_stats_cron['ip_intersection_box_list']

    # get all the intersections
    for hop in hop_to_src_dict:
        # get a list of boxes from srcs
        srcs_dict = hop_to_src_dict[hop]
        # get a list of boxes from landmarks
        boxes = []
        rtt_from_diff_src_dict = []
        #print srcs_dict
        for src_ip_int in srcs_dict:
            # get min rtt
            rtt_list = srcs_dict[src_ip_int]
            min_rtt = min(rtt_list)
            rtt_from_diff_src_dict.append(min_rtt)
            analysis_hops_pings.append(min_rtt)
            # create a box.
            src = src_info_dict[src_ip_int]
            if src["latitude"] == 0:
                continue
            src_lat = src["latitude"]
            src_lon = src["longitude"]
            bx = get_box(src_lat, src_lon, min_rtt)
            boxes.append(bx)
        analysis_rtt_range.append(max(rtt_from_diff_src_dict) - min(rtt_from_diff_src_dict))
        analysis_rtt_max.append(max(rtt_from_diff_src_dict))
        analysis_rtt_min.append(min(rtt_from_diff_src_dict))
        # instersect the boxes
        try:
            box = ppbox.intersect_boxes(boxes)
        except:
            print "Box Intersection Failed"
            traceback.print_exc()
        if box is None:
            continue
        ip = hop
        # save this intersection coordinates, the number of sources it saw, number of intersections.
        box_info = {'ip': pputils.ip_int_to_string(ip), 'lat_bottom_left': box.y1,
                            'lon_bottom_left': box.x1,
                            'lat_top_right': box.y2,
                            'lon_top_right': box.x2, 'num_boxes' : len(boxes)}
        ip_intersection_box_list.append(box_info)
    print "Time taken for Intersections:", str(datetime.now() - second_time)
    print "Total time:", str(datetime.now() - begin_time)
    second_time = datetime.now()

    basic_stats_cron['num_sources'] = len(src_info_dict)
    basic_stats_cron['num_hops_total'] = len(hop_to_src_dict)
    basic_stats_cron['num_traceroutes_total'] = len(all_traceroutes)
    basic_stats_cron['num_intesections'] =len(ip_intersection_box_list)
    analysis_rtt_range.sort()
    analysis_hops_pings.sort()
    analysis_rtt_min.sort()
    analysis_rtt_max.sort()
    basic_stats_cron['analysis_hops_pings'] = analysis_hops_pings
    basic_stats_cron['analysis_rtt_range'] = analysis_rtt_range
    basic_stats_cron['analysis_rtt_max'] = analysis_rtt_max
    basic_stats_cron['analysis_rtt_min'] = analysis_rtt_min

    # dump the output in a file, with telling the source(sol, cls, both)
    return basic_stats_cron


###############################################################################
###############################################################################
## LEGACY CODE
## NOTE USED ANYMORE
###############################################################################
###############################################################################

if __name__ == "__main__":
    speed_constraints()
