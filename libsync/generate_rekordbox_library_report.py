import pprint

from rekordbox_library import RekordboxLibrary


def generate_rekordbox_library_report(rekordbox_library: RekordboxLibrary) -> None:
    """print some useful lists/stats based on flags from user

    Args:
        rekordbox_library (RekordboxLibrary): user's library to analyze
    """
    print("analyze")
    playlists_song_is_on = {}
    for playlist in rekordbox_library.playlists:
        print(playlist)
        for track_id in playlist.tracks:
            if track_id in playlists_song_is_on:
                playlists_song_is_on[track_id].append(playlist.name)
            else:
                playlists_song_is_on[track_id] = [playlist.name]

    print(rekordbox_library.collection)
    # sort based on similarities
    list_of_tracks = [
        [track_id, len(playlists_song_is_on[track_id])]
        for track_id in rekordbox_library.collection.keys()
    ]
    list_of_tracks.sort(key=lambda entry: entry[1], reverse=True)
    for track_id, n in list_of_tracks:
        print(f"{n:3}   {rekordbox_library.collection[track_id]}")

    print("analyzed")
