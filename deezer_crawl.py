# -*- coding: utf-8 -*-

'''
    Script to crawl Deezer API playlist to create a nice graph :)
'''
import requests
from py2neo import neo4j


DEEZER_BASE_URL = 'http://api.deezer.com/2.0/'
GRAPH_DB = neo4j.GraphDatabaseService(neo4j.DEFAULT_URI)


def get_playlist_json_by_id(playlist_id):
    '''
        From an id retrieve the json of the playlist
    '''
    url = DEEZER_BASE_URL + 'playlist/' + str(playlist_id)
    playlist_result = requests.get(url)

    # If there is an error return an empty dic
    try:
        if playlist_result.json()['error']:
            return {}
    except:
        return playlist_result.json()


def main():
    '''
        Let's crawl!
    '''
    # Delete the database
    # GRAPH_DB.clear()

    playlist_index = GRAPH_DB.get_or_create_index(neo4j.Node, 'Playlist')
    track_index = GRAPH_DB.get_or_create_index(neo4j.Node, 'Track')

    # Go through a few playlist
    for i in range(201, 400):
        print 'iteration', i
        playlist_id = unicode(i)
        playlist_json = get_playlist_json_by_id(playlist_id)
        if playlist_json == {}:
            pass
        else:
            playlist_rating = playlist_json['rating']
            print 'Playlist id', playlist_id
            print 'Playlist rating', playlist_rating

            # Create the playlist_node or look for existing one
            playlist_node = GRAPH_DB.get_or_create_indexed_node(
                'Playlist',
                'playlist_id',
                {'playlist_id': playlist_id})

            playlist_node.set_properties({
                'playlist_id': playlist_id,
                'playlist_rating': playlist_rating})

            playlist_index.add(
                'playlist_id',
                playlist_node['playlist_id'],
                playlist_node)

            # Go through all tracks of the playlist to create the nodes
            for track in playlist_json['tracks']['data']:
                track_id = unicode(track['id'])
                print 'track_id', track_id

                # Try to find an existing node for the track
                track_node = GRAPH_DB.get_or_create_indexed_node(
                    'Track', 'track_id', {'track_id': track_id})

                track_node.set_properties({'track_id': track_id})

                track_index.add('track_id', track_node['track_id'], track_node)

            # Create the relationship between the track with a score
            for track_a in playlist_json['tracks']['data']:
                print 'track_a', track_a
                track_a_node = track_index.get(
                    'track_id',
                    unicode(track_a['id']))[0]

                for track_b in playlist_json['tracks']['data']:
                    track_b_node = track_index.get(
                        'track_id',
                        unicode(track_b['id']))[0]

                    # Get previous score
                    try:
                        old_relation = track_a_node.match_one(
                            'SIMILAR',
                            track_b_node)
                        old_score = old_relation.get_properties(
                            old_relation)['score']
                        GRAPH_DB.delete(old_relation)
                    except:
                        old_score = 0

                    # Create the new relationship
                    relation, = GRAPH_DB.create(
                        (track_a_node, 'SIMILAR', track_b_node))

                    # Add a score to the relation
                    new_score = old_score + playlist_rating**2
                    relation.set_properties({'score': new_score})

    return

if __name__ == "__main__":
    main()
