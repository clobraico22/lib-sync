import pprint


class RekordboxTrack:
    def __init__(self, id, name, artist, album=None):
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
RekordboxPlaylist = list[str]


class RekordboxLibrary:
    def __init__(
        self,
        collection: RekordboxCollection = {},
        playlists: list[RekordboxPlaylist] = [],
    ):
        self.collection = collection
        self.playlists = playlists

    def __repr__(self) -> str:
        return f"RekordboxLibrary object\n  collection:\n{pprint.pformat(self.collection)}\n  playlists:\n{self.playlists}"

    def __str__(self) -> str:
        return self.__repr__()
