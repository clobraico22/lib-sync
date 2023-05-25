import logging

from pyrekordbox import RekordboxXml

from rekordbox_library import RekordboxLibrary, RekordboxTrack


def get_rekordbox_library(rekordbox_xml_path: str) -> RekordboxLibrary:
    """_summary_

    Args:
        rekordbox_xml_path (str): _description_

    Returns:
        RekordboxLibrary: _description_
    """

    logging.info(
        f"running get_rekordbox_library with rekordbox_xml_path: {rekordbox_xml_path}"
    )

    xml = RekordboxXml(rekordbox_xml_path)
    rekordboxCollection = [
        RekordboxTrack(
            id=track.TrackID,
            name=track.Name,
            artist=track.Artist,
            album=track.Album,
        )
        for track in xml.get_tracks()
    ]
    # TODO: get the playlists

    return RekordboxLibrary(collection=rekordboxCollection, playlists=[])
