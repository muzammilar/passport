# -*- coding: utf-8 -*-
"""

    ppcore.system.offline
    ~~~~~~~~~~~~~~

    This module assumes that all the measurements have been performed
    and data has been cached. It then perform predictions and analysis
    using Prediction System and Traceroute Analysis modules in this package.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import ppcore.system.prediction as prediction_system
import ppcore.system.tracertanalysis as traceroutes_analysis

def main():
    prediction_system.main()
    traceroutes_analysis.main()


