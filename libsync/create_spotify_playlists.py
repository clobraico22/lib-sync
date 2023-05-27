import logging

from rekordbox_library import RekordboxPlaylist
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import pprint


def create_spotify_playlists(
    rekordbox_playlists: list[RekordboxPlaylist],
    rekordbox_to_spotify_map: dict[str, str],
    spotify_username: str,
    *,
    create_collection_playlist: bool = False,
    make_playlists_public: bool = False,
):
    """creates playlists in the user's account with the matched songs

    Args:
        rekordbox_playlists (list[RekordboxPlaylist]): user's playlists from rekordbox (list of rekordbox track IDs)
        rekordbox_to_spotify_map (dict[str, str]): mapping from rekordbox track IDs to spotify URIs
        spotify_username (str): TODO: replace with the rest of auth,
        create_collection_playlist (bool,optional): if true, will create a spotify playlist of the entire rekordbox collection
        make_playlists_public (bool,optional): determines if playlist will be made public or not
    """

    logging.info(
        "running create_spotify_playlists with\n"
        + f"rekordbox_playlists:\n{pprint.pformat(rekordbox_playlists)},\n"
        + f"rekordbox_to_spotify_map:\n{pprint.pformat(rekordbox_to_spotify_map)},\n"
        + f"spotify_username:\n{spotify_username}"
    )

    auth_manager = SpotifyOAuth(
        username=spotify_username,
        scope=["user-library-read", "playlist-modify-private"],
    )
    token = auth_manager.get_access_token(code=None, as_dict=False, check_cache=False)
    logging.info(f"got spotify token: {token}")

    if token:
        spotify_client = spotipy.Spotify(oauth_manager=auth_manager, auth=token)

        playlist_uri_map = {}
        for playlist in rekordbox_playlists:
            spotify_playlist_data = spotify_client.user_playlist_create(
                user=spotify_username,
                name=playlist.name,
                public=make_playlists_public,
                description="Automatically generated based on your rekordbox library by lib-sync.\nFor more information, visit here https://github.com/clobraico22/lib-sync",
            )
            logging.info(f"created spotify playlist: {playlist.name}")

            tracks_uris_to_add = [
                rekordbox_to_spotify_map[track_id] for track_id in playlist.tracks
            ]
            spotify_client.user_playlist_add_tracks(
                user=spotify_username, playlist_id=spotify_playlist_data["uri"], tracks=tracks_uris_to_add
            )
            logging.info(f"added tracks to spotify playlist: {playlist.name}")
            playlist_uri_map[playlist.name]= spotify_playlist_data['uri']

        if create_collection_playlist:
            playlist_data = spotify_client.user_playlist_create(
                user=spotify_username,
                name="Collection",
                public=make_playlists_public,
                description=(
                    "Automatically generated based on your rekordbox library by lib-sync.\n\n",
                    "For more information, visit here https://github.com/clobraico22/lib-sync",
                ),
            )
            logging.info(f"created spotify playlist: Collection")

            spotify_client.user_playlist_add_tracks(
                user=spotify_username,
                playlist_id=playlist_data["uri"],
                tracks=rekordbox_to_spotify_map.values(),
            )
            logging.info(f"added tracks to spotify playlist: Collection")

    else:
        print(f"Can't get token for user {spotify_username}")

    return playlist_uri_map
