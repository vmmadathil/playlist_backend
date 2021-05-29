import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util

from pathlib import Path
import os

from dotenv import load_dotenv

import pandas as pd
import random


import datetime
from dateutil.relativedelta import relativedelta

from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder




'''
This function will return a user's library of songs and the auditory features of the songs
'''
def getLibrary(sp):
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
            
    library_df = pd.DataFrame(features, index = track_names)

    #adding the time added to the df as a feature
    time_processed = []

    #stripping time to a datetime object
    for time in track_added_time:
        time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")
        time_processed.append(time)

    #adding the time and artist columns
    library_df['added_time'] = time_processed    
    library_df['artist_id'] = track_main_artists

    return library_df

def getTopSongs(sp):
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

    #adding the scores
    short_df['short_pts'] = 3
    med_df['med_pts'] = 2
    long_df['long_pts'] = 1

    #returning the songs
    return short_df, med_df, long_df


def getTopArtists(sp):
    #top short term artists
    artists_short = sp.current_user_top_artists(limit = 100, offset=0, time_range='short_term')['items']
    artist_short_id = [] 
    artist_short_names = []

    for i in range(0, len(artists_short)):
        #Removes the local tracks in your playlist if there are any
        artist_short_id.append(artists_short[i]['id'])
        artist_short_names.append(artists_short[i]['name'])
    
    #making df for short term top artists with points
    short_tuples = list(zip(artist_short_id, artist_short_names))
    artist_short_df = pd.DataFrame(short_tuples, columns=['artist_id','artist_name'])
    artist_short_df['artist_short_pts'] = 3


    #top medium term artists
    artists_med = sp.current_user_top_artists(limit = 100, offset=0, time_range='medium_term')['items']
    artist_med_id = [] 
    artist_med_names = []

    for i in range(0, len(artists_med)):
        #Removes the local tracks in your playlist if there is any
        artist_med_id.append(artists_med[i]['id'])
        artist_med_names.append(artists_med[i]['name'])

    #making df for medium term top artists with points
    med_tuples = list(zip(artist_med_id, artist_med_names))
    artist_med_df = pd.DataFrame(med_tuples, columns=['artist_id','artist_name'])
    artist_med_df['artist_med_pts'] = 2


    #top long term artists
    artists_long = sp.current_user_top_artists(limit = 100, offset=0, time_range='long_term')['items']
    artist_long_id = [] 
    artist_long_names = []

    for i in range(0, len(artists_long)):
        #Removes the local tracks in your playlist if there is any
        artist_long_id.append(artists_long[i]['id'])
        artist_long_names.append(artists_long[i]['name'])
    
    #making df for long term top artists with points
    long_tuples = list(zip(artist_long_id, artist_long_names))
    artist_long_df = pd.DataFrame(long_tuples, columns = ['artist_id', 'artist_name'])
    artist_long_df['artist_long_pts'] = 1

    #returning the top artists
    return artist_short_df, artist_med_df, artist_long_df


def calcScores(library_df, artist_short_df, artist_med_df, artist_long_df, short_df, med_df, long_df):
    #merging the artist dfs 
    library_df = library_df.merge(artist_short_df, how = 'left', on = 'artist_id')
    library_df = library_df.merge(artist_med_df, how = 'left', on = 'artist_id')
    library_df = library_df.merge(artist_long_df, how = 'left', on = 'artist_id')

    #merging the songs dfs
    library_df = library_df.merge(short_df, how = 'left', on = 'uri')
    library_df = library_df.merge(med_df, how = 'left', on = 'uri')
    library_df = library_df.merge(long_df, how = 'left', on = 'uri')

    #calculating time based scores
    ct = datetime.date.today()
    #last 0 - 3 months
    three_months = ct - relativedelta(months = 3)
    #last 6 months
    six_months = ct - relativedelta(months = 6)
    #last year
    last_year = ct - relativedelta(years = 1)

    #adding scores based on time added to library
    library_df.loc[(library_df['added_time'].dt.date >= three_months), 'time_pts'] = 3
    library_df.loc[(three_months > library_df['added_time'].dt.date) & (library_df['added_time'].dt.date  >= six_months), 'time_pts'] = 2
    library_df.loc[(six_months > library_df['added_time'].dt.date) & (library_df['added_time'].dt.date >= last_year), 'time_pts'] = 1 

    #calculating all scores
    library_df['total_pts'] = library_df['short_pts'] + library_df['med_pts'] + library_df['long_pts'] + library_df['time_pts'] + library_df['artist_short_pts'] + library_df['artist_med_pts'] + library_df['artist_long_pts']
    
    #assigning target
    library_df.loc[library_df['total_pts'] >= 3,'target'] = 1
    library_df.loc[library_df['total_pts'] < 3,'target'] = 0

    #dropping unneeded features
    tracks_df = library_df[['id', 'acousticness', 'danceability', 'duration_ms', 'energy', 'instrumentalness', 'key', 'liveness', 'loudness', 'speechiness', 'tempo', 'valence', 'target']]

    return tracks_df

# This function will train a random forest classifier
def trainModel(tracks_df):

    #creating pipeline object
    pipeline = Pipeline([('std_scaler', MinMaxScaler())])

    #preparing data from training
    X_train = tracks_df[["acousticness", "danceability", "duration_ms", "energy", "instrumentalness",  "key", "liveness", "loudness", "speechiness", "tempo", "valence"]]
    X_train_scaled = pipeline.fit_transform(X_train)
    y_train = tracks_df['target']
    y_train_scaled = LabelEncoder().fit_transform(y_train)

    classifier = RandomForestClassifier(n_estimators = 10, max_features='sqrt', max_depth = 13)
    classifier.fit(X_train_scaled, y_train_scaled)

    return classifier, pipeline

def predictSongs(tracks_df, classifier, pipeline, username, sp):
    rec_tracks = []

    ids = []

    for x in range(5):
        ids.append(random.choice(tracks_df.loc[tracks_df['target'] == 1]['id'].values.tolist()))

    #getting recommendations from the spotify API
    rec_tracks = sp.recommendations(seed_tracks=ids, limit=100)['tracks']

    rec_track_ids = []
    rec_track_names = []

    for i in rec_tracks:
        rec_track_ids.append(i['id'])
        rec_track_names.append(i['name'])

    rec_features = []
    for i in range(0,len(rec_track_ids)):
        rec_audio_features = sp.audio_features(rec_track_ids[i])
        for track in rec_audio_features:
            rec_features.append(track)

    rec_tracks_df = pd.DataFrame(rec_features, index = rec_track_ids)

    #keeping only relevant features
    rec_tracks_df = rec_tracks_df[["id", "acousticness", "danceability", "duration_ms", 
                         "energy", "instrumentalness",  "key", "liveness",
                         "loudness", "speechiness", "tempo", "valence", 'uri']]


    #preparing the tracks for prediction
    X_rec_tracks = rec_tracks_df.drop(columns = ['id', 'uri'])
    X_rec_scaled = pipeline.fit_transform(X_rec_tracks)

    rec_predict = classifier.predict(X_rec_scaled)

    #adding prediction to the DF
    rec_tracks_df['predict'] = rec_predict
    final_recs = rec_tracks_df.loc[rec_tracks_df['predict'] == 1]['id'].values.tolist()

    #creating playlist
    recs_playlist = sp.user_playlist_create(username, name= 'Python Recs II')

    #adding songs to playlist
    sp.user_playlist_add_tracks(username, recs_playlist['id'], final_recs)