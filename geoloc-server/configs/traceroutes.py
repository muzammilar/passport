# -*- coding: utf-8 -*-
"""

    config.traceroutes
    ~~~~~~~~~~~

    This configuration file contains the configs to perform forward and reverse traceroute measurements from remote VPs

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

__author__ = "Muzammil Abdul Rehman"
__copyright__ = "Northeastern University © 2018"
__license__ = "Custom BSD"
__email__ = "passport@ccs.neu.edu"


#################################
# api key for revtr server
KEY = 'API-KEY-REMOVED'   # please request a key.
# api key for EurekAPI
EUREKAPI_KEY = "API-KEY-REMOVED"
# api key for ipinfo.io
IPINFO_IO_TOKEN = "TOKEN-REMOVED"
#################################
# url for revtr posts
REVTR_URL = 'https://revtr.ccs.neu.edu/api/v1/revtr'
# url for traceroute posts
TRACE_URL = 'https://revtr.ccs.neu.edu/api/v1/traceroute'
# url for traceroute sources
# this is not currently used
SOURCES_URL = 'https://revtr.ccs.neu.edu/api/v1/sources'
# staleness for traceroutes in minutes
STALENESS = 60*24*15
# time in seconds to sleep between results queries
SLEEP_TIME = 10
# maximum number of tries to get results
MAX_TRIES = 10
TIME_FACTOR_REVTR = 10
# directory to store traceroute results in
TRACE_DIR = 'traceroutes'
FWD_DIR = 'fwdtr'
REV_DIR = 'revtr'
RESULTS_URL_DIR = 'results_url'
MAX_URLS_PER_COUNTRY = 3
MAX_TRACE_AGE = 30


#################################
# Ripe
from datetime import datetime
from datetime import timedelta
RIPE_MAX_PROC_INIT_PROCESSING = 5
RIPE_PARENT_FOLDER = 'ripe'
RIPE_DATA_FOLDER = 'data'
RIPE_NODE_FOLDER = 'nodes'
RIPE_TRACEROUTES_FOLDER = 'traceroutes'
RIPE_PINGS_FOLDER = 'pings'
RIPE_RAW_FOLDER = 'raw'
START_DATE_DATA = datetime(2017, 04, 24)
END_DATE_DATA = datetime(2017, 05, 01) + timedelta(days=1) # one day cos we include that day.
RELAVENT_TRACES_FILE_SUFFIX = "_relavent_traces.txt"
