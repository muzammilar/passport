# -*- coding: utf-8 -*-
"""

    ppcore.system.parser
    ~~~~~~~~~~~~~~

    (Deprecated) This module is an example of reading a simple bz2 compressed file

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import bz2
import json

def parse_file(file_path):
    with bz2.BZ2File(file_path, "r") as data_file:
        for line in data_file:
            json_data = json.loads(line)
            #print json_data

if __name__ == '__main__':
    parse_file('fwd_traces.txt.bz2')
