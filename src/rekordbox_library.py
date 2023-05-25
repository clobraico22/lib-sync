class RekordboxTrack:
    def __init__(self, id, name, artist, album=""):
        self.id = id
        self.name = name
        self.artist = artist
        self.album = album

    def __str__(self) -> str:
        return f"[{self.id}] {self.name} - {self.artist} - {self.album}"


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
