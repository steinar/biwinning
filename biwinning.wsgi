import os
import sys

sys.stdout = sys.stderr
os.chdir(os.path.dirname(os.path.abspath(__file__)))

os.environ['mode'] = 'production'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

activate_this = '/var/www/biwinning/biwinning-env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from biwinning import app as application