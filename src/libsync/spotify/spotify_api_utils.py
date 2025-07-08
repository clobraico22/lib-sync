import asyncio
import logging
import random
from collections.abc import Iterable
from typing import Any

import aiohttp
import requests
from tqdm import tqdm

from libsync.spotify.spotify_auth import SpotifyAuthManager
from libsync.utils import constants, string_utils
from libsync.utils.rekordbox_library import SpotifyPlaylistId, SpotifyURI

logger = logging.getLogger("libsync")


# New utility function for handling retries
async def get_from_spotify_with_retry(session, url, headers, params, description) -> Any:
    for attempt in range(constants.MAX_RETRIES):
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if isinstance(response, aiohttp.ClientResponse):
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", "5")) + 2 ** (
                            attempt + random.random()
                        )
                        logger.warning(
                            f"Rate limited. Retrying after {retry_after} seconds. Attempt {attempt + 1}/{constants.MAX_RETRIES}"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    if not response.ok:
                        logger.debug(
                            f"Response not OK: {response.status} - {await response.text()}"
                        )
                        response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, requests.RequestException) as e:
            logger.error(f"Error in API call: {e}. Attempt {attempt + 1}/{constants.MAX_RETRIES}")
            if attempt == constants.MAX_RETRIES - 1:
                raise ConnectionError(
                    f"{description} failed after {constants.MAX_RETRIES} attempts"
                ) from e
            await asyncio.sleep(2**attempt)  # Exponential backoff

    raise ConnectionError(f"{description} failed after {constants.MAX_RETRIES} attempts")


# New utility function for handling PUT/POST requests with retry
async def modify_spotify_with_retry(session, url, headers, json, method, description) -> Any:
    for attempt in range(constants.MAX_RETRIES):
        try:
            if method.upper() == "PUT":
                request_func = session.put
            elif method.upper() == "POST":
                request_func = session.post
            else:
                raise ValueError(f"Unsupported method: {method}")

            async with request_func(url, headers=headers, json=json) as response:
                if isinstance(response, aiohttp.ClientResponse):
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", "5")) + 2 ** (
                            attempt + random.random()
                        )
                        logger.warning(
                            f"Rate limited. Retrying after {retry_after} seconds. Attempt {attempt + 1}/{constants.MAX_RETRIES}"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    if not response.ok:
                        logger.debug(
                            f"Response not OK: {response.status} - {await response.text()}"
                        )
                        response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, requests.RequestException) as e:
            logger.error(f"Error in API call: {e}. Attempt {attempt + 1}/{constants.MAX_RETRIES}")
            if attempt == constants.MAX_RETRIES - 1:
                raise ConnectionError(
                    f"{description} failed after {constants.MAX_RETRIES} attempts"
                ) from e
            await asyncio.sleep(2**attempt)  # Exponential backoff

    raise ConnectionError(f"{description} failed after {constants.MAX_RETRIES} attempts")


# workers


async def fetch_playlist_details_worker(session, access_token, playlist_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    params = {"fields": "name,uri,tracks.total,tracks.items(track.id,track.name),tracks.limit"}

    playlist_data = await get_from_spotify_with_retry(
        session, url, headers, params, "fetching playlist details"
    )
    return playlist_id, playlist_data


async def fetch_additional_tracks_worker(
    session: aiohttp.ClientSession, access_token, playlist_id, limit, offset
):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit={limit}&offset={offset}"
    params = {"fields": "total,items(track.id,track.name),limit"}

    playlist_data = await get_from_spotify_with_retry(
        session, url, headers, params, "fetching additional playlist tracks"
    )
    return playlist_id, limit, offset, playlist_data


async def fetch_additional_playlists_worker(session, access_token, user_id, limit, offset):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists?limit={limit}&offset={offset}"
    params = {"fields": "items(id,name)"}

    playlist_data = await get_from_spotify_with_retry(
        session, url, headers, params, "fetching additional playlists"
    )
    return playlist_data


async def overwrite_playlists_worker(session, access_token, playlist_id, track_uri_list):
    logger.debug(f"clearing playlist: {playlist_id}, then adding {len(track_uri_list)} tracks.")
    pages = [
        track_uri_list[i : i + constants.SPOTIFY_API_ITEMS_PER_PAGE]
        for i in range(0, len(track_uri_list), constants.SPOTIFY_API_ITEMS_PER_PAGE)
    ]
    if len(pages) < 1:
        return []

    responses = []
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    # first page - clear the playlist
    json = {"uris": []}
    try:
        response_data = await modify_spotify_with_retry(
            session, url, headers, json, "PUT", f"clearing playlist {playlist_id}"
        )
        responses.append(response_data)

        # Add delay between clearing and adding tracks to avoid rate limits
        await asyncio.sleep(1)

        # following pages - add tracks with delay between batches
        for i, page in enumerate(pages):
            json = {"uris": page}
            response_data = await modify_spotify_with_retry(
                session,
                url,
                headers,
                json,
                "POST",
                f"adding tracks to playlist {playlist_id}",
            )
            responses.append(response_data)

            # Add delay between batches to reduce rate limiting
            if i < len(pages) - 1:
                await asyncio.sleep(0.5)

        return responses
    except ConnectionError as e:
        logger.error(f"Failed to update playlist {playlist_id}: {e}")
        # Return partial responses if we have any
        if responses:
            return responses
        return []


async def fetch_spotify_song_details_worker(
    session, access_token, list_of_sp_uris
) -> list[str, str, str]:
    headers = {"Authorization": f"Bearer {access_token}"}
    list_of_sp_ids = [string_utils.get_spotify_id_from_uri(sp_uri) for sp_uri in list_of_sp_uris]
    url = f"https://api.spotify.com/v1/tracks?ids={'%2C'.join(list_of_sp_ids)}"

    data = await get_from_spotify_with_retry(session, url, headers, None, "fetching song details")
    return [[track["uri"], track] for track in data["tracks"]]


async def fetch_spotify_search_results_worker(session, access_token, query):
    if not query:
        return query, None

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/search?q={query}&type=track"

    try:
        data = await get_from_spotify_with_retry(
            session, url, headers, None, "fetching search results"
        )
        return query, data["tracks"]["items"]

    except ConnectionError as e:
        logger.error(f"ConnectionError in fetch_spotify_search_results_worker: {e}")
        return query, None

    except KeyError as e:
        logger.error(f"KeyError in fetch_spotify_search_results_worker: {e}")
        return query, None


# controllers


async def fetch_playlist_details_controller(playlist_ids: Iterable[str]):
    access_token = SpotifyAuthManager.get_access_token()
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

        return {playlist_id: playlist_info for playlist_id, playlist_info in playlist_info_list}

    return {}


async def fetch_additional_tracks_controller(params_list: list[list[str, int, int]]):
    access_token = SpotifyAuthManager.get_access_token()
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_additional_tracks_worker(session, access_token, playlist_id, limit, offset)
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


async def get_all_user_playlists_set_controller():
    user_id = SpotifyAuthManager.get_user_id()

    access_token = SpotifyAuthManager.get_access_token()
    data = {}
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        params = {"fields": "total,items(id,name),limit"}
        data = await get_from_spotify_with_retry(
            session, url, headers, params, "fetching all user playlists"
        )

    total = data["total"]
    limit = data["limit"]
    all_user_playlists = {item["id"] for item in data["items"]}
    follow_up_job_params = [[user_id, limit, offset] for offset in range(limit, total, limit)]
    follow_up_playlist_ids = await fetch_additional_playlists_controller(follow_up_job_params)
    all_user_playlists.update(
        [
            item["id"]
            for playlist_batch in follow_up_playlist_ids
            for item in playlist_batch["items"]
        ]
    )
    return all_user_playlists


async def fetch_additional_playlists_controller(params_list: list[list[str, int, int]]):
    access_token = SpotifyAuthManager.get_access_token()
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_additional_playlists_worker(session, access_token, user_id, limit, offset)
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


async def overwrite_playlists_controller(
    params_list: list[tuple[SpotifyPlaylistId, list[SpotifyURI]]],
):
    access_token = SpotifyAuthManager.get_access_token()
    async with aiohttp.ClientSession() as session:
        tasks = [
            overwrite_playlists_worker(session, access_token, playlist_id, track_uri_list)
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
        for i in range(0, len(spotify_uris), constants.SPOTIFY_API_GET_TRACKS_ITEMS_PER_PAGE)
    ]
    if len(batches) < 1:
        return {}

    access_token = SpotifyAuthManager.get_access_token()
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_spotify_song_details_worker(session, access_token, batch) for batch in batches
        ]

        track_details_list = []
        for future in tqdm(
            asyncio.as_completed(tasks), total=len(tasks), desc="Fetching song details"
        ):
            track_details_list.append(await future)

        return {track_uri: track for batch in track_details_list for track_uri, track in batch}


async def fetch_spotify_search_results_controller(queries):
    access_token = SpotifyAuthManager.get_access_token()
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_spotify_search_results_worker(session, access_token, query) for query in queries
        ]
        # TODO: we're getting rate limited here when we try to hit this too quickly.
        # might be some persistent issues here
        # need to debug.
        # use case: trying to update 40+ playlists at once, we're successfully deleting them, but not recreating.
        # major bug.
        search_results_list = []
        for future in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Fetching search results",
        ):
            search_results_list.append(await future)

        return {query: results for query, results in search_results_list if results is not None}

    return {}


# driver


def get_user_playlists_details(playlists: Iterable[str]) -> dict[str, list[str]]:
    """get user playlists to check against deleted playlists

    Args:
        playlists (Iterable[str]): list of spotify playlist ids

    Returns:
        dict[str, list]: map from spotify playlist id to list of spotify track ids
    """

    initial_playlist_info = asyncio.run(fetch_playlist_details_controller(playlists))
    user_spotify_playlists = {}
    follow_up_job_params = []

    for playlist_id, playlist_info in initial_playlist_info.items():
        tracks = playlist_info["tracks"]
        user_spotify_playlists[playlist_id] = [item["track"]["id"] for item in tracks["items"]]
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
        user_spotify_playlists[entry[0]].extend([item["track"]["id"] for item in entry[3]["items"]])

    return user_spotify_playlists


def get_all_user_playlists_set() -> set[str]:
    """get all user playlists to check against deleted playlists

    Returns:
        set[str]: set of spotify playlist ids
    """
    return asyncio.run(get_all_user_playlists_set_controller())


def overwrite_playlists(params_list: list[tuple[SpotifyPlaylistId, list[SpotifyURI]]]):
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
