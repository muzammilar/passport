# -*- coding: utf-8 -*-
"""

    ensemble.datapts
    ~~~~~~~~~~~~~~~~~

    This module generates the number of training instances for each country required
    for each classifier


    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""
from ensemble import sourcediff


def get_acutual_numbers_and_write_to_file(lst_samples_per_country):
    sourcediff.get_difference_between_sources(lst_samples_per_country)


def generate_data_points():
    SAMPLE_SIZE_PER_COUNTRY_LIST = [30, 50]
    """
    getAccuraciesAndWriteToFile(SAMPLE_SIZE_PER_COUNTRY_LIST,
                    configs.system.DIR_DATA,configs.system.SECONDARY_ANALYSIS_FILE)
    """
    get_acutual_numbers_and_write_to_file(SAMPLE_SIZE_PER_COUNTRY_LIST)


