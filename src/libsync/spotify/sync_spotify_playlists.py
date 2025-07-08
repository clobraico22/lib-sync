"""contains sync_spotify_playlists function and helpers"""

import logging
import os
import pickle
import time

from libsync.db import db_read_operations, db_write_operations
from libsync.spotify import spotify_api_utils
from libsync.spotify.spotify_auth import SpotifyAuthManager
from libsync.utils import constants, string_utils
from libsync.utils.rekordbox_library import (
    PlaylistName,
    RekordboxCollection,
    RekordboxPlaylist,
    SpotifyPlaylistId,
    SpotifyURI,
)
from libsync.utils.string_utils import log_and_print

logger = logging.getLogger("libsync")


def fetch_spotify_playlists(
    playlist_id_map: dict[PlaylistName, SpotifyPlaylistId],
) -> tuple[dict[str, list[str]], set[str]]:
    """
    Fetches Spotify playlists and related information.

    Args:
        rekordbox_xml_path (str): Path to the Rekordbox XML file.
        rekordbox_playlists (list[RekordboxPlaylist]): List of Rekordbox playlists.

    Returns:
        tuple: Contains the following elements:
            - libsync_owned_spotify_playlists (dict[str, list[str]]): Details of Spotify playlists owned by libsync.
            - all_user_spotify_playlists (set[str]): Set of all user's Spotify playlist IDs.
    """
    string_utils.print_libsync_status("Fetching your Spotify playlists", level=1)
    libsync_owned_spotify_playlists = spotify_api_utils.get_user_playlists_details(
        playlist_id_map.values()
    )
    string_utils.print_libsync_status("Fetching all of your Spotify playlists", level=1)
    all_user_spotify_playlists = spotify_api_utils.get_all_user_playlists_set()
    string_utils.print_libsync_status_success("Done", level=1)

    return (
        libsync_owned_spotify_playlists,
        all_user_spotify_playlists,
    )


def sync_spotify_playlists(
    rekordbox_xml_path: str,
    rekordbox_playlists: list[RekordboxPlaylist],
    rekordbox_to_spotify_map: dict[str, str],
    make_playlists_public: bool,
    dry_run: bool,
    use_cached_spotify_playlist_data: bool,
    collection: RekordboxCollection,
) -> dict[str, str]:
    """creates playlists in the user's account with the matched songs

    Args:
        rekordbox_xml_path (str): xml path used for this run -
          this will be used to determine cache and csv paths
        rekordbox_playlists (list[RekordboxPlaylist]): user's playlists from rekordbox
            (list of rekordbox track IDs)
        rekordbox_to_spotify_map (dict[str, str]): mapping from rekordbox track IDs to spotify URIs
        make_playlists_public (bool): determines if playlist will be made public or not
        dry_run (bool): don't make playlists (skip for debugging or local matching)
        use_cached_spotify_playlist_data (bool): use cached spotify playlist data

    Returns:
        dict[str, str]: reference to playlist_id_map argument which is modified in place
    """

    # logger.debug(
    #     "running sync_spotify_playlists with\n"
    #     + f"rekordbox_playlists:\n{pprint.pformat(rekordbox_playlists)},\n"
    #     + f"rekordbox_to_spotify_map:\n{pprint.pformat(rekordbox_to_spotify_map)}"
    # )

    playlist_id_map = db_read_operations.get_playlist_id_map(rekordbox_xml_path)
    rekordbox_playlists_set = {rb_playlist.name for rb_playlist in rekordbox_playlists}
    libsync_owned_spotify_playlists = {}
    all_user_spotify_playlists = set()

    if use_cached_spotify_playlist_data:
        string_utils.print_libsync_status("Using cached Spotify playlist data", level=1)
        pickle_dir = os.path.join(os.path.dirname(rekordbox_xml_path), "test_data")
        pickle_path = os.path.join(pickle_dir, "spotify_playlists_test_data.pickle")

        try:
            with open(pickle_path, "rb") as f:
                test_data = pickle.load(f)

            libsync_owned_spotify_playlists = test_data["libsync_owned_spotify_playlists"]
            all_user_spotify_playlists = test_data["all_user_spotify_playlists"]

            string_utils.print_libsync_status_success("Loaded cached data successfully", level=1)
        except (FileNotFoundError, KeyError) as e:
            logger.error(f"Error loading cached data: {e}")
            string_utils.print_libsync_status(
                "Failed to load cached data. Fetching fresh data.", level=1
            )
            use_cached_spotify_playlist_data = False

    if not use_cached_spotify_playlist_data:
        string_utils.print_libsync_status("Fetching Spotify playlist data", level=1)
        (
            libsync_owned_spotify_playlists,
            all_user_spotify_playlists,
        ) = fetch_spotify_playlists(playlist_id_map)

        # Save variables to pickle file for future use
        test_data = {
            "libsync_owned_spotify_playlists": libsync_owned_spotify_playlists,
            "all_user_spotify_playlists": all_user_spotify_playlists,
        }

        pickle_dir = os.path.join(os.path.dirname(rekordbox_xml_path), "test_data")
        os.makedirs(pickle_dir, exist_ok=True)
        pickle_path = os.path.join(pickle_dir, "spotify_playlists_test_data.pickle")
        pickle_path_backup = os.path.join(
            pickle_dir,
            f"spotify_playlists_test_data_{time.strftime('%Y.%m.%d_%H.%M.%S')}.pickle",
        )

        with open(pickle_path, "wb") as f:
            pickle.dump(test_data, f)

        with open(pickle_path_backup, "wb") as f:
            pickle.dump(test_data, f)

        logger.info(f"Test data saved to {pickle_path}")

    # delete invalid entries from playlist_id_map:
    #   playlist deleted from rekordbox, or playlist deleted from spotify
    keys_to_delete_from_mapping = set()
    spotify_playlist_ids_to_delete = set()
    for rekordbox_playlist_name, spotify_playlist_id in playlist_id_map.items():
        rb_playlist_valid = rekordbox_playlist_name in rekordbox_playlists_set
        sp_playlist_valid = spotify_playlist_id in all_user_spotify_playlists
        if sp_playlist_valid and not rb_playlist_valid:
            keys_to_delete_from_mapping.add(rekordbox_playlist_name)
            spotify_playlist_ids_to_delete.add(spotify_playlist_id)
        if not sp_playlist_valid:
            keys_to_delete_from_mapping.add(rekordbox_playlist_name)

    for key in keys_to_delete_from_mapping:
        logger.debug(f"deleting playlist mapping for name: {key}")
        del playlist_id_map[key]

    spotify = SpotifyAuthManager.get_spotify_client()

    if len(spotify_playlist_ids_to_delete) < 1:
        string_utils.print_libsync_status("No Spotify playlists to delete", level=1)
    else:
        string_utils.print_libsync_status("Deleting old Spotify playlists", level=1)

        for playlist_id in spotify_playlist_ids_to_delete:
            logger.debug(f"deleting playlist with id: {playlist_id}")
            # "unfollowing" your own playlist is the same as deleting it from the spotify UI.
            # it's impossible to actually "delete" a spotify playlist.
            if not dry_run:
                spotify.current_user_unfollow_playlist(playlist_id)

        string_utils.print_libsync_status_success("Done", level=1)

    playlist_names_to_create = [
        rb_playlist.name
        for rb_playlist in rekordbox_playlists
        if rb_playlist.name not in playlist_id_map
    ]
    logger.debug(f"playlist_names_to_create: {playlist_names_to_create}")

    if len(playlist_names_to_create) < 1:
        string_utils.print_libsync_status("No Spotify playlists to create", level=1)
    else:
        if not dry_run:
            string_utils.print_libsync_status("Creating new Spotify playlists", level=1)

            # TODO: parallelize this if necessary (see spotify_api_utils), shouldn't be a very hot path.
            for rb_playlist_name in playlist_names_to_create:
                playlist_create_result = spotify.user_playlist_create(
                    user=SpotifyAuthManager.get_user_id(),
                    name=string_utils.generate_spotify_playlist_name(rb_playlist_name),
                    # NOTE: private playlists don't work! read here:
                    # https://community.spotify.com/t5/Spotify-for-Developers/Api-to-create-a-private-playlist-doesn-t-work/td-p/5407807
                    public=make_playlists_public,
                    description="Automatically generated by libsync",
                )
                logger.info(
                    f"created spotify playlist: {playlist_create_result['name']}"
                    + f" with id: {playlist_create_result['id']}"
                )
                playlist_id_map[rb_playlist_name] = playlist_create_result["id"]
                string_utils.print_libsync_status_success("Done", level=1)

        else:
            string_utils.print_libsync_status("Dry run, skipping", level=2)

    start_time = time.time()
    # save mapping of playlists in a readable csv
    db_write_operations.save_playlist_id_map(rekordbox_xml_path, playlist_id_map)
    logger.debug(
        f"time taken for save_list_of_user_playlists: {(time.time() - start_time):.3f} seconds"
    )

    spotify_playlist_write_jobs, new_spotify_additions = get_playlist_diffs(
        rekordbox_playlists,
        rekordbox_to_spotify_map,
        playlist_id_map,
        libsync_owned_spotify_playlists,
    )
    # logger.debug(f"spotify_playlist_write_jobs: {spotify_playlist_write_jobs}")
    logger.debug(f"new_spotify_additions: {new_spotify_additions}")

    if len(spotify_playlist_write_jobs) < 1:
        string_utils.print_libsync_status("No Spotify playlists to update", level=1)
    else:
        # Show summary of changes before proceeding
        print_spotify_playlist_changes_summary(
            spotify_playlist_write_jobs,
            libsync_owned_spotify_playlists,
            playlist_id_map,
            collection,
            rekordbox_to_spotify_map,
        )

        # Ask for confirmation
        confirmation = input("\nDo you want to proceed with these changes? (y/n): ").lower().strip()
        if confirmation != "y":
            string_utils.print_libsync_status("Canceling playlist updates", level=2)
            return playlist_id_map

        if not dry_run:
            string_utils.print_libsync_status("Updating Spotify playlists", level=1)

            logger.info(f"running overwrite_playlists with {len(spotify_playlist_write_jobs)} jobs")
            spotify_api_utils.overwrite_playlists(spotify_playlist_write_jobs)
            string_utils.print_libsync_status_success("Done", level=1)

        else:
            string_utils.print_libsync_status("Dry run, skipping", level=2)

    if constants.IGNORE_SP_NEW_TRACKS or len(new_spotify_additions) < 1:
        string_utils.print_libsync_status("No Rekordbox playlists to update", level=1)
        db_write_operations.save_pending_tracks_spotify_to_rekordbox(rekordbox_xml_path, set(), {})

    else:
        spotify_song_details = spotify_api_utils.get_spotify_song_details(
            list({sp_uri for tracklist in new_spotify_additions.values() for sp_uri in tracklist})
        )

        (
            new_songs_to_download,
            songs_to_playlists_diff_map,
            playlists_to_songs_diff_map,
        ) = calculate_diff(new_spotify_additions, rekordbox_to_spotify_map)

        db_write_operations.save_pending_tracks_spotify_to_rekordbox(
            rekordbox_xml_path, new_songs_to_download, spotify_song_details
        )

        print_rekordbox_diff_report(
            new_songs_to_download,
            songs_to_playlists_diff_map,
            playlists_to_songs_diff_map,
            spotify_song_details,
        )

    # save playlists to db of playlists libsync owns for the current spotify user id
    db_write_operations.save_list_of_user_playlists(playlist_id_map)

    return playlist_id_map


def calculate_diff(
    new_spotify_additions: dict[str, list[str]],
    rekordbox_to_spotify_map: dict[str, str],
):
    spotify_to_rekordbox_map = {
        sp_uri: rb_track_id for rb_track_id, sp_uri in rekordbox_to_spotify_map.items()
    }
    # logger.debug(f"spotify_to_rekordbox_map: {spotify_to_rekordbox_map}")

    songs_to_playlists_diff_map = {}
    playlists_to_songs_diff_map = {}
    for rb_playlist_name, sp_track_uris_to_add in new_spotify_additions.items():
        for sp_uri in sp_track_uris_to_add:
            if sp_uri not in songs_to_playlists_diff_map:
                songs_to_playlists_diff_map[sp_uri] = []
            if rb_playlist_name not in playlists_to_songs_diff_map:
                playlists_to_songs_diff_map[rb_playlist_name] = []

            songs_to_playlists_diff_map[sp_uri].append(rb_playlist_name)
            playlists_to_songs_diff_map[rb_playlist_name].append(sp_uri)

    new_songs_to_download = {
        sp_uri for sp_uri in songs_to_playlists_diff_map if sp_uri not in spotify_to_rekordbox_map
    }

    return (
        new_songs_to_download,
        songs_to_playlists_diff_map,
        playlists_to_songs_diff_map,
    )


def print_rekordbox_diff_report(
    new_songs_to_download: set[str],
    songs_to_playlists_diff_map: dict[str, list[str]],
    playlists_to_songs_diff_map: dict[str, list[str]],
    spotify_song_details: dict[str, dict[str, object]],
):
    string_utils.print_libsync_status("Calculating songs to add to Rekordbox playlists", level=1)

    string_utils.print_libsync_status_success("Done", level=1)
    if len(new_songs_to_download) < 1:
        string_utils.print_libsync_status("No new songs to download", level=1)
    else:
        string_utils.print_libsync_status(
            f"Download these songs ({len(new_songs_to_download)}):", level=1
        )
        for sp_uri in sorted(new_songs_to_download):
            log_and_print(
                f"    {sp_uri} "
                + f"{string_utils.pretty_print_spotify_track(spotify_song_details[sp_uri])}"
            )

    string_utils.print_libsync_status("Add these songs to your Rekordbox playlists:", level=1)

    songs_to_playlists_diff_map_new_tracks = {
        sp_uri: rb_playlists
        for sp_uri, rb_playlists in songs_to_playlists_diff_map.items()
        if sp_uri in new_songs_to_download
    }
    songs_to_playlists_diff_map_old_tracks = {
        sp_uri: rb_playlists
        for sp_uri, rb_playlists in songs_to_playlists_diff_map.items()
        if sp_uri not in new_songs_to_download
    }

    if len(songs_to_playlists_diff_map_new_tracks) >= 1:
        log_and_print("    New tracks")
        print_rekordbox_diff_report_by_track(
            songs_to_playlists_diff_map_new_tracks,
            spotify_song_details,
        )
    if len(songs_to_playlists_diff_map_old_tracks) >= 1:
        log_and_print("\n    Tracks already in your collection")
        print_rekordbox_diff_report_by_track(
            songs_to_playlists_diff_map_old_tracks,
            spotify_song_details,
        )

    log_and_print("\n    Sorted by playlist")
    print_rekordbox_diff_report_by_playlist(
        playlists_to_songs_diff_map,
        spotify_song_details,
    )

    string_utils.print_libsync_status_success("Done", level=1)


def print_rekordbox_diff_report_by_track(
    songs_to_playlists_diff_map: dict[str, list[str]],
    spotify_song_details: dict[str, dict[str, object]],
):
    for sp_uri, rb_playlists in sorted(
        songs_to_playlists_diff_map.items(),
        key=lambda item: string_utils.pretty_print_spotify_track(
            spotify_song_details[item[0]]
        ).lower(),
    ):
        log_and_print(
            f"      {string_utils.pretty_print_spotify_track(spotify_song_details[sp_uri])}"
        )
        for rb_playlist_name in sorted(rb_playlists):
            log_and_print(f"        {rb_playlist_name}")


def print_rekordbox_diff_report_by_playlist(
    playlists_to_songs_diff_map: dict[str, list[str]],
    spotify_song_details: dict[str, dict[str, object]],
):
    for rb_playlist_name, sp_uris in sorted(
        playlists_to_songs_diff_map.items(), key=lambda x: x[0]
    ):
        log_and_print(f"      {rb_playlist_name}")
        for sp_uri in sorted(sp_uris):
            log_and_print(
                f"        {string_utils.pretty_print_spotify_track(spotify_song_details[sp_uri])}"
            )


def get_filtered_spotify_uris_from_rekordbox_playlist(
    rb_playlist: RekordboxPlaylist, rekordbox_to_spotify_map: dict[str, str]
):
    return [
        rekordbox_to_spotify_map[rb_track_id]
        for rb_track_id in rb_playlist.tracks
        if rb_track_id in rekordbox_to_spotify_map
        and string_utils.is_spotify_uri(rekordbox_to_spotify_map[rb_track_id])
    ]


def get_playlist_diffs(
    rekordbox_playlists: list[RekordboxPlaylist],
    rekordbox_to_spotify_map: dict[str, str],
    playlist_id_map: dict[PlaylistName, SpotifyPlaylistId],
    libsync_owned_spotify_playlists: dict[str, list[str]],
) -> tuple[
    list[tuple[SpotifyPlaylistId, list[SpotifyURI]]],
    dict[PlaylistName, list[SpotifyURI]],
]:
    logger.debug("running get_playlist_diffs")
    spotify_playlist_write_jobs: list[tuple[SpotifyPlaylistId, list[SpotifyURI]]] = []
    new_spotify_additions: dict[PlaylistName, list[SpotifyURI]] = {}

    # figure out which playlists need to be updated
    for rb_playlist in rekordbox_playlists:
        logger.debug(f"get_playlist_diffs for rekordbox playlist with name: {rb_playlist.name}")

        if rb_playlist.name not in playlist_id_map:
            logger.error(f"failed to add playlist {rb_playlist.name} to playlist_id_map.")
            continue

        sp_uris_from_rb = get_filtered_spotify_uris_from_rekordbox_playlist(
            rb_playlist, rekordbox_to_spotify_map
        )
        # logger.debug(f"spotify uris from rekordbox playlist: {sp_uris_from_rb}")

        spotify_playlist_id = playlist_id_map[rb_playlist.name]
        if spotify_playlist_id not in libsync_owned_spotify_playlists:
            logger.debug("fresh playlist, need to add full list")
            # this should only happen for playlists we just created
            spotify_playlist_write_jobs.append([spotify_playlist_id, sp_uris_from_rb])
            continue

        sp_uris_from_sp = [
            string_utils.get_spotify_uri_from_id(spotify_track_id)
            for spotify_track_id in libsync_owned_spotify_playlists[spotify_playlist_id]
        ]
        # logger.debug(f"spotify uris from spotify playlist: {sp_uris_from_sp}")
        sp_new_tracks = [uri for uri in sp_uris_from_sp if uri not in set(sp_uris_from_rb)]
        if len(sp_new_tracks) >= 1:
            new_spotify_additions[rb_playlist.name] = sp_new_tracks

        # this is what we want the spotify playlist to look like
        if constants.IGNORE_SP_NEW_TRACKS:
            logger.debug(
                "ignoring new tracks from spotify playlist (overwriting with rekordbox playlist)"
            )
            target_uri_list = sp_uris_from_rb
        else:
            logger.debug(
                "appending unrecognized tracks from spotify playlist to the end of rekordbox playlist"
            )
            target_uri_list = sp_uris_from_rb + sp_new_tracks

        # if doesn't match what we expect, then add a job
        if target_uri_list != sp_uris_from_sp:
            logger.debug(
                "goal state for playlist doesn't match current state. overwriting spotify playlist"
            )
            logger.debug(
                f"set(target_uri_list) - set(sp_uris_from_sp): {set(target_uri_list) - set(sp_uris_from_sp)}"
            )
            logger.debug(
                f"set(sp_uris_from_sp) - set(target_uri_list): {set(sp_uris_from_sp) - set(target_uri_list)}"
            )

            spotify_playlist_write_jobs.append([spotify_playlist_id, target_uri_list])
            continue

    return spotify_playlist_write_jobs, new_spotify_additions


def print_spotify_playlist_changes_summary(
    spotify_playlist_write_jobs: list[list[str, list[str]]],
    libsync_owned_spotify_playlists: dict[str, list[str]],
    playlist_id_map: dict[PlaylistName, SpotifyPlaylistId],
    collection: RekordboxCollection,
    rekordbox_to_spotify_map: dict[str, str],
):
    """Print a summary of changes to be made to Spotify playlists.
    Shows which songs will be added and removed from each playlist.
    """
    string_utils.print_libsync_status(
        f"Changes to be made to {len(spotify_playlist_write_jobs)} playlists:", level=2
    )

    reverse_playlist_id_map = {v: k for k, v in playlist_id_map.items()}
    reverse_rekordbox_to_spotify_map = {v: k for k, v in rekordbox_to_spotify_map.items()}

    for playlist_id, new_track_uris in spotify_playlist_write_jobs:
        playlist_name = reverse_playlist_id_map[playlist_id]
        current_track_ids = libsync_owned_spotify_playlists.get(playlist_id, [])
        current_track_uris = [
            string_utils.get_spotify_uri_from_id(track_id) for track_id in current_track_ids
        ]

        added_tracks = set(new_track_uris) - set(current_track_uris)
        removed_tracks = set(current_track_uris) - set(new_track_uris)

        if len(added_tracks) == 0 and len(removed_tracks) == 0:
            continue

        log_and_print(f"\n      Playlist: {playlist_name}")

        if added_tracks:
            log_and_print("        Adding:")
            for uri in sorted(added_tracks):
                if uri in reverse_rekordbox_to_spotify_map:
                    rb_track = collection[reverse_rekordbox_to_spotify_map[uri]]
                    log_and_print(f"          {rb_track.artist} - {rb_track.name}")

        if removed_tracks:
            log_and_print("        Removing:")
            for uri in sorted(removed_tracks):
                if uri in reverse_rekordbox_to_spotify_map:
                    rb_track = collection[reverse_rekordbox_to_spotify_map[uri]]
                    log_and_print(f"          {rb_track.artist} - {rb_track.name}")
