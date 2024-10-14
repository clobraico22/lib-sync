"""analyze a user's rekordbox library"""

import logging

from libsync.analyze.generate_rekordbox_library_report import (
    generate_rekordbox_library_report,
)
from libsync.analyze.get_rekordbox_library import get_rekordbox_library

logger = logging.getLogger("libsync")


def analyze_rekordbox_library(
    rekordbox_xml_path: str,
    include_loose_songs: bool,
):
    """analyze a user's rekordbox library

    Args:
        rekordbox_xml_path (str): _description_
        include_loose_songs (bool): _description_
    """

    logger.info(
        "running analyze_rekordbox_library.py with args: "
        + f"rekordbox_xml_path={rekordbox_xml_path}, "
        + f"include_loose_songs={include_loose_songs}"
    )

    rekordbox_library = get_rekordbox_library(rekordbox_xml_path, False)
    generate_rekordbox_library_report(rekordbox_library)
