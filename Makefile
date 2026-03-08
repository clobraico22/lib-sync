.PHONY: help sync sync-check sync-overwrite analyze

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

sync: ## Fetch fresh Spotify data, match tracks, and show diff
	uv run libsync sync --dry_run

sync-check: ## Re-check diff using cached Spotify data (after updating Rekordbox)
	uv run libsync sync --dry_run --use_cached_spotify_playlist_data

sync-overwrite: ## Overwrite Spotify playlists with Rekordbox data (uses cached Spotify data)
	uv run libsync sync --overwrite_spotify_playlists --use_cached_spotify_playlist_data

analyze: ## Analyze Rekordbox library (key distribution, unplaylisted tracks)
	uv run libsync analyze
