"""utils for string operations and validation"""

import re
import string

import spotipy.client
from utils.constants import ARTIST_LIST_DELIMITERS
from utils.rekordbox_library import RekordboxTrack


def get_spotify_uri_from_url(spotify_url: str) -> str:
    """parse spotify url

    Args:
        spotify_url (str): _description_

    Returns:
        str: _description_
    """
    spotify = spotipy.Spotify()
    spotify_uri = spotify._get_uri(type="track", id=spotify_url)
    return spotify_uri


def remove_original_mix(song_title: str) -> str:
    trimmed_song_title = re.sub(r"[\(\[]original mix[\)\]]", "", song_title, flags=re.IGNORECASE)
    return trimmed_song_title


def remove_extended_mix(song_title: str) -> str:
    trimmed_song_title = re.sub(r"[\(\[]extended mix[\)\]]", "", song_title, flags=re.IGNORECASE)
    return trimmed_song_title


def get_name_varieties_from_track_name(name: str):
    return set(
        title.strip()
        for title in [
            name,
            remove_original_mix(name),
            remove_extended_mix(name),
        ]
    )


def get_artists_from_rekordbox_track(
    rekordbox_track: RekordboxTrack,
):
    return [artist.strip() for artist in re.split(ARTIST_LIST_DELIMITERS, rekordbox_track.artist)]


def strip_punctuation(name: str) -> str:
    return name.translate(str.maketrans("", "", string.punctuation))
