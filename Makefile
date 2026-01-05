.PHONY: help sync sync-dry-run sync-overwrite

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

sync: ## Sync playlists (use when Spotify has changed since last sync)
	uv run libsync sync

sync-dry-run: ## Preview overwriting Spotify playlists from Rekordbox (dry run)
	uv run libsync sync --overwrite_spotify_playlists --dry_run --use_cached_spotify_playlist_data

sync-overwrite: ## Overwrite Spotify playlists from Rekordbox (uses cached data)
	uv run libsync sync --overwrite_spotify_playlists --use_cached_spotify_playlist_data
