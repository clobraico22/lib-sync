"""Shazam recognition module with parallel processing and caching."""

from libsync.id.shazam.cache import SegmentCache
from libsync.id.shazam.extractor import SegmentExtractor
from libsync.id.shazam.models import SegmentCacheKey, SegmentResult, SegmentSpec, TrackMatch
from libsync.id.shazam.recognizer import ShazamRecognizer

__all__ = [
    "SegmentCache",
    "SegmentCacheKey",
    "SegmentExtractor",
    "SegmentResult",
    "SegmentSpec",
    "ShazamRecognizer",
    "TrackMatch",
]
