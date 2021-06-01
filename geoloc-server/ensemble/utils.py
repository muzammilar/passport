# -*- coding: utf-8 -*-
"""

    ensemble.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains miscellaneous support functions for ensemble.
    This module contains miscellaneous functions, like removing
    senseless predictions by the classifiers, adding a class
    where classifiers fail (Not a Country or NaC), etc.



    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from ppclassifier import GeoLocClassifier
import threading
import random
import os
import configs.system
import csv
import math
import copy
acc_list_lock = threading.RLock()

def remove_useless_countries_from_classifier(cur_list):
    useless_countries = ['mq', 'unknown_country', '']
    cur_list = list(set(cur_list))
    for useless_cntry in useless_countries:
        try:
            cur_list.remove(useless_cntry)
        except:
            pass
    # convert names.
    names_dict = {} # names_dict[predicted name]=real name
    names_dict['Itsly']= 'Italy'
    names_dict['Phillipines'] = 'Philippines'
    for indx, country in enumerate(cur_list):         
        if country in names_dict:
            cur_list[indx] = names_dict[country]
    cur_list = list(set(cur_list))
    return cur_list


def transpose(cur_list):
    y = zip(*cur_list)
    new_list = [list(x) for x in y]
    return new_list


def add_nac(data, num_inst):
    data2 = []
    for cur_host in range(num_inst):
        cur_train_instance = {'asn': -1,
                              'ip': '',
                              'asn_registry': '',
                              'isp': '',
                              'isp_city': '',
                              'isp_region': '',
                              'DDECCountry': '',
                              'ASCountry': '',
                              'ISPCountry': '',
                              'db_ip_country': '',
                              'eurekapi_country': '',
                              'ip2location_country': '',
                              'ipinfo_country': '',
                              'maxmind_country': '',
                              'as_name': '',
                              'num_as_in_org': -1,
                              'num_ipv4_prefix_in_org': -1,
                              'num_ipv4_ip_in_org': -1,
                              'realcountry': "unknown_country"}
        #cur_train_instance['asn_cidr_bgp'] = getString(cur_host.asn_cidr_bgp)
        #cur_train_instance['hostname'] = getString(cur_host.hostname)
        data2.append(cur_train_instance)
    for d in data:
        data2.append(copy.deepcopy(d))
    return data2


def train_classifier(data, num_inst):
    train = add_nac(data, num_inst)
    geoloc_cls = GeoLocClassifier()
    try:
        geoloc_cls.train_classifier(train)
        return geoloc_cls
    except:
        print "Failed to train-classifier"
        return None


def test_classifier(instance, test_count_list, geoloc_cls):
    try:
        predicted_countries = geoloc_cls.predict(instance)
        pred_cnt = predicted_countries[1::2]  # 1,3,5,7
        if pred_cnt[0] == instance['realcountry']:
            with acc_list_lock:
                test_count_list.append(1)
    except:
        #print "Predicted: ", pred_cnt
        return False


def get_mean_std_dev(lst_vals):
    if lst_vals == []:
        return 0, 0
    mean = float(sum(lst_vals)) / len(lst_vals)
    if len(lst_vals) == 1:
        return mean, 0
    devSqr = [(x - mean) ** 2 for x in lst_vals]
    stddev = (float((sum(devSqr))) / (len(lst_vals) - 1)) ** 0.5
    return mean, stddev


def choose_train_data(country_training_data, num_inst):
    try:
        train_data = choose_train_data_number(country_training_data, num_inst)
    except:
        train_data = choose_train_data_dict(country_training_data, num_inst)
    return train_data


def choose_train_data_number(country_training_data, num_inst):
    x = int(num_inst)
    training_data = []
    for country in country_training_data:
        y = int(math.ceil(len(country_training_data[country]) / 2.00))
        x_extra = []
        if y < num_inst:
            x = random.sample(country_training_data[country], y)
            for iter_i in range(num_inst - y):
                x_extra.append(copy.deepcopy(random.choice(x)))
        else:
            x = random.sample(country_training_data[country], num_inst)
        for i in x:
            training_data.append(copy.deepcopy(i))
        for i in x_extra:
            training_data.append(copy.deepcopy(i))
    return training_data


def choose_train_data_dict(country_training_data, num_inst_dict):
    training_data = []
    for country in country_training_data:
        if country not in num_inst_dict:
            continue
        y = int(math.ceil(len(country_training_data[country]) / 2.00))
        x_extra = []
        num_inst = num_inst_dict[country]
        if y < num_inst:
            x = random.sample(country_training_data[country], y)
            for iter_i in range(num_inst - y):
                x_extra.append(copy.deepcopy(random.choice(x)))
        else:
            x = random.sample(country_training_data[country], num_inst)
        for i in x:
            training_data.append(copy.deepcopy(i))
        for i in x_extra:
            training_data.append(copy.deepcopy(i))
    return training_data


def random_combination(iterable, r):
    "Random selection from itertools.combinations(iterable, r)"
    pool = tuple(iterable)
    n = len(pool)
    indices = sorted(random.sample(xrange(n), r))
    return tuple(pool[i] for i in indices)


def get_files_relative_folder(folder_name, current_extension='.txt'):
    working_directory = os.listdir(os.path.join(configs.system.PROJECT_ROOT, configs.system.DIR_DATA,
                                                                folder_name))
    country_files_name = [f for f in working_directory
                          if (os.path.isfile(os.path.join(configs.system.PROJECT_ROOT,
                                                          configs.system.DIR_DATA,folder_name,f))
                              and f.endswith(current_extension))]
    country_file_dict = {}
    for country in country_files_name:
        country_file = os.path.join(configs.system.PROJECT_ROOT, configs.system.DIR_DATA, folder_name,
                                                                    country)
        csv_reader = csv.reader(open(country_file, 'rb'))
        file_in_memory = []
        for line in csv_reader:
            file_in_memory.append(line)
        country_file_dict[country] = file_in_memory
    return country_file_dict
