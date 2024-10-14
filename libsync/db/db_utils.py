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


def get_libsync_pending_tracks_spotify_to_rekordbox_db_path(
    rekordbox_xml_path: str,
) -> str:
    return f"data/libsync_pending_tracks_spotify_to_rekordbox_cache_{get_sanitized_xml_path(rekordbox_xml_path)}.csv"


def get_sanitized_xml_path(xml_path: str) -> str:
    return xml_path.replace("/", "_")
