#!/usr/bin/env python
"""

    manage.py
    ~~~~~~~~~~~~~~

    This module needs to be run to setup ORM databases and other Django commands.
    This module has been developed to be used as django admin for creating the
    database. It is not used in the system once the databases have been created.
    It's only used for updating and modifying the database.

    :author: Muzammil Abdul Rehman
    :copyright: Copyright Northeastern University,  2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

import os
import sys

# Django ORM File

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ormsettings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


