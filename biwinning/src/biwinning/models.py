import datetime
import simplejson
from biwinning.config import db
from dateutil.relativedelta import relativedelta
from peewee import TextField, IntegerField, CharField, DateTimeField, BooleanField, TimeField, FloatField, ForeignKeyField, fn
from playhouse.signals import Model as SignalModel, pre_save, connect
from biwinning.utils import convert, parse_date

MODELS = []
TABLES = []

def model(cls):
    MODELS.append(cls)
    return cls

def table(cls):
    TABLES.append(cls)
    return cls


class Model(db.Model, SignalModel):
    @classmethod
    def all(cls):
        return cls.select()

    def matches_dict(self, value_dict, key_translation=None):
        """
        Returns True if all values of input dict match the corresponding attribute of the instance.
        Optional dict key => attribute name translation dictionary may be provided.
        """
        t = key_translation or {}
        return all([getattr(self, t.get(k, k)) == v for (k,v) in value_dict.items()])


    def values_from_dict(self, value_dict, key_translation=None, value_fn=None):
        """
        Set attributes values from input dictionary.
        Optional dict key => attribute name translation dictionary may be provided.
        """
        key_translation = key_translation or {}
        value_fn = value_fn or {}

        [setattr(self, key_translation.get(k, k), v) for (k,v) in value_dict.items()]

        translated = ((key_translation.get(k, convert(k)), value_fn.get(k, lambda x: x)(v)) for k, v in value_dict.items())
        [setattr(self, k, v) for (k,v,) in translated]

        return self

    def __eq__(self, other):
        return self.id == other.id

@model
class Club(Model):
    strava_id = IntegerField(unique=True, index=True)
    name = TextField(default='')

    @property
    def athletes(self):
        return Athlete.select().join(ClubAthlete).join(Club).where(Club.id == self.id)
#        return (ca.athlete for ca in self.clubathlete_set)

    def __repr__(self):
        return "<Club %s: %s>" % (self.id, self.username)



@model
class Athlete(Model):
    strava_id = IntegerField(unique=True, index=True)
    name = CharField(null=True)
    username = CharField(null=True)

    @property
    def clubs(self):
        return Club.select().join(ClubAthlete).join(Athlete).where(Athlete.id == self.id)
#        return (ca.club for ca in self.clubathlete_set)

    @property
    def max_ride_id(self):
        return Ride.select().where(Ride.athlete==self).aggregate(fn.Max(Ride.strava_id))

    def __repr__(self):
        return "<Athlete %s: %s>" % (self.id, self.username)

@model
class ClubAthlete(Model):
    """
    Club <-> Athlete many to many.
    """
    club = ForeignKeyField(Club, index=True)
    athlete = ForeignKeyField(Athlete, index=True)

    def __repr__(self):
        return "<ClubAthlete %s: %s, %s>" % (self.id, self.club, self.athlete)



@model
class Ride(Model):
    strava_id = IntegerField(default=0, unique=True, index=True)
    name = CharField(default='')
    description = TextField(null=True)
    start_date = DateTimeField(null=True)
    start_date_local = DateTimeField(null=True)
    distance = FloatField(default=0)
    athlete = ForeignKeyField(Athlete, related_name='rides')
    maximum_speed = FloatField(default=0)
    moving_time = IntegerField(default=0)
    elapsed_time = IntegerField(default=0)
    commute = BooleanField(default=False)
    elevation_gain = FloatField(default=0)
    trainer = BooleanField(default=False)
    average_speed = FloatField(default=0)
    average_watts = FloatField(default=0, null=True)
    time_zone_offset = IntegerField(default=0)
    location = CharField(default='')
    json = TextField(default='')

    # Added fields (not from strava)
    week = CharField(default='', null=True)

    def set_athlete(self, athlete_dict):
        print "Athlete", athlete_dict
        athlete = Athlete.get_or_create(strava_id=athlete_dict['id'])
        if not athlete.matches_dict(athlete_dict, {'id': 'strava_id'}):
            print "Not matcing"
            athlete.values_from_dict(athlete_dict, {'id': 'strava_id'})
            athlete.save()
        self.athlete = athlete


    def get_athlete(self):
        return self.athlete

    athlete_dict = property(get_athlete, set_athlete)

    def populate_from_dict(self, value_dict):
        self.json = simplejson.dumps(value_dict)

        key_translation = {
            'id': 'strava_id',
            'athlete': 'athlete_dict'
        }

        value_fn = {
            'startDate': parse_date,
            'startDateLocal': parse_date
        }

        self.values_from_dict(value_dict, key_translation, value_fn)
        return self

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
        return "<Ride %s: %s, %s>" % (self.id, self.strava_id, self.start_date)


@connect(pre_save, sender=Ride)
def ride_week(model_class, instance, created):
    instance.week = instance.start_date_local and instance.start_date_local.strftime("%Y-%W") or None

@model
class Quantity(Model):
    class_name = CharField(index=True)
    athlete = ForeignKeyField(Athlete, index=True, null=True)
    key = CharField(index=True)
    max_strava_id = IntegerField(default=0, index=True)
    value = FloatField(default=0)
    data_json = TextField(null=True)

    def get_data(self):
        return self.data_json and simplejson.loads(self.data_json) or {}

    def set_data(self, d):
        self.data_json = simplejson.dumps(d or {})

    data = property(get_data, set_data)

    @classmethod
    def add_or_update(cls, class_name, athlete, key, max_strava_id, value, data):
        try:
            instance = cls.get(class_name=class_name, athlete=athlete, key=key)
        except cls.DoesNotExist:
            instance = cls.create(class_name=class_name, athlete=athlete, key=key)

        instance.values_from_dict({'max_strava_id': max_strava_id, 'value': value, 'data': data})
        instance.save()

    def get_max_strava_id(self, athlete):
        return Quantity.select().where(Quantity.athlete==athlete).aggregate(fn.Max(Quantity.max_strava_id))

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "<Quantity %s: %s, %s, %s>" % (self.id, self.class_name, self.key, self.value)


for cls in MODELS:
    cls.create_table(fail_silently=True)

