import csv
import logging
import pickle

from libsync.db import db_read_operations, db_utils
from libsync.spotify.spotify_auth import SpotifyAuthManager
from libsync.utils.rekordbox_library import (
    PlaylistName,
    RekordboxLibrary,
    SpotifyPlaylistId,
)

logger = logging.getLogger("libsync")


def save_cached_spotify_search_results(
    spotify_search_results: dict[str, object], rekordbox_xml_path: str
):
    """save cached spotify search results in pickle format to save time next run

    Args:
        spotify_search_results (dict[str, object]): results from API calls,
          indexed by spotify search API query string
        rekordbox_xml_path (str): xml path used for this run -
          this will be used to determine cache and csv paths
    """

    spotify_search_cache_path = db_utils.get_spotify_search_cache_path(
        rekordbox_xml_path
    )

    logger.debug("save_cached_spotify_search_results")
    with open(spotify_search_cache_path, "wb") as handle:
        pickle.dump(spotify_search_results, handle, protocol=pickle.HIGHEST_PROTOCOL)


def save_pending_tracks_spotify_to_rekordbox(
    rekordbox_xml_path: str,
    new_songs_to_download: set[str],
    spotify_song_details: dict[str, dict[str, object]],
):
    pending_tracks_spotify_to_rekordbox_db_path = (
        db_utils.get_libsync_pending_tracks_spotify_to_rekordbox_db_path(
            rekordbox_xml_path
        )
    )

    logger.debug("save_cached_spotify_search_results")
    pending_tracks = {
        song_uri: spotify_song_details[song_uri] for song_uri in new_songs_to_download
    }

    with open(pending_tracks_spotify_to_rekordbox_db_path, "wb") as handle:
        pickle.dump(pending_tracks, handle, protocol=pickle.HIGHEST_PROTOCOL)


def save_list_of_user_playlists(
    playlist_id_map: dict[PlaylistName, SpotifyPlaylistId],
) -> None:
    user_id = SpotifyAuthManager.get_user_id()

    user_spotify_playlists_list_db_path = (
        db_utils.get_user_spotify_playlists_list_db_path(user_id)
    )
    playlists = set()
    try:
        playlists = set(
            db_read_operations.get_list_from_file(user_spotify_playlists_list_db_path)
        )
    except FileNotFoundError as error:
        logger.debug(error)
        logger.info(
            "no playlist data stored for this user previously. "
            + f"creating data file at '{user_spotify_playlists_list_db_path}'."
        )

    playlists.update(playlist_id_map.values())
    write_text_file_from_list(user_spotify_playlists_list_db_path, list(playlists))


def save_song_mappings_csv(
    rekordbox_library: RekordboxLibrary,
    rb_track_ids_flagged_for_rematch: set[str],
    rekordbox_to_spotify_map: dict[str, str],
):
    libsync_song_mapping_csv_path = db_utils.get_libsync_song_mapping_csv_path(
        rekordbox_library.xml_path
    )

    with open(libsync_song_mapping_csv_path, "w", encoding="utf-8") as handle:
        write = csv.writer(handle)
        write.writerow(
            [
                "Rekordbox id",
                "Artist",
                "Song title",
                "Spotify URI",
                "Spotify URL (input)",
                "Retry auto match (input)",
            ]
        )

        write.writerows(
            sorted(
                [
                    [
                        rb_track_id,
                        rekordbox_library.collection[rb_track_id].artist,
                        rekordbox_library.collection[rb_track_id].name,
                        spotify_uri,
                        "",
                        "1" if rb_track_id in rb_track_ids_flagged_for_rematch else "",
                    ]
                    for rb_track_id, spotify_uri in rekordbox_to_spotify_map.items()
                    if rb_track_id in rekordbox_library.collection
                ],
                key=lambda row: str(row[3]),
                reverse=True,
            )
        )


def save_playlist_id_map(
    rekordbox_xml_path: str, playlist_id_map: dict[PlaylistName, SpotifyPlaylistId]
):
    logger.debug("running save_playlist_id_map")
    user_spotify_playlist_mapping_db_path = (
        db_utils.get_spotify_playlist_mapping_db_path(
            rekordbox_xml_path, SpotifyAuthManager.get_user_id()
        )
    )

    with open(user_spotify_playlist_mapping_db_path, "w", encoding="utf-8") as handle:
        write = csv.writer(handle)
        write.writerow(
            [
                "Rekordbox playlist name (need to replace with path)",
                "Spotify playlist id",
            ]
        )

        write.writerows(
            sorted(
                [
                    [playlist_name, spotify_playlist_id]
                    for playlist_name, spotify_playlist_id in playlist_id_map.items()
                ],
                key=lambda row: str(row[0]),
            )
        )


def write_text_file_from_list(path: str, data_list: list[str]) -> set[str]:
    with open(path, "w", encoding="utf-8") as handle:
        handle.writelines([f"{item}\n" for item in data_list])
