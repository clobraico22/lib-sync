# lib-sync

libsync has some useful tools for managing your music library.

- `sync` syncs your rekordbox playlists to spotify playlists.
- `analyze` analyzes your rekordbox library.
- `id` identifies songs from a recording or youtube set.

## user guide

### prereqs

- [python 3.10](https://www.python.org/downloads/release/python-31010/) installed locally
- `.env` file in the root directory with client ID and secret
  - go to the [Spotify developers dashboard](https://developer.spotify.com/dashboard) and go to Create App to get a client ID and secret
  - copy `.example.env` from this directory into a new file `.env` in the same directory and add your `id` and `secret`

### setup

in this directory, run:

```bash
python3.10 -m venv .venv  # create python virtual environment
source .venv/bin/activate  # activate virtual environment
pip install -r requirements.txt  # install dependencies
```

### sync

- export your rekordbox library as xml (remember where you save the file)

```bash
python libsync/libsync.py sync -h   # display help page

python libsync/libsync.py sync \
--rekordbox_xml_path ${HOME}/Documents/rekordbox_export.xml \
--create_collection_playlist
```

#### manually fixing the mappings

After running the sync command at least once for your library, you can update the `spotify URL (input)` column in the `data/*.csv` file generated by libsync. Just paste in the track's spotify URL in the `Spotify URL (input)` column. Then next time you sync, libsync will pick up those new mappings and update your playlists. You can also manually update the `Spotify URI` column with `libsync:NOT_ON_SPOTIFY` for songs you know are not on Spotify, so libsync knows to stop looking for it.

If you want libsync to redo the auto mapping process for a previously analyzed song, you can tag it with a `1` in the `Retry auto match (input)` column in the csv. This can be useful if a song is newly posted on Spotify, or to take advantage of libsync improvements. This will override the `libsync:NOT_ON_SPOTIFY` flag. Use this with the `--ignore_spotify_search_cache` command line flag to hit the network again instead of just using the cache and running the matching algorithm again.

### analyze

```bash
python libsync/libsync.py analyze -h
```

## dev guide

### quickstart

one time setup:

```bash
python3.10 -m venv .venv
```

add the following to your `.bashrc` or `.zshrc`:

```bash
LIBSYNC_REPO_DIRECTORY='/Users/joshlebed/code/lib-sync' # update to the path to the repo on your machine
alias libsync-dev="${LIBSYNC_REPO_DIRECTORY}/.venv/bin/python ${LIBSYNC_REPO_DIRECTORY}/libsync/libsync.py"
```

activate python virtual environment and update dependencies (after each pull):

```bash
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

use `--verbose` or `-v` before the subcommand to increase the verbosity of logging to the console.
use one `-v` for INFO level, two for DEBUG level.
to run with sample data:

```bash
python libsync/libsync.py \
--verbose \
--verbose \
sync \
--rekordbox_xml_path sample_data/example_rekordbox_export.xml \
--create_collection_playlist
```

to run with prod data:

```bash
python libsync/libsync.py \
--verbose \
--verbose \
sync \
--rekordbox_xml_path ${HOME}/Documents/rekordbox_export.xml \
--create_collection_playlist
```

to run analysis command:

```bash
python libsync/libsync.py analyze \
--rekordbox_xml_path sample_data/example_rekordbox_export.xml \

python libsync/libsync.py analyze \
--rekordbox_xml_path ${HOME}/Documents/rekordbox_export.xml
```

to run id command:

```bash
python libsync/libsync.py id file \
--recording_audio_file_path sample_data/file.mp3 \
```

```bash
python libsync/libsync.py id youtube \
--youtube_url https://www.youtube.com/watch\?v\=6qSnO5U95yU \
```

## linting/formatting

you don't have to worry

# TODO

- multithread shazam process
- connect id tool to spotify mapper and playlist creator
- get markdown autoformatter
