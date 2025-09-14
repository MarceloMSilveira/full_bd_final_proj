#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
from config_db import db
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app import db
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(postgresql.ARRAY(sa.Text), default=list, server_default=sa.text("'{}'"), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='Venue', lazy=True)


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(postgresql.ARRAY(sa.Text), default=list, server_default=sa.text("'{}'"), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='Artist', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
   __tablename__='Show'
  
   id = db.Column(db.Integer, primary_key=True)
   id_artist = db.Column(db.Integer, db.ForeignKey('Artist.id'))
   id_venue = db.Column(db.Integer, db.ForeignKey('Venue.id'))
   date = db.Column(db.DateTime)
