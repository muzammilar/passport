# -*- coding: utf-8 -*-
"""

    ppcore.system.utils
    ~~~~~~~~~~~~~~

    This module contains utility functions for predictions
    by the Passport system checking for caches in memory and database, etc.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

###remove-me-later-muz###import ormsettings as DJANGO_SETTINGS
from ppstore.models import SYSTEM_PREDICTIONS
import traceback
import ppnamespace
from ppstore import traindata as training_data_file
import ensemble.utils as util_ensemble_code

USELESS_PREDICTED_COUNTRIES = ['EU']

def save_system_prediction_to_database_src_one(ip_addr, src, country, probability=None):
    try:
        sys_pred = SYSTEM_PREDICTIONS(ip=ip_addr, source=src, country=country)
        if probability is not None:
            sys_pred = SYSTEM_PREDICTIONS(ip=ip_addr, source=src, country=country,
                                        source_probability=probability)
        sys_pred.save()
    except:
        traceback.print_exc()


def save_system_predictions_to_database(ip_addr, src, country_list, country_probability_dict=None):
    # country_probability_dict is a sub structure, {cntry:prob}. 
    for country in country_list:
        if not country_probability_dict:
            save_system_prediction_to_database_src_one(ip_addr, src, country)
        else:
            save_system_prediction_to_database_src_one(ip_addr, src, country, country_probability_dict[country])


def truncate_system_predictions():
    try:
        print "Truncate SYSTEM_PREDICTIONS Table"
        SYSTEM_PREDICTIONS.objects.all().delete()
    except:
        print "Failed: Couldn't truncate SYSTEM_PREDICTIONS! Please do it manually."
        traceback.print_exc()
    print "Success: Truncate!"


def get_system_predictions_memory(predictions_dict):
    pred_sources = set()
    # get all sources from globals file
    ip = predictions_dict['ip']
    if ip in ppnamespace.overall:
        pred_sources.add(True)
        for ctry in ppnamespace.overall[ip]:
            predictions_dict['overall'].append(ctry) 
    if ip in ppnamespace.combined:
        pred_sources.add(True)
        for ctry in ppnamespace.combined[ip]:
            predictions_dict['combined'].append(ctry)
    if ip in ppnamespace.classifier:
        pred_sources.add(True)
        for ctry in ppnamespace.classifier[ip]:
            predictions_dict['classifier'].append(ctry)
    if ip in ppnamespace.area:
        pred_sources.add(True)
        for ctry in ppnamespace.area[ip]:
            predictions_dict['area'].append(ctry)
    if len(pred_sources) == 0:
        return False
    return True


def get_system_predictions_database(predictions_dict):
    ip = predictions_dict['ip']
    preds = SYSTEM_PREDICTIONS.objects.filter(ip=ip)
    pred_sources = set()
    for pred in preds:
        pred_sources.add(True)
        predictions_dict[pred.source].append(pred.country)
    if len(pred_sources) == 0:
        return False
    return True


def get_system_predictions(predictions_dict):
    if get_system_predictions_memory(predictions_dict):
        return True
    return get_system_predictions_database(predictions_dict)


def in_system_predictions_memory(ip):
    if ip in ppnamespace.overall or ip in ppnamespace.combined or ip in ppnamespace.classifier or ip in ppnamespace.area:
        return True
    return False


def in_system_predictions_database(ip):
    preds = SYSTEM_PREDICTIONS.objects.filter(ip=ip)
    pred_sources = set()
    for pred in preds:
        return True
    return False


def in_system_predictions(ip_addr):
    if in_system_predictions_memory(ip_addr):
        return True
    return in_system_predictions_database(ip_addr)

def perform_pred_classifier(ip, hostname, classifiers_from_disk):
    pred_results = []
    # read data from geosouces
    test_instance = training_data_file.get_test_data(ip,hostname)
    for loaded_cls in classifiers_from_disk:
        pred_data = loaded_cls.predict(test_instance)
        for i in xrange(len(pred_data)):
            if i % 2 == 0:
                pass
            else:
                pred_results.append(pred_data[i])
    #print pred_results
    # add ddec country if it's not there.
    pred_results.append(test_instance['DDECCountry'])
    pred_results = util_ensemble_code. \
                remove_useless_countries_from_classifier(pred_results) 
    return pred_results
