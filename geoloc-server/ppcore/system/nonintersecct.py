# -*- coding: utf-8 -*-
"""

    ppcore.system.nointersect
    ~~~~~~~~~~~~~~

    This module draws the graphs for no intersection ping measurements to see if they might be
    multicast IP addresses, failure in system predictions, system bugs or something else.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""


import os
import pickle
import configs.pvt
import world.geography
import pputils

from matplotlib import pyplot as plt
from descartes import PolygonPatch
import ppcore.system.prediction as prediction_system

def add_box_to_graph(ax, lat_bottom_left, lon_bottom_left, lat_top_right,
                                             lon_top_right, alpha_val=0.02):
    polygons_to_plot = world.geography.make_polygon_for_earth(lat_bottom_left,
        lon_bottom_left, lat_top_right, lon_top_right)
    color = pputils.get_random_color()
    for polygon_to_plot in polygons_to_plot:
        poly_patch = PolygonPatch(polygon_to_plot, ec=color,
                                                 fc=color, alpha=alpha_val)
        ax.add_patch(poly_patch)


def main_analysis_non_intersecting_traceroutes():
    FILE_ABS_PATH = os.path.abspath(__file__)
    CUR_DIR = os.path.dirname(FILE_ABS_PATH)
    SVE_FILE_NME = prediction_system.TRACEROUTE_IPS_LATLON_FILE
    #f_stats_name_intersections = SVE_FILE_NME + "_intersections.csv"
    data_file_name = prediction_system.TRACEROUTE_IPS_LATLON_FILE
    data_file = open(os.path.join(CUR_DIR, prediction_system.DATA_FOLDER,
                                  data_file_name), "rb")
    output_directory = os.path.join(CUR_DIR, prediction_system.DATA_FOLDER,
                                    configs.pvt.SUBDIR_NO_INTERSECTION)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    analysis_data = pickle.load(data_file)
    
    for non_intersection_box in analysis_data['ip_no_intersection_list']:
        #nib = non_intersection_box
        boxes = non_intersection_box['boxes']
        ip = non_intersection_box['ip']
        output_file_path = os.path.join(output_directory, ip + ".png")

        # create a figure
        fig = plt.figure(1, figsize=(20, 10), dpi=90)
        ax = fig.add_subplot(111)
        # draw all the boxes
        for bx in boxes:
            add_box_to_graph(ax, bx['lat_bottom_left'], bx['lon_bottom_left'],
                                    bx['lat_top_right'], bx['lon_top_right'])
        # save the graphs.
        #add_box_to_graph(ax, nib['lat_bottom_left'], nib['lon_bottom_left'],
        #                    nib['lat_top_right'], nib['lon_top_right'], 1)

        ax.set_title(ip)
        xrange_grph = [-180, 180]
        yrange_grph = [-90, 90]
        ax.set_xlim(*xrange_grph)
        ax.set_xlabel('longitude')
        #ax.set_xticks(range(*xrange_grph) + [xrange_grph[-1]])
        ax.set_ylim(*yrange_grph)
        ax.set_ylabel('latitude')
        #ax.set_yticks(range(*yrange_grph) + [yrange_grph[-1]])
        ax.set_aspect(1)
        fig.savefig(output_file_path)
        plt.clf()
        plt.cla()
        plt.close()
