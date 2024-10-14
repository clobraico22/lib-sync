import asyncio
import logging
from typing import Iterable

import aiohttp
import requests
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm

from libsync.db import db_utils
from libsync.utils import constants, string_utils

logger = logging.getLogger("libsync")


# worker


async def fetch_playlist_details_worker(session, access_token, playlist_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    params = {
        "fields": "name,uri,tracks.total,tracks.items(track.id,track.name),tracks.limit"
    }

    async with session.get(url, headers=headers, params=params) as response:
        if not response.ok:
            logger.debug(response)
            raise ConnectionError("fetching playlist failed")

        return playlist_id, await response.json()


async def fetch_additional_tracks_worker(
    session, access_token, playlist_id, limit, offset
):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit={limit}&offset={offset}"
    params = {"fields": "total,items(track.id,track.name),limit"}
    try:
        async with session.get(url, headers=headers, params=params) as response:
            if not response.ok:
                logger.debug(response)
                # TODO: swallow these errors with a custom error handler (set_exception_handler)
                raise ConnectionError("fetching additional tracks failed")

            return playlist_id, limit, offset, await response.json()

    except ConnectionResetError as e:
        logger.debug(e)
        raise ConnectionError("fetching additional tracks failed") from e


async def fetch_additional_playlists_worker(
    session, access_token, user_id, limit, offset
):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists?limit={limit}&offset={offset}"
    params = {"fields": "items(id,name)"}
    async with session.get(url, headers=headers, params=params) as response:
        if not response.ok:
            logger.debug(response)
            raise ConnectionError("fetching playlist failed")

        return await response.json()


# TODO: handle API errors and retries in this file
async def overwrite_playlists_worker(
    session, access_token, playlist_id, track_uri_list
):
    logger.debug(
        f"clearing playlist: {playlist_id}, then adding {len(track_uri_list)} tracks."
    )
    pages = [
        track_uri_list[i : i + constants.SPOTIFY_API_ITEMS_PER_PAGE]
        for i in range(0, len(track_uri_list), constants.SPOTIFY_API_ITEMS_PER_PAGE)
    ]
    if len(pages) < 1:
        return []

    responses = []
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    # first page
    json = {"uris": []}
    async with session.put(url, headers=headers, json=json) as response:
        if not response.ok:
            raise ConnectionError("updating playlist failed")

        responses.append(await response.json())

    # following pages
    for page in pages:
        json = {"uris": page}
        async with session.post(url, headers=headers, json=json) as response:
            if not response.ok:
                raise ConnectionError("updating playlist failed")

            responses.append(await response.json())

    return responses


async def fetch_spotify_song_details_worker(
    session, access_token, list_of_sp_uris
) -> list[str, str, str]:
    headers = {"Authorization": f"Bearer {access_token}"}
    list_of_sp_ids = [
        string_utils.get_spotify_id_from_uri(sp_uri) for sp_uri in list_of_sp_uris
    ]
    url = f"https://api.spotify.com/v1/tracks?ids={'%2C'.join(list_of_sp_ids)}"
    async with session.get(url, headers=headers) as response:
        if not response.ok:
            logger.debug(response)
            raise ConnectionError("fetching song details failed", response)

        logger.debug(f"response: {response}")
        result = await response.json()
        logger.debug(f"result: {result}")
        return [[track["uri"], track] for track in result["tracks"]]


async def fetch_spotify_search_results_worker(session, access_token, query):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/search?q={query}&type=track"

    try:
        async with session.get(url, headers=headers) as response:
            if not response.ok:
                logger.debug(response)
                return query, None

            return query, (await response.json())["tracks"]["items"]

    except KeyError as e:
        logger.error(f"KeyError in fetch_spotify_search_results_worker: {e}")
        return query, None


# controller


async def fetch_playlist_details_controller(playlist_ids):
    access_token = get_spotify_access_token(
        [
            "user-library-read",
            "playlist-read-private",
            "playlist-read-collaborative",
        ]
    )
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_playlist_details_worker(session, access_token, playlist_id)
            for playlist_id in playlist_ids
        ]
        playlist_info_list = []
        for future in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Fetching Spotify playlists",
        ):
            playlist_info_list.append(await future)

        return {
            playlist_id: playlist_info
            for playlist_id, playlist_info in playlist_info_list
        }

    return {}


async def fetch_additional_tracks_controller(params_list: list[list[str, int, int]]):
    access_token = get_spotify_access_token(
        [
            "user-library-read",
            "playlist-read-private",
            "playlist-read-collaborative",
        ]
    )
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_additional_tracks_worker(
                session, access_token, playlist_id, limit, offset
            )
            for playlist_id, limit, offset in params_list
        ]

        additional_track_details = []
        for future in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Fetching more Spotify playlists",
        ):
            additional_track_details.append(await future)

        return additional_track_details

    return []


async def fetch_additional_playlists_controller(params_list: list[list[str, int, int]]):
    access_token = get_spotify_access_token(
        [
            "user-library-read",
            "playlist-read-private",
            "playlist-read-collaborative",
        ]
    )
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_additional_playlists_worker(
                session, access_token, user_id, limit, offset
            )
            for user_id, limit, offset in params_list
        ]

        additional_playlists = []
        for future in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Fetching more Spotify playlists",
        ):
            additional_playlists.append(await future)

        return additional_playlists

    return []


async def overwrite_playlists_controller(params_list: list[list[str, list[str]]]):
    access_token = get_spotify_access_token(
        [
            "user-library-read",
            "playlist-read-private",
            "playlist-read-collaborative",
            "playlist-modify-private",
            "playlist-modify-public",
        ]
    )
    async with aiohttp.ClientSession() as session:
        tasks = [
            overwrite_playlists_worker(
                session, access_token, playlist_id, track_uri_list
            )
            for playlist_id, track_uri_list in params_list
        ]

        overwrite_playlists_results = []
        for future in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Modifying playlists",
        ):
            overwrite_playlists_results.append(await future)

        return overwrite_playlists_results

    return []


async def fetch_spotify_song_details_controller(
    spotify_uris: list[str],
) -> dict[str, dict[str, object]]:
    # split the uris into batches - can run the batches in parallel
    batches = [
        spotify_uris[i : i + constants.SPOTIFY_API_GET_TRACKS_ITEMS_PER_PAGE]
        for i in range(
            0, len(spotify_uris), constants.SPOTIFY_API_GET_TRACKS_ITEMS_PER_PAGE
        )
    ]
    if len(batches) < 1:
        return {}

    access_token = get_spotify_access_token(
        [
            "user-library-read",
            "playlist-read-private",
            "playlist-read-collaborative",
        ]
    )
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_spotify_song_details_worker(session, access_token, batch)
            for batch in batches
        ]

        track_details_list = []
        for future in tqdm(
            asyncio.as_completed(tasks), total=len(tasks), desc="Fetching song details"
        ):
            track_details_list.append(await future)

        return {
            track_uri: track
            for batch in track_details_list
            for track_uri, track in batch
        }


async def fetch_spotify_search_results_controller(queries):
    access_token = get_spotify_access_token(
        [
            "user-library-read",
            "playlist-read-private",
            "playlist-read-collaborative",
        ]
    )
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_spotify_search_results_worker(session, access_token, query)
            for query in queries
        ]
        search_results_list = []
        for future in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Fetching search results",
        ):
            search_results_list.append(await future)

        return {
            query: results
            for query, results in search_results_list
            if results is not None
        }

    return {}


# driver


def get_user_playlists_details(playlists: Iterable[str]) -> dict[str, list]:
    """get user playlists to check against deleted playlists

    Args:
        playlist_id_map (dict[str, str]): map from rekordbox playlist name to spotify playlist id

    Returns:
        dict[str, list]: map from spotify playlist id to list of spotify track URIs
    """

    initial_playlist_info = asyncio.run(fetch_playlist_details_controller(playlists))
    user_spotify_playlists = {}
    follow_up_job_params = []

    for playlist_id, playlist_info in initial_playlist_info.items():
        tracks = playlist_info["tracks"]
        user_spotify_playlists[playlist_id] = [
            item["track"]["id"] for item in tracks["items"]
        ]
        total = tracks["total"]
        limit = tracks["limit"]
        if total > limit:
            follow_up_job_params.extend(
                [[playlist_id, limit, offset] for offset in range(limit, total, limit)]
            )

    follow_up_playlist_tracks = asyncio.run(
        fetch_additional_tracks_controller(follow_up_job_params)
    )

    # sort by offset
    follow_up_playlist_tracks.sort(key=lambda entry: entry[2])

    for entry in follow_up_playlist_tracks:
        user_spotify_playlists[entry[0]].extend(
            [item["track"]["id"] for item in entry[3]["items"]]
        )

    return user_spotify_playlists


def get_all_user_playlists_set() -> set:
    # get user playlists to check against deleted playlists
    user_id = db_utils.get_spotify_user_id()
    access_token = get_spotify_access_token(
        [
            "user-library-read",
            "playlist-read-private",
            "playlist-read-collaborative",
        ]
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    params = {"fields": "total,items(id,name),limit"}
    response = requests.get(url, headers=headers, params=params, timeout=10)
    if not response.ok:
        logger.debug(response)
        raise ConnectionError("fetching playlist failed")

    result = response.json()
    total = result["total"]
    limit = result["limit"]
    all_user_playlists = {item["id"] for item in result["items"]}
    follow_up_job_params = [
        [user_id, limit, offset] for offset in range(limit, total, limit)
    ]
    follow_up_playlist_ids = asyncio.run(
        fetch_additional_playlists_controller(follow_up_job_params)
    )
    all_user_playlists.update(
        [
            item["id"]
            for playlist_batch in follow_up_playlist_ids
            for item in playlist_batch["items"]
        ]
    )
    return all_user_playlists


def overwrite_playlists(params_list: list[list[str, list[str]]]):
    return asyncio.run(overwrite_playlists_controller(params_list))


def get_spotify_song_details(spotify_uris: list[str]) -> dict[str, dict[str, object]]:
    """get song details for songs to add - for the purpose of reporting to the user

    Args:
        spotify_uris (list[str]): list of spotify URIs to look up

    Returns:
        dict[str, dict[str, object]]: map from spotify URI to spotify track json
    """
    logger.debug(f"running get_spotify_song_details with spotify_uris: {spotify_uris}")
    return asyncio.run(fetch_spotify_song_details_controller(spotify_uris))


def get_spotify_search_results(queries: list[str]):
    logger.debug(f"running get_spotify_search_results with queries: {queries}")
    return asyncio.run(fetch_spotify_search_results_controller(queries))


# misc


def get_spotify_access_token(scope: list[str]) -> str:
    auth_manager = SpotifyOAuth(scope=scope)
    return auth_manager.get_access_token(as_dict=False)
