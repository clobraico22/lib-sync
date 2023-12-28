"""contains utility functions related to the youtube download module"""

import logging
from urllib.parse import parse_qs, urlparse

OUTPUT_TEMPLATE = "data/%(id)s_audio_download"


class YoutubeDLLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        logging.info(f"YoutubeDL error: {msg}")


def youtube_dl_progress_hook(d):
    if d["status"] == "finished":
        logging.info("Done downloading, now converting to mp3.")


def get_mp3_output_path(youtube_video_id):
    output_path = OUTPUT_TEMPLATE % {"id": youtube_video_id}
    return f"{output_path}.mp3"


def get_youtube_video_id_from_url(value):
    """
    copied from online somewhere
    """

    query = urlparse(value)
    if query.hostname == "youtu.be":
        return query.path[1:]
    if query.hostname in ("www.youtube.com", "youtube.com"):
        if query.path == "/watch":
            p = parse_qs(query.query)
            return p["v"][0]
        if query.path[:7] == "/embed/":
            return query.path.split("/")[2]
        if query.path[:3] == "/v/":
            return query.path.split("/")[2]

    raise ValueError("invalid youtube link.")


YDL_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": OUTPUT_TEMPLATE,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "logger": YoutubeDLLogger(),
    "progress_hooks": [youtube_dl_progress_hook],
}
