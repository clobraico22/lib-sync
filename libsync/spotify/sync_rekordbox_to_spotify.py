"""sync rekordbox library to spotify playlists"""

import logging
import pickle
from pprint import pprint

import requests
from analyze.get_rekordbox_library import get_rekordbox_library
from spotify.create_spotify_playlists import create_spotify_playlists
from spotify.get_spotify_matches import get_spotify_matches


def sync_rekordbox_to_spotify(
    rekordbox_xml_path: str,
    create_collection_playlist: bool,
    make_playlists_public: bool,
    include_loose_songs: bool,
) -> None:
    """sync a user's rekordbox playlists to their spotify account

    Args:
        rekordbox_xml_path (str): _description_
        create_collection_playlist (bool): _description_
        make_playlists_public (bool): _description_
        include_loose_songs (bool): _description_
    """

    libsync_cache_path = f"data/{rekordbox_xml_path.replace('/', '_')}_libsync_sync_cache.db"
    logging.info(
        "running sync_rekordbox_to_spotify.py with args: "
        + f"rekordbox_xml_path={rekordbox_xml_path}, "
        + f"libsync_cache_path={libsync_cache_path}, "
        + f"create_collection_playlist={create_collection_playlist}, "
        + f"make_playlists_public={make_playlists_public}, "
        + f"include_loose_songs={include_loose_songs}"
    )

    rekordbox_to_spotify_map = {}
    playlist_id_map = {}
    cached_search_search_results = {}

    # get libsync cache from file
    try:
        with open(libsync_cache_path, "rb") as handle:
            cache = pickle.load(handle)
            (
                rekordbox_to_spotify_map,
                playlist_id_map,
                cached_search_search_results,
            ) = (
                cache["rekordbox_to_spotify_map"],
                cache["playlist_id_map"],
                cache["cached_search_search_results"],
            )
            pprint(rekordbox_to_spotify_map)
            # TODO: store rekordbox_to_spotify_map in a csv for better visibility and manual editing
    except FileNotFoundError as error:
        logging.exception(error)
        print(f"no cache found. creating cache at '{libsync_cache_path}'.")
    except KeyError as error:
        logging.exception(error)
        print(f"error parsing cache at '{libsync_cache_path}'. clearing cache.")
        # TODO actually clear cache, also centralize this duplicated caching logic

    # get rekordbox db from xml
    try:
        rekordbox_library = get_rekordbox_library(rekordbox_xml_path, include_loose_songs)
        logging.debug(f"got rekordbox library: {rekordbox_library}")
    except FileNotFoundError as error:
        logging.exception(error)
        print(f"couldn't find '{rekordbox_xml_path}'. check the path and try again")
        return
    except TypeError as error:
        logging.exception(error)
        print(f"the file at '{rekordbox_xml_path}' is the wrong format. try exporting again")
        return

    # map songs from the user's rekordbox library onto spotify search results
    get_spotify_matches(
        rekordbox_to_spotify_map,
        cached_search_search_results,
        rekordbox_library.collection,
    )

    # create a playlist in the user's account for each rekordbox playlist
    try:
        create_spotify_playlists(
            playlist_id_map=playlist_id_map,
            rekordbox_playlists=rekordbox_library.playlists,
            rekordbox_to_spotify_map=rekordbox_to_spotify_map,
            create_collection_playlist=create_collection_playlist,
            make_playlists_public=make_playlists_public,
        )
        logging.debug(f"succeeded in writing ## playlists")
    except requests.exceptions.ConnectionError as error:
        # maybe catch this at a lower level
        logging.exception(error)
        print(f"error connecting to spotify. fix your internet connection and try again.")

    with open(libsync_cache_path, "wb") as handle:
        pickle.dump(
            {
                "rekordbox_to_spotify_map": rekordbox_to_spotify_map,
                "playlist_id_map": playlist_id_map,
                "cached_search_search_results": cached_search_search_results,
            },
            handle,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
