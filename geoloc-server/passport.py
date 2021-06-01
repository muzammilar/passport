# -*- coding: utf-8 -*-
"""

    passport.py
    ~~~~~~~~~~~

    Passport: A country-lvel router geolocation system
    This module implements the execution of main geolcation system (with website) of the Passport System.

    :author: Muzammil Abdul Rehman
    :credits: [Muzammil Abdul Rehman, Dave Choffnes, Sharon Goldberg]
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

__author__ = "Muzammil Abdul Rehman"
__copyright__ = "Northeastern University © 2018"
__license__ = "Custom BSD"
__email__ = "passport@ccs.neu.edu"


import sys
import os
import signal
import configs.system
from ppstore import traindata
import ppclassifier
from ppclassifier import GeoLocClassifier
###remove-me-later-muz###from ipwhois import IPWhois
import traceback
from flask import Flask, request, jsonify
import flask
import json
###remove-me-later-muz###import trparse
from multiprocessing import Process, Manager
from threading import Thread
import time
# -*- coding: utf-8 -*-
###remove-me-later-muz###from intervaltree import Interval, IntervalTree
import ensemble.extinfluence.quadratic
import ensemble.extinfluence.randomize
import ensemble.extinfluence.proportional
import ensemble.secondaryanalysis
import ensemble.datapts
import ensemble.utils as util_ensemble_code
import geosources
import pputils
from ppmeasurements import util as util_traceroutes
###remove-me-later-muz###import netaddr as ipaddress
import ppnamespace
import geosources.geolocation
from geosources import whois
###remove-me-later-muz###import logging
import ppcore.system.online
import ppcore.system.prediction as prediction_system
import ppcore.system.utils as util_geoloc_system
import routerinfo.aliases as router_alias_package
import world.geography
import datetime

WEB_SERVER_APP = Flask(__name__.split('.')[0], 
        static_folder=os.path.join(configs.system.WEB_PARENT_FOLDER, 
                configs.system.WEB_STATIC_FOLDER),
        template_folder=os.path.join(configs.system.WEB_PARENT_FOLDER, 
                configs.system.WEB_TEMPLATES_FOLDER))

##############################################################################
##############################################################################
# Web server - Starts

def get_whois_information(ip_address):
    """ Returns the WhoIS information for a speicific IP address"""
    return whois.get_whois_information(ip_address)


def run_web_server():
    """ This starts a webserver that listens and responds to user requests"""
    WEB_SERVER_APP.run(host=configs.system.SERVER_HOST,
            port=configs.system.SERVER_PORT, threaded=True,
            debug=configs.system.WEB_DEBUG_MODE)


@WEB_SERVER_APP.route('/')
def index_page():
    """ The index page when the user lands on the website"""
    #return flask.redirect(flask.url_for('v1_locate_ip_address_form'))
    return flask.render_template('index.html')


@WEB_SERVER_APP.route('/contact')
def contact_page():
    """ Return the page containing the contact infromation of the developers"""
    return flask.render_template('contact.html')


@WEB_SERVER_APP.route('/about')
def about_page():
    """ Return the page containing the infromation about the developers  and the project"""
    return flask.render_template('about.html')


@WEB_SERVER_APP.route('/interesting_cases')
def interesting_cases():
    return flask.render_template('interesting_cases.html')


@WEB_SERVER_APP.route('/locate_ip_address_form')
def v1_locate_ip_address_form():
    """ Returns a form to submit an IP address for geolocation """
    return flask.render_template('locate_ip_address_form.html')


@WEB_SERVER_APP.route('/api/v1/locatetrace', methods=['GET'])
@WEB_SERVER_APP.route('/api/v1/locate_traceroute', methods=['GET'])
@WEB_SERVER_APP.route('/api/v1/locateip', methods=['GET'])
@WEB_SERVER_APP.route('/api/v1/locate_ip_address', methods=['GET'])
def api_access_page():
    """ Return the redirection page for get requests to the API"""
    return flask.render_template('api_access.html')


@WEB_SERVER_APP.route('/locate_ip_address', methods=['POST'])
def v1_locate_ip_address():
    """ Returns the web page after posting a request to geolocate an IP address"""
    predictions_all = []
    ip_address = request.form['ip_address']    
    predictions_dict = v1_locateip(ip_address)
    predictions_all.append(predictions_dict)
    # package data in a traceroute object
    predictions_dict_traceroute = {'error': predictions_dict['error'],
                                   'error_type': predictions_dict['error_type'],
                                   'status': predictions_dict['status'],
                                   'completed': True,
                                   'dest_name': '',
                                   'dest_ip': '',
                                   'predictions': predictions_all}
    if predictions_dict_traceroute['status'] != 'finished':
        predictions_dict_traceroute['completed'] = False
    # get countries
    country_name_dict = {}      
    country_name_dict = {ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND[cde]:cde
                         for cde in ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND}
    return flask.render_template('locate_ip_address.html', traceroute_info_object=predictions_dict_traceroute,
                                 predictions=predictions_dict_traceroute['predictions'],
                                 status=predictions_dict_traceroute['status'],
                                 error_type=predictions_dict_traceroute['error_type'],
                                 error=predictions_dict_traceroute['error'], country_name_to_code=country_name_dict)


@WEB_SERVER_APP.route('/api/v1/locateip', methods=['POST'])
@WEB_SERVER_APP.route('/api/v1/locate_ip_address', methods=['POST'])
def v1_api_locate_ip_address():
    """ Requests an IP geolocation (using API) if not already requested, and returns the information about that
        IP address (if infromation is available)
    # input:  {'ip': 12.3.12.1}
    # output: {"status": "finished", "error_type": "private_IPv4_address", "area": [], "ip": "10.200.204.2",
    #           "hostname": "10.200.204.2", "overall": [], "combined": [], "hop": 1, "error": True, "classifier": []}
    """
    data = request.data
    return_data = {'error': True, 'error_type': 'Invalid Input'}

    try:
        data_dict = json.loads(data)
        if 'ip' not in data_dict or (type(data_dict['ip']) != str and type(data_dict['ip']) != unicode):
            return return_data
    except:
        return_data['error_type'] = 'Invalid Input: Please provide a JSON object.'
        return return_data                        
    predictions_dict = v1_locateip(data_dict['ip'])
    return jsonify(predictions_dict)


def v1_locateip(ip_address):
    """
    Requests the online system add an IP address to the measurement queue and return the result.
    :param ip_address: a string representation of an IPv4 address
    :return predictions_dict: A dictionary containing information about errors, predicted locations and status of IP.
    """
    #predictions_all = []
    predictions_dict = ppcore.system.online.get_predictions_ip_address(ip_address)
    #predictions_all.append(predictions_dict)
    #online_system.sort_on_hop_number(predictions_all)
    print_data = "v1_locateip: " + str(predictions_dict)
    WEB_SERVER_APP.logger.debug(print_data)
    return predictions_dict


@WEB_SERVER_APP.route('/locate_traceroute_form')
def v1_locate_traceroute_form():
    """ Returns the web page after posting a request to geolocate all IP addresses of a traceroute"""
    return flask.render_template('locate_traceroute_form.html')


@WEB_SERVER_APP.route('/locate_traceroute', methods=['POST'])
def v1_locate_traceroute():
    """ Returns the web page after posting a request to geolocate all IP addresses of a trsceroute"""
    traceroute_data = request.form['traceroute_data']    
    predictions_dict_traceroute = v1_locatetrace(traceroute_data)
    #WEB_SERVER_APP.logger.debug(globals_file.COUNTRY_ISO_CODE_DICT)
    country_name_dict = {}      
    country_name_dict = {ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND[cde]:cde
                         for cde in ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND}
    return flask.render_template('locate_traceroute.html',traceroute_info_object=predictions_dict_traceroute,
                                 predictions=predictions_dict_traceroute['predictions'],
                                 status=predictions_dict_traceroute['status'],
                                 error_type=predictions_dict_traceroute['error_type'],
                                 error=predictions_dict_traceroute['error'], country_name_to_code=country_name_dict)


@WEB_SERVER_APP.route('/api/v1/locatetrace', methods=['POST'])
@WEB_SERVER_APP.route('/api/v1/locate_traceroute', methods=['POST'])
def v1_api_locate_traceroute():
    """ Requests IP geolocation (using API) of all IPs in traceroutes if not already requested. Also parses and
    checks the validity of the traceroute.
    # input:  {'traceroute_data': "some string about traceroutes"}
    # output:
    {"status": "running", "dest_name": "10.200.204.2", "completed": False, "error_type": "", "predictions": [
        {"status": "finished", "error_type": "private_IPv4_address", "area": [], "ip": "10.200.204.2",
         "hostname": "10.200.204.2", "overall": [], "combined": [], "hop": 1, "error": True, "classifier": []},
        {"status": "running", "error_type": "", "area": [], "ip": "129.10.110.2", "hostname": "129.10.110.2",
         "overall": [], "combined": [], "hop": 2, "error": False, "classifier": []},
        {"status": "finished", "error_type": "private_IPv4_address", "area": [], "ip": "10.2.29.52",
         "hostname": "10.2.29.52", "overall": [], "combined": [], "hop": 3, "error": True, "classifier": []},
        {"status": "finished", "error_type": "private_IPv4_address", "area": [], "ip": "10.2.29.33",
         "hostname": "10.2.29.33", "overall": [], "combined": [], "hop": 4, "error": True, "classifier": []},
        {"status": "finished", "error_type": "private_IPv4_address", "area": [], "ip": "10.2.29.230",
         "hostname": "10.2.29.230", "overall": [], "combined": [], "hop": 5, "error": True, "classifier": []},
        {"status": "running", "error_type": "", "area": [], "ip": "207.210.142.101",
         "hostname": "nox1sumgw1-neu-cps.nox.org", "overall": [], "combined": [], "hop": 6, "error": False,
         "classifier": []}, {"status": "finished", "error_type": "",
                             "area": ["United States", "Canada", "Bermuda", "Saint Pierre and Miquelon"],
                             "ip": "198.71.47.61", "hostname": "et-10-0-0.122.rtr.eqch.net.internet2.ed",
                             "overall": ["United States"], "combined": ["United States"], "hop": 7, "error": False,
                             "classifier": ["United States"]},
        {"status": "running", "error_type": "", "area": [], "ip": "72.14.220.117", "hostname": "72.14.220.117",
         "overall": [], "combined": [], "hop": 8, "error": False, "classifier": []},
        {"status": "running", "error_type": "", "area": [], "ip": "108.170.243.193", "hostname": "108.170.243.193",
         "overall": [], "combined": [], "hop": 9, "error": False, "classifier": []},
        {"status": "running", "error_type": "", "area": [], "ip": "216.239.42.107", "hostname": "216.239.42.107",
         "overall": [], "combined": [], "hop": 10, "error": False, "classifier": []},
        {"status": "running", "error_type": "", "area": [], "ip": "216.58.192.206",
         "hostname": "ord30s25-in-f206.1e100.net", "overall": [], "combined": [], "hop": 11, "error": False,
         "classifier": []}], "error": False, "dest_ip": "10.200.204.2"}
     """

    data = request.data
    return_data = {'error': True, 'error_type': 'Invalid Input.', 'status': 'failed', 'predictions': []}

    try:
        data_dict = json.loads(data)
        if 'traceroute_data' not in data_dict or (type(data_dict['traceroute_data']) != str and type(data_dict['traceroute_data']) != unicode):
            return return_data  
    except:
        return_data['error_type'] = 'Invalid Input: Please provide a JSON object.'
        return return_data                        
        
    predictions_dict_traceroute = v1_locatetrace(str(data_dict['traceroute_data']))
    return jsonify(predictions_dict_traceroute)


def v1_locatetrace(traceroute_data_string):
    """
    Tries to parse a string and convert to machine-readable traceorute information. Then perform geolocation on
    all IP addresses
    :param traceroute_data_string: same data type as `func` v1_api_locate_traceroute()
    :return: same data type as `func` v1_api_locate_traceroute()
    """
    predictions_all = []
    return_data = {'error': False,
                   'error_type': '',
                   'status': 'running',
                   'completed': False,
                   'dest_name': '',
                   'dest_ip': '',
                   'predictions': predictions_all}

    # convert a stringt to a list using external libraries
    success, trparse_list = util_traceroutes.traceroute_string_to_list(traceroute_data_string)

    # if failed to parse the string for traceroute return
    if not success:
        return_data['status'] = 'failed'  # finished, failed, running,
        return_data['error'] = True
        return_data['error_type'] = 'Invalid Traceroute: Please provide a correct traceroute.'
        return return_data

    # if successful
    return_data['dest_name'] = trparse_list.dest_name
    return_data['dest_ip'] = trparse_list.dest_ip
    # for each hop request geolcation
    for hop in trparse_list.hops:
        # we only do one probe 
        hop_idx = hop.idx
        for probe in hop.probes:
            if probe.ip is None:
                continue
            hostname = probe.name
            if probe.name is None:
                hostname = ''
            predictions_dict = ppcore.system.online.get_predictions_ip_address(probe.ip, hostname, hop_idx)
            predictions_all.append(predictions_dict)
            break
    # sorting the results is important for website display
    ppcore.system.online.sort_on_hop_number(predictions_all)
    return_data['predictions'] = predictions_all
    return_data['status'] = 'finished'  # finished, failed, running,
    return_data['completed'] = True

    # check if all the IP addresses located
    for pred in predictions_all:
        if pred['status'] != 'finished':
            return_data['status'] = 'running'  # finished, failed, running,
    if return_data['status'] != 'finished':
        return_data['completed'] = False
    return return_data


@WEB_SERVER_APP.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404


@WEB_SERVER_APP.route('/api/v1/geosources', methods=['POST'])
def geosources():
    data = request.data
    data_list = json.loads(data)
    return json.dumps(geosources.geolocation.get_inaccurate_locations(data_list[0]))


@WEB_SERVER_APP.route('/api/v1/whois', methods=['POST'])
def whois():
    """ A function to get whois information about an ip address """
    #WEB_SERVER_APP.logger.warning('A warning occurred (%d apples)', 42)
    #WEB_SERVER_APP.logger.error('An error occurred')
    #WEB_SERVER_APP.logger.info('Info')
    data = request.data
    data_list = json.loads(data)
    #print data_list
    return json.dumps(whois.get_whois_information(data_list[0]))


@WEB_SERVER_APP.route('/api/v1/test_classifier', methods=['POST'])
def testclassifier():
    """ A function to test classifier predictions """
    data = request.data
    test_data = json.loads(data)
    pred_results = []
    for loaded_cls in ppnamespace.LOADED_CLASSIFIERS:
        pred_data = loaded_cls.predict(test_data)
        #print pred_data
        for i in xrange(len(pred_data)):
            if i % 2 == 0:
                elem = loaded_cls.classifier_name + "_" + pred_data[i]
            else:
                elem = pred_data[i]
            pred_results.append(elem)
    return json.dumps(pred_results)

# Web server - Ends
##############################################################################
##############################################################################



global RUNNING_PROCESSES
RUNNING_PROCESSES = []
global RUNNING_THREADS
RUNNING_THREADS = []
global MANAGER
MANAGER = Manager()
ppnamespace.init(MANAGER)

def close_program(graceful_close):
    """ Cleaning exit the system and kill all the processes """
    # close the flask process.
    #globals_file.SYSTEM_DICT_MAIN[configs.system.SYSTEM_PROC_RUNNING] = False
    for process in RUNNING_PROCESSES:
        try:
            if not graceful_close:
                process.terminate()
            process.join()
        except:
            pass
    sys.exit(0)


def signal_handler(signal, frame):
    close_program(False)


def redo_analysis():
    """Perfoms the offlline classifier analysis, only."""

    current_processes = []
    # primary analysis for three types of external influences (of number of instances) on the country prediction
    proc = Process(target=ensemble.extinfluence.quadratic.main)
    current_processes.append(proc)
    proc = Process(target=ensemble.extinfluence.randomize.main)
    current_processes.append(proc)
    proc = Process(target=ensemble.extinfluence.proportional.main)
    current_processes.append(proc)
    for proc in current_processes:
        RUNNING_PROCESSES.append(proc)
        proc.start()
    for proc in current_processes:
        proc.join()
        try:
            RUNNING_PROCESSES.remove(proc)
        except:
            pass

    # secondary analysis using second deriv and max points
    ensemble.secondaryanalysis.perform_secondary_analysis()

    # generate a file containing the number of instances :)
    ensemble.datapts.generate_data_points()
    # this is the folder called 8. if you want to compare with prop then take
    # number_against_countrydata.py file and rename it to generate_points_data
    # and then modify it like the seconday analysis file. but till then
    # use the points generated from secondary analysis file and add a simple
    # 30 and 50  instance classifier as well.


def train_classifiers_after_analyis():
    """ Train all the new classifiers after running an offline analysis on the ground truth."""

    # get country-based training data
    countries_with_count = traindata.get_all_countries()
    countries_with_count.sort(key=lambda k: k['count'])
    country_training_data = {}
    for country in countries_with_count:
        cnt_data = traindata.get_training_data_country(country)
        country_training_data[country['country']] = cnt_data

    # load the csv file containing the number of points for each classifier.
    DATA_PTS_FILES = util_ensemble_code.get_files_relative_folder('', '.csv')
    data_pts_file = DATA_PTS_FILES[configs.system.GENERATE_DATA_POINTS_FILE_PTS]
    IMPORTANT_COLUMNS = [2, 3, 7, 9, 13, 14]
    remove_symbols = [' ', '/', '(', ')']
    # train multiple variants of each classifier
    for i in range(configs.system.NUM_VARIANTS_CLS):
        for col in IMPORTANT_COLUMNS:
            f_name = data_pts_file[0][col]
            f_name = f_name.lower()
            for sym in remove_symbols:
                f_name = f_name.replace(sym, "_")
            f_name = f_name + "_" + str(i) + ".pkl"
            num_inst = {}
            for row in data_pts_file:
                cnt_nme = row[0].split('.txt')[0]
                try:
                    num_inst[cnt_nme] = int(float(row[col]))
                except:
                    num_inst[cnt_nme] = 1
            # get training data
            train = util_ensemble_code.choose_train_data(country_training_data,
                                                             num_inst)
            train = util_ensemble_code.add_nac(train, 50)
            # train
            print "Training: ", f_name
            geoloc_cls = GeoLocClassifier()
            geoloc_cls.train_classifier(train)
            if not ppclassifier.save_classifier(geoloc_cls, f_name):
                print "Failed to save:", f_name
            # save the classifier
            ppnamespace.LOADED_CLASSIFIERS.append(geoloc_cls)


def train_default_classifier():
    """ Train a classifier using the entire training dataset """
    train = traindata.get_training_data_all()
    train = util_ensemble_code.add_nac(train, 50)
    geoloc_cls_default = GeoLocClassifier()
    geoloc_cls_default.train_classifier(train)
    if not ppclassifier.save_classifier(geoloc_cls_default,
                                                     configs.system.DEFAULT_CLS_FILE):
        print "Failed to save a default classifier. Will serve only from mem."
        ppclassifier.delete_classifier(configs.system.DEFAULT_CLS_FILE)
    ppnamespace.LOADED_CLASSIFIERS.append(geoloc_cls_default)
    print "Default classifier saved."


def read_values_to_geo_sources():
    pputils.read_values_to_geo_sources()


def thread_process_geolocate_ip_addresses():
    """ A process that maintains a queue and schedules measurements from vantage points at regular intervals
    so as to never overwhelm the remote machines (VPs)"""
    while True:
        #print "IPs to look up:", globals_file.QUEUE_IPS_LOOKUP.qsize()
        # ip address processing thread
        ip_addresses_to_proc = []
        if ppnamespace.QUEUE_IPS_LOOKUP.empty():
            time.sleep(configs.system.THREAD_IP_PROCESSING_WAIT)
            continue
        while not ppnamespace.QUEUE_IPS_LOOKUP.empty():
            try:
                ip_addr_proc, hostname = ppnamespace.QUEUE_IPS_LOOKUP.get(False)
                suc = util_geoloc_system.in_system_predictions(ip_addr_proc)
                if suc:
                    continue
                ip_addresses_to_proc.append((ip_addr_proc, hostname))
                if len(ip_addresses_to_proc) >= configs.system.MAX_IPS_PROCESSING:
                    break
            except:
                traceback.print_exc()
                pass
        # schedule measurements for these all.
        thread_list = []
        for ip_addr,hostnm in ip_addresses_to_proc:
            p = Thread(target=ppcore.system.online.perform_measurement_prediction_ip_address, args=(ip_addr, hostnm,))
            p.daemon = False
            thread_list.append(p)
        for p in thread_list:
            p.start()
        for p in thread_list:
            p.join()
        try:
            del thread_list[:] #delete elements
        except:
            pass


def main():
    """The program to perform offline analysis (if necessary) then start background threads to setup the measurement
    system as well as the website"""
    # don't remove this line since strptime is not threadsafe
    datetime.datetime.strptime(datetime.datetime.now().strftime('%Y%m%d%H%M%S'),'%Y%m%d%H%M%S')
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Load classifiers either from disk or create new ones
    if configs.system.TRAIN_NEW_CLASSIFIERS:
        # train a default classifier
        train_default_classifier()

        # redo analysis
        redo_analysis()

        # retrain new classifiers and add them
        train_classifiers_after_analyis()
    elif configs.system.RETRAIN_CLASSIFIERS_WITHOUT_ANALYSIS_AGAIN:
        # train a default classifier
        train_default_classifier()
        # retrain new classifiers and add them
        train_classifiers_after_analyis()        
    else:
        classifiers_from_disk = ppclassifier.load_all_classifiers()
        for cls in classifiers_from_disk:
            ppnamespace.LOADED_CLASSIFIERS.append(cls)
    print "Loaded Classifiers"

    # Load past predictions
    # globals_file.overall, globals_file.classifier, globals_file.area, globals_file.combined =
    #       prediction_system.load_all_prediction_systems()
    prediction_system.load_all_prediction_systems_into_manager(ppnamespace.overall, ppnamespace.classifier,
                                                               ppnamespace.area, ppnamespace.combined)
    print "Loaded Prediction Systems"

    # Load router aliases and country maps
    ppnamespace.router_aliases_dict = router_alias_package.get_router_aliases() # move to parent function
    ppnamespace.country_polygon_dict = world.geography.load_country_maps() # move to parent function
    print "Loaded Maps and Aliases"

    # read global variable
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    pputils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND)
    # read the global variables
    pputils.read_values_to_geo_sources()

    # create threads and name them
    # thread-1: reads queue, processes the ip addresses as required (don't use processes)
    proc = Process(target=thread_process_geolocate_ip_addresses, name=configs.system.THREAD_NAME_IP_PROCESSING)
    RUNNING_PROCESSES.append(proc)
    proc.start()
    # thread-2: saves global structures (area, classifier, overall, combined) to disk

    # start the flask server, whois, test, test ensemble in a new process
    proc = Process(target=run_web_server)
    RUNNING_PROCESSES.append(proc)
    proc.start()

    # run the algorithm every x seconds and update the database.

    # close all
    close_program(True)


if __name__ == "__main__":
    main()
    #train_default_classifier()
    #train_classifiers_after_analyis()
    #ensemble_code.generate_data_points.main()
    """
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if configs.system.TRAIN_NEW_CLASSIFIERS:
        # train a default classifier
        train_default_classifier()
    else:
        classifiers_from_disk = ppclassifier.load_all_classifiers()
        for cls in classifiers_from_disk:
            globals_file.LOADED_CLASSIFIERS.append(cls)
    #main()
    p = Process(target=run_web_server)
    RUNNING_PROCESSES.append(p)
    p.start()

    close_program(True)

    """
