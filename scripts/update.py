#!/usr/bin/env python
import os
os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))

from biwinning.models import Club
from biwinning.tasks import update_club

def update():
    for club in Club.all():
        print "Updating: ", club.strava_id
        update_club(club)

if __name__ == '__main__':
    update()
