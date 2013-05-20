from flask import session, render_template
import simplejson
from biwinning.config import app
from biwinning.data import get_club
from biwinning.quantify import AthleteDistanceByWeek, AthleteDistanceByDay
from biwinning.utils import day_id_to_date


@app.route('/api/<club_id>/week-chart/<week_id>')
def api_week_chart(club_id=None, week_id=None):
    club = get_club(club_id)
    quantifier = AthleteDistanceByWeek(club)
    scoreboard = quantifier.scoreboard(week_id)

    return simplejson.dumps([
        {'label': q.athlete.name.split()[0], 'value': round(q.value/1000)}
        for q in scoreboard
    ])


@app.route('/api/<club_id>/day-chart/<day_id>')
def api_day_chart(club_id=None, day_id=None):
    club = get_club(club_id)
    quantifier = AthleteDistanceByDay(club)
    scoreboard = quantifier.scoreboard(day_id)

    return simplejson.dumps([
        {'label': q.athlete.name.split()[0], 'value': round(q.value/1000)}
        for q in scoreboard
    ])

@app.route('/api/<club_id>/range/<start_date_id>/<end_date_id>')
def api_date_range(club_id, start_date_id, end_date_id):
    date_start, date_end = day_id_to_date(start_date_id), day_id_to_date(end_date_id)
    club = get_club(club_id)
    session['club_id'] = club_id
    quantifier = AthleteDistanceByDay(club)
    scoreboard = quantifier.date_range(date_start, date_end)

    return simplejson.dumps([
        {'label': r.athlete.name.split()[0], 'value': round(r.distance/1000)}
        for r in scoreboard
    ])
