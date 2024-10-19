# run this in the root dir of the project

source .venv/bin/activate

# testing interactive mode
if true; then
  python -m libsync \
  --verbose \
  --verbose \
  sync \
  --rekordbox_xml_path ${HOME}/Documents/rekordbox/rekordbox_export.xml \
  --create_collection_playlist \
  --interactive_mode \
  --dry_run \
  --use_cached_spotify_playlist_data \
  # --skip_spotify_playlist_sync \

fi

# non prod data (KEEP skip_spotify_playlist_sync FLAG!)
if false; then
  python -m libsync \
  --verbose \
  --verbose \
  sync \
  --rekordbox_xml_path sample_data/example_rekordbox_export.xml \
  --skip_spotify_playlist_sync \
  --create_collection_playlist \

fi

# all flags
if false; then
  python -m libsync \
  --verbose \
  --verbose \
  sync \
  --rekordbox_xml_path ${HOME}/Documents/rekordbox/rekordbox_export.xml \
  --interactive_mode \
  --create_collection_playlist \
  --skip_spotify_playlist_sync \
  --include_loose_songs \

fi
