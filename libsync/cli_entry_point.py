import argparse
import logging

from create_spotify_playlists import create_spotify_playlists
from get_rekordbox_library import get_rekordbox_library
from get_spotify_matches import get_spotify_matches


def main():
    parser = argparse.ArgumentParser(description="description here")
    parser.add_argument(
        "--rekordbox_xml_path",
        type=str,
        help="path to rekordbox db [add more help here]",
    )
    # TODO: maybe add a path to the user's local db that remembers some sync prefs
    parser.add_argument(
        "--spotify_username",
        type=str,
        help="spotify username [add other spotify auth]",
    )
    args = parser.parse_args()
    rekordbox_xml_path = args.rekordbox_xml_path
    spotify_username = args.spotify_username

    # this library will be a python representation of the rekordbox db structure
    try:
        rekordbox_library = get_rekordbox_library(rekordbox_xml_path)
        logging.info(f"got rekordbox library: {rekordbox_library}")
    except FileNotFoundError as e:
        logging.error(e)
        print(f"couldn't find '{rekordbox_xml_path}'. check the path and try again")
        return
    except TypeError as e:
        logging.error(e)
        print(
            f"the file at '{rekordbox_xml_path}' is the wrong format. try exporting again"
        )
        return

    # this map will map songs from the user's rekordbox library onto spotify search results
    rekordbox_to_spotify_map = get_spotify_matches(rekordbox_library.collection)

    # this will create playlists in the user's account corresponding to
    create_spotify_playlists(
        rekordbox_library.playlists, rekordbox_to_spotify_map, spotify_username
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("starting up lib-sync")

    main()