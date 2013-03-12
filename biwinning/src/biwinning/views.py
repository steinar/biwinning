from flask import render_template, redirect, url_for, session, send_from_directory
import os
from biwinning.config import app
from biwinning.data import get_club
from biwinning.models import Club
from biwinning.quantify import AthleteDistanceByWeek
from biwinning.tasks import update_club
from biwinning.utils import  monday, date, week_id

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
@app.route('/<club_id>/weeks/<first_week_id>')
def weekly_scoreboard_page(club_id, first_week_id=None):
    week_per_request = 3
    base_date = date(first_week_id or week_id(monday()))
    mon = lambda i: monday(i, base_date)

    weeks = [(week_id(mon(-i)), mon(-i), mon(-i + 1))
             for i in range(0, week_per_request)]

    club = get_club(club_id)
    session['club_id'] = club_id
    quantifier = AthleteDistanceByWeek(club)
    scoreboards = dict((week[0], quantifier.scoreboard(week[0])) for week in weeks)

    return render_template('rides-by-week.html',
        club=club,
        scoreboards=scoreboards,
        weeks=weeks,
        next_week_id=week_id(mon(-week_per_request))
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