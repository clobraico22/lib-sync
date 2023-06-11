"""parser utils for CLI"""

import argparse

from rekordbox_library import LibsyncCommand


def get_cli_argparser():
    """get parser for CLI arguments"""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="commands",
        help="",
        metavar="",
        required=True,
        dest="command",
    )

    # sync command
    parser_sync = subparsers.add_parser(
        LibsyncCommand.SYNC.value, help="sync your rekordbox playlists to spotify"
    )
    parser_sync.add_argument(
        "--rekordbox_xml_path",
        type=str,
        help="path to rekordbox xml (in rekordbox: file -> Export Collection in xml format)",
        required=True,
    )
    parser_sync.add_argument(
        "--libsync_db_path",
        type=str,
        default="libsync.db",
        help="path to local libsync db file."
        + "This can be a db from a previous run, or a new db will be created if none exists.",
    )
    parser_sync.add_argument(
        "--create_collection_playlist",
        action="store_true",
        help="make a playlist of the total rekordbox collection",
    )
    parser_sync.add_argument(
        "--make_playlists_public",
        action="store_true",
        help="make generated playlists public",
    )
    parser_sync.add_argument(
        "--include_loose_songs",
        action="store_true",
        help="include songs not on any playlists",
    )

    # analyze command
    parser_analyze = subparsers.add_parser(
        LibsyncCommand.ANALYZE.value, help="analyze your rekordbox library"
    )
    parser_analyze.add_argument(
        "--rekordbox_xml_path",
        type=str,
        help="path to rekordbox xml (in rekordbox: file -> Export Collection in xml format)",
        required=True,
    )
    parser_analyze.add_argument(
        "--include_loose_songs",
        action="store_true",
        help="include songs not on any playlists",
    )

    return parser
