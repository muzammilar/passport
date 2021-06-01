# Passport: Enabling Accurate Country-Level Router Geolocation using Inaccurate Sources
---
Passport provides location predictions with limited active measurements, using machine learning to combine information from IP geolocation databases, router hostnames, whois records, and ping (and traceroute measurements) measurements.

Read the full paper at: https://arxiv.org/abs/1905.04651

Webiste: https://passport.ccs.neu.edu

**Note:** The system was originally written in *Python2.7* in *2016*.

## Publications

* Abdul Rehman, Muzammil, Sharon Goldberg, and David Choffnes. "Passport: enabling accurate country-level router geolocation using inaccurate sources." *arXiv preprint arXiv:1905.04651* (2019). Link: https://arxiv.org/abs/1905.04651

## Website
Check out the website at: https://passport.ccs.neu.edu

## User Guide
https://docs.google.com/document/d/1rw15Egq2bvc6R6B6WLXZ464R5s2nZrJRLn4rJPFEWIM


## Pre-setup Instructions
Things that you'll need:

* Databases from Maxmind, IP2Location, and DBIP. Look at `geoloc-server/config.py` for the names of the files (containing databases) and `geoloc-server/data` folder for minor modifications to the database files downloaded from their websites.
* API Key for EurekAPI
* API Key for IPInfo.io
* API Key for Google Maps API
* API Key for revtr.ccs.neu.edu
* A prayer that ddec.caida.org is working

## Setup Instructions
* Move all scripts in the `setup` directory to current directory.
* Run `third_party.sh` (or `third_party_centos.sh` depending on your OS)
* Run `mysql_setup_centos.sh` (for centos or similar command for your OS)
* Run `create_directories.sh`
* Create and run a virtual environment
* `pip install -r requirements.txt` in the virtual environment.
* Change passwords in `geoloc-server/config.txt`
* Create a MySQL database `dbgeoroute` with `utf-8 default coalition`.
* Populate some of the database tables with hints information using the `database_tables.tar.bz2` file.
* In the `geoloc-server` folder, run `sudo python manage.py syncdb`
* You're all set.

### Setup Instructions for Production Server (Online System)
#### Local Server
* Activate the virtual environment.
* Modify `config.py` in the `geoloc-server` folder, set `WEB_DEBUG_MODE` to `True`
* Run `python passport.py` in the `geoloc-server` folder.

#### Production Server
* Install nginx.
* Copy contents from `nginx.conf` to `/etc/nginx/nginx.conf`. Modify `/etc/nginx/nginx.conf` as per production requirements (see `geoloc-server/config.py` file for the server port).
* Make sure port 80 and 443 are externally visible.
* Run `sudo service nginx start` (or `sudo service nginx reload`)
* Follow the tutorial following tutorial for setting up HTTPS using Let's Encrypt: `https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-centos-7`
* Activate the virtual environment.
* Modify `config.py` in the `geoloc-server` folder, set `WEB_DEBUG_MODE` to `False`
* Run `uwsgi --reload-on-exception --enable-threads --python passport.py  2>&1 > /dev/null &` in the `geoloc-server` folder
* **Note:** The above command is known to have runtime problems since we have multiple processes running, so run `python passport.py 2>&1 > /dev/null &` in the `geoloc-server` folder. If you can get the system to run under `uwsgi`, go ahead.


##### Stopping the Production Server
* Run `pkill -9 uwsgi`. Note: This command will kill all the processes with name uwsgi. Run it if you're sure only Passport system is using uwsgi.

##### Opening Port 80
* Run `sudo apt-get install iptables` (or `sudo yum install iptables` on CentOS)
* Run `sudo iptables -A INPUT -p tcp -m tcp --dport 80 -j ACCEPT`
* Run `sudo /etc/init.d/iptables save` or `sudo /sbin/iptables-save` (depends on OS)
* On CentOS `sudo firewall-cmd --zone=public --add-port=80/tcp --permanent`
* On CentOS `sudo firewall-cmd --reload`
* On CentOS/SELinux `sudo setsebool -P httpd_can_network_connect 1` if nginx cannot connect to the client port.

##### Instructions on CentOS Restart/MySQL Database and Nginx Issues on CentOS
* Try the following commands:
    * `sudo mkdir /var/log/mysql`
    * `sudo mkdir /var/run/mysqld`
    * `sudo chown mysql:mysql /var/run/mysqld`
    * `sudo /sbin/service mysqld start`
    * `sudo service nginx start`
* Run `nano /var/log/mysqld.log`, parse through the log file and find out the issue (and resolve it).
* This link might help: https://stackoverflow.com/questions/34113689/job-for-mysqld-service-failed-in-centos-7

#### Database Hints Tables
* The table `georoute_hints_world_cities_pop_maxmind_geolite` has been polutated from Maxmind Free World Cities Database. It's available at:
https://www.maxmind.com/en/free-world-cities-database. It can be shared under OPEN DATA LICENSE: http://download.maxmind.com/download/geoip/database/LICENSE_WC.txt

* The table `georoute_hints_as_info` has been created using CAIDA's AS Rank Info (asrank.caida.org).
* The table `georoute_ddec_hostname` has been created using CAIDA's DDEC hostname resolution system (ddec.caida.org).
