import os
import datetime
from flask import render_template as flask_render_template, redirect, url_for, session, send_from_directory, request
from biwinning.config import app
from biwinning.data import get_club
from biwinning.models import Club
from biwinning.quantify import AthleteDistanceByWeek, AthleteDistanceByDay
from biwinning.tasks import update_club, reload_club_week, clean_club
from biwinning.utils import  monday, week_id_to_date, week_id, day_id, day_id_to_date

print_safe = lambda x: x.decode('utf8', 'ignore')

def render_template(*args, **kwargs):
    kwargs.update({
        'clubs': Club.all_augmented(),
        'club': kwargs.get('club') or (session.get('club_id') and get_club(session.get('club_id')))
    })
    return flask_render_template(*args, **kwargs)

@app.route('/')
def index():
    return redirect(url_for('clubs'))


@app.route('/clubs')
def clubs():
    return render_template('clubs.html')

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
    base_date = week_id_to_date(first_week_id or week_id(monday()))
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


@app.route('/<club_id>/days')
@app.route('/<club_id>/days/<first_day_id>')
def daily_scoreboard(club_id, first_day_id=None):
    days_per_request = 3
    base_date = first_day_id and day_id_to_date(first_day_id) or datetime.date.today()

    days = [(day_id(base_date, -i))
             for i in range(0, days_per_request)]

    club = get_club(club_id)
    session['club_id'] = club_id
    quantifier = AthleteDistanceByDay(club)
    scoreboard = dict((day, quantifier.scoreboard(day)) for day in days)

    # pprint.pprint([(k, list(v)) for (k,v) in scoreboard.items()])

    return render_template('rides-by-day.html',
        club=club,
        scoreboard=scoreboard,
        days=days,
        next_day_id=day_id(base_date, -days_per_request)
    )

@app.route('/<club_id>/range/<start_date_id>/<end_date_id>')
def date_range(club_id, start_date_id, end_date_id):
    date_start, date_end = day_id_to_date(start_date_id), day_id_to_date(end_date_id)
    club = get_club(club_id)
    session['club_id'] = club_id
    quantifier = AthleteDistanceByDay(club)
    scoreboard = quantifier.date_range(date_start, date_end)

    return render_template('rides-by-range.html',
        club=club,
        scoreboard=scoreboard,
        date_start=date_start,
        date_end=date_end,
        start_date_id=start_date_id,
        end_date_id=end_date_id,
    )

@app.route('/<club_id>/reload-week/<week_id>')
def reload_week(club_id, week_id):
    reload_club_week(club_id, week_id)
    return redirect(url_for('weekly_scoreboard', club_id=club_id, first_week_id=week_id))


@app.route('/<club_id>/update')
def update(club_id):
    club = get_club(club_id)
    next_view = request.args.get('next') or 'club_overview'
    return render_template('update.html', club=club, next_view=next_view)


@app.route('/<club_id>/clean')
def clean(club_id):
    club = get_club(club_id)
    clean_club(club)
    next_view = request.args.get('next') or 'club_overview'
    return redirect(url_for(next_view, club_id=club_id))


@app.route('/<club_id>/do-update')
def do_update(club_id):
    club = get_club(club_id)
    update_club(club, threaded=True)
    next_view = request.args.get('next') or 'club_overview'
    return redirect(url_for(next_view, club_id=club_id))


@app.route('/static/js/<path:filename>')
def send_pic(filename):
    return send_from_directory(os.path.join(app.config['BASE_PATH'], 'static/js'), filename)