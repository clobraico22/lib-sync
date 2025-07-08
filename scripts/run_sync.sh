#!/bin/bash
# run this in the root dir of the project

# testing interactive mode
if true; then
  rye run libsync \
    sync \
    --rekordbox_xml_path "${HOME}"/Documents/rekordbox/rekordbox_export.xml \
    --create_collection_playlist \
    --interactive_mode \
    --interactive_mode_pending_tracks \
    --use_cached_spotify_playlist_data \
    --dry_run

fi

# non prod data (KEEP skip_spotify_playlist_sync FLAG!)
if false; then
  rye run libsync \
    --verbose \
    --verbose \
    sync \
    --rekordbox_xml_path sample_data/example_rekordbox_export.xml \
    --skip_spotify_playlist_sync \
    --create_collection_playlist

fi

# all flags
if false; then
  rye run libsync \
    --verbose \
    --verbose \
    sync \
    --rekordbox_xml_path "${HOME}"/Documents/rekordbox/rekordbox_export.xml \
    --interactive_mode \
    --create_collection_playlist \
    --skip_spotify_playlist_sync \
    --include_loose_songs

fi
