"""contains constants used across modules"""

import logging

# --- global ---
# in prod, run with logging level critial -
#   this hides all of our exception handling, and only allows print statements
# LOGGING_LEVEL = logging.CRITICAL
# in dev, run with logging level info or warn
# LOGGING_LEVEL = logging.WARN
LOGGING_LEVEL = logging.INFO

# --- sync command ---
ARTIST_LIST_DELIMITERS = r",| & |vs\.|\n|ft\.|feat\.|featuring| / |; "
NUMBER_OF_RESULTS_PER_QUERY = 5
USE_RB_TO_SPOTIFY_MATCHES_CACHE = True
DEBUG_SIMILARITY = False
MINIMUM_SIMILARITY_THRESHOLD = 0.95
RESOLVE_FAILED_MATCHES = True

# --- id command ---
FORCE_REDO_SHAZAM = False
NUM_SHAZAM_MATCHES_THRESHOLD = 3
SHOW_URL_IN_SHAZAM_OUTPUT = False