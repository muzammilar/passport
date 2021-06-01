# -*- coding: utf-8 -*-
"""

    ppstore.models
    ~~~~~~~~~~~~~~~~~

    A module containing all the Django models. This module contains all the
    Django database Models used by the Passport system. Any new model can be
    added and the database can be updated (see Django docs)




    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

# this file has been copied from the website portion.
import math
###remove-me-later-muz###from django.db import models

"""
class Host(models.Model):
    ip = models.GenericIPAddressField(unique=True, db_index=True, null=True)
    hostname = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    unknown_neighbors = models.IntegerField(null=True)
    to_update = models.BooleanField()
    # candidates (many-to-many with locations)
    # neighbors (one-to-many with HostPointer)
    # dependants (one-to-many with HostPointer)

    def __unicode__(self):
        return self.hostname + " " + self.ip


class HostPointer(models.Model):
    # One Host have multiple HostPointers
    host = models.ForeignKey(Host, db_index=True, null=True)

    ip = models.GenericIPAddressField(db_index=True, null=True)
    drtt = models.FloatField(null=True)
    is_neighbor = models.BooleanField()
    is_dependent = models.BooleanField()

class Location(models.Model):
    # One Host can have multiple locations
    host = models.ForeignKey(Host, db_index=True, null=True)

    data_source = models.CharField(db_index=True, max_length=255)
    longitude = models.FloatField(db_index=True, null=True)
    latitude = models.FloatField(db_index=True, null=True)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    error = models.FloatField(null=True)
    merged = models.BooleanField()
    timestamp_ms = models.BigIntegerField(db_index=True, null=True)

    def __sub__(self, other):
        ret = 0
        ret += math.pow(self.longitude - other.longitude, 2)
        ret += math.pow(self.latitude - other.latitude, 2)
        ret += abs(self.error - other.error) / math.pi
        # Normalize error as circle's radius
        # shengy TODO: since we changed circles to boxes, will this be a
        # problem?
        return ret

    # def __unicode__(self):
    #     return self.host.ip + " " + self.data_source


class Candidate(models.Model):
    host = models.ForeignKey(Host, db_index=True, null=True)
    location = models.ForeignKey('Location', db_index=True, null=True)

    def __unicode__(self):
        return str(self.host.id) + " " + str(self.location.id)




class ClientRun(models.Model):
    start_time = models.BigIntegerField(null=True)
    end_time = models.BigIntegerField(null=True)
    ip = models.GenericIPAddressField(db_index=True, null=True)
    country = models.CharField(max_length=255)

    def __unicode__(self):
        return str(self.start_time) + " " + str(self.end_time)


class TraceRoute(models.Model):
    # One client run can have multiple TraceRoutes
    client_run = models.ForeignKey(ClientRun, db_index=True, null=True)

    dst_addr = models.GenericIPAddressField(null=True)
    dst_name = models.CharField(max_length=255)
    src_addr = models.GenericIPAddressField(null=True)
    made_it = models.BooleanField()

    timestamp = models.BigIntegerField(null=True)

    def __unicode__(self):
        return self.dst_name + " (" + str(self.dst_addr) + ")"


class TraceRouteResult(models.Model):
    # One TraceRoute have multiple TraceRouteResults
    traceroute = models.ForeignKey(TraceRoute, db_index=True, null=True)

    hop = models.SmallIntegerField(null=True)
    rtt0 = models.FloatField(null=True)
    rtt1 = models.FloatField(null=True)
    rtt2 = models.FloatField(null=True)
    router_ip = models.GenericIPAddressField(db_index=True, null=True)

    def __unicode__(self):
        return str(self.router_ip) + ' hop: ' + str(self.hop)


class Hint(models.Model):
    ip = models.GenericIPAddressField(db_index=True, null=True)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    data_source = models.CharField(max_length=255)

    def __unicode__(self):
        return str(self.ip) + ' name: ' + self.name
"""

class Hints_DDEC_Location_Lat_Long(models.Model):
    location = models.CharField(max_length=255, db_index=True, primary_key=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    city = models.CharField(max_length=255, db_index=True)
    region = models.CharField(max_length=255, db_index=True)
    country = models.CharField(max_length=255, db_index=True)
    ne_lat = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    ne_lon = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    sw_lat = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    sw_lon = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)

    def __unicode__(self):
        return str(self.location) + ' country: ' + self.country


class DDEC_Hostname(models.Model):
    hostname = models.CharField(max_length=255, db_index=True)
    location = models.CharField(max_length=255, db_index=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)

    def __unicode__(self):
        return str(self.hostname) + ' location: ' + str(self.location)


class Hints_country_codes(models.Model):
    country = models.CharField(max_length=255, primary_key=True)
    iso_two_code = models.CharField(max_length=2, db_index=True)
    iso_three_code = models.CharField(max_length=3, db_index=True)
    continent = models.CharField(max_length=45, db_index=True)

    def __unicode__(self):
        return str(self.iso_two_code) + ' country: ' + self.country


class Hints_state_codes(models.Model):
    state = models.CharField(max_length=255, primary_key=True)
    ansi = models.CharField(max_length=2, db_index=True)
    uscg = models.CharField(max_length=2, db_index=True)

    def __unicode__(self):
        return str(self.ansi) + ' country: ' + self.state

class Hints_country_lat_long(models.Model):
    country = models.CharField(max_length=255, primary_key=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True)

    def __unicode__(self):
        return str(self.country) + ' lat: ' + str(self.latitude) +  ' lon: '+  str(self.longitude)


class Hints_world_cities_pop_maxmind_geolite(models.Model):
    country = models.CharField(max_length=255, db_index=True)
    city = models.CharField(max_length=255, db_index=True)
    accentcity = models.CharField(max_length=255, db_index=True)
    region = models.CharField(max_length=255, db_index=True)
    population = models.IntegerField(db_index=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10, db_index=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10, db_index=True)

    def __unicode__(self):
        return str(self.city) + ', ' + str(self.region) + ', ' + str(self.country) + ' lat: '+ str(self.latitude) +  ' lon: '+  str(self.longitude)


class Hints_IXP_MARMOT_RIPE(models.Model):
    entery_id = models.IntegerField(primary_key=True)
    ip = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(db_index=True)
    georesult = models.CharField(max_length=255, db_index=True)
    confidence = models.IntegerField(db_index=True)
    user = models.IntegerField(db_index=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    canonical_georesult = models.CharField(max_length=255, db_index=True)
    country = models.CharField(max_length=255, db_index=True)
    city = models.CharField(max_length=255, db_index=True)
    region = models.CharField(max_length=255, db_index=True)
    ne_lat = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    ne_lon = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    sw_lat = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    sw_lon = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)

    def __unicode__(self):
        return str(self.ip) + ' country: ' + str(self.country)


class Hints_AS_INFO(models.Model):
    as_rank = models.IntegerField(db_index=True, null=True)
    as_number = models.IntegerField(primary_key=True)
    as_name = models.CharField(max_length=255, db_index=True, null=True)
    org_name = models.CharField(max_length=255, db_index=True, null=True)
    num_as_in_org = models.IntegerField(db_index=True, null=True)
    num_ipv4_prefix_in_org = models.IntegerField(db_index=True, null=True)
    num_ipv4_ip_in_org = models.IntegerField(db_index=True, null=True)

    def __unicode__(self):
        return 'AS INFO:: ' + str(self.as_number) + ' org: ' + str(self.org_name)


class Loc_Source_DB_IP(models.Model):
    ip = models.CharField(max_length=39, primary_key=True)
    country = models.CharField(max_length=145, db_index=True, null=True)
    region = models.CharField(max_length=145, db_index=True, null=True)
    city = models.CharField(max_length=145, db_index=True, null=True)
    isp = models.CharField(max_length=145, db_index=True, null=True)
    timezone = models.CharField(max_length=145, db_index=True, null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    organization = models.CharField(max_length=255, db_index=True, null=True)
    Time = models.DateTimeField(null=True)

    def __unicode__(self):
        return 'IP Source:: ' + str(self.ip) + ' from DB-IP'


class GROUND_TRUTH_OPENIPMAP(models.Model):
    ip = models.CharField(max_length=39, primary_key=True)
    country = models.CharField(max_length=145, db_index=True, null=True)
    region = models.CharField(max_length=145, db_index=True, null=True)
    city = models.CharField(max_length=145, db_index=True, null=True)
    hostname = models.CharField(max_length=255, db_index=True, null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    updated_at = models.DateTimeField(null=True)
    rank = models.IntegerField(db_index=True, null=True)

    def __unicode__(self):
        return 'Open IP Map:: ' + str(self.ip)


class Loc_Source_EUREKAPI(models.Model):
    ip = models.CharField(max_length=39, primary_key=True)
    country = models.CharField(max_length=145, db_index=True, null=True)
    region = models.CharField(max_length=145, db_index=True, null=True)
    city = models.CharField(max_length=145, db_index=True, null=True)
    isp = models.CharField(max_length=145, db_index=True, null=True)
    continent = models.CharField(max_length=145, db_index=True, null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    organization = models.CharField(max_length=255, db_index=True, null=True)
    Time = models.DateTimeField(null=True)

    def __unicode__(self):
        return 'IP Source:: ' + str(self.ip) + ' from EurekAPI'


class Loc_Source_IP2LOCATION(models.Model):
    ip = models.CharField(max_length=39, primary_key=True)
    country = models.CharField(max_length=145, db_index=True, null=True)
    region = models.CharField(max_length=145, db_index=True, null=True)
    city = models.CharField(max_length=145, db_index=True, null=True)
    isp = models.CharField(max_length=145, db_index=True, null=True)
    Time = models.DateTimeField(null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)

    def __unicode__(self):
        return 'IP Source:: ' + str(self.ip) + ' from IP2LOCATION'


class Loc_Source_IPINFO_IO(models.Model):
    ip = models.CharField(max_length=39, primary_key=True)
    country = models.CharField(max_length=145, db_index=True, null=True)
    region = models.CharField(max_length=145, db_index=True, null=True)
    city = models.CharField(max_length=145, db_index=True, null=True)
    postal_code = models.IntegerField(db_index=True, null=True)
    organization = models.CharField(max_length=145, db_index=True, null=True)
    hostname = models.CharField(max_length=255, db_index=True, null=True)
    location = models.CharField(max_length=145, db_index=True, null=True)
    Time = models.DateTimeField(null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)

    def __unicode__(self):
        return 'IP Source:: ' + str(self.ip) + ' from IPINFO.IO'


class Loc_Source_MAXMIND_GEOLITE_CITY(models.Model):
    ip = models.CharField(max_length=39, primary_key=True)
    country = models.CharField(max_length=145, db_index=True, null=True)
    region = models.CharField(max_length=145, db_index=True, null=True)
    city = models.CharField(max_length=145, db_index=True, null=True)
    postal_code = models.IntegerField(db_index=True, null=True)
    area_code = models.IntegerField(db_index=True, null=True)
    Time = models.DateTimeField(null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)

    def __unicode__(self):
        return 'IP Source:: ' + str(self.ip) + ' from IPINFO.IO'


class IP_WHOIS_INFORMATION(models.Model):
    ip = models.CharField(max_length=45, primary_key=True)
    asn = models.IntegerField(null=True)
    asn_cidr_bgp = models.CharField(max_length=45, db_index=True, null=True)
    asn_country = models.CharField(max_length=45, db_index=True, null=True)
    asn_registry = models.CharField(max_length=45, db_index=True, null=True)
    isp = models.CharField(max_length=145, db_index=True, null=True)
    isp_country = models.CharField(max_length=145, db_index=True, null=True)
    isp_city = models.CharField(max_length=145, db_index=True, null=True)
    isp_region = models.CharField(max_length=145, db_index=True, null=True)

    def __unicode__(self):
        return 'WhoIS information:: ' + str(self.ip)


class CLASSIFIER_DATA(models.Model):
    ip = models.CharField(max_length=45)
    classifier = models.CharField(max_length=145)
    predictedcountry = models.CharField(max_length=145, db_index=True,
        null=True)

    def __unicode__(self):
        return 'Classifier: ' + str(self.ip)


class SYSTEM_PREDICTIONS(models.Model):
    ip = models.CharField(max_length=45, db_index=True)
    source = models.CharField(max_length=145, db_index=True)
    country = models.CharField(max_length=145, db_index=True)
    source_probability = models.DecimalField(max_digits=15, decimal_places=10,
         db_index=True, null=True)

    def __unicode__(self):
        return 'System Prediction: ' + str(self.ip)


class CLASSIFIER_DATA_TRAIN(models.Model):
    ip = models.CharField(max_length=45, primary_key=True)
    asn = models.IntegerField(null=True)
    asn_cidr_bgp = models.CharField(max_length=45, db_index=True, null=True)
    asn_registry = models.CharField(max_length=45, db_index=True, null=True)
    isp = models.CharField(max_length=255, db_index=True, null=True)
    isp_city = models.CharField(max_length=145, db_index=True, null=True)
    isp_region = models.CharField(max_length=145, db_index=True, null=True)
    hostname = models.CharField(max_length=255,null=True)
    DDECcountry = models.CharField(max_length=145, db_index=True, null=True)
    AScountry = models.CharField(max_length=45, db_index=True, null=True)
    ISPcountry = models.CharField(max_length=145, db_index=True, null=True)
    db_ip_country = models.CharField(max_length=145, db_index=True, null=True)
    eurekapi_country = models.CharField(max_length=145, db_index=True, null=True)
    ip2location_country = models.CharField(max_length=145, db_index=True, null=True)
    ipinfo_country = models.CharField(max_length=145, db_index=True, null=True)
    maxmind_country = models.CharField(max_length=145, db_index=True, null=True)
    as_name = models.CharField(max_length=255, db_index=True, null=True)
    num_as_in_org = models.IntegerField(db_index=True, null=True)
    num_ipv4_prefix_in_org = models.IntegerField(db_index=True, null=True)
    num_ipv4_ip_in_org = models.IntegerField(db_index=True, null=True)
    realcountry = models.CharField(max_length=145, db_index=True)

    def __unicode__(self):
        return 'Classifier-train IP: ' + self.ip

class CLASSIFIER_DATA_TRAIN_GROUND(models.Model):
    ip = models.CharField(max_length=45, primary_key=True)
    asn = models.IntegerField(null=True)
    asn_cidr_bgp = models.CharField(max_length=45, db_index=True, null=True)
    asn_registry = models.CharField(max_length=45, db_index=True, null=True)
    isp = models.CharField(max_length=255, db_index=True, null=True)
    isp_city = models.CharField(max_length=145, db_index=True, null=True)
    isp_region = models.CharField(max_length=145, db_index=True, null=True)
    hostname = models.CharField(max_length=255,null=True)
    DDECcountry = models.CharField(max_length=145, db_index=True, null=True)
    AScountry = models.CharField(max_length=45, db_index=True, null=True)
    ISPcountry = models.CharField(max_length=145, db_index=True, null=True)
    db_ip_country = models.CharField(max_length=145, db_index=True, null=True)
    eurekapi_country = models.CharField(max_length=145, db_index=True, null=True)
    ip2location_country = models.CharField(max_length=145, db_index=True, null=True)
    ipinfo_country = models.CharField(max_length=145, db_index=True, null=True)
    maxmind_country = models.CharField(max_length=145, db_index=True, null=True)
    as_name = models.CharField(max_length=255, db_index=True, null=True)
    num_as_in_org = models.IntegerField(db_index=True, null=True)
    num_ipv4_prefix_in_org = models.IntegerField(db_index=True, null=True)
    num_ipv4_ip_in_org = models.IntegerField(db_index=True, null=True)
    realcountry = models.CharField(max_length=145, db_index=True)

    def __unicode__(self):
        return 'Classifier-train-ground IP: ' + self.ip

class CLASSIFIER_DATA_TRAIN_OPENIPMAP(models.Model):
    ip = models.CharField(max_length=45, primary_key=True)
    asn = models.IntegerField(null=True)
    asn_cidr_bgp = models.CharField(max_length=45, db_index=True, null=True)
    asn_registry = models.CharField(max_length=45, db_index=True, null=True)
    isp = models.CharField(max_length=255, db_index=True, null=True)
    isp_city = models.CharField(max_length=145, db_index=True, null=True)
    isp_region = models.CharField(max_length=145, db_index=True, null=True)
    hostname = models.CharField(max_length=255,null=True)
    DDECcountry = models.CharField(max_length=145, db_index=True, null=True)
    AScountry = models.CharField(max_length=45, db_index=True, null=True)
    ISPcountry = models.CharField(max_length=145, db_index=True, null=True)
    db_ip_country = models.CharField(max_length=145, db_index=True, null=True)
    eurekapi_country = models.CharField(max_length=145, db_index=True, null=True)
    ip2location_country = models.CharField(max_length=145, db_index=True, null=True)
    ipinfo_country = models.CharField(max_length=145, db_index=True, null=True)
    maxmind_country = models.CharField(max_length=145, db_index=True, null=True)
    as_name = models.CharField(max_length=255, db_index=True, null=True)
    num_as_in_org = models.IntegerField(db_index=True, null=True)
    num_ipv4_prefix_in_org = models.IntegerField(db_index=True, null=True)
    num_ipv4_ip_in_org = models.IntegerField(db_index=True, null=True)
    realcountry = models.CharField(max_length=145, db_index=True)

    def __unicode__(self):
        return 'Classifier-train-openipmap IP: ' + self.ip
