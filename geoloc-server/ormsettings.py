"""

    ormsettings.py
    ~~~~~~~~~~~~~~

    This module contains Django settings to be used for ORM (database connection).
    This module has been developed to be used as django settings module for accessing (not creating) the database.
    It has to be imported in every file that needs to access the database or the Django Models.

    :author: Muzammil Abdul Rehman
    :copyright: Copyright Northeastern University,  2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from django.conf import settings
import configs.system
from ConfigParser import SafeConfigParser

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

ADMIN_ENABLED = False

################################################
config_parser = SafeConfigParser()
config_parser.read("configs.txt")
if configs.system.HOSTED_LOCALLY:
    section = "Local"
else:
    section = "Remote"
username = config_parser.get(section, 'username')
password = config_parser.get(section, 'password')
hostname = config_parser.get(section, 'hostname')
database = config_parser.get(section, 'database')
################################################

if configs.system.HOSTED_LOCALLY:
    DATABASES = {
      'default': {
        'ENGINE': 'django.db.backends.mysql',
          # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': database,                    
        'USER': username,                      
        'PASSWORD': password,                  
        'HOST': hostname,                  
        'PORT': '3306',                      
      }
    }

else:
    DATABASES = {
      'default': {
        'ENGINE': 'django.db.backends.mysql',
          # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': database,                      # Or path to database file if using sqlite3.
        'USER': username,                      # Not used with sqlite3.
        'PASSWORD': password,                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
      }
    }

INSTALLED_APPS = ("ppstore",)

settings.configure(DATABASES=DATABASES, INSTALLED_APPS=INSTALLED_APPS)
