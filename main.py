#from src.playlistmaker import getTopSongs
import flask

from flask import render_template

from playlistmaker import *

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util

from dotenv import load_dotenv
import os

token = ''

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    #return "<h1>Travel Playlist Creator</h1><p>This site is a prototype API for a service that will create personalized playlists for users.</p>"
    return render_template('about.html')
    
@app.route('/authorize/<username>', methods=['GET'])
def authorize(username):
    env_path = ('../.env')
    load_dotenv(dotenv_path=env_path)

    SPOTIFY_CLIENT = os.getenv('SPOTIFY_CLIENT')
    SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
    USERNAME = username
    redirect_uri = 'http://localhost:8888/callback/'

    global token

    #authorizations
    scope = 'user-library-read user-top-read playlist-modify-public playlist-read-private'

    credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT, client_secret=SPOTIFY_SECRET) 
    sp = spotipy.Spotify(client_credentials_manager=credentials_manager)
    token = util.prompt_for_user_token(username, scope, SPOTIFY_CLIENT, SPOTIFY_SECRET, redirect_uri)

    if token:
        return 'Successful Auth', token
    else:
        return("Can't get token for", username)
         
    
@app.route('/create/<username>', methods=['GET'])
def create(username):

    global token
    print(token)
    
    sp = spotipy.Spotify(auth=token)

    library_df = getLibrary(sp)
    print('got library')

    short_df, med_df, long_df = getTopSongs(sp)
    print('got top songs')

    artist_short_df, artist_med_df, artist_long_df = getTopArtists(sp)
    print('got top artists')

    tracks_df = calcScores(library_df, artist_short_df, artist_med_df, artist_long_df, short_df, med_df, long_df)
    print('calculated scores')

    classifer, pipeline = trainModel(tracks_df)
    print('trained model')

    predictSongs(tracks_df, classifer, pipeline, username, sp)
    print('made playlist')

    return 'Made Playlist'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)