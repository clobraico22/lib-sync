"""
the rekordbox_library module contains the RekordboxLibrary class and other related classes
"""

import pprint
from enum import Enum


class LibsyncCommand(str, Enum):
    """enum with the names of commands"""

    SYNC = "sync"
    ANALYZE = "analyze"
    ID = "id"
    FILE = "file"
    YOUTUBE = "youtube"


class RekordboxTrack:
    """Relevant track info from rekordbox xml file"""

    def __init__(self, id, name, artist, album=None) -> None:
        self.id = id
        self.name = name
        self.artist = artist
        self.album = album

    def __repr__(self) -> str:
        return f"[{self.id}] {self.name} - {self.artist} - " + (
            self.album if self.album else "<no album>"
        )

    def __str__(self) -> str:
        return self.__repr__()


# dict of all tracks in a collection, indexed by track ID from rekordbox
RekordboxCollection = dict[str, RekordboxTrack]


# ordered list of track IDs
class RekordboxPlaylist:
    def __init__(self, name: str, tracks: list[str]) -> None:
        self.name = name
        self.tracks = tracks

    def __repr__(self) -> str:
        return f"Playlist object with name: {self.name}\n{pprint.pformat(self.tracks)}"

    def __str__(self) -> str:
        return self.__repr__()


class RekordboxLibrary:
    def __init__(
        self,
        collection: RekordboxCollection,
        playlists: list[RekordboxPlaylist],
    ) -> None:
        self.collection = collection
        self.playlists = playlists

    def __repr__(self) -> str:
        return (
            "RekordboxLibrary object\n  "
            + f"collection:\n{pprint.pformat(self.collection)}\n  "
            + f"playlists:\n{pprint.pformat(self.playlists)}"
        )

    def __str__(self) -> str:
        return self.__repr__()


class RekordboxNodeType(Enum):
    FOLDER = 0
    PLAYLIST = 1
