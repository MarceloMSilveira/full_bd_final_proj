#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

#import json
import dateutil.parser
from datetime import datetime, date, time
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
#from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from config_db import db

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app) #legado
app.config.from_object('config')
db.init_app(app)

migrate = Migrate(app,db)

#models are in a separated file now! 
#deve ser importado aqui:
from models import Venue, Artist, Show

with app.app_context():
   db.create_all()
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if value is None:
    return ''

  # 1) Normalize para datetime
  if isinstance(value, datetime):
      dt = value
  elif isinstance(value, date):
      dt = datetime.combine(value, time.min)
  else:
      dt = dateutil.parser.parse(str(value))  # só parseia se for string
    
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  
  return babel.dates.format_datetime(dt, format, locale='en')

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
    
  def get_qtt_upcoming_shows(venue_id):
    venue = db.get_or_404(Venue, venue_id)
    now = datetime.now()
    upcoming_shows_count = len([show for show in venue.shows if show.date>now])
    return upcoming_shows_count


  stmt = db.select(
     Venue.city, Venue.state, Venue.name, Venue.id
     ).order_by(Venue.city,Venue.state,Venue.name)
  
  rows = db.session.execute(stmt).mappings().all()

  data = []
  previous_key = None

  for row in rows:
    key = (row['city'],row['state'])

    if (previous_key != key):
      actual_place = {
         "city":row['city'],
         "state":row['state'],
         "venues":[]
      }
      data.append(actual_place)
      previous_key = key

    actual_place["venues"].append(
      {
        "id": row['id'],
        "name": row['name'], 
        "num_upcoming_shows": get_qtt_upcoming_shows(row['id'])
      }
    )   

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term= (request.form.get('search_term') or '').strip()
  if not search_term:
    response = {"count": 0, "data": []}
    return render_template('pages/search_venues.html',results=response, search_term=search_term)
  
  pattern = f"%{search_term.replace('%','\\%').replace('_','\\_')}%"

  stmt = (
    db.select(Venue)
    .where(Venue.name.ilike(pattern, escape='\\'))
    .order_by(Venue.name)
    .limit(50)
  )
  
  venues = db.session.execute(stmt).scalars().all()
  data = [{"id":v.id,"name":v.name} for v in venues]

  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # done
  try:
    data = db.get_or_404(Venue,venue_id)
    venue = {
      'id':data.id,
      'name':data.name,
      'city':data.city,
      'state':data.state,
      'genres':data.genres,
      'image_link':data.image_link,
      'seeking_talent':data.seeking_talent,
      'seeking_description':data.seeking_description,
      'upcoming_shows': [],
      'past_shows': [],
      'upcoming_shows_count': 0,
      'past_shows_count': 0,
    }    
    shows = data.shows
    for show in shows:
      artist_id = show.id_artist
      artist = db.session.execute(db.select(Artist.name, Artist.image_link).filter_by(id=artist_id)).one()
      new_show = {
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.date,
        "artist_id": artist_id
      }
      
      now = datetime.now()
      if new_show['start_time'] > now:
        venue['upcoming_shows'].append(new_show)
      else:
        venue['past_shows'].append(new_show)
          
    venue['upcoming_shows_count'] = len(venue['upcoming_shows'])
    venue['past_shows_count'] = len(venue['past_shows'])
    return render_template('pages/show_venue.html', venue=venue)
  
  except Exception as e:
    print(str(e))
    flash(f"Venue with id {venue_id} not found")
    return render_template('pages/home.html')

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  if form.validate_on_submit():
    #genres_list = form.genres.data
    #genres = ','.join(genres_list)
    new_venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        genres = form.genres.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
    )
    try:
      db.session.add(new_venue)
      db.session.commit()
      print(new_venue.id)
      # on successful db insert, flash success
      flash('Venue ' + new_venue.name+ ' was successfully listed!')
    except Exception as e:
       db.session.rollback()
       print(f"Ocorreu um erro inesperado: {str(e)}")
       flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    finally:
       db.session.close()

  else:
     flash(' Error inserting Venue ' + form.name.data)
     print(form.errors)
  
  return render_template('pages/home.html')  

#DELETE
@app.route('/venues/<int:venue_id>/delete', methods=['GET','POST'])
def delete_venue(venue_id):
  venue = db.get_or_404(Venue,venue_id)
  form = DeleteVenueForm()
  if form.validate_on_submit():
    try:
      db.session.delete(venue)
      db.session.commit()
      flash(f'Venue {venue.name} apagada com sucesso!')
      return render_template('pages/home.html')
    except Exception as e:
      db.session.rollback()
      print(str(e))
      flash(f'Falha ao tentar deletar Venue {venue_id}!')
      return render_template('pages/home.html')

  return render_template('forms/delete_venue.html', venue=venue, form=form) 



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # done

  data = db.session.execute(db.select(Artist.id,Artist.name)).all()
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  stmt = db.select(Artist).where(Artist.name.ilike(f'%{search_term}%'))
  results = db.session.execute(stmt).scalars().all()
  data=[]
  for result in results:
    artist = {
      'id':result.id,
      'name':result.name
    }
    data.append(artist)

  len_data = len(data)

  #num_upcoming_shows = 

  response={
    "count": len_data,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # done
  
  try:
    data = db.get_or_404(Artist,artist_id)
    #genres = data.genres.split(',')
    new_artist ={
      "id":data.id,
      "name":data.name,
      "genres":data.genres,
      "city":data.city,
      "state":data.state,
      "phone":data.phone,
      "seeking_venue":data.seeking_venue,
      "seeking_description":data.seeking_description,
      "image_link":data.image_link,
      "past_shows":[],
      "upcoming_shows":[],
      "past_shows_count":0,
      "upcoming_shows_count":0,
    }
    
    shows = data.shows
    for show in shows:
      venue_id = show.id_venue
      venue = db.session.execute(db.select(Venue.name, Venue.image_link).filter_by(id=venue_id)).one()
      new_show ={
        'venue_id':venue_id,
        'venue_image_link':venue.image_link,
        'venue_name':venue.name,
        'start_time':show.date
      }

      now = datetime.now()

      if new_show['start_time'] > now:
        new_artist['upcoming_shows'].append(new_show)
      else:
        new_artist['past_shows'].append(new_show)

    new_artist['upcoming_shows_count'] = len(new_artist['upcoming_shows'])
    new_artist['past_shows_count'] = len(new_artist['past_shows'])

    return render_template('pages/show_artist.html', artist=new_artist)
  except Exception as e:
    print(str(e))
    flash(f"Artist id={artist_id} not found")
    return render_template('pages/home.html')

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  if form.validate_on_submit():
    # genres_list = form.genres.data
    # genres = ",".join(genres_list)
    try:
      new_artist = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = form.genres.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(new_artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')  
    except Exception as e:
      db.session.rollback()
      print(f"error inserting Artist: {str(e)}")
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    finally:
      db.session.close()
  else:
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')

  return render_template('pages/home.html')



#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  try:
    data = db.get_or_404(Artist,artist_id)
    #genres = (data.genres).split(',')
    artist = {
      "id":data.id,
      "name":data.name,
      "genres":data.genres,
      "city":data.city,
      "state":data.state,
      "phone":data.phone,
      "seeking_venue":data.seeking_venue,
      "seeking_description":data.seeking_description,
      "image_link":data.image_link
    }
    form = ArtistForm(data=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  except Exception as e:
    print(str(e))
    flash(f"Fail on finding data for artist with id{artist_id}")
    return render_template('pages/home.html')

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  if form.validate_on_submit():
    print('test')
    try:
      artist = db.get_or_404(Artist,artist_id)
      #genres = ','.join(form.genres.data or [])
      
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.image_link = form.image_link.data
      artist.facebook_link = form.facebook_link.data
      artist.website_link = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data

      db.session.commit()

    except Exception as e:
      db.session.rollback()
      print(str(e))
      flash('Erro ao tentar atualizar o artista!')
  else:
    for field, errors in form.errors.items():
      for error in errors:
        flash(f'Erro no campo {getattr(form, field).label.text}: {error}')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  try:
    data = db.get_or_404(Venue,venue_id)
    #genres = data.genres.split(',')
    venue = {
      'id':data.id,
      'name':data.name,
      'city':data.city,
      'state':data.state,
      'genres':data.genres,
      'image_link':data.image_link,
      'address':data.address,
      'website_link':data.website_link,
      'facebook_link':data.facebook_link, 
      'seeking_talent':data.seeking_talent,
      'seeking_description':data.seeking_description,
      'image_link' :data.image_link
    }
    form = VenueForm(data=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)
  except Exception as e:
    print(str(e))
    flash(f"Fail on finding data for venue with id{venue_id}")
    return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  if (form.validate_on_submit()):
    try:
      venue = db.get_or_404(Venue,venue_id)
      #genres_list = form.genres.data
      #genres = ','.join(genres_list)
    
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.image_link = form.image_link.data
      venue.facebook_link = form.facebook_link.data
      venue.website_link = form.website_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data

      db.session.commit()
      return redirect(url_for('show_venue', venue_id=venue_id))
    
    except Exception as e:
      print(str(e))
    
  else:
    flash('Falha ao validar formulário de atualização de venue')
    return redirect(url_for('index'))
  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  stmt = db.select(
    Show.id_venue.label('venue_id'), 
    Show.id_artist.label('artist_id'),
    Show.date.label('start_time'),
    Artist.name.label('artist_name'),
    Artist.image_link.label('artist_image_link'), 
    Venue.name.label('venue_name')).join(Venue).join(Artist)
  
  data = db.session.execute(stmt).all()
    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  form = ShowForm()

  newShow = Show(
    id_artist = form.artist_id.data,
    id_venue = form.venue_id.data,
    date = form.start_time.data
  )

  try:
    db.session.add(newShow)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e:
    flash('Failure inserting data. Show was NOT listed!')
    print(f"Error creating show {str(e)}")
  finally:
    db.session.close()
  
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
