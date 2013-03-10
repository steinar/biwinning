from biwinning.config import QUANTIFIERS
from biwinning.data import fetch_club_new_rides_fair, get_orphan_rides

def update_club(club):
    # Add new rides
    for ride in fetch_club_new_rides_fair(club):
        quantifiers = [q(club) for q in QUANTIFIERS]
        [q.add_ride(ride) for q in quantifiers]

def clean_club(club):
    # Remove orphan rides
    [ride.delete_instance() for ride in get_orphan_rides(club)]

    # Remove orphan quantity records
    for quantifier in QUANTIFIERS:
        [quantity.delete_instance() for quantity in quantifier.orphans()]
