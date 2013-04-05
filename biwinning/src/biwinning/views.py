from flask import render_template, redirect, url_for, session, send_from_directory, request
import os
from biwinning.config import app
from biwinning.data import get_club
from biwinning.models import Club
from biwinning.quantify import AthleteDistanceByWeek, AthleteDistanceByDay
from biwinning.tasks import update_club, reload_club_week
from biwinning.utils import  monday, date, week_id

print_safe = lambda x: x.decode('utf8', 'ignore')


@app.route('/')
def index():
    if session.get('club_id'):
        return redirect(url_for('club_overview', club_id=session['club_id']))
    return redirect(url_for('clubs'))


@app.route('/clubs')
def clubs():
    clubs = Club.all_augmented()
    return render_template('clubs.html', clubs=clubs)

@app.route('/add-club', methods=['POST'])
def add_club():
    club = get_club(request.form['add_club_id'])
    if club:
        return redirect(url_for('club_overview', club_id=club.strava_id))
    return redirect(url_for('clubs'))


@app.route('/<club_id>/overview')
def club_overview(club_id):
    club = get_club(club_id)

    quantifier_day = AthleteDistanceByDay(club)
    last_28_days = quantifier_day.last_28_days()[0:5]

    quantifier_week = AthleteDistanceByWeek(club)
    week_scoreboards = dict([(week, quantifier_week.scoreboard(week)) for week in [week_id(monday(0))]])

    return render_template('club-overview.html',
        club=club,
        last_28_days=last_28_days,
        week_scoreboards=week_scoreboards,
        week_id=week_id(monday(0)),
        week_start = monday(),
        week_end = monday(+1)
    )




@app.route('/<club_id>/weeks')
@app.route('/<club_id>/weeks/<first_week_id>')
def weekly_scoreboard(club_id, first_week_id=None):
    week_per_request = 3
    base_date = date(first_week_id or week_id(monday()))
    mon = lambda i: monday(i, base_date)

    weeks = [(week_id(mon(-i)), mon(-i), mon(-i + 1))
             for i in range(0, week_per_request)]

    club = get_club(club_id)
    session['club_id'] = club_id
    quantifier = AthleteDistanceByWeek(club)
    week_scoreboards = dict((week[0], quantifier.scoreboard(week[0])) for week in weeks)

    return render_template('rides-by-week.html',
        club=club,
        week_scoreboards=week_scoreboards,
        weeks=weeks,
        next_week_id=week_id(mon(-week_per_request))
    )

@app.route('/<club_id>/reload-week/<week_id>')
def reload_week(club_id, week_id):
    reload_club_week(club_id, week_id)
    return redirect(url_for('weekly_scoreboard', club_id=club_id, first_week_id=week_id))



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