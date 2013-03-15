import datetime
import simplejson
from biwinning.config import db
from dateutil.relativedelta import relativedelta
from peewee import TextField, IntegerField, CharField, DateTimeField, BooleanField, TimeField, FloatField, ForeignKeyField, fn, JOIN_INNER, JOIN_FULL, JOIN_LEFT_OUTER, DateField
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

        def decode(x):
            try:
                return hasattr(x, 'decode') and x.decode('utf-8', 'ignore') or x
            except UnicodeEncodeError:
                return x

        return all([getattr(self, t.get(k, k)) == decode(v) for (k,v) in value_dict.items()])


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

    @classmethod
    def all_augmented(cls):
        return cls.select(cls, fn.Count(ClubAthlete.id).alias('athlete_count')).join(ClubAthlete, JOIN_LEFT_OUTER).group_by(ClubAthlete.club)

    def __repr__(self):
        return "<Club %s: %s>" % (self.id, self.name)


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

    @property
    def url(self):
        return "http://app.strava.com/athletes/%s" % self.strava_id

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
    athlete = ForeignKeyField(Athlete, related_name='rides', null=True)

    name = CharField(default='')
    description = TextField(null=True)
    start_date = DateTimeField(null=True)
    start_date_local = DateTimeField(null=True)
    distance = FloatField(default=0)
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
    date = DateField(null=True)
    week = CharField(default='', null=True)
    month = CharField(default='', null=True)
    year = CharField(default='', null=True)

    def set_athlete(self, athlete_dict):
        athlete = Athlete.get_or_create(strava_id=athlete_dict['id'])
        if not athlete.matches_dict(athlete_dict, {'id': 'strava_id'}):
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

    def __repr__(self):
        return "<Ride %s: %s, %s>" % (self.id, self.strava_id, self.start_date)


try:
    @connect(pre_save, sender=Ride)
    def ride_week(model_class, instance, created):
        date = instance.start_date_local
        instance.date = date and date.date() or None
        instance.week = date and date.strftime("%Y-%W") or None
        instance.month = date and date.strftime("%Y-%m") or None
        instance.year = date and date.strftime("%Y") or None

    pass

except ValueError, e:
    print e

class JsonField(TextField):
    def db_value(self, value):
        return value if value is None else self.coerce(simplejson.dumps(value))

    def python_value(self, value):
        return value if value is None else simplejson.loads(self.coerce(value))


@model
class Quantity(Model):
    class_name = CharField(index=True)
    athlete = ForeignKeyField(Athlete, index=True, null=True)
    key = CharField(index=True)
    max_strava_id = IntegerField(default=0, index=True)
    value = FloatField(default=0)
    data = JsonField(null=True)
    strava_ids = JsonField(null=True)

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

