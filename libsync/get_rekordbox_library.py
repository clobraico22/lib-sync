"""
contains get_rekordbox_library function and helpers
"""

import logging
import xml.etree.ElementTree as ET

from rekordbox_library import (
    RekordboxLibrary,
    RekordboxNodeType,
    RekordboxPlaylist,
    RekordboxTrack,
)


def get_rekordbox_library(rekordbox_xml_path: str, include_loose_songs: bool) -> RekordboxLibrary:
    """_summary_

    Args:
        rekordbox_xml_path (str): _description_

    Returns:
        RekordboxLibrary: _description_
    """

    logging.info(f"running get_rekordbox_library with rekordbox_xml_path: {rekordbox_xml_path}")

    tree = ET.parse(rekordbox_xml_path)
    root = tree.getroot()
    # xml = RekordboxXml(rekordbox_xml_path)
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
            RekordboxNodeType.FOLDER if node.get("Type") == "0" else RekordboxNodeType.PLAYLIST
        )

        logging.debug(f"running loop with nodes: {nodes}, " + f"nodes[0]: {nodes[0]}, ")
        if node_type == RekordboxNodeType.PLAYLIST:
            logging.debug("found playlist")
            rekordbox_playlists.append(
                RekordboxPlaylist(
                    name=node.get("Name"),
                    tracks=[track.get("Key") for track in node.findall("TRACK")],
                )
            )
            for track in rekordbox_playlists[-1].tracks:
                tracks_found_on_at_least_one_playlist.add(track)

        elif node_type == RekordboxNodeType.FOLDER:
            logging.debug("found folder")
            nodes.extend(node.findall("NODE"))

        else:
            logging.debug("breaking")
            break

        nodes.pop(0)

    if not include_loose_songs:
        rekordbox_collection_list = list(
            filter(
                lambda track: track.id in tracks_found_on_at_least_one_playlist,
                rekordbox_collection_list,
            )
        )

    logging.info("done getting rekordbox library")
    return RekordboxLibrary(
        collection={track.id: track for track in rekordbox_collection_list},
        playlists=rekordbox_playlists,
    )
