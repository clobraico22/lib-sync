import logging

from rekordbox_library import RekordboxPlaylist


def create_spotify_playlists(
    rekordbox_playlists: list[RekordboxPlaylist],
    rekordbox_to_spotify_map: dict[str, str],
    spotify_username: str,
):
    """creates playlists in the user's account with the matched songs

    Args:
        rekordbox_playlists (list[RekordboxPlaylist]): user's playlists from rekordbox (list of rekordbox track IDs)
        rekordbox_to_spotify_map (dict[str, str]): mapping from rekordbox track IDs to spotify URIs
        spotify_username (str): TODO: replace with the rest of auth
    """

    logging.info(
        "running create_spotify_playlists with "
        + f"rekordbox_playlists: {rekordbox_playlists}, "
        + f"rekordbox_to_spotify_map: {rekordbox_to_spotify_map}, "
        + f"spotify_username: {spotify_username}"
    )

    return
