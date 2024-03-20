"""
contains get_spotify_matches function and helpers
"""

import logging
import pprint
import urllib.parse

import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.constants import (
    MINIMUM_SIMILARITY_THRESHOLD,
    NUMBER_OF_RESULTS_PER_QUERY,
    USE_RB_TO_SPOTIFY_MATCHES_CACHE,
    USE_SPOTIFY_SEARCH_RESULTS_CACHE,
)
from utils.rekordbox_library import RekordboxCollection, RekordboxTrack
from utils.similarity_utils import calculate_similarities
from utils.string_utils import (
    get_artists_from_rekordbox_track,
    get_name_varieties_from_track_name,
    strip_punctuation,
)


def get_spotify_matches(
    rekordbox_to_spotify_map: dict[str, str],
    cached_search_search_results: dict,
    rekordbox_collection: RekordboxCollection,
    rb_track_ids_flagged_for_rematch: set[str],
) -> dict[str, str]:
    """attempt to map all songs in rekordbox library to spotify uris

    Args:
        rekordbox_to_spotify_map (dict[str, str]): map from rekordbox song ID to spotify URI.
            passed by reference, modified in place
        cached_search_search_results: dict [TODO: docs]
        rekordbox_collection (RekordboxCollection): dict of songs indexed by rekordbox track id

    Returns:
        dict[str, str]: reference to rekordbox_to_spotify_map argument which is modified in place
    """
    logging.debug(
        "running get_spotify_matches with rekordbox_collection:\n"
        + f"{pprint.pformat(rekordbox_collection)}"
    )
    print("  searching for spotify matches...")

    scope = ["user-library-read", "playlist-modify-private"]
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    logging.info(f"{len(rekordbox_collection)} total tracks in collection")

    rb_track_ids_to_look_up = []
    unmatched_tracks = []

    for rb_track_id in rekordbox_collection:
        if USE_RB_TO_SPOTIFY_MATCHES_CACHE and rb_track_id in rekordbox_to_spotify_map:
            if rb_track_id in rb_track_ids_flagged_for_rematch:
                rb_track_ids_to_look_up.append(rb_track_id)

            elif (
                rekordbox_to_spotify_map[rb_track_id] == ""
                or rekordbox_to_spotify_map[rb_track_id] is None
            ):
                logging.debug("libsync db has this track, but with no match")
                unmatched_tracks.append(rb_track_id)

            else:
                logging.debug(
                    "found a match in libsync db, skipping this spotify query"
                )

        else:
            logging.debug("not found, adding to list")
            rb_track_ids_to_look_up.append(rb_track_id)

    logging.info(
        f"{len(unmatched_tracks)} unmatched tracks. currently ignoring "
        + "(update in csv if you want to match these)"
    )

    # TODO: add CLI flag to add these tracks to rb_track_ids_to_look_up
    # so we can try to find matches again

    spotify_search_cache_hit_count = 0
    spotify_search_cache_miss_count = 0

    logging.info(f"{len(rb_track_ids_to_look_up)} tracks to match on spotify")
    for i, rb_track_id in enumerate(rb_track_ids_to_look_up):
        logging.debug(f"matching {i}/{len(rb_track_ids_to_look_up)}")

        rb_track = rekordbox_collection[rb_track_id]

        if (
            USE_SPOTIFY_SEARCH_RESULTS_CACHE
            and rb_track_id in cached_search_search_results
        ):
            spotify_search_cache_hit_count += 1
            logging.debug("found cached search results")
            spotify_search_results = cached_search_search_results[rb_track_id]
        else:
            spotify_search_cache_miss_count += 1
            logging.debug("couldn't find cached search results, searching spotify")
            spotify_search_results = get_spotify_search_results(spotify, rb_track)
            cached_search_search_results[rb_track_id] = spotify_search_results

        best_match_uri = find_best_track_match_uri(rb_track, spotify_search_results)
        rekordbox_to_spotify_map[rb_track_id] = (
            "" if best_match_uri is None else best_match_uri
        )
        if best_match_uri in spotify_search_results:
            logging.info(
                f"matched {rb_track} to "
                + pretty_print_spotify_track(spotify_search_results[best_match_uri])
            )
        else:
            logging.info(f"couldn't find a match for track {rb_track}")

    print("  done searching for spotify matches.")
    return rekordbox_to_spotify_map


def get_spotify_search_results(
    spotify_client: spotipy.Spotify,
    rekordbox_track: RekordboxTrack,
) -> list:
    """search spotify for a given rekordbox track.

    Args:
        spotify_client (spotipy.Spotify): spotipy client for using spotify api
        rekordbox_track (RekordboxTrack): reack object with members 'name','artist','album'

    Returns:
        search_result_tracks (dict): dict top results from various searches based on
            the rekordbox track, indexed by spotify URI
    """
    search_result_tracks = {}
    queries = get_spotify_queries_from_rekordbox_track(rekordbox_track)
    for query in queries:
        try:
            results = spotify_client.search(
                q=query, limit=NUMBER_OF_RESULTS_PER_QUERY, offset=0, type="track"
            )["tracks"]["items"]
            for track in results:
                search_result_tracks[track["uri"]] = track
        except requests.exceptions.ConnectionError as error:
            # maybe catch this at a lower level
            logging.exception(error)
            print(
                "error connecting to spotify. fix your internet connection and try again."
            )

    return search_result_tracks


def get_spotify_queries_from_rekordbox_track(
    rekordbox_track: RekordboxTrack,
):
    search_titles = get_name_varieties_from_track_name(rekordbox_track.name)
    search_artists = get_artists_from_rekordbox_track(rekordbox_track=rekordbox_track)
    search_titles.extend([strip_punctuation(term) for term in search_titles])
    search_artists.extend([strip_punctuation(term) for term in search_artists])

    query_lists = []
    for search_title in search_titles:
        for search_artist in search_artists:
            query_lists.append([search_artist, search_title])
            query_lists.append([search_title, search_artist])
            query_lists.append([search_title])
            query_lists.append([search_artist])

    queries = []
    for query_list in query_lists:
        # build query
        query = urllib.parse.quote(" ".join(query_list))
        queries.append(query)

    return queries


def pretty_print_spotify_track(track: object):
    return (
        ", ".join([artist["name"] for artist in track["artists"]])
        + " - "
        + track["name"]
    )


def find_best_track_match_uri(
    rekordbox_track: RekordboxTrack, spotify_search_results: dict
):
    """pick best track out of spotify search results.
    If best track is above similarity threshold, return it to client. Otherwise, return none.

    Args:
        rekordbox_track (RekordboxTrack): original track from rekordbox to compare with
        spotify_search_results (dict): search results from spotify to choose from

    Returns:
        str | None: spotify URI if one is found, otherwise None
    """
    logging.debug(
        f"running find_best_track_match_uri with rekordbox_track: {rekordbox_track}"
    )

    if len(spotify_search_results) < 1:
        logging.debug("spotify_search_results is empty. Returning None...")
        return None

    # find similarity metric
    # compare similarity for all tracks in list_of_spotify_tracks
    # make sure the top choice is similar enough to be worth considering

    # for each spotify URI key, similarities contains a dict of name similarity and artist similarity
    # logging.debug("track options from spotify search:")
    # for track in spotify_search_results.values():
    #     logging.debug(" - " + pretty_print_spotify_track(track=track))

    similarities = calculate_similarities(rekordbox_track, spotify_search_results)

    # sort based on similarities
    list_of_spotify_tracks = [
        [spotify_track, similarities[spotify_track["uri"]]]
        for spotify_track in spotify_search_results.values()
    ]

    list_of_spotify_tracks.sort(key=lambda entry: entry[1], reverse=True)

    logging.debug(
        f"track options from spotify search, sorted by similarity to rekordbox track {rekordbox_track}:"
    )
    for spotify_track, similarity in list_of_spotify_tracks:
        logging.debug(
            f" - {similarity:3}: " + pretty_print_spotify_track(spotify_track)
        )

    best_match = list_of_spotify_tracks[0]
    spotify_track = best_match[0]
    similarity = best_match[1]
    if similarity > MINIMUM_SIMILARITY_THRESHOLD:
        return spotify_track["uri"]
    else:
        return None
