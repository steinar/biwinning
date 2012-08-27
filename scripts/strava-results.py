import urllib
import itertools
import simplejson
import datetime
from dateutil.relativedelta import relativedelta
import re
import pickle
import os
import sys

CLUB_ID = 7459

results = (
    ('All time (rides)', lambda user, rides: len(rides[user])),
    ('This year (km)', lambda user, rides: km(sum(map(lambda r: r.distance,  filter(lambda r: r.is_this_year, rides[user]))))),
    ('Last month (km)', lambda user, rides: km(sum(map(lambda r: r.distance,  filter(lambda r: r.is_last_month, rides[user]))))),
    ('Last week (km)', lambda user, rides: km(sum(map(lambda r: r.distance,  filter(lambda r: r.is_last_week, rides[user]))))),
    ('This month (km)', lambda user, rides: km(sum(map(lambda r: r.distance,  filter(lambda r: r.is_this_month, rides[user]))))),
    ('This week (km)', lambda user, rides: km(sum(map(lambda r: r.distance,  filter(lambda r: r.is_this_week, rides[user]))))),
    ('Last 28 days (km)', lambda user, rides: km(sum(map(lambda r: r.distance,  filter(lambda r: r.is_last_28_days, rides[user]))))),
    ('Last 7 days (km)', lambda user, rides: km(sum(map(lambda r: r.distance,  filter(lambda r: r.is_last_7_days, rides[user]))))),
)


def convert(name):
    """Camel case to underscore. veryNice => very_nice
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


parse_date = lambda d: datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")
stretch = lambda s,l: (str(s)[:l] + " "* (l-len(str(s).decode("utf-8"))))
stretch_r = lambda s,l: (" "* (l-len(str(s).decode("utf-8")))+ str(s)[:l])
km = lambda n: "%skm" % round(n/1000.,1)
m = lambda n: "%s m" % round(n,1)
first_name = lambda s: s.split()[0]


def store(obj):
    if not os.path.exists('./data/'):
        os.makedirs('./data/')
    output = open('data/%s-%s.pkl' % (obj.__class__.__name__, obj.id) , 'wb')
    pickle.dump(obj, output)
    output.close()
    return obj


def get(cls, id):
    filename = 'data/%s-%s.pkl' % (cls.__name__, id)
    if os.path.exists(filename):
        input = open(filename , 'rb')
        return pickle.  load(input)
    return None

class Rides(dict):
    pass

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
        for k,v in [(convert(k),v) for k,v in d.items() if hasattr(instance, convert(k))]:
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
        last_week = (datetime.datetime.today()+datetime.timedelta(days=-7)).isocalendar()
        return self.start_date.isocalendar()[:2] == last_week[:2]

    @property
    def is_this_month(self):
        today = datetime.datetime.today()
        year_month = lambda d: (d.year, d.month)
        return year_month(self.start_date) == year_month(today)

    @property
    def is_last_month(self):
        last_month = (datetime.datetime.today()+relativedelta(months=-1))
        year_month = lambda d: (d.year, d.month)
        return year_month(self.start_date) == year_month(last_month)

    @property
    def is_last_28_days(self):
        d = datetime.datetime.today()
        shift = datetime.timedelta(days=-28, hours=-d.hour, minutes=-d.minute, seconds=d.second, microseconds=-d.microsecond)
        relative_date = d+shift
        return self.start_date >= relative_date

    @property
    def is_last_7_days(self):
        d = datetime.datetime.today()
        shift = datetime.timedelta(days=-7, hours=-d.hour, minutes=-d.minute, seconds=d.second, microseconds=-d.microsecond)
        relative_date = d+shift
        return self.start_date >= relative_date

    @property
    def is_this_year(self):
        return self.start_date.isocalendar()[0] == datetime.datetime.today().isocalendar()[0]

    def __repr__(self):
        return "<Ride %s:%s>" % (self.id, self.start_date)


def json(url):
    f = urllib.urlopen(url)
    return simplejson.loads(f.read())

def load_club_members(club_id, use_cache=True):
    if use_cache and get(Club, 'gv'):
        club = get(Club, 'gv')
    else:
        club = json('http://app.strava.com/api/v1/clubs/%s/members' % club_id)
        store(Club(club))
    return club['club']['name'].encode('utf-8', 'ignore'), \
           dict(map(lambda m: (m['name'].encode('utf-8', 'ignore'), m['id']), club['members']))

def load_rides(id, offset=0):
    rides = json("http://app.strava.com/api/v1/rides?athleteId=%s&offset=%s" % (id, offset))['rides']
    if (len(rides)-offset) == 50:
        rides = itertools.chain(rides, load_rides(id, offset+50))
    return rides



def get_ride(id):
    if get(Ride, id):
        return get(Ride, id)
    return store(Ride.from_dict(json("http://www.strava.com/api/v1/rides/%s" % id)['ride']))


def get_rides(user_map, use_cache=True):
    key = "-".join(user_map.keys())
    if use_cache and get(Rides, key):
        return get(Rides, key)
    rides = Rides()
    rides.id = key

    for user,id in [(k,user_map[k]) for k in sorted(user_map)]:
        print "Loading rides for %s" % (first_name(user), )
        rides[user] = map(lambda item: get_ride(item['id']), load_rides(id))
    return store(rides)


def generate_report():
    use_cache = len(sys.argv) == 1 or sys.argv[1] == reload

    if use_cache:
        print "Using local cache. Use 'reload' argument to fetch new rides."

    club_name, members = load_club_members(CLUB_ID, use_cache)

    print "Rides for club %s" % club_name

    rides = get_rides(members, use_cache)
    users = sorted(members.keys())

    weeks = set(map(lambda x: x.week_id, itertools.chain(*rides.values())))

    print stretch('', 22) + \
          " | ".join(map(lambda u: stretch_r(first_name(u), 10), users))

    print " "*22 + "-+-".join(["-"*10]*len(members))

    for name, fn in results:
        print stretch(name, 22) + \
              " | ".join(map(lambda u: stretch_r(fn(u, rides), 10), users))

    print " "*22 + "-+-".join(["-"*10]*len(members))
    print
    print stretch('', 22) +\
          " | ".join(map(lambda u: stretch_r(first_name(u), 10), users))
    print " "*22 + "-+-".join(["-"*10]*len(members))

    for week_id in sorted(weeks)[-5:]:
        week_distance_fn = lambda user, rides: sum(map(lambda r: r.distance,  filter(lambda r: r.week_id == week_id, rides[user])))
        dist = map(lambda u: week_distance_fn(u, rides), users)
        mark_max = lambda s,l: "*" if s == max(l) else ""
        print stretch(week_id, 22) +\
              " | ".join(map(lambda d: stretch_r(mark_max(d, dist) + km(d), 10), dist))

        elevation_fn = lambda user, rides: sum(map(lambda r: r.elevation_gain,  filter(lambda r: r.week_id == week_id, rides[user])))
        elev = map(lambda u: elevation_fn(u, rides), users)
        print stretch(week_id, 22) +\
              " | ".join(map(lambda e: stretch_r(mark_max(e, elev) + m(e), 10), elev))

        print " "*22 + "-+-".join(["-"*10]*len(members))


if __name__ == '__main__':
    generate_report()
