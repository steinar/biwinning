import simplejson
from biwinning.config import app
from biwinning.data import get_club
from biwinning.quantify import AthleteDistanceByWeek

@app.route('/api/<club_id>/week-chart/<week_id>')
def api_week_chart(club_id=None, week_id=None):
    club = get_club(club_id)
    quantifier = AthleteDistanceByWeek(club)
    scoreboard = quantifier.scoreboard(week_id)[0:10]

    return simplejson.dumps([
        {'label': q.athlete.name.split()[0], 'value': round(q.value/1000)}
        for q in scoreboard
    ])

