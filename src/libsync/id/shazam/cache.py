"""SQLite-backed segment-level cache for Shazam recognition results."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

import builtins

from libsync.id.shazam.models import SegmentCacheKey, SegmentResult

logger = logging.getLogger("libsync")


class SegmentCache:
    """SQLite-backed segment-level cache for Shazam results.

    Provides:
    - Per-segment caching (unlike the old file-level pickle cache)
    - Resume capability after interruption
    - Fast re-runs of previously processed files
    - Queryable cache for debugging
    """

    def __init__(self, cache_path: str):
        """Initialize the cache.

        Args:
            cache_path: Path to the SQLite database file
        """
        self.cache_path = cache_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the cache database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS segment_results (
                    cache_key TEXT PRIMARY KEY,
                    audio_hash TEXT NOT NULL,
                    start_ms INTEGER NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    result_json TEXT,
                    track_id TEXT,
                    title TEXT,
                    artist TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audio_hash
                ON segment_results(audio_hash)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audio_hash_start
                ON segment_results(audio_hash, start_ms)
            """)

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.cache_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def get(self, key: SegmentCacheKey) -> SegmentResult | None:
        """Retrieve cached result for a segment.

        Args:
            key: Cache key identifying the segment

        Returns:
            SegmentResult if cached, None if not in cache
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM segment_results WHERE cache_key = ?", (str(key),)
            ).fetchone()

            if row is None:
                return None

            # Reconstruct the SegmentResult
            raw_response = json.loads(row["result_json"]) if row["result_json"] else None
            return SegmentResult(
                start_ms=row["start_ms"],
                raw_response=raw_response,
                track_id=row["track_id"],
                title=row["title"],
                artist=row["artist"],
            )

    def set(self, key: SegmentCacheKey, result: SegmentResult) -> None:
        """Store a segment result in the cache.

        Args:
            key: Cache key identifying the segment
            result: Recognition result to cache
        """
        result_json = json.dumps(result.raw_response) if result.raw_response else None

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO segment_results
                (cache_key, audio_hash, start_ms, duration_ms, result_json,
                 track_id, title, artist)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(key),
                    key.audio_file_hash,
                    key.start_ms,
                    key.duration_ms,
                    result_json,
                    result.track_id,
                    result.title,
                    result.artist,
                ),
            )

    def has(self, audio_hash: str, start_ms: int, duration_ms: int = 15000) -> bool:
        """Check if a segment is already cached.

        Args:
            audio_hash: Audio file hash
            start_ms: Segment start time
            duration_ms: Segment duration

        Returns:
            True if segment is cached, False otherwise
        """
        key = SegmentCacheKey(audio_hash, start_ms, duration_ms)
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM segment_results WHERE cache_key = ?", (str(key),)
            ).fetchone()
            return row is not None

    def get_cached_segments(self, audio_hash: str) -> builtins.set[int]:
        """Get all cached segment start times for a given audio file.

        Args:
            audio_hash: Audio file hash

        Returns:
            Set of start_ms values that are cached
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT start_ms FROM segment_results WHERE audio_hash = ?", (audio_hash,)
            ).fetchall()
            return {row["start_ms"] for row in rows}

    def get_all_results(self, audio_hash: str) -> list[SegmentResult]:
        """Get all cached results for an audio file.

        Args:
            audio_hash: Audio file hash

        Returns:
            List of SegmentResults ordered by start_ms
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM segment_results
                WHERE audio_hash = ?
                ORDER BY start_ms
            """,
                (audio_hash,),
            ).fetchall()

            results = []
            for row in rows:
                raw_response = json.loads(row["result_json"]) if row["result_json"] else None
                results.append(
                    SegmentResult(
                        start_ms=row["start_ms"],
                        raw_response=raw_response,
                        track_id=row["track_id"],
                        title=row["title"],
                        artist=row["artist"],
                    )
                )
            return results

    def get_matches_only(self, audio_hash: str) -> list[SegmentResult]:
        """Get only cached results that have a track match.

        Args:
            audio_hash: Audio file hash

        Returns:
            List of SegmentResults with matches, ordered by start_ms
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM segment_results
                WHERE audio_hash = ? AND track_id IS NOT NULL
                ORDER BY start_ms
            """,
                (audio_hash,),
            ).fetchall()

            results = []
            for row in rows:
                raw_response = json.loads(row["result_json"]) if row["result_json"] else None
                results.append(
                    SegmentResult(
                        start_ms=row["start_ms"],
                        raw_response=raw_response,
                        track_id=row["track_id"],
                        title=row["title"],
                        artist=row["artist"],
                    )
                )
            return results

    def clear_for_audio(self, audio_hash: str) -> int:
        """Clear all cached results for a specific audio file.

        Args:
            audio_hash: Audio file hash

        Returns:
            Number of rows deleted
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM segment_results WHERE audio_hash = ?", (audio_hash,))
            deleted = cursor.rowcount
            logger.info(f"Cleared {deleted} cached segments for audio hash {audio_hash}")
            return deleted

    def get_cache_stats(self, audio_hash: str) -> dict[str, int]:
        """Get statistics about cached segments for an audio file.

        Args:
            audio_hash: Audio file hash

        Returns:
            Dict with stats: total_segments, segments_with_match, unique_tracks
        """
        with self._get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM segment_results WHERE audio_hash = ?", (audio_hash,)
            ).fetchone()[0]

            with_match = conn.execute(
                "SELECT COUNT(*) FROM segment_results WHERE audio_hash = ? AND track_id IS NOT NULL",
                (audio_hash,),
            ).fetchone()[0]

            unique_tracks = conn.execute(
                "SELECT COUNT(DISTINCT track_id) FROM segment_results WHERE audio_hash = ? AND track_id IS NOT NULL",
                (audio_hash,),
            ).fetchone()[0]

            return {
                "total_segments": total,
                "segments_with_match": with_match,
                "unique_tracks": unique_tracks,
            }
