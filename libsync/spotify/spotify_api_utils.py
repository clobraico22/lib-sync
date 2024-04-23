import asyncio
import logging
from typing import Iterable

import aiohttp
import requests
from db import db_utils
from spotipy.oauth2 import SpotifyOAuth
from utils import constants

logger = logging.getLogger("libsync")


async def fetch_playlist_info_worker(session, access_token, playlist_id):
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
    async with session.get(url, headers=headers, params=params) as response:
        if not response.ok:
            logger.debug(response)
            raise ConnectionError("fetching additional tracks failed")

        return playlist_id, limit, offset, await response.json()


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
        track_uri_list[i : i + constants.ITEMS_PER_PAGE_SPOTIFY_API]
        for i in range(0, len(track_uri_list), constants.ITEMS_PER_PAGE_SPOTIFY_API)
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


async def fetch_playlist_info_controller(playlist_ids):
    access_token = get_spotify_access_token(
        [
            "user-library-read",
            "playlist-read-private",
            "playlist-read-collaborative",
        ]
    )
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_playlist_info_worker(session, access_token, playlist_id)
            for playlist_id in playlist_ids
        ]
        playlist_info_list = await asyncio.gather(*tasks)
        return {
            playlist_id: playlist_info
            for playlist_id, playlist_info in playlist_info_list
        }


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
        return await asyncio.gather(*tasks)


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
        return await asyncio.gather(*tasks)


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
        return await asyncio.gather(*tasks)


def get_user_playlists_details(playlists: Iterable[str]) -> dict[str, list]:
    # get user playlists to check against deleted playlists
    """get specified playlists

    Args:
        playlist_id_map (dict[str, str]): map from rekordbox playlist name to spotify playlist id

    Returns:
        dict[str, list]: map from spotify playlist id to list of spotify track URIs
    """

    initial_playlist_info = asyncio.run(fetch_playlist_info_controller(playlists))
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


def get_spotify_access_token(scope: list[str]) -> str:
    auth_manager = SpotifyOAuth(scope=scope)
    return auth_manager.get_access_token(as_dict=False)


def overwrite_playlists(params_list: list[list[str, list[str]]]):
    return asyncio.run(overwrite_playlists_controller(params_list))
