"""CLI entry point"""
import logging

from generate_rekordbox_library_report import generate_rekordbox_library_report
from get_rekordbox_library import get_rekordbox_library


def analyze_rekordbox_library(
    rekordbox_xml_path: str,
    include_loose_songs: bool,
):
    """analyze a user's rekordbox library

    Args:
        rekordbox_xml_path (str): _description_
        include_loose_songs (bool): _description_
    """

    logging.info(
        "running analyze_rekordbox_library.py with args: "
        + f"rekordbox_xml_path={rekordbox_xml_path}, "
        + f"include_loose_songs={include_loose_songs}"
    )

    # get rekordbox db from xml
    try:
        rekordbox_library = get_rekordbox_library(rekordbox_xml_path, include_loose_songs)
        logging.debug(f"got rekordbox library: {rekordbox_library}")
    except FileNotFoundError as error:
        logging.exception(error)
        print(f"couldn't find '{rekordbox_xml_path}'. check the path and try again")
        return
    except TypeError as error:
        logging.exception(error)
        print(f"the file at '{rekordbox_xml_path}' is the wrong format. try exporting again")
        return

    generate_rekordbox_library_report(rekordbox_library)
