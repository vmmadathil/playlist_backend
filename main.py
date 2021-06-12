#from src.playlistmaker import getTopSongs
import flask
from flask import render_template, redirect, request, session

from playlistmaker import *
import spotifyauth

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util

from dotenv import load_dotenv

env_path = ('../.env')
load_dotenv(dotenv_path=env_path)


app = flask.Flask(__name__)
app.config["DEBUG"] = True

global token 
global username

@app.route('/', methods=['POST', 'GET'])
def home():
    return render_template('about.html')



@app.route('/authorize', methods = ['POST'])
def authorize():
    if request.method == 'POST':
        responses = request.form
        global username
        username = responses.get('usname')
        #session['username'] = username

        response = spotifyauth.getUser()
        return redirect(response)

@app.route('/callback/')
def callback():
    spotifyauth.getUserToken(request.args['code'])
    global token
    token = spotifyauth.getAccessToken()[0]
    return redirect('/create')

@app.route('/create', methods=['GET', 'POST'])
def create():

    if request.method == 'GET':
        return render_template('loading.html')

    if request.method == 'POST':
      
        sp = spotipy.Spotify(auth=token)

        print('getting library')
        library_df = getLibrary(sp)
        short_df, med_df, long_df = getTopSongs(sp)
        artist_short_df, artist_med_df, artist_long_df = getTopArtists(sp)
        print('got everything')
        tracks_df = calcScores(library_df, artist_short_df, artist_med_df, artist_long_df, short_df, med_df, long_df)
        classifer, pipeline = trainModel(tracks_df)
        print('made model')
        session['playlist_id'] = predictSongs(tracks_df, classifer, pipeline, username, sp)
       

        return 'done'

@app.route('/success', methods=['GET', 'POST'])
def success():
    id = session['playlist_id']
    return render_template('success.html', value = id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port = '8888', debug=True)