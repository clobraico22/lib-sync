"""CLI entry point"""
import argparse
import logging
import pickle

from create_spotify_playlists import create_spotify_playlists
from dotenv import load_dotenv
from get_rekordbox_library import get_rekordbox_library
from get_spotify_matches import get_spotify_matches


def main():
    """
    parse command line args, call other components
    """
    load_dotenv()
    parser = argparse.ArgumentParser(description="description here")
    parser.add_argument(
        "--rekordbox_xml_path",
        type=str,
        help="path to rekordbox db [add more help here]",
    )
    parser.add_argument(
        "--libsync_db_path",
        type=str,
        help="path to local libsync db file."
        + "This can be a db from a previous run, or a new db will be created if none exists.",
    )
    parser.add_argument(
        "--create_collection_playlist",
        action=argparse.BooleanOptionalAction,
        help="make a playlist of the total rekordbox collection",
    )
    parser.add_argument(
        "--make_playlists_public",
        action=argparse.BooleanOptionalAction,
        help="make generated playlists public",
    )
    args = parser.parse_args()
    rekordbox_xml_path = args.rekordbox_xml_path
    libsync_db_path = args.libsync_db_path
    create_collection_playlist = args.create_collection_playlist
    make_playlists_public = args.make_playlists_public

    rekordbox_to_spotify_map = {}
    playlist_id_map = {}

    # get libsync db from file
    try:
        with open(libsync_db_path, "rb") as handle:
            database = pickle.load(handle)
            rekordbox_to_spotify_map, playlist_id_map = (
                database["rekordbox_to_spotify_map"],
                database["playlist_id_map"],
            )
    except FileNotFoundError as error:
        logging.error(error)
        print(
            f"couldn't find database: '{rekordbox_xml_path}'. creating new database from scratch"
        )
    except KeyError as error:
        logging.error(error)
        print(
            f"database is an incorrect format: '{rekordbox_xml_path}'. creating new database from scratch"
        )
        rekordbox_to_spotify_map = {}
        playlist_id_map = {}

    # get rekordbox db from xml
    try:
        rekordbox_library = get_rekordbox_library(rekordbox_xml_path)
        logging.debug(f"got rekordbox library: {rekordbox_library}")
    except FileNotFoundError as error:
        logging.error(error)
        print(f"couldn't find '{rekordbox_xml_path}'. check the path and try again")
        return
    except TypeError as error:
        logging.error(error)
        print(
            f"the file at '{rekordbox_xml_path}' is the wrong format. try exporting again"
        )
        return

    # map songs from the user's rekordbox library onto spotify search results
    get_spotify_matches(rekordbox_to_spotify_map, rekordbox_library.collection)

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
            },
            handle,
            protocol=pickle.HIGHEST_PROTOCOL,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("starting up lib-sync")

    main()
