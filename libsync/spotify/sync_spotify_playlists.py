"""contains sync_spotify_playlists function and helpers"""

import logging
import pprint
import time

import spotipy
from db import db_read_operations, db_write_operations
from spotify import spotify_api_utils
from spotipy.oauth2 import SpotifyOAuth
from utils import constants, string_utils
from utils.rekordbox_library import RekordboxPlaylist

logger = logging.getLogger("libsync")


def sync_spotify_playlists(
    rekordbox_xml_path: str,
    rekordbox_playlists: list[RekordboxPlaylist],
    rekordbox_to_spotify_map: dict[str, str],
    make_playlists_public: bool,
) -> dict[str, str]:
    """creates playlists in the user's account with the matched songs

    Args:
        rekordbox_xml_path (str): xml path used for this run -
          this will be used to determine cache and csv paths
        rekordbox_playlists (list[RekordboxPlaylist]): user's playlists from rekordbox
            (list of rekordbox track IDs)
        rekordbox_to_spotify_map (dict[str, str]): mapping from rekordbox track IDs to spotify URIs
        make_playlists_public (bool): determines if playlist will be made public or not
        skip_spotify_playlist_sync (bool): don't make playlists
            (skip for debugging or local matching)

    Returns:
        dict[str, str]: reference to playlist_id_map argument which is modified in place
    """

    logger.debug(
        "running sync_spotify_playlists with\n"
        + f"rekordbox_playlists:\n{pprint.pformat(rekordbox_playlists)},\n"
        + f"rekordbox_to_spotify_map:\n{pprint.pformat(rekordbox_to_spotify_map)}"
    )

    string_utils.print_libsync_status("Fetching your Spotify playlists", level=1)
    playlist_id_map = db_read_operations.get_playlist_id_map(rekordbox_xml_path)
    libsync_owned_spotify_playlists = spotify_api_utils.get_user_playlists_details(
        playlist_id_map.values()
    )
    all_user_spotify_playlists = spotify_api_utils.get_all_user_playlists_set()
    rekordbox_playlists_set = {rb_playlist.name for rb_playlist in rekordbox_playlists}
    string_utils.print_libsync_status_success("Done", level=1)

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

    # TODO: centralize all this auth logic into a singleton class to avoid repeated auth
    scope = [
        "user-library-read",
        "playlist-read-private",
        "playlist-read-collaborative",
        "playlist-modify-private",
        "playlist-modify-public",
    ]
    auth_manager = SpotifyOAuth(scope=scope)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user_id = spotify.current_user()["id"]

    if len(spotify_playlist_ids_to_delete) < 1:
        string_utils.print_libsync_status("No Spotify playlists to delete", level=1)
    else:
        string_utils.print_libsync_status("Deleting old Spotify playlists", level=1)

        for playlist_id in spotify_playlist_ids_to_delete:
            logger.debug(f"deleting playlist with id: {playlist_id}")
            # TODO: parallelize this if necessary, shouldn't be a very hot path.
            # "unfollowing" your own playlist is the same as deleting it from the spotify UI.
            # it's impossible to actually "delete" a spotify playlist.
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
        string_utils.print_libsync_status("Creating new Spotify playlists", level=1)

        # TODO: parallelize this if necessary, shouldn't be a very hot path.
        for rb_playlist_name in playlist_names_to_create:
            # TODO: need better error handling for spotify API calls
            #   (network failures, bad IDs, etc)
            #   catch aiohttp.client_exceptions.ServerDisconnectedError in asyncio workers
            playlist_create_result = spotify.user_playlist_create(
                user=user_id,
                name=string_utils.generate_spotify_playlist_name(rb_playlist_name),
                # TODO: private playlists don't work! read here:
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
    logger.debug(f"spotify_playlist_write_jobs: {spotify_playlist_write_jobs}")
    logger.debug(f"new_spotify_additions: {new_spotify_additions}")

    if len(spotify_playlist_write_jobs) < 1:
        string_utils.print_libsync_status("No Spotify playlists to update", level=1)
    else:
        string_utils.print_libsync_status("Updating Spotify playlists", level=1)
        spotify_api_utils.overwrite_playlists(spotify_playlist_write_jobs)
        string_utils.print_libsync_status_success("Done", level=1)

    if constants.IGNORE_SP_NEW_TRACKS or len(new_spotify_additions) < 1:
        string_utils.print_libsync_status("No Rekordbox playlists to update", level=1)
    else:
        print_rekordbox_diff_report(new_spotify_additions, rekordbox_to_spotify_map)

    # save playlists to db of playlists libsync owns for the current spotify user id
    db_write_operations.save_list_of_user_playlists(playlist_id_map)

    return playlist_id_map


def print_rekordbox_diff_report(
    new_spotify_additions: dict[str, list[str]],
    rekordbox_to_spotify_map: dict[str, str],
):
    string_utils.print_libsync_status(
        "Calculating songs to add to Rekordbox playlists", level=1
    )
    spotify_song_details = spotify_api_utils.get_spotify_song_details(
        list(
            {
                sp_uri
                for tracklist in new_spotify_additions.values()
                for sp_uri in tracklist
            }
        )
    )

    # TODO: there's an issue with the workflow of adding songs to spotify, and then adding them to
    # rekordbox. auto match may pick a different song than the one you added to spotify, leading to
    # a diff that never goes away, plus two versions of the same song in all of the spotify
    # playlists. need to fix
    # TODO: there's also an issue with the workflow of deleting a song from a rekordbox playlist
    # after it's been synced to spotify. libsync doesn't know it was deleted manually, so it will
    # report that the song is missing from the rekordbox playlist. need to keep track of rekordbox
    # collection history to track deletions
    spotify_to_rekordbox_map = {
        sp_uri: rb_track_id for rb_track_id, sp_uri in rekordbox_to_spotify_map.items()
    }
    logger.debug(f"spotify_to_rekordbox_map: {spotify_to_rekordbox_map}")

    songs_to_playlists_diff_map = {}
    for rb_playlist_name, sp_track_uris_to_add in new_spotify_additions.items():
        for sp_uri in sp_track_uris_to_add:
            if sp_uri not in songs_to_playlists_diff_map:
                songs_to_playlists_diff_map[sp_uri] = []

            songs_to_playlists_diff_map[sp_uri].append(rb_playlist_name)

    new_songs_to_download = {
        sp_uri
        for sp_uri in songs_to_playlists_diff_map
        if sp_uri not in spotify_to_rekordbox_map
    }
    string_utils.print_libsync_status_success("Done", level=1)
    if len(new_songs_to_download) < 1:
        string_utils.print_libsync_status("No new songs to download", level=1)
    else:
        string_utils.print_libsync_status("Download these songs:", level=1)
        for sp_uri in new_songs_to_download:
            print(
                f"    {sp_uri} "
                + f"{string_utils.pretty_print_spotify_track(spotify_song_details[sp_uri])}"
            )

    string_utils.print_libsync_status(
        "Add these songs to your Rekordbox playlists:", level=1
    )
    songs_to_playlists_diff_map_new_tracks = (
        {
            sp_uri: rb_playlists
            for sp_uri, rb_playlists in songs_to_playlists_diff_map.items()
            if sp_uri in new_songs_to_download
        },
    )
    songs_to_playlists_diff_map_old_tracks = (
        {
            sp_uri: rb_playlists
            for sp_uri, rb_playlists in songs_to_playlists_diff_map.items()
            if sp_uri not in new_songs_to_download
        },
    )

    if len(songs_to_playlists_diff_map_new_tracks) >= 1:
        print("    New tracks")
        print_rekordbox_diff_report_by_track(
            songs_to_playlists_diff_map_new_tracks,
            spotify_song_details,
        )
    if len(songs_to_playlists_diff_map_old_tracks) >= 1:
        print("\n    Tracks already in your collection")
        print_rekordbox_diff_report_by_track(
            songs_to_playlists_diff_map_old_tracks,
            spotify_song_details,
        )

    string_utils.print_libsync_status_success("Done", level=1)


def print_rekordbox_diff_report_by_track(
    songs_to_playlists_diff_map, spotify_song_details
):
    for sp_uri, rb_playlists in songs_to_playlists_diff_map.items():
        print(
            f"      {string_utils.pretty_print_spotify_track(spotify_song_details[sp_uri])}"
        )
        for rb_playlist_name in rb_playlists:
            print(f"        {rb_playlist_name}")


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
    rekordbox_playlists,
    rekordbox_to_spotify_map,
    playlist_id_map,
    libsync_owned_spotify_playlists,
):
    logger.debug("running get_playlist_diffs")
    spotify_playlist_write_jobs = []
    new_spotify_additions = {}

    # figure out which playlists need to be updated
    for rb_playlist in rekordbox_playlists:
        logger.debug(
            f"get_playlist_diffs for rekordbox playlist with name: {rb_playlist.name}"
        )

        if rb_playlist.name not in playlist_id_map:
            logger.error(
                f"failed to add playlist {rb_playlist.name} to playlist_id_map."
            )
            continue

        sp_uris_from_rb = get_filtered_spotify_uris_from_rekordbox_playlist(
            rb_playlist, rekordbox_to_spotify_map
        )
        logger.debug(f"spotify uris from rekordbox playlist: {sp_uris_from_rb}")

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
        logger.debug(f"spotify uris from spotify playlist: {sp_uris_from_sp}")
        sp_new_tracks = [
            uri for uri in sp_uris_from_sp if uri not in set(sp_uris_from_rb)
        ]
        if len(sp_new_tracks) >= 1:
            # TODO: get details on tracks to add to spotify (artist, title, etc)
            # can probably do this from rekordbox library/collection in the output function
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
