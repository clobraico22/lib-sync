"""contains create_spotify_playlists function and helpers"""

import logging
import pprint

import spotipy
from db import db_read_operations, db_write_operations
from spotify import spotify_api_utils
from spotipy.oauth2 import SpotifyOAuth
from utils.constants import (
    FORCE_CREATE_NEW_PLAYLISTS,
    ITEMS_PER_PAGE_SPOTIFY_API,
    NOT_ON_SPOTIFY_FLAG,
    SPOTIFY_TRACKS_LIMIT,
)
from utils.rekordbox_library import RekordboxPlaylist

logger = logging.getLogger("libsync")


def create_spotify_playlists(
    rekordbox_xml_path: str,
    rekordbox_playlists: list[RekordboxPlaylist],
    rekordbox_to_spotify_map: dict[str, str],
    create_collection_playlist: bool,
    make_playlists_public: bool,
    skip_create_spotify_playlists: bool,
) -> dict[str, str]:
    """creates playlists in the user's account with the matched songs

    Args:
        rekordbox_xml_path (str): xml path used for this run -
          this will be used to determine cache and csv paths
        rekordbox_playlists (list[RekordboxPlaylist]): user's playlists from rekordbox
            (list of rekordbox track IDs)
        rekordbox_to_spotify_map (dict[str, str]): mapping from rekordbox track IDs to spotify URIs
        create_collection_playlist (bool): if true, will create a spotify playlist of
            the entire rekordbox collection
        make_playlists_public (bool): determines if playlist will be made public or not
        skip_create_spotify_playlists (bool): don't make playlists
            (skip for debugging or local matching)

    Returns:
        dict[str, str]: reference to playlist_id_map argument which is modified in place
    """

    # if skip_create_spotify_playlists:
    #     return

    logger.debug(
        "running create_spotify_playlists with\n"
        + f"rekordbox_playlists:\n{pprint.pformat(rekordbox_playlists)},\n"
        + f"rekordbox_to_spotify_map:\n{pprint.pformat(rekordbox_to_spotify_map)}"
    )

    print("  fetching your playlists...")

    playlist_id_map = db_read_operations.get_playlist_id_map(rekordbox_xml_path)
    libsync_owned_spotify_playlists = spotify_api_utils.get_user_playlists(
        playlist_id_map
    )
    all_user_playlists = spotify_api_utils.get_all_user_playlists()
    spotify_playlists = {
        playlist_id: track_list
        for playlist_id, track_list in libsync_owned_spotify_playlists.items()
        if playlist_id in all_user_playlists
    }

    print("  done fetching your playlists.")
    print("  creating spotify playlists...")

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
    # TODO: working here on reverse sync

    if create_collection_playlist:
        logger.debug("adding Collection playlist")
        # TODO: currently no mechanism for removing deleted songs from rekordbox_to_spotify_map
        rekordbox_playlists.append(
            RekordboxPlaylist(
                name="Collection",
                tracks=list(rekordbox_to_spotify_map.keys()),
            )
        )

    for playlist in rekordbox_playlists:
        if skip_create_spotify_playlists:
            continue

        try:
            existing_track_uris = []
            # get or create playlist
            if (
                playlist.name in playlist_id_map
                and playlist_id_map[playlist.name] in spotify_playlists
                and not FORCE_CREATE_NEW_PLAYLISTS
            ):
                playlist_id = playlist_id_map[playlist.name]

                # get full playlist
                offset = 0
                logger.info("fetching tracks")
                while True:
                    logger.debug(
                        f"fetching next page of playlist tracks, with offset {offset}"
                    )

                    playlist_tracks_result = spotify.playlist_tracks(
                        playlist_id, limit=SPOTIFY_TRACKS_LIMIT, offset=offset
                    )
                    existing_track_uris.extend(
                        [
                            item["track"]["uri"]
                            for item in playlist_tracks_result["items"]
                        ]
                    )
                    if playlist_tracks_result["next"] is None:
                        break
                    offset += SPOTIFY_TRACKS_LIMIT

                logger.debug(
                    f'done fetching {len(playlist_tracks_result)} tracks from "{playlist.name}"'
                )

            else:
                if playlist.name in playlist_id_map:
                    logger.info("detected deleted playlist, recreating")

                playlist_create_result = spotify.user_playlist_create(
                    user=user_id,
                    name=f"[ls] {playlist.name}",
                    # TODO: private playlists don't work! read here:
                    # https://community.spotify.com/t5/Spotify-for-Developers/Api-to-create-a-private-playlist-doesn-t-work/td-p/5407807
                    public=make_playlists_public,
                    description="Automatically generated by libsync",
                )
                playlist_id = playlist_create_result["id"]
                logger.info(f"created spotify playlist: {playlist.name}")

            playlist_id_map[playlist.name] = playlist_id

            tracks_uris_to_add = []
            for track_id in playlist.tracks:
                spotify_uri = rekordbox_to_spotify_map[track_id]
                if (
                    spotify_uri != ""
                    and spotify_uri is not None
                    and spotify_uri != NOT_ON_SPOTIFY_FLAG
                ):
                    tracks_uris_to_add.append(spotify_uri)

            if existing_track_uris == tracks_uris_to_add:
                logger.info(f'contents of playlist "{playlist.name}" are unchanged')
            else:
                logger.info(f'updating contents of playlist "{playlist.name}"')

                spotify.playlist_replace_items(playlist_id, [])
                logger.info(f'cleared playlist "{playlist.name}"')
                pages = [
                    tracks_uris_to_add[i : i + ITEMS_PER_PAGE_SPOTIFY_API]
                    for i in range(
                        0, len(tracks_uris_to_add), ITEMS_PER_PAGE_SPOTIFY_API
                    )
                ]
                for page in pages:
                    spotify.playlist_add_items(playlist_id=playlist_id, items=page)

                logger.info(
                    f'successfully added tracks to spotify playlist "{playlist.name}"'
                )

        except spotipy.exceptions.SpotifyException as error:
            logger.exception(error)
            print(f"failed to create playlist {playlist.name}")

    # save mapping of playlists in a readable csv
    db_write_operations.save_playlist_id_map(rekordbox_xml_path, playlist_id_map)

    # TODO: deprecate this (might still be useful for testing)
    # save playlists to db of playlists libsync owns for the current spotify user id
    db_write_operations.save_list_of_user_playlists(playlist_id_map)

    print("  done creating spotify playlists.")
    return playlist_id_map
