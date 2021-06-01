# -*- coding: utf-8 -*-
"""

    ppcore.system.prediction
    ~~~~~~~~~~~~~~

     This module uses the utility and intersection modules of this system.
     It assumes that all the measurements have been performed and data has
     been cached. It first loads traceroute measurements with respective ping
     measurements, perform intersections for both the revtr and Ripe Atlas
     measurements, predict the countries from the classifiers, applies the Passport
     aggregation algorithm for the predictions and stores the  predictions for
     all IP addresses in different .pkl files.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import configs.system
import configs.intersection
import configs.traceroutes
import configs.pvt
import os
import ppnamespace
from ppmeasurements import traceroute, ping
import geosources.ipinfo as ip_info
from multiprocessing import Manager
import pickle
import routerinfo.aliases as router_alias_package
from ppcore.intersectalgo import get_box
import traceback
from ppcore import ppbox
import json
import ppmeasurements.ripeatlas as ripe_data_proc
import socket
import csv
import world.geography
import ppclassifier
from ppstore import feedback
import ppstore.traindata as training_data_file
import geosources.ddec as ddec
from ppcore.system import rttintersect
from ppcore.system import utils as util_geoloc_system
import pputils as utils

#######################################################################
# useless coutnries for sources and others
USELESS_PREDICTED_COUNTRIES = util_geoloc_system.USELESS_PREDICTED_COUNTRIES
#######################################################################

DATA_FOLDER = 'data'
# all ips and hostnames as (ip, hostname)
ALL_IPS_FILE = "all_ips_file.pkl" # contains [ tuple(ip, hostname) ...]
# contains dump for ripe probes
RIPE_NODE_INFO_FILE = 'ripe_node_info.pkl'
# hostname files
RIPE_IPS_HOSTNAMES_FILE = 'ripe_ips_hostnames.pkl'  # only contains {ip_int:hostname}
TRACEROUTE_IPS_FILE = 'trace_ips.pkl'  # contains set( tuple(ip_str, hostname) ...), set not a list
TRACEROUTE_IPS_HOSTNAME_DICT_FILE = 'trace_ips_dict.pkl'  # only contains {ip_str:hostname}
# cotain rtts for different detinations. ip addresses are in integer
TRACEROUTE_IPS_RTT_FILE = 'trace_ips_with_rtt.pkl'
RIPE_IPS_RTT_FILE = 'ripe_ips_with_rtt.pkl'
# these two files are loaded. they already have intersection boxes
TRACEROUTE_IPS_LATLON_FILE = 'trace_ips_with_latlon.pkl'
RIPE_IPS_LATLON_FILE = 'ripe_ips_with_latlon.pkl'
# file for alidade
ALIDADE_IP_FILE = 'alidade.csv'
# area prediction files
TRACEROUTE_PREDICTIONS_DUMP_FILE = 'trace_area_predictions.pkl'
RIPE_PREDICTIONS_DUMP_FILE = 'ripe_area_predictions.pkl'
AREA_PREDICTIONS_ALL = "all_area_predictions.pkl"
CLASSIFIER_PREDICTIONS_DUMP_FILE = 'classifier_predictions.pkl'
# system predicition file. combines both above files and classifier
OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE = 'overall_predictions.pkl'
# use these files whenever you wanna read something. they should have majority of ips
# RIPE_IPS_HOSTNAMES_FILE
# TRACEROUTE_IPS_FILE
# better yet, use this file, after we generate it.
# ALL_IPS_FILE
#######################################################################




def main():
    print "load_intersect_traceroute_traceroutes"
    load_intersect_traceroute_traceroutes()
    print "intersect_traceroute_ips"
    intersect_traceroute_ips()
    print "load_ripe_traceroutes"
    load_ripe_traceroutes()
    print "intersect_ripe_ips"
    intersect_ripe_ips()
    print "Generating file to request alidade"
    #generate_ips_for_alidade()
    print "Getting all unique IPs"
    get_all_unique_ips_hostnames()
    print "Get hostnames from DDEC"
    get_hostnames_from_ddec()
    print "perform_predictions"
    perform_predictions()
    print "generate_prediction_statistics"
    generate_prediction_statistics()
    print "Adding Prediction System to database"
    add_prediction_system_to_database()

def test():
    ip = "80.231.152.33"
    area_pred_dict = load_pickle(AREA_PREDICTIONS_ALL)
    classifier_pred_dict= load_pickle(CLASSIFIER_PREDICTIONS_DUMP_FILE)
    print "Area:", area_pred_dict[ip]
    print "Classifier:", classifier_pred_dict[ip]



def predict_ip_address_locations_new_measurement():
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    utils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    utils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND)
    utils.read_values_to_geo_sources()
    ips = ["4.68.63.202", "213.244.164.205", "208.178.194.126","208.178.194.206"]
    for ip in ips:
        try:
            ip_hostname = socket.gethostbyaddr(ip)[0]
        except:
            ip_hostname = ''
        traceroute.get_geolocation_sources_info((ip, ip_hostname))
        
    src_info_dict = {} # it's empty for now, move it to parent function
    router_aliases_dict = router_alias_package.get_router_aliases() # move to parent function
    country_polygon_dict = world.geography.load_country_maps() # move to parent function
    classifiers_from_disk = ppclassifier.load_all_classifiers() #move to parent function   
    for ip_str in ips:
        hostname = '' #change it 
        print ip_str
        print "SoL:", rttintersect.get_ip_rtt_intersection(ip_str, country_polygon_dict, src_info_dict, router_aliases_dict)
        print "Classifier:", perform_pred_classifier(ip_str, hostname, classifiers_from_disk)
        

def test_update_overall():
    system_predictions = load_pickle(OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    ground_truth_from_database = training_data_file.get_ground_truth_all()
    for ip in ground_truth_from_database:
        if ip in system_predictions['overall']:
            continue
        overall = [ground_truth_from_database[ip]]
        system_predictions['overall'][ip] = overall
    # save
    save_pickle(system_predictions,OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    

def test_ip_predictions():
    system_predictions = load_pickle(OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    combined = system_predictions['combined']
    overall = system_predictions['overall']
    area_pred_dict = load_pickle(AREA_PREDICTIONS_ALL)
    classifier_pred_dict= load_pickle(CLASSIFIER_PREDICTIONS_DUMP_FILE)
    ips = ["4.68.63.202", "213.244.164.205", "208.178.194.126","208.178.194.206"]
    for ip in ips:
        try:
            print "Overall:", overall[ip]          
            print "Area:", area_pred_dict[ip]
            print "Classifier:", classifier_pred_dict[ip]
        except:
            print "Failed:",ip 

def load_all_prediction_systems():
    system_predictions = load_pickle(OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    combined = system_predictions['combined']
    overall = system_predictions['overall']
    area = load_pickle(AREA_PREDICTIONS_ALL)
    classifier = load_pickle(CLASSIFIER_PREDICTIONS_DUMP_FILE)
    return overall, classifier, area, combined

def load_all_prediction_systems_into_manager(overall, classifier, area, combined):
    system_predictions = load_pickle(OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    _combined = system_predictions['combined']
    for x in _combined:
        combined[x] = _combined[x]
    _overall = system_predictions['overall']
    for x in _overall:
        overall[x] = _overall[x]
    _area = load_pickle(AREA_PREDICTIONS_ALL)
    for x in _area:
        area[x] = _area[x]
    _classifier = load_pickle(CLASSIFIER_PREDICTIONS_DUMP_FILE)
    for x in _classifier:
        classifier[x] = _classifier[x]



def add_prediction_system_to_database():
    system_predictions = load_pickle(OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    combined = system_predictions['combined']
    overall = system_predictions['overall']
    area = load_pickle(AREA_PREDICTIONS_ALL)
    classifier = load_pickle(CLASSIFIER_PREDICTIONS_DUMP_FILE)
    util_geoloc_system.truncate_system_predictions()
    for ip in overall:
        util_geoloc_system.save_system_predictions_to_database(ip, 'overall', overall[ip])
    for ip in classifier:
        util_geoloc_system.save_system_predictions_to_database(ip, 'classifier', classifier[ip], country_probability_dict=None)
    for ip in combined:
        util_geoloc_system.save_system_predictions_to_database(ip, 'combined', combined[ip])
    for ip in area:
        util_geoloc_system.save_system_predictions_to_database(ip, 'area', area[ip])

#######################################################################
#######################################################################
def save_pickle(obj, file_name):
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    write_file = os.path.join(cur_dir, DATA_FOLDER,file_name)
    if not os.path.exists(os.path.join(cur_dir, DATA_FOLDER)):
        os.makedirs(os.path.join(cur_dir, DATA_FOLDER))
    with open(write_file,'w') as handle:
        pickle.dump(obj, handle)
    
def load_pickle(file_name):
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    read_file = os.path.join(cur_dir, DATA_FOLDER,file_name)
    with open(read_file,'r') as handle:
        obj = pickle.load(handle)
    return obj


#######################################################################
#######################################################################

def perform_predictions():
    perform_area_prediction_from_all_sources()
    perform_classifier_predictions()
    perform_overall_prediction()

#######################################################################

def perform_overall_prediction():
    classifiers_from_disk = ppclassifier.load_all_classifiers()
    total_num_classifiers = len(classifiers_from_disk)
    ground_truth_from_database = training_data_file.get_ground_truth_all()
    # read the classifier file and area file
    system_predictions = {}
    system_predictions['combined'] = {}
    system_predictions['overall'] = {}
    ip_hostname_set = load_pickle(ALL_IPS_FILE)
    classifier_pred_dict= load_pickle(CLASSIFIER_PREDICTIONS_DUMP_FILE)
    area_pred_dict = load_pickle(AREA_PREDICTIONS_ALL)
    total = len(ip_hostname_set)
    counter = 0
    for ip,hostname in ip_hostname_set:
        # useless print
        counter += 1
        if counter % 500 == 0:
            print "Overall predictions:", counter, "| Total:", total
        if type(ip) == int:
            ip = utils.ip_int_to_string(ip)
        # apply feedback
        try:
            if ip in area_pred_dict and len(area_pred_dict[ip]) <= configs.system.FEEDBACK_MAX_COUNTRIES:
                feedback.add_feedback_to_ground(ip, area_pred_dict[ip])
        except:
            traceback.print_exc()
        # get both results
        area_results = []
        if ip in area_pred_dict:
            area_results = area_pred_dict[ip]
        classifier_results = []
        if ip in classifier_pred_dict:
            classifier_results = classifier_pred_dict[ip]
        # combined. these are the countries in both
        combined = []
        for area_country in area_results:
            for cls_country in classifier_results:
                if area_country.lower()==cls_country.lower():
                    combined.append(cls_country)
                    break
        # overall
        overall = []
        if len(area_results)== 1:
            overall = area_results[:]
        elif ip in ground_truth_from_database:      # direct from ground truth
            overall = [ground_truth_from_database[ip]]
        elif len(area_results)== 0:
            overall = classifier_results[:]
        else:
            if len(combined) == 0 and len(area_results) <= len(classifier_results):
                overall = area_results[:]
            else:
                overall = combined[:]
        # aggregate the results
        system_predictions['combined'][ip] = combined
        system_predictions['overall'][ip] = overall
    for ip in ground_truth_from_database:
        if ip in system_predictions['overall']:
            continue
        overall = [ground_truth_from_database[ip]]
        system_predictions['overall'][ip] = overall
    # save
    save_pickle(system_predictions,OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    


#######################################################################

def perform_classifier_predictions():
    # load all ip, hostname pairs
    classifier_pred_dict = {}
    ip_hostname_set = load_pickle(ALL_IPS_FILE)
    classifiers_from_disk = ppclassifier.load_all_classifiers()
    counter = 0
    total = len(ip_hostname_set)
    for ip,hostname in ip_hostname_set:
        if type(ip) == int:
            ip = utils.ip_int_to_string(ip)
        # useless print
        counter += 1
        if counter % 500 == 0:
            print "Classifier predictions:", counter, "| Total:", total
        # perform classifier predictions
        pred_results = perform_pred_classifier(ip, hostname, classifiers_from_disk)
        classifier_pred_dict[ip] = pred_results
    # save
    save_pickle(classifier_pred_dict,CLASSIFIER_PREDICTIONS_DUMP_FILE)

def perform_pred_classifier(ip, hostname, classifiers_from_disk):
    return util_geoloc_system.perform_pred_classifier(ip, hostname, classifiers_from_disk)

#######################################################################

def perform_area_prediction_from_all_sources():
    print "Predicting countries for Traceroutes."
    perform_area_prediction(TRACEROUTE_IPS_LATLON_FILE,TRACEROUTE_PREDICTIONS_DUMP_FILE)
    print "Predicting countries for Ripe Atlas."
    perform_area_prediction(RIPE_IPS_LATLON_FILE, RIPE_PREDICTIONS_DUMP_FILE)
    print "Combining countries for area sources."
    perform_area_prediction_combine_results([RIPE_PREDICTIONS_DUMP_FILE, TRACEROUTE_PREDICTIONS_DUMP_FILE])


def perform_area_prediction(input_file_name_lat_lon, output_file_name):
    # read both primary and secondary lists, use a boolean if secondary
    area_pred_dict = {} # a dict of dict with each value as lists. {ip_str:{'countries':[], 'secondary_prediction':True}}
    analysis_data = load_pickle(input_file_name_lat_lon)
    country_polygon_dict = world.geography.load_country_maps()
    
    for ip_bx in analysis_data['ip_intersection_box_list']:
        get_area_pred_countries_single_box(ip_bx, country_polygon_dict,area_pred_dict,False)
        
    for ip_bx in analysis_data["ip_intersection_box_list_second"]:
        get_area_pred_countries_single_box(ip_bx, country_polygon_dict,area_pred_dict,True)

    save_pickle(area_pred_dict,output_file_name)
    pass


def get_intersection_boxes_ip_dict(input_file_name_lat_lon):
    return_dict = {}
    analysis_data = load_pickle(input_file_name_lat_lon)
    for ip_bx in analysis_data["ip_intersection_box_list_second"]:
        return_dict[ip_bx['ip']] = ip_bx
        
    for ip_bx in analysis_data['ip_intersection_box_list']:
        return_dict[ip_bx['ip']] = ip_bx
        
    return return_dict


def get_area_pred_countries_single_box(ip_bx, country_polygon_dict, area_pred_dict, secondary=False):
    ip_address = ip_bx['ip']
    area_results = world.geography.detect_region(country_polygon_dict,
                                                 ip_bx['lat_bottom_left'], ip_bx['lon_bottom_left'],
                                                 ip_bx['lat_top_right'], ip_bx['lon_top_right'])
    ip_dict = {}
    ip_dict['countries'] = [country_tuple[0] for country_tuple in area_results]
    ip_dict['secondary_prediction'] = secondary
    area_pred_dict[ip_address] = ip_dict
    return area_pred_dict


def perform_area_prediction_combine_results(list_prediction_files):
    area_pred_dict = {} # dict with each value as lists. {ip_str:[]}
    # load all files
    prediction_data_files = {}
    prediction_data_files_list = []
    ip_set = set()
    for file_name in list_prediction_files:
        analysis_data = load_pickle(file_name)
        prediction_data_files[file_name] = analysis_data
        prediction_data_files_list.append(analysis_data)
        for ip_addr in analysis_data:
            ip_set.add(ip_addr)
    
    for ip_addr in ip_set:
        # try intersection
        possible_countries = None
        for pred_file in prediction_data_files_list:
            if ip_addr not in pred_file:
                continue
            if possible_countries is None:
                possible_countries = set(pred_file[ip_addr]['countries'])                
            possible_countries = possible_countries.intersection(set(pred_file[ip_addr]['countries']))
        if len(possible_countries) > 0:
            area_pred_dict[ip_addr] = list(possible_countries)
            continue
        # if it fails try union
        possible_countries = set()
        for pred_file in prediction_data_files_list:
            if ip_addr not in pred_file:
                continue
            possible_countries = possible_countries.union(set(pred_file[ip_addr]['countries']))
        area_pred_dict[ip_addr] = list(possible_countries)
        
    save_pickle(area_pred_dict,AREA_PREDICTIONS_ALL)
    

#######################################################################
#######################################################################


def generate_prediction_statistics():
    # read all the data
    ip_hostname_set = load_pickle(ALL_IPS_FILE)
    classifier = load_pickle(CLASSIFIER_PREDICTIONS_DUMP_FILE)
    area = load_pickle(AREA_PREDICTIONS_ALL)
    system_predictions = load_pickle(OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    combined = system_predictions['combined']
    overall = system_predictions['overall']
    mechanisms = [classifier,area,combined,overall]
    statistics_dict = {}
    mechanism_names = ['classifier','area','combined','overall']
    for mech_name in mechanism_names:
        statistics_dict[mech_name] = {}
    total_addresses = len(ip_hostname_set)
    # create a sparse dict
    max_country_number = 0
    for ip,hostname in ip_hostname_set:
        if type(ip) == int:
            ip = utils.ip_int_to_string(ip)
        for mechanism_name, mechanism in zip(mechanism_names, mechanisms):            
            mech_results = []
            if ip in mechanism:
                mech_results = mechanism[ip]
            num_countries = len(mech_results)
            max_country_number = max(max_country_number, num_countries)    
            if num_countries not in statistics_dict[mechanism_name]:
                statistics_dict[mechanism_name][num_countries] = 0
            statistics_dict[mechanism_name][num_countries] += 1
    # write to file now
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    write_file_name = os.path.join(cur_dir, DATA_FOLDER,"prediction_stats.csv")
    if not os.path.exists(os.path.join(cur_dir, DATA_FOLDER)):
        os.makedirs(os.path.join(cur_dir, DATA_FOLDER))
    write_file = open(write_file_name, 'wb')
    csvw = csv.writer(write_file)
    header = ["num_countries"]
    for mech_name in mechanism_names:
        header.append(mech_name)
    csvw.writerow(header)
    for i in range(max_country_number+1):
        row_to_write = [i]
        for mech_name in mechanism_names:
            if i in statistics_dict[mech_name]:
                row_to_write.append(statistics_dict[mech_name][i]*100.00/total_addresses)
            else:
                row_to_write.append(0.0)
        csvw.writerow(row_to_write)

#######################################################################
#######################################################################

def get_all_unique_ips_hostnames():
    traceroutes_data = load_pickle(TRACEROUTE_IPS_FILE)
    ripe_data = load_pickle(RIPE_IPS_HOSTNAMES_FILE)
    ip_set = set()
    ip_hostname_set = set()
    hostname_only_set =set()
    # trace
    for ip,hostname in traceroutes_data:
        if ip not in ip_set:
            ip_hostname_set.add((ip,hostname))
        hostname_only_set.add(hostname)
        ip_set.add(ip)
    # ripe        
    for ip in ripe_data:
        hostname = ripe_data[ip]
        if ip not in ip_set:
            ip_hostname_set.add((ip,hostname))        
        hostname_only_set.add(hostname)
        ip_set.add(ip)
    save_pickle(ip_hostname_set, ALL_IPS_FILE)
    print "Trace IPs:", len(traceroutes_data)
    print "Ripe IPs:", len(ripe_data)
    print "Union:", len(ip_hostname_set)


#######################################################################
#######################################################################

def slice_per(source, step):
    return [source[i::step] for i in range(step)]


def get_hostnames_from_ddec():
    traceroutes_data = load_pickle(TRACEROUTE_IPS_FILE)
    ripe_data = load_pickle(RIPE_IPS_HOSTNAMES_FILE)
    ip_set = set()
    ip_hostname_set = set()
    hostname_only_set =set()
    # trace
    for ip,hostname in traceroutes_data:
        if ip not in ip_set:
            ip_hostname_set.add((ip,hostname))
        hostname_only_set.add(hostname)
        ip_set.add(ip)
    # ripe        
    for ip in ripe_data:
        hostname = ripe_data[ip]
        if ip not in ip_set:
            ip_hostname_set.add((ip,hostname))        
        hostname_only_set.add(hostname)
        ip_set.add(ip)
    get_hostnames_if_possible(hostname_only_set)


def get_hostnames_if_possible(hostname_only_set): 
    hostname_list = list(hostname_only_set)
    total_hostnames = len(hostname_list)
    looked_hostnames = 0
    hostname_list_list = slice_per(hostname_list, 15)
    for hostname_list in hostname_list_list:
        try:
            ddec.search_and_store_ddec_hostnames(hostname_list)
        except:
            traceback.print_exc()
        looked_hostnames += len(hostname_list)
        print "Set of hostnames done: ", looked_hostnames, "| Total hostnames:", total_hostnames

#######################################################################
#######################################################################
def load_ripe_traceroutes():
    traceroutes_dir = os.path.join(configs.system.PROJECT_ROOT,
                                   configs.intersection.traceroute_pkg_folder,
                                   configs.traceroutes.RIPE_PARENT_FOLDER,
                                   configs.traceroutes.RIPE_RAW_FOLDER)
    return_data_dict = {}
    meta_info_dict={"traces":0,"pings":0}
    for trace_file_id in os.listdir(traceroutes_dir):
        if trace_file_id in configs.intersection.ignore_files:
            continue
        # read tracefile, parse
        print "Processing file with msm_id:", trace_file_id
        return_data_dict = ripe_data_proc.load_results_file(trace_file_id, return_data_dict, meta_info_dict)
    save_pickle(return_data_dict, RIPE_IPS_RTT_FILE)
    # save 
    label_save_hostnames_ripe()
    print "Unique IP addresses: ", len(return_data_dict)
    print "Total traceroutes: ", meta_info_dict["traces"]
    print "Total pings: ", meta_info_dict["pings"]


def label_save_hostnames_ripe():
    # saves as {ip_int: hostname}
    ripe_data = load_pickle(RIPE_IPS_RTT_FILE)
    # labelling hostnames
    print "Saving Ripe Hostnames."
    try:
        data_dict_hostnames = load_pickle(RIPE_IPS_HOSTNAMES_FILE)
        print "Older file loaded"
    except:
        data_dict_hostnames = {}
    counter = len(data_dict_hostnames)
    for hp in ripe_data:
        #print "IP: ",ip,"| ", hostname,"| counter:", counter        
        if counter % 100 == 0:
            print "IP addresses looked up for hostname:", len(data_dict_hostnames), "| Total:", len(ripe_data)           
            save_pickle(data_dict_hostnames, RIPE_IPS_HOSTNAMES_FILE)
        counter += 1
        try:
            ip = utils.ip_int_to_string(hp)
            if hp in data_dict_hostnames:
                continue 
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname=''
        data_dict_hostnames[hp] = hostname  # note that this is in integer
    save_pickle(data_dict_hostnames, RIPE_IPS_HOSTNAMES_FILE)

    
def label_save_hostname_missing_traceroutes():
    traceroutes_data = load_pickle(TRACEROUTE_IPS_FILE)
    ips_hostnames_traceroute = set()
    total = len(traceroutes_data)
    # trace
    counter = 0
    for ip,hostname in traceroutes_data:
        counter += 1
        if hostname != '':
            ips_hostnames_traceroute.add((ip,hostname))
            continue
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname=''
        ips_hostnames_traceroute.add((ip,hostname))
        print "Processed missing hostnames for Traceroutes:", counter, "| Total:", total 
    save_pickle(ips_hostnames_traceroute, TRACEROUTE_IPS_FILE)
    # create a dict
    ips_hostnames_dict = {}
    print "Creating a dictionary for easy access for traceroute hostnames."
    for ip,hostname in ips_hostnames_traceroute:
        if ip in ips_hostnames_dict and hostname == '':
            continue
        ips_hostnames_dict[ip] = hostname
    print "Traceroute hostname dict size:", len(ips_hostnames_dict)
    save_pickle(ips_hostnames_dict, TRACEROUTE_IPS_HOSTNAME_DICT_FILE)



def intersect_ripe_ips():
    ripe_probes_info_dict = load_ripe_node_info()
    hop_to_src_dict = load_pickle(RIPE_IPS_RTT_FILE)

    # get all the intersections
    insufficient_info = []
    ip_intersection_box_list = []
    ip_intersection_box_list_second = []
    ip_no_intersection_list = []
    exception_counter = 0
    # get all the intersections
    for hop in hop_to_src_dict:
        # get a list of boxes from srcs
        srcs_dict = hop_to_src_dict[hop]['srcs']
        # get a list of boxes from landmarks
        boxes = []
        #print srcs_dict
        for src_probe in srcs_dict:
            # get min rtt
            min_rtt = srcs_dict[src_probe]
            if min_rtt > configs.intersection.SPEED_MAX_RTT:
                continue
            # create a box.
            src = ripe_probes_info_dict[src_probe]
            if src["latitude"] == 0:
                continue
            src_lat = src["latitude"]
            src_lon = src["longitude"]
            bx = get_box(src_lat, src_lon, min_rtt)
            boxes.append(bx)
        # sort the boxes on area so that smallest boxes are chosen first
        if len(boxes) == 0:
            insufficient_info.append(hop)
            continue
        boxes.sort()  #the sort function is in the geo_code_box
        # instersect the boxes
        try:
            box = ppbox.intersect_boxes(boxes)
        except:
            print "Box Intersection Failed"
            traceback.print_exc()
            exception_counter += 1
        ip = hop
        if box is not None:
            # save this intersection coordinates,
            # the number of sources it saw, number of intersections.
            box_info = {'ip': utils.ip_int_to_string(ip),
                                'lat_bottom_left': box.y1,
                                'lon_bottom_left': box.x1,
                                'lat_top_right': box.y2,
                                'lon_top_right': box.x2, 'num_boxes': len(boxes)}
            ip_intersection_box_list.append(box_info)
            continue

        # try the second intersection way.
        # don't reverse the boxes, you lose information
        #boxes.sort(reverse=True)
        boxes.sort()
        # instersect the boxes
        try:
            box = ppbox.intersect_boxes_second(boxes)
        except:
            print "Box Intersection Failed"
            traceback.print_exc()
            exception_counter += 1
        ip = hop

        if box is not None:
            # save this intersection coordinates,
            # the number of sources it saw, number of intersections.
            box_info = {'ip': utils.ip_int_to_string(ip),
                                'lat_bottom_left': box.y1,
                                'lon_bottom_left': box.x1,
                                'lat_top_right': box.y2,
                                'lon_top_right': box.x2, 'num_boxes': len(boxes)}
            ip_intersection_box_list_second.append(box_info)
            continue

        # box is none    
        no_box_info = {'ip': utils.ip_int_to_string(ip),
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

    print "Total hops with RTT < 100 ms:", len(hop_to_src_dict) - len(insufficient_info) 
    print "Intersection Success:", len(ip_intersection_box_list)
    print "Intersection Success Second phase:", len(ip_intersection_box_list_second)
    print "Intersection Failures:", len(ip_no_intersection_list)
    print "Total number of exceptions for box intersections:", exception_counter
    print "Insufficient information (with RTTs > 100 ms):", len(insufficient_info)

    # save
    save_data = {}
    save_data["ip_no_intersection_list"] = ip_no_intersection_list
    save_data["ip_intersection_box_list"] = ip_intersection_box_list
    save_data["ip_intersection_box_list_second"] = ip_intersection_box_list_second
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    write_file = os.path.join(cur_dir, DATA_FOLDER,RIPE_IPS_LATLON_FILE)

    with open(write_file,'w') as handle:
        pickle.dump(save_data, handle)


#######################################################################
#######################################################################
def load_ripe_node_info():
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    read_file = os.path.join(cur_dir, DATA_FOLDER,RIPE_NODE_INFO_FILE)
    try:
        with open(read_file,'r') as handle:
            return pickle.load(handle)
    except:
        print "No Node info for ripe found. Will creat a new one"
    nodes_dir = os.path.join(configs.system.PROJECT_ROOT,
                             configs.intersection.traceroute_pkg_folder,
                             configs.traceroutes.RIPE_PARENT_FOLDER,
                             configs.traceroutes.RIPE_NODE_FOLDER)
    nodes_info = {}
    for node_file in os.listdir(nodes_dir):
        if node_file in configs.intersection.ignore_files:
            continue
        if not node_file.endswith('.json'):
            continue
        data_file = open(os.path.join(nodes_dir, node_file), 'r')
        nodes_data = json.load(data_file)
        data_file.close()
        print "Processing file:", node_file
        for probe in nodes_data["objects"]:
            if probe['id'] in nodes_info:
                continue
            nodes_info[probe['id']] = probe
    save_ripe_node_info(nodes_info)
    print "New node info file created"
    return nodes_info


def save_ripe_node_info(node_info_dict):
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    write_file = os.path.join(cur_dir, DATA_FOLDER,RIPE_NODE_INFO_FILE)
    with open(write_file,'w') as handle:
        pickle.dump(node_info_dict, handle)


#######################################################################
#######################################################################
#######################################################################
#######################################################################
#######################################################################
def load_intersect_traceroute_traceroutes():
    get_all_ips_traceroutes()
    label_save_hostname_missing_traceroutes()
    get_pings_traceroutes()
    perform_intersections_traceroutes()


def intersect_traceroute_ips():
    pass
#######################################################################
#######################################################################


def get_unique_ips_traceroute(dir_name,revtr):
    ips_unique = set()
    num_traceroutes = 0
    for src_ip in os.listdir(dir_name):
        print "Traceroute, reading for source:", src_ip, "| Revtr:",revtr
        if src_ip in configs.intersection.ignore_files:
            continue
        folder_path = os.path.join(dir_name, src_ip)
        if not os.path.isdir(folder_path):
            continue
        for dst_ip in os.listdir(folder_path):
            if dst_ip in configs.intersection.ignore_files:
                continue
            num_traceroutes += 1
            traceroute_data = traceroute.get_existing_trace(src_ip, dst_ip, revtr)
            if traceroute_data is None:
                continue
            if "hops" not in traceroute_data:
                continue
            for entry in traceroute_data["hops"]:
                hop_ip = entry['ip']
                hostname=''
                if 'hostname' in entry:
                    hostname = entry['hostname']
                ips_unique.add((hop_ip, hostname))
    return ips_unique, num_traceroutes
            

def get_all_ips_traceroutes():
    ips_unique = set()

    traceroutes_dir = os.path.join(configs.system.PROJECT_ROOT,
                                   configs.intersection.traceroute_pkg_folder,
                                   configs.intersection.traceroute_folder)
    fwd_trace_dir = os.path.join(traceroutes_dir, configs.traceroutes.FWD_DIR)
    rev_trace_dir = os.path.join(traceroutes_dir, configs.traceroutes.REV_DIR)
    # get IPs
    fwd_ips, fwd_traces = get_unique_ips_traceroute(fwd_trace_dir,False)
    rev_ips, rev_traces = get_unique_ips_traceroute(rev_trace_dir,True)
    print len(fwd_ips), "IPs in", fwd_traces, "FWD Traces" 
    print len(rev_ips), "IPs in", rev_traces, "REV Traces" 
    for ip in fwd_ips: 
        ips_unique.add(ip)
    for ip in rev_ips: 
        ips_unique.add(ip)
    print "Total IPs:", len(ips_unique)
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    write_file = os.path.join(cur_dir, DATA_FOLDER,TRACEROUTE_IPS_FILE)
    if not os.path.exists(os.path.join(cur_dir, DATA_FOLDER)):
        os.makedirs(os.path.join(cur_dir, DATA_FOLDER))
    with open(write_file,'w') as handle:
        pickle.dump(ips_unique, handle)


def get_pings_traceroutes():
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    utils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    utils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND)

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    read_file = os.path.join(cur_dir, DATA_FOLDER,TRACEROUTE_IPS_FILE)
    with open(read_file,'r') as handle:
        ips_unique = pickle.load(handle)

    # global structures
    src_info_dict = {} # also contains landmarks.
    hop_to_src_dict = {} # an ip to a list of dicts that have the source # hop:source
    router_aliases_dict = router_alias_package.get_router_aliases()

    # get pings
    for ip_address,ip_hostname in ips_unique:
        print "IP ping measurement:",ip_address
        min_pings = ping.get_existing_pings(ip_address)
        hop_ip = utils.ip_string_to_int(ip_address)
        if hop_ip in router_aliases_dict:
            hop_ip = router_aliases_dict[hop_ip]
        if not min_pings:
            continue
        hop_src_dict = {}
        if hop_ip in hop_to_src_dict:
            hop_src_dict = hop_to_src_dict[hop_ip]
        for src in min_pings:
            src_ip_int = utils.ip_string_to_int(src)
            if src_ip_int not in src_info_dict:
                src_info = ip_info.get_info_cached(src)
                src_info_dict[src_ip_int] = src_info
            entry_rtt = min_pings[src]
            if entry_rtt > configs.intersection.SPEED_MAX_RTT:
                continue
            if src_ip_int in hop_src_dict:
                hop_src_dict[src_ip_int] = min(entry_rtt,hop_src_dict[src_ip_int])
            else:
                hop_src_dict[src_ip_int] = entry_rtt 
        if hop_src_dict:
            hop_to_src_dict[hop_ip] = hop_src_dict
    # save
    save_data = {}
    save_data["hop_to_src_dict"] = hop_to_src_dict
    save_data["src_info_dict"] = src_info_dict
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    write_file = os.path.join(cur_dir, DATA_FOLDER,TRACEROUTE_IPS_RTT_FILE)
    if not os.path.exists(os.path.join(cur_dir, DATA_FOLDER)):
        os.makedirs(os.path.join(cur_dir, DATA_FOLDER))
    with open(write_file,'w') as handle:
        pickle.dump(save_data, handle)
    

def perform_intersections_traceroutes():
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    read_file  = os.path.join(cur_dir, DATA_FOLDER,TRACEROUTE_IPS_RTT_FILE)
    with open(read_file,'r') as handle:
        save_data = pickle.load(handle)
    hop_to_src_dict = save_data["hop_to_src_dict"]
    src_info_dict = save_data["src_info_dict"]
    # get all the intersections
    ip_intersection_box_list = []
    ip_intersection_box_list_second = []
    ip_no_intersection_list = []
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
            min_rtt = srcs_dict[src_ip_int]
            # create a box.
            src = src_info_dict[src_ip_int]
            if src["latitude"] == 0:
                continue
            if src["country"] in USELESS_PREDICTED_COUNTRIES:
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
        if box is not None:
            # save this intersection coordinates,
            # the number of sources it saw, number of intersections.
            box_info = {'ip': utils.ip_int_to_string(ip),
                                'lat_bottom_left': box.y1,
                                'lon_bottom_left': box.x1,
                                'lat_top_right': box.y2,
                                'lon_top_right': box.x2, 'num_boxes': len(boxes)}
            ip_intersection_box_list.append(box_info)
            continue

        # try the second intersection way.
        #boxes.sort(reverse=True) # don't reverse, bad idea
        boxes.sort()
        # instersect the boxes
        try:
            box = ppbox.intersect_boxes_second(boxes)
        except:
            print "Box Intersection Failed"
            traceback.print_exc()
            exception_counter += 1
        ip = hop

        if box is not None:
            # save this intersection coordinates,
            # the number of sources it saw, number of intersections.
            box_info = {'ip': utils.ip_int_to_string(ip),
                                'lat_bottom_left': box.y1,
                                'lon_bottom_left': box.x1,
                                'lat_top_right': box.y2,
                                'lon_top_right': box.x2, 'num_boxes': len(boxes)}
            ip_intersection_box_list_second.append(box_info)
            continue

        # box is none    
        no_box_info = {'ip': utils.ip_int_to_string(ip),
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

    print "Total hops with RTT < 100 ms:", len(hop_to_src_dict) 
    print "Intersection Success:", len(ip_intersection_box_list)
    print "Intersection Success Second phase:", len(ip_intersection_box_list_second)
    print "Intersection Failures:", len(ip_no_intersection_list)
    print "Total number of exceptions for box intersections:", exception_counter

    # save
    save_data = {}
    save_data["ip_no_intersection_list"] = ip_no_intersection_list
    save_data["ip_intersection_box_list"] = ip_intersection_box_list
    save_data["ip_intersection_box_list_second"] = ip_intersection_box_list_second
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    write_file = os.path.join(cur_dir, DATA_FOLDER,TRACEROUTE_IPS_LATLON_FILE)
    if not os.path.exists(os.path.join(cur_dir, DATA_FOLDER)):
        os.makedirs(os.path.join(cur_dir, DATA_FOLDER))
    with open(write_file,'w') as handle:
        pickle.dump(save_data, handle)

#######################################################################
#######################################################################
#######################################################################

def generate_ips_for_alidade():
    save_data = load_pickle(TRACEROUTE_IPS_RTT_FILE)
    traceroutes_data = save_data["hop_to_src_dict"]
    src_info_dict = save_data["src_info_dict"]
    ripe_data = load_pickle(RIPE_IPS_RTT_FILE)
    ip_set = set()
    for ip in traceroutes_data:
        ip_set.add(ip)

    for ip in ripe_data:
        ip_set.add(ip)
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    ali_file_pth = os.path.join(cur_dir, DATA_FOLDER, ALIDADE_IP_FILE)
    ali_file = open(ali_file_pth, 'wb')  
    csvw = csv.writer(ali_file)
    for ip in ip_set:
        csvw.writerow([utils.ip_int_to_string(ip)])


#######################################################################
#######################################################################
#######################################################################

