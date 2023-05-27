import logging
import pprint
import urllib.parse

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

from rekordbox_library import RekordboxCollection
from rekordbox_library import RekordboxTrack


def get_spotify_matches(rekordbox_collection: RekordboxCollection) -> dict[str, str]:
    """attempt to map all songs in rekordbox library to spotify uris

    Args:
        rekordbox_collection (RekordboxCollection): set of songs

    Returns:
        dict[str, str]: map from rekordbox song ID to spotify URI
    """

    logging.info(
        f"running get_spotify_matches with rekordbox_collection:\n{pprint.pformat(rekordbox_collection)}"
    )

    match_map = {}
    for rb_track in rekordbox_collection:
        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        spotify_search_track_results = search_spotify_for_rekordbox_track(
            spotify,
            rb_track,
        )
        list_of_spotify_tracks = spotify_search_track_results["items"] # this will give us the first page of results
        best_match = find_best_track_match(rb_track,list_of_spotify_tracks)
        match_map[rb_track.id] = best_match['uri'] # NOTE: consider returning the entire dictionary rather than just uri

    return match_map


load_dotenv()


def search_spotify_for_rekordbox_track(spotify_client: spotipy.Spotify,rekordbox_track: RekordboxTrack,*,market: str="US",)->dict[str,list]:
    """search spotify for a given rekordbox track

    Args:
        spotify_client (spotipy.Spotify): spotipy client for using spotify api
        rekordbox_track (RekordboxTrack): reack object with members 'name','artist','album'
        market (str, optional): An ISO 3166-1 alpha-2 country code or the string from_token. Defaults to "US".

    Raises:
        ValueError: if all of the fields ('name','artist','album') for rekordbox_track are None

    Returns:
        search_result_tracks (dict[str,list]): dictionary of track results from search. 'items' key will return track information for first page of results
    """
    filter_map = {
        "artist": rekordbox_track.artist,
        "track": rekordbox_track.name,
        "album": rekordbox_track.album,
    }
    if all(value is None for value in filter_map.values()):
        raise ValueError("The given rekordbox track is empty. At least one of the following fields must not be None: 'artist', 'track', 'album'")
    filter_list = [f"{key}:{filter_map[key]}" for key in filter_map]
    query = urllib.parse.quote(" ".join(filter_list))
    search_result_tracks = spotify_client.search(q=query, type="track", market="US")["tracks"]
    return search_result_tracks

def find_best_track_match(rekordbox_track: RekordboxTrack,list_of_spotify_tracks: list):
    logging.info(
        f"running find_best_track_match with rekordbox_track:\n{pprint.pformat(rekordbox_track)}"
    )
    # TODO: Implement algo to find best track
    return list_of_spotify_tracks[0]