"""sync rekordbox library to spotify playlists"""

import logging

import requests

from libsync.analyze.get_rekordbox_library import get_rekordbox_library
from libsync.db import db_read_operations
from libsync.spotify.get_spotify_matches import get_spotify_matches
from libsync.spotify.sync_spotify_playlists import sync_spotify_playlists
from libsync.utils import string_utils

logger = logging.getLogger("libsync")


def sync_rekordbox_to_spotify(
    rekordbox_xml_path: str,
    create_collection_playlist: bool,
    make_playlists_public: bool,
    include_loose_songs: bool,
    ignore_spotify_search_cache: bool,
    interactive_mode: bool,
    interactive_mode_pending_tracks: bool,
    skip_spotify_playlist_sync: bool,
    dry_run: bool,
    use_cached_spotify_playlist_data: bool,
) -> None:
    """sync a user's rekordbox playlists to their spotify account"""

    logger.debug(
        "running sync_rekordbox_to_spotify.py with args: "
        + ", ".join(
            [
                f"rekordbox_xml_path={rekordbox_xml_path}",
                f"create_collection_playlist={create_collection_playlist}",
                f"make_playlists_public={make_playlists_public}",
                f"include_loose_songs={include_loose_songs}",
                f"ignore_spotify_search_cache={ignore_spotify_search_cache}",
                f"interactive_mode={interactive_mode}",
                f"dry_run={dry_run}",
                f"use_cached_spotify_playlist_data={use_cached_spotify_playlist_data}",
            ]
        )
    )
    string_utils.print_libsync_status("Syncing your Rekordbox with Spotify", level=0)

    # get cached data
    (
        rekordbox_to_spotify_map,
        rb_track_ids_flagged_for_rematch,
    ) = db_read_operations.get_cached_sync_data(rekordbox_xml_path)

    pending_tracks_spotify_to_rekordbox = (
        db_read_operations.get_pending_tracks_spotify_to_rekordbox(rekordbox_xml_path)
    )

    # get rekordbox db from xml
    rekordbox_library = get_rekordbox_library(rekordbox_xml_path, create_collection_playlist)

    # this muddies up the logs quite a bit - add it back if needed
    # logger.debug(f"got rekordbox library: {rekordbox_library}")

    # map songs from the user's rekordbox library onto spotify search results
    rekordbox_to_spotify_map = get_spotify_matches(
        rekordbox_to_spotify_map,
        rekordbox_library,
        rb_track_ids_flagged_for_rematch,
        pending_tracks_spotify_to_rekordbox,
        ignore_spotify_search_cache,
        interactive_mode,
        interactive_mode_pending_tracks,
    )

    # create a playlist in the user's account for each rekordbox playlist
    if skip_spotify_playlist_sync:
        string_utils.print_libsync_status_error("Skipping Spotify playlist sync", level=1)

    else:
        try:
            sync_spotify_playlists(
                rekordbox_xml_path=rekordbox_xml_path,
                rekordbox_playlists=rekordbox_library.playlists,
                rekordbox_to_spotify_map=rekordbox_to_spotify_map,
                make_playlists_public=make_playlists_public,
                dry_run=dry_run,
                use_cached_spotify_playlist_data=use_cached_spotify_playlist_data,
                collection=rekordbox_library.collection,
            )
            logger.debug("done writing playlists")

        except (ConnectionError, requests.exceptions.ConnectionError) as e:
            logger.error(e)
            string_utils.print_libsync_status_error(
                "Failed to connect to Spotify. Please try again later.", level=1
            )
            exit()

    string_utils.print_libsync_status_success("Sync complete!", level=0)
