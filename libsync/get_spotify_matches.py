import logging
import pprint
import urllib.parse

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

from rekordbox_library import RekordboxCollection


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

    return


load_dotenv()


def search_spotify(
    spotify_client: spotipy.Spotify,
    filter_map: dict[str, str] = None,
    keyword_str: str = None,
    type="track",
):
    # TODO: create the filter map using the a rekordbox track type (waiting on josh)
    filter_list = [f"{key}:{filter_map[key]}" for key in filter_map]
    if keyword_str is not None:
        filter_list.insert(0, keyword_str)
    query = urllib.parse.quote(" ".join(filter_list))
    return spotify_client.search(q=query, type="track", market="US")


def test_search_spotify(artist="Fisher", track="Losing it"):
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    filter_map = {"artist": artist, "track": track}
    results = search_spotify(spotify, filter_map)
    tracks = results["tracks"]
    list_of_tracks = results["tracks"]["items"]
    for track in list_of_tracks:
        print(track["name"], track["uri"])


if __name__ == "__main__":
    test_search_spotify()
