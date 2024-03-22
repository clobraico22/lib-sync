"""sync rekordbox library to spotify playlists"""

import logging

import requests
from analyze.get_rekordbox_library import get_rekordbox_library
from spotify.create_spotify_playlists import create_spotify_playlists
from spotify.get_cached_sync_data import get_cached_sync_data
from spotify.get_spotify_matches import get_spotify_matches
from spotify.save_cached_sync_data import save_cached_sync_data

logger = logging.getLogger("libsync")


def sync_rekordbox_to_spotify(
    rekordbox_xml_path: str,
    create_collection_playlist: bool,
    make_playlists_public: bool,
    include_loose_songs: bool,
    ignore_spotify_search_cache: bool,
    interactive_mode: bool,
    skip_create_spotify_playlists: bool,
) -> None:
    """sync a user's rekordbox playlists to their spotify account

    Args: (see -h for sync command for descriptions)
        rekordbox_xml_path (str): _description_
        create_collection_playlist (bool): _description_
        make_playlists_public (bool): _description_
        include_loose_songs (bool): _description_
        ignore_spotify_search_cache (bool): _description_
        interactive_mode (bool): _description_
        skip_create_spotify_playlists (bool): _description_
    """

    libsync_cache_path = (
        f"data/libsync_sync_cache_{rekordbox_xml_path.replace('/', '_')}.db"
    )
    libsync_song_mapping_csv_path = (
        f"data/libsync_song_mapping_cache_{rekordbox_xml_path.replace('/', '_')}.csv"
    )
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
                f"libsync_cache_path={libsync_cache_path}",
                f"libsync_song_mapping_csv_path={libsync_song_mapping_csv_path}",
            ]
        )
    )
    print("syncing rekordbox => spotify")

    # get cached data
    (
        rekordbox_to_spotify_map,
        playlist_id_map,
        cached_spotify_search_results,
        rb_track_ids_flagged_for_rematch,
    ) = get_cached_sync_data(
        libsync_cache_path,
        libsync_song_mapping_csv_path,
    )

    # get rekordbox db from xml
    rekordbox_library = get_rekordbox_library(rekordbox_xml_path, include_loose_songs)
    logger.debug(f"got rekordbox library: {rekordbox_library}")

    # map songs from the user's rekordbox library onto spotify search results
    (
        rekordbox_to_spotify_map,
        cached_spotify_search_results,
    ) = get_spotify_matches(
        rekordbox_to_spotify_map,
        cached_spotify_search_results,
        rekordbox_library.collection,
        rb_track_ids_flagged_for_rematch,
        ignore_spotify_search_cache,
        interactive_mode,
    )

    # create a playlist in the user's account for each rekordbox playlist
    try:
        create_spotify_playlists(
            playlist_id_map=playlist_id_map,
            rekordbox_playlists=rekordbox_library.playlists,
            rekordbox_to_spotify_map=rekordbox_to_spotify_map,
            create_collection_playlist=create_collection_playlist,
            make_playlists_public=make_playlists_public,
            skip_create_spotify_playlists=skip_create_spotify_playlists,
        )
        logger.debug("done writing playlists")
    except requests.exceptions.ConnectionError as error:
        # TODO: catch this in the function
        logger.exception(error)
        print(
            "error connecting to spotify. fix your internet connection and try again."
        )

    # save cached data
    save_cached_sync_data(
        libsync_cache_path,
        playlist_id_map,
        cached_spotify_search_results,
        libsync_song_mapping_csv_path,
        rekordbox_library,
        rb_track_ids_flagged_for_rematch,
        rekordbox_to_spotify_map,
    )
