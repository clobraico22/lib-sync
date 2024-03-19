# lib-sync

rekordbox -> spotify playlists

## user guide

### prereqs

- [python 3.10](https://www.python.org/downloads/release/python-31010/) installed locally
- `.env` file in the root directory with client ID and secret
  - go to the [Spotify developers dashboard](https://developer.spotify.com/dashboard) and go to Create App to get a client ID and secret
  - copy `.example.env` from this directory into a new file `.env` in the same directory and add your `id` and `secret`

### steps

- export your rekordbox library as xml (remember where you save the file)
- in this directory, run:

```bash
python3.10 -m venv .venv  # create python virtual environment
source .venv/bin/activate  # activate virtual environment
pip install -r requirements.txt  # install dependencies

# see options for various commands
python libsync/libsync.py -h
python libsync/libsync.py sync -h
python libsync/libsync.py analyze -h
```

## dev quickstart

one time setup:

```bash
python3.10 -m venv .venv
```

activate python virtual environment and update dependencies (after each pull):

```bash
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

to run with sample data:

```bash
python libsync/libsync.py sync \
--rekordbox_xml_path sample_data/example_rekordbox_export.xml \
--create_collection_playlist
```

to run with prod data:

```bash
python libsync/libsync.py sync \
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

# TODO

- multithread shazam process
- connect id tool to spotify mapper and playlist creator
- add editor step before uploading sjpotify playlist
  - maybe just save mappings in a human readable file instead of pickled
  - remember mappings from rekordbox ids and youtube ids
