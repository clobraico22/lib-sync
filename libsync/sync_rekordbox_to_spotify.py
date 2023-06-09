"""CLI entry point"""
import logging
import pickle

from create_spotify_playlists import create_spotify_playlists
from get_rekordbox_library import get_rekordbox_library
from get_spotify_matches import get_spotify_matches


def sync_rekordbox_to_spotify(
    rekordbox_xml_path: str,
    libsync_db_path: str,
    create_collection_playlist: bool,
    make_playlists_public: bool,
    include_loose_songs: bool,
):
    """sync a user's rekordbox playlists to their spotify account

    Args:
        rekordbox_xml_path (str): _description_
        libsync_db_path (str): _description_
        create_collection_playlist (bool): _description_
        make_playlists_public (bool): _description_
        include_loose_songs (bool): _description_
    """

    logging.info(
        "running sync_rekordbox_to_spotify.py with args: "
        + f"rekordbox_xml_path={rekordbox_xml_path}, "
        + f"libsync_db_path={libsync_db_path}, "
        + f"create_collection_playlist={create_collection_playlist}, "
        + f"make_playlists_public={make_playlists_public}, "
        + f"include_loose_songs={include_loose_songs}"
    )

    rekordbox_to_spotify_map = {}
    playlist_id_map = {}

    # get libsync db from file
    try:
        with open(libsync_db_path, "rb") as handle:
            database = pickle.load(handle)
            (
                rekordbox_to_spotify_map,
                playlist_id_map,
                cached_search_search_results,
            ) = (
                database["rekordbox_to_spotify_map"],
                database["playlist_id_map"],
                database["cached_search_search_results"],
            )
    except FileNotFoundError as error:
        logging.exception(error)
        print(
            f"couldn't find database: '{rekordbox_xml_path}'. creating new database from scratch"
        )
    except KeyError as error:
        logging.exception(error)
        print(
            f"database is an incorrect format: '{rekordbox_xml_path}'. creating new database from scratch"
        )
        rekordbox_to_spotify_map = {}
        playlist_id_map = {}
        cached_search_search_results = {}

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
    create_spotify_playlists(
        playlist_id_map=playlist_id_map,
        rekordbox_playlists=rekordbox_library.playlists,
        rekordbox_to_spotify_map=rekordbox_to_spotify_map,
        create_collection_playlist=create_collection_playlist,
        make_playlists_public=make_playlists_public,
    )

    with open(libsync_db_path, "wb") as handle:
        pickle.dump(
            {
                "rekordbox_to_spotify_map": rekordbox_to_spotify_map,
                "playlist_id_map": playlist_id_map,
                "cached_search_search_results": cached_search_search_results,
            },
            handle,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
