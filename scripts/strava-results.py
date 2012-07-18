import urllib
import itertools
import simplejson
import datetime
from dateutil.relativedelta import relativedelta
import re
import pickle
import os

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
stretch = lambda s,l: (str(s)[:l] + " "* (l-len(str(s))))
stretch_r = lambda s,l: (" "* (l-len(str(s)))+ str(s)[:l])
km = lambda n: round(n/1000.,1)
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

def load_club_members(club_id):
    club = json('http://app.strava.com/api/v1/clubs/%s/members' % club_id)
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


def get_rides(user_map):
    rides = {}
    for user,id in [(k,user_map[k]) for k in sorted(user_map)]:
        print "Loading rides for %s" % (first_name(user), )
        rides[user] = map(lambda item: get_ride(item['id']), load_rides(id))
    return rides


def generate_report():
    club_name, members = load_club_members(CLUB_ID)

    print "Loading rides for club %s" % club_name

    rides = get_rides(members)
    users = sorted(members.keys())

    print stretch('', 22) + \
          " | ".join(map(lambda u: stretch_r(first_name(u), 10), users))

    print " "*22 + "-+-".join(["-"*10]*len(members))

    for name, fn in results:
        print stretch(name, 22) + \
              " | ".join(map(lambda u: stretch_r(fn(u, rides), 10), users))

    print " "*22 + "-+-".join(["-"*10]*len(members))


if __name__ == '__main__':
    generate_report()
