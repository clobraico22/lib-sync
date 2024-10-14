"""contains functions to download audio from various sources"""

import logging

import yt_dlp

from libsync.id.youtube_dl_utils import YDL_OPTIONS

logger = logging.getLogger("libsync")


def download_mp3_from_youtube_url(youtube_url: str) -> int:
    """downloads mp3 from youtube url using yt_dlp

    Args:
        youtube_url (str): url of source video

    Returns:
        int: return code from YoutubeDL call. 0 is good, anything else is bad.
    """

    logger.info(f"downloading mp3 from youtube url: {youtube_url}")

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        return ydl.download([youtube_url])
