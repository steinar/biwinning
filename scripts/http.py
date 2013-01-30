from flask import Flask, render_template, redirect, url_for
import itertools
import sys
import strava

app = Flask("biwinning")
CLUB_ID = 7459

print_safe = lambda x: x.decode('utf8', 'ignore')

def get_users_week_summary(weeks,rides,users):
    for week_id in weeks:
        week_distance_fn = lambda user: sum(
            map(lambda r: r.distance, filter(lambda r: r.week_id == week_id, rides[user])))
        elevation_fn = lambda user: sum(
            map(lambda r: r.elevation_gain, filter(lambda r: r.week_id == week_id, rides[user])))
        mark_max = lambda s, l: "*" if s == max(l) else ""

        km = lambda n: round(n / 1000., 1)
        meters = lambda n: round(n, 1)

        dist = map(lambda u: km(week_distance_fn(u)), users)
        elev = map(lambda u: meters(elevation_fn(u)), users)

        max_dist = max(dist)
        dist_with_max = [(d,max_dist == d) for d in dist]
        max_elev = max(elev)
        elev_with_max = [(e,max_elev == e) for e in elev]

        yield (week_id, zip(map(print_safe, users), zip(dist_with_max,elev_with_max)))

@app.route('/')
def weeks(update=False):
    club_name, members = strava.load_club_members(CLUB_ID)
    rides = strava.get_rides_from_cache(members)
    users = sorted(members.keys())
    weeks = set(map(lambda x: x.week_id, itertools.chain(*rides.values())))

    results = get_users_week_summary(reversed(sorted(weeks)[-5:]), rides, users)

    return render_template('rides-by-week.html', results=list(results),users=map(print_safe, users))

@app.route('/update')
def update():
    return render_template('update.html')

@app.route('/do-update')
def do_update():
    club_name, members = strava.load_club_members(CLUB_ID)
    strava.get_rides_threaded(members)
    return redirect(url_for('weeks'))

if __name__ == '__main__':
    debug = 'debug' in sys.argv
    app.run(debug=debug)
