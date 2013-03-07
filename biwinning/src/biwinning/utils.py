import time
import datetime
import re

parse_date = lambda d: datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")

first_name = lambda s: s.split()[0]


def convert(name):
    """Camel case to underscore. veryNice => very_nice
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2 - t1) * 1000.0)
        return res

    return wrapper

def monday(offset=0):
    today = datetime.date.today()
    return today + datetime.timedelta(days=-today.weekday(), weeks=offset)

def get_week_id(date):
    return date.strftime("%Y-%W")
