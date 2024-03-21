import csv
import logging
import pickle

from utils.constants import NOT_ON_SPOTIFY_FLAG
from utils.string_utils import get_spotify_uri_from_url

logger = logging.getLogger("libsync")


def get_cached_sync_data(
    libsync_cache_path: str,
    libsync_song_mapping_csv_path: str,
):
    """get cached data for sync command from file

    Args:
        libsync_cache_path (str): _description_
        libsync_song_mapping_csv_path (str): _description_

    Returns:
        _type_: _description_
    """

    rekordbox_to_spotify_map = {}
    playlist_id_map = {}
    cached_search_search_results = {}
    rb_track_ids_flagged_for_rematch = set()

    # get libsync cache from file
    try:
        with open(libsync_cache_path, "rb") as handle:
            cache = pickle.load(handle)
            (
                playlist_id_map,
                cached_search_search_results,
            ) = (
                cache["playlist_id_map"],
                cache["cached_search_search_results"],
            )
    except FileNotFoundError as error:
        logger.debug(error)
        print(f"no cache found. will create cache at '{libsync_cache_path}'.")
    except KeyError as error:
        logger.exception(error)
        print(f"error parsing cache at '{libsync_cache_path}'. clearing cache.")
        # TODO actually clear cache, also centralize this duplicated caching logic

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
                if spotify_url == NOT_ON_SPOTIFY_FLAG:
                    spotify_uri = NOT_ON_SPOTIFY_FLAG
                elif spotify_url != "":
                    logger.debug(
                        "found a spotify URL manually input into the CSV by the user, "
                        + "trying to parse now"
                    )
                    # TODO: save logs to a file instead of stdout
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
        print(
            f"no song mapping file found. will create mapping file at '{libsync_song_mapping_csv_path}'."
        )

    return (
        rekordbox_to_spotify_map,
        playlist_id_map,
        cached_search_search_results,
        rb_track_ids_flagged_for_rematch,
    )
