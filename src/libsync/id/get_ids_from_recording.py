"""module to get track IDs from a recording"""

import asyncio
import logging
import os
import pickle
from datetime import timedelta

import ffmpeg
from aiohttp_retry import ExponentialRetry
from shazamio import HTTPClient, Shazam

from libsync.id.download_audio import download_mp3_from_youtube_url
from libsync.id.youtube_dl_utils import (
    get_mp3_output_path,
    get_youtube_video_id_from_url,
)
from libsync.utils import string_utils
from libsync.utils.constants import (
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
    logger.info("get_track_ids_from_audio_file with args " + f"youtube_url: {youtube_url}")

    youtube_video_id = get_youtube_video_id_from_url(youtube_url)
    mp3_output_path = get_mp3_output_path(youtube_video_id)
    logger.info(f"using youtube_video_id: {youtube_video_id}, mp3_output_path: {mp3_output_path}")

    if not os.path.isfile(mp3_output_path):
        logger.info("couldn't find file, downloading from youtube")
        download_mp3_from_youtube_url(youtube_url)
    else:
        logger.info("found file, skipping download")

    # run shazam script
    get_track_ids_from_audio_file(mp3_output_path)


async def recognize_segments(
    audio_path: str, segment_length_ms: int = 15000, overlap_ms: int = 5000
):
    """Recognize songs in overlapping segments of the audio file

    Args:
        audio_path: Path to the audio file
        segment_length_ms: Length of each segment in milliseconds (default 10 seconds)
        overlap_ms: Overlap between segments in milliseconds (default 5 seconds)
    """
    # Get audio duration using ffprobe
    probe = ffmpeg.probe(audio_path)
    audio_stream = next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "audio"), None
    )
    if not audio_stream:
        raise ValueError(f"No audio stream found in {audio_path}")

    total_duration_seconds = float(audio_stream["duration"])
    total_duration_ms = int(total_duration_seconds * 1000)

    # Create temporary directory for segments if it doesn't exist
    temp_dir = os.path.join(os.path.dirname(audio_path), "temp_segments")
    os.makedirs(temp_dir, exist_ok=True)

    # Initialize Shazam
    shazam = Shazam(
        http_client=HTTPClient(
            retry_options=ExponentialRetry(
                attempts=12, max_timeout=204.8, statuses={500, 502, 503, 504, 429}
            ),
        ),
    )

    shazam_matches_by_id = {}

    try:
        # Process audio in overlapping segments
        for start_ms in range(0, total_duration_ms, segment_length_ms - overlap_ms):
            end_ms = min(start_ms + segment_length_ms, total_duration_ms)
            if end_ms - start_ms < 5000:  # Skip segments shorter than 5 seconds
                continue

            # Extract segment using ffmpeg
            start_seconds = start_ms / 1000
            duration_seconds = (end_ms - start_ms) / 1000
            segment_path = os.path.join(temp_dir, f"segment_{start_ms}.mp3")

            # Use ffmpeg to extract and save the segment
            (
                ffmpeg.input(audio_path, ss=start_seconds, t=duration_seconds)
                .output(segment_path, acodec="mp3", audio_bitrate="128k")
                .overwrite_output()
                .run(quiet=True)
            )

            # Recognize segment
            try:
                logger.info(
                    f"Recognizing segment at {timedelta(milliseconds=start_ms)}, segment_path: {segment_path}"
                )

                # TODO - should cache here based on segment_path (also name segment_path based on start_ms and youtube id)
                # don't cache logic, just shazam results
                result = await shazam.recognize(segment_path)

                if result and "matches" in result and "track" in result:
                    track = result["track"]
                    offset = start_ms
                    shazam_id = track["key"]
                    title = track["title"]
                    artist = track["subtitle"]

                    if shazam_id and shazam_id not in shazam_matches_by_id:
                        timestamp = str(timedelta(milliseconds=offset))
                        shazam_matches_by_id[shazam_id] = {
                            "offset": offset,
                            "artist": artist,
                            "title": title,
                            "count": 1,
                        }

                    elif shazam_id:
                        shazam_matches_by_id[shazam_id]["count"] += 1
                        if shazam_matches_by_id[shazam_id]["count"] > NUM_SHAZAM_MATCHES_THRESHOLD:
                            print(f"{timestamp} {artist:40} - {title:80} {shazam_id}")

                # Clean up segment file
                os.remove(segment_path)

            except Exception as e:
                logger.error(f"Error processing segment at {start_ms}ms: {str(e)}")
                continue

    finally:
        # Clean up temporary directory and any remaining files
        try:
            os.rmdir(temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {str(e)}")

    return shazam_matches_by_id


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
    shazam_matches_by_id = {}

    # Load cache if it exists
    try:
        with open(libsync_cache_path, "rb") as handle:
            cache = pickle.load(handle)
            shazam_matches_by_id = cache["shazam_matches_by_id"]
    except (FileNotFoundError, KeyError) as error:
        logger.debug(f"Cache error: {error}")
        string_utils.print_libsync_status_error(
            f"No valid cache found. Creating new cache at '{libsync_cache_path}'."
        )

    if len(shazam_matches_by_id) == 0 or FORCE_REDO_SHAZAM:
        try:
            # Run recognition on segments
            shazam_matches_by_id = asyncio.run(recognize_segments(recording_audio_file_path))

            # Save matches to cache
            with open(libsync_cache_path, "wb") as handle:
                pickle.dump(
                    {"shazam_matches_by_id": shazam_matches_by_id},
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )

        except Exception as e:
            logger.error(f"Error during Shazam recognition: {str(e)}")
            string_utils.print_libsync_status_error(
                "Failed to recognize songs in the recording. Please try again."
            )
            raise e

    shazam_ids_in_order = [
        item[0] for item in sorted(list(shazam_matches_by_id.items()), key=lambda x: x[1]["offset"])
    ]

    # Print results
    for shazam_id in shazam_ids_in_order:
        match = shazam_matches_by_id[shazam_id]
        match_count = match["count"]
        offset = match["offset"]
        timestamp = str(timedelta(milliseconds=offset))
        artist = match["artist"]
        title = match["title"]
        if match_count >= NUM_SHAZAM_MATCHES_THRESHOLD:
            url_component = f"{shazam_id:30}" if SHOW_URL_IN_SHAZAM_OUTPUT else ""
            print(f"{match_count:3} {timestamp} {artist:30} - {title:30}{url_component}")


# TODO: add youtube title to db and output
