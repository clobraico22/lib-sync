import logging
import pprint
import urllib.parse
from difflib import SequenceMatcher as SM
from datetime import datetime

import spotipy
from dotenv import load_dotenv
from rekordbox_library import RekordboxCollection, RekordboxTrack
from spotipy.oauth2 import SpotifyClientCredentials


load_dotenv()


def get_spotify_matches(rekordbox_collection: RekordboxCollection) -> dict[str, str]:
    """attempt to map all songs in rekordbox library to spotify uris

    Args:
        rekordbox_collection (RekordboxCollection): set of songs

    Returns:
        dict[str, str]: map from rekordbox song ID to spotify URI
    """

    logging.info(
        f"running get_spotify_matches with rekordbox_collection:\n{pprint.pformat(rekordbox_collection)}"
    )

    match_map = {}
    failed_matches = []
    for rb_track in rekordbox_collection:
        best_match_uri = "next"
        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        spotify_search_track_results = search_spotify_for_rekordbox_track(
            spotify,
            rb_track,
        )
        logging.debug(
            f"Search results for track {rb_track}: {pprint.pformat([track['name'] for track in spotify_search_track_results['items']])}"
        )

        best_match_uri = find_best_track_match_uri(
            rb_track, spotify_search_track_results["items"]
        )
        while best_match_uri == "next" and spotify_search_track_results["next"]:
            spotify_search_track_results = spotify.next(spotify_search_track_results)[
                "tracks"
            ]
            best_match = find_best_track_match_uri(
                rb_track, spotify_search_track_results["items"]
            )

        if best_match_uri is None:
            logging.warning(f"could not find a good match for the track {rb_track}")
            failed_matches.append(rb_track)
        match_map[rb_track.id] = best_match_uri

    if failed_matches:
        export_failed_matches_to_file(failed_matches)
    return match_map


def export_failed_matches_to_file(failed_matches: list[RekordboxTrack]):
    """export a list of rekordbox track that were unable to be found in spotify to a txt file

    Args:
        failed_matches (list[RekordboxTrack]): list of failed rekordbox tracks
    """

    with open(f"failed_matches_{datetime.now()}.txt", "w") as fp:
        fp.write(
            "The below files were not found on Spotify. Consider updating the metadata before re-running lib-sync.\n"
        )
        for line in failed_matches:
            fp.write(f"\t{line}\n")


def search_spotify_for_rekordbox_track(
    spotify_client: spotipy.Spotify,
    rekordbox_track: RekordboxTrack,
    *,
    market: str = "US",
) -> dict[str, list]:
    """search spotify for a given rekordbox track.Z

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


# NOTE: WIP!!
def find_best_track_match_uri(
    rekordbox_track: RekordboxTrack, list_of_spotify_tracks: list
):
    """finds the best uri of matching spotify track, given a rekordbox track

    Args:
        rekordbox_track (RekordboxTrack): _description_
        list_of_spotify_tracks (list): list of spotify tracks from a spotify search

    Returns:
        str: uri of the matching spotify track; If an exact match is not found, the user either selects the uri index, 0, or 11.
             0 returns None. 11 iterates to the next page of results
    """
    logging.info(
        f"running find_best_track_match with rekordbox_track:\n{pprint.pformat(rekordbox_track)}"
    )
    if not list_of_spotify_tracks:
        logging.warning(f"list_of_spotify_tracks is empty. Returning None...\n")
        return None
    if rekordbox_track.name.strip() == list_of_spotify_tracks[0]:
        logging.info(
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
            track_uri = track["uri"]
            potential_match_strings[
                i
            ] = f"{track_name} - Artist(s): {artists} Album: {album}"
            i += 1

        potential_match_strings[11] = "See next page of results"

        print(f"No exact matches were found for {rekordbox_track}")

        for k, v in potential_match_strings.items():
            print(f"  {k}: {v}")
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
