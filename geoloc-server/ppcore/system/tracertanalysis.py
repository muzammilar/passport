# -*- coding: utf-8 -*-
"""

    ppcore.system.prediction
    ~~~~~~~~~~~~~~

     This module uses the predictions from the Prediction System
     module, uses them to label traceroutes (from individual IP address
     predictions from Prediction System) for both Ripe Atlas and
     revtr measurements, perform distance analysis between the predicted
    countries, and generate interesting cases (as seen in the paper)
     to be verified manually.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from ppmeasurements import traceroute, ripeatlas
import pputils as utils
from ppcore.system import prediction
import bz2
import configs.traceroutes
import  configs.intersection
import configs.system
import configs.pvt
import ppmeasurements.util as util_traceroutes
import json
import geosources.ipinfo as ip_info
from multiprocessing import Manager
import ppnamespace
###remove-me-later-muz###import ormsettings as DJANGO_SETTINGS
###remove-me-later-muz###from geopy.distance import great_circle
import traceback
from ppstore import traindata as training_data_file
import sys
import configs.pvt
import csv
import os
import geosources.ddec as ddec

##############################################################################
OUTPUT_FILE_FWD_TRACES = "traces_fwd.txt.bz2"
OUTPUT_FILE_REV_TRACES = "traces_rev.txt.bz2"
OUTPUT_FILE_RIPE_TRACES = "traces_ripe.txt.bz2"
# these files save distances in meters
DISTANCE_FILE_REVTR = "distance_analysis_rev.pkl"
DISTANCE_FILE_RIPE = "distance_analysis_ripe.pkl"
DISTANCE_FILE_FWDTR = "distance_analysis_fwd.pkl"
DISTANCE_FILE_OUTPUT = "distance_analysis.csv"
# leaving country
OUTPUT_DISTANCE_SPECIAL_REV = "distance_special_case_rev.txt.bz2"
OUTPUT_DISTANCE_SPECIAL_FWD =  "distance_special_case_fwd.txt.bz2"
OUTPUT_DISTANCE_SPECIAL_RIPE = "distance_special_case_ripe.txt.bz2"
OUTPUT_DISTANCE_SPECIAL_RIPE_HIGH_DIST = "distance_special_case_ripe_high_distance.txt.bz2"
USELESS_PREDICTED_COUNTRIES = ['EU']
WORLD_LONGEST_DISTANCE = 40075 # km. roughly half of the circumference 
MAX_ASN_PER_COUNTRY_FOR_MANUAL = 5
TRACEOUTES_IP_ADDRESSES_FILE = 'all_traceroutes_ip_addresses.pkl' # contains a list of sets(ip1,ip2,ip3)
##############################################################################


def main():
    print "Labelling all traceroutes using the system!"
    label_all_traceroutes()
    perform_distance_analysis()
    compare_with_local_sources()
    compare_local_sources_with_speed_get_top_countries()
    compare_with_local_sources_get_predictions_for_manual_analysis()
    get_src_countries_total_all()
    get_interesting_cases_ripe_leaving_country()
    get_interesting_cases_ripe_leaving_continent()
    get_src_countries_total_ripe()
    get_reverse_forward_interesting_cases_one_country_only()
    get_traceroute_forward_interesting_cases_continent_country()
    get_traceroute_forward_interesting_cases_targetted_src_dst('Brazil','Russia', ['United States']) # no function for ripe yet.
    generate_all_ip_addresses_per_traceroutes_file()
    generate_traceoutes_with_atleast_one_ground_truth_ip_traceroutes_ripe(13)
    generate_traceoutes_with_atleast_one_ground_truth_ip_traceroutes_ripe(5)


def label_all_traceroutes():
    label_traceroute_traceroutes_all()
    label_ripe_traceroutes_all()


def perform_distance_analysis():
    perform_distance_analysis_ripe()
    perform_distance_analysis_revtr()
    perform_distance_analysis_fwdtr()
    aggregate_distance_files([DISTANCE_FILE_REVTR,DISTANCE_FILE_RIPE, DISTANCE_FILE_FWDTR])

def test():
    aggregate_distance_files([DISTANCE_FILE_REVTR,DISTANCE_FILE_RIPE, DISTANCE_FILE_FWDTR])
        
    ripe_probes_info_dict = prediction.load_ripe_node_info()
    for probe_id in ripe_probes_info_dict:
        if ripe_probes_info_dict[probe_id]['address_v4'] == '84.205.73.1':
            ripe_probes_info_dict[probe_id]
        break

##############################################################################
##############################################################################
##############################################################################
##############################################################################


def label_ripe_traceroutes_all():
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    utils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    utils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND)
    ripe_probes_info_dict = prediction.load_ripe_node_info()
    for probe_id in ripe_probes_info_dict:
        cntry_code = ripe_probes_info_dict[probe_id]["country_code"]
        country_name = utils.get_country_name_from_iso_code(ppnamespace.COUNTRY_ISO_CODE_DICT,
                                                            cntry_code)
        ripe_probes_info_dict[probe_id]["country_name_full"] = country_name
        #print ripe_probes_info_dict[probe_id]    
    print "Labelling Ripe | Probes loaded."
    system_predictions = prediction.load_pickle(prediction.OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    overall_predictions = system_predictions['overall']
    print "Labelling Ripe | Predictions loaded."

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    output_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    
    ripe_hostname_dict = prediction.load_pickle(prediction.RIPE_IPS_HOSTNAMES_FILE)
    print "Labelling Ripe | Hostnames loaded."
    no_predictions_set = set() # where the overall system fails
    all_ips_set = set()
    num_traces = 0
    traceroutes_dir = os.path.join(configs.system.PROJECT_ROOT,
                                   configs.intersection.traceroute_pkg_folder,
                                   configs.traceroutes.RIPE_PARENT_FOLDER,
                                   configs.traceroutes.RIPE_RAW_FOLDER)
    with bz2.BZ2File(output_file_path, "w") as data_file_handle:
        for trace_file_id in os.listdir(traceroutes_dir):
            if trace_file_id in configs.intersection.ignore_files:
                continue
            # read tracefile, parse
            print "Processing file with msm_id:", trace_file_id
            num_traces += ripeatlas.predict_ripe_traceroutes(trace_file_id,
                                                             overall_predictions, data_file_handle,
                                                             ripe_probes_info_dict, ripe_hostname_dict,
                                                             no_predictions_set, all_ips_set)
            print "Traceroutes processed:", num_traces, \
                "| Prediction Failed for IPs:", len(no_predictions_set), \
                "| Total IPs seen:", len(all_ips_set)


##############################################################################
def label_traceroute_traceroutes_all():
    MANAGER = Manager()
    ppnamespace.init(MANAGER)
    utils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT)
    utils.get_country_name_iso_code_dict(ppnamespace.COUNTRY_ISO_CODE_DICT_SECOND)
    fwd_traces = label_traceroute_traceroutes(revtr=False)
    back_traces = label_traceroute_traceroutes(revtr=True)
    print "Fwd traces:", fwd_traces , " | Rev traces:", back_traces


def label_traceroute_traceroutes(revtr=False):
    traceroutes_dir = os.path.join(configs.system.PROJECT_ROOT,
                                   configs.intersection.traceroute_pkg_folder,
                                   configs.intersection.traceroute_folder)
    fwd_trace_dir = os.path.join(traceroutes_dir, configs.traceroutes.FWD_DIR)
    rev_trace_dir = os.path.join(traceroutes_dir, configs.traceroutes.REV_DIR)
    out_file_name = OUTPUT_FILE_FWD_TRACES
    trace_dir = fwd_trace_dir
    if revtr:
        trace_dir = rev_trace_dir
        out_file_name = OUTPUT_FILE_REV_TRACES
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    output_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, out_file_name)
    
    system_predictions = prediction.load_pickle(prediction.OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    overall_predictions = system_predictions['overall']
    
    ips_hostname_dict_trace = prediction.load_pickle(prediction.TRACEROUTE_IPS_HOSTNAME_DICT_FILE)
    num_traceroutes = 0
    src_country_info = {}
    for src_ip in os.listdir(trace_dir):
        if src_ip in configs.intersection.ignore_files:
            continue
        src_country_inf = ip_info.get_info_cached(src_ip)
        src_country = src_country_inf["country"]
        if src_country == "":
            print "Src country not found for src:", src_ip, "| Revtr:", revtr 
            continue
        src_country_info[src_ip] = src_country

    with bz2.BZ2File(output_file_path, "w") as data_file:
        for src_ip in os.listdir(trace_dir):
            print "Traceroute reading for source:", src_ip, "| Revtr:",revtr
            if src_ip in configs.intersection.ignore_files:
                continue
            if src_ip not in src_country_info:
                continue
            src_country = src_country_info[src_ip]
            folder_path = os.path.join(trace_dir, src_ip)
            if not os.path.isdir(folder_path):
                continue
            for dst_ip in os.listdir(folder_path):
                if dst_ip in configs.intersection.ignore_files:
                    continue
                traceroute_data = traceroute.get_existing_trace(src_ip, dst_ip, revtr)
                if traceroute_data is None:
                    continue
                traceroute_data["src_cntry_name"] = src_country
                if "hops" not in traceroute_data:
                    continue
                num_traceroutes += 1
                for entry in traceroute_data["hops"]:
                    hop_ip = entry['ip']
                    if util_traceroutes.is_private_ip(hop_ip):
                        entry['predictions'] = []
                        continue
                    if 'hostname' not in entry:
                            try:
                                hostname = ips_hostname_dict_trace[hop_ip]
                            except:
                                hostname = ''
                            entry['hostname'] = hostname
                    if hop_ip not in overall_predictions:
                        print "No predictions for:", hop_ip
                        entry['predictions'] = []
                        continue
                    entry['predictions'] = overall_predictions[hop_ip]
                data_file.write(json.dumps(traceroute_data))
                data_file.write('\n')  
    print "Traceroutes:", num_traceroutes, "| Revtr:", revtr
    return num_traceroutes


##############################################################################
##############################################################################
##############################################################################
def get_all_countries_names_traceroutes_paths(hops_data):
    countries = set()
    if len(hops_data) == 0:
        return countries
    for hop in hops_data:
        if 'ip' not in hop:
            continue
        hop_ip = hop['ip']
        if util_traceroutes.is_private_ip(hop_ip):
            continue
        if 'predictions' in hop:
            for cntry in hop['predictions']:
                countries.add(cntry)
    return countries


def is_there_only_one_prediction(hops_data):
    if len(hops_data) == 0:
        return False
    for hop in hops_data:
        if 'ip' not in hop:
            continue
        hop_ip = hop['ip']
        if util_traceroutes.is_private_ip(hop_ip):
            continue
        if 'predictions' in hop and len(hop['predictions']) == 1:
            continue
        return False
    return True


def one_prediction_best_hop_variant_ripe(hop):
    variant_id = -1
    if 'result' not in hop:
        return False, -1, True            
    hop_result = hop['result']
    for variant in hop_result:
        # ignore it if it's a private IP address
        if 'late' in variant:
            continue
        if 'from' not in variant:
            return False, -1, True
        hop_ip = variant['from']
        if util_traceroutes.is_private_ip(hop_ip):
            return False, -1, True            
        # ignore it if it's a private IP address ^^
        variant_id += 1
        if 'predictions' in variant and len(variant['predictions']) == 1:
            return True, variant_id, False
    return False, -1, False
    

def is_there_only_one_prediction_ripe(results_data):
    one_country_hop_dict = {}
    if len(results_data) == 0:
        return False, {}
    hop_counter = 0
    for hop in results_data:
        single_prediction, idx, is_private = one_prediction_best_hop_variant_ripe(hop)
        if is_private:
            hop_counter += 1
            continue
        if single_prediction:
            one_country_hop_dict[hop_counter] = idx
            hop_counter += 1
            continue
        return False, {}
    if len(one_country_hop_dict) == 0:
        return False, one_country_hop_dict
    return True, one_country_hop_dict

def read_country_lat_lon_dict():
    return utils.get_country_lat_lon_dict()


def get_src_dest_distance(traceroute_data, lat_long_dict):
    src = traceroute_data["src_cntry_name"]
    dst = traceroute_data["dst_cntry_name"]
    if src in prediction.USELESS_PREDICTED_COUNTRIES:
        return False, -1
    try:
        src_lat = lat_long_dict[src]["lat"]
        dst_lat = lat_long_dict[dst]["lat"]
        src_lon = lat_long_dict[src]["lon"]
        dst_lon = lat_long_dict[dst]["lon"]
        src_dest_distance = great_circle((src_lat,src_lon), (dst_lat,dst_lon)).meters
        return True, src_dest_distance
    except:
        traceback.print_exc()
        print traceroute_data["src"]
        return False, 0

def get_total_measured_distance(traceroute_data,lat_long_dict,revtr=False):
    src = traceroute_data["src_cntry_name"]
    dst = traceroute_data["dst_cntry_name"]
    src_lat = lat_long_dict[src]["lat"]
    dst_lat = lat_long_dict[dst]["lat"]
    src_lon = lat_long_dict[src]["lon"]
    dst_lon = lat_long_dict[dst]["lon"]
    total_measured_distance = 0
    last_loc = (src_lat,src_lon)
    traceroute_hops = traceroute_data['hops']
    if revtr:
        traceroute_hops.reverse()
    for hop in traceroute_hops:
        if 'ip' not in hop:
            continue
        hop_ip = hop['ip']
        if util_traceroutes.is_private_ip(hop_ip):
            continue
        predicted_country = hop['predictions'][0]   # not, it will always be one, since we already checked.
        if predicted_country in prediction.USELESS_PREDICTED_COUNTRIES:
            return False, -1
        try:
            cur_lat = lat_long_dict[predicted_country]["lat"]
            cur_lon = lat_long_dict[predicted_country]["lon"]
            current_loc = (cur_lat,cur_lon)
        except:
            traceback.print_exc()
            continue
        total_measured_distance += great_circle(last_loc, current_loc).meters
        last_loc = current_loc
    # distance from last hop to destination.
    total_measured_distance += great_circle(last_loc, (dst_lat,dst_lon)).meters 
    return True, total_measured_distance


def get_src_dest_distance_ripe(traceroute_data, lat_long_dict, dst_hop, one_country_hop_dict):
    src = traceroute_data["probe_country"]
    variant = one_country_hop_dict[dst_hop]
    #print len(traceroute_data["result"]), dst_hop
    if src in prediction.USELESS_PREDICTED_COUNTRIES:
        return False, -1
    try:
        dst = traceroute_data["result"][dst_hop]['result'][variant]['predictions'][0] # zero since it will have one elem always. we check it before this.
        src_lat = lat_long_dict[src]["lat"]
        dst_lat = lat_long_dict[dst]["lat"]
        src_lon = lat_long_dict[src]["lon"]
        dst_lon = lat_long_dict[dst]["lon"]
        src_dest_distance = great_circle((src_lat,src_lon), (dst_lat,dst_lon)).meters
        return True, src_dest_distance
    except:
        traceback.print_exc()
        # print traceroute_data["src"]
        return False, 0

def get_all_countries_in_path_ripe_all_cnty(traceroute_data, lat_long_dict, useful_hop_idx_list, one_country_hop_dict):
    traceroute_hops = traceroute_data['result']
    seen = set()
    for hop in useful_hop_idx_list:
        variants = traceroute_hops[hop]['result']
        for variant in variants:
            try: 
                predicted_countries = [variant]['predictions']
                for predicted_country in predicted_countries:
                    if predicted_country in prediction.USELESS_PREDICTED_COUNTRIES:
                        continue
                    seen.add(predicted_country)
            except:
                continue
    return seen


def get_all_countries_in_path_ripe_one_cnty(traceroute_data, lat_long_dict, useful_hop_idx_list, one_country_hop_dict):
    traceroute_hops = traceroute_data['result']
    seen = set()
    for hop in useful_hop_idx_list:
        variant = one_country_hop_dict[hop]
        predicted_countries = traceroute_hops[hop]['result'][variant]['predictions']
        for predicted_country in predicted_countries:
            if predicted_country in prediction.USELESS_PREDICTED_COUNTRIES:
                continue
            seen.add(predicted_country)
    return seen

def get_all_countries_in_path_ripe(traceroute_data, lat_long_dict, useful_hop_idx_list,
                                   one_country_hop_dict, only_one_countr_per_hop):
    if only_one_countr_per_hop:
        return get_all_countries_in_path_ripe_one_cnty(traceroute_data, lat_long_dict,
                                                       useful_hop_idx_list, one_country_hop_dict)
    return get_all_countries_in_path_ripe_all_cnty(traceroute_data, lat_long_dict,
                                                   useful_hop_idx_list, one_country_hop_dict)


def get_total_measured_distance_ripe(traceroute_data, lat_long_dict, useful_hop_idx_list, one_country_hop_dict):
    src = traceroute_data["probe_country"]
    #variant = one_country_hop_dict[dst_hop]
    #dst = traceroute_data["result"][dst_hop]['result'][variant]['predictions'][0] # zero since it will have one elem always. we check it before this.
    src_lat = lat_long_dict[src]["lat"]
    src_lon = lat_long_dict[src]["lon"]
    total_measured_distance = 0
    last_loc = (src_lat,src_lon)
    traceroute_hops = traceroute_data['result']
    for hop in useful_hop_idx_list:
        variant = one_country_hop_dict[hop]
        try:
            predicted_country = traceroute_hops[hop]['result'][variant]['predictions'][0]   # not, it will always be one, since we already checked.
            if predicted_country in prediction.USELESS_PREDICTED_COUNTRIES:
                return False, -1
            cur_lat = lat_long_dict[predicted_country]["lat"]
            cur_lon = lat_long_dict[predicted_country]["lon"]
            current_loc = (cur_lat,cur_lon)
        except:
            traceback.print_exc()
            continue
        total_measured_distance += great_circle(last_loc, current_loc).meters
        last_loc = current_loc
    # distance from last hop to destination. we don't do it for ripe since we're not sure about dest loc
    #total_measured_distance += great_circle(last_loc, (dst_lat,dst_lon)).meters 
    return True, total_measured_distance


#################################################################
#################################################################
def perform_distance_analysis_ripe():
    country_lat_lon_dict = read_country_lat_lon_dict()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    special_case_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_DISTANCE_SPECIAL_RIPE)
    special_case_high_dist_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_DISTANCE_SPECIAL_RIPE_HIGH_DIST)
    special_case_file = bz2.BZ2File(special_case_file_path, "w")
    special_case_high_dist_handle = bz2.BZ2File(special_case_high_dist_path, "w")
    num_useful_traceroutes = 0
    num_all_traceroutes = 0
    abs_distance_inc_list = []
    abs_distance_total_list = []
    percentage_distance_inc_list = []
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            num_all_traceroutes += 1
            if 'result' not in traceroute_data:
                continue
            # we're only looking for one
            single_prediction, one_country_hop_dict = is_there_only_one_prediction_ripe(traceroute_data['result'])
            if not single_prediction:
                continue
            #print one_country_hop_dict # this dict contains the variant of hop (there are usualy 3 variants after traceroute. but we only need one.
            useful_hop_idx_list = one_country_hop_dict.keys()
            useful_hop_idx_list.sort()
            dst_hop = max(useful_hop_idx_list) # we only go to the last hop
            #print dst_hop
            success, src_dest_distance = get_src_dest_distance_ripe(traceroute_data, country_lat_lon_dict, dst_hop, one_country_hop_dict)
            if not success:
                continue
            success, total_measured_distance = get_total_measured_distance_ripe(traceroute_data,country_lat_lon_dict, useful_hop_idx_list, one_country_hop_dict)
            if not success:
                continue
            num_useful_traceroutes += 1
            #print traceroute_data['result']
            # use the following one_country_hop_dict to go over results
            # leaving country
            if total_measured_distance > src_dest_distance and src_dest_distance==0:
                special_case_file.write(line)
                special_case_file.write('\n')
                continue
            if total_measured_distance < src_dest_distance:
                print "Minimum distance allowed:",src_dest_distance, "| Measured distance:", total_measured_distance
                raise Exception("Sanity Check Failed!")
            abs_dist_diff = total_measured_distance - src_dest_distance
            if src_dest_distance == 0 and abs_dist_diff == 0:
                perc_dist_diff = 0
            else:
                perc_dist_diff = abs_dist_diff*100.00/src_dest_distance
            if abs_dist_diff/1000.00 > WORLD_LONGEST_DISTANCE:  # in kim
                special_case_high_dist_handle.write(line)
                special_case_high_dist_handle.write('\n')
            abs_distance_inc_list.append(abs_dist_diff)
            abs_distance_total_list.append(src_dest_distance)
            percentage_distance_inc_list.append(perc_dist_diff)
    special_case_file.close()
    special_case_high_dist_handle.close()
    save_data = {'abs_distance_total_list': abs_distance_total_list,
                 'abs_distance_inc_list': abs_distance_inc_list,
                 'percentage_distance_inc_list': percentage_distance_inc_list}
    prediction.save_pickle(save_data, DISTANCE_FILE_RIPE)

    print "Number of Traceroutes with only one prediction for all hops in Ripe trace:", num_useful_traceroutes
    print "Total Number of Traceroutes in Ripe trace:", num_all_traceroutes

##############################################################################

def perform_distance_analysis_revtr():
    country_lat_lon_dict = read_country_lat_lon_dict()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_REV_TRACES)
    special_case_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_DISTANCE_SPECIAL_REV)
    special_case_file = bz2.BZ2File(special_case_file_path, "w")
    num_useful_traceroutes = 0
    num_all_traceroutes = 0
    abs_distance_inc_list = []
    abs_distance_total_list = []
    percentage_distance_inc_list = []
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            num_all_traceroutes += 1
            if 'hops' not in traceroute_data:
                continue
            # we're only looking for one
            if not is_there_only_one_prediction(traceroute_data['hops']):
                continue
            success, src_dest_distance = get_src_dest_distance(traceroute_data, country_lat_lon_dict)
            if not success:
                continue
            success, total_measured_distance = get_total_measured_distance(traceroute_data,country_lat_lon_dict, True)
            if not success:
                continue
            num_useful_traceroutes += 1
            # leaving country
            if total_measured_distance > src_dest_distance and src_dest_distance == 0:
                special_case_file.write(line)
                special_case_file.write('\n')
                continue
            if total_measured_distance < src_dest_distance:
                print "Minimum distance allowed:",src_dest_distance, "| Measured distance:", total_measured_distance
                raise Exception("Sanity Check Failed!")
            abs_dist_diff = total_measured_distance - src_dest_distance
            if src_dest_distance == 0 and abs_dist_diff == 0:
                perc_dist_diff = 0
            else:
                perc_dist_diff = abs_dist_diff*100.00/src_dest_distance
            abs_distance_inc_list.append(abs_dist_diff)
            abs_distance_total_list.append(src_dest_distance)
            percentage_distance_inc_list.append(perc_dist_diff)
    special_case_file.close()
    save_data = {'abs_distance_total_list': abs_distance_total_list,
                 'abs_distance_inc_list': abs_distance_inc_list,
                 'percentage_distance_inc_list': percentage_distance_inc_list}
    prediction.save_pickle(save_data, DISTANCE_FILE_REVTR)

    print "Number of Traceroutes with only one prediction for all hops in REV trace:", num_useful_traceroutes
    print "Total Number of Traceroutes in REV trace:", num_all_traceroutes


##############################################################################

def perform_distance_analysis_fwdtr():
    country_lat_lon_dict = read_country_lat_lon_dict()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_FWD_TRACES)
    special_case_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_DISTANCE_SPECIAL_FWD)
    special_case_file = bz2.BZ2File(special_case_file_path, "w")
    num_useful_traceroutes = 0
    num_all_traceroutes = 0
    abs_distance_inc_list = []
    abs_distance_total_list = []
    percentage_distance_inc_list = []
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            num_all_traceroutes += 1
            if 'hops' not in traceroute_data:
                continue
            # we're only looking for one
            if not is_there_only_one_prediction(traceroute_data['hops']):
                continue
            success, src_dest_distance = get_src_dest_distance(traceroute_data,country_lat_lon_dict)
            if not success:
                continue
            num_useful_traceroutes += 1
            success, total_measured_distance = get_total_measured_distance(traceroute_data,country_lat_lon_dict,False)
            if not success:
                continue
            # leaving country
            if total_measured_distance > src_dest_distance and src_dest_distance==0:
                special_case_file.write(line)
                special_case_file.write('\n')
                continue
            if total_measured_distance < src_dest_distance:
                print "Minimum distance allowed:",src_dest_distance, "| Measured distance:", total_measured_distance
                raise Exception("Sanity Check Failed!")
            abs_dist_diff = total_measured_distance - src_dest_distance
            if src_dest_distance == 0 and abs_dist_diff == 0:
                perc_dist_diff = 0
            else:
                perc_dist_diff = abs_dist_diff*100.00/src_dest_distance
            abs_distance_inc_list.append(abs_dist_diff)
            abs_distance_total_list.append(src_dest_distance)
            percentage_distance_inc_list.append(perc_dist_diff)
    special_case_file.close()
    save_data = {}
    save_data['abs_distance_total_list'] = abs_distance_total_list
    save_data['abs_distance_inc_list'] = abs_distance_inc_list
    save_data['percentage_distance_inc_list'] = percentage_distance_inc_list
    prediction.save_pickle(save_data, DISTANCE_FILE_FWDTR)
    print "Number of Traceroutes with only one prediction for all hops in FWD trace:", num_useful_traceroutes
    print "Total Number of Traceroutes in FWD trace:", num_all_traceroutes

##############################################################################

def aggregate_distance_files(file_names_list):
    #save this file to the graph folder
    country_lat_lon_dict = read_country_lat_lon_dict()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    output_file_path = os.path.join(cur_dir, configs.pvt.DIR_GRAPH, DISTANCE_FILE_OUTPUT)
    abs_distance_inc_list = []
    abs_distance_total_list = []
    percentage_distance_inc_list = []
    save_data = {}
    for file_name in file_names_list:
        save_data = prediction.load_pickle(file_name)
        abs_distance_inc_list_file = save_data['abs_distance_inc_list']
        abs_distance_total_list_file = save_data['abs_distance_total_list']
        percentage_distance_inc_list_file = save_data['percentage_distance_inc_list']
        abs_distance_inc_list += abs_distance_inc_list_file  # append lists
        percentage_distance_inc_list += percentage_distance_inc_list_file # append lists
        abs_distance_total_list += abs_distance_total_list_file
    abs_distance_inc_list.sort()
    abs_distance_total_list.sort()
    percentage_distance_inc_list.sort()
    max_distance_allowed = max(abs_distance_inc_list)/1000.00
    list_high_dist = [x/1000.0 for x in abs_distance_inc_list if x/1000.00 > WORLD_LONGEST_DISTANCE]
    print "Too High distances:",list_high_dist
    print "Total paths with too high distance:", len(list_high_dist), "| Total paths:", len(abs_distance_inc_list)
    #print "Max Percentage increase:", max(percentage_distance_inc_list)
    #print "Max Distance:", max_distance_allowed, "km"
    if max_distance_allowed > WORLD_LONGEST_DISTANCE:
        #raise Exception("Something went horribly wrong! Are you sure that your distance is not shorter?")
        pass
    abs_distance_inc_list = [x/1000.0 for x in abs_distance_inc_list if x/1000.00 < WORLD_LONGEST_DISTANCE]
    #abs_distance_inc_list = [x/1000.0 for x in abs_distance_inc_list]
    percentage_distance_inc_list = percentage_distance_inc_list[:len(abs_distance_inc_list)]
    abs_distance_total_list = [x/1000.0 for x in abs_distance_total_list]
    abs_distance_inc_list.sort()
    max_distance_allowed = max(abs_distance_inc_list)
    print "Distance!"
    print "Max Percentage increase:", max(percentage_distance_inc_list)
    print "Max Distance:", max_distance_allowed, "km"
    csvw = csv.writer(open(output_file_path,"w"))
    csvw.writerow(["Counter", "Abs. Increase Distance", "Percentage Increase Distance",'Abs Distance Total'])
    for i in xrange(len(abs_distance_inc_list)):
        csvw.writerow([i, abs_distance_inc_list[i], percentage_distance_inc_list[i], abs_distance_total_list[i]])



#######################################################################
#######################################################################
#######################################################################


def is_ip_in_traceroute_path(ip_set, traceroutes_ips_set):
    for ip in ip_set:
        if ip in traceroutes_ips_set:
            return 1
    return 0


def traceroutes_affected_by_ips(trace_stats_dict, sources_different_ip, traceroute_ips_list):
    counter = 0
    for traceroutes_ips_set in traceroute_ips_list:
        counter += 1
        if counter % 500 == 0:
            print "Traces evaluated:", counter
        for src in sources_different_ip:
            ip_set = sources_different_ip[src]
            trace_stats_dict[src] += is_ip_in_traceroute_path(ip_set, traceroutes_ips_set)


def load_all_alidade_source(cur_dir ,ALIDADE_FOLDER, srcs_alidade):
    print "Loading Geo-sources by Alidade!"
    cached_lat_lon = {}
    sources_alidade_with_location = {}
    #country_polygon_dict = world.geography.loadFile()
    for src in srcs_alidade:
        print "Loading Geo-sources by Alidade:", src
        file_name = src + '.txt'
        cntry_not_found_counter = 0
        input_file_path = os.path.join(cur_dir, ALIDADE_FOLDER, file_name)
    # read and compare their data.
        sources_alidade_with_location[src]={}
        counter = 0
        with open(input_file_path, "rb") as data_file:
            for line in data_file:
                dat = line.split(" ")
                ip_address = dat[0]
                try:
                    lat = float(dat[1])
                    lon = float(dat[2])
                    if (lat, lon) in cached_lat_lon:
                        cntry_info = cached_lat_lon[(lat, lon)]
                    else:
                        cntry_info = utils.get_country_name_from_lat_lon(lat, lon)
                except:
                    cntry_info = None
                counter += 1
                if counter % 5000 == 0:
                    #break
                    print "Reading Alidade source:",src,"| IPs read:", counter
                if cntry_info is None:
                    cntry_not_found_counter += 1
                    #print "Country not found for:", (lat, lon)
                    cntry_name = ''
                else:
                    #print "Looking for:", lat, lon, "| Got:", cntry_info[2],cntry_info[3], "| Country:", cntry_info[0]
                    cntry_name = cntry_info
                    cached_lat_lon[(lat, lon)] = cntry_info
                    #print cntry_name
                sources_alidade_with_location[src][ip_address] = cntry_name
        print "Countries not found for src: ", src, "| Not found:", cntry_not_found_counter 
    return sources_alidade_with_location


def compare_local_sources_with_speed_get_top_countries():
    ALIDADE_FOLDER = 'alidade_results'
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    traceroute_ips_list = prediction.load_pickle(TRACEOUTES_IP_ADDRESSES_FILE)
    system_predictions = prediction.load_pickle(prediction.OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    combined = system_predictions['combined']
    overall = system_predictions['overall']
    area_pred_dict = prediction.load_pickle(prediction.AREA_PREDICTIONS_ALL)
    #system_ips = set()
    system_countries = set()
    srcs_alidade = ['locs-es-latest', 'locs-es','ips--dbip', 'ips--mml','ips--mm','ips--iplg','ips--ip2l']
    srcs_alidade_exceptions = {x:0 for x in srcs_alidade}
    #srcs_alidade = ['locs-es']
    sources_compare = ['maxmind_country', 'ipinfo_country', 'ip2location_country', 'db_ip_country']
    sources_all = sources_compare + srcs_alidade
    sources_country = {}
    sources_different_ip = {}
    sources_count = {}
    trace_stats_dict = {}
    country_stats_dict = {}
    area_pred_violation_stats = {}
    sources_alidade_with_location = load_all_alidade_source(cur_dir ,ALIDADE_FOLDER, srcs_alidade)
    area_predictions_violated = {}
    for src in sources_all:
        sources_different_ip[src] = set()
        sources_country[src] = set()
        sources_count[src] = 0
        trace_stats_dict[src] = 0
        country_stats_dict[src] = 0
        area_predictions_violated[src] = 0
        area_pred_violation_stats[src] = {}
    total_traces = len(traceroute_ips_list)
    area_predictions_total = 0
    total_ips = 0
    counter = 0
    for ip in area_pred_dict:
        counter += 1
        if counter % 500 == 0:
            #break
            print "IPs Looked for comparison:", counter
        try:
            ip_results = overall[ip]
            if len(ip_results) != 1:
                continue
        except:
            print ip, area_pred_dict[ip]
        try:
            # don't consider the sources that you didn't send to Alidade.
            src = srcs_alidade[0]
            a = sources_alidade_with_location[src][ip]       
        except:
            continue
        total_ips += 1
        area_predictions_total += 1
        area_predictions_ip_set = area_pred_dict[ip]
        area_prediction_for_ip = True
        # our sources
        test_instance = training_data_file.get_test_data(ip)
        for src in sources_compare:
      
            if test_instance[src] not in area_predictions_ip_set:
                area_predictions_violated[src] += 1
                pred_cnt_src = test_instance[src]
                if pred_cnt_src not in area_pred_violation_stats[src]:
                    area_pred_violation_stats[src][pred_cnt_src] = 0
                area_pred_violation_stats[src][pred_cnt_src] += 1

        # alidade sources
        for src in srcs_alidade:
            try:
                if sources_alidade_with_location[src][ip] not in area_predictions_ip_set:
                    area_predictions_violated[src] += 1
                    pred_cnt_src = sources_alidade_with_location[src][ip]
                    if pred_cnt_src not in area_pred_violation_stats[src]:
                        area_pred_violation_stats[src][pred_cnt_src] = 0
                    area_pred_violation_stats[src][pred_cnt_src] += 1
            except:
                #traceback.print_exc()
                srcs_alidade_exceptions[src] += 1
                sources_different_ip[src].add(ip)

    print "##############################################"
    print "Results:"
    print "##############################################"
    print "Total IP addresses:", total_ips
    print "Worst countries:", area_pred_violation_stats
    print "##############################################"
    area_pred_violation_stats_fraction = {}                        
    for src in sources_all:        
        area_pred_violation_stats_fraction[src] = {x:area_pred_violation_stats[src][x]*1.0/total_ips for x in area_pred_violation_stats[src]}        
    print "Worst Coutries Fraction:", area_pred_violation_stats_fraction
    print "##############################################"
    print "##############################################"
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    out_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, "wrong_countries_geosources.csv")
    csvw = csv.writer(open(out_file_path,'w'))
    for src in sources_all:
        stats_dict = area_pred_violation_stats[src]
        cntry_list = sorted(stats_dict,key=stats_dict.get,reverse=True)
        csvw.writerow([src,"",""])
        csvw.writerow(["Country","Numbers","Percentage"])
        for cnt in cntry_list:
            csvw.writerow([cnt,area_pred_violation_stats[src][cnt], area_pred_violation_stats_fraction[src][cnt]])
    

def compare_with_local_sources():
    ALIDADE_FOLDER = 'alidade_results'
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    traceroute_ips_list = prediction.load_pickle(TRACEOUTES_IP_ADDRESSES_FILE)
    system_predictions = prediction.load_pickle(prediction.OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    combined = system_predictions['combined']
    overall = system_predictions['overall']
    area_pred_dict = prediction.load_pickle(prediction.AREA_PREDICTIONS_ALL)
    #system_ips = set()
    system_countries = set()
    srcs_alidade = ['locs-es-latest', 'locs-es','ips--dbip', 'ips--mml','ips--mm','ips--iplg','ips--ip2l']
    srcs_alidade_exceptions = {x:0 for x in srcs_alidade}
    #srcs_alidade = ['locs-es']
    sources_compare = ['maxmind_country', 'ipinfo_country', 'ip2location_country', 'db_ip_country']
    sources_all = sources_compare + srcs_alidade
    sources_country = {}
    sources_different_ip = {}
    sources_count = {}
    trace_stats_dict = {}
    country_stats_dict = {}
    sources_alidade_with_location = load_all_alidade_source(cur_dir ,ALIDADE_FOLDER, srcs_alidade)
    area_predictions_violated = {}
    for src in sources_all:
        sources_different_ip[src] = set()
        sources_country[src] = set()
        sources_count[src] = 0
        trace_stats_dict[src] = 0
        country_stats_dict[src] = 0
        area_predictions_violated[src] = 0
    total_traces = len(traceroute_ips_list)
    area_predictions_total = 0
    total_ips = 0
    counter = 0
    for ip in overall:
        counter += 1
        if counter % 500 == 0:
            #break
            print "IPs Looked for comparison:", counter

        ip_results = overall[ip]
        if len(ip_results) != 1:
            continue
        try:
            # don't consider the sources that you didn't send to Alidade.
            src = srcs_alidade[0]
            a = sources_alidade_with_location[src][ip]       
        except:
            continue
        total_ips += 1
        pred_country = ip_results[0]
        system_countries.add(pred_country)
        area_prediction_for_ip = False
        area_predictions_ip_set = set()
        if ip in area_pred_dict:
            area_predictions_total += 1
            area_predictions_ip_set = area_pred_dict[ip]
            area_prediction_for_ip = True
        # our sources
        test_instance = training_data_file.get_test_data(ip)
        for src in sources_compare:
            sources_country[src].add(test_instance[src])       
            if test_instance[src].lower() != pred_country.lower():
                sources_different_ip[src].add(ip)
            else:
                sources_count[src] += 1
            if area_prediction_for_ip and test_instance[src] not in area_predictions_ip_set:
                area_predictions_violated[src] += 1
        # alidade sources
        for src in srcs_alidade:
            try:
                sources_country[src].add(sources_alidade_with_location[src][ip])       
                if sources_alidade_with_location[src][ip].lower() != pred_country.lower():
                    sources_different_ip[src].add(ip)
                else:
                    sources_count[src] += 1
                if area_prediction_for_ip and sources_alidade_with_location[src][ip] not in area_predictions_ip_set:
                    area_predictions_violated[src] += 1
            except:
                #traceback.print_exc()
                srcs_alidade_exceptions[src] += 1
                sources_different_ip[src].add(ip)

    for src in sources_all:    # subtract two from all due to '' and 'EU'
        x = system_countries.difference(sources_country[src])
        y = sources_country[src].difference(system_countries)
        country_stats_dict[src] = len(x.union(y))
    print "Looking for differences all "
    traceroutes_affected_by_ips(trace_stats_dict, sources_different_ip, traceroute_ips_list)
    print "##############################################"
    print "Results:"
    print "##############################################"
    print "Total IP addresses:", total_ips
    print "Similarity dict of IP addresses:", sources_count
    print "Traceroutes Affected by these IPs:", trace_stats_dict
    print "Country difference:", country_stats_dict
    print "Total IP addresses with area predictions/SoL/Ground:", area_predictions_total
    print "Violations for area predictions/SoL/Ground:", area_predictions_violated
    print "##############################################"
    print "Total IPs:", total_ips
    print "Total Traceroutes:", total_traces
    print "Similarity dict of IP addresses:", {x:sources_count[x]*1.0/total_ips for x in sources_count}
    print "Traceroutes Affected by these IPs:", {x:trace_stats_dict[x]*1.0/total_traces for x in trace_stats_dict}
    print "Country difference:", country_stats_dict
    print "(Adjust for these) Alidade sources Exceptions:", srcs_alidade_exceptions
    print "Total IP addresses with area predictions/SoL/Ground:", area_predictions_total
    print "Violations for area predictions/SoL/Ground:", {x:area_predictions_violated[x]*1.0/area_predictions_total for x in area_predictions_violated}
    print "##############################################"
    print "##############################################"



def compare_with_local_sources_get_predictions_for_manual_analysis():
    ALIDADE_FOLDER = 'alidade_results'
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    traceroute_ips_list = prediction.load_pickle(TRACEOUTES_IP_ADDRESSES_FILE)
    system_predictions = prediction.load_pickle(prediction.OVERALL_SYSTEM_PREDICTIONS_DUMP_FILE)
    combined = system_predictions['combined']
    overall = system_predictions['overall']
    area_pred_dict = prediction.load_pickle(prediction.AREA_PREDICTIONS_ALL)
    #system_ips = set()
    system_countries = set()
    srcs_alidade = ['locs-es-latest', 'locs-es','ips--dbip', 'ips--mml','ips--mm','ips--iplg','ips--ip2l']
    srcs_alidade_exceptions = {x:0 for x in srcs_alidade}
    #srcs_alidade = ['locs-es']
    sources_compare = ['maxmind_country', 'ipinfo_country', 'ip2location_country', 'db_ip_country']
    sources_all = sources_compare + srcs_alidade
    sources_country = {}
    sources_different_ip = {}
    sources_count = {}
    trace_stats_dict = {}
    country_stats_dict = {}
    ip_addresses_predictions_dict = {}
    sources_alidade_with_location = load_all_alidade_source(cur_dir ,ALIDADE_FOLDER, srcs_alidade)
    area_predictions_violated = {}
    for src in sources_all:
        sources_different_ip[src] = set()
        sources_country[src] = set()
        sources_count[src] = 0
        trace_stats_dict[src] = 0
        country_stats_dict[src] = 0
        area_predictions_violated[src] = 0
    total_traces = len(traceroute_ips_list)
    area_predictions_total = 0
    total_ips = 0
    counter = 0
    for ip in overall:
        counter += 1
        if counter % 500 == 0:
            #break
            print "IPs Looked for comparison:", counter

        ip_results = overall[ip]
        if len(ip_results) != 1:
            continue
        try:
            # don't consider the sources that you didn't send to Alidade.
            src = srcs_alidade[0]
            a = sources_alidade_with_location[src][ip]       
        except:
            continue
        total_ips += 1
        pred_country = ip_results[0]
        system_countries.add(pred_country)
        area_prediction_for_ip = False        
        if ip in area_pred_dict:
            area_predictions_total += 1
            area_predictions_ip_set = area_pred_dict[ip]
            area_prediction_for_ip = True
        # our sources
        test_instance = training_data_file.get_test_data(ip)
        ip_addresses_predictions_dict[ip] = test_instance
        ip_addresses_predictions_dict[ip]['passport'] = pred_country
        for src in sources_compare:
            sources_country[src].add(test_instance[src])       
            if test_instance[src].lower() != pred_country.lower():
                sources_different_ip[src].add(ip)
            else:
                sources_count[src] += 1
            if area_prediction_for_ip and test_instance[src] not in area_predictions_ip_set:
                area_predictions_violated[src] += 1
        # alidade sources
        for src in srcs_alidade:
            try:
                sources_country[src].add(sources_alidade_with_location[src][ip])   
                ip_addresses_predictions_dict[ip][src] = sources_alidade_with_location[src][ip]
                if sources_alidade_with_location[src][ip].lower() != pred_country.lower():
                    sources_different_ip[src].add(ip)
                else:
                    sources_count[src] += 1
                if area_prediction_for_ip and sources_alidade_with_location[src][ip] not in area_predictions_ip_set:
                    area_predictions_violated[src] += 1
            except:
                #traceback.print_exc()
                ip_addresses_predictions_dict[ip][src] = ''
                srcs_alidade_exceptions[src] += 1
                sources_different_ip[src].add(ip)

    # get ip addresses for manual analysis.
    SVE_FILE_NAME = 'ip_addresses_selected_for_manual_comparison.csv'
    output_file_path = os.path.join(cur_dir, configs.pvt.DIR_DATA, SVE_FILE_NAME)
    csvw = csv.writer(open(output_file_path,"w"))
    selected_country_addresses = {}
    for ip in ip_addresses_predictions_dict:
        asn = ip_addresses_predictions_dict[ip]['asn'] 
        passport_country = ip_addresses_predictions_dict[ip]['passport']
        if asn  == -1:
            continue
        if passport_country not in selected_country_addresses:
            selected_country_addresses[passport_country] = {}
        if asn in selected_country_addresses[passport_country]: # only one ip per asn
            continue
        if len(selected_country_addresses[passport_country]) >= MAX_ASN_PER_COUNTRY_FOR_MANUAL:
            continue
        selected_country_addresses[passport_country][asn] = ip_addresses_predictions_dict[ip]
    headers = ['ip', 'asn', 'passport'] + sources_all
    other_headers = [k for k in ip_addresses_predictions_dict[ip] if k not in headers]
    headers = headers + other_headers
    csvw.writerow(headers)
    for cntry in selected_country_addresses:
        for asn in selected_country_addresses[cntry]:
            csvw.writerow([selected_country_addresses[cntry][asn][k] for k in headers])




#######################################################################
#######################################################################
def get_src_countries_total_all():
    get_src_countries_total(file_name=OUTPUT_FILE_FWD_TRACES)
    get_src_countries_total(file_name=OUTPUT_FILE_REV_TRACES)


def get_src_countries_total(file_name=OUTPUT_FILE_FWD_TRACES):
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, file_name)
    countries = set()
    countries_dest = set()
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            #print traceroute_data
            country = traceroute_data["src_cntry_name"]
            country_dest = traceroute_data["dst_cntry_name"]
            if country not in prediction.USELESS_PREDICTED_COUNTRIES:
                countries.add(country)
            if country_dest not in prediction.USELESS_PREDICTED_COUNTRIES:
                countries_dest.add(country_dest)
    print "Traceroutes | Total Source countries:", len(countries)
    print "Traceroutes | Total Source countries:", len(countries_dest)


def get_src_countries_total_ripe():
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    countries = set()
    probes = set()
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            #print traceroute_data
            probe = traceroute_data["prb_id"]
            country = traceroute_data["probe_country"]
            probes.add(probe)
            if country not in prediction.USELESS_PREDICTED_COUNTRIES:
                countries.add(country)
    print "Ripe | Total Source probes:", len(probes)
    print "Ripe | Total Source countries:", len(countries)


#######################################################################
#######################################################################
#######################################################################
def get_all_countries_trace(file_name, only_one_country_per_hop=True):
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, file_name)
    path_countries_dict = {}
    all_paths = {}
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            if 'hops' not in traceroute_data:
                continue
            # we're only looking for one
            #if traceroute_data["dst_cntry_name"] == "Pakistan" and traceroute_data["src_cntry_name"]!='United States':
                #print traceroute_data
            if only_one_country_per_hop and not is_there_only_one_prediction(traceroute_data['hops']):
                continue
            country_names = get_all_countries_names_traceroutes_paths(traceroute_data['hops'])
            if len(country_names) <= 0:
                continue
            src_name = traceroute_data["src"]
            dst_name = traceroute_data["dst"]
            src_c_name = traceroute_data["src_cntry_name"]
            dst_c_name = traceroute_data["dst_cntry_name"]
            all_paths[(src_c_name,dst_c_name,src_name,dst_name)] = traceroute_data
            path_countries_dict[(src_c_name,dst_c_name,src_name,dst_name)] = country_names
    return path_countries_dict,all_paths

def get_reverse_forward_interesting_cases_one_country_only(only_one_country_per_hop=True):
    sys_out_original = sys.stdout
    if only_one_country_per_hop: # one country predicted per hop
        output_file = "reverse_forward_difference_one_country_per_hop_only.txt"
    else:
        output_file = "reverse_forward_difference_all.txt"
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    out_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, output_file)
    out_file_handle = open(out_file_path, "w")
    #sys.stdout = out_file_handle
    path_countries_fwd, all_paths_fwd = get_all_countries_trace(OUTPUT_FILE_FWD_TRACES, only_one_country_per_hop)
    path_countries_rev, all_paths_rev = get_all_countries_trace(OUTPUT_FILE_REV_TRACES, only_one_country_per_hop)
    src_dst_pairs = path_countries_rev.keys() #expensive
    src_dst_pairs.sort()
    dst_countries_all = set()
    pairs_total = 0
    pairs_different = 0
    pairs_same = 0
    for src_dst in src_dst_pairs:
        if src_dst in path_countries_fwd:
            pairs_total += 1
            rev_cntry = path_countries_rev[src_dst]
            fwd_cntry = path_countries_fwd[src_dst]
            rev_only = rev_cntry.difference(fwd_cntry)
            fwd_only = fwd_cntry.difference(rev_cntry)
            if len(rev_only) > 0 or len(fwd_only) > 0:
                pairs_different += 1
                out_file_handle.write(str(src_dst))
                out_file_handle.write('\n')
                out_file_handle.write(json.dumps(all_paths_fwd[src_dst]))
                out_file_handle.write('\n')
                out_file_handle.write(json.dumps(all_paths_rev[src_dst]))
                out_file_handle.write('\n\n')
            else:
                pairs_same += 1
    print "Traceroutes with only one country per hop in path:", pairs_total 
    print "Traceroutes with only one country per hop in path and possible difference in countries for fwd and rev:", pairs_different
    print "Traceroutes with only one country per hop in path and no difference in countries for fwd and rev:", pairs_same 
    #sys.stdout = sys_out_original



#######################################################################
#######################################################################
#######################################################################
def get_traceroute_forward_interesting_cases_continent_country(only_one_country_per_hop=True):
    sys_out_original = sys.stdout
    if only_one_country_per_hop: # one country predicted per hop
        output_file = "traces_forward_leaving_country_one_country_per_hop_only.txt"
        output_file_continent = "traces_forward_leaving_continent_one_country_per_hop_only.txt"
    else:
        output_file = "traces_forward_leaving_country_all.txt"
        output_file_continent = "traces_forward_leaving_continent_all.txt"
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    country_continent_dict = utils.get_country_continent_dict()
    out_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, output_file)
    out_file_cont_path = os.path.join(cur_dir, prediction.DATA_FOLDER, output_file_continent)
    out_file_handle = open(out_file_path, "w")
    out_file_cont_handle = open(out_file_cont_path, "w")
    #sys.stdout = out_file_handle
    path_countries_fwd, all_paths_fwd = get_all_countries_trace(OUTPUT_FILE_FWD_TRACES, only_one_country_per_hop)
    #path_countries_rev, all_paths_rev = get_all_countries_trace(OUTPUT_FILE_REV_TRACES, only_one_country_per_hop)
    src_dst_pairs = path_countries_fwd.keys() #expensive
    src_dst_pairs.sort() # even more expensive
    dst_countries_all = set()
    pairs_total = 0
    pairs_different = 0
    pairs_same = 0
    all_cntry_set =set()
    all_bad_continents =set()
    all_bad_countries = set()
    for src_dst in src_dst_pairs:
        try:
            dst_continent = country_continent_dict[src_dst[1]]
            src_continent = country_continent_dict[src_dst[0]]
        except:
            continue
        fwd_cntry = path_countries_fwd[src_dst]
        line = json.dumps(all_paths_fwd[src_dst]) +'\n'
        # remove both countries
        if src_dst[1] in fwd_cntry:
            fwd_cntry.remove(src_dst[1])
        if src_dst[0] in fwd_cntry:
            fwd_cntry.remove(src_dst[0])

        if src_continent != dst_continent:
            continue

        fwd_cntnt = set([country_continent_dict[x] for x in fwd_cntry if x!=src_dst[1]])
        if src_continent in fwd_cntnt:
            fwd_cntnt.remove(src_continent)
        fwd_cntnt = list(fwd_cntnt)
        fwd_cntnt.sort()
        if len(fwd_cntnt) > 0:
            all_bad_continents.add(tuple(fwd_cntnt))
            out_file_cont_handle.write(line)
            out_file_cont_handle.write('\n')
            out_file_cont_handle.write('Src Country: ')
            out_file_cont_handle.write(src_dst[0])
            out_file_cont_handle.write(' | Src Continent: ')
            out_file_cont_handle.write(src_continent)
            out_file_cont_handle.write('\n')
            out_file_cont_handle.write('Dst Country: ')
            out_file_cont_handle.write(src_dst[1])
            out_file_cont_handle.write(' | Dst Continent: ')
            out_file_cont_handle.write(dst_continent)
            out_file_cont_handle.write('\n')
            out_file_cont_handle.write('Continents:\n')
            print >>out_file_cont_handle, fwd_cntnt
            out_file_cont_handle.write('\n')
            out_file_cont_handle.write('\n')
            
        if src_dst[0] != src_dst[1]: 
            # same country.
            continue

        fwd_cntry =list(fwd_cntry)
        fwd_cntry.sort()
        if len(fwd_cntry) == 0:
            continue
        all_bad_countries.add(tuple(fwd_cntry))
        out_file_handle.write(line)
        out_file_handle.write('\n')
        out_file_handle.write('Countries:\n')
        print >>out_file_handle, fwd_cntry
        out_file_handle.write('\n')
        out_file_handle.write('\n')

    print >>out_file_cont_handle, all_bad_continents
    print >>out_file_handle, all_bad_countries
            


#######################################################################################################
#######################################################################################################
#######################################################################################################
def get_traceroute_forward_interesting_cases_targetted_src_dst(src_cnt, dst_cnt, avoid_cnt_list, only_one_country_per_hop=True):
    sys_out_original = sys.stdout
    output_file = "traces_forward_interesting_cases_src_dst_avoid.txt"
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    country_continent_dict = utils.get_country_continent_dict()
    out_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, output_file)
    out_file_handle = open(out_file_path, "w")
    #sys.stdout = out_file_handle
    path_countries_fwd, all_paths_fwd = get_all_countries_trace(OUTPUT_FILE_FWD_TRACES, only_one_country_per_hop)
    #path_countries_rev, all_paths_rev = get_all_countries_trace(OUTPUT_FILE_REV_TRACES, only_one_country_per_hop)
    src_dst_pairs = path_countries_fwd.keys() #expensive
    src_dst_pairs.sort() # even more expensive
    dst_countries_all = set()
    pairs_total = 0
    pairs_different = 0
    pairs_same = 0
    traceroutes_total = 0
    all_cntry_set =set()
    all_bad_continents =set()
    all_bad_countries = set()
    traceroutes_total += 1
    for src_dst in src_dst_pairs:
        traceroutes_total += 1
        if dst_cnt != src_dst[1]:
            continue
        if src_cnt != src_dst[0]:
            continue
        fwd_cntry = path_countries_fwd[src_dst]
        bad_cnt_found = [x for x in fwd_cntry if x in avoid_cnt_list]
        if len(bad_cnt_found) <= 0:
            continue
        line = json.dumps(all_paths_fwd[src_dst]) +'\n'
    
        out_file_handle.write(line)
        out_file_handle.write('\n')
        out_file_handle.write('\n')
    print traceroutes_total

#######################################################################################################
#######################################################################################################
#######################################################################################################
def get_interesting_cases_ripe_leaving_country(only_one_country_per_hop=True):
    # we don't consider intera EU cases interesting.
    country_lat_lon_dict = read_country_lat_lon_dict()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    special_file_name = "ripe_leaving_country_all.txt.bz2"
    if only_one_country_per_hop:
        special_file_name = "ripe_leaving_country_only_one_country_per_hop.txt.bz2"
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    special_case_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, special_file_name)
    special_case_high_dist_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_DISTANCE_SPECIAL_RIPE_HIGH_DIST)
    special_case_file = bz2.BZ2File(special_case_file_path, "w")
    #ignore_countries = ['Canada', 'Germany', 'United Kingdom', 'Hong Kong', 'Denmark', 'Switzerland','Cuba','Sweden']
    #ignore_sets = [('Belgium', 'United Kingdom'),('Belgium', 'Denmark'), ('Denmark', 'Romania'),('Poland',),('France', 'Poland', 'United States'),('Austria', 'United States'),('France', 'United Kingdom', 'United States'),('France', 'Hong Kong', 'United States')]   # make sure all tuples are sorted
    all_bad_countries = set()
    us_to_us = 0
    ca_to_ca_via_us = 0
    ca_to_ca = 0
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            if 'result' not in traceroute_data:
                continue
            # we're only looking for one
            single_prediction, one_country_hop_dict = is_there_only_one_prediction_ripe(traceroute_data['result'])
            if only_one_country_per_hop and not single_prediction:
                continue
            #print one_country_hop_dict # this dict contains the variant of hop (there are usualy 3 variants after traceroute. but we only need one.
            useful_hop_idx_list = one_country_hop_dict.keys()
            useful_hop_idx_list.sort()
            dst_hop = max(useful_hop_idx_list) # we only go to the last hop
            success, src_dest_distance = get_src_dest_distance_ripe(traceroute_data, country_lat_lon_dict, dst_hop, one_country_hop_dict)
            if not success:
                continue
            if src_dest_distance > 0: # src and dst are not in same country.
                continue
            src_country = traceroute_data["probe_country"]
            all_countries_set = get_all_countries_in_path_ripe(traceroute_data,country_lat_lon_dict, useful_hop_idx_list, one_country_hop_dict, only_one_country_per_hop)
            if src_country == "United States":
                us_to_us += 1
            if src_country == "Canada":
                ca_to_ca += 1            
            if len(all_countries_set) > 1:
                bad_cntry = [x for x in all_countries_set if x!=src_country]
                #if len(bad_cntry) == 1 and bad_cntry[0] in ignore_countries:
                #    continue
                bad_cntry.sort()
                #if tuple(bad_cntry) in ignore_sets:
                #    continue
                if src_country == "Canada" and "United States" in bad_cntry:
                    ca_to_ca_via_us += 1
                all_bad_countries.add(tuple(bad_cntry))
                special_case_file.write(line)
                special_case_file.write('\n')
                special_case_file.write('Countries:\n')
                print >>special_case_file, bad_cntry
                special_case_file.write('\n')
                special_case_file.write('\n')
    special_case_file.close()
    print all_bad_countries
    print "All USA:", us_to_us
    print "Canada to canada via usa:", ca_to_ca_via_us, ca_to_ca




#######################################################################################################
#######################################################################################################
#######################################################################################################

def get_interesting_cases_ripe_leaving_continent(only_one_country_per_hop=True):
    # we don't consider intera EU cases interesting.
    country_lat_lon_dict = read_country_lat_lon_dict()
    country_continent_dict = utils.get_country_continent_dict()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    special_file_name = "ripe_leaving_continent_all.txt.bz2"
    if only_one_country_per_hop:
        special_file_name = "ripe_leaving_continent_only_one_country_per_hop.txt.bz2"
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    special_case_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, special_file_name)
    special_case_high_dist_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_DISTANCE_SPECIAL_RIPE_HIGH_DIST)
    special_case_file = bz2.BZ2File(special_case_file_path, "w")
    #ignore_countries = ['Canada', 'Germany', 'United Kingdom', 'Hong Kong', 'Denmark', 'Switzerland','Cuba','Sweden']
    #ignore_sets = [('Belgium', 'United Kingdom'),('Belgium', 'Denmark'), ('Denmark', 'Romania'),('Poland',),('France', 'Poland', 'United States'),('Austria', 'United States'),('France', 'United Kingdom', 'United States'),('France', 'Hong Kong', 'United States')]   # make sure all tuples are sorted
    all_bad_continents = set()
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            if 'result' not in traceroute_data:
                continue
            # we're only looking for one
            single_prediction, one_country_hop_dict = is_there_only_one_prediction_ripe(traceroute_data['result'])
            if only_one_country_per_hop and not single_prediction:
                continue
            #print one_country_hop_dict # this dict contains the variant of hop (there are usualy 3 variants after traceroute. but we only need one.
            useful_hop_idx_list = one_country_hop_dict.keys()
            useful_hop_idx_list.sort()
            dst_hop = max(useful_hop_idx_list) # we only go to the last hop
            success, src_dest_distance = get_src_dest_distance_ripe(traceroute_data, country_lat_lon_dict, dst_hop, one_country_hop_dict)
            if not success:
                continue
            src_country = traceroute_data["probe_country"]
            variant = one_country_hop_dict[dst_hop]
            #print len(traceroute_data["result"]), dst_hop
            dst_country = traceroute_data["result"][dst_hop]['result'][variant]['predictions'][0] # zero since it will have one elem always. we check it before this.
            try:
                dst_continent = country_continent_dict[dst_country]
                src_continent = country_continent_dict[src_country]
            except:
                traceback.print_exc()
                continue
            if src_continent != dst_continent:
                continue
            all_countries_set = get_all_countries_in_path_ripe(traceroute_data,country_lat_lon_dict, useful_hop_idx_list, one_country_hop_dict, only_one_country_per_hop)
            all_continents_set = set([country_continent_dict[x] for x in all_countries_set])
            if len(all_continents_set) > 1:
                bad_cntnt = [x for x in all_continents_set if x!=src_continent]
                #if len(bad_cntry) == 1 and bad_cntry[0] in ignore_countries:
                #    continue
                bad_cntnt.sort()
                #if tuple(bad_cntry) in ignore_sets:
                #    continue
                all_bad_continents.add(tuple(bad_cntnt))
                special_case_file.write(line)
                special_case_file.write('\n')
                special_case_file.write('Src Country: ')
                special_case_file.write(src_country)
                special_case_file.write(' | Src Continent: ')
                special_case_file.write(src_continent)
                special_case_file.write('\n')
                special_case_file.write('Dst Country: ')
                special_case_file.write(dst_country)
                special_case_file.write(' | Dst Continent: ')
                special_case_file.write(dst_continent)
                special_case_file.write('\n')
                special_case_file.write('Continents:\n')
                print >>special_case_file, bad_cntnt
                special_case_file.write('\n')
                special_case_file.write('\n')
    print >>special_case_file, all_bad_continents
    special_case_file.close()
    print all_bad_continents

#######################################################################################################
#######################################################################################################
#######################################################################################################
def add_all_ip_address_per_traceroutes_traceoutes(input_file_path, traceroute_ips_list):
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            if 'hops' not in traceroute_data:
                continue            
            traceroute_hops = traceroute_data['hops']
            ip_addresses = set()
            for hop in traceroute_hops:
                if 'ip' not in hop:
                    continue
                ip_addresses.add(hop['ip'])
            #print len(ip_addresses)
            traceroute_ips_list.append(ip_addresses)



def generate_all_ip_addresses_per_traceroutes_file():
    # read ripe traceroutes.
    cur_dir = os.path.dirname(os.path.realpath(__file__))    
    traceroute_ips_list = []
    print "Generating Traceoute to IP mapping!"
    print "Generating Traceoute to IP mapping: Reading FWD Trace"
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_FWD_TRACES)
    add_all_ip_address_per_traceroutes_traceoutes(input_file_path, traceroute_ips_list)
    print "Generating Traceoute to IP mapping: Reading REV Trace"
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_REV_TRACES)
    add_all_ip_address_per_traceroutes_traceoutes(input_file_path, traceroute_ips_list)
    print "Generating Traceoute to IP mapping: Reading Ripe Atlas"
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    with bz2.BZ2File(input_file_path, "r") as data_file:
        for line in data_file:
            traceroute_data = json.loads(line)
            if 'result' not in traceroute_data:
                continue            
            traceroute_hops = traceroute_data['result']
            ip_addresses = set()
            for hop in traceroute_hops:
                if 'result' not in hop:
                    continue
                hop_results = hop['result']
                for hop_result in hop_results:
                    if 'from' not in hop_result:
                        continue
                    ip_addresses.add(hop_result['from'])
            #print len(ip_addresses)
            traceroute_ips_list.append(ip_addresses)
    print "Total traceroutes to IP mappings:", len(traceroute_ips_list)
    prediction.save_pickle(traceroute_ips_list, TRACEOUTES_IP_ADDRESSES_FILE)



###########################################################################

def generate_traceoutes_with_atleast_one_ground_truth_ip_traceroutes_ripe(cnt_min_ground_truth):
    cur_dir = os.path.dirname(os.path.realpath(__file__))    
    traceroute_ips_list = []
    ripe_probes_info_dict = prediction.load_ripe_node_info()
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    save_file_name = OUTPUT_FILE_RIPE_TRACES.split('.')[0]+"_with_atleast_"+str(cnt_min_ground_truth)+"_correct_ips.bz2"
    output_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, save_file_name)
    cached_info = {}
    cached_hostname_dictionary = {}
    ground_truth_from_database = training_data_file.get_ground_truth_all()
    area_intesection_boxes_ripe = prediction.get_intersection_boxes_ip_dict(
        prediction.RIPE_IPS_LATLON_FILE)
    lines_processed = 0
    with bz2.BZ2File(output_file_path, "w") as write_data_file:
        with bz2.BZ2File(input_file_path, "r") as data_file:
            for line in data_file:
                hostnames_seen = set()
                ip_addresses_seen = set()
                lines_processed += 1
                if lines_processed % 100 == 0:
                    print "Traceroutes Processed:", str(lines_processed)
                ground_truth_count = 0
                traceroute_data = json.loads(line)
                if 'result' not in traceroute_data:
                    continue            
                src = ripe_probes_info_dict[traceroute_data["prb_id"]]
                if src["latitude"] == 0:
                    continue
                src_lat = src["latitude"]
                src_lon = src["longitude"]
                traceroute_data["src_longitude"] = src_lon
                traceroute_data["src_latitude"] = src_lat
                traceroute_hops = traceroute_data['result']
                ip_addresses = set()
                for hop in traceroute_hops:
                    if 'result' not in hop:
                        continue
                    hop_results = hop['result']
                    for hop_result in hop_results:
                        if 'from' not in hop_result:
                            continue
                        if hop_result['from'] in ground_truth_from_database and hop_result['from'] not in ip_addresses_seen:
                            ip_addresses_seen.add(hop_result['from'])
                            #ground_truth_count += 1
                        if hop_result['from'] not in cached_info:
                            cached_info[hop_result['from']] = training_data_file.get_test_data(hop_result['from']) 
                        hop_result['as_information'] = cached_info[hop_result['from']]
                        if 'hostname' not in hop_result:
                            continue 
                        if hop_result['hostname'] not in cached_hostname_dictionary:
                            loc_info_hostname = ddec.ddec_get_hostname_location(hop_result['hostname'])
                            cached_hostname_dictionary[hop_result['hostname']] = loc_info_hostname
                        else:
                            loc_info_hostname = cached_hostname_dictionary[hop_result['hostname']]
                        try:
                            if loc_info_hostname:
                                if hop_result['hostname'] not in hostnames_seen:
                                    hostnames_seen.add(hop_result['hostname'])
                                    ground_truth_count += 1
                                hop_result['location_info'] = {}
                                hop_result['location_info']['latitude'] = float(str(loc_info_hostname['latitude']))
                                hop_result['location_info']['longitude'] = float(str(loc_info_hostname['longitude']))
                        except:
                            traceback.print_exc()
                        if hop_result['from'] not in area_intesection_boxes_ripe:
                            #print hop_result
                            continue
                        hop_result['intersection_region'] = area_intesection_boxes_ripe[hop_result['from']]
                if ground_truth_count >= cnt_min_ground_truth:
                    write_data_file.write(json.dumps(traceroute_data))
                    write_data_file.write('\n') 


def generate_traceoutes_with_atleast_one_ground_truth_ip_traceroutes_ripe_speed(cnt_min_ground_truth):
    cur_dir = os.path.dirname(os.path.realpath(__file__))    
    traceroute_ips_list = []
    ripe_probes_info_dict = prediction.load_ripe_node_info()
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    save_file_name = OUTPUT_FILE_RIPE_TRACES.split('.')[0]+"_with_atleast_"+str(cnt_min_ground_truth)+"_correct_ips_speed.bz2"
    output_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, save_file_name)
    cached_info = {}
    ground_truth_from_database = training_data_file.get_ground_truth_all()
    area_intesection_boxes_ripe = prediction.get_intersection_boxes_ip_dict(
        prediction.RIPE_IPS_LATLON_FILE)
    lines_processed = 0
    with bz2.BZ2File(output_file_path, "w") as write_data_file:
        with bz2.BZ2File(input_file_path, "r") as data_file:
            for line in data_file:
                ip_addresses_seen = set()
                lines_processed += 1
                if lines_processed % 100 == 0:
                    print "Traceroutes Processed:", str(lines_processed)
                ground_truth_count = 0
                traceroute_data = json.loads(line)
                if 'result' not in traceroute_data:
                    continue            
                src = ripe_probes_info_dict[traceroute_data["prb_id"]]
                if src["latitude"] == 0:
                    continue
                src_lat = src["latitude"]
                src_lon = src["longitude"]
                traceroute_data["src_longitude"] = src_lon
                traceroute_data["src_latitude"] = src_lat
                traceroute_hops = traceroute_data['result']
                ip_addresses = set()
                for hop in traceroute_hops:
                    if 'result' not in hop:
                        continue
                    hop_results = hop['result']
                    for hop_result in hop_results:
                        if 'from' not in hop_result:
                            continue
                        if hop_result['from'] in ground_truth_from_database and hop_result['from'] not in ip_addresses_seen:
                            ip_addresses_seen.add(hop_result['from'])
                            ground_truth_count += 1
                        if hop_result['from'] not in cached_info:
                            cached_info[hop_result['from']] = training_data_file.get_test_data(hop_result['from']) 
                        hop_result['as_information'] = cached_info[hop_result['from']]
                        if hop_result['from'] not in area_intesection_boxes_ripe:
                            #print hop_result
                            continue
                        hop_result['intersection_region'] = area_intesection_boxes_ripe[hop_result['from']]
                if ground_truth_count >= cnt_min_ground_truth:
                    write_data_file.write(json.dumps(traceroute_data))
                    write_data_file.write('\n') 

###########################################################################

def generate_traceoutes_with_specific_ip_addresses(ip_addresses_list):
    ip_addresses_list_set = set(ip_addresses_list)
    cur_dir = os.path.dirname(os.path.realpath(__file__))    
    traceroute_ips_list = []
    ripe_probes_info_dict = prediction.load_ripe_node_info()
    input_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, OUTPUT_FILE_RIPE_TRACES)
    save_file_name = OUTPUT_FILE_RIPE_TRACES.split('.')[0]+"_traceoutes_with_specific_ip_addresses.bz2"
    output_file_path = os.path.join(cur_dir, prediction.DATA_FOLDER, save_file_name)
    cached_info = {}
    ground_truth_from_database = training_data_file.get_ground_truth_all()
    area_intesection_boxes_ripe = prediction.get_intersection_boxes_ip_dict(
        prediction.RIPE_IPS_LATLON_FILE)
    lines_processed = 0
    with bz2.BZ2File(output_file_path, "w") as write_data_file:
        with bz2.BZ2File(input_file_path, "r") as data_file:
            for line in data_file:
                ip_addresses_seen = set()
                lines_processed += 1
                if lines_processed % 100 == 0:
                    print "Traceroutes Processed:", str(lines_processed)
                traceroute_data = json.loads(line)
                if 'result' not in traceroute_data:
                    continue            
                src = ripe_probes_info_dict[traceroute_data["prb_id"]]
                if src["latitude"] == 0:
                    continue
                src_lat = src["latitude"]
                src_lon = src["longitude"]
                traceroute_data["src_longitude"] = src_lon
                traceroute_data["src_latitude"] = src_lat
                traceroute_hops = traceroute_data['result']
                ip_addresses = set()
                found_ip = False
                for hop in traceroute_hops:
                    if found_ip:
                        break
                    if 'result' not in hop:
                        continue
                    hop_results = hop['result']
                    for hop_result in hop_results:
                        if 'from' not in hop_result:
                            continue
                        if hop_result['from'] in ip_addresses_list:
                            found_ip = True
                if found_ip:
                    write_data_file.write(json.dumps(traceroute_data))
                    write_data_file.write('\n') 
                    write_data_file.write('\n') 
                    write_data_file.write('\n') 

