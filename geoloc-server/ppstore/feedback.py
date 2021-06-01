# -*- coding: utf-8 -*-
"""

    ppstore.feedback
    ~~~~~~

    This module has been developed to take an IP address and a set of  countries predicted by Speed of Light
    constraints, use this information to see if only one country is predicted. If
    only one country is predicted then gather information from all the geolocation
    sources and insert/update the ground truth label for that IP address. It either
    updates (if the IP address exists in ground truth) or adds a new entry for the
    IP address.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

###remove-me-later-muz###import settings as DJANOG_SETTINGS
import configs.system
from ppstore.models import CLASSIFIER_DATA_TRAIN
from ppstore.models import DDEC_Hostname
from ppstore.models import Hints_DDEC_Location_Lat_Long
from ppstore.models import IP_WHOIS_INFORMATION
from ppstore.models import Hints_AS_INFO
from ppstore.models import Loc_Source_DB_IP
from ppstore.models import Loc_Source_EUREKAPI
from ppstore.models import Loc_Source_IP2LOCATION
from ppstore.models import Loc_Source_IPINFO_IO
from ppstore.models import Loc_Source_MAXMIND_GEOLITE_CITY


#####################################################################
# remove feedback-rewrite
#####################################################################



#####################################################################
# add feedback
#####################################################################
def add_feedback_to_ground(ip_address, real_country_list, hst_nm = ''):
    if not configs.system.APPLY_FEEDBACK:
        return
    num_countries = len(real_country_list)
    if num_countries > configs.system.FEEDBACK_MAX_COUNTRIES:
        return
    # no countries.
    if num_countries == 0:
        return

    for real_cntry in real_country_list:
        dataset = CLASSIFIER_DATA_TRAIN.objects.filter(ip=ip_address,
            realcountry=real_cntry)
        # see if IP-real_country pair exists.
        if dataset.count() > 0:
            return
        # update if a copy exists
        dataset = CLASSIFIER_DATA_TRAIN.objects.filter(ip=ip_address)
        # see if IP exists exists.
        try:
            if dataset.count() > 0:
                #update the ip address real country tuple.if it already exists.
                training_instance = dataset[0]
                training_instance.realcountry=real_cntry                 
                training_instance.save()
                return 
        except:
            print "Couldn't update instance after feedback:", ip_address


        # add to training dataset.
        ip_str = ip_address
        #all_hsts = Host.objects.filter(ip=ip_str)
        #try:
        #    cur_hst = all_hsts[0]
        #    ip_str = cur_hst.ip
        #    hst_nm = cur_hst.hostname
        #except:
        #    hst_nm = ''
        try:
            host_objs = DDEC_Hostname.objects.filter(hostname=hst_nm)
            loc = host_objs[0].location
            x = Hints_DDEC_Location_Lat_Long.objects.filter(location=loc)
            ddeccountry = x.country
        except:
            ddeccountry = ''
        try:
            db_ipcountry = Loc_Source_DB_IP.objects.filter(ip=ip_str)[0].country
        except:
            db_ipcountry = ''
        try:
            ipinfocountry = Loc_Source_IPINFO_IO.objects.filter(ip=ip_str)[0].country
        except:
            ipinfocountry = ''
        try:
            eurekapicountry = Loc_Source_EUREKAPI.objects.filter(ip=ip_str)[0].country
        except:
            eurekapicountry = ''
        try:
            ip2locationcountry = Loc_Source_IP2LOCATION.objects.filter(ip=ip_str)[0].country
        except:
            ip2locationcountry = ''
        try:
            maxmindcountry = Loc_Source_MAXMIND_GEOLITE_CITY.objects.filter(ip=ip_str)[0].country
        except:
            maxmindcountry = ''
        asn_num = -1
        try:
            ip_object = IP_WHOIS_INFORMATION.objects.filter(ip=ip_str)[0]
            asn_num = ip_object.asn
            asn_cidr_bgp1 = ip_object.asn_cidr_bgp
            asn1 = ip_object.asn
            asn_registry1 = ip_object.asn_registry
            isp1 = ip_object.isp
            isp_city1 = ip_object.isp_city
            isp_region1 = ip_object.isp_region
            ISPCountry1 = ip_object.isp_country
            ASCountry1 = ip_object.asn_country
        except:
            asn_registry1 = ''
            isp1 = ''
            isp_city1 = ''
            isp_region1 = ''
            ISPCountry1 = ''
            ASCountry1 = ''
            asn1 = -1
            asn_cidr_bgp1 = ''
        as_name1 = ''
        num_as_in_org1 = -1
        num_ipv4_prefix_in_org1 = -1
        num_ipv4_ip_in_org1 = -1
        try:
            asn_object = Hints_AS_INFO.objects.filter(as_number=asn_num)[0]
            as_name1 = asn_object.as_name
            num_as_in_org1 = asn_object.num_as_in_org
            num_ipv4_prefix_in_org1 = asn_object.num_ipv4_prefix_in_org
            num_ipv4_ip_in_org1 = asn_object.num_ipv4_ip_in_org
        except:
            pass
        try:
            #update the ip address real country tuple.if it already exists.
            training_instance = CLASSIFIER_DATA_TRAIN(ip=ip_address,
                realcountry=real_cntry, DDECcountry=ddeccountry,
                db_ip_country=db_ipcountry, eurekapi_country=eurekapicountry,
                ip2location_country=ip2locationcountry,
                ipinfo_country=ipinfocountry,
                maxmind_country=maxmindcountry, asn=asn1,
                asn_registry=asn_registry1, hostname=hst_nm, isp=isp1,
                isp_region=isp_region1, ISPcountry=ISPCountry1,
                AScountry=ASCountry1, isp_city=isp_city1, as_name=as_name1,
                num_as_in_org=num_as_in_org1,
                num_ipv4_prefix_in_org=num_ipv4_prefix_in_org1,
                num_ipv4_ip_in_org=num_ipv4_ip_in_org1,
                asn_cidr_bgp=asn_cidr_bgp1)
            training_instance.save()
        except:
            #traceback.print_exc()
            print "Couldn't add instance after feedback:", ip_address

