import os
from flask import Flask


DATABASE = {
    'name': 'biwinning.db',
    'engine': 'peewee.SqliteDatabase',
    }

DEBUG = True
SECRET_KEY = 'ssshhhh'
CLUB_ID = 7459

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = '%s/biwinning.db' % BASE_PATH
DATA_PATH = os.path.join(os.getcwd(), 'data')

app = Flask("biwinning")
app.config.from_object(__name__)