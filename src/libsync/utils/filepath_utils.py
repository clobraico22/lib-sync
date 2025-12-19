"""Centralized filepath utilities for libsync.

This module contains all path-related constants and functions used across the libsync codebase.
All data is stored under ~/.libsync/data with organized subdirectories for different purposes.
"""

import time
from datetime import datetime
from pathlib import Path

# Main data directory for all libsync storage
LIBSYNC_DATA_DIR = Path.home() / ".libsync" / "data"
LIBSYNC_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Subdirectories for specific purposes
LIBSYNC_LOGS_DIR = LIBSYNC_DATA_DIR / "logs"
LIBSYNC_LOGS_DIR.mkdir(parents=True, exist_ok=True)

SPOTIFY_PLAYLIST_BACKUPS_DIR = LIBSYNC_DATA_DIR / "spotify_playlist_backups"
SPOTIFY_PLAYLIST_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

REKORDBOX_XML_BACKUPS_DIR = LIBSYNC_DATA_DIR / "rekordbox_xml_backups"
REKORDBOX_XML_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


# Spotify-related paths
def get_spotify_playlist_mapping_db_path(rekordbox_xml_path: str, user_id: str) -> str:
    """Get path for Spotify playlist mapping cache."""
    return str(
        LIBSYNC_DATA_DIR
        / f"libsync_spotify_playlist_mapping_cache_{get_sanitized_xml_path(rekordbox_xml_path)}_{user_id}.csv"
    )


def get_user_spotify_playlists_list_db_path(user_id: str) -> str:
    """Get path for user's Spotify playlists cache."""
    return str(LIBSYNC_DATA_DIR / f"libsync_spotify_playlists_cache_{user_id}.txt")


def get_spotify_search_cache_path(rekordbox_xml_path: str) -> str:
    """Get path for Spotify search results cache."""
    return str(
        LIBSYNC_DATA_DIR
        / f"libsync_search_results_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.db"
    )


def get_spotify_playlist_cache_path() -> str:
    """Get the path for the primary spotify playlist cache file."""
    return str(SPOTIFY_PLAYLIST_BACKUPS_DIR / "playlists.pickle")


def get_spotify_playlist_backup_path() -> str:
    """Get the path for a timestamped spotify playlist backup file."""
    return str(
        SPOTIFY_PLAYLIST_BACKUPS_DIR / f"playlists_{time.strftime('%Y.%m.%d_%H.%M.%S')}.pickle"
    )


# Rekordbox-related paths
def get_libsync_song_mapping_csv_path(rekordbox_xml_path: str) -> str:
    """Get path for libsync song mapping cache."""
    return str(
        LIBSYNC_DATA_DIR
        / f"libsync_song_mapping_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.csv"
    )


def get_libsync_pending_tracks_spotify_to_rekordbox_db_path(
    rekordbox_xml_path: str,
) -> str:
    """Get path for pending tracks from Spotify to Rekordbox."""
    return str(
        LIBSYNC_DATA_DIR
        / f"libsync_pending_tracks_spotify_to_rekordbox_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.csv"
    )


def get_rekordbox_xml_backup_path(xml_path: str, mtime: float) -> Path:
    """Get backup path for a Rekordbox XML file using its modification time."""
    mtime_datetime = datetime.fromtimestamp(mtime)
    timestamp_str = mtime_datetime.strftime("%Y.%m.%d_%H.%M.%S")
    xml_filename = Path(xml_path).name
    backup_filename = f"{Path(xml_filename).stem}_{timestamp_str}.xml"
    return REKORDBOX_XML_BACKUPS_DIR / backup_filename


# Log file paths
def get_log_file_path() -> Path:
    """Get path for current log file with timestamp."""
    log_filename = f"libsync_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    return LIBSYNC_LOGS_DIR / log_filename


# Failed matches export
def get_failed_matches_export_path() -> Path:
    """Get path for failed matches export file."""
    filename = f"failed_matches_{datetime.now()}.txt".replace(" ", "_")
    return LIBSYNC_DATA_DIR / filename


# YouTube download paths
def get_youtube_download_output_template() -> str:
    """Get output template for YouTube downloads."""
    return str(LIBSYNC_DATA_DIR / "%(id)s_audio_download")


# Shazam cache paths
SHAZAM_CACHE_DIR = LIBSYNC_DATA_DIR / "shazam_cache"
SHAZAM_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_shazam_segment_cache_path(audio_file_path: str) -> str:
    """Get path for Shazam segment-level cache database.

    The cache is named using a hash of the audio file path to keep
    the filename short while remaining unique per audio file.

    Args:
        audio_file_path: Path to the audio file being processed

    Returns:
        Path to the SQLite cache database
    """
    import hashlib

    # Create a short hash of the audio path for the filename
    path_hash = hashlib.sha256(audio_file_path.encode()).hexdigest()[:12]
    return str(SHAZAM_CACHE_DIR / f"shazam_cache_{path_hash}.db")


# Utility functions
def get_sanitized_xml_path(xml_path: str) -> str:
    """Sanitize XML path for use in filenames."""
    return xml_path.replace("/", "_")
