import urllib2
import itertools
import simplejson
import datetime
import re
import pickle
import os
import sys
from dateutil.relativedelta import relativedelta
from collections import deque
from threading import Thread



###
# Utils
###

parse_date = lambda d: datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")

first_name = lambda s: s.split()[0]


def convert(name):
    """Camel case to underscore. veryNice => very_nice
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


###
# Disk-cache methods
###

def cache_store(obj, id=None):
    if not os.path.exists('./data/'):
        os.makedirs('./data/')
    key = "%s-%s" % (obj.__class__.__name__, id or obj.id)
    output = open('data/%s.pkl' % key, 'wb')
    pickle.dump(obj, output)
    output.close()
    return obj


def cache_get(cls, id):
    key = "%s-%s" % (cls.__name__, id)
    filename = 'data/%s.pkl' % key
    if os.path.exists(filename):
        input = open(filename, 'rb')
        return pickle.load(input)
    return None


###
# Models
###

class ClubRides(dict):
    pass


class UserRides(deque):
    def extendleft(self, other):
        for item in other:
            self.appendleft(item)


class Club(dict):
    id = 'gv'


class Ride(object):
    description = None
    start_date = None
    name = None
    distance = None
    athlete = None
    maximum_speed = None
    commute = None
    moving_time = None
    elapsed_time = None
    bike = None
    elevation_gain = None
    trainer = None
    average_speed = None
    start_date_local = None
    average_watts = None
    id = None
    time_zone_offset = None
    location = None

    @classmethod
    def from_dict(cls, d):
        instance = Ride()
        for k, v in [(convert(k), v) for k, v in d.items() if hasattr(instance, convert(k))]:
            setattr(instance, k, 'date' in k and parse_date(v) or v)
        return instance

    @property
    def is_this_week(self):
        return self.start_date.isocalendar()[:2] == datetime.datetime.today().isocalendar()[:2]

    @property
    def week_id(self):
        return "%s-%s" % self.start_date.isocalendar()[:2]

    @property
    def is_last_week(self):
        last_week = (datetime.datetime.today() + datetime.timedelta(days=-7)).isocalendar()
        return self.start_date.isocalendar()[:2] == last_week[:2]

    @property
    def is_this_month(self):
        today = datetime.datetime.today()
        year_month = lambda d: (d.year, d.month)
        return year_month(self.start_date) == year_month(today)

    @property
    def is_last_month(self):
        last_month = (datetime.datetime.today() + relativedelta(months=-1))
        year_month = lambda d: (d.year, d.month)
        return year_month(self.start_date) == year_month(last_month)

    @property
    def is_last_28_days(self):
        d = datetime.datetime.today()
        shift = datetime.timedelta(days=-28, hours=-d.hour, minutes=-d.minute, seconds=d.second,
            microseconds=-d.microsecond)
        relative_date = d + shift
        return self.start_date >= relative_date

    @property
    def is_last_7_days(self):
        d = datetime.datetime.today()
        shift = datetime.timedelta(days=-7, hours=-d.hour, minutes=-d.minute, seconds=d.second,
            microseconds=-d.microsecond)
        relative_date = d + shift
        return self.start_date >= relative_date

    @property
    def is_this_year(self):
        return self.start_date.isocalendar()[0] == datetime.datetime.today().isocalendar()[0]

    def __repr__(self):
        return "<Ride %s:%s>" % (self.id, self.start_date)


###
# API load methods
###

def load_json(url):
    f = urllib2.urlopen(url)
    return simplejson.loads(f.read())


def load_club_members(club_id, use_cache=True):
    if use_cache and cache_get(Club, 'gv'):
        club = cache_get(Club, 'gv')
    else:
        club = load_json('http://app.strava.com/api/v1/clubs/%s/members' % club_id)
        cache_store(Club(club))
    return club['club']['name'].encode('utf-8', 'ignore'),\
           dict(map(lambda m: (m['name'].encode('utf-8', 'ignore'), m['id']), club['members']))


def load_rides(id, offset=0, startId=0):
    rides = load_json("http://app.strava.com/api/v1/rides?athleteId=%s&offset=%s&startId=%s" % (id, offset, startId))[
            'rides']
    for ride in rides:
        yield ride
    if len(rides) >= 50:
        for ride in load_rides(id, offset + 50, startId=startId):
            yield ride


###
# Data methods
##

def get_ride(id):
    if cache_get(Ride, id):
        return cache_get(Ride, id)
    return cache_store(Ride.from_dict(load_json("http://www.strava.com/api/v1/rides/%s" % id)['ride']))


def get_rides_for_user(id, use_cache):
    """
    Check for new rides only, if cache is enabled, otherwise reload the entire list.
    """
    startId = max([0] + map(lambda x: x.id, cache_get(UserRides, id) or [])) if use_cache else 0
    rides_list = load_rides(id, 1 if startId else 0, startId)

    rides = cache_get(UserRides, id) if use_cache else UserRides()
    rides.extendleft(map(lambda item: get_ride(item['id']), rides_list))

    return cache_store(rides, id)


def get_rides(user_map, use_cache=True):
    rides = ClubRides()

    for user, id in [(k, user_map[k]) for k in sorted(user_map)]:
        print "Loading rides for %s" % (first_name(user), )
        rides[user] = get_rides_for_user(id, use_cache)

    return rides

def get_rides_from_cache(user_map):
    return dict((user, cache_get(UserRides, id)) for (user,id) in [(k, user_map[k]) for k in sorted(user_map)])

def get_rides_threaded(user_map, use_cache=True):
    rides = {}
    threads = []

    # Create threads
    for user, id in [(k, user_map[k]) for k in sorted(user_map)]:
        print "Loading rides for %s" % (first_name(user), )
        rides[user] = UserRides()
        threads.append(Thread(target=lambda q, i, c: q.extend(get_rides_for_user(i, c)), args=(rides[user], id, use_cache)))

    # Start all
    [t.start() for t in threads]

    # Wait for all
    [t.join() for t in threads]

    return rides

