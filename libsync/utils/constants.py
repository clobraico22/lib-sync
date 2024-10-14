"""contains constants used across modules"""

from enum import Enum


class SpotifyMappingDbFlags(str, Enum):
    """enum with database flag strings"""

    NOT_ON_SPOTIFY = "libsync:NOT_ON_SPOTIFY"
    SKIP_TRACK = "libsync:SKIP_TRACK"


class InteractiveWorkflowCommands(str, Enum):
    """enum with song match interactive workflow command strings"""

    NOT_ON_SPOTIFY = "NOT_ON_SPOTIFY"
    EXIT_AND_SAVE = "EXIT_AND_SAVE"
    SKIP_TRACK = "SKIP_TRACK"
    CANCEL = "CANCEL"


# Constants

ARTIST_LIST_DELIMITERS = r",| & |vs\.|\n|ft\.|feat\.|featuring| / |; "
NUMBER_OF_RESULTS_PER_QUERY = 5
MINIMUM_SIMILARITY_THRESHOLD = 0.95
SPOTIFY_TRACK_URI_PREFIX = "spotify:track:"
SPOTIFY_API_ITEMS_PER_PAGE = 100
SPOTIFY_API_GET_TRACKS_ITEMS_PER_PAGE = 50

NUM_SHAZAM_MATCHES_THRESHOLD = 5


# Flags
# TODO: clean up some of these global flags, move the useful ones into cli args

USE_RB_TO_SPOTIFY_MATCHES_CACHE = True
DEBUG_SIMILARITY = False
IGNORE_SP_NEW_TRACKS = False

FORCE_REDO_SHAZAM = False
SHOW_URL_IN_SHAZAM_OUTPUT = False

MAX_RETRIES = 3
