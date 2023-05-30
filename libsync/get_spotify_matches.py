"""
contains get_spotify_matches function and helpers
"""

import logging
import pprint
import urllib.parse
from datetime import datetime

import spotipy
from rekordbox_library import RekordboxCollection, RekordboxTrack
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth


def get_spotify_matches(
    rekordbox_to_spotify_map: dict[str, str], rekordbox_collection: RekordboxCollection
) -> dict[str, str]:
    """attempt to map all songs in rekordbox library to spotify uris

    Args:
        rekordbox_to_spotify_map (dict[str, str]): map from rekordbox song ID to spotify URI.
            passed by reference, modified in place
        rekordbox_collection (RekordboxCollection): set of songs

    Returns:
        dict[str, str]: reference to rekordbox_to_spotify_map argument which is modified in place
    """

    logging.debug(
        "running get_spotify_matches with rekordbox_collection:\n"
        + f"{pprint.pformat(rekordbox_collection)}"
    )

    # TODO: currently doing nothing with these search results,
    # eventually the interactive component can use them to provide options
    library_search_results = {}
    failed_matches = []

    scope = ["user-library-read", "playlist-modify-private"]
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    for rb_track in rekordbox_collection:
        if rb_track.id in rekordbox_to_spotify_map:
            logging.debug("found a match in libsync db, skipping this spotify query")
            continue

        best_match_uri = "next"
        # spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        spotify_search_results = search_spotify_for_rekordbox_track(
            spotify,
            rb_track,
        )
        logging.debug(
            f"Search results for track {rb_track}: "
            + f"{pprint.pformat([track['name'] for track in spotify_search_results['items']])}"
        )

        library_search_results[rb_track.id] = spotify_search_results
        best_match_uri = find_best_track_match_uri(
            rb_track, spotify_search_results["items"]
        )
        if best_match_uri is None:
            logging.warning(f"could not find a good match for the track {rb_track}")
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

    with open(f"failed_matches_{datetime.now()}.txt", "w", encoding="utf-8") as file:
        file.write(
            "The below files were not found on Spotify. "
            + "Consider updating the metadata before re-running lib-sync.\n"
        )
        for line in failed_matches:
            file.write(f"\t{line}\n")


def search_spotify_for_rekordbox_track(
    spotify_client: spotipy.Spotify,
    rekordbox_track: RekordboxTrack,
) -> dict[str, list]:
    """search spotify for a given rekordbox track.

    Args:
        spotify_client (spotipy.Spotify): spotipy client for using spotify api
        rekordbox_track (RekordboxTrack): reack object with members 'name','artist','album'

    Returns:
        search_result_tracks (dict[str,list]): dictionary of track results from search.
        'items' key will return track information for first page of results
    """
    search_list = [rekordbox_track.name, rekordbox_track.artist]
    query = urllib.parse.quote(" ".join(search_list))
    search_result_tracks = spotify_client.search(q=query, type="track", market="US")[
        "tracks"
    ]
    return search_result_tracks


def try_to_find_perfect_match_and_fall_back_on_user_input(
    rekordbox_track: RekordboxTrack, list_of_spotify_tracks: list
):
    if rekordbox_track.name.strip() == list_of_spotify_tracks[0]:
        logging.debug(
            f"Found an exact match for rekordbox_track:\n{pprint.pformat(rekordbox_track)}"
        )
        return list_of_spotify_tracks[0]

    # TODO: Implement algo to find best tracks
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


# NOTE: WIP!!
def find_best_track_match_uri(
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
    logging.debug(
        f"running find_best_track_match with rekordbox_track:\n{pprint.pformat(rekordbox_track)}"
    )
    if not list_of_spotify_tracks:
        logging.debug("list_of_spotify_tracks is empty. Returning None...")
        return None

    return list_of_spotify_tracks[0]["uri"]
    # try_to_find_perfect_match_and_fall_back_on_user_input(
    #     rekordbox_track, list_of_spotify_tracks
    # )
