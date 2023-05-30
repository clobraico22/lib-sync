"""
contains create_spotify_playlists function and helpers
"""

import logging
import pprint

import spotipy
from rekordbox_library import RekordboxPlaylist
from spotipy.oauth2 import SpotifyOAuth


def create_spotify_playlists(
    playlist_id_map: dict[str, str],
    rekordbox_playlists: list[RekordboxPlaylist],
    rekordbox_to_spotify_map: dict[str, str],
    create_collection_playlist: bool = False,
    make_playlists_public: bool = False,
):
    """creates playlists in the user's account with the matched songs

    Args:
        playlist_id_map (dict[str, str]): map from rekordbox playlist name to spotify playlist id.
            passed by reference, modified in place
        rekordbox_playlists (list[RekordboxPlaylist]): user's playlists from rekordbox (list of rekordbox track IDs)
        rekordbox_to_spotify_map (dict[str, str]): mapping from rekordbox track IDs to spotify URIs
        create_collection_playlist (bool,optional): if true, will create a spotify playlist of the entire rekordbox collection
        make_playlists_public (bool,optional): determines if playlist will be made public or not

    Returns:
        dict[str, str]: reference to playlist_id_map argument which is modified in place
    """

    logging.debug(
        "running create_spotify_playlists with\n"
        + f"rekordbox_playlists:\n{pprint.pformat(rekordbox_playlists)},\n"
        + f"rekordbox_to_spotify_map:\n{pprint.pformat(rekordbox_to_spotify_map)}"
    )

    scope = ["user-library-read", "playlist-modify-private"]
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    user_id = spotify.current_user()["id"]

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
            # get or create playlist
            if playlist.name in playlist_id_map:
                spotify_playlist_data = spotify.playlist(playlist_id_map[playlist.name])
                logging.info(f"found spotify playlist from last time: {playlist.name}")
                # clear playlist
                spotify.playlist_replace_items(spotify_playlist_data["uri"], [])

            else:
                # TODO: public and description aren't working, figure out why
                spotify_playlist_data = spotify.user_playlist_create(
                    user=user_id,
                    name=playlist.name,
                    public=make_playlists_public,
                    description="Automatically generated based on your rekordbox library by lib-sync."
                    + "\nFor more information, visit here https://github.com/clobraico22/lib-sync",
                )
                logging.info(f"created spotify playlist: {playlist.name}")

            playlist_id = spotify_playlist_data["id"]
            playlist_id_map[playlist.name] = playlist_id

            tracks_uris_to_add = [
                rekordbox_to_spotify_map[track_id]
                for track_id in playlist.tracks
                if track_id in rekordbox_to_spotify_map
            ]

            # TODO: paginate this call, spotify only allows 100 items per call
            print(tracks_uris_to_add)
            spotify.playlist_add_items(
                playlist_id=playlist_id, items=tracks_uris_to_add
            )
            logging.info(f"added tracks to spotify playlist: {playlist.name}")

        except spotipy.exceptions.SpotifyException as error:
            logging.error(error)
            print(f"failed to create playlist {playlist.name}")

    return playlist_id_map
