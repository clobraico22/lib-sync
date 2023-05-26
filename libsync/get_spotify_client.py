import spotipy
import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

load_dotenv()
#TODO: DELETE

# CLIENT_ID = os.getenv("CLIENT_ID")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# REDIRECT_URI = "http://localhost:8080"
username="Claudio LoBraico"
scope=["user-library-read","playlist-modify-private"]

auth_manager= SpotifyOAuth(
    username=username,
    scope=scope
)
auth_manager.get_access_token(code=None, as_dict=True, check_cache=True)


# if token:
#     sp = spotipy.Spotify(auth=token)
#     results = sp.current_user_saved_tracks()
#     for item in results['items']:
#         track = item['track']
#         print(track['name'] + ' - ' + track['artists'][0]['name'])
# else:
#     print("Can't get token for", username)

# token = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

# cache_token = token.get_access_token()
# spotify = spotipy.Spotify(cache_token)

# results1 = spotify.user_playlist_tracks(user="mattyrear", playlist_id="Grease", limit=100, offset=0)