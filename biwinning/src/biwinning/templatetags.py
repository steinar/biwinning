import datetime
from jinja2.filters import do_mark_safe
from biwinning.config import app

def register(fn):
    app.jinja_env.filters[fn.__name__] = fn
    return fn

@register
def date(date, fmt='%d/%m/%y'):
    # check whether the value is a datetime object
    if not isinstance(date, (datetime.date, datetime.datetime)):
        try:
            date = datetime.datetime.strptime(str(date), '%Y-%m-%d').date()
        except Exception, e:
            return date
    return date.strftime(fmt)

@register
def kilo(n):
    return do_mark_safe("%s <small>km</small>" % round(n/1000))

@register
def meters(n):
    return do_mark_safe("%s <small>m</small>" % round(n))

@register
def ms2km(n):
    return do_mark_safe("%s <small>km/h</small>" % round(n*3.6))


@register
def minutes(n):
    return str(datetime.timedelta(seconds=n))

