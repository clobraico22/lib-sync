"""Data models for the Shazam recognition module."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SegmentSpec:
    """Specification for an audio segment to process."""

    start_ms: int
    duration_ms: int = 15000  # Default 15 seconds

    @property
    def end_ms(self) -> int:
        return self.start_ms + self.duration_ms


@dataclass
class SegmentCacheKey:
    """Unique identifier for a cached Shazam result.

    The cache key combines:
    - audio_file_hash: First 1MB SHA256 hash to detect file changes
    - start_ms: Segment start time
    - duration_ms: Segment duration (to invalidate if parameters change)
    """

    audio_file_hash: str
    start_ms: int
    duration_ms: int = 15000

    def __str__(self) -> str:
        return f"{self.audio_file_hash}_{self.start_ms}_{self.duration_ms}"

    @staticmethod
    def compute_file_hash(audio_path: str, read_bytes: int = 1024 * 1024) -> str:
        """Compute partial hash of audio file for cache identification.

        Uses first 1MB of file for fast hashing while still detecting changes.

        Args:
            audio_path: Path to the audio file
            read_bytes: Number of bytes to read for hashing (default 1MB)

        Returns:
            16-character hex string of the hash
        """
        hasher = hashlib.sha256()
        with open(audio_path, "rb") as f:
            hasher.update(f.read(read_bytes))
        return hasher.hexdigest()[:16]


@dataclass
class SegmentResult:
    """Result from Shazam recognition of a single segment."""

    start_ms: int
    raw_response: dict[str, Any] | None = None
    track_id: str | None = None
    title: str | None = None
    artist: str | None = None

    @property
    def has_match(self) -> bool:
        return self.track_id is not None

    @classmethod
    def from_shazam_response(cls, start_ms: int, response: dict[str, Any] | None) -> SegmentResult:
        """Create a SegmentResult from a Shazam API response.

        Args:
            start_ms: Segment start time in milliseconds
            response: Raw Shazam API response dict

        Returns:
            SegmentResult with extracted track info if available
        """
        if not response or "track" not in response:
            return cls(start_ms=start_ms, raw_response=response)

        track = response["track"]
        return cls(
            start_ms=start_ms,
            raw_response=response,
            track_id=track.get("key"),
            title=track.get("title"),
            artist=track.get("subtitle"),
        )


@dataclass
class TrackMatch:
    """Aggregated match information for a single track."""

    shazam_id: str
    title: str
    artist: str
    first_seen_ms: int
    last_seen_ms: int
    match_timestamps: list[int] = field(default_factory=list)

    @property
    def match_count(self) -> int:
        return len(self.match_timestamps)

    @property
    def duration_ms(self) -> int:
        """Duration from first to last detection."""
        return self.last_seen_ms - self.first_seen_ms

    def calculate_confidence(self) -> float:
        """Calculate confidence score based on match count and temporal spread.

        Returns:
            Float between 0 and 1 indicating confidence level
        """
        # Factor 1: Number of matches (capped at 3 for full score)
        count_score = min(self.match_count / 3, 1.0)

        # Factor 2: Temporal spread (90s spread = full score)
        spread_score = min(self.duration_ms / 90000, 1.0)

        # Weighted combination
        return count_score * 0.6 + spread_score * 0.4

    def add_match(self, timestamp_ms: int) -> None:
        """Add a new match timestamp and update bounds."""
        self.match_timestamps.append(timestamp_ms)
        self.first_seen_ms = min(self.first_seen_ms, timestamp_ms)
        self.last_seen_ms = max(self.last_seen_ms, timestamp_ms)
