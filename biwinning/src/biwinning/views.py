import itertools
import datetime
from flask import render_template, redirect, url_for
from biwinning.config import app
from biwinning.models import Club
from biwinning.quantify import AthleteDistanceByWeek
from biwinning.tasks import update_club
from biwinning.utils import get_week_id, monday

print_safe = lambda x: x.decode('utf8', 'ignore')

@app.route('/')
def weeks(update=False):
    club = Club.all()[0]
    quantifier = AthleteDistanceByWeek(club)
    athletes = list(club.athletes)
    weeks = [(get_week_id(monday(-i)), monday(-i), monday(-i+1)) for i in range(0, 10)]
    week_ids = [w[0] for w in weeks]

    distance_by_week = dict((week_id, dict([(a.id, quantifier.get(a, week_id)) for a in athletes])) for week_id in week_ids)
    scoreboards = dict((week_id, quantifier.scoreboard(week_id)) for week_id in week_ids)

    return render_template('rides-by-week.html',
        club=club,
        week_ids=week_ids,
        distance_by_week=distance_by_week,
        scoreboards=scoreboards,
        weeks=weeks
    )

@app.route('/update')
def update():
    return render_template('update.html')

@app.route('/do-update')
def do_update():
    club = Club.all()[0]
    update_club(club)
    return redirect(url_for('weeks'))
