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
    CANCEL_FLAG,
    EXIT_AND_SAVE_FLAG,
    MINIMUM_SIMILARITY_THRESHOLD,
    NOT_ON_SPOTIFY_FLAG,
    NUMBER_OF_RESULTS_PER_QUERY,
    SKIP_TRACK_FLAG,
    USE_RB_TO_SPOTIFY_MATCHES_CACHE,
)
from utils.rekordbox_library import RekordboxCollection, RekordboxTrack
from utils.similarity_utils import calculate_similarities
from utils.string_utils import (
    get_artists_from_rb_track,
    get_name_varieties_from_track_name,
    get_spotify_uri_from_url,
    pretty_print_spotify_track,
    strip_punctuation,
)

logger = logging.getLogger("libsync")


def get_spotify_matches(
    rekordbox_to_spotify_map: dict[str, str],
    cached_spotify_search_results: dict,
    rekordbox_collection: RekordboxCollection,
    rb_track_ids_flagged_for_rematch: set[str],
    ignore_spotify_search_cache: bool,
    interactive_mode: bool,
) -> dict[str, str]:
    """attempt to map all songs in rekordbox library to spotify uris

    Args:
        rekordbox_to_spotify_map (dict[str, str]): map from rekordbox song ID to spotify URI.
            passed by reference, modified in place
        cached_spotify_search_results (dict): [TODO: docs]
        rekordbox_collection (RekordboxCollection): dict of songs indexed by rekordbox track id
        ignore_spotify_search_cache (bool): hit spotify apis to fetch songs
            instead of relying on local libsync cache
        interactive_mode (bool): run searching + matching process
            with manual input on failed auto match

    Returns:
        rekordbox_to_spotify_map (dict[str, str]): reference to rekordbox_to_spotify_map argument
            which is modified in place
        cached_spotify_search_results (dict[str, object]): cache of spotify search results to save
    """
    logger.debug(
        "running get_spotify_matches with rekordbox_collection:\n"
        + f"{pprint.pformat(rekordbox_collection)}"
    )

    logger.debug(
        "running sync_rekordbox_to_spotify.py with args: "
        + ", ".join(
            [
                # f"rekordbox_to_spotify_map={rekordbox_to_spotify_map}",
                # f"cached_spotify_search_results={cached_spotify_search_results}",
                # f"rekordbox_collection={rekordbox_collection}",
                f"rb_track_ids_flagged_for_rematch={rb_track_ids_flagged_for_rematch}",
                f"ignore_spotify_search_cache={ignore_spotify_search_cache}",
                f"interactive_mode={interactive_mode}",
            ]
        )
    )

    print("  searching for spotify matches...")

    scope = ["user-library-read", "playlist-modify-private"]
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    logger.info(f"{len(rekordbox_collection)} total tracks in collection")

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
                logger.debug("libsync db has this track, but with no match")
                unmatched_tracks.append(rb_track_id)

            else:
                logger.debug("found a match in libsync db, skipping this spotify query")

        else:
            logger.debug("not found, adding to list")
            rb_track_ids_to_look_up.append(rb_track_id)

    logger.info(
        f"{len(unmatched_tracks)} unmatched tracks. currently ignoring "
        + "(update in csv if you want to match these)"
    )

    # TODO: improve UX for retrying matching

    logger.info(f"{len(rb_track_ids_to_look_up)} tracks to match on spotify")
    for i, rb_track_id in enumerate(rb_track_ids_to_look_up):
        logger.debug(f"matching track {i + 1}/{len(rb_track_ids_to_look_up)}")

        rb_track = rekordbox_collection[rb_track_id]

        spotify_search_results = get_spotify_search_results(
            spotify, rb_track, cached_spotify_search_results
        )

        best_match_uri = find_best_track_match_uri(
            rb_track, spotify_search_results, interactive_mode
        )
        if best_match_uri == SKIP_TRACK_FLAG:
            rekordbox_to_spotify_map[rb_track_id] = ""

        elif best_match_uri == NOT_ON_SPOTIFY_FLAG:
            rekordbox_to_spotify_map[rb_track_id] = NOT_ON_SPOTIFY_FLAG

        elif best_match_uri == EXIT_AND_SAVE_FLAG:
            return (
                rekordbox_to_spotify_map,
                cached_spotify_search_results,
            )

        elif best_match_uri == CANCEL_FLAG:
            exit()

        else:
            rekordbox_to_spotify_map[rb_track_id] = best_match_uri

        if best_match_uri in spotify_search_results:
            logger.info(
                f"matched {rb_track} to "
                + pretty_print_spotify_track(spotify_search_results[best_match_uri])
            )
        else:
            logger.info(f"couldn't find a match for track {rb_track}")

    print("  done searching for spotify matches.")
    return (
        rekordbox_to_spotify_map,
        cached_spotify_search_results,
    )


def get_spotify_search_results(
    spotify_client: spotipy.Spotify,
    rb_track: RekordboxTrack,
    cached_spotify_search_results: dict,
) -> list:
    """search spotify for a given rekordbox track.

    Args:
        spotify_client (spotipy.Spotify): spotipy client for using spotify api
        rb_track (RekordboxTrack): reack object with members 'name','artist','album'

    Returns:
        search_result_tracks (dict): dict top results from various searches based on
            the rekordbox track, indexed by spotify URI
    """
    search_result_tracks = {}
    queries = get_spotify_queries_from_rb_track(rb_track)
    for query in queries:
        if not query:  # TODO: figure out what is causing empty queries and remove them from the list
            continue
        if query in cached_spotify_search_results:
            results = cached_spotify_search_results[query]
        else:
            try:
                results = spotify_client.search(
                    q=query, limit=NUMBER_OF_RESULTS_PER_QUERY, offset=0, type="track"
                )["tracks"]["items"]
                cached_spotify_search_results[query] = results

            except requests.exceptions.ConnectionError as error:
                # maybe catch this at a lower level
                logger.exception(error)
                print(
                    "error connecting to spotify. fix your internet connection and try again."
                )

        for track in results:
            if track is None:
                logger.warning(
                    f"track in spotify search results is None! This is unexpected and may indicate an issue with data returned from Spofify API.\nResults: {results}."
                )
                continue

            search_result_tracks[track["uri"]] = track

    return search_result_tracks


def get_spotify_queries_from_rb_track(
    rb_track: RekordboxTrack,
):
    search_titles = get_name_varieties_from_track_name(rb_track.name)
    search_artists = get_artists_from_rb_track(rb_track=rb_track)
    search_titles.extend([strip_punctuation(term) for term in search_titles])
    search_artists.extend([strip_punctuation(term) for term in search_artists])

    query_lists = []
    for search_title in search_titles:
        for search_artist in search_artists:
            query_lists.append([search_artist, search_title])
            query_lists.append([search_title, search_artist])
            query_lists.append([search_title])
            query_lists.append([search_artist])

    queries = [" ".join(query_list).lower() for query_list in query_lists]
    queries = [urllib.parse.quote(query) for query in queries]
    queries = [query.replace("%20", "+") for query in queries]
    return queries


def find_best_track_match_uri(
    rb_track: RekordboxTrack,
    spotify_search_results: dict,
    interactive_mode: bool,
):
    """pick best track out of spotify search results.
    If best track is above similarity threshold, return it to client. Otherwise, return none.

    Args:
        rb_track (RekordboxTrack): original track from rekordbox to compare with
        spotify_search_results (dict): search results from spotify to choose from
        interactive_mode (bool):

    Returns:
        str | None: spotify URI if one is found, otherwise None
    """
    logger.debug(f"running find_best_track_match_uri with rb_track: {rb_track}")

    if len(spotify_search_results) < 1:
        logger.debug("spotify_search_results is empty. Returning None...")
        return SKIP_TRACK_FLAG

    similarities = calculate_similarities(rb_track, spotify_search_results)

    # sort based on similarities
    list_of_spotify_tracks = [
        [spotify_track, similarities[spotify_track["uri"]]]
        for spotify_track in spotify_search_results.values()
    ]

    list_of_spotify_tracks.sort(key=lambda entry: entry[1], reverse=True)

    logger.info(
        f"track options from spotify search, sorted by similarity to rekordbox track {rb_track}:"
    )
    for spotify_track, similarity in list_of_spotify_tracks:
        logger.info(
            f" - {similarity:3.2f}: " + pretty_print_spotify_track(spotify_track)
        )

    best_match = list_of_spotify_tracks[0]
    spotify_track = best_match[0]
    similarity = best_match[1]
    if similarity > MINIMUM_SIMILARITY_THRESHOLD:
        return spotify_track["uri"]

    elif interactive_mode:
        return get_interactive_input(rb_track, list_of_spotify_tracks)

    else:
        return None


def get_interactive_input(rb_track, list_of_spotify_tracks: list):
    """get input from user for interactive mode

    Args:
        list_of_spotify_tracks (list): _description_

    Returns:
        str: input from the user, validated
    """

    # cut off list at 10 results for UX
    list_of_spotify_tracks = list_of_spotify_tracks[:10]
    # key to save and exit
    # link to spotify search url to get the track url yourself and paste it in
    # maybe also link to the song itself - opening it in finder?
    # with the web app it could be possible to fetch the album art from the file using rekordbox info
    # but that doesn't scale to a web app architecture
    # type a number 1-10 to select a high ranking track (also include link)
    selection = get_valid_interactive_input(rb_track, list_of_spotify_tracks)
    if selection == "s":
        print("skipping this track")
        return SKIP_TRACK_FLAG

    elif selection == "m":
        print("marking song as missing")
        return NOT_ON_SPOTIFY_FLAG

    elif selection == "x":
        print("exiting and saving")
        return EXIT_AND_SAVE_FLAG

    elif selection == "cancel":
        print("exiting without saving")
        return CANCEL_FLAG

    elif selection.isdigit():
        index = int(selection) - 1
        spotify_track = list_of_spotify_tracks[int(selection) - 1][0]
        logger.debug(
            f"selected track index: {index}, track: {pretty_print_spotify_track(spotify_track)}"
        )
        return spotify_track["uri"]

    elif "spotify" in selection:
        return selection

    return None


def get_valid_interactive_input(rb_track, list_of_spotify_tracks: list):
    """get input from user for interactive mode

    Args:
        list_of_spotify_tracks (list): _description_

    Returns:
        str: input from the user, validated
    """
    search_query = urllib.parse.quote(f"{rb_track.artist} - {rb_track.name}")
    web_search_url = f"https://open.spotify.com/search/{search_query}"
    print(
        "---------------------------------------------------"
        + "-------------------------------------------------"
    )
    print(f"looking for a match for rekordbox track with id: {rb_track}")
    print(f"url to search spotify for this song: {web_search_url}")

    for i, (spotify_track, similarity) in enumerate(list_of_spotify_tracks):
        print(
            f"{i + 1:3}. {int(similarity * 100):3}%: "
            + pretty_print_spotify_track(spotify_track, include_url=True)
        )

    while True:
        user_input = input(
            'enter "s" to skip, "m" to mark a song as missing on spotify, '
            + '"x" to exit and save matches, "cancel" to exit without saving, '
            + f"any number between 1 and {len(list_of_spotify_tracks)} to select "
            + "one of the results from the list above, or paste a spotify link to "
            + "the track to save it: "
        )
        user_input = user_input.strip()
        if user_input.lower() in ("s", "m", "x", "cancel"):
            return user_input

        elif user_input.isdigit() and 1 <= int(user_input) <= len(
            list_of_spotify_tracks
        ):
            return user_input

        elif "spotify" in user_input:
            try:
                spotify_uri = get_spotify_uri_from_url(user_input.strip())
                return spotify_uri

            except Exception as e:
                logger.debug(e)
                print("Invalid spotify link. Try again.")

        else:
            print("Invalid input. Try again.")
