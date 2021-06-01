# -*- coding: utf-8 -*-
"""

    world.geography
    ~~~~~~

    A module to load country shapes, and finding the countries in a given region.
    This module loads the shapefiles for the countries, process them, and provides the countries
    that intersection with a specific region or the country where a point is location.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""


import shapefile
import configs.system
import configs.pvt
from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely.geometry import box
import os
import pputils
#import concave_hull_module

from matplotlib import pyplot as plt
from shapely.geometry import Polygon
from descartes import PolygonPatch


def load_country_maps():
    """
        Loads the shape file containing country information into system readable polygons

    :return: A dictionary of dictionaries. {"country name":
                                                    {"country_code": A two character string, "lat": float, "lon": float,
                                                    "polygon": shapely readable polygon,
                                                    "convex_hull": convex hull of the shapely readable polygon}
                                            ...}
    """

    # read shapefile
    fname = os.path.join(configs.system.PROJECT_ROOT, 
                            configs.system.DIR_DATA,
                            configs.system.WORLD_BORDER_DIR_BASE,
                            configs.system.WORLD_BORDER_FILE)
    sf = shapefile.Reader(fname)
    shape_records_ensemble = sf.shapeRecords()
    country_polygon_dict = {}

    # load all shape records
    for shapeRec in shape_records_ensemble:
        x = Polygon(shapeRec.shape.points)
        country_code = shapeRec.record[1]
        country_lon = shapeRec.record[9]
        country_lat = shapeRec.record[10]
        country_shape_object = {"country_code": country_code,
             "lat": country_lat, "lon": country_lon, "polygon": x, "convex_hull":x.convex_hull}
        country_name = pputils.get_country_name_from_code(country_code)
        country_polygon_dict[country_name] = country_shape_object
        #print country_name
    # add other names
    # corner case of Bosnia
    try:
        country_polygon_dict["Bosnia"] = country_polygon_dict["Bosnia and Herzegovina"]
    except:
        try:
            country_polygon_dict["Bosnia and Herzegovina"] = country_polygon_dict["Bosnia"]
        except:
            pass
    # fix some country shape errors
    country_polygon_dict = perform_error_correction_loaded_file(country_polygon_dict)
    return country_polygon_dict


def detect_region(country_polygon_ensemble, lat_bottom_left, lon_bottom_left, lat_top_right,
                  lon_top_right):  # expensive time consuming operation
    """
    Finds all the coutnries present in the given region

    :param country_polygon_ensemble: A dictionary of dictionaries. {"country name":
                                                    {"country_code": A two character string, "lat": float, "lon": float,
                                                    "polygon": shapely readable polygon,
                                                    "convex_hull": convex hull of the shapely readable polygon}
                                            ...}
    :param lat_bottom_left: float (-90 to 90)
    :param lon_bottom_left: float (-180 to 180)
    :param lat_top_right: float  (-90 to 90)
    :param lon_top_right: float (-180 to 180)
    :return: A list of strings. ["country 1", ....]

        ------------  <-----(lon top right, lat top right)
        |          |
        |          |
        |          |
        |          |
        ------------

        ^
        |
        ---- (lon bottom left, lat bottom left)

    """

    detected_countries = []
    focus_regions = make_polygon_for_earth(lat_bottom_left, lon_bottom_left, lat_top_right, lon_top_right)

    # find intersection for all countries
    for country_name in country_polygon_ensemble:
        country_polygon = country_polygon_ensemble[country_name]
        x = country_polygon["polygon"]
        for focus_region in focus_regions:
            if x.intersects(focus_region):
                # there's a problem with geocords of usa, it causes us to also be printed.
                country_code = country_polygon["country_code"]
                country_lon = country_polygon["lon"]
                country_lat = country_polygon['lat']
                country_info = (country_name, country_code, country_lat,
                                country_lon)
                detected_countries.append(country_info)
            # print shape.points
    # remove duplicates
    detected_countries_set = set(detected_countries)
    detected_countries = list(detected_countries_set)
    return detected_countries

#####################################################
## Internal use functions
#####################################################

def perform_error_correction_loaded_file(country_polygon_dict):
    """ Fix some loading errors in the polygon shapes to decrease false positives during region intersection"""
    # convex hull for some
    convex_hull_countries = [ 'Brazil', 'Oman', 'Greenland', 'Mozambique']
    for cntry in convex_hull_countries:
        country_polygon_dict[cntry]["polygon"] = country_polygon_dict[cntry]["polygon"].convex_hull

    # delete some
    del_countries = [x for x in country_polygon_dict if len(x)==2] # delete those with only the code
    for cntry in del_countries:
        del country_polygon_dict[cntry]

    # convert to 180
    countries_180 = ['Fiji', 'Kiribati', 'New Zealand', 'Russia']
    for cntry in countries_180:
        plgyn = country_polygon_dict[cntry]["polygon"]
        #print country_polygon_dict[cntry]["polygon"].area
        new_plgyn_cord = []
        old_coords = plgyn.exterior.coords[:]
        for coords in old_coords:
            if coords[0] < 0:
                coords = list(coords)
                coords[0] = 180
            new_plgyn_cord.append(coords)
        country_polygon_dict[cntry]["polygon"] = Polygon(new_plgyn_cord)
        country_polygon_dict[cntry]["convex_hull"] = country_polygon_dict[cntry]["polygon"].convex_hull
    
    # convert to -180
    countries_neg_180 = ['United States']
    for cntry in countries_neg_180:
        plgyn = country_polygon_dict[cntry]["polygon"]
        new_plgyn_cord = []
        old_coords = plgyn.exterior.coords[:]
        for coords in old_coords:
            if coords[0] > 0:
                coords = list(coords)
                coords[0] = -180
            new_plgyn_cord.append(coords)
        #concave_hull, new_plgyn_cord = concave_hull_module.alpha_shape(new_plgyn_cord, 0.4)
        country_polygon_dict[cntry]["polygon"] = Polygon(new_plgyn_cord)
        country_polygon_dict[cntry]["polygon"], country_polygon_dict[cntry]["convex_hull"] = \
            country_polygon_dict[cntry]["polygon"].convex_hull, country_polygon_dict[cntry]["polygon"]
    return country_polygon_dict


def make_polygon_for_earth(lat_bottom_left, lon_bottom_left, lat_top_right, lon_top_right):
    """
    Divides the region into two separate regions (if needed) so as to handle the cases where the regions
    cross the international date

    :param lat_bottom_left: float (-90 to 90)
    :param lon_bottom_left: float (-180 to 180)
    :param lat_top_right: float  (-90 to 90)
    :param lon_top_right: float (-180 to 180)
    :return:

        ------------  <-----(lon top right, lat top right)
        |          |
        |          |
        |          |
        |          |
        ------------

        ^
        |
        ---- (lon bottom left, lat bottom left)

    """

    focus_regions = []

    # case where region starts around 180 longitude and then wraps around to -180 longitude (complete cylinder)
    # international date line crossed
    if lon_bottom_left > lon_top_right:  # overlap of latitudes
        # we need two polygons.
        focus_region1 = Polygon([
            [lon_bottom_left, lat_bottom_left],
            [lon_bottom_left, lat_top_right],
            [180, lat_top_right],
            [180, lat_bottom_left]])
        focus_region2 = Polygon([
            [-180, lat_bottom_left],
            [-180, lat_top_right],
            [lon_top_right, lat_top_right],
            [lon_top_right, lat_bottom_left]])
        focus_regions = [focus_region1, focus_region2]
    else: # international dateline not crossed
        focus_region1 = Polygon([
            [lon_bottom_left, lat_bottom_left],
            [lon_bottom_left, lat_top_right],
            [lon_top_right, lat_top_right],
            [lon_top_right, lat_bottom_left]])
        focus_regions = [focus_region1]
    return focus_regions


def draw_all_countries(country_polygon_ensemble):
    """ A function to draw country polygons on a map to visualize any possible errors in shape loading"""
    countries_names_list = [cntry for cntry in country_polygon_ensemble]
    draw_some_countries(country_polygon_ensemble, countries_names_list)


def draw_some_countries(country_polygon_ensemble, countries_names_list):
    """ A function to draw country polygons on a map to visualize any possible errors in shape loading"""
    FILE_ABS_PATH = os.path.abspath(__file__)
    CUR_DIR = os.path.dirname(FILE_ABS_PATH)
    dirname = os.path.join(CUR_DIR, configs.system.WORLD_BORDER_DIR_BASE,
                                                configs.pvt.DIR_GRAPH)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)  # race condition if dir created between these two. but won't happen
    for country_name in countries_names_list:
        country_polygon_data = country_polygon_ensemble[country_name]
        country_polygon = country_polygon_data["polygon"]
        save_polygon(country_polygon, country_name, dirname)


def save_polygon(polygon_data, country_name, output_directory, alpha_val=0.7):
    """ Save the polygon of a country to a specific directory """
    output_file_path = os.path.join(output_directory, country_name + ".png")

    # create a figure
    fig = plt.figure(1, figsize=(20, 10), dpi=90)
    ax = fig.add_subplot(111)
    # draw polygon
    color = pputils.get_random_color()
    poly_patch = PolygonPatch(polygon_data, ec=color,
                                             fc=color, alpha=alpha_val)
    ax.add_patch(poly_patch)
    ax.set_title(country_name)
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


def main():
    x = load_country_maps()
    countries = detect_region(x, 24, -100, 35, 140)
    print countries


if __name__ == '__main__':
    main()
