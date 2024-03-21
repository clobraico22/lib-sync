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
    song_title = re.sub(
        r"[\(\[]original mix[\)\]]", "", song_title, flags=re.IGNORECASE
    )
    song_title = re.sub(
        r"[\(\[]original version[\)\]]", "", song_title, flags=re.IGNORECASE
    )
    song_title = re.sub(r"[\(\[]original[\)\]]", "", song_title, flags=re.IGNORECASE)
    return song_title


def remove_extended_mix(song_title: str) -> str:
    song_title = re.sub(
        r"[\(\[]extended mix[\)\]]", "", song_title, flags=re.IGNORECASE
    )
    # TODO: do something about case sensitivity throughout the app
    song_title = re.sub(r"extended mix", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"extended", "", song_title, flags=re.IGNORECASE)
    return song_title


def remove_radio_mix(song_title: str) -> str:
    song_title = re.sub(r"[\(\[]radio mix[\)\]]", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"[\(\[]radio edit[\)\]]", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"radio mix", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"radio edit", "", song_title, flags=re.IGNORECASE)
    return song_title


def remove_bootleg(song_title: str) -> str:
    song_title = re.sub(r"[\(\[]bootleg[\)\]]", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"bootleg", "", song_title, flags=re.IGNORECASE)
    return song_title


def remove_suffixes(song_title: str) -> str:
    song_title = remove_original_mix(song_title)
    song_title = remove_extended_mix(song_title)
    song_title = remove_radio_mix(song_title)
    song_title = remove_bootleg(song_title)
    return song_title


def get_name_varieties_from_track_name(name: str):
    return list(set(title.strip() for title in [name, remove_suffixes(name)]))


def get_artists_from_rb_track(
    rb_track: RekordboxTrack,
):
    return [
        artist.strip() for artist in re.split(ARTIST_LIST_DELIMITERS, rb_track.artist)
    ]


def strip_punctuation(name: str) -> str:
    return name.translate(str.maketrans("", "", string.punctuation))


def pretty_print_spotify_track(track: object, include_url: bool = False):
    if track["artists"] is None or track["name"] is None:
        return "invalid spotify track"

    return (
        ((track["external_urls"]["spotify"][8:] + "  ") if include_url else "")
        + ", ".join([artist["name"] for artist in track["artists"]])
        + " - "
        + track["name"]
    )
