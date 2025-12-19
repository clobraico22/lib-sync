"""Parallel Shazam recognition with rate limiting and caching."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

from aiohttp_retry import ExponentialRetry
from shazamio import HTTPClient, Shazam

from libsync.id.shazam.cache import SegmentCache
from libsync.id.shazam.models import SegmentCacheKey, SegmentResult

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger("libsync")


class ShazamRecognizer:
    """Parallel Shazam API requests with semaphore-based rate limiting.

    Uses asyncio.Semaphore to limit concurrent requests and prevent
    overwhelming the Shazam API with too many parallel requests.
    """

    def __init__(self, max_concurrent: int = 10):
        """Initialize the recognizer.

        Args:
            max_concurrent: Maximum number of concurrent Shazam API requests
        """
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._shazam: Shazam | None = None

    def _get_shazam(self) -> Shazam:
        """Get or create the Shazam client with retry configuration."""
        if self._shazam is None:
            self._shazam = Shazam(
                http_client=HTTPClient(
                    retry_options=ExponentialRetry(
                        attempts=12,
                        max_timeout=204.8,
                        statuses={500, 502, 503, 504, 429},
                    ),
                ),
            )
        return self._shazam

    async def recognize_segment(
        self,
        segment_path: str,
        start_ms: int,
        audio_hash: str,
        duration_ms: int,
        cache: SegmentCache | None = None,
    ) -> SegmentResult:
        """Recognize a single segment with semaphore limiting.

        Args:
            segment_path: Path to the audio segment file
            start_ms: Segment start time in milliseconds
            audio_hash: Hash of the source audio file
            duration_ms: Segment duration in milliseconds
            cache: Optional cache to check/store results

        Returns:
            SegmentResult with recognition data
        """
        cache_key = SegmentCacheKey(audio_hash, start_ms, duration_ms)

        # Check cache first (outside semaphore to avoid blocking)
        if cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for segment at {start_ms}ms")
                return cached_result

        # Acquire semaphore for API call
        async with self._semaphore:
            try:
                shazam = self._get_shazam()
                response = await shazam.recognize(segment_path)
                result = SegmentResult.from_shazam_response(start_ms, response)

                # Cache the result
                if cache:
                    cache.set(cache_key, result)

                if result.has_match:
                    logger.debug(f"Match at {start_ms}ms: {result.artist} - {result.title}")
                else:
                    logger.debug(f"No match at {start_ms}ms")

                return result

            except Exception as e:
                logger.error(f"Shazam error at {start_ms}ms: {e}")
                # Return empty result on error (don't cache failures)
                return SegmentResult(start_ms=start_ms)

    async def recognize_batch(
        self,
        segment_paths: list[tuple[str, int]],
        audio_hash: str,
        duration_ms: int,
        cache: SegmentCache | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        cleanup_segments: bool = True,
    ) -> list[SegmentResult]:
        """Recognize multiple segments in parallel.

        Args:
            segment_paths: List of (segment_path, start_ms) tuples
            audio_hash: Hash of the source audio file
            duration_ms: Segment duration in milliseconds
            cache: Optional cache for results
            progress_callback: Optional callback(completed, total) for progress
            cleanup_segments: Whether to delete segment files after recognition

        Returns:
            List of SegmentResults
        """
        tasks = [
            self.recognize_segment(path, start_ms, audio_hash, duration_ms, cache)
            for path, start_ms in segment_paths
        ]

        results: list[SegmentResult] = []

        # Process with progress tracking using as_completed
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            result = await coro
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(tasks))
            # Small delay every 5 requests to avoid rate limiting
            if i % 5 == 4:
                await asyncio.sleep(2.0)

        # Cleanup segment files if requested
        if cleanup_segments:
            for path, _ in segment_paths:
                try:
                    os.remove(path)
                except OSError as e:
                    logger.warning(f"Failed to remove segment file {path}: {e}")

        return results

    async def recognize_batch_ordered(
        self,
        segment_paths: list[tuple[str, int]],
        audio_hash: str,
        duration_ms: int,
        cache: SegmentCache | None = None,
        cleanup_segments: bool = True,
    ) -> list[SegmentResult]:
        """Recognize multiple segments, returning results in input order.

        Args:
            segment_paths: List of (segment_path, start_ms) tuples
            audio_hash: Hash of the source audio file
            duration_ms: Segment duration in milliseconds
            cache: Optional cache for results
            cleanup_segments: Whether to delete segment files after recognition

        Returns:
            List of SegmentResults in same order as input
        """
        tasks = [
            self.recognize_segment(path, start_ms, audio_hash, duration_ms, cache)
            for path, start_ms in segment_paths
        ]

        results = await asyncio.gather(*tasks)

        # Cleanup segment files if requested
        if cleanup_segments:
            for path, _ in segment_paths:
                try:
                    os.remove(path)
                except OSError as e:
                    logger.warning(f"Failed to remove segment file {path}: {e}")

        return list(results)


async def extract_and_recognize_parallel(
    audio_path: str,
    temp_dir: str,
    segments_to_process: list[int],
    audio_hash: str,
    segment_duration_ms: int,
    cache: SegmentCache,
    max_concurrent_shazam: int = 10,
    max_ffmpeg_workers: int = 4,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[SegmentResult]:
    """Combined extraction and recognition pipeline.

    Extracts segments in parallel with FFmpeg, then recognizes them
    in parallel with Shazam, with appropriate rate limiting for each.

    Args:
        audio_path: Path to source audio file
        temp_dir: Directory for temporary segment files
        segments_to_process: List of start_ms values to process
        audio_hash: Hash of the source audio file
        segment_duration_ms: Duration of each segment in milliseconds
        cache: Cache for storing results
        max_concurrent_shazam: Max parallel Shazam requests
        max_ffmpeg_workers: Max parallel FFmpeg processes
        progress_callback: Optional callback(completed, total, phase)

    Returns:
        List of SegmentResults for all processed segments
    """
    from libsync.id.shazam.extractor import SegmentExtractor
    from libsync.id.shazam.models import SegmentSpec

    # Create segment specs
    specs = [SegmentSpec(start_ms=s, duration_ms=segment_duration_ms) for s in segments_to_process]

    # Phase 1: Extract segments
    extractor = SegmentExtractor(max_workers=max_ffmpeg_workers)

    def extraction_progress(done: int, total: int) -> None:
        if progress_callback:
            progress_callback(done, total, "extracting")

    segment_paths = await extractor.extract_batch(
        audio_path, temp_dir, specs, progress_callback=extraction_progress
    )

    # Phase 2: Recognize segments
    recognizer = ShazamRecognizer(max_concurrent=max_concurrent_shazam)

    def recognition_progress(done: int, total: int) -> None:
        if progress_callback:
            progress_callback(done, total, "recognizing")

    results = await recognizer.recognize_batch(
        segment_paths,
        audio_hash,
        segment_duration_ms,
        cache=cache,
        progress_callback=recognition_progress,
        cleanup_segments=True,
    )

    # Cleanup extractor
    extractor.shutdown()

    return results
