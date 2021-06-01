# -*- coding: utf-8 -*-
"""

    config.intersection
    ~~~~~~~~~~~

    This configuration file contains the configs for analyising all measurements using the
    hexagon/geodisic circle/rectangle intersection.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

# traceroute package
traceroute_pkg_folder = "ppmeasurements"
# traceroute folder
traceroute_folder = "traceroutes"
ignore_files = ["_info.txt", ".gitignore"]
SPEED_MAX_RTT = 100  # milliseconds
SPEED_LIGHT = 299.792458 # kilometers/milisecond
SPEED_LIGHT_FACTOR = 0.47 # 0.47c, 0.667c or c. we use 0.51 in order to remove uncertaininty in lat-lon
#OUTPUT_INTERMEDIATE_HOPS_CAIDA_ALIAS = True  ## This is not in use
