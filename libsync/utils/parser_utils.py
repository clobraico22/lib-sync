"""parser utils for CLI"""

import argparse

from utils.rekordbox_library import LibsyncCommand


def get_cli_argparser():
    """get parser for CLI arguments"""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase output verbosity"
    )

    subparsers = parser.add_subparsers(
        title="commands",
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

    # id command
    parser_id = subparsers.add_parser(
        LibsyncCommand.ID.value, help="ID tracks from an audio file or youtube link"
    )
    subsubparsers = parser_id.add_subparsers(
        title="subcommands",
        required=True,
        dest="subcommand",
    )

    # file subcommand
    parser_file = subsubparsers.add_parser(
        LibsyncCommand.FILE.value, help="ID tracks from an audio file"
    )
    parser_file.add_argument(
        "--recording_audio_file_path",
        type=str,
        help="path to audio recording to ID",
        required=True,
    )

    # youtube subcommand
    parser_youtube = subsubparsers.add_parser(
        LibsyncCommand.YOUTUBE.value, help="ID tracks from a youtube link"
    )
    parser_youtube.add_argument(
        "--youtube_url",
        type=str,
        help="URL of youtube video to ID",
        required=True,
    )

    return parser
