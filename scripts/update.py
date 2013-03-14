#!/usr/bin/env python
import os
from biwinning.models import Club
from biwinning.tasks import update_club

os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))

if __name__ == '__main__':
    for club in Club.all():
        print "Updating: ", club
        update_club(club)