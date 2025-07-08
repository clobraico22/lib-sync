"""contains utility functions to compare two song results"""

import logging
import unicodedata
from difflib import SequenceMatcher

from libsync.utils.constants import DEBUG_SIMILARITY
from libsync.utils.rekordbox_library import RekordboxTrack, SpotifySongCollection
from libsync.utils.string_utils import (
    get_artists_from_rb_track,
    get_name_varieties_from_track_name,
    remove_suffixes,
    strip_punctuation,
)

logger = logging.getLogger("libsync")


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
    logger.debug(f"get_string_similarity: {result:3} for '{string_1}' vs '{string_2}'")
    return result


def remove_accents(input_str):
    return unicodedata.normalize("NFKD", input_str)


def calculate_similarities(
    rb_track: RekordboxTrack, spotify_search_results: SpotifySongCollection
) -> dict:
    """calculate similarity to rb_track for each result in spotify_search_results

    Args:
        rb_track (RekordboxTrack): rekordbox track to compare with
        spotify_search_results (dict): dict of search results (spotify track URI mapped to song details)

    Returns:
        dict: spotify track URI mapped to similarity value
    """
    similarities = {}
    for spotify_track_uri, spotify_track_option in spotify_search_results.items():
        # normalize and clean up for best comparison
        spotify_song_name = remove_accents(
            strip_punctuation(remove_suffixes(spotify_track_option["name"]))
        ).strip()
        # TODO: improve this matching functionality:
        # -- test out remove_suffixes from the spotify name to get radio edits, etc
        # -- ideally, add logic to catch radio edits when nothing else is there,
        #    but prefer the version that you have on rekordbox
        # -- handle (feat. Artist Name)
        # -- handle '&' in artist names (at the spotify search level)
        rekordbox_song_names = [
            remove_accents(strip_punctuation(name)).strip()
            for name in get_name_varieties_from_track_name(rb_track.name.lower())
        ]

        # name similarity
        name_similarities = [
            get_string_similarity(spotify_song_name, rekordbox_song_name)
            for rekordbox_song_name in rekordbox_song_names
        ]

        # artist similarity
        spotify_artist_list = [artist["name"] for artist in spotify_track_option["artists"]]
        rekordbox_artist_list = [
            artist.lower() for artist in get_artists_from_rb_track(rb_track=rb_track)
        ]

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
