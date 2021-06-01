# -*- coding: utf-8 -*-
"""

    ensemble.extinfluence.quadratic
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module finds the decision tree sensitivity when twice number of training instances
    are used for other countries (see paper). Finding the change in accuracy of a country as
    the number of training instances of a country is increased while the number of
    training instances of other countries increased in the same manner as the country.
    This is finding the decision tree sensitivity to the number of training instances.


    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""
import csv
import threading
import random
import math
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


def choose_training_data(country_training_data, countries_with_less_instances, num_inst, cnt1):
    training_data = []
    for country in countries_with_less_instances:
        td_list =country_training_data[country]
        for td_instance in td_list:
            training_data.append(td_instance)
    for country in country_training_data:
        if country in countries_with_less_instances:
            continue
        if country == cnt1:
            x = random.sample(country_training_data[country],num_inst)
        else:
            num_inst2 = min(num_inst*2, len(country_training_data[country]))
            x = random.sample(country_training_data[country],num_inst2)
        for i in x:
            training_data.append(i)
    return training_data


def divide_countries_with_and_instances(country_count, num_inst):
    country_with_less_instances = []
    country_with_more_instances = []
    for country in country_count:
        if country_count[country] < num_inst:
            country_with_less_instances.append(country)
        else:
            country_with_more_instances.append(country)
    return country_with_less_instances, country_with_more_instances


def test_classifier(country_training_data, countries_with_more_instances, country, geoloc_cls):
    acc_dict = {}
    test_count_list = []
    t_list = []
    test_data_list = country_training_data[country]
    total_count = min(len(test_data_list),130)
    num_spawn_threads = 0
    test_data_list2 = random.sample(test_data_list,total_count)
    for testInstance in test_data_list2:
        num_spawn_threads += 1
        thread1 = threading.Thread(target=util_ensemble_code.test_classifier,
                                   args=(testInstance, test_count_list, geoloc_cls,))
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

def main():
    countries_with_count = traindata.get_all_countries()
    countries_with_count.sort(key=lambda k:k['count'])
    #print countries_with_count
    country_training_data ={}
    max_count = 0
    country_count = {}
    for country in countries_with_count:
        training_data = traindata.get_training_data_country(country)
        country_training_data[country['country']] = training_data
        max_count = country['count']
        country_count[country['country']] = country['count']
    cur_count = 0
    #start with a 0. nothing trained.
    util_ensemble_code.train_classifier([], 10)
    while cur_count <= max_count:
        countries_with_less_instances, countries_with_more_instances = divide_countries_with_and_instances(country_count, cur_count)
        country_acc_list_dict = {}
        for cnt in countries_with_more_instances:
            country_acc_list_dict[cnt] = []
        # repeat 500 times.
        for i in range(5):
            # chose cur_count training data
            for cnt1 in countries_with_more_instances:
                training_data = choose_training_data(country_training_data, countries_with_less_instances, cur_count, cnt1)
                trained_classifier = util_ensemble_code.train_classifier(training_data, cur_count)
                country_acc_dict = test_classifier(country_training_data, countries_with_more_instances, cnt1, trained_classifier)
                for cnt2 in country_acc_dict:
                    x = country_acc_list_dict[cnt2]
                    x.append(country_acc_dict[cnt2])
                    country_acc_list_dict[cnt2] = x
        for cnt3 in country_acc_list_dict:
            acc_list = country_acc_list_dict[cnt3]
            min_val = min(acc_list)
            max_val = max(acc_list)
            mean,stddev = util_ensemble_code.get_mean_std_dev(acc_list)
            w_f_name =cnt3+".txt"
            csvwriter = csv.writer(open(os.path.join(configs.system.PROJECT_ROOT, configs.system.DIR_DATA,
                                                     configs.system.ANALYSIS_FOLDER_DOUBLE, w_f_name),
                                        'ab'))
            csvwriter.writerow([cur_count, mean, stddev, min_val, max_val, len(acc_list)])
        if cur_count == 0:
            cur_count += 1
        else:
            cur_count *= 1.2
            cur_count = int(math.ceil(cur_count))

