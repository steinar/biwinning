#!/usr/bin/env python
import os
import itertools
import biwinning
from werkzeug import script
from biwinning.config import app, CLUB_ID

os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))

def make_shell():
    modules = (biwinning.quantify, biwinning.data, biwinning.models, biwinning.utils)
    context = [[(x, getattr(module, x)) for x in dir(module) if not x.startswith('_')] for module in modules]
    return dict(app=app, **dict(itertools.chain(*context)))

if __name__ == "__main__":
    script.make_shell(make_shell, use_ipython=True)()