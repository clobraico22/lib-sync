"""CLI entry point"""
import logging
import time

from analyze_rekordbox_library import analyze_rekordbox_library
from dotenv import load_dotenv
from parser_utils import get_cli_argparser
from rekordbox_library import LibsyncCommand
from sync_rekordbox_to_spotify import sync_rekordbox_to_spotify


def main():
    """
    parse command line args, call other components
    """

    logging.info("running main()")
    load_dotenv()
    parser = get_cli_argparser()
    args = parser.parse_args()
    command = args.command

    if command == LibsyncCommand.SYNC:
        rekordbox_xml_path = args.rekordbox_xml_path
        libsync_db_path = args.libsync_db_path
        create_collection_playlist = args.create_collection_playlist
        make_playlists_public = args.make_playlists_public
        include_loose_songs = args.include_loose_songs

        sync_rekordbox_to_spotify(
            rekordbox_xml_path,
            libsync_db_path,
            create_collection_playlist,
            make_playlists_public,
            include_loose_songs,
        )

    elif command == LibsyncCommand.ANALYZE:
        rekordbox_xml_path = args.rekordbox_xml_path
        include_loose_songs = args.include_loose_songs

        analyze_rekordbox_library(
            rekordbox_xml_path,
            include_loose_songs,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    main()
    logging.info(f"total runtime: {time.time() - start_time} seconds")
