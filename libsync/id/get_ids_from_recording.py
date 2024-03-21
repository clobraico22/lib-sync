"""module to get track IDs from a recording"""

import logging
import os
import pickle
from datetime import timedelta

from id.download_audio import download_mp3_from_youtube_url
from id.youtube_dl_utils import get_mp3_output_path, get_youtube_video_id_from_url
from ShazamAPI import Shazam
from utils.constants import (
    FORCE_REDO_SHAZAM,
    NUM_SHAZAM_MATCHES_THRESHOLD,
    SHOW_URL_IN_SHAZAM_OUTPUT,
)

logger = logging.getLogger("libsync")


def get_track_ids_from_youtube_link(youtube_url: str) -> None:
    """analyze audio file to find track IDs

    Args:
        youtube_url (str): URL of youtube video to analyze
    """
    logger.info(
        "get_track_ids_from_audio_file with args " + f"youtube_url: {youtube_url}"
    )

    youtube_video_id = get_youtube_video_id_from_url(youtube_url)
    mp3_output_path = get_mp3_output_path(youtube_video_id)
    logger.info(
        f"using youtube_video_id: {youtube_video_id}, mp3_output_path: {mp3_output_path}"
    )

    if not os.path.isfile(mp3_output_path):
        logger.info("couldn't find file, downloading from youtube")
        download_mp3_from_youtube_url(youtube_url)
    else:
        logger.info("found file, skipping download")

    # run shazam script
    get_track_ids_from_audio_file(mp3_output_path)


def get_track_ids_from_audio_file(recording_audio_file_path: str) -> None:
    """analyze audio file using shazam to find track IDs

    Args:
        recording_audio_file_path (str): path to audio file to analyze
    """

    libsync_cache_path = f"{recording_audio_file_path}_libsync_shazam_cache.db"
    logger.info(
        "get_track_ids_from_audio_file with args "
        + f"recording_audio_file_path: {recording_audio_file_path}, "
        + f"libsync_cache_path: {libsync_cache_path}"
    )
    shazam_matches_by_url = {}
    shazam_urls_in_order = []

    # get libsync cache from file
    try:
        with open(libsync_cache_path, "rb") as handle:
            cache = pickle.load(handle)
            (
                shazam_matches_by_url,
                shazam_urls_in_order,
            ) = (
                cache["shazam_matches_by_url"],
                cache["shazam_urls_in_order"],
            )

    except FileNotFoundError as error:
        logger.debug(error)
        print(f"no cache found. creating cache at '{libsync_cache_path}'.")
    except KeyError as error:
        logger.exception(error)
        print(f"error parsing cache at '{libsync_cache_path}'. clearing cache.")
        # TODO actually clear cache, also centralize this duplicated caching logic

    input_file = open(recording_audio_file_path, "rb").read()
    shazam = Shazam(input_file)
    recognize_generator = shazam.recognizeSong()
    if len(shazam_urls_in_order) == 0 or FORCE_REDO_SHAZAM:
        while True:
            try:
                result = next(recognize_generator)
                timestamp = timedelta(seconds=result[0])
                details = result[1]
                if len(details["matches"]) >= 1:
                    track = details["track"]
                    subtitle = track["subtitle"]
                    title = track["title"]
                    url = track["url"]
                    if url not in shazam_matches_by_url:
                        shazam_urls_in_order.append(url)
                        print(f"{str(timestamp)} {subtitle:40} - {title:80} {url}")
                        shazam_matches_by_url[url] = {
                            "timestamps": [timestamp],
                            "subtitle": subtitle,
                            "title": title,
                        }
                    else:
                        shazam_matches_by_url[url]["timestamps"].append(timestamp)

            except StopIteration as _:
                logger.info("reached end of file.")
                break

    # save matches
    with open(libsync_cache_path, "wb") as handle:
        pickle.dump(
            {
                "shazam_matches_by_url": shazam_matches_by_url,
                "shazam_urls_in_order": shazam_urls_in_order,
            },
            handle,
            protocol=pickle.HIGHEST_PROTOCOL,
        )

    # PRINT RESULTS
    for url in shazam_urls_in_order:
        match = shazam_matches_by_url[url]
        num_matches = len(match["timestamps"])
        timestamp = match["timestamps"][0]
        subtitle = match["subtitle"]
        title = match["title"]
        if num_matches >= NUM_SHAZAM_MATCHES_THRESHOLD:
            url_component = f"{url:30}" if SHOW_URL_IN_SHAZAM_OUTPUT else ""
            print(
                f"{num_matches:3} {str(timestamp)} {subtitle:30} - {title:30}{url_component}"
            )
