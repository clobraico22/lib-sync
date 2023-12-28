"""contains utility functions related to the youtube download module"""

import logging
import re

OUTPUT_TEMPLATE = "data/%(id)s_audio_download"
YOUTUBE_URL_PARSE_PATTERN = (
    r"(?:https?:\/{2})?(?:w{3}\.)?youtu(?:be)?\.(?:com|be)(?:\/watch\?v=|\/)([^\s&]+)"
)


class YoutubeDLLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        logging.info(f'YoutubeDL error: {msg}')


def youtube_dl_progress_hook(d):
    if d["status"] == "finished":
        logging.info("Done downloading, now converting to mp3.")


def get_mp3_output_path(youtube_video_id):
    output_path = OUTPUT_TEMPLATE % {"id": youtube_video_id}
    return f"{output_path}.mp3"


def get_youtube_video_id_from_url(youtube_url):
    matches = re.findall(YOUTUBE_URL_PARSE_PATTERN, youtube_url)
    if len(matches) < 1:
        raise ValueError("invalid youtube link.")

    return matches[0]

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
