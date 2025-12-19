#!/usr/bin/env python3
"""
Combined Analysis Visualization Script

Creates a visualization combining:
1. BPM analysis over time
2. Shazam track detections with timestamps

Usage:
    python scripts/combined_analysis_viz.py <audio_file> [--min-matches 2]
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libsync.id.shazam.cache import SegmentCache
from libsync.id.shazam.models import SegmentCacheKey, TrackMatch
from libsync.utils.filepath_utils import get_shazam_segment_cache_path


def load_shazam_results(audio_path: str, min_matches: int = 2) -> list[TrackMatch]:
    """
    Load Shazam results from the cache for an audio file.

    Args:
        audio_path: Path to the audio file
        min_matches: Minimum number of matches to include a track

    Returns:
        List of TrackMatch objects sorted by first_seen_ms
    """
    cache_path = get_shazam_segment_cache_path(audio_path)

    if not Path(cache_path).exists():
        print(f"  No Shazam cache found at: {cache_path}")
        return []

    # Compute audio hash
    audio_hash = SegmentCacheKey.compute_file_hash(audio_path)

    # Load from cache
    cache = SegmentCache(cache_path)
    results = cache.get_matches_only(audio_hash)

    if not results:
        print(f"  No Shazam results found for audio hash: {audio_hash}")
        return []

    # Aggregate into TrackMatch objects
    matches: dict[str, TrackMatch] = {}
    for result in results:
        if result.track_id is None:
            continue

        track_id = result.track_id
        if track_id not in matches:
            matches[track_id] = TrackMatch(
                shazam_id=track_id,
                title=result.title or "",
                artist=result.artist or "",
                first_seen_ms=result.start_ms,
                last_seen_ms=result.start_ms,
                match_timestamps=[result.start_ms],
            )
        else:
            matches[track_id].add_match(result.start_ms)

    # Filter by min_matches
    filtered = [m for m in matches.values() if m.match_count >= min_matches]

    # Sort by first_seen_ms
    filtered.sort(key=lambda m: m.first_seen_ms)

    print(f"  Found {len(filtered)} tracks with >= {min_matches} matches")
    return filtered


def run_bpm_analysis(audio_path: str) -> dict | None:
    """
    Run BPM analysis on the audio file.

    Returns the analysis results dict or None if failed.
    """
    # Import here to avoid circular imports and allow standalone use
    try:
        from scripts.bpm_analysis import analyze_recording
    except ImportError:
        # Try relative import
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "bpm_analysis",
            Path(__file__).parent / "bpm_analysis.py"
        )
        if spec is None or spec.loader is None:
            print("Error: Could not load bpm_analysis module")
            return None
        bpm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bpm_module)
        analyze_recording = bpm_module.analyze_recording

    # Run analysis (suppress plot generation)
    results = analyze_recording(
        audio_path,
        window_size_sec=15.0,
        hop_size_sec=5.0,
        output_plot="skip",  # Don't save individual plot
    )
    return results


def create_combined_visualization(
    audio_path: str,
    bpm_results: dict,
    tracks: list[TrackMatch],
    output_path: str | None = None,
):
    """
    Create a combined visualization with BPM and track detections.
    """
    times = bpm_results["times"]
    filtered_bpms = bpm_results["filtered_bpms"]
    corrected_bpms = bpm_results["corrected_bpms"]
    confidences = bpm_results["confidences"]
    has_music = bpm_results["has_music"]
    is_outlier = bpm_results["is_outlier"]
    stats = bpm_results["stats"]

    # Convert times to minutes
    times_min = times / 60

    # Create figure with 2 subplots
    fig, axes = plt.subplots(2, 1, figsize=(18, 10), height_ratios=[3, 1], sharex=True)

    # === Plot 1: BPM with track annotations ===
    ax1 = axes[0]

    # Plot BPM data
    valid_mask = ~is_outlier & has_music & (corrected_bpms > 0)
    outlier_mask = is_outlier & (corrected_bpms > 0)

    # Outliers (faded)
    ax1.scatter(
        times_min[outlier_mask],
        corrected_bpms[outlier_mask],
        c="lightgray",
        alpha=0.3,
        s=10,
        marker="x",
        zorder=1,
    )

    # Valid measurements
    ax1.scatter(
        times_min[valid_mask],
        corrected_bpms[valid_mask],
        c="steelblue",
        alpha=0.6,
        s=20,
        zorder=2,
    )

    # Smoothed trend line
    ax1.plot(
        times_min[has_music],
        filtered_bpms[has_music],
        color="darkblue",
        linewidth=2.5,
        alpha=0.9,
        label=f"BPM Trend (Median: {stats.get('median_bpm', 0):.1f})",
        zorder=3,
    )

    # Add track annotations
    if tracks:
        # Calculate y positions for track labels to avoid overlap
        # Use alternating heights
        y_positions = []
        base_y = 170  # Top of plot area
        y_step = 8
        prev_x = -float("inf")
        current_y_level = 0

        for track in tracks:
            track_time_min = track.first_seen_ms / 60000

            # Reset y level if far enough from previous track
            if track_time_min - prev_x > 3:  # More than 3 minutes gap
                current_y_level = 0
            else:
                current_y_level = (current_y_level + 1) % 4  # Cycle through 4 levels

            y_pos = base_y - current_y_level * y_step
            y_positions.append(y_pos)
            prev_x = track_time_min

        # Plot track markers and labels
        colors = plt.cm.tab20(np.linspace(0, 1, max(len(tracks), 1)))

        for i, track in enumerate(tracks):
            track_time_min = track.first_seen_ms / 60000
            track_end_min = track.last_seen_ms / 60000
            y_pos = y_positions[i]
            color = colors[i % len(colors)]

            # Vertical line at track start
            ax1.axvline(
                x=track_time_min,
                color=color,
                linestyle="-",
                alpha=0.5,
                linewidth=1,
                zorder=4,
            )

            # Shaded region for track duration
            if track_end_min > track_time_min:
                ax1.axvspan(
                    track_time_min,
                    track_end_min,
                    alpha=0.1,
                    color=color,
                    zorder=0,
                )

            # Track label
            label = f"{track.artist[:20]} - {track.title[:25]}"
            if len(track.artist) > 20 or len(track.title) > 25:
                label += "..."
            label += f" [{track.match_count}x]"

            ax1.annotate(
                label,
                xy=(track_time_min, y_pos),
                fontsize=7,
                color=color,
                fontweight="bold",
                rotation=0,
                ha="left",
                va="bottom",
                zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor=color, linewidth=0.5),
            )

    # Styling for BPM plot
    ax1.set_ylabel("BPM", fontsize=12)
    ax1.set_title(
        f"BPM Analysis with Track Detections - {Path(audio_path).name}",
        fontsize=14,
        fontweight="bold",
    )
    ax1.legend(loc="lower right", fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(80, 180)

    # Add secondary info
    info_text = f"Tracks: {len(tracks)} | Valid BPM: {stats.get('valid_percentage', 0):.0f}%"
    ax1.text(
        0.02, 0.02, info_text,
        transform=ax1.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    # === Plot 2: Track timeline ===
    ax2 = axes[1]

    if tracks:
        # Create a timeline view of tracks
        for i, track in enumerate(tracks):
            track_start_min = track.first_seen_ms / 60000
            track_end_min = track.last_seen_ms / 60000
            duration_min = max(track_end_min - track_start_min, 0.5)  # Minimum width for visibility

            color = colors[i % len(colors)]

            # Draw track bar
            ax2.barh(
                y=0,
                width=duration_min,
                left=track_start_min,
                height=0.8,
                color=color,
                alpha=0.7,
                edgecolor="black",
                linewidth=0.5,
            )

            # Add match count label
            ax2.text(
                track_start_min + duration_min / 2,
                0,
                f"{track.match_count}",
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                color="white",
            )

    # Styling for timeline
    ax2.set_xlabel("Time (minutes)", fontsize=12)
    ax2.set_ylabel("")
    ax2.set_title("Track Detection Timeline", fontsize=11)
    ax2.set_ylim(-0.6, 0.6)
    ax2.set_yticks([])
    ax2.grid(True, axis="x", alpha=0.3)

    # Set x-axis limits based on audio duration
    max_time_min = times_min[-1] if len(times_min) > 0 else 120
    ax2.set_xlim(0, max_time_min + 1)
    ax1.set_xlim(0, max_time_min + 1)

    plt.tight_layout()

    # Save or show
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"\nSaved combined visualization to: {output_path}")
    else:
        plt.show()

    return fig


def main():
    parser = argparse.ArgumentParser(
        description="Create combined BPM + Shazam visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/combined_analysis_viz.py recording.m4a
    python scripts/combined_analysis_viz.py recording.mp3 --min-matches 3
    python scripts/combined_analysis_viz.py recording.wav -o combined.png
        """,
    )
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument(
        "--min-matches",
        type=int,
        default=2,
        help="Minimum Shazam matches to include a track (default: 2)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output path for plot (default: <input>_combined_analysis.png)",
    )
    parser.add_argument(
        "--skip-bpm",
        action="store_true",
        help="Skip BPM analysis if already done (not implemented yet)",
    )

    args = parser.parse_args()

    audio_path = args.audio_file
    if not Path(audio_path).exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)

    # Resolve to absolute path for cache lookup
    audio_path = str(Path(audio_path).resolve())

    print("\n" + "=" * 60)
    print("COMBINED ANALYSIS VISUALIZATION")
    print("=" * 60)
    print(f"Audio file: {audio_path}")

    # Load Shazam results
    print("\nLoading Shazam results...")
    tracks = load_shazam_results(audio_path, min_matches=args.min_matches)

    # Run BPM analysis
    print("\nRunning BPM analysis...")
    bpm_results = run_bpm_analysis(audio_path)

    if bpm_results is None:
        print("Error: BPM analysis failed")
        sys.exit(1)

    # Create output path
    if args.output is None:
        input_path = Path(audio_path)
        output_path = str(input_path.parent / f"{input_path.stem}_combined_analysis.png")
    else:
        output_path = args.output

    # Create visualization
    print("\nCreating combined visualization...")
    create_combined_visualization(audio_path, bpm_results, tracks, output_path)

    # Print track summary
    if tracks:
        print("\n" + "-" * 60)
        print("DETECTED TRACKS")
        print("-" * 60)
        for track in tracks:
            timestamp_min = track.first_seen_ms / 60000
            mins = int(timestamp_min)
            secs = int((timestamp_min - mins) * 60)
            print(f"  {mins:3d}:{secs:02d}  [{track.match_count:2d}x]  {track.artist} - {track.title}")
        print("-" * 60)
        print(f"Total: {len(tracks)} tracks")

    print("\nDone!")


if __name__ == "__main__":
    main()
