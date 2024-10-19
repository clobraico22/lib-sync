from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyAuthManager:
    _auth_manager: Optional[SpotifyOAuth] = None
    _user_id: Optional[str] = None
    _spotify_client: Optional[spotipy.Spotify] = None
    _access_token: Optional[str] = None

    # base level
    @classmethod
    def get_auth_manager(cls) -> SpotifyOAuth:
        if cls._auth_manager is None:
            scope = [
                "user-library-read",
                "playlist-read-private",
                "playlist-read-collaborative",
                "playlist-modify-private",
                "playlist-modify-public",
            ]
            cls._auth_manager = SpotifyOAuth(scope=scope)
        return cls._auth_manager

    # relies on get_auth_manager
    @classmethod
    def get_access_token(cls) -> str:
        if cls._access_token is None:
            auth_manager = cls.get_auth_manager()
            cls._access_token = auth_manager.get_access_token(as_dict=False)
        return cls._access_token

    # relies on get_auth_manager
    @classmethod
    def get_spotify_client(cls) -> spotipy.Spotify:
        if cls._spotify_client is None:
            auth_manager = cls.get_auth_manager()
            cls._spotify_client = spotipy.Spotify(auth_manager=auth_manager)
        return cls._spotify_client

    # relies on get_spotify_client (which relies on get_auth_manager)
    @classmethod
    def get_user_id(cls) -> str:
        if cls._user_id is None:
            spotify = cls.get_spotify_client()
            cls._user_id = spotify.current_user()["id"]
        return cls._user_id
