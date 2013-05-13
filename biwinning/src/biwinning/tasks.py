from biwinning.config import QUANTIFIERS
from biwinning.data import fetch_club_new_rides_fair, get_orphan_rides, get_club_rides_for_week, fetch_ride, fetch_new_club_rides_fast


def update_club(club, threaded=False):
    # Add new rides
    for ride in (fetch_new_club_rides_fast(club) if threaded else fetch_club_new_rides_fair(club)):
        quantifiers = [q(club) for q in QUANTIFIERS]
        [q.add_ride(ride) for q in quantifiers]

def reload_club_week(club, week_id):
    for ride in get_club_rides_for_week(club, week_id):
        fetch_ride(ride.strava_id)

def clean_club(club):
    # Remove orphan rides
    [ride.delete_instance() for ride in get_orphan_rides(club)]

    # Remove orphan quantity records
    for quantifier in QUANTIFIERS:
        [quantity.delete_instance() for quantity in quantifier.orphans()]
