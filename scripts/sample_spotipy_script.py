import sys

import spotipy
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
    spotify = spotipy.Spotify(auth=token)
    results = spotify.current_user_saved_tracks()
    for item in results["items"]:
        track = item["track"]
        print(track["name"] + " - " + track["artists"][0]["name"])
    # spotify.pause_playback()
    user_id = spotify.current_user()["id"]

    spotify_playlist_data = spotify.user_playlist_create(user=user_id, name="TESTTT")

    exit()

else:
    print("Can't get token for", username)
