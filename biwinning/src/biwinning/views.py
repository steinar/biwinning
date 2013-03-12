from flask import render_template, redirect, url_for, session, send_from_directory, request
import os
from biwinning.config import app
from biwinning.data import get_club
from biwinning.models import Club
from biwinning.quantify import AthleteDistanceByWeek
from biwinning.tasks import update_club
from biwinning.utils import get_week_id, monday
from biwinning.api import *

print_safe = lambda x: x.decode('utf8', 'ignore')


@app.route('/')
def index():
    if session.get('club_id'):
        return redirect(url_for('weekly_scoreboard', club_id=session['club_id']))
    return redirect(url_for('clubs'))

@app.route('/clubs')
def clubs():
    clubs = Club.all_augmented()
    return render_template('clubs.html', clubs=clubs)



@app.route('/<club_id>/weeks')
def weekly_scoreboard(club_id):
    return weekly_scoreboard_page(club_id, 0)

@app.route('/<club_id>/weeks/<page>')
def weekly_scoreboard_page(club_id, page):
    weeks_per_page = 1
    club = get_club(club_id)
    page = int(page)
    session['club_id'] = club_id
    quantifier = AthleteDistanceByWeek(club)
    weeks = [(get_week_id(monday(-i)), monday(-i), monday(-i+1)) for i in range(page*weeks_per_page, (page+1)*weeks_per_page)]


    scoreboards = dict((week[0], quantifier.scoreboard(week[0])) for week in weeks)

    return render_template('rides-by-week.html',
        club=club,
        scoreboards=scoreboards,
        weeks=weeks,
        page=page
    )

@app.route('/<club_id>/update')
def update(club_id):
    club = get_club(club_id)
    return render_template('update.html', club=club)

@app.route('/<club_id>/do-update')
def do_update(club_id):
    club = get_club(club_id)
    update_club(club)
    return redirect(url_for('weekly_scoreboard', club_id=club_id))

@app.route('/static/js/<path:filename>')
def send_pic(filename):
    return send_from_directory(os.path.join(app.config['BASE_PATH'], 'static/js'), filename)