from webbrowser import BackgroundBrowser
from app import db


class Venue(db.Model):
    __tablename__ = "Venue"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    city = db.Column(db.String(500))
    state = db.Column(db.String(500))
    address = db.Column(db.String(500))
    phone = db.Column(db.String(500))
    genres = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    facebook_link = db.Column(db.String(200))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref="venue", lazy="dynamic")


class Artist(db.Model):
    __tablename__ = "Artist"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    shows = db.relationship("Show", backref="artist", lazy="dynamic")


class Show(db.Model):
    __tablename__ = "Show"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime(timezone=True))
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
