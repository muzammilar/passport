# -*- coding: utf-8 -*-
"""

    ensemble.sourcediff
    ~~~~~~~~~~~~~~~~~

    This module generates the number of training instances for each country required
    for each classifier. This module generates the number of training instances
    based on the analysis of all the other modules in this package.



    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import os
import csv
import ensemble.utils as util_ensemble_code
import configs.system
#Note: This script only runs on linux


def get_second_derivative_mean_and_point(country_data):
    if len(country_data) < 3:
        return None, None
    country_data_len = len(country_data)
    max_pt, mean =None,None
    for i in range(1,country_data_len - 1):
        cur_pt = country_data[i]
        last_pt = country_data[i-1]
        next_pt = country_data[i+1]
        m1 = (float(cur_pt[1])-float(last_pt[1]))/(float(cur_pt[0])-float(last_pt[0]))
        m2 = (float(cur_pt[1])-float(next_pt[1]))/(float(cur_pt[0])-float(next_pt[0]))
        if m2 - m1 < 0:
            mean = float(country_data[i][1])
            max_pt = float(country_data[i][0])
            return max_pt, mean
    return max_pt, mean

def get_second_derivate_mean_and_point_final(country_data):
    if len(country_data) < 3:
        return None, None
    country_data_len = len(country_data)
    max_pt, mean =None,None
    for i in range(1,country_data_len - 1):
        cur_pt = country_data[i]
        last_pt = country_data[i-1]
        next_pt = country_data[i+1]
        m1 = (float(cur_pt[1])-float(last_pt[1]))/(float(cur_pt[0])-float(last_pt[0]))
        m2 = (float(cur_pt[1])-float(next_pt[1]))/(float(cur_pt[0])-float(next_pt[0]))
        if m2 - m1 < 0:
            mean = float(country_data[i][1])
            max_pt = float(country_data[i][0])
    return max_pt, mean

def get_second_derivate_mean_and_point_max(country_data):
    if len(country_data) < 3:
        return None, None
    country_data_len = len(country_data)
    max_pt, mean =None,None
    last_change = 0 # everthing has to be less than this
    for i in range(1,country_data_len - 1):
        cur_pt = country_data[i]
        last_pt = country_data[i-1]
        next_pt = country_data[i+1]
        m1 = (float(cur_pt[1])-float(last_pt[1]))/(float(cur_pt[0])-float(last_pt[0]))
        m2 = (float(cur_pt[1])-float(next_pt[1]))/(float(cur_pt[0])-float(next_pt[0]))
        if m2 - m1 < last_change:
            mean = float(country_data[i][1])
            max_pt = float(country_data[i][0])
            last_change = m2 - m1
    return max_pt, mean


def get_difference_between_sources(other_points):
    COMPARISON_SOURCES = ['propotional increase','double increase','random increase']
    FOLDER_NAME_DICT = {'propotional increase':'proportional','double increase':'double','random increase':'random'}
    SOURCES_COUNTRY_FILES = {}
    # Get files
    for comparison_source in COMPARISON_SOURCES:
        folder_name = FOLDER_NAME_DICT[comparison_source]
        SOURCES_COUNTRY_FILES[comparison_source] = util_ensemble_code.get_files_relative_folder(folder_name)
    country_names = (SOURCES_COUNTRY_FILES['propotional increase']).keys()
   # compare mean and std dev.
    #num_instances, mean, stddev, min/max,max/min, number of trials
    #################################
    # max point, within one second derivative.
    #################################
    max_point_country_dict = {}
    rel_point_country_dict = {}
    for country in country_names:
        max_point_country_dict[country] = [country]
        rel_point_country_dict[country] = [country]
    for comparison_source in COMPARISON_SOURCES:
        countries_data = SOURCES_COUNTRY_FILES[comparison_source]
        for country in countries_data:
            country_data = countries_data[country]
            cur_max_mean = 0
            cur_max_std_dev = 0
            cur_max_point = 0
            for line in country_data:
                cur_point = float(line[0])
                cur_mean = float(line[1])
                cur_stddev = float(line[2])
                if cur_mean > cur_max_mean + cur_max_std_dev/2.0: #change by 0.5 std dev.
                    cur_max_mean = cur_mean
                    cur_max_std_dev = cur_stddev
                    cur_max_point = cur_point
                elif cur_stddev < cur_max_std_dev/2.0: # current std dev is half of the max stddev.
                    cur_max_mean = cur_mean
                    cur_max_std_dev = cur_stddev
                    cur_max_point = cur_point
            x = max_point_country_dict[country]
            x.append(cur_max_point)
            x.append(cur_max_mean)
            x = rel_point_country_dict[country]
            x.append(cur_max_point)

    #################################
    # second derivative
    #################################
    for comparison_source in COMPARISON_SOURCES:
        countries_data = SOURCES_COUNTRY_FILES[comparison_source]
        for country in countries_data:
            country_data = countries_data[country]
            cur_max_point, cur_max_mean = get_second_derivative_mean_and_point(country_data)
            x = max_point_country_dict[country]
            x.append(cur_max_point)
            x.append(cur_max_mean)
            x = rel_point_country_dict[country]
            x.append(cur_max_point)
    # Final sec derivative change
    for comparison_source in COMPARISON_SOURCES:
        countries_data = SOURCES_COUNTRY_FILES[comparison_source]
        for country in countries_data:
            country_data = countries_data[country]
            cur_max_point, cur_max_mean = get_second_derivate_mean_and_point_final(country_data)
            x = max_point_country_dict[country]
            x.append(cur_max_point)
            x.append(cur_max_mean)
            x = rel_point_country_dict[country]
            x.append(cur_max_point)
    # Max sec derivative/ i.e most negative
    for comparison_source in COMPARISON_SOURCES:
        countries_data = SOURCES_COUNTRY_FILES[comparison_source]
        for country in countries_data:
            country_data = countries_data[country]
            cur_max_point, cur_max_mean = get_second_derivate_mean_and_point_max(country_data)
            x = max_point_country_dict[country]
            x.append(cur_max_point)
            x.append(cur_max_mean)
            x = rel_point_country_dict[country]
            x.append(cur_max_point)

    #################################
    #################################
    csv_writer = csv.writer(open(os.path.join(configs.system.PROJECT_ROOT,
                                              configs.system.DIR_DATA,
                                              configs.system.GENERATE_DATA_POINTS_FILE_PTS),"wb"))
    header_row = ["Country","Prop-Max Point","Double-Max Point","Random-Max Point",
                  "Prop-First Change in Sec Deriv","Double-First Change in Sec Deriv",
                  "Random-First Change in Sec Deriv","Prop-Last Change in Sec Deriv",
                  "Double-Last Change in Sec Deriv","Random-Last Change in Sec Deriv",
                  "Prop-Max(-ve) Change in Sec Deriv","Double-Max(-ve) Change in Sec Deriv",
                  "Random-Max(-ve) Change in Sec Deriv"]
    for i in other_points:
        y = "Propotional with Undersample/Oversample to "+str(i)+" per country"
        header_row.append(y)
    csv_writer.writerow(header_row)
    for key in sorted(rel_point_country_dict.iterkeys()):
        x = rel_point_country_dict[key]
        for i in other_points:
            x.append(i)
        csv_writer.writerow(x)


