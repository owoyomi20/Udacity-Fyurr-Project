# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import os
import sys
import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    abort,
    jsonify,
    flash,
    redirect,
    url_for,
)
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, desc
import logging
from datetime import datetime, timezone
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

from models import *

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# form submission getter
def extract_data(field_name):
    if field_name == "genres":
        return request.form.getlist(field_name)
    elif (
        field_name == "seeking_talent"
        or field_name == "seeking_venue"
        and request.form[field_name] == "y"
    ):
        return True
    elif (
        field_name == "seeking_talent"
        or field_name == "seeking_venue"
        and request.form[field_name] != "y"
    ):
        return False
    else:
        return request.form[field_name]


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    all_venues = Venue.query.all()

    # sorting venues by city and state.
    venues_dict = {}

    for v in all_venues:
        key = f"{v.city}, {v.state}"

        venues_dict.setdefault(key, []).append(
            {
                "id": v.id,
                "name": v.name,
                "num_upcoming_shows": v.shows.count(),
                "city": v.city,
                "state": v.state,
            }
        )

    data = []
    for value in venues_dict.values():
        data.append(
            {"city": value[0]["city"], "state": value[0]["state"], "venues": value}
        )

    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_term = extract_data("search_term")
    venue_result = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()

    response = {"count": len(venue_result), "data": []}

    for result in venue_result:
        response["data"].append(
            {
                "id": result.id,
                "name": result.name,
                "num_upcoming_shows": result.shows.count(),
            }
        )

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term"),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = db.session.query(Venue).filter(Venue.id == venue_id).all()
    current_time = datetime.now(timezone.utc)
    data = {}
    down_show = []
    up_show = []
    for col in venue:
        upcoming_shows = col.shows.filter(Show.start_time > current_time).all()
        past_shows = col.shows.filter(Show.start_time < current_time).all()
        data.update(
            {
                "id": col.id,
                "name": col.name,
                "genres": col.genres.split(", "),
                "address": col.address,
                "city": col.city,
                "state": col.state,
                "phone": col.phone,
                "website": col.website,
                "facebook_link": col.facebook_link,
                "seeking_talent": col.seeking_talent,
                "seeking_description": col.seeking_description,
                "image_link": col.image_link,
            }
        )
        for show in upcoming_shows:
            if len(upcoming_shows) == 0:
                data.update(
                    {
                        "upcoming_shows": [],
                    }
                )
            else:
                artist = (
                    db.session.query(Artist.name, Artist.image_link)
                    .filter(Artist.id == show.artist_id)
                    .one()
                )
                up_show.append(
                    {
                        "artist_id": show.artist_id,
                        "artist_name": artist.name,
                        "artist_image_link": artist.image_link,
                        "start_time": show.start_time.strftime("%m/%d/%Y"),
                    }
                )
        for show in past_shows:
            if len(past_shows) == 0:
                data.update(
                    {
                        "past_shows": [],
                    }
                )
            else:
                artist = (
                    db.session.query(Artist.name, Artist.image_link)
                    .filter(Artist.id == show.artist_id)
                    .one()
                )
                down_show.append(
                    {
                        "artist_id": show.artist_id,
                        "artist_name": artist.name,
                        "artist_image_link": artist.image_link,
                        "start_time": show.start_time.strftime("%m/%d/%Y"),
                    }
                )
        data.update({"upcoming_shows": up_show})
        data.update({"past_shows": down_show})
        data.update(
            {
                "past_shows_count": len(past_shows),
                "upcoming_shows_count": len(upcoming_shows),
            }
        )

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    try:
        data = Venue()
        data.name = request.form.get("name")
        data.genres = ", ".join(request.form.getlist("genres"))
        data.address = request.form.get("address")
        data.city = request.form.get("city")
        data.state = request.form.get("state")
        data.phone = request.form.get("phone")
        data.facebook_link = request.form.get("facebook_link")
        data.image_link = request.form.get("image_link")
        data.website = request.form.get("website_link")
        data.seeking_talent = (
            True if request.form.get("seeking_talent") != None else False
        )
        data.seeking_description = request.form.get("seeking_description")

        db.session.add(data)
        db.session.commit()
    except:
        flash(
            "An error occurred. Venue "
            + request.form.get("name")
            + " could not be listed.",
            category="error",
        )
        print("exc_info()", sys.exc_info())
        db.session.rollback()

    finally:
        db.session.close()
        return redirect(url_for("venues"))


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    status = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        status = True
        flash("Venue successfully deleted!")

    except:
        print(sys.exc_info())
        db.session.rollback()
        status = False
        flash("Error deleting venue", category="error")

    finally:
        db.session.close()

    return jsonify({"success": status})


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    data = []
    all_artists = Artist.query.all()
    for artist in all_artists:
        data.append({"id": artist.id, "name": artist.name})
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search_term = extract_data("search_term")
    artist_result = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()

    response = {"count": len(artist_result), "data": []}

    for result in artist_result:
        response["data"].append(
            {
                "id": result.id,
                "name": result.name,
                "num_upcoming_shows": result.shows.count(),
            }
        )
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = db.session.query(Artist).filter(Artist.id == artist_id).all()
    current_time = datetime.now(timezone.utc)
    data = {}
    down_show = []
    up_show = []
    for entry in artist:
        upcoming_shows = (
            db.session.query(Show)
            .join(Venue)
            .filter(Show.artist_id == artist_id)
            .filter(Show.start_time > datetime.now())
            .all()
        )
        past_shows = (
            db.session.query(Show)
            .join(Venue)
            .filter(Show.artist_id == artist_id)
            .filter(Show.start_time > datetime.now())
            .all()
        )
        data.update(
            {
                "id": entry.id,
                "name": entry.name,
                "genres": entry.genres.split(", "),
                "city": entry.city,
                "state": entry.state,
                "phone": entry.phone,
                "website": entry.website,
                "facebook_link": entry.facebook_link,
                "seeking_venue": entry.seeking_venue,
                "seeking_description": entry.seeking_description,
                "image_link": entry.image_link,
            }
        )
        for show in upcoming_shows:
            if len(upcoming_shows) == 0:
                data.update(
                    {
                        "upcoming_shows": [],
                    }
                )
            else:
                venue = (
                    db.session.query(Venue.name, Venue.image_link)
                    .filter(Venue.id == show.venue_id)
                    .one()
                )
                up_show.append(
                    {
                        "venue_id": show.venue_id,
                        "venue_name": venue.name,
                        "venue_image_link": venue.image_link,
                        "start_time": show.start_time.strftime("%m/%d/%Y"),
                    }
                )
        for show in past_shows:
            if len(past_shows) == 0:
                data.update(
                    {
                        "past_shows": [],
                    }
                )
            else:
                venue = (
                    db.session.query(Venue.name, Venue.image_link)
                    .filter(Venue.id == show.venue_id)
                    .one()
                )
                down_show.append(
                    {
                        "venue_id": show.venue_id,
                        "venue_name": venue.name,
                        "venue_image_link": venue.image_link,
                        "start_time": show.start_time.strftime("%m/%d/%Y"),
                    }
                )
        data.update({"upcoming_shows": up_show})
        data.update({"past_shows": down_show})
        data.update(
            {
                "past_shows_count": len(past_shows),
                "upcoming_shows_count": len(upcoming_shows),
            }
        )
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    data = Artist.query.get(artist_id)
    edit_artist_data = {
        "id": data.id,
        "name": data.name,
        "genres": data.genres.split(", "),
        "city": data.city,
        "state": data.state,
        "phone": data.phone,
        "website_link": data.website,
        "facebook_link": data.facebook_link,
        "seeking_venue": data.seeking_venue,
        "seeking_description": data.seeking_description,
        "image_link": data.image_link,
    }
    return render_template("forms/edit_artist.html", form=form, artist=edit_artist_data)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    try:
        data = Artist.query.get(artist_id)
        data.name = request.form.get("name")
        data.genres = ", ".join(request.form.getlist("genres"))
        data.city = request.form.get("city")
        data.state = request.form.get("state")
        data.phone = request.form.get("phone")
        data.facebook_link = request.form.get("facebook_link")
        data.image_link = request.form.get("image_link")
        data.website = request.form.get("website_link")
        data.seeking_venue = (
            True if request.form.get("seeking_venue") != None else False
        )
        data.seeking_description = request.form.get("seeking_description")
        db.session.add(data)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    data = Venue.query.get(venue_id)
    edit_venue_data = {
        "id": data.id,
        "name": data.name,
        "genres": data.genres.split(", "),
        "address": data.address,
        "city": data.city,
        "state": data.state,
        "phone": data.phone,
        "website": data.website,
        "facebook_link": data.facebook_link,
        "seeking_talent": data.seeking_talent,
        "seeking_description": data.seeking_description,
        "image_link": data.image_link,
    }
    return render_template("forms/edit_venue.html", form=form, venue=edit_venue_data)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    try:
        data = Venue.query.get(venue_id)
        data.name = request.form.get("name")
        data.genres = ", ".join(request.form.getlist("genres"))
        data.address = request.form.get("address")
        data.city = request.form.get("city")
        data.state = request.form.get("state")
        data.phone = request.form.get("phone")
        data.facebook_link = request.form.get("facebook_link")
        data.image_link = request.form.get("image_link")
        data.website = request.form.get("website_link")
        data.seeking_talent = (
            True if request.form.get("seeking_talent") != None else False
        )
        data.seeking_description = request.form.get("seeking_description")
        db.session.add(data)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    error = False
    try:
        data = Artist()
        data.name = request.form.get("name")
        data.genres = ", ".join(request.form.getlist("genres"))
        data.city = request.form.get("city")
        data.state = request.form.get("state")
        data.phone = request.form.get("phone")
        data.facebook_link = request.form.get("facebook_link")
        data.image_link = request.form.get("image_link")
        data.website = request.form.get("website_link")
        data.seeking_venue = (
            True if request.form.get("seeking_venue") != None else False
        )
        data.seeking_description = request.form.get("seeking_description")
        db.session.add(data)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        flash("Artist " + request.form.get("name") + " was successfully listed!")
    else:
        flash(
            "An error occurred. Artist "
            + request.form.get("name")
            + " could not be listed."
        )
        # Internal Server Error
        abort(500)
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    data = []
    shows = db.session.query(Show).order_by(desc(Show.start_time)).all()
    for show in shows:
        artist = (
            db.session.query(Artist.name, Artist.image_link)
            .filter(Artist.id == show.artist_id)
            .one()
        )
        venue = db.session.query(Venue.name).filter(Venue.id == show.venue_id).one()
        data.append(
            {
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.start_time.strftime("%m/%d/%Y"),
            }
        )

    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    error = False
    try:
        data = Show()
        data.venue_id = request.form.get("venue_id")
        data.artist_id = request.form.get("artist_id")
        data.start_time = request.form.get("start_time")
        db.session.add(data)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if not error:
        flash("Show was successfully listed!")
    else:
        flash("An error occurred. Show could not be listed.")
        # Internal Server Error
        abort(500)
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# # Default port:
# if __name__ == "__main__":
#     app.run()

# Or specify port manually:

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7000))
    app.run(host="127.0.0.1", port=port)
