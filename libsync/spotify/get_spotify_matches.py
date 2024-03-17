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
    DEBUG_SIMILARITY,
    MINIMUM_SIMILARITY_THRESHOLD,
    NUMBER_OF_RESULTS_PER_QUERY,
    RESOLVE_FAILED_MATCHES,
    USE_RB_TO_SPOTIFY_MATCHES_CACHE,
)
from utils.file_utils import export_failed_matches_to_file
from utils.rekordbox_library import RekordboxCollection, RekordboxTrack
from utils.similarity_utils import calculate_similarities
from utils.string_utils import (
    check_if_spotify_url_is_valid,
    get_artists_from_rekordbox_track,
    get_name_varieties_from_track_name,
    strip_punctuation,
)


def get_spotify_matches(
    rekordbox_to_spotify_map: dict[str, str],
    cached_search_search_results: dict,
    rekordbox_collection: RekordboxCollection,
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

    failed_matches = []

    scope = ["user-library-read", "playlist-modify-private"]
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    for rb_track_id, rb_track in rekordbox_collection.items():
        # if already in db, skip it
        if USE_RB_TO_SPOTIFY_MATCHES_CACHE and rb_track_id in rekordbox_to_spotify_map:
            logging.debug("found a match in libsync db, skipping this spotify query")
            continue

        if rb_track_id in cached_search_search_results:
            spotify_search_results = cached_search_search_results[rb_track_id]
        else:
            spotify_search_results = get_spotify_search_results(spotify, rb_track)
            cached_search_search_results[rb_track_id] = spotify_search_results

        logging.debug(
            f"Search results for track {rb_track}: "
            + f"{pprint.pformat([track['name'] for track in spotify_search_results.values()])}"
        )

        best_match_uri = find_best_track_match_uri(rb_track, spotify_search_results)
        if best_match_uri is None:
            failed_matches.append(rb_track)
        else:
            rekordbox_to_spotify_map[rb_track_id] = best_match_uri

    if RESOLVE_FAILED_MATCHES:
        rekordbox_to_spotify_map = resolve_failed_matches(failed_matches, rekordbox_to_spotify_map)
    else:
        export_failed_matches_to_file(failed_matches)

    return rekordbox_to_spotify_map


def resolve_failed_matches(
    failed_matches: list[RekordboxTrack],
    rekordbox_to_spotify_map: dict[str, str],
):
    """get user input to fix failed automatic matches

    Args:
        failed_matches (list[RekordboxTrack]): list of tracks that couldn't be automatically matched
        rekordbox_to_spotify_map (dict[str, str]): map from rekordbox song ID to spotify URI.
            passed by reference, modified in place

    Returns:
        _type_: _description_
    """
    for rb_track in failed_matches:
        correct_uri = get_correct_spotify_url_from_user(rb_track)
        if correct_uri:
            # correct_url = convert_uri_to_url(correct_uri)
            rekordbox_to_spotify_map[rb_track.id] = correct_uri

        elif check_if_track_should_be_ignored_in_future_from_user(rb_track):
            rekordbox_to_spotify_map[rb_track.id] = None

    return rekordbox_to_spotify_map


def get_correct_spotify_url_from_user(rb_track):
    # TODO: consider using click for user input https://click.palletsprojects.com/en/8.1.x/
    correct_spotify_url_input = input(
        f"Couldn't find a good match for {rb_track}. Please paste the matching spotify link here (press 'Enter' to skip): "
    ).strip(" ")
    print(f"Entered {correct_spotify_url_input=}")
    while True:
        if correct_spotify_url_input == "" or check_if_spotify_url_is_valid(
            correct_spotify_url_input
        ):
            return correct_spotify_url_input

        correct_spotify_url_input = input(
            "The given response is invalid. Please try again (press 'Enter' to skip): "
        ).strip("")


def check_if_track_should_be_ignored_in_future_from_user(rb_track):
    ignore_track_in_future_input = (
        input(
            "No link entered. Would you like lib-sync to ignore this track in the future? [y/n]: "
        )
        .lower()
        .strip(" ")
    )
    while True:
        if ignore_track_in_future_input in {"y", "yes", "ye"}:
            return True
        elif ignore_track_in_future_input in {"n", "no"}:
            return False

        ignore_track_in_future_input = (
            input(
                "The given response is invalid. Please enter 'y' or 'n'.\nWould you like lib-sync to ignore this track in the future? [y/n]: "
            )
            .lower()
            .strip(" ")
        )


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
        results = spotify_client.search(
            q=query, limit=NUMBER_OF_RESULTS_PER_QUERY, offset=0, type="track"
        )["tracks"]["items"]
        if DEBUG_SIMILARITY:
            print(f"query: {query} got # of results: {len(results)}")
        for track in results:
            search_result_tracks[track["uri"]] = track

    return search_result_tracks


def get_spotify_queries_from_rekordbox_track(
    rekordbox_track: RekordboxTrack,
):
    search_titles = get_name_varieties_from_track_name(rekordbox_track.name)
    search_artists = get_artists_from_rekordbox_track(rekordbox_track=rekordbox_track)

    queries = []
    for search_title in search_titles:
        for search_artist in search_artists:
            search_terms = [search_artist, search_title]
            # try artist first, then song name first
            for ordered_search_terms in [search_terms, reversed(search_terms)]:
                # remove punctuation
                ordered_search_terms = [strip_punctuation(term) for term in ordered_search_terms]
                # build query
                query = urllib.parse.quote(" ".join(ordered_search_terms))
                queries.append(query)

    return queries


def find_best_track_match_uri(rekordbox_track: RekordboxTrack, spotify_search_results: dict):
    """pick best track out of spotify search results.
    If best track is above similarity threshold, return it to client. Otherwise, return none.

    Args:
        rekordbox_track (RekordboxTrack): original track from rekordbox to compare with
        spotify_search_results (dict): search results from spotify to choose from

    Returns:
        str | None: spotify URI if one is found, otherwise None
    """
    logging.debug(
        f"running find_best_track_match_uri with rekordbox_track:\n{pprint.pformat(rekordbox_track)}"
    )

    if len(spotify_search_results) < 1:
        logging.debug("spotify_search_results is empty. Returning None...")
        return None

    # find similarity metric
    # compare similarity for all tracks in list_of_spotify_tracks
    # make sure the top choice is similar enough to be worth considering

    # for each spotify URI key, similarities contains a dict of name similarity and artist similarity
    similarities = calculate_similarities(rekordbox_track, spotify_search_results)

    # sort based on similarities
    list_of_spotify_tracks = [
        [spotify_track, similarities[spotify_track["uri"]]]
        for spotify_track in spotify_search_results.values()
    ]
    list_of_spotify_tracks.sort(key=lambda entry: entry[1], reverse=True)

    best_match = list_of_spotify_tracks[0]
    spotify_track = best_match[0]
    similarity = best_match[1]
    if similarity > MINIMUM_SIMILARITY_THRESHOLD:
        return spotify_track["uri"]
    else:
        return None
