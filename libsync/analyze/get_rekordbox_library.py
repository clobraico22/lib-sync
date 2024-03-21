"""contains get_rekordbox_library function and helpers"""

import logging
import xml.etree.ElementTree as ET

from utils.rekordbox_library import (
    RekordboxLibrary,
    RekordboxNodeType,
    RekordboxPlaylist,
    RekordboxTrack,
)

logger = logging.getLogger("libsync")


def get_rekordbox_library(
    rekordbox_xml_path: str, include_loose_songs: bool
) -> RekordboxLibrary:
    """get user's rekordbox library from filepath and convert it into internal data structures

    Args:
        rekordbox_xml_path (str): path to user's library export

    Returns:
        RekordboxLibrary: data structure containing a representation of the library
    """

    logger.debug(
        f"running get_rekordbox_library with rekordbox_xml_path: {rekordbox_xml_path}"
    )
    print("  reading rekordbox library...")

    try:
        tree = ET.parse(rekordbox_xml_path)
    except FileNotFoundError as error:
        logger.debug(error)
        print(f"couldn't find '{rekordbox_xml_path}'. check the path and try again")
        exit(1)
    except TypeError as error:
        logger.exception(error)
        print(
            f"the file at '{rekordbox_xml_path}' is the wrong format. try exporting again"
        )
        exit(1)

    root = tree.getroot()
    rekordbox_collection_list = [
        RekordboxTrack(
            id=track.get("TrackID"),
            name=track.get("Name"),
            artist=track.get("Artist"),
            album=track.get("Album"),
        )
        for track in root.findall("./COLLECTION/TRACK")
    ]
    tracks_found_on_at_least_one_playlist = set()
    # flatten playlist structure into one folder
    rekordbox_playlists: list[RekordboxPlaylist] = []
    nodes: list = root.findall("./PLAYLISTS/NODE")
    while len(nodes) >= 1:
        node = nodes[0]
        node_type = (
            RekordboxNodeType.FOLDER
            if node.get("Type") == "0"
            else RekordboxNodeType.PLAYLIST
        )

        logger.debug(f"running loop with nodes: {nodes}, " + f"nodes[0]: {nodes[0]}, ")
        if node_type == RekordboxNodeType.PLAYLIST:
            logger.debug("found playlist")
            rekordbox_playlists.append(
                RekordboxPlaylist(
                    name=node.get("Name"),
                    tracks=[track.get("Key") for track in node.findall("TRACK")],
                )
            )
            for track in rekordbox_playlists[-1].tracks:
                tracks_found_on_at_least_one_playlist.add(track)

        elif node_type == RekordboxNodeType.FOLDER:
            logger.debug("found folder")
            nodes.extend(node.findall("NODE"))

        else:
            logger.debug("breaking")
            break

        nodes.pop(0)

    if not include_loose_songs:
        rekordbox_collection_list = list(
            filter(
                lambda track: track.id in tracks_found_on_at_least_one_playlist,
                rekordbox_collection_list,
            )
        )

    logger.debug("done with get_rekordbox_library")
    print("  done reading rekordbox library.")

    return RekordboxLibrary(
        collection={track.id: track for track in rekordbox_collection_list},
        playlists=rekordbox_playlists,
    )
