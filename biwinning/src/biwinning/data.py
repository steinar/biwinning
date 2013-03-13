"""
Strava data methods.

First argument for all methods may be either a model object or strava id.

Fetch methods will request data from strava, create the corresponding model instances or update them.
Get methods fetch from strava only if the data is not found in the local database.

"""
import urllib2
import simplejson
from biwinning.config import db
from biwinning.models import Ride, Club, Athlete, ClubAthlete


def load_json(url):
    f = urllib2.urlopen(url)
    return simplejson.loads(f.read())


get_strava_id = lambda id_or_instance: isinstance(id_or_instance, db.Model) and id_or_instance.strava_id or id_or_instance


def strava_id(f):
    """
    Decorator which converts first argument to strava_id if model instance is provided.
    """
    def g(*args, **kwargs):
        return f(*((get_strava_id(args[0]),)+args[1:]), **kwargs)
    return g


@strava_id
def fetch_ride(ride):
    """
    Fetch and store a single ride from strava. Argument is either Ride instance or strava id.
    """
    data = load_json("http://www.strava.com/api/v1/rides/%s" % ride)['ride']
    instance = Ride.get_or_create(strava_id=ride).populate_from_dict(data)
    instance.save()
    return instance


@strava_id
def get_ride(ride):
    """
    Get ride from database or fetch from strava.
    """
    try:
        return Ride.get(strava_id=ride)
    except Ride.DoesNotExist:
        return fetch_ride(ride)


@strava_id
def fetch_athletes(club, data=None):
    """
    Fetch and store club members from strava.
    """
    data = data or load_json('http://app.strava.com/api/v1/clubs/%s/members' % club)

    def handle_member(m):
        name,athlete_id = (m['name'].encode('utf-8', 'ignore'), m['id'])
        athlete = Athlete.get_or_create(strava_id=athlete_id)

        if not athlete.matches_dict({'name': name}):
            athlete.values_from_dict({'name': name})
            athlete.save()

        club_athlete = ClubAthlete.get_or_create(club=club, athlete=athlete)
        club_athlete.save()

        return athlete

    return (handle_member(m) for m in data['members'])


@strava_id
def fetch_club(club):
    """
    Fetch and store club information and members from strava.
    """
    data = load_json('http://app.strava.com/api/v1/clubs/%s/members' % club)
    instance = Club.get_or_create(strava_id=club).values_from_dict(data['club'], {'id': 'strava_id'})
    instance.save()

    fetch_athletes(club, data=data)

    return instance


@strava_id
def get_club(club):
    """
    Get club information from database or strava.
    """
    try:
        return Club.get(strava_id=club)
    except Club.DoesNotExist:
        return fetch_club(club)


@strava_id
def get_athletes(club):
    """
    Get club members from database or strava.
    """
    instance = get_club(club)
    return instance.athletes


@strava_id
def fetch_athlete_ride_ids(athlete, offset=0, startId=0):
    """
    Fetch list of rides from strava. Optionally offset or startId may be provided.
    This method fetches 50 records at a time and returns a generator.
    """
    rides = load_json("http://app.strava.com/api/v1/rides?athleteId=%s&offset=%s&startId=%s" % \
                      (athlete, offset, startId))['rides']
    for ride_id in (r['id'] for r in rides):
        if not ride_id == startId:
            yield ride_id
    if len(rides) >= 50:
        for ride_id in fetch_athlete_ride_ids(athlete, offset + 50, startId=startId):
            if ride_id is not startId:
                yield ride_id


@strava_id
def fetch_athlete(athlete):
    """
    Fetch and store athlete information from strava. (API workaround).
    """
    return get_ride(fetch_athlete_ride_ids(athlete)[0]).athlete


@strava_id
def get_athlete(athlete):
    """
    Get athlete from database or strava.
    """
    try:
        return Athlete.get(strava_id=athlete)
    except Athlete.DoesNotExist:
        return fetch_athlete(athlete)


@strava_id
def fetch_new_rides(athlete):
    """
    Fetch and store athlete's rides from strava.
    Returns a generator.
    """
    instance = get_athlete(athlete)
    startId = instance.max_ride_id
    return (get_ride(id) for id in fetch_athlete_ride_ids(athlete, 0, startId))


@strava_id
def get_rides(athlete):
    """
    Get athlete's rides from database or strava.
    """
    return get_athlete(athlete).rides

@strava_id
def fetch_club_new_rides(club):
    for athlete in get_athletes(club):
        for ride in fetch_new_rides(athlete):
            yield ride

@strava_id
def fetch_club_new_rides_fair(club):
    """
    One ride per athlete in each iteration
    """
    generators = [fetch_new_rides(athlete) for athlete in fetch_athletes(club)]
    while len(generators) > 0:
        for gen in generators:
            try:
                yield next(gen)
            except StopIteration:
                generators.remove(gen)

@strava_id
def get_club_rides(club):
    for athlete in get_athletes(club):
        for ride in get_rides(athlete):
            yield ride


@strava_id
def get_orphan_rides(club):
    for athlete in get_athletes(club):
        db_ids = set(r.strava_id for r in Ride.select(Ride.strava_id).where(Ride.athlete == athlete))
        strava_ids = set(fetch_athlete_ride_ids(athlete))
        for id in db_ids.difference(strava_ids):
            yield Ride.get(Ride.strava_id == id)

#def authenticate():
#    data = {'email': 'hugi@steinar.is', 'password': 'azazo', 'agreed_to_terms': '1'}
#    fp = urllib2.urlopen('http://www.strava.com/api/v1/authentication/login',
#        "&".join("=".join([k,v]) for (k,v) in data.items()))
#    return simplejson.loads(fp.read())
#
#def get_authentication():
#    from biwinning.config import STRAVA_AUTH
#    if not STRAVA_AUTH:
#        STRAVA_AUTH.update(authenticate())
#    return STRAVA_AUTH

