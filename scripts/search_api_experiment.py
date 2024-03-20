import logging
import sys

import spotipy.util as util

scope = ["user-library-read"]

scope = [
    # "ugc-image-upload",
    # "user-read-playback-state",
    # "user-modify-playback-state",
    # "user-read-currently-playing",
    "app-remote-control",
    "streaming",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    # "user-follow-modify",
    # "user-follow-read",
    # "user-read-playback-position",
    # "user-top-read",
    # "user-read-recently-played",
    # "user-library-modify",
    "user-library-read",
    # "user-read-email",
    # "user-read-private",
    # "user-soa-link",
    # "user-soa-unlink",
    # "soa-manage-entitlements",
    # "soa-manage-partner",
    # "soa-create-partner",
]

# scope = []

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

token = util.prompt_for_user_token(username, scope)

if token:
    print(token)
    print(
        "https://api-partner.spotify.com/pathfinder/v1/query?operationName=searchDesktop&variables=%7B%22searchTerm%22%3A%22mystringuniquestring%22%2C%22offset%22%3A0%2C%22limit%22%3A10%2C%22numberOfTopResults%22%3A5%2C%22includeAudiobooks%22%3Atrue%2C%22includeArtistHasConcertsField%22%3Afalse%2C%22includePreReleases%22%3Afalse%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22339dfbacfc823a4b720b2c42dda51cc5b302966652b823958a6bdddbe914fa41%22%7D%7D"
    )
    logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(level=logging.ERROR)
    logging.debug("info")
    logging.info("info")
    logging.error("info")

    exit()

else:
    print("Can't get token for", username)
