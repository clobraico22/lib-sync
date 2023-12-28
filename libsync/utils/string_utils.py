"""utils for string operations and validation"""

import logging
import re
import string

from utils.constants import ARTIST_LIST_DELIMITERS
from utils.rekordbox_library import RekordboxTrack


def check_if_spotify_url_is_valid(spotify_url: str) -> bool:
    """check for valid spotify url

    Args:
        spotify_url (str): url to spotify track

    Returns:
        bool: true if url is valid, false if not
    """
    logging.info(spotify_url)
    # TODO: implement this (probably with regex)
    return True


def remove_original_mix(song_title: str) -> str:
    trimmed_song_title = re.sub(
        r"[\(\[]original mix[\)\]]", "", song_title, flags=re.IGNORECASE
    )
    return trimmed_song_title


def remove_extended_mix(song_title: str) -> str:
    trimmed_song_title = re.sub(
        r"[\(\[]extended mix[\)\]]", "", song_title, flags=re.IGNORECASE
    )
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
    return [
        artist.strip()
        for artist in re.split(ARTIST_LIST_DELIMITERS, rekordbox_track.artist)
    ]


def strip_punctuation(name: str) -> str:
    return name.translate(str.maketrans("", "", string.punctuation))
