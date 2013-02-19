from flask import Flask
from flask_peewee.db import Database
from biwinning.config import app


db = Database(app)
