"""contains utility functions to compare two song results"""

import logging
import unicodedata
from difflib import SequenceMatcher

from utils.constants import DEBUG_SIMILARITY
from utils.string_utils import (
    get_artists_from_rekordbox_track,
    get_name_varieties_from_track_name,
    strip_punctuation,
)


def calculate_similarity_metric(similarity_matrix: dict):
    """how good is this similarity matrix

    Args:
        similarity_matrix (dict): name similarity and artist similarity

    Returns:
        float: between 0 and 1, how high is the similarity metric score (higher is more similar)
    """
    return similarity_matrix["name_similarity"] * similarity_matrix["artist_similarity"]


def get_string_similarity(string_1: str, string_2: str) -> float:
    result = SequenceMatcher(None, string_1.lower(), string_2.lower()).ratio()
    logging.debug(
        f" - get_string_similarity: {result:3} for '{string_1}' vs '{string_2}'"
    )
    return result


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    only_ascii = nfkd_form.encode("ASCII", "ignore")
    return str(only_ascii)


def calculate_similarities(rekordbox_track, spotify_search_results) -> dict:
    similarities = {}
    for spotify_track_uri, spotify_track_option in spotify_search_results.items():
        # normalize and clean up for best comparison
        spotify_song_name = remove_accents(
            strip_punctuation(spotify_track_option["name"])
        )
        # TODO: should we remove_suffixes from the spotify name? to get radio edits, etc
        # need to add logic to catch radio edits when nothing else is there,
        # but prefer the version that you have on rekordbox
        # Maybe also add something to remove (feat. Artist Name)
        rekordbox_song_names = [
            remove_accents(strip_punctuation(name))
            for name in get_name_varieties_from_track_name(rekordbox_track.name)
        ]

        # name similarity
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

    return similarities
