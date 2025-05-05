"""
contains get_spotify_matches function and helpers
"""

import logging
import urllib.parse
from typing import Iterable, Optional

import spotipy.exceptions

from libsync.db import db_read_operations, db_write_operations
from libsync.spotify import spotify_api_utils
from libsync.utils import string_utils
from libsync.utils.constants import (
    MINIMUM_SIMILARITY_THRESHOLD_NEW_MATCHES,
    MINIMUM_SIMILARITY_THRESHOLD_PENDING_MATCHES,
    USE_RB_TO_SPOTIFY_MATCHES_CACHE,
    InteractiveWorkflowCommands,
    SpotifyMappingDbFlags,
)
from libsync.utils.rekordbox_library import (
    RekordboxLibrary,
    RekordboxTrack,
    RekordboxTrackID,
    SpotifySearchResults,
    SpotifySongCollection,
)
from libsync.utils.similarity_utils import calculate_similarities
from libsync.utils.string_utils import (
    get_artists_from_rb_track,
    get_name_varieties_from_track_name,
    get_spotify_uri_from_url,
    log_and_print,
    pretty_print_spotify_track,
    strip_punctuation,
)

logger = logging.getLogger("libsync")


class ExitAndSaveException(Exception):
    """Custom exception to signal exit and save operation."""


class SkipRemainingException(Exception):
    """Custom exception to signal skip remaining operation."""


def get_spotify_matches(
    rekordbox_to_spotify_map: dict[str, str],
    rekordbox_library: RekordboxLibrary,
    rb_track_ids_flagged_for_rematch: set[str],
    pending_tracks_spotify_to_rekordbox: dict[str, object],
    ignore_spotify_search_cache: bool,
    interactive_mode: bool,
    interactive_mode_pending_tracks: bool,  # Add this parameter
) -> dict[str, str]:
    """attempt to map all songs in rekordbox library to spotify uris

    Args:
        rekordbox_to_spotify_map (dict[str, str]): map from rekordbox song ID to spotify URI.
            passed by reference, modified in place
        rekordbox_library (RekordboxLibrary): rekordbox library to match with spotify
        rb_track_ids_flagged_for_rematch (set[str]): set of rekordbox song IDs that the user
            manually flagged for rematch
        pending_tracks_spotify_to_rekordbox (dict[str, str]): map from spotify uri to spotify song details object
        ignore_spotify_search_cache (bool): hit spotify apis to fetch songs
            instead of relying on local libsync cache
        interactive_mode (bool): run searching + matching process
            with manual input on failed auto match
        interactive_mode_pending_tracks (bool): run searching + matching process
            for pending tracks with manual input on failed auto match

    Returns:
        rekordbox_to_spotify_map (dict[str, str]): reference to rekordbox_to_spotify_map argument
            which is modified in place
    """
    # logger.debug(
    #     "running get_spotify_matches with rekordbox_library:\n"
    #     + f"{pprint.pformat(rekordbox_library)}"
    # )

    logger.debug(
        "running sync_rekordbox_to_spotify.py with args: "
        + ", ".join(
            [
                # f"rekordbox_to_spotify_map={rekordbox_to_spotify_map}",
                # f"spotify_search_results={spotify_search_results}",
                # f"rekordbox_library={rekordbox_library}",
                f"rb_track_ids_flagged_for_rematch={rb_track_ids_flagged_for_rematch}",
                # f"pending_tracks_spotify_to_rekordbox={pending_tracks_spotify_to_rekordbox}",
                f"ignore_spotify_search_cache={ignore_spotify_search_cache}",
                f"interactive_mode={interactive_mode}",
                f"interactive_mode_pending_tracks={interactive_mode_pending_tracks}",
            ]
        )
    )

    logger.info(f"{len(rekordbox_library.collection)} total tracks in collection")

    rb_track_ids_to_match = get_rb_track_ids_to_match(
        rekordbox_library.collection.keys(),
        rekordbox_to_spotify_map,
        rb_track_ids_flagged_for_rematch,
    )

    # TODO: improve UX for retrying matching

    logger.info(f"{len(rb_track_ids_to_match)} tracks to match on spotify")
    spotify_search_results = db_read_operations.get_cached_spotify_search_results(
        rekordbox_library.xml_path
    )

    if len(rb_track_ids_to_match) <= 0:
        string_utils.print_libsync_status("No new Rekordbox tracks to match", level=1)
        return rekordbox_to_spotify_map

    if len(pending_tracks_spotify_to_rekordbox) > 0:
        string_utils.print_libsync_status(
            "First, checking new Rekordbox tracks against Spotify pending tracks from previous run",
            level=1,
        )

        rekordbox_to_spotify_map = check_pending_tracks_for_matches(
            rb_track_ids_to_match,
            rekordbox_library,
            rekordbox_to_spotify_map,
            pending_tracks_spotify_to_rekordbox,
        )

        # cache rekordbox -> spotify mappings
        db_write_operations.save_song_mappings_csv(
            rekordbox_library,
            rb_track_ids_flagged_for_rematch,
            rekordbox_to_spotify_map,
        )

        rb_track_ids_to_match = [
            t
            for t in rb_track_ids_to_match
            if t not in rekordbox_to_spotify_map
            or rekordbox_to_spotify_map[t] == SpotifyMappingDbFlags.SKIP_TRACK
        ]

        if not interactive_mode_pending_tracks:
            string_utils.print_libsync_status(
                f"Skipping interactive matching against pending tracks for {len(rb_track_ids_to_match)} tracks",
                level=1,
            )

        elif len(rb_track_ids_to_match) == 0:
            string_utils.print_libsync_status(
                "No tracks left to match interactively against pending tracks",
                level=1,
            )

        else:
            rekordbox_to_spotify_map = (
                pick_best_pending_tracks_spotify_matches_interactively(
                    rb_track_ids_to_match,
                    rekordbox_library,
                    rekordbox_to_spotify_map,
                    pending_tracks_spotify_to_rekordbox,
                )
            )

        # cache rekordbox -> spotify mappings
        db_write_operations.save_song_mappings_csv(
            rekordbox_library,
            rb_track_ids_flagged_for_rematch,
            rekordbox_to_spotify_map,
        )

        string_utils.print_libsync_status_success("Done", level=1)
        # exit()

    spotify_search_results = get_spotify_search_results_and_update_cache(
        rb_track_ids_to_match, rekordbox_library, spotify_search_results
    )

    rekordbox_to_spotify_map = pick_best_spotify_matches_automatically(
        rb_track_ids_to_match,
        rekordbox_library,
        spotify_search_results,
        rekordbox_to_spotify_map,
    )

    # cache rekordbox -> spotify mappings
    db_write_operations.save_song_mappings_csv(
        rekordbox_library,
        rb_track_ids_flagged_for_rematch,
        rekordbox_to_spotify_map,
    )

    rb_track_ids_to_match = [
        t
        for t in rb_track_ids_to_match
        if t not in rekordbox_to_spotify_map
        or rekordbox_to_spotify_map[t] == SpotifyMappingDbFlags.SKIP_TRACK
    ]

    if not interactive_mode:
        string_utils.print_libsync_status(
            f"Skipping interactive matching for f{len(rb_track_ids_to_match)} tracks",
            level=1,
        )

    elif len(rb_track_ids_to_match) == 0:
        string_utils.print_libsync_status(
            "No tracks left to match interactively", level=1
        )

    else:
        rekordbox_to_spotify_map = pick_best_spotify_matches_interactively(
            rb_track_ids_to_match,
            rekordbox_library,
            spotify_search_results,
            rekordbox_to_spotify_map,
        )

    # cache rekordbox -> spotify mappings
    db_write_operations.save_song_mappings_csv(
        rekordbox_library,
        rb_track_ids_flagged_for_rematch,
        rekordbox_to_spotify_map,
    )

    string_utils.print_libsync_status_success("Done", level=1)

    return rekordbox_to_spotify_map


def get_spotify_search_results_and_update_cache(
    rb_track_ids_to_match: list[RekordboxTrackID],
    rekordbox_library: RekordboxLibrary,
    spotify_search_results: SpotifySearchResults,
):
    string_utils.print_libsync_status(
        f"Searching Spotify for matches for {len(rb_track_ids_to_match)} new Rekordbox tracks",
        level=1,
    )

    list_of_search_queries = {
        query
        for rb_track_id in rb_track_ids_to_match
        for query in get_spotify_queries_from_rb_track(
            rekordbox_library.collection[rb_track_id]
        )
        if query not in spotify_search_results
    }
    logger.debug(f"len(list_of_search_queries): {len(list_of_search_queries)}")
    logger.debug(
        f"len(set(list_of_search_queries)): {len(set(list_of_search_queries))}"
    )
    new_results_to_add = spotify_api_utils.get_spotify_search_results(
        list(list_of_search_queries)
    )
    logger.debug(f"len(new_results_to_add): {len(new_results_to_add)}")

    spotify_search_results.update(
        {
            query: results
            for query, results in new_results_to_add.items()
            if results is not None
        }
    )
    missing_search_results = {
        query for query, results in new_results_to_add.items() if results is None
    }
    logger.debug(f"len(spotify_search_results): {len(spotify_search_results)}")
    logger.debug(f"len(missing_search_results): {len(missing_search_results)}")

    # cache spotify search results
    db_write_operations.save_cached_spotify_search_results(
        spotify_search_results, rekordbox_library.xml_path
    )

    if len(missing_search_results) >= 1:
        string_utils.print_libsync_status_error(
            "some search results failed to load due to a connection issue. try again"
        )
        exit(1)

    return spotify_search_results


def check_pending_tracks_for_matches(
    rb_track_ids_to_match: list[RekordboxTrackID],
    rekordbox_library: RekordboxLibrary,
    rekordbox_to_spotify_map: dict[str, str],
    pending_tracks_spotify_to_rekordbox: dict[str, object],
):
    logger.debug(
        "running check_pending_tracks_for_matches for "
        + f"rb_track_ids_to_match: {rb_track_ids_to_match}"
        # + f" and pending_tracks_spotify_to_rekordbox: {pending_tracks_spotify_to_rekordbox}"
    )

    for i, rb_track_id in enumerate(rb_track_ids_to_match):
        logger.debug(
            f"automatically matching track {i + 1}/{len(rb_track_ids_to_match)}"
        )

        rb_track = rekordbox_library.collection[rb_track_id]

        logger.debug(
            f"len(pending_tracks_spotify_to_rekordbox): {len(pending_tracks_spotify_to_rekordbox)}"
        )

        best_match_uri = pick_matching_track_automatically(
            rb_track,
            pending_tracks_spotify_to_rekordbox,
            MINIMUM_SIMILARITY_THRESHOLD_PENDING_MATCHES,
        )
        if best_match_uri is None:
            logger.info(f"failed to auto match track {rb_track}")
            # don't update rekordbox_to_spotify_map.
            # if interactive mode is off, then we don't add failed auto matches to the db at all.

        else:
            logger.info(
                f" automatically matched {rb_track} to "
                + pretty_print_spotify_track(
                    pending_tracks_spotify_to_rekordbox[best_match_uri]
                )
            )
            rekordbox_to_spotify_map[rb_track_id] = best_match_uri

    return rekordbox_to_spotify_map


def pick_best_spotify_matches_automatically(
    rb_track_ids_to_match: list[RekordboxTrackID],
    rekordbox_library: RekordboxLibrary,
    spotify_search_results: SpotifySearchResults,
    rekordbox_to_spotify_map: dict[str, str],
):
    logger.debug(
        "running pick_best_spotify_matches_automatically for "
        + f"rb_track_ids_to_match: {rb_track_ids_to_match}"
    )

    for i, rb_track_id in enumerate(rb_track_ids_to_match):
        logger.debug(
            f"automatically matching track {i + 1}/{len(rb_track_ids_to_match)}"
        )

        rb_track = rekordbox_library.collection[rb_track_id]

        song_search_results = get_cached_results_for_track(
            rb_track, spotify_search_results
        )
        logger.debug(f"len(song_search_results): {len(song_search_results)}")

        best_match_uri = pick_matching_track_automatically(
            rb_track, song_search_results
        )
        if best_match_uri is None:
            logger.info(f"failed to auto match track {rb_track}")
            # don't update rekordbox_to_spotify_map.
            # if interactive mode is off, then we don't add failed auto matches to the db at all.

        else:
            logger.info(
                f" automatically matched {rb_track} to "
                + pretty_print_spotify_track(song_search_results[best_match_uri])
            )
            rekordbox_to_spotify_map[rb_track_id] = best_match_uri

    return rekordbox_to_spotify_map


def pick_best_pending_tracks_spotify_matches_interactively(
    rb_track_ids_to_match: list[RekordboxTrackID],
    rekordbox_library: RekordboxLibrary,
    rekordbox_to_spotify_map: dict[str, str],
    pending_tracks_spotify_to_rekordbox: SpotifySongCollection,
):
    logger.debug(
        "running pick_best_pending_tracks_spotify_matches_interactively for "
        + f"rb_track_ids_to_match: {rb_track_ids_to_match}"
        # + f" and pending_tracks_spotify_to_rekordbox: {pending_tracks_spotify_to_rekordbox}"
    )

    # if there are a lot of tracks left to manually match with pending tracks, let's sort by how well they matched.
    # going to duplicate some processing here now for the sake of readability.
    # doing the same processing that we do for each track in pick_matching_track_interactively_and_process_input here
    # just to sort. inefficient but not a big deal

    # TODO: if we successfully match a song, take it out of contention for future matches.
    rb_track_id_to_max_similarity_score = {
        rb_track_id: max(
            [
                track_tuple[1]
                for track_tuple in get_sorted_list_tracks_with_similarity(
                    rekordbox_library.collection[rb_track_id],
                    pending_tracks_spotify_to_rekordbox,
                )
            ]
        )
        for rb_track_id in rb_track_ids_to_match
    }
    sorted_rb_track_ids_to_match = sorted(
        rb_track_ids_to_match,
        key=lambda rb_track_id: rb_track_id_to_max_similarity_score[rb_track_id],
        reverse=True,
    )

    for i, rb_track_id in enumerate(sorted_rb_track_ids_to_match):
        logger.debug(
            f"interactively matching track {i + 1}/{len(sorted_rb_track_ids_to_match)}"
        )

        rb_track = rekordbox_library.collection[rb_track_id]

        logger.debug(
            f"len(pending_tracks_spotify_to_rekordbox): {len(pending_tracks_spotify_to_rekordbox)}"
        )

        try:
            rekordbox_to_spotify_map = (
                pick_matching_track_interactively_and_process_input(
                    rekordbox_to_spotify_map,
                    rb_track,
                    pending_tracks_spotify_to_rekordbox,
                )
            )

        except SkipRemainingException:
            logger.debug("skip remaining flag received")
            for rb_track_id in sorted_rb_track_ids_to_match[i:]:
                rekordbox_to_spotify_map[rb_track_id] = SpotifyMappingDbFlags.SKIP_TRACK

            return rekordbox_to_spotify_map

        except ExitAndSaveException:
            logger.debug("exit and save flag received")
            return rekordbox_to_spotify_map

    return rekordbox_to_spotify_map


def pick_best_spotify_matches_interactively(
    rb_track_ids_to_match: list[RekordboxTrackID],
    rekordbox_library: RekordboxLibrary,
    spotify_search_results: SpotifySearchResults,
    rekordbox_to_spotify_map: dict[str, str],
):
    logger.debug(
        "running pick_best_spotify_matches_interactively for "
        + f"rb_track_ids_to_match: {rb_track_ids_to_match}"
    )

    # if there are a lot of tracks left to manually match with pending tracks, let's sort by how well they matched.
    # going to duplicate some processing here now for the sake of readability.
    # doing the same processing that we do for each track in pick_matching_track_interactively_and_process_input here
    # just to sort. inefficient but not a big deal
    rb_track_id_to_max_similarity_score = {
        rb_track_id: max(
            [
                track_tuple[1]
                for track_tuple in get_sorted_list_tracks_with_similarity(
                    rekordbox_library.collection[rb_track_id],
                    get_cached_results_for_track(
                        rekordbox_library.collection[rb_track_id],
                        spotify_search_results,
                    ),
                )
            ]
        )
        for rb_track_id in rb_track_ids_to_match
    }
    sorted_rb_track_ids_to_match = sorted(
        rb_track_ids_to_match,
        key=lambda rb_track_id: rb_track_id_to_max_similarity_score[rb_track_id],
        reverse=True,
    )
    log_and_print(
        f"rb_track_id_to_max_similarity_score: {rb_track_id_to_max_similarity_score}"
    )
    log_and_print(f"sorted_rb_track_ids_to_match: {sorted_rb_track_ids_to_match}")

    for i, rb_track_id in enumerate(sorted_rb_track_ids_to_match):
        logger.debug(
            f"interactively matching track {i + 1}/{len(sorted_rb_track_ids_to_match)}"
        )

        rb_track = rekordbox_library.collection[rb_track_id]

        song_search_results = get_cached_results_for_track(
            rb_track, spotify_search_results
        )
        logger.debug(f"len(song_search_results): {len(song_search_results)}")

        try:
            rekordbox_to_spotify_map = (
                pick_matching_track_interactively_and_process_input(
                    rekordbox_to_spotify_map, rb_track, song_search_results
                )
            )

        except SkipRemainingException:
            logger.debug("skip remaining flag received")
            for rb_track_id in sorted_rb_track_ids_to_match[i:]:
                rekordbox_to_spotify_map[rb_track_id] = SpotifyMappingDbFlags.SKIP_TRACK

            return rekordbox_to_spotify_map

        except ExitAndSaveException:
            logger.debug("exit and save flag received")
            return rekordbox_to_spotify_map

    return rekordbox_to_spotify_map


def pick_matching_track_interactively_and_process_input(
    rekordbox_to_spotify_map: dict[str, str],
    rb_track: RekordboxTrack,
    song_search_results: dict[str, object],
):
    interactive_input_result = pick_matching_track_interactively(
        rb_track, song_search_results
    )

    if interactive_input_result == InteractiveWorkflowCommands.SKIP_TRACK:
        rekordbox_to_spotify_map[rb_track.id] = SpotifyMappingDbFlags.SKIP_TRACK

    elif interactive_input_result == InteractiveWorkflowCommands.SKIP_REMAINING:
        raise SkipRemainingException("skip remaining flag received")

    elif interactive_input_result == InteractiveWorkflowCommands.NOT_ON_SPOTIFY:
        rekordbox_to_spotify_map[rb_track.id] = SpotifyMappingDbFlags.NOT_ON_SPOTIFY

    elif interactive_input_result == InteractiveWorkflowCommands.EXIT_AND_SAVE:
        raise ExitAndSaveException("exit and save flag received")

    elif interactive_input_result == InteractiveWorkflowCommands.CANCEL:
        logger.debug(
            "pick_best_spotify_matches_interactively got cancel flag, exiting without saving"
        )
        exit()

    else:
        logger.debug(
            f"interactively picked interactive_input_result: {interactive_input_result}"
        )
        rekordbox_to_spotify_map[rb_track.id] = interactive_input_result

    return rekordbox_to_spotify_map


def get_rb_track_ids_to_match(
    rb_track_ids: Iterable[str],
    rekordbox_to_spotify_map: dict[str, str],
    rb_track_ids_flagged_for_rematch: set[str],
) -> list[str]:
    rb_track_ids_to_match = []
    skipped_tracks = []

    for rb_track_id in rb_track_ids:
        logger.debug(f"checking db for matches for track_id: {rb_track_id}")
        if (
            not USE_RB_TO_SPOTIFY_MATCHES_CACHE
            or rb_track_id not in rekordbox_to_spotify_map
        ):
            logger.debug("track not found in db, adding to list to search list")
            rb_track_ids_to_match.append(rb_track_id)

        else:
            if rb_track_id in rb_track_ids_flagged_for_rematch:
                logger.debug(
                    "track manually flagged for rematch, adding to list to search list"
                )
                rb_track_ids_to_match.append(rb_track_id)

            elif (
                rekordbox_to_spotify_map[rb_track_id]
                == SpotifyMappingDbFlags.SKIP_TRACK
            ):
                # logger.debug(
                #     "skipped matching this track last time, adding to list of skipped tracks"
                # )
                # skipped_tracks.append(rb_track_id)
                logger.debug(
                    "skipped matching this track last time, let's try matching it this time"
                )
                rb_track_ids_to_match.append(rb_track_id)

            else:
                logger.debug("track already matched, no need for lookup")

    logger.info(
        f"{len(skipped_tracks)} skipped tracks. currently ignoring "
        + "(update in csv if you want to match these)"
    )

    return rb_track_ids_to_match


def get_cached_results_for_track(
    rb_track: RekordboxTrack,
    spotify_search_results: SpotifySearchResults,
) -> SpotifySongCollection:
    """search spotify for a given rekordbox track.

    Args:
        rb_track (RekordboxTrack): track object with members 'name','artist','album'
        spotify_search_results (SpotifySongCollection): map of spotify URI to a spotify song object

    Returns:
        search_result_tracks (dict): dict top results from various searches based on
            the rekordbox track, indexed by spotify URI
    """
    logger.debug(f"running get_cached_results_for_track for track ID: {rb_track.id}")

    queries = get_spotify_queries_from_rb_track(rb_track)
    return {
        track["uri"]: track
        for query in queries
        if query in spotify_search_results
        for track in spotify_search_results[query]
    }


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
    logger.debug(f"get_spotify_queries_from_rb_track results: {queries}")
    return list(set(queries))


def pick_matching_track_automatically(
    rb_track: RekordboxTrack,
    song_search_results: SpotifySongCollection,
    min_similarity_threshold: float = MINIMUM_SIMILARITY_THRESHOLD_NEW_MATCHES,
) -> Optional[str]:
    """pick best track out of spotify search results.

    Args:
        rb_track (RekordboxTrack): original track from rekordbox to compare with
        spotify_search_results (dict): search results from spotify to choose from

    Returns:
        str: spotify URI if one is found, otherwise None
    """

    logger.debug(f"running pick_matching_track_automatically with rb_track: {rb_track}")

    tracks_with_similarity = get_sorted_list_tracks_with_similarity(
        rb_track, song_search_results
    )

    if len(tracks_with_similarity) == 0:
        return None

    best_spotify_track, best_similarity = tracks_with_similarity[0]

    if best_similarity > min_similarity_threshold:
        logger.debug(
            f"found a good match automatically, with similarity: {best_similarity} "
            + f"and track: {pretty_print_spotify_track(best_spotify_track)}"
        )
        return best_spotify_track["uri"]

    else:
        logger.debug(
            f"failed to find a good match automatically. best similarity: {best_similarity} "
            + f"and best track: {pretty_print_spotify_track(best_spotify_track)}"
        )
        return None


def pick_matching_track_interactively(
    rb_track: RekordboxTrack,
    song_search_results: dict[str, object],
) -> str:
    """interactively pick best track out of spotify search results.

    Args:
        rb_track (RekordboxTrack): original track from rekordbox to compare with
        song_search_results (dict): search results from spotify to choose from - can be empty

    Returns:
        str: spotify URI if one is selected, otherwise SKIP_TRACK signal
    """

    logger.debug(f"running pick_matching_track_interactively with rb_track: {rb_track}")

    tracks_with_similarity = get_sorted_list_tracks_with_similarity(
        rb_track, song_search_results
    )

    return get_interactive_input_for_track(rb_track, tracks_with_similarity)


def get_interactive_input_for_track(rb_track, list_of_spotify_tracks: list):
    """get input from user for interactive mode

    Args:
        list_of_spotify_tracks (list): _description_

    Returns:
        str: input from the user, validated
    """

    # cut off list at 10 results for UX
    list_of_spotify_tracks = list_of_spotify_tracks[:10]
    selection = get_valid_interactive_input(rb_track, list_of_spotify_tracks)
    if selection == "s":
        log_and_print("skipping this track")
        return InteractiveWorkflowCommands.SKIP_TRACK

    elif selection == "skip_remaining":
        log_and_print("skipping the rest of the tracks")
        return InteractiveWorkflowCommands.SKIP_REMAINING

    elif selection == "m":
        log_and_print("marking song as missing")
        return InteractiveWorkflowCommands.NOT_ON_SPOTIFY

    elif selection == "x":
        log_and_print("exiting and saving")
        return InteractiveWorkflowCommands.EXIT_AND_SAVE

    elif selection == "cancel":
        log_and_print("exiting without saving")
        return InteractiveWorkflowCommands.CANCEL

    elif selection.isdigit():
        index = int(selection) - 1
        spotify_track = list_of_spotify_tracks[int(selection) - 1][0]
        log_and_print(
            f"selected track index: {index}, track: {pretty_print_spotify_track(spotify_track)}"
        )
        return spotify_track["uri"]

    elif "spotify" in selection:
        return selection

    return None


def get_valid_interactive_input(rb_track: RekordboxTrack, list_of_spotify_tracks: list):
    """get input from user for a single rekordbox track, given a list of potential spotify tracks

    Args:
        rb_track (RekordboxTrack): track to match
        list_of_spotify_tracks (list): list of spotify tracks to choose from,
          should be sorted. can be empty.

    Returns:
        str: input from the user, validated. may be a spotify URI or a command.
    """
    search_query = urllib.parse.quote(f"{rb_track.artist} - {rb_track.name}")
    web_search_url = f"https://open.spotify.com/search/{search_query}"
    log_and_print(
        "---------------------------------------------------"
        + "-------------------------------------------------"
    )
    log_and_print(f"looking for a match for rekordbox track with id: {rb_track}")
    log_and_print(f"url to search spotify for this song: {web_search_url}")

    for i, (spotify_track, similarity) in enumerate(list_of_spotify_tracks):
        log_and_print(
            f"{i + 1:3}. {int(similarity * 100):3}%: "
            + pretty_print_spotify_track(spotify_track, include_url=True)
        )

    while True:
        user_input = input(
            "Enter one of the following options:\n"
            + '  "s" to skip\n'
            + '  "skip_remaining" to skip the rest of the tracks for this section\n'
            + '  "m" to mark a song as missing on spotify\n'
            + '  "x" to exit and save matches\n'
            + '  "cancel" to exit without saving\n'
            + (
                f"  any number between 1 and {len(list_of_spotify_tracks)} to select one of the results from the list above\n"
                if len(list_of_spotify_tracks) >= 1
                else ""
            )
            + "  or paste a spotify link to the track to save it\n"
            + "Your choice: "
        )
        user_input = user_input.strip()
        if user_input.lower() in ("s", "skip_remaining", "m", "x", "cancel"):
            return user_input

        elif user_input.isdigit() and 1 <= int(user_input) <= len(
            list_of_spotify_tracks
        ):
            return user_input

        elif "spotify" in user_input:
            spotify_url = user_input.strip()
            try:
                logger.debug(
                    "detected manually pasted spotify link:"
                    + f" '{spotify_url}', trying to parse now"
                )

                return get_spotify_uri_from_url(spotify_url)

            except spotipy.exceptions.SpotifyException as error:
                logger.debug(error)
                log_and_print("Invalid spotify link. Try again.")

        else:
            log_and_print("Invalid input. Try again.")


# being called incorrectly rn
def get_sorted_list_tracks_with_similarity(
    rb_track: RekordboxTrack, song_search_results: SpotifySongCollection
):
    """get list of spotify tracks sorted by similarity to rekordbox track

    Args:
        rb_track (RekordboxTrack): rekordbox track to compare against
        song_search_results (SpotifySongCollection): tracks to compare against

    Returns:
        list: list of tuples, each containing a spotify track and its similarity score
    """

    similarities = calculate_similarities(rb_track, song_search_results)

    tracks_with_similarity = [
        [spotify_track, similarities[spotify_track["uri"]]]
        for spotify_track in song_search_results.values()
    ]

    # sort based on similarities
    tracks_with_similarity.sort(key=lambda entry: entry[1], reverse=True)

    logger.debug(
        f"track options from spotify search, sorted by similarity to rekordbox track {rb_track}:"
    )
    for spotify_track, similarity in tracks_with_similarity:
        logger.debug(
            f"* {similarity:3.2f}: " + pretty_print_spotify_track(spotify_track)
        )

    return tracks_with_similarity
