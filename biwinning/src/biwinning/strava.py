import urllib2
import peewee
import simplejson
import os
from biwinning.models import Ride, Club, Athlete, ClubAthlete

###
# API load methods
###

def load_json(url):
    f = urllib2.urlopen(url)
    return simplejson.loads(f.read())


def refresh_club(club_id):
    data = load_json('http://app.strava.com/api/v1/clubs/%s/members' % club_id)
    club = Club.get_or_create(strava_id=club_id)
    club.values_from_dict(data['club'], {'id': 'strava_id'})
    club.save()

    for name,athlete_id in [(m['name'].encode('utf-8', 'ignore'), m['id']) for m in data['members']]:
        athlete = Athlete.get_or_create(strava_id=athlete_id)
        if not athlete.matches_dict({'name': name}):
            athlete.values_from_dict({'name': name})
            athlete.save()

        club_athlete = ClubAthlete.get_or_create(club=club, athlete=athlete)
        club_athlete.save()

def load_club_members(club_id, refresh=False):
    count = Club.select(Club.strava_id==club_id).count()

    if refresh or not count:
        refresh_club(club_id)

    club = Club.get(strava_id=club_id)

    return club.name, dict([(a.name.encode('utf-8', 'ignore'), a.strava_id) for a in club.athletes])


def load_rides(id, offset=0, startId=0):
    rides = load_json("http://app.strava.com/api/v1/rides?athleteId=%s&offset=%s&startId=%s" % (id, offset, startId))[
            'rides']
    for ride in rides:
        if ride['id'] is not startId:
            yield ride
    if len(rides) >= 50:
        for ride in load_rides(id, offset + 50, startId=startId):
            if ride['id'] is not startId:
                yield ride


###
# Data methods
##

def get_ride(id):
    try:
        return Ride.get(strava_id=id)
    except:
        ride = Ride().populate_from_dict(load_json("http://www.strava.com/api/v1/rides/%s" % id)['ride'])
        ride.save()
        return ride


def get_rides_for_athlete(athlete, refresh):
    startId = str(athlete.max_ride_id)
    if refresh:
        new_rides = [get_ride(item['id']) for item in load_rides(athlete.strava_id, 0, startId)]
        [r.save() for r in new_rides]

    return athlete.rides


def get_rides_for_user(strava_id, refresh):
    """
    Check for new rides only, if cache is enabled, otherwise reload the entire list.
    """
    athlete = Athlete.get_or_create(strava_id=strava_id)
    if not athlete.id:
        athlete.save()
    return get_rides_for_athlete(athlete, refresh)


def get_rides(club_id, refresh=False):
    rides = {}

    club = Club.get(strava_id=club_id)
    for athlete in club.athletes:
        rides[athlete.name.encode('utf-8', 'ignore')] = get_rides_for_athlete(athlete, refresh)
    return rides
