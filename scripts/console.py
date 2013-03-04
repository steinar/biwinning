#!/usr/bin/env python
import itertools
import datetime
import re
import sys
from biwinning import strava

CLUB_ID = 7459

###
# Presentation utils
###

results = (
    ('All time (rides)', lambda user, rides: rides[user].count()),
    ('This year (km)',
     lambda user, rides: km(sum(map(lambda r: r.distance, filter(lambda r: r.is_this_year, rides[user]))))),
    ('Last month (km)',
     lambda user, rides: km(sum(map(lambda r: r.distance, filter(lambda r: r.is_last_month, rides[user]))))),
    ('Last week (km)',
     lambda user, rides: km(sum(map(lambda r: r.distance, filter(lambda r: r.is_last_week, rides[user]))))),
    ('This month (km)',
     lambda user, rides: km(sum(map(lambda r: r.distance, filter(lambda r: r.is_this_month, rides[user]))))),
    ('This week (km)',
     lambda user, rides: km(sum(map(lambda r: r.distance, filter(lambda r: r.is_this_week, rides[user]))))),
    ('Last 28 days (km)',
     lambda user, rides: km(sum(map(lambda r: r.distance, filter(lambda r: r.is_last_28_days, rides[user]))))),
    ('Last 7 days (km)',
     lambda user, rides: km(sum(map(lambda r: r.distance, filter(lambda r: r.is_last_7_days, rides[user]))))),
    )


parse_date = lambda d: datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")

first_name = lambda s: s.split()[0]

stretch = lambda s, l: (str(s)[:l] + " " * (l - len(str(s).decode("utf-8"))))

stretch_r = lambda s, l: (" " * (l - len(str(s).decode("utf-8"))) + str(s)[:l])

km = lambda n: "%s km" % round(n / 1000., 1)

m = lambda n: "%s m" % round(n, 1)


###
# Console view
###

def generate_report(refresh=False):
    if not refresh:
        print "Using local cache. Use 'reload' argument to fetch new rides."

    club_name, members = strava.load_club_members(CLUB_ID, refresh)

    print "Rides for club %s" % club_name

    rides = strava.get_rides(CLUB_ID, refresh)
    users = sorted(members.keys())

    weeks = set(map(lambda x: x.week_id, itertools.chain(*rides.values())))

    print stretch('', 22) +\
          " | ".join(map(lambda u: stretch_r(first_name(u), 10), users))

    print " " * 22 + "-+-".join(["-" * 10] * len(members))

    for name, fn in results:
        print stretch(name, 22) +\
              " | ".join(map(lambda u: stretch_r(fn(u, rides), 10), users))

    print " " * 22 + "-+-".join(["-" * 10] * len(members))
    print
    print stretch('', 22) +\
          " | ".join(map(lambda u: stretch_r(first_name(u), 10), users))
    print " " * 22 + "-+-".join(["-" * 10] * len(members))

    for week_id in sorted(weeks)[-5:]:
        week_distance_fn = lambda user, rides: sum(
            map(lambda r: r.distance, filter(lambda r: r.week_id == week_id, rides[user])))
        dist = map(lambda u: week_distance_fn(u, rides), users)
        mark_max = lambda s, l: "*" if s == max(l) else ""
        elevation_fn = lambda user, rides: sum(
            map(lambda r: r.elevation_gain, filter(lambda r: r.week_id == week_id, rides[user])))
        elev = map(lambda u: elevation_fn(u, rides), users)
        print stretch("Week: %s    dist." % week_id, 22) +\
              " | ".join(map(lambda d: stretch_r(mark_max(d, dist) + km(d), 10), dist))
        print stretch_r("elev.", 22) +\
              " | ".join(map(lambda e: stretch_r(mark_max(e, elev) + m(e), 10), elev))

        print " " * 22 + "-+-".join(["-" * 10] * len(members))


if __name__ == '__main__':
    print "Available arguments: refresh"
    refresh = 'refresh' in sys.argv
    generate_report(refresh)

