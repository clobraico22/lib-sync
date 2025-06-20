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


class RekordboxTrack:
    """Relevant track info from rekordbox xml file"""

    def __init__(
        self, id: RekordboxTrackID, name: str, artist: str, album: str | None = None
    ) -> None:
        self.id = id
        self.name = name
        self.artist = artist
        self.album = album

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
