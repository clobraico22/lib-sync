"""CLI entry point"""

import logging
import time

from analyze.analyze_rekordbox_library import analyze_rekordbox_library
from dotenv import load_dotenv
from id.get_ids_from_recording import (
    get_track_ids_from_audio_file,
    get_track_ids_from_youtube_link,
)
from spotify.sync_rekordbox_to_spotify import sync_rekordbox_to_spotify
from utils.parser_utils import get_cli_argparser
from utils.rekordbox_library import LibsyncCommand


def main():
    """
    parse command line args, call other components
    """

    logging.info("running main()")
    load_dotenv()
    parser = get_cli_argparser()
    args = parser.parse_args()
    verbose = args.verbose
    if verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.ERROR)

    logging.info("running main()")
    command = args.command

    if command == LibsyncCommand.SYNC:
        rekordbox_xml_path = args.rekordbox_xml_path
        create_collection_playlist = args.create_collection_playlist
        make_playlists_public = args.make_playlists_public
        include_loose_songs = args.include_loose_songs

        sync_rekordbox_to_spotify(
            rekordbox_xml_path,
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

    elif command == LibsyncCommand.ID:
        subcommand = args.subcommand
        if subcommand == LibsyncCommand.FILE:
            recording_audio_file_path = args.recording_audio_file_path
            get_track_ids_from_audio_file(recording_audio_file_path)

        elif subcommand == LibsyncCommand.YOUTUBE:
            youtube_url = args.youtube_url
            get_track_ids_from_youtube_link(youtube_url)


if __name__ == "__main__":
    start_time = time.time()
    main()
    logging.info(f"total runtime: {(time.time() - start_time):.3f} seconds")
