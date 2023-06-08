"""
contains get_spotify_matches function and helpers
"""

import logging
import pprint
import re
import string
import urllib.parse
from datetime import datetime
from difflib import SequenceMatcher

import spotipy
from rekordbox_library import RekordboxCollection, RekordboxTrack
from spotipy.oauth2 import SpotifyOAuth

ARTIST_LIST_DELIMITERS = r",| & |vs\.|\n|ft\.|feat\.|featuring| / |; "
NUMBER_OF_RESULTS_PER_QUERY = 5
# while prototyping, leave this off
USE_SAVED_DB_MATCHES = False
# turn this on for debugging without the spotify match module
SKIP_GET_SPOTIFY_MATCHES = False
DEBUG_SIMILARITY = False
MINIMUM_SIMILARITY_THRESHOLD = 0.9


def get_spotify_matches(
    rekordbox_to_spotify_map: dict[str, str],
    library_search_results: dict,
    rekordbox_collection: RekordboxCollection,
) -> dict[str, str]:
    """attempt to map all songs in rekordbox library to spotify uris

    Args:
        rekordbox_to_spotify_map (dict[str, str]): map from rekordbox song ID to spotify URI.
            passed by reference, modified in place
        library_search_results: dict [TODO]
        rekordbox_collection (RekordboxCollection): set of songs

    Returns:
        dict[str, str]: reference to rekordbox_to_spotify_map argument which is modified in place
    """
    if SKIP_GET_SPOTIFY_MATCHES:
        return
    logging.debug(
        "running get_spotify_matches with rekordbox_collection:\n"
        + f"{pprint.pformat(rekordbox_collection)}"
    )

    # TODO: cache these results in local db to cut down on iteration time during testing
    library_search_results = {}
    failed_matches = []

    scope = ["user-library-read", "playlist-modify-private"]
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    for rb_track in rekordbox_collection:
        # if already in db, skip it
        if USE_SAVED_DB_MATCHES and rb_track.id in rekordbox_to_spotify_map:
            logging.debug("found a match in libsync db, skipping this spotify query")
            continue

        if rb_track.id in library_search_results:
            spotify_search_results = library_search_results[rb_track.id]
        else:
            spotify_search_results = get_spotify_search_results(spotify, rb_track)
            library_search_results[rb_track.id] = spotify_search_results

        logging.debug(
            f"Search results for track {rb_track}: "
            + f"{pprint.pformat([track['name'] for track in spotify_search_results.values()])}"
        )

        best_match_uri = find_best_track_match_uri(rb_track, spotify_search_results)
        if best_match_uri is None:
            failed_matches.append(rb_track)
        else:
            rekordbox_to_spotify_map[rb_track.id] = best_match_uri

    if failed_matches:
        export_failed_matches_to_file(failed_matches)

    return rekordbox_to_spotify_map


def export_failed_matches_to_file(failed_matches: list[RekordboxTrack]):
    """export a list of rekordbox track that were unable to be found in spotify to a txt file

    Args:
        failed_matches (list[RekordboxTrack]): list of failed rekordbox tracks
    """

    with open(
        f"failed_matches_{datetime.now()}.txt".replace(" ", "_"), "w", encoding="utf-8"
    ) as file:
        file.write(
            "The below files were not found on Spotify. "
            + "Consider updating the metadata before re-running lib-sync.\n"
        )
        for line in failed_matches:
            file.write(f"\t{line}\n")


def remove_original_mix(song_title: str) -> str:
    trimmed_song_title = re.sub(
        r"[\(\[]original mix[\)\]]", "", song_title, flags=re.IGNORECASE
    )
    return trimmed_song_title


def remove_extended_mix(song_title: str) -> str:
    trimmed_song_title = re.sub(
        r"[\(\[]extended mix[\)\]]", "", song_title, flags=re.IGNORECASE
    )
    return trimmed_song_title


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


def get_artists_from_rekordbox_track(
    rekordbox_track: RekordboxTrack,
):
    return [
        artist.strip()
        for artist in re.split(ARTIST_LIST_DELIMITERS, rekordbox_track.artist)
    ]


def get_name_varieties_from_track_name(name: str):
    return set(
        title.strip()
        for title in [
            name,
            remove_original_mix(name),
            remove_extended_mix(name),
        ]
    )


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
                ordered_search_terms = [
                    strip_punctuation(term) for term in ordered_search_terms
                ]
                # build query
                query = urllib.parse.quote(" ".join(ordered_search_terms))
                queries.append(query)

    return queries


def try_to_find_perfect_match_and_fall_back_on_user_input(
    rekordbox_track: RekordboxTrack, list_of_spotify_tracks: list
):
    """finds the best uri of matching spotify track, given a rekordbox track

    Args:
        rekordbox_track (RekordboxTrack): _description_
        list_of_spotify_tracks (list): list of spotify tracks from a spotify search

    Returns:
        str: uri of the matching spotify track.
        If an exact match is not found, the user either selects the uri index, 0, or 11.
        0 returns None. 11 iterates to the next page of results
    """
    if rekordbox_track.name.strip() == list_of_spotify_tracks[0]:
        logging.debug(
            f"Found an exact match for rekordbox_track:\n{pprint.pformat(rekordbox_track)}"
        )
        return list_of_spotify_tracks[0]

    else:
        potential_match_strings = {}
        potential_match_strings[0] = "None"
        i = 1
        for track in list_of_spotify_tracks:
            album = track["album"]["name"]
            artists = [artist["name"] for artist in track["artists"]]
            track_name = track["name"]
            # track_uri = track["uri"]
            potential_match_strings[
                i
            ] = f"{track_name} - Artist(s): {artists} Album: {album}"
            i += 1

        potential_match_strings[11] = "See next page of results"

        print(f"No exact matches were found for {rekordbox_track}")

        for index, track_string in potential_match_strings.items():
            print(f"  {index}: {track_string}")
        selected_match_i = int(
            input("Please select an an option from the list [0-11]: ")
        )
        print(
            f"Selected option {selected_match_i}: {potential_match_strings[selected_match_i]}"
        )
        if not selected_match_i:
            print("This track will be ignored and left out of spotify playlist.)")
            return None
        elif selected_match_i == 11:
            return "next"

        return list_of_spotify_tracks[selected_match_i - 1]["uri"]


def calculate_similarity_metric(similarity_matrix: dict):
    """how good is this similarity matrix

    Args:
        similarity_matrix (dict): name similarity and artist similarity

    Returns:
        float: between 0 and 1, how high is the similarity metric score (higher is more similar)
    """
    return similarity_matrix["name_similarity"] * similarity_matrix["artist_similarity"]


def strip_punctuation(name: str) -> str:
    return name.translate(str.maketrans("", "", string.punctuation))


def get_string_similarity(string_1: str, string_2: str) -> float:
    return SequenceMatcher(None, string_1.lower(), string_2.lower()).ratio()


def find_best_track_match_uri(
    rekordbox_track: RekordboxTrack, spotify_search_results: dict
):
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
    similarities = {}
    for spotify_track_uri, spotify_track_option in spotify_search_results.items():
        # name similarity
        spotify_song_name = strip_punctuation(spotify_track_option["name"])
        rekordbox_song_names = [
            strip_punctuation(name)
            for name in list(get_name_varieties_from_track_name(rekordbox_track.name))
        ]
        name_similarities = [
            get_string_similarity(spotify_song_name, rekordbox_song_name)
            for rekordbox_song_name in rekordbox_song_names
        ]

        # artist similarity
        spotify_artist_list = [
            artist["name"] for artist in spotify_track_option["artists"]
        ]
        rekordbox_artist_list = get_artists_from_rekordbox_track(
            rekordbox_track=rekordbox_track
        )

        artist_similarities = [
            get_string_similarity(spotify_artist, rekordbox_artist)
            for spotify_artist in spotify_artist_list
            for rekordbox_artist in rekordbox_artist_list
        ]
        best_name_similarity = max(name_similarities)
        best_artist_similarity = max(artist_similarities)
        similarity = {
            "name_similarity": best_name_similarity,
            "artist_similarity": best_artist_similarity,
        }
        similarity_metric = calculate_similarity_metric(similarity)
        similarities[spotify_track_uri] = similarity_metric
        if DEBUG_SIMILARITY:
            print(f"overall similarity score: {similarity_metric}, ")
            print(
                f"-- name similarity score: {best_name_similarity}, "
                + f"rekordbox_name varieties: {rekordbox_song_names}, "
                + f"spotify_name: {spotify_song_name}, "
            )
            print(
                f"-- best artist similarity score: {best_artist_similarity}, "
                + f"rekordbox_artists: {rekordbox_artist_list}, "
                + f"spotify_name: {spotify_artist_list}, "
            )

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
        # print(f"probably a good match for {rekordbox_track}: {spotify_track['uri']}")
        return spotify_track["uri"]
    else:
        # TODO: add multiple choice or just allow pasting in a url or uri
        print(
            f"couldn't find a good match for {rekordbox_track}. "
            + f"best match (similarity {similarity}): "
            + f"{spotify_track['name']} - "
            + f"{[artist['name'] for artist in spotify_track['artists']]} ({spotify_track['uri']})"
        )
        # input("enter to continue")
        return None
