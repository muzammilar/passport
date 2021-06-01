# -*- coding: utf-8 -*-
"""

    ensemble.secondaryanalysis
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module looks at points from the points and their accuracies from the
    proportional increase, quadratic increase and randomize increase modules in
    ensemble.extinfluence and then get the ideal number of training instances
    for these classifiers. It finds the knee point (point of diminishing returns)
    and max accuracy for all the countries from the all three modules.




    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import csv
import threading
import random
from ppstore import traindata
import ensemble.utils as util_ensemble_code
import os
import configs.system


acc_list_lock = threading.RLock()


def choose_random_combos(data, sze):
    combos_list = []
    for i in range(1200):
        rand_items = random.sample(data,sze)
        if rand_items not in combos_list:
            combos_list.append(rand_items)
    return combos_list


def choose_training_data(country_training_data, num_train_instances):
    training_data = []
    for country in country_training_data:
        x = random.sample(country_training_data[country],num_train_instances[country])
        for i in x:
            training_data.append(i)
    return training_data

def get_countries_with_less_instances(country_count, num_inst):
    country_with_less_instances = []
    country_with_more_instances = []
    for country in country_count:
        if country_count[country] < num_inst:
            country_with_less_instances.append(country)
        else:
            country_with_more_instances.append(country)
    return country_with_less_instances, country_with_more_instances

def test_classifier(country_training_data, countriesWithMoreInstances, country, geoloc_cls):
    acc_dict = {}
    test_count_list = []
    t_list = []
    test_data_list = country_training_data[country]
    total_count = min(len(test_data_list),200)
    num_spawn_threads = 0
    test_data_list2 = random.sample(test_data_list,total_count)
    for testInstance in test_data_list2:
        num_spawn_threads += 1
        thread1 = threading.Thread(target=util_ensemble_code.test_classifier, args=(testInstance, test_count_list, geoloc_cls,))
        thread1.daemon = True
        thread1.start()
        t_list.append(thread1)
        if num_spawn_threads%25 == 0:
            num_spawn_threads = 0
            for t in t_list:
                t.join()
            t_list = []
    for t in t_list:
        t.join()
    test_count = sum(test_count_list)
    acc = test_count*100.0/total_count
    acc_dict[country] = acc
    #print acc_dict
    return acc_dict


def get_second_derivate_mean_and_point(country_data):
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



def get_all_second_derivatives_and_max_points(COMPARISON_SOURCES, SOURCES_COUNTRY_FILES, rel_point_country_dict):
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
            x = rel_point_country_dict[country]
            x.append(cur_max_point)
    for comparison_source in COMPARISON_SOURCES:
        countries_data = SOURCES_COUNTRY_FILES[comparison_source]
        for country in countries_data:
            country_data = countries_data[country]
            cur_max_point, cur_max_mean = get_second_derivate_mean_and_point(country_data)
            x = rel_point_country_dict[country]
            x.append(cur_max_point)
    # Final sec derivative change
    for comparison_source in COMPARISON_SOURCES:
        countries_data = SOURCES_COUNTRY_FILES[comparison_source]
        for country in countries_data:
            country_data = countries_data[country]
            cur_max_point, cur_max_mean = get_second_derivate_mean_and_point_final(country_data)
            x = rel_point_country_dict[country]
            x.append(cur_max_point)
    # Max sec derivative/ i.e most negative
    for comparison_source in COMPARISON_SOURCES:
        countries_data = SOURCES_COUNTRY_FILES[comparison_source]
        for country in countries_data:
            country_data = countries_data[country]
            cur_max_point, cur_max_mean = get_second_derivate_mean_and_point_max(country_data)
            x = rel_point_country_dict[country]
            x.append(cur_max_point)
    return rel_point_country_dict


def perform_secondary_analysis():
    COMPARISON_SOURCES = ['propotional increase','double increase','random increase']
    FOLDER_NAME_DICT = {'propotional increase':'proportional','double increase':'double','random increase':'random'}
    SOURCES_COUNTRY_FILES = {}
    # Get files
    for comparison_source in COMPARISON_SOURCES:
        folder_name = FOLDER_NAME_DICT[comparison_source]
        SOURCES_COUNTRY_FILES[comparison_source] = util_ensemble_code.get_files_relative_folder(folder_name)
    rel_point_country_dict = {}
    country_source_accuracy = {}
    country_names = (SOURCES_COUNTRY_FILES['propotional increase']).keys()
    for country in country_names:
        country1 = country.split('.txt')[0]
        rel_point_country_dict[country] = [country1]
        country_source_accuracy[country1] = [country1]
    #################################################################
    rel_point_country_dict = get_all_second_derivatives_and_max_points(COMPARISON_SOURCES,
                                                                       SOURCES_COUNTRY_FILES,
                                                                       rel_point_country_dict)
    ###############################################################################
    countries_with_count = traindata.get_all_countries()
    countries_with_count.sort(key=lambda k:k['count'])
    #print countries_with_count
    country_training_data ={}
    country_count = {}
    for country in countries_with_count:
        trainingData = traindata.get_training_data_country(country)
        country_training_data[country['country']] = trainingData
        country_count[country['country']] = country['count']
    #start with a 0. nothing trained.
    util_ensemble_code.train_classifier([], 10)
    classifiers_type_list = ["Country","Prop-Max Point","Double-Max Point","Random-Max Point",
                             "Prop-First Change in Sec Deriv","Double-First Change in Sec Deriv",
                             "Random-First Change in Sec Deriv","Prop-Last Change in Sec Deriv",
                             "Double-Last Change in Sec Deriv","Random-Last Change in Sec Deriv",
                             "Prop-Max(-ve) Change in Sec Deriv","Double-Max(-ve) Change in Sec Deriv",
                             "Random-Max(-ve) Change in Sec Deriv"]
    for iter_i in range(1,len(classifiers_type_list)):
        num_train_instances = {}
        #print iter_i
        for country_2 in country_count:
            try:
                num_train_instances[country_2] = int(rel_point_country_dict[country_2+".txt"][iter_i])
            except:
                num_train_instances[country_2] = 0
        country_acc_list_dict = {}
        for cnt in country_count:
            country_acc_list_dict[cnt] = []
        # repeat 500 times.
        for i in range(10):
            # chose cur_count training data
            trainingData = choose_training_data(country_training_data, num_train_instances)
            trained_classifier = util_ensemble_code.train_classifier(trainingData, 40)
            for cnt1 in country_count:
                country_acc_dict = test_classifier(country_training_data, country_count, cnt1, trained_classifier)
                for cnt2 in country_acc_dict:
                    x = country_acc_list_dict[cnt2]
                    x.append(country_acc_dict[cnt2])
                    country_acc_list_dict[cnt2] = x
        for cnt3 in country_acc_list_dict:
            acc_list = country_acc_list_dict[cnt3]
            #min_val = min(acc_list)
            #max_val = max(acc_list)
            mean, stddev = util_ensemble_code.get_mean_std_dev(acc_list)
            if cnt3 not in country_source_accuracy:
                #print cnt3
                continue
            x = country_source_accuracy[cnt3]
            x.append(mean)
            x.append(stddev)
    csv_writer = csv.writer(open(os.path.join(configs.system.PROJECT_ROOT,
                                              configs.system.DIR_DATA,
                                              configs.system.SECONDARY_ANALYSIS_FILE),"wb"))
    csv_writer.writerow(["Country","Prop-Max Point","","Double-Max Point","",
                         "Random-Max Point","","Prop-First Change in Sec Deriv","",
                         "Double-First Change in Sec Deriv","","Random-First Change in Sec Deriv","",
                         "Prop-Last Change in Sec Deriv","","Double-Last Change in Sec Deriv","",
                         "Random-Last Change in Sec Deriv","","Prop-Max(-ve) Change in Sec Deriv","",
                         "Double-Max(-ve) Change in Sec Deriv","","Random-Max(-ve) Change in Sec Deriv",""])
    for key in sorted(country_source_accuracy.iterkeys()):
        csv_writer.writerow(country_source_accuracy[key])



