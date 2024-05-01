import csv
import logging
import pickle

from db import db_utils, db_write_operations
from utils import string_utils
from utils.constants import SpotifyMappingDbFlags
from utils.string_utils import get_spotify_uri_from_url

logger = logging.getLogger("libsync")


def get_cached_spotify_search_results(
    rekordbox_xml_path: str,
) -> dict[str, object]:
    """get cached search results
    this has a side effect of creating an empty cache if no cache is found, or the cache is invalid.

    Args:
        rekordbox_xml_path (str): xml path used for this run -
          this will be used to determine cache and csv paths

    Returns:
        dict[str, object]: results from API calls from previous libsync run,
          indexed by spotify search API query string
    """

    spotify_search_cache_path = db_utils.get_spotify_search_cache_path(
        rekordbox_xml_path
    )

    try:
        with open(spotify_search_cache_path, "rb") as handle:
            cached_spotify_search_results = pickle.load(handle)
            assert isinstance(cached_spotify_search_results, dict)
            return cached_spotify_search_results

    except FileNotFoundError as error:
        logger.debug(error)
        logger.info(f"no cache found. creating cache at '{spotify_search_cache_path}'.")

    except AssertionError as error:
        logger.debug(error)
        string_utils.print_libsync_status_error(
            f"error parsing cache at '{spotify_search_cache_path}'. replacing cache file."
        )

    # if getting cache failed, create empty cache and return empty dict
    db_write_operations.save_cached_spotify_search_results({}, rekordbox_xml_path)
    return {}


def get_playlist_id_map(
    rekordbox_xml_path: str,
) -> dict[str, str]:
    logger.debug("running get_playlist_id_map")
    user_spotify_playlist_mapping_db_path = (
        db_utils.get_spotify_playlist_mapping_db_path(
            rekordbox_xml_path,
            db_utils.get_spotify_user_id(),
        )
    )
    playlist_id_map = {}
    try:
        with open(
            user_spotify_playlist_mapping_db_path, mode="r", encoding="utf-8"
        ) as file:
            reader = csv.reader(file)
            next(reader, None)  # skip the headers
            csv_lines = [line for line in reader]
            logger.debug(f"len(csv_lines): {len(csv_lines)}")
            for line in csv_lines:
                playlist_name, spotify_playlist_id = (
                    line[0],
                    line[1],
                )
                # TODO: replace playlist name with playlist path (including folders)
                playlist_id_map[playlist_name] = spotify_playlist_id

        logger.debug(
            "len(playlist_id_map) (after reading from csv): "
            + f"{len(playlist_id_map)}"
        )
        return playlist_id_map

    except FileNotFoundError as error:
        logger.debug(error)
        logger.info(
            "no playlist mapping file found. will create mapping file at "
            + f"'{user_spotify_playlist_mapping_db_path}'."
        )

    return {}


def get_cached_sync_data(
    rekordbox_xml_path: str,
):
    """get cached data for sync command from files

    Args:
        rekordbox_xml_path (str): xml path used for this run -
          this will be used to determine cache and csv paths

    Returns:
        tuple: bundle of data (TODO: fill in details here)
    """

    rekordbox_to_spotify_map = {}
    rb_track_ids_flagged_for_rematch = set()

    # get song mappings data from csv
    libsync_song_mapping_csv_path = db_utils.get_libsync_song_mapping_csv_path(
        rekordbox_xml_path
    )
    try:
        with open(libsync_song_mapping_csv_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # skip the headers
            csv_lines = [line for line in reader]
            logger.debug(f"len(csv_lines): {len(csv_lines)}")
            for line in csv_lines:
                rb_track_id, spotify_uri, spotify_url, flag_for_rematch = (
                    line[0],
                    line[3],
                    line[4],
                    line[5],
                )
                if spotify_url == SpotifyMappingDbFlags.NOT_ON_SPOTIFY:
                    spotify_uri = SpotifyMappingDbFlags.NOT_ON_SPOTIFY
                elif spotify_url != "":
                    logger.debug(
                        "found a spotify URL manually input into the CSV by the user, "
                        + "trying to parse now"
                    )
                    # TODO: save debug level logs to file
                    # TODO: check for valid spotify url, or catch exception from underlying library
                    spotify_uri = get_spotify_uri_from_url(spotify_url)

                rekordbox_to_spotify_map[rb_track_id] = spotify_uri
                if flag_for_rematch != "":
                    rb_track_ids_flagged_for_rematch.add(rb_track_id)

        logger.debug(
            "len(rekordbox_to_spotify_map) (after reading from csv): "
            + f"{len(rekordbox_to_spotify_map)}"
        )

    except FileNotFoundError as error:
        logger.debug(error)
        logger.info(
            f"no song mapping file found. will create mapping file at '{libsync_song_mapping_csv_path}'."
        )

    return (rekordbox_to_spotify_map, rb_track_ids_flagged_for_rematch)


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
