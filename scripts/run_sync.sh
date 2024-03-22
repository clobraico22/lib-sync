# run this in the root dir

source .venv/bin/activate

# all flags
if false; then
  python libsync/libsync.py \
  --verbose \
  --verbose \
  sync \
  --rekordbox_xml_path ${HOME}/Documents/rekordbox_export.xml \
  --interactive_mode \
  --create_collection_playlist \
  --skip_create_spotify_playlists \
  --include_loose_songs \

fi


# testing interactive mode
if true; then
  python libsync/libsync.py \
  sync \
  --rekordbox_xml_path ${HOME}/Documents/rekordbox_export.xml \
  --create_collection_playlist \
  --skip_create_spotify_playlists \
  --interactive_mode \


fi
