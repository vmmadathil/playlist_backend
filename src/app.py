import flask
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util

from pathlib import Path
import os

from dotenv import load_dotenv

import pandas as pd


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return "<h1>Travel Playlist Creator</h1><p>This site is a prototype API for a service that will create personalized playlists for users.</p>"


def getAuth(username):
    env_path = ('../.env')
    load_dotenv(dotenv_path=env_path)

    SPOTIFY_CLIENT = os.getenv('SPOTIFY_CLIENT')
    SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
    USERNAME = username
    redirect_uri = 'http://localhost:8888/callback/'

    #authorizations
    scope = 'user-library-read user-top-read playlist-modify-public playlist-read-private'

    credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT, client_secret=SPOTIFY_SECRET) 
    sp = spotipy.Spotify(client_credentials_manager=credentials_manager)
    token = util.prompt_for_user_token(USERNAME, scope, SPOTIFY_CLIENT, SPOTIFY_SECRET, redirect_uri)

    if token:
        sp = spotipy.Spotify(auth=token)
    else:
        print("Can't get token for", USERNAME) 

'''
This function will return a user's library of songs and the auditory features of the songs
'''
def getLibrary():
    #getting the user's saved tracks 
    results = sp.current_user_saved_tracks()
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    #creating a DF of all songs and features
    track_ids = []
    track_names = []
    track_added_time = []
    track_main_artists = []

    for i in range(0, len(tracks)):
        #Removes the local tracks in your playlist if there are any
        if tracks[i]['track']['id'] != None: 
            track_ids.append(tracks[i]['track']['id'])
            track_names.append(tracks[i]['track']['name'])
            track_added_time.append(tracks[i]['added_at'])
            track_main_artists.append(tracks[i]['track']['artists'][0]['id'])

    #getting the different auditory features of the songs in the library
    features = []
    for i in range(0,len(track_ids)):
        audio_features = sp.audio_features(track_ids[i])
        for track in audio_features:
            features.append(track)
            
    playlist_df = pd.DataFrame(features, index = track_names)

def getTopSongs():
    #creating DF of top 100 short term songs
    short_id = []
    short_names = []

    results_short = sp.current_user_top_tracks(limit = 100, offset=0, time_range='short_term')['items']

    for i in range(0, len(results_short)):
        #Removes the local tracks in your playlist if there is any
        short_id.append(results_short[i]['uri'])
        short_names.append(results_short[i]['name'])

    short_df = pd.DataFrame(short_id, index = short_names, columns = ['uri'])

    #creating DF of top 100 medium term songs
    results_medium = sp.current_user_top_tracks(limit=100,offset=0,time_range='medium_term')['items']

    med_id = []
    med_names = []

    for i in range(0, len(results_medium)):
        #Removes the local tracks in your playlist if there is any
        med_id.append(results_medium[i]['uri'])
        med_names.append(results_medium[i]['name'])

    med_df = pd.DataFrame(med_id, index = med_names, columns = ['uri'])

    #creating DF of top 100 long term songs
    results_long = sp.current_user_top_tracks(limit=100,offset=0,time_range='long_term')['items']

    long_id = [] 
    long_names = []

    for i in range(0, len(results_long)):
        #Removes the local tracks in your playlist if there is any
        long_id.append(results_long[i]['uri'])
        long_names.append(results_long[i]['name'])

    long_df = pd.DataFrame(long_id, index = long_names, columns = ['uri'])

app.run()
