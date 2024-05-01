"""generates report based on user's rekordbox library"""

from utils import string_utils
from utils.rekordbox_library import RekordboxLibrary


def generate_rekordbox_library_report(rekordbox_library: RekordboxLibrary) -> None:
    """print some useful lists/stats based on flags from user

    Args:
        rekordbox_library (RekordboxLibrary): user's library to analyze
    """
    string_utils.print_libsync_status("Analyzing Rekordbox library", level=1)

    track_to_playlists_map = {track_id: [] for track_id in rekordbox_library.collection}
    for playlist in rekordbox_library.playlists:
        for track_id in playlist.tracks:
            track_to_playlists_map[track_id].append(playlist.name)

    tracks_not_on_any_playlists = [
        track_id
        for track_id, playlists in track_to_playlists_map.items()
        if len(playlists) == 0
    ]
    print("tracks not on any playlists:")
    for track_id in tracks_not_on_any_playlists:
        print(f"{rekordbox_library.collection[track_id]}")

    string_utils.print_libsync_status_success("Done", level=1)
