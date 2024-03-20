"""sync rekordbox library to spotify playlists"""

import csv
import logging
import pickle

import requests
from analyze.get_rekordbox_library import get_rekordbox_library
from spotify.create_spotify_playlists import create_spotify_playlists
from spotify.get_spotify_matches import get_spotify_matches
from utils.string_utils import get_spotify_uri_from_url


def sync_rekordbox_to_spotify(
    rekordbox_xml_path: str,
    create_collection_playlist: bool,
    make_playlists_public: bool,
    include_loose_songs: bool,
) -> None:
    """sync a user's rekordbox playlists to their spotify account

    Args:
        rekordbox_xml_path (str): _description_
        create_collection_playlist (bool): _description_
        make_playlists_public (bool): _description_
        include_loose_songs (bool): _description_
    """

    libsync_cache_path = (
        f"data/{rekordbox_xml_path.replace('/', '_')}_libsync_sync_cache.db"
    )
    libsync_song_mapping_csv = (
        f"data/{rekordbox_xml_path.replace('/', '_')}_libsync_song_mapping_cache.csv"
    )
    logging.debug(
        "running sync_rekordbox_to_spotify.py with args: "
        + f"rekordbox_xml_path={rekordbox_xml_path}, "
        + f"libsync_cache_path={libsync_cache_path}, "
        + f"create_collection_playlist={create_collection_playlist}, "
        + f"make_playlists_public={make_playlists_public}, "
        + f"include_loose_songs={include_loose_songs}"
    )
    print("syncing rekordbox => spotify")

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
        logging.debug(error)
        print(f"no cache found. will create cache at '{libsync_cache_path}'.")
    except KeyError as error:
        logging.exception(error)
        print(f"error parsing cache at '{libsync_cache_path}'. clearing cache.")
        # TODO actually clear cache, also centralize this duplicated caching logic

    try:
        with open(libsync_song_mapping_csv, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # skip the headers
            csv_lines = [line for line in reader]
            logging.debug(f"len(csv_lines): {len(csv_lines)}")
            for line in csv_lines:
                rb_track_id, spotify_uri, spotify_url, flag_for_rematch = (
                    line[0],
                    line[3],
                    line[4],
                    line[5],
                )
                if spotify_url == "libsync:NOT_ON_SPOTIFY":
                    spotify_uri = "libsync:NOT_ON_SPOTIFY"
                elif spotify_url != "":
                    logging.debug(
                        "found a spotify URL manually input into the CSV by the user, "
                        + "trying to parse now"
                    )
                    # TODO: save logs to a file instead of stdout
                    # TODO: check for valid spotify url, or catch exception from underlying library
                    spotify_uri = get_spotify_uri_from_url(spotify_url)

                rekordbox_to_spotify_map[rb_track_id] = spotify_uri
                if flag_for_rematch != "":
                    rb_track_ids_flagged_for_rematch.add(rb_track_id)

        logging.debug(
            "len(rekordbox_to_spotify_map) (after reading from csv): "
            + f"{len(rekordbox_to_spotify_map)}"
        )

    except FileNotFoundError as error:
        logging.debug(error)
        print(
            f"no song mapping file found. will create mapping file at '{libsync_song_mapping_csv}'."
        )

    # get rekordbox db from xml
    try:
        rekordbox_library = get_rekordbox_library(
            rekordbox_xml_path, include_loose_songs
        )
        logging.debug(f"got rekordbox library: {rekordbox_library}")
    except FileNotFoundError as error:
        logging.debug(error)
        print(f"couldn't find '{rekordbox_xml_path}'. check the path and try again")
        return
    except TypeError as error:
        logging.exception(error)
        print(
            f"the file at '{rekordbox_xml_path}' is the wrong format. try exporting again"
        )
        # TODO: convert print statements to logging.info(),
        # except for stuff that should actually be printed
        return

    # map songs from the user's rekordbox library onto spotify search results
    get_spotify_matches(
        rekordbox_to_spotify_map,
        cached_search_search_results,
        rekordbox_library.collection,
        rb_track_ids_flagged_for_rematch,
    )

    # TODO: add CLI flag to skip creating playlists for debugging
    # create a playlist in the user's account for each rekordbox playlist
    try:
        create_spotify_playlists(
            playlist_id_map=playlist_id_map,
            rekordbox_playlists=rekordbox_library.playlists,
            rekordbox_to_spotify_map=rekordbox_to_spotify_map,
            create_collection_playlist=create_collection_playlist,
            make_playlists_public=make_playlists_public,
        )
        logging.debug("done writing playlists")
    except requests.exceptions.ConnectionError as error:
        # maybe catch this at a lower level
        logging.exception(error)
        print(
            "error connecting to spotify. fix your internet connection and try again."
        )

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

    with open(libsync_song_mapping_csv, "w", encoding="utf-8") as handle:
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
