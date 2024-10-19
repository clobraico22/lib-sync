"""utils for file read and write operations"""

from datetime import datetime

from libsync.utils.rekordbox_library import RekordboxTrack


def export_failed_matches_to_file(failed_matches: list[RekordboxTrack]):
    """export a list of rekordbox track that were unable to be found in spotify to a txt file

    Args:
        failed_matches (list[RekordboxTrack]): list of failed rekordbox tracks
    """

    with open(
        f"data/failed_matches_{datetime.now()}.txt".replace(" ", "_"),
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "The below files were not found on Spotify. "
            + "Consider updating the metadata before re-running lib-sync.\n"
        )
        for line in failed_matches:
            file.write(f"\t{line}\n")
