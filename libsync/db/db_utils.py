import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_spotify_playlist_mapping_db_path(rekordbox_xml_path: str, user_id: str) -> str:
    return (
        "data/libsync_spotify_playlist_mapping_cache_"
        + f"{get_sanitized_xml_path(rekordbox_xml_path)}_{user_id}.csv"
    )


def get_user_spotify_playlists_list_db_path(user_id: str) -> str:
    return f"data/libsync_spotify_playlists_cache_{user_id}.txt"


def get_spotify_search_cache_path(rekordbox_xml_path: str) -> str:
    return f"data/libsync_search_results_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.db"


def get_libsync_song_mapping_csv_path(rekordbox_xml_path: str) -> str:
    return f"data/libsync_song_mapping_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.csv"


def get_sanitized_xml_path(xml_path: str) -> str:
    return xml_path.replace("/", "_")


def get_spotify_user_id() -> str:
    scope = [
        "user-library-read",
    ]
    auth_manager = SpotifyOAuth(scope=scope)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user_id = spotify.current_user()["id"]
    return user_id
