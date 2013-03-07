import itertools
import datetime
from flask import render_template, redirect, url_for
from biwinning import strava
from biwinning.config import app
from biwinning.models import Club
from biwinning.quantify import AthleteDistanceByWeek
from biwinning.utils import get_week_id, monday

print_safe = lambda x: x.decode('utf8', 'ignore')

@app.route('/')
def weeks(update=False):
    club = Club.all()[0]
    quantifier = AthleteDistanceByWeek(club)
    athletes = list(club.athletes)
    weeks = []
    for i in range(0, 10):
        week_id = get_week_id(monday(-i))
        weeks.append((week_id, dict([(a.id, quantifier.get(a, week_id)) for a in athletes])))
    return render_template('rides-by-week.html', club=club, weeks=weeks)

@app.route('/update')
def update():
    return render_template('update.html')

@app.route('/do-update')
def do_update():
    return redirect(url_for('weeks'))
