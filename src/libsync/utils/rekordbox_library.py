"""the rekordbox_library module contains the RekordboxLibrary class and other related classes"""

import pprint
from enum import Enum


class LibsyncCommand(str, Enum):
    """enum with the names of commands"""

    SYNC = "sync"
    ANALYZE = "analyze"
    ID = "id"
    FILE = "file"
    YOUTUBE = "youtube"


RekordboxTrackID = str

CAMELOT_TO_MUSICAL_KEY = {
    "1A": "Ab minor",
    "2A": "Eb minor",
    "3A": "Bb minor",
    "4A": "F minor",
    "5A": "C minor",
    "6A": "G minor",
    "7A": "D minor",
    "8A": "A minor",
    "9A": "E minor",
    "10A": "B minor",
    "11A": "F# minor",
    "12A": "Db minor",
    "1B": "B major",
    "2B": "F# major",
    "3B": "Db major",
    "4B": "Ab major",
    "5B": "Eb major",
    "6B": "Bb major",
    "7B": "F major",
    "8B": "C major",
    "9B": "G major",
    "10B": "D major",
    "11B": "A major",
    "12B": "E major",
}


class RekordboxTrack:
    """Relevant track info from rekordbox xml file"""

    def __init__(
        self,
        id: RekordboxTrackID,
        name: str,
        artist: str,
        album: str | None = None,
        tonality: str | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.artist = artist
        self.album = album
        self.tonality = tonality

    def __repr__(self) -> str:
        return f"[{self.id}] {self.artist} - {self.name} - " + (
            self.album if self.album else "<no album>"
        )

    def __str__(self) -> str:
        return self.__repr__()


# dict of all tracks in a collection, indexed by track ID from rekordbox
RekordboxCollection = dict[str, RekordboxTrack]


# ordered list of track IDs
class RekordboxPlaylist:
    def __init__(self, name: str, tracks: list[RekordboxTrackID]) -> None:
        self.name = name
        self.tracks = tracks

    def __repr__(self) -> str:
        return f"Playlist object with name: {self.name}, tracks: {self.tracks}"

    def __str__(self) -> str:
        return self.__repr__()


class RekordboxLibrary:
    def __init__(
        self,
        xml_path: str,
        collection: RekordboxCollection,
        playlists: list[RekordboxPlaylist],
    ) -> None:
        self.xml_path = xml_path
        self.collection = collection
        self.playlists = playlists

    def __repr__(self) -> str:
        return (
            "RekordboxLibrary object\n  "
            + f"xml_path:\n{self.xml_path}\n  "
            + f"collection:\n{pprint.pformat(self.collection)}\n  "
            + f"playlists:\n{pprint.pformat(self.playlists)}"
        )

    def __str__(self) -> str:
        return self.__repr__()


class RekordboxNodeType(Enum):
    FOLDER = 0
    PLAYLIST = 1


SpotifyURI = str
SpotifyURL = str
SpotifySearchQuery = str
SpotifySong = dict[str, object]
SpotifySongCollection = dict[SpotifyURI, SpotifySong]
SpotifySearchResults = dict[SpotifySearchQuery, list[SpotifySong]]
PlaylistName = str
SpotifyPlaylistId = str
