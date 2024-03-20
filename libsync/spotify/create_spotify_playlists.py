"""contains create_spotify_playlists function and helpers"""

import logging
import pprint

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.rekordbox_library import RekordboxPlaylist

ITEMS_PER_PAGE_SPOTIFY_API = 100
# turn this on for debugging without the spotify match module
SKIP_CREATE_SPOTIFY_PLAYLISTS = True
FORCE_CREATE_NEW_PLAYLISTS = False
SPOTIFY_PLAYLISTS_LIMIT = 50
SPOTIFY_TRACKS_LIMIT = 100


def create_spotify_playlists(
    playlist_id_map: dict[str, str],
    rekordbox_playlists: list[RekordboxPlaylist],
    rekordbox_to_spotify_map: dict[str, str],
    create_collection_playlist: bool = False,
    make_playlists_public: bool = False,
) -> dict[str, str]:
    """creates playlists in the user's account with the matched songs

    Args:
        playlist_id_map (dict[str, str]): map from rekordbox playlist name to spotify playlist id.
            passed by reference, modified in place
        rekordbox_playlists (list[RekordboxPlaylist]): user's playlists from rekordbox
            (list of rekordbox track IDs)
        rekordbox_to_spotify_map (dict[str, str]): mapping from rekordbox track IDs to spotify URIs
        create_collection_playlist (bool,optional): if true, will create a spotify playlist of
            the entire rekordbox collection
        make_playlists_public (bool,optional): determines if playlist will be made public or not

    Returns:
        dict[str, str]: reference to playlist_id_map argument which is modified in place
    """

    if SKIP_CREATE_SPOTIFY_PLAYLISTS:
        return

    logging.debug(
        "running create_spotify_playlists with\n"
        + f"rekordbox_playlists:\n{pprint.pformat(rekordbox_playlists)},\n"
        + f"rekordbox_to_spotify_map:\n{pprint.pformat(rekordbox_to_spotify_map)}"
    )
    print("  creating spotify playlists...")

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

    # get user playlists to check against deleted playlists
    offset = 0
    user_playlists = set()
    logging.debug("fetching user playlists")
    while True:
        logging.debug(f"fetching next page of user playlists, with offset {offset}")
        result = spotify.user_playlists(
            user=user_id, limit=SPOTIFY_PLAYLISTS_LIMIT, offset=offset
        )
        user_playlists.update([item["id"] for item in result["items"]])
        if result["next"] is None:
            break
        offset += SPOTIFY_PLAYLISTS_LIMIT
    logging.info(f"done fetching {len(user_playlists)} user playlists")

    if create_collection_playlist:
        logging.debug("adding Collection playlist")
        rekordbox_playlists.append(
            RekordboxPlaylist(
                name="Collection",
                tracks=list(rekordbox_to_spotify_map.keys()),
            )
        )

    for playlist in rekordbox_playlists:
        try:
            existing_track_uris = []
            # get or create playlist
            if (
                playlist.name in playlist_id_map
                and playlist_id_map[playlist.name] in user_playlists
                and not FORCE_CREATE_NEW_PLAYLISTS
            ):
                playlist_id = playlist_id_map[playlist.name]

                # get full playlist
                offset = 0
                logging.info("fetching tracks")
                while True:
                    logging.debug(
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

                logging.debug(
                    f'done fetching {len(playlist_tracks_result)} tracks from "{playlist.name}"'
                )

            else:
                if playlist.name in playlist_id_map:
                    logging.info("detected deleted playlist, recreating")

                playlist_create_result = spotify.user_playlist_create(
                    user=user_id,
                    name=f"[ls] {playlist.name}",
                    # TODO: private playlists don't work! read here:
                    # https://community.spotify.com/t5/Spotify-for-Developers/Api-to-create-a-private-playlist-doesn-t-work/td-p/5407807
                    public=make_playlists_public,
                    description="Automatically generated by libsync",
                )
                playlist_id = playlist_create_result["id"]
                logging.info(f"created spotify playlist: {playlist.name}")

            playlist_id_map[playlist.name] = playlist_id

            tracks_uris_to_add = []
            for track_id in playlist.tracks:
                spotify_uri = rekordbox_to_spotify_map[track_id]
                if spotify_uri != "" and spotify_uri != "libsync:NOT_ON_SPOTIFY":
                    tracks_uris_to_add.append(spotify_uri)

            if existing_track_uris == tracks_uris_to_add:
                logging.info(f'contents of playlist "{playlist.name}" are unchanged')
            else:
                logging.info(f'updating contents of playlist "{playlist.name}"')

                spotify.playlist_replace_items(playlist_id, [])
                logging.info(f'cleared playlist "{playlist.name}"')
                pages = [
                    tracks_uris_to_add[i : i + ITEMS_PER_PAGE_SPOTIFY_API]
                    for i in range(
                        0, len(tracks_uris_to_add), ITEMS_PER_PAGE_SPOTIFY_API
                    )
                ]
                for page in pages:
                    spotify.playlist_add_items(playlist_id=playlist_id, items=page)

                logging.info(
                    f'successfully added tracks to spotify playlist "{playlist.name}"'
                )

        except spotipy.exceptions.SpotifyException as error:
            logging.exception(error)
            print(f"failed to create playlist {playlist.name}")

    print("  done creating spotify playlists.")
    return playlist_id_map
