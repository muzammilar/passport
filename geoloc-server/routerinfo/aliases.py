# -*- coding: utf-8 -*-
"""

    routerinfo.aliases
    ~~~~~~

    A module to convert multiple router IP address aliases to a single router IP address.
     This module contains the code for converting multiple router aliases to single router address.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import os
import pputils
import configs.system
# these IP addresses are integer not strings!

def get_latest_file_path():
    """ Returns the path to the folder containing router aliases"""
    FILE_ABS_PATH = os.path.abspath(__file__)
    data_folder_name = os.path.basename(FILE_ABS_PATH).split(".py")[0]
    data_folder = os.path.join(configs.system.PROJECT_ROOT,
                               configs.system.DIR_DATA,
                               configs.system.ROUTER_LOC_ALIAS_DIR)
    data_folder_files = os.listdir(data_folder)
    latest_file = max(data_folder_files)  # this is because yyyymmdd.sets
    f_path = os.path.join(data_folder, latest_file)
    return f_path


def get_router_aliases():
    """
    Returns a dictionary containing IP address aliases

    :return: A dictionary with a single IP address as the `key` and a <set> of IP addresses aliases as `values`
            {'1.2.3.4':set(['2.4.5.6', '6.7.8.9']), ...}
    """
    file_path = get_latest_file_path()
    alias_dictionary = {}
    router_set_ip = ''
    new_set = False
    with open(file_path, 'r') as alias_file:
        for line in alias_file:
            # # set
            if line.startswith('# set ') or line.startswith('# set\t'):
                new_set = True
                continue
            # comments
            if line.startswith('#'):
                continue
            # first after '# set'
            if new_set:
                new_set = False
                router_set_ip = pputils.ip_string_to_int(line.split('\n')[0])
            # all the other
            router_alias = pputils.ip_string_to_int(line.split('\n')[0])
            alias_dictionary[router_alias] = router_set_ip
    return alias_dictionary


if __name__ == '__main__':
    print get_router_aliases()
