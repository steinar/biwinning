import datetime
from peewee import fn, R
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

    def get(self, athlete, key):
        try:
            return Quantity.get(class_name=self.name, athlete=athlete, key=self._key(key))
        except Quantity.DoesNotExist:
            return Quantity(class_name=self.name, athlete=athlete, key=self._key(key), value=0)


    def all(self):
        return Quantity.select().where(Quantity.class_name == self.name)

    def _fetch_data(self, max_strava_id=0):
        """
        Yield data for rides newer than max_strava_id.
        """
        pass

    def rebuild(self):
        """
        Rebuild local storage.
        """

    def rebuild(self):
        self.update(None)

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

    def _key(self, *args, **kwargs):
        """
        Key for individual quantity entry.
        """
        pass

    def clean(self):
        pass



@quantifier
class AthleteDistanceByWeek(Quantifier):
    unit = 'm'
    group_by = (Ride.athlete, Ride.week)

    def __init__(self, club):
        self.club = club
        self.data = {}
        super(AthleteDistanceByWeek, self).__init__()


    def _key(self, ride_or_date):
        if isinstance(ride_or_date, Ride):
            return ride_or_date.week
        return isinstance(ride_or_date, datetime.date) and ride_or_date.strftime("%Y-%W") or ride_or_date

    def _base_query(self):
        return (Ride
                 .select(
            Ride.athlete,
            Ride.week,
            Ride.month,
            Ride.year,
            Ride.date,
            fn.Max(Ride.strava_id).alias('max_strava_id'),
            fn.Sum(Ride.distance).alias('distance'),
            fn.Sum(Ride.elevation_gain).alias('elevation_gain'),
            fn.Sum(Ride.moving_time).alias('moving_time'),
            fn.Count().alias('count'))
                 .join(Athlete).join(ClubAthlete)
                 .where(ClubAthlete.club == self.club)
            )

    def _key_query(self):
        """
        List of weeks in which athlete has one or more rides.
        """
        return (Ride
         .select(Ride.week)
         .join(Athlete).join(ClubAthlete)
         .where(ClubAthlete.club == self.club)
         .group_by(Ride.week)
        )

    def orphans(self):
        return Quantity.select().where(~(Quantity.key << self._key_query()))

    def _fetch_data(self, athlete=None, max_strava_id=0, group_by=None):
        query = self._base_query()

        if max_strava_id:
            query = query.where(Ride.strava_id > max_strava_id)

        if athlete:
            query = query.where(Ride.athlete == athlete)

        if group_by:
            query = query.group_by(*group_by)

        return query


    def update(self, max_strava_id):
        for result in self._fetch_data(group_by=self.group_by):
            print result
            Quantity.add_or_update(self.name,
                result.athlete,
                self._key(result),
                result.max_strava_id,
                result.distance,
                {'count': result.count,
                 'elevation_gain': result.elevation_gain,
                 'moving_time': result.moving_time,
                 'distance': result.distance,
                 'average_speed': result.distance/result.moving_time
                }
            )

    def scoreboard(self, week_or_date):
        return (Quantity
                .select()
                .where(Quantity.key == self._key(week_or_date), Quantity.value > 0)
                .join(Athlete)
                .join(ClubAthlete)
                .where(ClubAthlete.club == self.club).order_by(Quantity.value.desc())
            )

    def add_ride(self, ride):
        quantity = self.get(athlete=ride.athlete, key=ride.start_date_local)
        quantity.value += ride.distance
        data = quantity.data or {}
        val = lambda k: data.get(k, 0)

        data.update({
            'count': val('count') + 1,
            'distance': val('distance') + ride.distance,
            'elevation_gain': val('elevation_gain') + ride.elevation_gain,
            'moving_time': val('moving_time') + ride.moving_time,
        })

        data['average_speed'] = val('distance')/val('moving_time') if val('moving_time') else 0
        quantity.data = data

        quantity.save()

        return quantity


    def subtract_ride(self, ride):
        q = self.get(athlete=ride.athlete, key=ride.start_date_local)
        q.value -= ride.distance

        d = lambda k: q.data.get(k, 0)

        if d('count') == 1:
            q.delete_instance()
            return None

        q.data.update({
            'count': d('count') - 1,
            'distance': d('distance') - ride.distance,
            'elevation_gain': d('elevation_gain') - ride.elevation_gain,
            'moving_time': d('moving_time') - ride.moving_time,
        })

        q.data['average_speed'] = d('distance')/d('moving_time')

        q.save()

        return q

    def clean(self):
        return len([q.delete_instance() for q in self.orphans()])


@quantifier
class AthleteDistanceByDay(AthleteDistanceByWeek):
    unit = 'm'
    group_by = (Ride.athlete, Ride.date)

    def _key(self, ride_or_date):
        if isinstance(ride_or_date, Ride):
            return ride_or_date.week
        if isinstance(ride_or_date, datetime.datetime):
            return ride_or_date.date()
        return ride_or_date


    def _key_query(self):
        return (Ride
                .select(Ride.week)
                .join(Athlete).join(ClubAthlete)
                .where(ClubAthlete.club == self.club)
                .group_by(Ride.date)
            )

    def last_28_days(self):
        query = (self._fetch_data()
                 .where(Ride.date >= datetime.date.today() - datetime.timedelta(days=28))
                 .group_by(Ride.athlete)
                 .order_by(R('distance desc'))
            )
        return query


@quantifier
class AthleteDistanceByMonth(AthleteDistanceByWeek):
    unit = 'm'
    group_by = (Ride.athlete, Ride.month)

    def _key(self, ride_or_date):
        if isinstance(ride_or_date, Ride):
            return ride_or_date.month
        if isinstance(ride_or_date, datetime.datetime):
            return ride_or_date.strftime("%Y-%m")
        return ride_or_date


    def _key_query(self):
        return (Ride
                .select(Ride.month)
                .join(Athlete).join(ClubAthlete)
                .where(ClubAthlete.club == self.club)
                .group_by(Ride.date)
            )
