import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_user_spotify_playlist_mapping_db_path(user_id: str) -> str:
    return f"data/libsync_spotify_playlist_mapping_cache_{user_id}.csv"


def get_user_spotify_playlists_list_db_path(user_id: str) -> str:
    return f"data/libsync_spotify_playlists_cache_{user_id}.txt"


def get_libsync_cache_path(rekordbox_xml_path: str) -> str:
    return f"data/libsync_sync_cache_{rekordbox_xml_path.replace('/', '_')}.db"


def get_libsync_song_mapping_csv_path(rekordbox_xml_path: str) -> str:
    return f"data/libsync_song_mapping_cache_{rekordbox_xml_path.replace('/', '_')}.csv"


def get_spotify_user_id() -> str:
    scope = [
        "user-library-read",
    ]
    auth_manager = SpotifyOAuth(scope=scope)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user_id = spotify.current_user()["id"]
    return user_id
