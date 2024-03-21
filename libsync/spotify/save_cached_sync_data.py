import csv
import logging
import pickle

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.rekordbox_library import RekordboxLibrary

logger = logging.getLogger("libsync")


def save_cached_sync_data(
    libsync_cache_path: str,
    playlist_id_map: dict[str, str],
    cached_search_search_results: dict[str, object],
    libsync_song_mapping_csv_path: str,
    rekordbox_library: RekordboxLibrary,
    rb_track_ids_flagged_for_rematch: set[str],
    rekordbox_to_spotify_map: dict[str, str],
):
    """save cached data from sync command to a file

    Args:
        libsync_cache_path (str): _description_
        playlist_id_map (dict[str, str]): _description_
        cached_search_search_results (dict[str, object]): _description_
        libsync_song_mapping_csv_path (str): _description_
        rekordbox_library (RekordboxLibrary): _description_
        rb_track_ids_flagged_for_rematch (set[str]): _description_
        rekordbox_to_spotify_map (dict[str, str]): _description_
    """

    with open(libsync_cache_path, "wb") as handle:
        pickle.dump(
            {
                "playlist_id_map": playlist_id_map,
                "cached_search_search_results": cached_search_search_results,
            },
            # TODO: add ops script to clear individual caches, or break caches out into individual files
            handle,
            protocol=pickle.HIGHEST_PROTOCOL,
        )

    with open(libsync_song_mapping_csv_path, "w", encoding="utf-8") as handle:
        # using csv.writer method from CSV package
        write = csv.writer(handle)
        write.writerow(
            [
                "Rekordbox id",
                "Artist",
                "Song title",
                "Spotify URI (don't touch)",
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
                ],
                key=lambda row: str(row[3]),
                reverse=True,
            )
        )

    # save playlists to db of playlists libsync owns for the current spotify user id
    user_spotify_playlists_list_db_path = get_user_spotify_playlists_list_db_path()
    playlists = set()
    try:
        playlists = set(get_list_from_file(user_spotify_playlists_list_db_path))
    except FileNotFoundError as error:
        logger.debug(error)
        logger.info(
            "no playlist data stored for this user previously. "
            + f"creating data file at '{user_spotify_playlists_list_db_path}'."
        )

    playlists.update(playlist_id_map.values())
    save_libsync_spotify_playlists_for_current_user(
        user_spotify_playlists_list_db_path, list(playlists)
    )


def get_user_spotify_playlists_list_db_path() -> str:
    scope = [
        "user-library-read",
    ]
    auth_manager = SpotifyOAuth(scope=scope)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user_id = spotify.current_user()["id"]
    return f"data/{user_id}_libsync_spotify_playlists.txt"


def get_list_from_file(list_file_path) -> set[str]:
    """get list from file path stored as plain text, line separated

    Args:
        list_file_path (_type_): _description_

    Returns:
        set[str]: _description_
    """

    lines = []
    try:
        with open(list_file_path, "r", encoding="utf-8") as handle:
            for line in handle.readlines():
                lines.append(line.strip())

    except FileNotFoundError as error:
        logger.debug(error)
        logger.info(
            "no playlist data stored for this user previously. "
            + f"creating data file at '{list_file_path}'."
        )

    return lines


def save_libsync_spotify_playlists_for_current_user(
    user_spotify_playlists_list_db_path: str, playlists: list[str]
) -> set[str]:
    with open(user_spotify_playlists_list_db_path, "w", encoding="utf-8") as handle:
        handle.writelines([f"{playlist}\n" for playlist in playlists])
