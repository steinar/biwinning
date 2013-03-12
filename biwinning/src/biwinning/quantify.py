import datetime
from peewee import fn
from biwinning.config import QUANTIFIERS
from biwinning.models import Ride, Quantity, Athlete, ClubAthlete

__author__ = 'steinar'

def quantifier(cls):
    QUANTIFIERS.append(cls)
    return cls

class Quantifier(object):
    unit = None
    max_strava_id = None

    def __init__(self):
        self.name = self.__class__.__name__


    def add_ride(self, ride):
        pass

    def subtract_ride(self, ride):
        pass

    def get_value(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        pass

    def all(self):
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

    def orphans(self):
        """
        Records where corresponding record is no longer found on strava.
        """
        pass

    def key(self, *args, **kwargs):
        """
        Key for individual quantity entry.
        """
        pass



@quantifier
class AthleteDistanceByWeek(Quantifier):
    unit = 'm'

    def __init__(self, club):
        self.club = club
        self.data = {}
        super(AthleteDistanceByWeek, self).__init__()

    def rebuild(self):
        self.update(None)

    def key(self, week_or_date):
        return isinstance(week_or_date, datetime.date) and week_or_date.strftime("%Y-%W") or week_or_date

    def base_query(self):
        return (Ride
                 .select(
            Ride.athlete,
            Ride.week,
            fn.Max(Ride.strava_id).alias('max_strava_id'),
            fn.Sum(Ride.distance).alias('distance'),
            fn.Sum(Ride.elevation_gain).alias('elevation_gain'),
            fn.Sum(Ride.moving_time).alias('moving_time'),
            fn.Count().alias('count'))
                 .join(Athlete).join(ClubAthlete)
                 .where(ClubAthlete.club == self.club)
            )

    def weeks_query(self):
        return (Ride
         .select(Ride.week)
         .join(Athlete).join(ClubAthlete)
         .where(ClubAthlete.club == self.club)
         .group_by(Ride.week)
        )

    def orphans(self):
        return Quantity.select().where(~(Quantity.key << self.weeks_query()))

    def fetch_data(self, athlete=None, max_strava_id=0):
        query = self.base_query()

        if max_strava_id:
            query = query.where(Ride.strava_id > max_strava_id)

        if athlete:
            query = query.where(Ride.athlete == athlete)

        query = query.group_by(Ride.athlete, Ride.week)

        for ride in query:
            yield ride.athlete, ride.week, ride.max_strava_id, ride.distance, ride.elevation_gain, ride.moving_time, ride.count

    def get(self, athlete, week_or_date):
        try:
            return Quantity.get(class_name=self.name, athlete=athlete, key=self.key(week_or_date))
        except Quantity.DoesNotExist:
            return Quantity(class_name=self.name, athlete=athlete, key=self.key(week_or_date), value=0)

    def all(self):
        return Quantity.select().where(Quantity.class_name == self.name)

    def update(self, athlete):
        max_strava_id = athlete and Quantity.get_max_strava_id(athlete) or 0
        for athlete, week, max_strava_id, distance, elevation_gain, moving_time, count in self.fetch_data():
            Quantity.add_or_update(self.name,
                athlete,
                self.key(week),
                max_strava_id,
                distance,
                {'count': count,
                 'elevation_gain': elevation_gain,
                 'moving_time': moving_time,
                 'distance': distance,
                 'average_speed': distance/moving_time
                }
            )

    def scoreboard(self, week_or_date):
        return (Quantity
                .select()
                .where(Quantity.key == self.key(week_or_date), Quantity.value > 0)
                .join(Athlete)
                .join(ClubAthlete)
                .where(ClubAthlete.club == self.club).order_by(Quantity.value.desc())
            )

    def add_ride(self, ride):
        q = self.get(ride.athlete, ride.start_date_local)
        q.value += ride.distance


        if not q.data:
            q.data = {}

        val = lambda k: q.data.get(k, 0)
        q.data.update({
            'count': val('count') + 1,
            'distance': val('distance') + ride.distance,
            'elevation_gain': val('elevation_gain') + ride.elevation_gain,
            'moving_time': val('moving_time') + ride.moving_time,
        })

        q.data['average_speed'] = val('distance')/val('moving_time')

        q.save()

        return q


    def subtract_ride(self, ride):
        q = self.get(ride.athlete, ride.start_date_local)
        q.value -= ride.distance

        d = lambda k: q.data.get(k, 0)

        q.data.update({
            'count': d('count') - 1,
            'distance': d('distance') - ride.distance,
            'elevation_gain': d('elevation_gain') - ride.elevation_gain,
            'moving_time': d('moving_time') - ride.moving_time,
        })

        q.data['average_speed'] = d('distance')/d('moving_time')

        q.save()

        return q

#
#@quantifier
#class ClubDistanceByWeek(AthleteDistanceByWeek):
#    unit = 'km'
#
#    def base_query(self):
#        return (Ride
#                .select(
#            Ride.week,
#            fn.Max(Ride.strava_id).alias('max_strava_id'),
#            fn.Sum(Ride.distance).alias('distance'),
#            fn.Sum(Ride.elevation_gain).alias('elevation_gain'),
#            fn.Sum(Ride.moving_time).alias('moving_time'),
#            fn.Count().alias('count'))
#                .join(Athlete).join(ClubAthlete)
#                .where(ClubAthlete.club == self.club)
#            )
#
#    def orphans(self):
#        return Quantity.select().where(~(Quantity.key << self.weeks_query()))
#
#    def fetch_data(self, athlete=None, max_strava_id=0):
#        query = self.base_query()
#
#        if max_strava_id:
#            query = query.where(Ride.strava_id > max_strava_id)
#
#        if athlete:
#            query = query.where(Ride.athlete == athlete)
#
#        query = query.group_by(Ride.athlete, Ride.week)
#
#        for ride in query:
#            yield ride.athlete, ride.week, ride.max_strava_id, ride.distance, ride.elevation_gain, ride.moving_time, ride.count
#
#    def get(self, athlete, week_or_date):
#        return Quantity.get_or_create(class_name=self.name, key=self.key(week_or_date))
#
#    def update(self, athlete):
#        max_strava_id = athlete and Quantity.get_max_strava_id(athlete) or 0
#        for athlete, week, max_strava_id, distance, elevation_gain, moving_time, count in self.fetch_data():
#            Quantity.add_or_update(self.name,
#                athlete,
#                self.key(week),
#                max_strava_id,
#                distance,
#                {'count': count,
#                 'elevation_gain': elevation_gain,
#                 'moving_time': moving_time,
#                 'distance': distance,
#                 'average_speed': distance/moving_time
#                }
#            )
#
#    def scoreboard(self, week_or_date):
#        return (Quantity
#                .select()
#                .where(Quantity.key == self.key(week_or_date), Quantity.value > 0)
#                .join(ClubAthlete)
#                .where(ClubAthlete.club == self.club).order_by(Quantity.value.desc())
#            )
#
#    def add_ride(self, ride):
#        q = self.get(ride.athlete, ride.start_date_local)
#        q.value += ride.distance
#
#        d = lambda k: q.data.get(k, 0)
#
#        q.data.update({
#            'count': d('count') + 1,
#            'distance': d('distance') + ride.distance,
#            'elevation_gain': d('elevation_gain') + ride.elevation_gain,
#            'moving_time': d('moving_time') + ride.moving_time,
#            })
#
#        q.data['average_speed'] = d('distance')/d('moving_time')
#
#        q.save()
#
#        return q
#
#
#    def subtract_ride(self, ride):
#        q = self.get(ride.athlete, ride.start_date_local)
#        q.value -= ride.distance
#
#        d = lambda k: q.data.get(k, 0)
#
#        q.data.update({
#            'count': d('count') - 1,
#            'distance': d('distance') - ride.distance,
#            'elevation_gain': d('elevation_gain') - ride.elevation_gain,
#            'moving_time': d('moving_time') - ride.moving_time,
#            })
#
#        q.data['average_speed'] = d('distance')/d('moving_time')
#
#        q.save()
#
#        return q

