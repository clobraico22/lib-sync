"""CLI entry point"""

import argparse
import logging

from create_spotify_playlists import create_spotify_playlists
from get_rekordbox_library import get_rekordbox_library
from get_spotify_matches import get_spotify_matches
from dotenv import load_dotenv

# from spotipy.util import prompt_for_user_token


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
        "--spotify_username",
        type=str,
        help="spotify username [add other spotify auth]",
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
    spotify_username = args.spotify_username
    create_collection_playlist = args.create_collection_playlist
    make_playlists_public = args.make_playlists_public

    # this library will be a python representation of the rekordbox db structure
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

    # token = prompt_for_user_token(
    #     username=spotify_username,
    #     scope=["user-library-read", "playlist-modify-private"],
    # )
    # logging.info(f"got spotify token: {token}")

    # this map will map songs from the user's rekordbox library onto spotify search results
    rekordbox_to_spotify_map = get_spotify_matches(rekordbox_library.collection)

    # this will create playlists in the user's account corresponding to
    # create_spotify_playlists(
    #     rekordbox_library.playlists,
    #     rekordbox_to_spotify_map,
    #     spotify_username,
    #     create_collection_playlist=create_collection_playlist,
    #     make_playlists_public=make_playlists_public,
    # )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("starting up lib-sync")

    main()
