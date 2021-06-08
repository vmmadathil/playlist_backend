#from src.playlistmaker import getTopSongs
import flask

from flask import render_template, redirect, url_for, request, session

from playlistmaker import *

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util

from dotenv import load_dotenv
import os

env_path = ('../.env')
load_dotenv(dotenv_path=env_path)
SECRET = os.getenv('MY_SECRET')


app = flask.Flask(__name__)
app.config["DEBUG"] = True

app.secret_key = SECRET


@app.route('/', methods=['POST', 'GET'])
def home():
    return render_template('about.html')



@app.route('/authorize', methods = ['POST'])
def authorize():
    if request.method == 'POST':
        responses = request.form
        username = responses.get('usname')


        SPOTIFY_CLIENT = os.getenv('SPOTIFY_CLIENT')
        SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
        redirect_uri = 'http://localhost:8888/callback/'

        global token

        #authorizations
        scope = 'user-library-read user-top-read playlist-modify-public playlist-read-private'

        credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT, client_secret=SPOTIFY_SECRET) 
        #sp = spotipy.Spotify(client_credentials_manager=credentials_manager)
        token = util.prompt_for_user_token(username, scope, SPOTIFY_CLIENT, SPOTIFY_SECRET, redirect_uri)

        if token:
            #return 'Successful Auth', token
            session['username'] = username
            session['token'] = token
            return redirect(url_for('create'))
        else: 
            return("Can't get token for", username)
         
    
@app.route('/create', methods=['GET', 'POST'])
def create():

    if request.method == 'GET':
        return render_template('loading.html')

    if request.method == 'POST':

        username = session['username']
        token = session['token']
        #global token
        print(token)
        print(username)
        
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

        session['playlist_id'] = predictSongs(tracks_df, classifer, pipeline, username, sp)
        print('made playlist')

        return 'done'

@app.route('/success', methods=['GET', 'POST'])
def success():
    id = session['playlist_id']

    id = '3Jqi5SzsaASC0wLgCOLBQp'
    return render_template('success.html', value = id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)