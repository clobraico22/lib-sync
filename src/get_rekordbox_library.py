from rekordbox_library import RekordboxLibrary, RekordboxTrack


def get_rekordbox_library(rekordbox_xml_path: str) -> RekordboxLibrary:
    """_summary_

    Args:
        rekordbox_xml_path (str): _description_

    Returns:
        RekordboxLibrary: _description_
    """
    return RekordboxLibrary(
        {
            "id1": RekordboxTrack("id1", "Winona", "DJ Boring", "Winona EP"),
            "id2": RekordboxTrack(
                "id2", "Kali", "Charlotte de Witte", "Universal Consciousness EP"
            ),
            "id3": RekordboxTrack("id3", "Funk You (Original Mix)", "Kreech"),
        }
    )
