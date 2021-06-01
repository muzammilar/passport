# -*- coding: utf-8 -*-
"""

    config.system
    ~~~~~~~~~~~

    This configuration file contains the configs for booting up the system, the locations of classifiers, the website,
    accessing geolocation sources

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu
"""

import os

########################################################
# Website - Online System
########################################################
SERVER_HOST = "0.0.0.0"  # 0.0.0.0 for external visible localhost for local
SERVER_PORT = 45481
WEB_PARENT_FOLDER = "website"
WEB_TEMPLATES_FOLDER = "templates"
WEB_STATIC_FOLDER = "static"
WEB_DEBUG_MODE = True
THREAD_IP_PROCESSING_WAIT = 5 # sec
MAX_IPS_PROCESSING = 6 # max ips to lookup simultaneously using revtr

########################################################
# Google MAPs API key for DDEC
GOOGLE_MAP_API_KEYS=["API-KEY-REMOVED"] #please provide one.

########################################################

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

########################################################
# Database related

HOSTED_LOCALLY = True
CONFIG_FILE_PATH = "../config.txt"

########################################################
# Classifier Related

CLASSIFIER_FILES_DIR_NAME = "classifiers"
NUM_TREE_IN_FOREST = 10
TRAIN_NEW_CLASSIFIERS = False
RETRAIN_CLASSIFIERS_WITHOUT_ANALYSIS_AGAIN = False
GEO_SOURCES_UPDATED = True
SAVE_CLASSIFIERS_GRAPH = True
SAVE_CLASSIFIERS_GRAPH_DIR = "graph"

########################################################
# Classifier File names

DEFAULT_CLS_FILE = "default.pkl"
NUM_VARIANTS_CLS = 2

########################################################
# Data folders

DIR_DATA = "data"
ROUTER_LOC_ALIAS_DIR = "aliases"
ANALYSIS_FOLDER_DOUBLE = "double"
ANALYSIS_FOLDER_PROPORTIONAL = "proportional"
ANALYSIS_FOLDER_RANDOM = "random"
SECONDARY_ANALYSIS_FILE = "secondary_analysis.csv"
GENERATE_DATA_POINTS_FILE_PTS = "data_points.csv"
GENERATE_DATA_POINTS_FILE_ACC = "data_points_acc.csv"
SRC_MAXMIND = "MaxMindGeoLite2.csv"
SRC_MAXMIND_LOC_INFO = "MaxMindGeoLite2_locations.csv"
SRC_DBIP = "DBIP.csv"
SRC_IP2LOCATION = "IP2Location.csv"
GEO_FOLDER_DUMP = 'geosources'
MAXMIND_DUMP_NAME = "mm.pkl"
MAXMIND_DICT_DUMP_NAME = "mm_dict.pkl"
DBIP_DUMP_NAME = "dbip.pkl"
IP2LOCATION_DUMP_NAME = "ip2loc.pkl"

########################################################
# world borders maps.
WORLD_BORDER_FILE = "TM_WORLD_BORDERS_SIMPL"
WORLD_BORDER_DIR_BASE = "country_maps"

########################################################
# feedback
APPLY_FEEDBACK = True
FEEDBACK_MAX_COUNTRIES = 1

########################################################
# DDEC
EXTERNAL_TIMEOUT = 30

########################################################
# IXP
IXP_DATA_DIR = "ixps"
IXP_DATA_EXCHANGE_PREF = "exchange"
IXP_DATA_ACTIVE_SUBNET_PREF = "subnet_active"


########################################################
# Update ground truth
CLEAN_CACHE_GROUND_TRUTH = True

########################################################
# Thread names
THREAD_NAME_IP_PROCESSING = 'PROCESS-IP-Processing'
THREAD_NAME_SAVE_PRED_DISK = 'PROCESS-Save-Predictions'

########################################################
#Variable names
SYSTEM_PROC_RUNNING = 'SYSTEM_PROC_RUNNING'
SYSTEM_PRED_UPDATED = 'SYSTEM_PRED_UPDATED'

########################################################
#Online System
ONLINE_GEOLOCATION_MAX_COUNTRIES_ALLOWED = 2
ONLINE_GEOLOCATION_UNKNOWN_COUNTRY = "Unknown"

########################################################
# Speed
PROPAGATION_SPEED = 1.79986
