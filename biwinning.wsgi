import os
import sys

os.environ['mode'] = 'production'

sys.path.insert(0, '/var/www/biwinning/repo/')

activate_this = '/var/www/biwinning/biwinning-env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from biwinning import app as application
