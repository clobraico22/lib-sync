# run this in the root dir of the project

source .venv/bin/activate

# testing interactive mode
if true; then
  python libsync/libsync.py \
  --verbose \
  --verbose \
  sync \
  --rekordbox_xml_path ${HOME}/Documents/rekordbox_export.xml \
  --create_collection_playlist \
  --interactive_mode \

fi

# all flags
if false; then
  python libsync/libsync.py \
  --verbose \
  --verbose \
  sync \
  --rekordbox_xml_path ${HOME}/Documents/rekordbox_export.xml \
  --interactive_mode \
  --create_collection_playlist \
  --skip_spotify_playlist_sync \
  --include_loose_songs \

fi
