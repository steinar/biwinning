import datetime
from peewee import fn
from biwinning.data import get_rides, get_athletes
from biwinning.models import Ride, Quantity
from biwinning.utils import monday

__author__ = 'steinar'

class Quantifier(object):
    unit = None
    max_strava_id = None

    def __init__(self):
        self.name = self.__class__.__name__

    def key(self, *args, **kwargs):
        """
        Key for individual quantity entry.
        """
        pass

    def fetch_data(self, max_strava_id=0):
        """
        Yield data for rides newer than max_strava_id.
        """
        pass

    def rebuild(self):
        """
        Rebuild local storage.
        """
        pass

    def update(self, *args, **kwargs):
        """
        Update with new data.
        """
        pass

    def add_ride(self, ride):
        pass

    def substract_ride(self, ride):
        pass

    def get_value(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        pass

    def all(self):
        pass



class AthleteDistanceByWeek(Quantifier):
    unit = 'km'

    def __init__(self, club):
        self.club = club
        self.data = {}
        super(AthleteDistanceByWeek, self).__init__()

    def rebuild(self):
        self.update(None)

    def key(self, week):
        return week

    def fetch_data(self, athlete=None, max_strava_id=0):
        query = (Ride
                 .select(
            Ride.athlete,
            Ride.week,
            fn.Max(Ride.strava_id).alias('max_strava_id'),
            fn.Sum(Ride.distance).alias('sum'),
            fn.Count().alias('count')))

        if max_strava_id:
            query = query.where(Ride.strava_id > max_strava_id)

        if athlete:
            query = query.where(Ride.athlete == athlete)

        query = query.group_by(Ride.athlete, Ride.week)

        for ride in query:
            yield ride.athlete, ride.week, ride.max_strava_id, ride.sum, ride.count

    def get(self, athlete, week_or_date):
        week = isinstance(week_or_date, datetime.date) and week_or_date.strftime("%Y-%W")
        return Quantity.get_or_create(class_name=self.name, athlete=athlete, key=self.key(week))

    def all(self):
        return Quantity.select().where(Quantity.class_name == self.name)

    def update(self, athlete):
        max_strava_id = athlete and Quantity.get_max_strava_id(athlete) or 0
        for athlete, week, max_strava_id, sum, count in self.fetch_data():
            Quantity.add_or_update(self.name, athlete, self.key(week), max_strava_id, sum, {'count': count})

