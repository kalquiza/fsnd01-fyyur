#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.orm import relationship
from sqlalchemy import event

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
# Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

artist_genre = db.Table('artist_genre',
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

venue_genre = db.Table('venue_genre',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = relationship("Genre", secondary=venue_genre)
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))    
    image_link = db.Column(db.String(500))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = relationship("Genre", secondary=artist_genre)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))
    image_link = db.Column(db.String(500))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Genre(db.Model):
    __tablename__ = 'Genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column('id', db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'))
    start_time = db.Column(db.DateTime, nullable=False)

    venue = db.relationship(Venue, backref="shows", passive_deletes=True, cascade="all")
    artist = db.relationship(Artist, backref="shows", passive_deletes=True, cascade="all")


#----------------------------------------------------------------------------#
# Helpers
#----------------------------------------------------------------------------#
@event.listens_for(db.session, 'after_flush')
def delete_address_orphans(session, ctx):
  # delete-orphan cascades only work for children with a single parent 
  # manually delete orphans in Show with an event listener that cleans
  # up after each flush

  if any(isinstance(i, Show) for i in session.dirty):
    query = session.query(Show).filter_by(venue_id=None)
    orphans = query.all()
    for orphan in orphans:
      session.delete(orphan)

    query = session.query(Show).filter_by(artist_id=None)
    orphans = query.all()
    for orphan in orphans:
      session.delete(orphan)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # shows list of venues page organized by city, state
  # replace with real venues data.
  # num_shows should be aggregated based on number of upcoming shows per venue.

  data=[]
  # iterate through venues by city, state
  locations = Venue.query.with_entities(Venue.city, Venue.state).distinct()
  for location in locations:
    # add venues located in each city, state
    venue_list=[]
    venues = Venue.query.filter_by(city=location[0], state=location[1])
    for venue in venues:
      num_upcoming_shows = 0
      for show in venue.shows:
        if show.start_time > datetime.today():
          num_upcoming_shows += 1
      venue_list.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": num_upcoming_shows
      })
    data.append({
      "city": location[0],
      "state": location[1],
      "venues": venue_list
    })
    
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # implement search on artists with partial string search. Ensure it is case-insensitive.

  search='%'+request.form.get('search_term')+'%'
  venues = Venue.query.filter(Venue.name.ilike(search)).all()
  count= Venue.query.filter(Venue.name.ilike(search)).count()
  data=[]
  
  for venue in venues:    
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": Show.query.filter(Show.venue_id==venue.id, Show.start_time>datetime.today()).count()
    })

  response={
    "count": count,
    "data": data
  }  


  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id

  # replace with real venue data from the Venues table, using venue_id
  try:
    venue = Venue.query.get(venue_id)

    # modify show data to fit template
    past_shows=[]
    upcoming_shows=[]
    for show in venue.shows:
      if show.start_time > datetime.today():
        upcoming_shows.append({
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": babel.dates.format_datetime(show.start_time, "EE MM, dd, y h:mma")
      })
      else:
        past_shows.append({
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": babel.dates.format_datetime(show.start_time, "EE MM, dd, y h:mma")
      })

    data={
      "id": venue.id,
      "name": venue.name,
      "genres": [genre.name for genre in venue.genres],
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website_link,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
    
  except Exception:
    return not_found_error(Exception)
    
  return render_template('pages/show_venue.html', venue=data)

#  Create
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # modify data to be the data object returned from db insertion
  # insert form data as a new aenue record in the db, instead

  form = VenueForm(request.form)
  error = False
  try:
    if form.validate():
      venue = Venue(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        address=form.address.data,
        phone=form.phone.data,
        website_link=form.website_link.data,
        facebook_link=form.facebook_link.data,
        image_link=form.image_link.data,
        seeking_talent=form.seeking_talent.data,
        seeking_description=form.seeking_description.data
        )
      db.session.add(venue)

      # insert form data for genre and venue_genres records
      for genre in form.genres.data:
        existing_genre = Genre.query.filter_by(name=genre).first()
        # insert genre data as a new genre record in the db if it does not exist
        if not existing_genre:
          venue.genres.append(Genre(name=genre))
        else:
          venue.genres.append(existing_genre)
      db.session.commit()
    else:
      error = True
  except Exception:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

#  Update
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # shows the edit venue page with the given venue_id

  # populate form with fields from venue with ID <venue_id>
  try:
    venue = Venue.query.get(venue_id)
    form = VenueForm(
      name=venue.name,
      genres=[genre.name for genre in venue.genres],
      address=venue.address,
      city=venue.city,
      state=venue.state,
      phone=venue.phone,
      website_link=venue.website_link,
      facebook_link=venue.facebook_link,
      seeking_talent=venue.seeking_talent,
      seeking_description=venue.seeking_description,
      image_link=venue.image_link
    )

  except Exception:
    return not_found_error(Exception)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  form = VenueForm(request.form)
  error = False
  try:
    venue = Venue.query.get(venue_id)

    if form.validate():
      venue.name=form.name.data
      venue.address=form.address.data
      venue.city=form.city.data
      venue.state=form.state.data
      venue.phone=form.phone.data
      venue.website_link=form.website_link.data
      venue.facebook_link=form.facebook_link.data
      venue.image_link=form.image_link.data
      venue.seeking_talent=form.seeking_talent.data
      venue.seeking_description=form.seeking_description.data
      
      # remove existing venue-genre relations
      venue.genres = []

      # create new venue-genre relations
      for genre in form.genres.data:
        existing_genre = Genre.query.filter_by(name=genre).first()
        # insert genre data as a new genre record in the db if it does not exist
        if not existing_genre:
          venue.genres.append(Genre(name=genre))
        else:
          venue.genres.append(existing_genre)
          
      db.session.commit()
    else:
      error = True
  except Exception:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully updated!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Delete
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  venue_name= None
  try:
    venue = Venue.query.get(venue_id)
    venue_name = venue.name
    db.session.delete(venue)
    db.session.commit()
  except Exception:
    db.session.rollback()
  finally:
    db.session.close()
  # returns the name of
  return venue_name


@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue_submission(venue_id):
  # create endpoint to allow deletions from the edit page

  venue = None
  error = False
  try:
    venue = delete_venue(venue_id)
    print(venue)
  except Exception:
    error = True
  if venue is None: 
    # on unsuccessful db deletion, flash an error instead.
    flash('An error occurred. The selected venue could not be deleted.')
  else:
    # on successful db deletion, flash success
    flash('Venue ' + venue + ' was successfully deleted.')
    
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data=[]
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search='%'+request.form.get('search_term')+'%'
  artists = Artist.query.filter(Artist.name.ilike(search)).all()
  count= Artist.query.filter(Artist.name.ilike(search)).count()
  data=[]
  
  for artist in artists:    
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": Show.query.filter(Show.artist_id==artist.id, Show.start_time>datetime.today()).count()
    })

  response={
    "count": count,
    "data": data
  }  

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  
  # replace with real artist data from the Artists table, using artist_id
  try:
    artist = Artist.query.get(artist_id)

    # modify show data to fit template
    past_shows=[]
    upcoming_shows=[]
    for show in artist.shows:
      if show.start_time > datetime.today():
        upcoming_shows.append({
          "venue_id": show.id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": babel.dates.format_datetime(show.start_time, "EE MM, dd, y h:mma")
        })
      else:
        past_shows.append({
          "venue_id": show.venue.id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": babel.dates.format_datetime(show.start_time, "EE MM, dd, y h:mma")
        })

    data={
      "id": artist.id,
      "name": artist.name,
      "genres": [genre.name for genre in artist.genres],
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website_link,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
  except Exception:
    return not_found_error(Exception)
    
  return render_template('pages/show_artist.html', artist=data)

#  Create
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # modify data to be the data object returned from db insertion
  # insert form data as a new artist record in the db
  form = ArtistForm(request.form)
  error = False
  try:
    if form.validate():
      artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        website_link=form.website_link.data,
        facebook_link=form.facebook_link.data,
        image_link=form.image_link.data,
        seeking_venue=form.seeking_venue.data,
        seeking_description=form.seeking_description.data
        )
      db.session.add(artist)
      # insert form data for genre and artist_genres records
      for genre in form.genres.data:
        existing_genre = Genre.query.filter_by(name=genre).first()
        # insert genre data as a new genre record in the db if it does not exist
        if not existing_genre:
          artist.genres.append(Genre(name=genre))
        else:
          artist.genres.append(existing_genre)
      db.session.commit()
    else:
      error = True
  except Exception:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # shows the edit artist page with the given artist_id

  # populate form with fields from artist with ID <artist_id>
  try:
    artist = Artist.query.get(artist_id)
    form = ArtistForm(
      name=artist.name,
      genres=[genre.name for genre in artist.genres],
      city=artist.city,
      state=artist.state,
      phone=artist.phone,
      website_link=artist.website_link,
      facebook_link=artist.facebook_link,
      seeking_venue=artist.seeking_venue,
      seeking_description=artist.seeking_description,
      image_link=artist.image_link
    )

  except Exception:
    return not_found_error(Exception)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm(request.form)
  error = False
  try:
    artist = Artist.query.get(artist_id)

    if form.validate():
      artist.name=form.name.data
      artist.city=form.city.data
      artist.state=form.state.data
      artist.phone=form.phone.data
      artist.website_link=form.website_link.data
      artist.facebook_link=form.facebook_link.data
      artist.image_link=form.image_link.data
      artist.seeking_venue=form.seeking_venue.data
      artist.seeking_description=form.seeking_description.data
      
      # remove existing artist-genre relations
      artist.genres = []

      # create new artist-genre relations
      for genre in form.genres.data:
        existing_genre = Genre.query.filter_by(name=genre).first()
        # insert genre data as a new genre record in the db if it does not exist
        if not existing_genre:
          artist.genres.append(Genre(name=genre))
        else:
          artist.genres.append(existing_genre)

      db.session.commit()
    else:
      error = True
  except Exception:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

#  Delete
#  ----------------------------------------------------------------

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  # Complete this endpoint for taking a artist_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  artist_name= None
  try:
    artist = Artist.query.get(artist_id)
    artist_name = artist.name
    db.session.delete(artist)
    db.session.commit()
  except Exception:
    db.session.rollback()
  finally:
    db.session.close()
  # returns the name of
  return artist_name


@app.route('/artists/<artist_id>/delete', methods=['POST'])
def delete_artist_submission(artist_id):
  # create endpoint to allow deletions from the edit page

  artist = None
  error = False
  try:
    artist = delete_artist(artist_id)
    print(artist)
  except Exception:
    error = True
  if artist is None: 
    # on unsuccessful db deletion, flash an error instead.
    flash('An error occurred. The selected artist could not be deleted.')
  else:
    # on successful db deletion, flash success
    flash('Artist ' + artist + ' was successfully deleted.')

  return redirect(url_for('index'))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows

  # replace with show data ordered by descending start time
  data=[]
  shows = Show.query.order_by(Show.start_time.desc()).all()
  for show in shows:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": babel.dates.format_datetime(show.start_time, "EE MM, dd, y h:mma")
    })
 
  return render_template('pages/shows.html', shows=data)

#  Create
#  ----------------------------------------------------------------

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # insert form data as a new Show record in the db, instead

  form = ShowForm(request.form)
  error = False
  try:
    if form.validate():
      print('data is valid')
      print(form.venue_id.data)
      print(form.artist_id.data)
      print(form.start_time.data)

      show = Show(
        venue_id=form.venue_id.data,
        artist_id=form.artist_id.data,
        start_time=form.start_time.data
      )
      db.session.add(show)
      db.session.commit()
    else:
      error = True
  except Exception:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
