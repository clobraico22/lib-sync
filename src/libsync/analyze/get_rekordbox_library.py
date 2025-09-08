"""contains get_rekordbox_library function and helpers"""

import logging
import os
import shutil
import time
import xml.etree.ElementTree as ET

from libsync.utils import filepath_utils, string_utils
from libsync.utils.rekordbox_library import (
    RekordboxLibrary,
    RekordboxNodeType,
    RekordboxPlaylist,
    RekordboxTrack,
)

logger = logging.getLogger("libsync")


# TODO: investigate if we can read/modify the rekordbox library directly
# see https://github.com/erikrichardlarson/unbox
# see rekordbox section here:
# https://github.com/erikrichardlarson/unbox/blob/main/src/poller.js#L134
# https://www.reddit.com/r/Rekordbox/comments/qou6nm/comment/hjpi2u3/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
# ~/Library/Application Support/Pioneer/rekordboxAgent/storage/options.json


def get_rekordbox_library(
    rekordbox_xml_path: str,
    skip_collection_playlist: bool,
) -> RekordboxLibrary:
    """get user's rekordbox library from filepath and convert it into internal data structures

    Args:
        rekordbox_xml_path (str): path to user's library export
        skip_collection_playlist (bool): should we skip creating an additional playlist with
          everything in the collection

    Returns:
        RekordboxLibrary: data structure containing a representation of the library
    """

    logger.debug(f"running get_rekordbox_library with rekordbox_xml_path: {rekordbox_xml_path}")
    string_utils.print_libsync_status("Reading Rekordbox library", level=1)

    tree = get_tree_from_xml(rekordbox_xml_path)
    root = tree.getroot()
    rekordbox_collection_list = [
        RekordboxTrack(
            id=track.get("TrackID"),
            name=track.get("Name"),
            artist=track.get("Artist"),
            album=track.get("Album"),
        )
        for track in root.findall("./COLLECTION/TRACK")
        if should_keep_track_in_collection(track)
    ]
    rekordbox_collection_id_set = {track.id for track in rekordbox_collection_list}

    # flatten playlist structure into one folder
    rekordbox_playlists: list[RekordboxPlaylist] = []
    rekordbox_playlist_names_set = set()
    nodes: list = root.findall("./PLAYLISTS/NODE")
    while len(nodes) >= 1:
        node = nodes[0]
        node_type = (
            RekordboxNodeType.FOLDER if node.get("Type") == "0" else RekordboxNodeType.PLAYLIST
        )

        logger.debug(f"running loop with nodes: {nodes}, " + f"nodes[0]: {nodes[0]}, ")
        if node_type == RekordboxNodeType.PLAYLIST:
            playlist_name = node.get("Name")
            logger.debug(f"found playlist {playlist_name}")

            if playlist_name in rekordbox_playlist_names_set:
                string_utils.print_libsync_status_error(
                    f'Found duplicate playlist name "{playlist_name}". '
                    + "Libsync doesn't support this. "
                    + "Please rename this duplicate playlist in rekordbox and export again."
                )
                exit(1)

            rekordbox_playlist_names_set.add(playlist_name)
            rekordbox_playlists.append(
                RekordboxPlaylist(
                    name=playlist_name,
                    tracks=[
                        track.get("Key")
                        for track in node.findall("TRACK")
                        if track.get("Key") in rekordbox_collection_id_set
                    ],
                )
            )

        elif node_type == RekordboxNodeType.FOLDER:
            logger.debug("found folder")
            nodes.extend(node.findall("NODE"))

        else:
            logger.debug("found unknown node type, breaking loop")
            break

        nodes.pop(0)

    if not skip_collection_playlist:
        logger.debug("adding Collection playlist")
        rekordbox_playlists.append(
            RekordboxPlaylist(
                name="Collection",
                tracks=[track.id for track in rekordbox_collection_list],
            )
        )

    logger.debug("done with get_rekordbox_library")
    string_utils.print_libsync_status_success("Done", level=1)

    return RekordboxLibrary(
        xml_path=rekordbox_xml_path,
        collection={track.id: track for track in rekordbox_collection_list},
        playlists=rekordbox_playlists,
    )


def get_tree_from_xml(xml_path: str):
    # Validate file before attempting to parse
    if not os.path.exists(xml_path):
        string_utils.print_libsync_status_error(
            f"couldn't find '{xml_path}'. check the path and try again"
        )
        exit(1)

    if not os.path.isfile(xml_path):
        string_utils.print_libsync_status_error(f"'{xml_path}' is not a file")
        exit(1)

    if not os.access(xml_path, os.R_OK):
        string_utils.print_libsync_status_error(
            f"'{xml_path}' is not readable. check file permissions"
        )
        exit(1)

    # Check file size (reject files larger than 1GB or empty files)
    file_size = os.path.getsize(xml_path)
    if file_size == 0:
        string_utils.print_libsync_status_error(f"'{xml_path}' is empty")
        exit(1)

    if file_size > 100_000_000:  # 100MB
        string_utils.print_libsync_status_error(
            f"'{xml_path}' is too large ({file_size / 1_000_000:.1f}MB). "
            + "rekordbox XML files should not exceed 100MB"
        )
        exit(1)

    # Check file modification time
    file_mtime = os.path.getmtime(xml_path)
    current_time = time.time()
    age_seconds = current_time - file_mtime
    age_hours = age_seconds / 3600

    if age_hours > 1:
        logger.warning(f"'{xml_path}' was last modified {age_hours:.1f} hours ago")
        string_utils.print_libsync_status(
            f"⚠️  Warning: XML file is {age_hours:.1f} hours old. "
            + "Consider exporting a fresh copy from Rekordbox for the most up-to-date library.",
            level=1,
        )

    # Backup the XML file before parsing
    backup_path = filepath_utils.get_rekordbox_xml_backup_path(xml_path, file_mtime)

    # Only backup if this exact file hasn't been backed up already
    if not backup_path.exists():
        try:
            shutil.copy2(xml_path, backup_path)
            logger.info(f"Backed up XML file to: {backup_path}")
        except Exception as error:
            logger.warning(f"Failed to backup XML file: {str(error)}")
            # Don't exit on backup failure, just warn

    # Quick check for XML header
    try:
        with open(xml_path, "rb") as f:
            header = f.read(100)
            if not header.strip().startswith(b"<?xml") and not header.strip().startswith(b"<"):
                string_utils.print_libsync_status_error(
                    f"'{xml_path}' does not appear to be an XML file"
                )
                exit(1)
    except Exception as error:
        logger.exception(error)
        string_utils.print_libsync_status_error(f"error reading '{xml_path}': {str(error)}")
        exit(1)

    try:
        return ET.parse(xml_path)
    except FileNotFoundError as error:
        logger.debug(error)
        string_utils.print_libsync_status_error(
            f"couldn't find '{xml_path}'. check the path and try again"
        )
        exit(1)
    except TypeError as error:
        logger.exception(error)
        string_utils.print_libsync_status_error(
            f"the file at '{xml_path}' is the wrong format. try exporting again"
        )
        exit(1)
    except ET.ParseError as error:
        logger.exception(error)
        string_utils.print_libsync_status_error(
            f"error parsing XML file '{xml_path}': {str(error)}"
        )
        exit(1)


def should_keep_track_in_collection(track):
    if track.get("Kind") == "Unknown Format":
        return False

    return True
