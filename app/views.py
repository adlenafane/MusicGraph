# -*- coding: utf-8 -*-

'''
    Handle the Flask interface
'''

from flask import render_template, request
from app import app
from utility import get_song_json, get_similar_song_json, get_song_json_by_id
from utility import Song
from py2neo import neo4j, cypher
import Queue


BASE_URL = 'http://developer.echonest.com/api/v4/'
ECHO_NEST_API_KEY = "JKVBCIDFBTBNKAVH0"
PLAYLIST = Queue.Queue()
GRAPH_DB = neo4j.GraphDatabaseService("http://localhost:7474/db/data/")


@app.route('/')
def index():
    '''
        Display the home page of the tool, allowing to search for songs
    '''
    # Retrieve the input data
    song_start = request.args.get('songStart', '')
    artist_start = request.args.get('artistStart', '')
    song_end = request.args.get('songEnd', '')
    artist_end = request.args.get('artistEnd', '')

    # Find the starting point
    # song_start_result = song.search(title=song_start)[0]
    song_start_result_json = get_song_json(artist_start, song_start)

    song_start_echonest_id = song_start_result_json['response']['songs'][0]['tracks'][0]['id']
    print song_start_echonest_id

    similar_songs_result = get_similar_song_json(song_start_echonest_id)

    # Find the ending point
    # song_end_result = song.search(title=song_end)[0]
    song_end_result_json = get_song_json(artist_end, song_end)

    return render_template('index.html',
                           title='Music Graph',
                           song_start_query=song_start,
                           song_end_query=song_end,
                           artist_start_query=artist_start,
                           artist_end_query=artist_end,
                           song_start_result=song_start_result_json,
                           song_end_result=song_end_result_json,
                           similar_songs=similar_songs_result)


@app.route('/batchwork')
def create_graph():
    '''
        Batch work to fill the graph
    '''
    # GRAPH_DB.clear()
    # Get a place to start
    song_start = request.args.get('songStart', '')
    artist_start = request.args.get('artistStart', '')
    song_start_result_json = get_song_json(artist_start, song_start)
    song_start_echonest_id = Song(song_start_result_json).song_id

    # Avoid duplicate with index
    song_index = GRAPH_DB.get_or_create_index(neo4j.Node, 'Song')

    # Fill the Queue
    PLAYLIST.put(song_start_echonest_id)
    viewed_songs = []
    count = 0

    # Crawl them all!
    while not PLAYLIST.empty() or count < 2:
        # Get the new id to go through
        current_id = PLAYLIST.get()
        print 'current_id', current_id
        viewed_songs.append(current_id)

        # Create the song object
        current_song = Song(get_song_json_by_id(current_id))

        # Create the current note
        current_node = {
            "song_id": current_song.song_id,
            "title": current_song.title,
            "artist": current_song.artist,
            "spotify_id": current_song.spotify_id}
        # Add node to the index
        song_index.add('Song', current_node['song_id'], current_node)

        # Find the similar songs
        similar_songs = get_similar_song_json(current_id)['response']['songs']

        # For each similar song create a node and a relation
        for similar_song in similar_songs:
            new_node, rel1, rel2 = GRAPH_DB.create(
                {'song_id': similar_song['id'],
                 'title': similar_song['title'],
                 'artist': similar_song['artist_name']},
                (current_node, 'similar', 0),
                (0, 'similar', current_node))

            new_song_json = get_song_json(
                similar_song['artist_name'],
                similar_song['title'])

            print 'new_song_json', new_song_json
            new_song = Song(new_song_json)
            try:
                PLAYLIST.put(new_song.song_id)
                viewed_songs.append(similar_song['id'])
            except:
                pass
        print 'similar_songs', similar_songs
        count += 1

    return render_template('batch.html',
                           count=count,
                           viewed_songs=list(set(viewed_songs)))


@app.route('/test')
def test():
    '''
        Just for personal tests :)
    '''
    # song_start = request.args.get('songStart', '')
    # artist_start = request.args.get('artistStart', '')
    # song_start_result_json = get_song_json(artist_start, song_start)
    # song = Song(song_start_result_json)

    # test_json = get_song_json_by_id(song.id)
    # song = Song(test_json)

    song_id_1 = 1
    song_id_2 = 2

    query = 'START song_1 = node:nodes(track_id = ' + song_id_1 + '),\
                   song_2 = node:nodes(track_id = ' + song_id_2 + ')\
             MATCH p = song_1 -[SIMILAR*2..200]->song_2\
             WHERE NOT(song_1-->song_2) \
             RETURN p'

    data, metadata = cypher.execute(GRAPH_DB, query)

    return render_template('test.html',
                           song_id=song_id_1,
                           song_id_2=song_id_2,
                           data=data,
                           metadata=metadata)
