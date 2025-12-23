# Lib-Sync

Lib-Sync is a collection of tools for managing your music library across different platforms.

## Features

- **Sync**: Synchronize your Rekordbox playlists with Spotify playlists
- **Analyze**: Analyze your Rekordbox library for insights and statistics
- **Identify**: Identify songs from recordings or YouTube sets using audio fingerprinting

## Installation from PyPI

Please make sure you have Python 3.11 or newer (python --version).

### Install lib-sync

```bash
# with uvx (recommended)
uvx lib-sync

# with pipx
pipx install lib-sync

# with pip
python -m pip install lib-sync
```

### Upgrade lib-sync

```bash
# with uv (recommended)
uv tool upgrade lib-sync

# with pipx
pipx upgrade lib-sync

# with pip
python -m pip install --upgrade lib-sync
```

After installation, the `libsync` command will be available in your terminal.

**Troubleshooting**: If `libsync` command is not found:

- Make sure you're using Python 3.11 or higher
- If your python is installed via uv (or in a virtual environment), try `python -m pip install --force-reinstall --user lib-sync`
- try running `python -m pip install --upgrade pip wheel` first

### Prerequisites

- Python 3.11 or higher
- For YouTube id extraction, you'll need [ffmpeg](https://www.ffmpeg.org/download.html) installed and available on PATH
- For Spotify sync functionality, you'll need Spotify API credentials (see [Spotify API Setup](#spotify-api-setup) below)

## Configuration

### Environment Variables

Create a `.env` file in your working directory:

```bash
cp .env.example .env
```

Supported environment variables:

```bash
# Required for Spotify sync
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://localhost:8080

# Optional: Default path to Rekordbox XML export
REKORDBOX_XML_PATH=/path/to/rekordbox_export.xml
```

### Spotify API Setup

1. Go to the [Spotify Developers Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create App" to get a Client ID and Client Secret
3. Add your credentials to the `.env` file (see above)

## Usage

### Sync Rekordbox to Spotify

1. Export your library from Rekordbox (File → Export Collection in XML format)
2. Tell libsync where to find the exported XML file - two options:
   - CLI flag: `--rekordbox_xml_path /path/to/export.xml` (takes precedence)
   - Environment variable: Set `REKORDBOX_XML_PATH` in your `.env` file
3. Run the sync command:

```bash
# Describe available flags
libsync sync -h

# Basic sync (using environment variable from .env)
libsync sync

# Basic sync (using CLI flag)
libsync sync --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml
```

### Analyze Rekordbox Library

```bash
# Describe available flags
libsync analyze -h

# Analyze library (path from CLI or .env)
libsync analyze

# Analyze with explicit path
libsync analyze --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml
```

### Identify Songs

```bash
# Identify from audio file
libsync id file --recording_audio_file_path ~/Music/unknown_track.mp3

# Identify from YouTube URL
libsync id youtube --youtube_url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Audio Analysis Scripts

In addition to the CLI commands, lib-sync includes standalone scripts for analyzing audio recordings.

#### BPM Analysis

Analyzes BPM throughout an audio recording and produces a visualization showing tempo changes over time.

```bash
# Basic usage
uv run python scripts/bpm_analysis.py recording.m4a

# Custom window size and BPM range
uv run python scripts/bpm_analysis.py recording.mp3 --window-size 20 --hop-size 10

# Specify BPM range for electronic music
uv run python scripts/bpm_analysis.py recording.wav --min-bpm 100 --max-bpm 150

# Custom output path
uv run python scripts/bpm_analysis.py recording.m4a -o my_analysis.png
```

**Features:**
- Multi-method tempo detection (tempogram, autocorrelation, beat tracking) for robustness
- Automatic octave error correction (handles half/double tempo detection errors)
- Music vs silence detection to exclude non-music sections
- Outlier filtering with configurable thresholds
- Three-panel visualization: BPM trend, detection confidence, music presence

**Output:** Generates `<filename>_bpm_analysis.png` with:
- BPM measurements over time with outliers marked
- Smoothed BPM trend line
- Confidence scores for each measurement
- Music/silence detection timeline
- Summary statistics (median, mean, std dev, range)

#### Combined Analysis Visualization

Creates a combined visualization showing BPM analysis with Shazam track detections overlaid. Requires running `libsync id file` first to populate the Shazam cache.

```bash
# Basic usage (after running libsync id file on the recording)
uv run python scripts/combined_analysis_viz.py recording.m4a

# Require more matches for higher confidence
uv run python scripts/combined_analysis_viz.py recording.m4a --min-matches 3

# Custom output path
uv run python scripts/combined_analysis_viz.py recording.m4a -o combined.png
```

**Features:**
- Overlays detected track names on the BPM graph with timestamps
- Color-coded track regions showing where each song was detected
- Match count displayed for each track (e.g., `[7x]` = detected 7 times)
- Track detection timeline showing song durations
- Prints tracklist summary with timestamps

**Output:** Generates `<filename>_combined_analysis.png` with:
- Top panel: BPM trend with track annotations and shaded regions
- Bottom panel: Track detection timeline with match counts

### Debugging

Logs go to `~/.libsync/data/logs`. check there for records of all the libsync commands you run.
Use `-v` or `--verbose` flags before the subcommand for more detailed output:

```bash
# INFO level logging
libsync -v sync

# DEBUG level logging
libsync -vv sync
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
