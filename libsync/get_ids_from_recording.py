"""module to get track IDs from a recording"""

import logging
import pickle
import re
from datetime import timedelta

from constants import USE_CACHED_SHAZAM_MATCHES
from ShazamAPI import Shazam

YOUTUBE_URL_PARSE_PATTERN = (
    r"(?:https?:\/{2})?(?:w{3}\.)?youtu(?:be)?\.(?:com|be)(?:\/watch\?v=|\/)([^\s&]+)"
)


def get_track_ids_from_youtube_link(youtube_url: str) -> None:
    """analyze audio file to find track IDs

    Args:
        youtube_url (str): URL of youtube video to analyze
    """
    logging.info(
        "get_track_ids_from_audio_file with args " + f"youtube_url: {youtube_url}"
    )

    matches = re.findall(YOUTUBE_URL_PARSE_PATTERN, youtube_url)
    if len(matches) < 1:
        raise ValueError("invalid youtube link.")
    youtube_video_id = matches[0]

    mp3_output_path = f"{youtube_video_id}.libsync.mp3"
    logging.info(f"using mp3_output_path: {mp3_output_path}")

    # get mp3
    raise Exception("not implemented yet")

    # run shazam script
    get_track_ids_from_audio_file(mp3_output_path)


def get_track_ids_from_audio_file(recording_audio_file_path: str) -> None:
    """analyze audio file to find track IDs

    Args:
        recording_audio_file_path (str): path to audio file to analyze
    """

    libsync_cache_path = f"{recording_audio_file_path}.libsync.id.db"
    logging.info(
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
        logging.exception(error)
        print(f"no cache found. creating cache at '{libsync_cache_path}'.")
    except KeyError as error:
        logging.exception(error)
        print(f"error parsing cache at '{libsync_cache_path}'. clearing cache.")

    input_file = open(recording_audio_file_path, "rb").read()
    shazam = Shazam(input_file)
    recognize_generator = shazam.recognizeSong()
    if len(shazam_urls_in_order) == 0 or not USE_CACHED_SHAZAM_MATCHES:
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
                logging.info("reached end of file.")
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
        print(f"{num_matches:3} {str(timestamp)} {subtitle:40} - {title:80} {url}")
