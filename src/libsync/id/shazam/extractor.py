"""Parallel FFmpeg segment extraction for audio files."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from libsync.id.shazam.models import SegmentSpec

logger = logging.getLogger("libsync")


class SegmentExtractor:
    """Handles parallel FFmpeg segment extraction using ThreadPoolExecutor.

    FFmpeg operations are CPU-bound, so we use a thread pool to parallelize
    across multiple CPU cores. The default of 4 workers is a good balance
    between parallelism and avoiding disk I/O contention.
    """

    def __init__(self, max_workers: int = 4):
        """Initialize the extractor.

        Args:
            max_workers: Maximum number of parallel FFmpeg processes
        """
        self.max_workers = max_workers
        self._executor: ThreadPoolExecutor | None = None

    def _get_executor(self) -> ThreadPoolExecutor:
        """Get or create the thread pool executor."""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._executor

    def _extract_segment_sync(
        self,
        audio_path: str,
        output_path: str,
        start_seconds: float,
        duration_seconds: float,
    ) -> str:
        """Synchronous segment extraction (runs in thread pool).

        Args:
            audio_path: Path to source audio file
            output_path: Path for extracted segment
            start_seconds: Start time in seconds
            duration_seconds: Duration in seconds

        Returns:
            Path to extracted segment

        Raises:
            subprocess.CalledProcessError: If FFmpeg fails
        """
        subprocess.run(
            [
                "ffmpeg",
                "-y",  # Overwrite output
                "-ss",
                str(start_seconds),
                "-t",
                str(duration_seconds),
                "-i",
                audio_path,
                "-acodec",
                "mp3",
                "-ab",
                "128k",
                "-loglevel",
                "error",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
        return output_path

    async def extract_segment(
        self,
        audio_path: str,
        output_path: str,
        start_ms: int,
        duration_ms: int,
    ) -> str:
        """Async wrapper for segment extraction.

        Args:
            audio_path: Path to source audio file
            output_path: Path for extracted segment
            start_ms: Start time in milliseconds
            duration_ms: Duration in milliseconds

        Returns:
            Path to extracted segment
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._get_executor(),
            self._extract_segment_sync,
            audio_path,
            output_path,
            start_ms / 1000,
            duration_ms / 1000,
        )

    async def extract_batch(
        self,
        audio_path: str,
        temp_dir: str,
        segments: list[SegmentSpec],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[tuple[str, int]]:
        """Extract multiple segments in parallel.

        Args:
            audio_path: Path to source audio file
            temp_dir: Directory for temporary segment files
            segments: List of segment specifications
            progress_callback: Optional callback(completed, total) for progress

        Returns:
            List of (segment_path, start_ms) tuples for successfully extracted segments
        """
        os.makedirs(temp_dir, exist_ok=True)

        async def extract_with_tracking(spec: SegmentSpec) -> tuple[str, int] | None:
            segment_path = os.path.join(temp_dir, f"segment_{spec.start_ms}.mp3")
            try:
                await self.extract_segment(
                    audio_path, segment_path, spec.start_ms, spec.duration_ms
                )
                return (segment_path, spec.start_ms)
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg failed for segment at {spec.start_ms}ms: {e.stderr}")
                return None

        tasks = [extract_with_tracking(spec) for spec in segments]
        results: list[tuple[str, int] | None] = []

        # Process with progress tracking
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            result = await coro
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(tasks))

        # Filter out failed extractions
        return [r for r in results if r is not None]

    async def extract_batch_ordered(
        self,
        audio_path: str,
        temp_dir: str,
        segments: list[SegmentSpec],
    ) -> list[tuple[str, int]]:
        """Extract multiple segments in parallel, returning results in order.

        Unlike extract_batch, this preserves the order of the input segments.

        Args:
            audio_path: Path to source audio file
            temp_dir: Directory for temporary segment files
            segments: List of segment specifications

        Returns:
            List of (segment_path, start_ms) tuples in input order
        """
        os.makedirs(temp_dir, exist_ok=True)

        async def extract_single(spec: SegmentSpec) -> tuple[str, int] | None:
            segment_path = os.path.join(temp_dir, f"segment_{spec.start_ms}.mp3")
            try:
                await self.extract_segment(
                    audio_path, segment_path, spec.start_ms, spec.duration_ms
                )
                return (segment_path, spec.start_ms)
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg failed for segment at {spec.start_ms}ms: {e.stderr}")
                return None

        results = await asyncio.gather(*[extract_single(spec) for spec in segments])
        return [r for r in results if r is not None]

    def shutdown(self) -> None:
        """Shutdown the thread pool executor."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.shutdown()
