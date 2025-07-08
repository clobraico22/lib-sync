# Contributing to Lib-Sync

Thank you for your interest in contributing to Lib-Sync! This guide will help you set up your development environment and understand our development workflow.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [Rye](https://rye-up.com/) for Python project management
- [ffmpeg](https://www.ffmpeg.org/download.html) installed and available on PATH
- [pipx](https://pipx.pypa.io/stable/installation/) for testing wheel installation locally

### Initial Setup

1. Clone the repository:

```bash
git clone https://github.com/clobraico22/lib-sync.git
cd lib-sync
```

2. Install development dependencies using Rye:

```bash
rye sync --all-features
```

3. Install pre-commit hooks:

```bash
rye run pre-commit install
```

4. Create a `.env` file for testing:

```bash
cp .env.example .env
# Add your Spotify API credentials to .env
```

### Development Workflow

#### Running the Code

During development, use Rye to run the code:

```bash
# Run with Rye
rye run libsync sync --help
```

#### Useful Shell Aliases

Add these to your `.bashrc` or `.zshrc` for convenience:

```bash
# Update the path to match your local repo location
LIBSYNC_REPO_DIRECTORY="${HOME}/code/lib-sync"
alias libsync-dev="cd ${LIBSYNC_REPO_DIRECTORY} && rye run libsync"
alias libsync-run-sync="cd ${LIBSYNC_REPO_DIRECTORY} && ${LIBSYNC_REPO_DIRECTORY}/scripts/run_sync.sh"
alias libsync-run-sync-edit="cd ${LIBSYNC_REPO_DIRECTORY} && code ${LIBSYNC_REPO_DIRECTORY}/scripts/run_sync.sh"
```

### Testing

#### Running with Sample Data

The repository includes sample data for testing:

```bash
# Test sync command
rye run libsync -vv sync \
  --rekordbox_xml_path sample_data/example_rekordbox_export.xml \
  --create_collection_playlist

# Test analyze command
rye run libsync analyze \
  --rekordbox_xml_path sample_data/example_rekordbox_export.xml

# Test identify command
rye run libsync id file \
  --recording_audio_file_path sample_data/file.mp3

rye run libsync id youtube \
  --youtube_url "https://www.youtube.com/watch?v=6qSnO5U95yU"
```

#### Running with Your Own Data

```bash
# Sync with your Rekordbox library
rye run libsync -vv sync \
  --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml \
  --create_collection_playlist

# Analyze your library
rye run libsync analyze \
  --rekordbox_xml_path ~/Documents/rekordbox/rekordbox_export.xml
```

### Code Quality

#### Linting and Formatting

We use Ruff for both linting and formatting:

```bash
# Run linter
rye run ruff check src/

# Run formatter
rye run ruff format src/

# Run both with pre-commit
rye run pre-commit run --all-files
```

#### Type Checking

We use mypy for static type checking:

```bash
rye run mypy src/
```

### Project Structure

```
lib-sync/
├── src/libsync/        # Main package source code
│   ├── analyze/        # Library analysis tools
│   ├── db/            # Database operations
│   ├── id/            # Song identification tools
│   ├── spotify/       # Spotify integration
│   └── utils/         # Shared utilities
├── sample_data/       # Test data
├── data/              # Caches and mappings
├── scripts/           # Utility scripts
├── pyproject.toml     # Project configuration
└── .pre-commit-config.yaml  # Pre-commit hooks
```

### Making Changes

1. Create a new branch for your feature/fix:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and ensure tests pass
3. Run pre-commit checks:

```bash
rye run pre-commit run --all-files
```

4. Commit your changes with a descriptive message
5. Push your branch and create a pull request

### Adding Dependencies

To add a new dependency:

```bash
# Add a runtime dependency
rye add package-name

# Add a development dependency
rye add --dev package-name
```

Then run `rye sync` to update the lock file.

### Building and Publishing

To build the package:

```bash
rye build
```

To publish to PyPI (maintainers only):

```bash
rye run publish
```

### Testing wheel installation locally

```bash
# Build the wheel
rye build

# Install the wheel
python -m pip install --force-reinstall --user dist/lib_sync-*.whl
```

## Future Development Ideas

### Features

- Support for tracking deletions from Rekordbox
- Read-only playlist support (e.g., "to be tagged")
- Multi-threaded Shazam processing for faster identification
- Direct integration between ID tool and Spotify playlist creation

### Technical Improvements

- Add more comprehensive test coverage
- Improve error handling and user feedback
- Add progress bars for long-running operations
- Implement caching strategies for better performance

## Getting Help

- Open an issue on GitHub for bugs or feature requests
- Join our discussions for questions and ideas
- Check existing issues before creating new ones

```

```
