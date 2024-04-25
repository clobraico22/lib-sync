"""contains constants used across modules"""

# TODO: clean up some of these global flags, move the useful ones into cli args

# --- sync command ---
ARTIST_LIST_DELIMITERS = r",| & |vs\.|\n|ft\.|feat\.|featuring| / |; "
NUMBER_OF_RESULTS_PER_QUERY = 5
USE_RB_TO_SPOTIFY_MATCHES_CACHE = True
DEBUG_SIMILARITY = False
MINIMUM_SIMILARITY_THRESHOLD = 0.95
RESOLVE_FAILED_MATCHES = False
NOT_ON_SPOTIFY_FLAG = "libsync:NOT_ON_SPOTIFY"
EXIT_AND_SAVE_FLAG = "libsync:EXIT_AND_SAVE"
SKIP_TRACK_FLAG = "libsync:SKIP_TRACK_FLAG"
CANCEL_FLAG = "libsync:CANCEL_FLAG"
SPOTIFY_TRACK_URI_PREFIX = "spotify:track:"
IGNORE_SP_NEW_TRACKS = False
SPOTIFY_API_ITEMS_PER_PAGE = 100

# --- id command ---
FORCE_REDO_SHAZAM = False
NUM_SHAZAM_MATCHES_THRESHOLD = 5
SHOW_URL_IN_SHAZAM_OUTPUT = False
