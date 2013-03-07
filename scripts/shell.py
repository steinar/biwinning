#!/usr/bin/env python
import itertools
import biwinning
from werkzeug import script
from biwinning.config import app, CLUB_ID

def make_shell():
    modules = (biwinning.strava, biwinning.quantify, biwinning.models)
    context = [[(x, getattr(module, x)) for x in dir(module) if not x.startswith('_')] for module in modules]
    return dict(app=app, **dict(itertools.chain(*context)))

if __name__ == "__main__":
    script.make_shell(make_shell, use_ipython=True)()