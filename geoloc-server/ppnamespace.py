# -*- coding: utf-8 -*-
"""

    ppnamespace.py
    ~~~~~~~~~~~~~~

    This module contains all the global variables in the Passport namespace. It should be initialized during the
    bootstrap of the system. These variables should not be modified after creation, except the queue and cache.
    This module has been developed to keep the global state of the system. This global state is required for
    country name translations (from ISO 2 Code to Country Name), cached predictions, router aliases, data
    structures to store country polygons (for intersection), geolocation sources (MaxMind, DBIP, IP2Location).
    The main purpose is to prevent the system from reading data from the database/disk again and again.


    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from multiprocessing import Process, Manager, Queue
import threading
#import Queue
import configs.system

def init(MANAGER=None):
    """Initializes all the globally accessible resources in the Passport namespaces"""

    if MANAGER is None:
        MANAGER = Manager()
    global LOADED_CLASSIFIERS
    global COUNTRY_ISO_CODE_DICT
    global COUNTRY_ISO_CODE_DICT_SECOND
    global DBIP_INTERVAL_TREE
    global MAXMIND_INTERVAL_TREE
    global MAXMIND_DICT
    global IP2LOCATION_INTERVAL_TREE
    global IXP_SUBNET_INTERVAL_TREE
    global IXP_LOCATION_DICT
    global overall
    global classifier
    global area
    global combined
    global src_info_dict
    global SYSTEM_DICT_MAIN
    global WRITE_LOCK_SRC_INFO
    global QUEUE_IPS_LOOKUP
    global LOCK_PROC_RUNNING
    global LOCK_PREDICTIONS_UPDATED
    SYSTEM_DICT_MAIN = MANAGER.dict()
    SYSTEM_DICT_MAIN[configs.system.SYSTEM_PROC_RUNNING] = True
    SYSTEM_DICT_MAIN[configs.system.SYSTEM_PRED_UPDATED] = False
    LOCK_PREDICTIONS_UPDATED = MANAGER.Lock()
    WRITE_LOCK_SRC_INFO = threading.Lock()
    QUEUE_IPS_LOOKUP = Queue()   # queue for IP addresses
    LOCK_PROC_RUNNING = MANAGER.Lock()
    IP2LOCATION_INTERVAL_TREE = []
    MAXMIND_INTERVAL_TREE = []
    DBIP_INTERVAL_TREE = []
    MAXMIND_DICT = {}
    IXP_SUBNET_INTERVAL_TREE = []
    IXP_LOCATION_DICT = {}
    LOADED_CLASSIFIERS = MANAGER.list()
    COUNTRY_ISO_CODE_DICT = MANAGER.dict()
    COUNTRY_ISO_CODE_DICT_SECOND = {}
    overall = MANAGER.dict()    # cache for locations by system
    combined = MANAGER.dict()   # cache for location intersection of area and classifier
    area = MANAGER.dict()       # cache for location by SoL intersection
    classifier = MANAGER.dict() # cache for locations by classifier
    src_info_dict = MANAGER.dict()
    router_aliases_dict = {}
    country_polygon_dict = {}
