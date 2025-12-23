import os
import sys

import spotipy
from spotipy.oauth2 import SpotifyOAuth

REQUIRED_SPOTIFY_ENV_VARS = [
    "SPOTIPY_CLIENT_ID",
    "SPOTIPY_CLIENT_SECRET",
    "SPOTIPY_REDIRECT_URI",
]


def validate_spotify_env_vars() -> None:
    """Check that all required Spotify environment variables are set.

    Exits with a user-friendly error message if any are missing.
    """
    missing_vars = [var for var in REQUIRED_SPOTIFY_ENV_VARS if not os.environ.get(var)]

    if missing_vars:
        print("Error: Missing required Spotify environment variables:", file=sys.stderr)
        for var in missing_vars:
            print(f"  - {var}", file=sys.stderr)
        print(
            "\nPlease set these in your .env file or environment. See .env.example for reference.",
            file=sys.stderr,
        )
        sys.exit(1)


class SpotifyAuthManager:
    _auth_manager: SpotifyOAuth | None = None
    _user_id: str | None = None
    _spotify_client: spotipy.Spotify | None = None
    _access_token: str | None = None

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
