"""CLI entry point"""

import logging
import time

from dotenv import load_dotenv

from libsync.analyze.analyze_rekordbox_library import analyze_rekordbox_library
from libsync.id.get_ids_from_recording import (
    get_track_ids_from_audio_file,
    get_track_ids_from_youtube_link,
)
from libsync.spotify.sync_rekordbox_to_spotify import sync_rekordbox_to_spotify
from libsync.utils.parser_utils import get_cli_argparser
from libsync.utils.rekordbox_library import LibsyncCommand


def setup_logger(logger):
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


def cli():
    """
    parse command line args, call other components
    """

    logger = logging.getLogger("libsync")
    setup_logger(logger)
    load_dotenv()

    start_time = time.time()
    parser = get_cli_argparser()
    args = parser.parse_args()

    verbose = args.verbose
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.ERROR)

    logger.info("running cli()")
    command = args.command

    if command == LibsyncCommand.SYNC:
        sync_rekordbox_to_spotify(
            rekordbox_xml_path=args.rekordbox_xml_path,
            create_collection_playlist=args.create_collection_playlist,
            make_playlists_public=args.make_playlists_public,
            include_loose_songs=args.include_loose_songs,
            ignore_spotify_search_cache=args.ignore_spotify_search_cache,
            interactive_mode=args.interactive_mode,
            interactive_mode_pending_tracks=args.interactive_mode_pending_tracks,
            skip_spotify_playlist_sync=args.skip_spotify_playlist_sync,
            dry_run=args.dry_run,
            use_cached_spotify_playlist_data=args.use_cached_spotify_playlist_data,
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

    logger.info(f"total runtime: {(time.time() - start_time):.3f} seconds")
