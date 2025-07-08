"""utils for string operations and validation"""

import re
import string
import time
from pathlib import Path

import spotipy.client
from colorama import Fore, Style

from libsync.utils.constants import ARTIST_LIST_DELIMITERS, SPOTIFY_TRACK_URI_PREFIX
from libsync.utils.rekordbox_library import RekordboxTrack

# Use ~/.libsync/data for all data storage
LIBSYNC_DATA_DIR = Path.home() / ".libsync" / "data"
LIBSYNC_LOGS_DIR = LIBSYNC_DATA_DIR / "logs"

# Create directories if they don't exist
LIBSYNC_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Create log file
log_filename = f"libsync_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
output_file = open(LIBSYNC_LOGS_DIR / log_filename, "w")


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


def get_spotify_uri_from_id(spotify_track_id: str) -> str:
    return SPOTIFY_TRACK_URI_PREFIX + spotify_track_id


def get_spotify_id_from_uri(spotify_track_uri: str) -> str:
    assert is_spotify_uri(spotify_track_uri)
    return spotify_track_uri[len(SPOTIFY_TRACK_URI_PREFIX) :]


def is_spotify_uri(value: str) -> bool:
    return value.startswith(SPOTIFY_TRACK_URI_PREFIX)


def remove_original_mix(song_title: str) -> str:
    song_title = re.sub(r"[\(\[]original mix[\)\]]", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"[\(\[]original version[\)\]]", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"[\(\[]original[\)\]]", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"original mix", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"original version", "", song_title, flags=re.IGNORECASE)
    return song_title


def remove_extended_mix(song_title: str) -> str:
    song_title = re.sub(r"[\(\[]extended mix[\)\]]", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"extended mix", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"[\(\[]extended version[\)\]]", "", song_title, flags=re.IGNORECASE)
    song_title = re.sub(r"extended version", "", song_title, flags=re.IGNORECASE)
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
    return [artist.strip() for artist in re.split(ARTIST_LIST_DELIMITERS, rb_track.artist)]


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


def generate_spotify_playlist_name(rb_playlist_name: str) -> str:
    return f"[ls] {rb_playlist_name}"


def print_libsync_status(status_message, level=0, arrow_color=Fore.BLUE, text_color=Fore.WHITE):
    message = (
        "  " * (level - 1)
        + ((arrow_color + "==> " + Style.RESET_ALL) if level >= 1 else "")
        + Style.BRIGHT
        + text_color
        + status_message
        + Style.RESET_ALL
    )
    print(message)
    # Remove ANSI color codes and escape sequences before writing to file
    clean_message = re.sub(r"\033\[\d+(;\d+)*m", "", message)
    output_file.write(clean_message + "\n")


def log_and_print(message):
    print(message)
    output_file.write(message + "\n")


def print_libsync_status_success(status_message, level=0):
    return print_libsync_status(
        status_message, level, arrow_color=Fore.GREEN, text_color=Fore.GREEN
    )


def print_libsync_status_error(error_message, level=0):
    return print_libsync_status(error_message, level, arrow_color=Fore.RED, text_color=Fore.WHITE)
