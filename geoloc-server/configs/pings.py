# -*- coding: utf-8 -*-
"""

    config.pings
    ~~~~~~~~~~~

    This configuration file contains the configs to perform ping measurements to remote VPs

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu
"""

__author__ = "Muzammil Abdul Rehman"
__copyright__ = "Northeastern University © 2018"
__license__ = "Custom BSD"
__email__ = "passport@ccs.neu.edu"

######################################################
# api key for the revtr server
KEY = {'Api-Key': 'API-KEY-REMOVED'}   # change this key

# Pings for ground truth
PERFORM_NEW_PINGS_GROUND_TRUTH = False
# url for ping posts
PING_URL = 'https://revtr.ccs.neu.edu/api/v1/ping'
# number of pings to run from one source to destination
PING_COUNT = 3
# url for ping sources
SOURCES_URL = 'https://revtr.ccs.neu.edu/api/v1/vps'
#KEY = {'Api-Key': 'api_limit'}   # change this key
# time in seconds to sleep between results queries
SLEEP_TIME = 7
# maximum number of tries to get results
MAX_TRIES = 3
# directory to store ping results in
PINGS_DIR = 'pings'
RESULTS_URL_DIR = 'results_url'
# maximum number of days a ping measurement is valid for
MAX_PING_AGE = 30
# print number of addresses looked up
PRINT_NUM_POOLS_FINISHED = True
POOLS_FINISHED_TIMER = 30 # seconds
