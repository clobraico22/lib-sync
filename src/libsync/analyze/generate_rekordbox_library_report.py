"""generates report based on user's rekordbox library"""

from collections import Counter

from libsync.utils import string_utils
from libsync.utils.rekordbox_library import (
    CAMELOT_TO_MUSICAL_KEY,
    RekordboxCollection,
    RekordboxLibrary,
    RekordboxTrackID,
)
from libsync.utils.string_utils import log_and_print


def _get_key_distribution(
    track_ids: list[RekordboxTrackID], collection: RekordboxCollection
) -> tuple[Counter, int, int, int]:
    """Return (key_counter, tracks_with_key, minor_count, major_count)."""
    key_counter: Counter = Counter()
    tracks_with_key = 0
    minor_count = 0
    major_count = 0
    for tid in track_ids:
        track = collection.get(tid)
        if not track or not track.tonality:
            continue
        tracks_with_key += 1
        key_counter[track.tonality] += 1
        if track.tonality.endswith("A"):
            minor_count += 1
        elif track.tonality.endswith("B"):
            major_count += 1
    return key_counter, tracks_with_key, minor_count, major_count


def _print_key_distribution(
    label: str, track_ids: list[RekordboxTrackID], collection: RekordboxCollection
) -> None:
    """Print a formatted key distribution table."""
    total = len(track_ids)
    key_counter, tracks_with_key, minor_count, major_count = _get_key_distribution(
        track_ids, collection
    )
    tracks_without_key = total - tracks_with_key

    log_and_print(f"\n--- Key Distribution: {label} ---")
    log_and_print(f"Total tracks: {total}")
    log_and_print(f"Tracks with key: {tracks_with_key}")
    if tracks_without_key > 0:
        log_and_print(f"Tracks without key: {tracks_without_key}")

    if tracks_with_key == 0:
        log_and_print("No key data available.")
        return

    minor_pct = minor_count / tracks_with_key * 100
    major_pct = major_count / tracks_with_key * 100
    log_and_print(f"Minor keys: {minor_count} ({minor_pct:.1f}%)")
    log_and_print(f"Major keys: {major_count} ({major_pct:.1f}%)")

    log_and_print("")
    log_and_print(f"{'Camelot':<10}{'Musical Key':<15}{'Count':<8}{'%'}")
    log_and_print("-" * 41)
    for camelot_key, count in key_counter.most_common():
        musical_key = CAMELOT_TO_MUSICAL_KEY.get(camelot_key, "Unknown")
        pct = count / tracks_with_key * 100
        log_and_print(f"{camelot_key:<10}{musical_key:<15}{count:<8}{pct:.1f}%")


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
        track_id for track_id, playlists in track_to_playlists_map.items() if len(playlists) == 0
    ]
    log_and_print("tracks not on any playlists:")
    for track_id in tracks_not_on_any_playlists:
        log_and_print(f"{rekordbox_library.collection[track_id]}")

    # Key distribution analysis
    log_and_print("\n==> Key Distribution Analysis")

    all_track_ids = list(rekordbox_library.collection.keys())
    _print_key_distribution("Full Library", all_track_ids, rekordbox_library.collection)

    string_utils.print_libsync_status_success("Done", level=1)
