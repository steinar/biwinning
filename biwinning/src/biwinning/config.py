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
DATA_PATH = os.path.join(os.getcwd(), 'data')

DATABASE = {
    'name': 'biwinning.db',
    'engine': 'peewee.SqliteDatabase',
    }

app = Flask("biwinning")
app.config.from_object(__name__)