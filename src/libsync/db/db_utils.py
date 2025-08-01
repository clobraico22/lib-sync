import time
from pathlib import Path

# Use ~/.libsync/data for all data storage
LIBSYNC_DATA_DIR = Path.home() / ".libsync" / "data"
# Create directory if it doesn't exist
LIBSYNC_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Spotify playlist backups directory
SPOTIFY_PLAYLIST_BACKUPS_DIR = LIBSYNC_DATA_DIR / "spotify_playlist_backups"
# Create directory if it doesn't exist
SPOTIFY_PLAYLIST_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


def get_spotify_playlist_mapping_db_path(rekordbox_xml_path: str, user_id: str) -> str:
    return str(
        LIBSYNC_DATA_DIR
        / f"libsync_spotify_playlist_mapping_cache_{get_sanitized_xml_path(rekordbox_xml_path)}_{user_id}.csv"
    )


def get_user_spotify_playlists_list_db_path(user_id: str) -> str:
    return str(LIBSYNC_DATA_DIR / f"libsync_spotify_playlists_cache_{user_id}.txt")


def get_spotify_search_cache_path(rekordbox_xml_path: str) -> str:
    return str(
        LIBSYNC_DATA_DIR
        / f"libsync_search_results_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.db"
    )


def get_libsync_song_mapping_csv_path(rekordbox_xml_path: str) -> str:
    return str(
        LIBSYNC_DATA_DIR
        / f"libsync_song_mapping_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.csv"
    )


def get_libsync_pending_tracks_spotify_to_rekordbox_db_path(
    rekordbox_xml_path: str,
) -> str:
    return str(
        LIBSYNC_DATA_DIR
        / f"libsync_pending_tracks_spotify_to_rekordbox_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.csv"
    )


def get_spotify_playlist_cache_path() -> str:
    """Get the path for the primary spotify playlist cache file."""
    return str(SPOTIFY_PLAYLIST_BACKUPS_DIR / "playlists.pickle")


def get_spotify_playlist_backup_path() -> str:
    """Get the path for a timestamped spotify playlist backup file."""
    return str(
        SPOTIFY_PLAYLIST_BACKUPS_DIR / f"playlists_{time.strftime('%Y.%m.%d_%H.%M.%S')}.pickle"
    )


def get_sanitized_xml_path(xml_path: str) -> str:
    return xml_path.replace("/", "_")
