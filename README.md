# Lib-Sync

Lib-Sync is a collection of tools for managing your music library across different platforms.

## Features

- **Sync**: Synchronize your Rekordbox playlists with Spotify playlists
- **Analyze**: Analyze your Rekordbox library for insights and statistics
- **Identify**: Identify songs from recordings or YouTube sets using audio fingerprinting

## Installation

### Install from PyPI

```bash
# with pip
pip install lib-sync

# or with uv
uv pip install --system lib-sync
```

After installation, the `libsync` command will be available in your terminal.

### Prerequisites

- Python 3.11 or higher
- [ffmpeg](https://www.ffmpeg.org/download.html) installed and available on PATH
- Spotify API credentials (for sync functionality)

## Configuration

### Spotify API Setup

1. Go to the [Spotify Developers Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create App" to get a Client ID and Client Secret
3. Create a `.env` file in your working directory:

```bash
cp .example.env .env
```

4. Add your Spotify credentials to the `.env` file:

```
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
```

## Usage

### Sync Rekordbox to Spotify

First, export your library from Rekordbox as XML (File → Export Collection in XML format).

```bash
# Display help
libsync sync -h

# Basic sync
libsync sync --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml

# Sync with collection playlist creation
libsync sync \
  --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml \
  --create_collection_playlist

# Sync specific playlists only
libsync sync \
  --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml \
  --rekordbox_playlist_names "House Music" "Techno Classics"

# Force refresh Spotify search cache
libsync sync \
  --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml \
  --ignore_spotify_search_cache
```

### Analyze Rekordbox Library

```bash
# Display help
libsync analyze -h

# Analyze library
libsync analyze --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml

# Generate detailed report
libsync analyze \
  --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml \
  --output_format detailed
```

### Identify Songs

```bash
# Identify from audio file
libsync id file --recording_audio_file_path ~/Music/unknown_track.mp3

# Identify from YouTube URL
libsync id youtube --youtube_url "https://www.youtube.com/watch?v=VIDEO_ID"

# Identify with timestamp range (for DJ sets)
libsync id youtube \
  --youtube_url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --start_time "10:30" \
  --end_time "15:45"
```

### Debugging

Use `-v` or `--verbose` flags before the subcommand for more detailed output:

```bash
# INFO level logging
libsync -v sync --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml

# DEBUG level logging
libsync -vv sync --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml
```

## Manual Track Matching

After running sync at least once, Lib-Sync creates a CSV file in the `data/` directory with your track mappings. You can manually improve the matches:

1. Open the generated CSV file (e.g., `data/rekordbox_spotify_matches_YYYY-MM-DD.csv`)
2. To manually match a track:
   - Paste the Spotify track URL in the `Spotify URL (input)` column
   - For tracks not on Spotify, enter `libsync:NOT_ON_SPOTIFY` in the `Spotify URI` column
3. To retry automatic matching:
   - Put `1` in the `Retry auto match (input)` column
   - Use with `--ignore_spotify_search_cache` to force a new search

The next sync will use your manual corrections.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.
