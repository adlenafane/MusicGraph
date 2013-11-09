# -*- coding: utf-8 -*-

'''
    Getters to clean things up
'''

import requests

BASE_URL = 'http://developer.echonest.com/api/v4/'
API_KEY = "JKVBCIDFBTBNKAVH0"
DEEZER_BASE_URL = 'http://api.deezer.com/2.0/'


def get_song_json(artist, song):
    '''
        From a string of artist name and/or song name, return the first result of echonest
    '''
    url = BASE_URL + 'song/search?api_key=' + API_KEY\
                   + '&format=json&results=1&artist=' + artist \
                   + '&title=' + song \
                   + '&bucket=id:spotify-WW&bucket=tracks&limit=true'
    song_start_result = requests.get(url)
    return song_start_result.json()


def get_similar_song_json(song_id, number=20):
    '''
        From an echonest track_id get the similar songs
    '''
    similar_songs_url = BASE_URL + 'playlist/static?api_key=' \
                                 + API_KEY \
                                 + '&song_id=' + song_id \
                                 + '&format=json'\
                                 + '&results=' + str(number)\
                                 + '&type=song-radio'
    return requests.get(similar_songs_url).json()


def get_song_json_by_id(song_id):
    '''
        From an echonest track_id get the json of the song
    '''
    url = BASE_URL + 'song/profile?api_key=' + API_KEY\
                   + '&format=json&results=1&track_id=' + song_id \
                   + '&bucket=id:spotify-WW&bucket=tracks&limit=true'
    song_start_result = requests.get(url)
    return song_start_result.json()


class Song():
    def __init__(self, song_json):
        songs_list = song_json['response']['songs']
        if len(songs_list) > 0:
            self.song_id = songs_list[0]['tracks'][0]['id']
            self.artist = songs_list[0]['artist_name']
            self.title = songs_list[0]['title']
            self.spotify_id = songs_list[0]['tracks'][0]['foreign_id']
        else:
            pass
        self.json = song_json


class DeezerSong():
    """
        Create a nice object for a song from Deezer based on the id of the song
    """
    def __init__(self, track_deezer_id):
        self.track_deezer_id = track_deezer_id

        # Create the request to retrieve the full json
        url = DEEZER_BASE_URL + 'track/' + track_deezer_id
        self.json = requests.get(url).json()

        # Fill all the element for the Deezer song
        self.readable = self.json['readable']
        self.title = self.json['title']
        self.link = self.json['link']
        self.duration = self.json['duration']
        self.track_position = self.json['track_position']
        self.disk_number = self.json['disk_number']
        self.rank = self.json['rank']
        self.preview = self.json['preview']

        self.artist_id = self.json['artist']['id']
        self.album_id = self.json['album']['id']


class DeezerArtist():
    """
        Create a nice object for an artist from Deezer based on the id of the artist
    """
    def __init__(self, artist_deezer_id):
        self.artist_deezer_id = artist_deezer_id

        # Create the request to retrieve the full json
        url = DEEZER_BASE_URL + 'artist/' + artist_deezer_id
        self.json = requests.get(url).json()

        # Fill all the element for the Deezer artist
        self.name = self.json['name']
        self.link = self.json['link']
        self.picture = self.json['picture']
        self.nb_album = self.json['nb_album']
        self.nb_fan = self.json['nb_fan']
        self.radio = self.json['radio']


class DeezerAlbum():
    """
        Create a nice object for an album from Deezer based on the id of the album
    """
    def __init__(self, album_deezer_id):
        self.album_deezer_id = album_deezer_id

        # Create the request to retrieve the full json
        url = DEEZER_BASE_URL + 'album/' + album_deezer_id
        self.json = requests.get(url).json()

        # Fill all the element for the Deezer album
        self.title = self.json['title']
        self.link = self.json['link']
        self.cover = self.json['cover']
        self.genre_id = self.json['genre_id']
        self.label = self.json['label']
        self.duration = self.json['duration']
        self.fans = self.json['fans']
        self.rating = self.json['rating']
        self.release_date = self.json['release_date']
        self.available = self.json['available']
        self.artist = self.json['artist']
