#!/bin/bash
# run this in the root dir of the project

# testing interactive mode
if true; then
  uv run libsync \
    --verbose \
    sync

fi

# non prod data (KEEP skip_spotify_playlist_sync FLAG!)
if false; then
  uv run libsync \
    --verbose \
    --verbose \
    sync \
    --rekordbox_xml_path sample_data/example_rekordbox_export.xml \
    --skip_spotify_playlist_sync \

fi

# all flags
if false; then
  uv run libsync \
    --verbose \
    --verbose \
    sync \
    --rekordbox_xml_path "${HOME}"/Documents/rekordbox/rekordbox_export.xml \
    --skip_interactive_mode \
    --skip_interactive_mode_pending_tracks \
    --ignore_spotify_search_cache \
    --skip_spotify_playlist_sync \
    --skip_collection_playlist \
    --make_playlists_public \
    --include_loose_songs \
    --dry_run \
    --use_cached_spotify_playlist_data \
    --overwrite_spotify_playlists \

fi
