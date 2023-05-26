# lib-sync

rekordbox -> spotify playlists

## how to use

TODO: make this script more portable so anyone can run it on their machine (preferably without docker)

### prereqs

- python 3.10
- pip install packages from requirements.txt (TODO: add virtualenvs)
- `.env` file in the root directory (copy .example.env and add your `id` and `secret`)

### steps

- export your rekordbox library as xml (remember where you save the file)
- in this directory, run:

```bash
python3.10 libsync/cli_entry_point.py \
--rekordbox_xml_path <path to your XML file> \
--spotify_username <your spotify username>
```

## dev quickstart

to run with sample data:

```bash
python3.10 libsync/cli_entry_point.py \
--rekordbox_xml_path sample_data/example_rekordbox_export.xml
```
