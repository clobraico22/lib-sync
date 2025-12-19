#!/usr/bin/env python3
"""
BPM Analysis Script

Analyzes BPM throughout an audio recording using windowed tempo detection.
Includes robust heuristics to handle noise, bad measurements, and sections without music.
Outputs a visualization of BPM over time.

Usage:
    python scripts/bpm_analysis.py <audio_file> [--window-size 15] [--hop-size 5]
"""

import argparse
import sys
from pathlib import Path

import librosa
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import median_filter, uniform_filter1d


def load_audio(filepath: str, sr: int = 22050) -> tuple[np.ndarray, int]:
    """Load audio file and return samples and sample rate."""
    print(f"Loading audio file: {filepath}")
    y, sr = librosa.load(filepath, sr=sr, mono=True)
    duration = len(y) / sr
    print(f"  Duration: {duration / 60:.1f} minutes ({duration:.1f} seconds)")
    print(f"  Sample rate: {sr} Hz")
    return y, sr


def estimate_tempo_tempogram(
    y: np.ndarray,
    sr: int,
    min_bpm: float = 80.0,
    max_bpm: float = 180.0,
) -> tuple[float, float]:
    """
    Estimate tempo using tempogram analysis - more robust than beat_track.

    Returns:
        tempo: Estimated BPM
        strength: Confidence/strength of the tempo estimate (0-1)
    """
    # Compute onset envelope
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    # Compute tempogram
    tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)

    # Get tempo frequencies
    tempo_freqs = librosa.tempo_frequencies(tempogram.shape[0], sr=sr)

    # Aggregate tempogram over time
    tempo_strength = np.mean(tempogram, axis=1)

    # Find valid BPM range
    valid_mask = (tempo_freqs >= min_bpm) & (tempo_freqs <= max_bpm)

    if not np.any(valid_mask):
        return 0.0, 0.0

    valid_tempos = tempo_freqs[valid_mask]
    valid_strengths = tempo_strength[valid_mask]

    # Find the tempo with maximum strength
    best_idx = np.argmax(valid_strengths)
    best_tempo = valid_tempos[best_idx]

    # Normalize strength to 0-1
    max_strength = valid_strengths[best_idx]
    total_strength = np.sum(valid_strengths) + 1e-6
    confidence = max_strength / total_strength * len(valid_strengths) / 10  # Normalize
    confidence = np.clip(confidence, 0, 1)

    return float(best_tempo), float(confidence)


def estimate_tempo_autocorr(
    y: np.ndarray,
    sr: int,
    min_bpm: float = 80.0,
    max_bpm: float = 180.0,
) -> tuple[float, float]:
    """
    Estimate tempo using onset autocorrelation - good for electronic music.

    Returns:
        tempo: Estimated BPM
        strength: Confidence of the estimate (0-1)
    """
    # Compute onset envelope
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    # Use librosa's tempo estimation with prior
    tempo = librosa.feature.tempo(
        onset_envelope=onset_env,
        sr=sr,
        aggregate=None,  # Get per-frame estimates
        prior=None,
    )

    if len(tempo) == 0:
        return 0.0, 0.0

    # Filter to valid range
    valid_tempos = tempo[(tempo >= min_bpm) & (tempo <= max_bpm)]

    if len(valid_tempos) == 0:
        # Try octave correction
        half_tempos = tempo[(tempo * 2 >= min_bpm) & (tempo * 2 <= max_bpm)]
        double_tempos = tempo[(tempo / 2 >= min_bpm) & (tempo / 2 <= max_bpm)]

        if len(half_tempos) > len(double_tempos):
            valid_tempos = half_tempos * 2
        elif len(double_tempos) > 0:
            valid_tempos = double_tempos / 2
        else:
            return 0.0, 0.0

    # Use median for robustness
    estimated_tempo = float(np.median(valid_tempos))

    # Confidence based on consistency of estimates
    if len(valid_tempos) > 1:
        consistency = 1.0 - np.std(valid_tempos) / (np.mean(valid_tempos) + 1e-6)
        confidence = np.clip(consistency, 0, 1)
    else:
        confidence = 0.5

    return estimated_tempo, confidence


def estimate_tempo_combined(
    y: np.ndarray,
    sr: int,
    min_bpm: float = 80.0,
    max_bpm: float = 180.0,
) -> tuple[float, float, dict]:
    """
    Combine multiple tempo estimation methods for robustness.

    Returns:
        tempo: Best estimated BPM
        confidence: Combined confidence score
        details: Dictionary with individual method results
    """
    # Method 1: Tempogram
    tempo_tg, conf_tg = estimate_tempo_tempogram(y, sr, min_bpm, max_bpm)

    # Method 2: Autocorrelation-based
    tempo_ac, conf_ac = estimate_tempo_autocorr(y, sr, min_bpm, max_bpm)

    # Method 3: Standard beat_track as fallback
    try:
        tempo_bt, _ = librosa.beat.beat_track(y=y, sr=sr)
        if isinstance(tempo_bt, np.ndarray):
            tempo_bt = float(tempo_bt[0]) if len(tempo_bt) > 0 else 0.0
        tempo_bt = float(tempo_bt)

        # Apply octave correction if needed
        if tempo_bt < min_bpm and tempo_bt * 2 <= max_bpm:
            tempo_bt *= 2
        elif tempo_bt > max_bpm and tempo_bt / 2 >= min_bpm:
            tempo_bt /= 2
        elif tempo_bt < min_bpm or tempo_bt > max_bpm:
            tempo_bt = 0.0
        conf_bt = 0.5 if min_bpm <= tempo_bt <= max_bpm else 0.0
    except Exception:
        tempo_bt, conf_bt = 0.0, 0.0

    details = {
        "tempogram": (tempo_tg, conf_tg),
        "autocorr": (tempo_ac, conf_ac),
        "beat_track": (tempo_bt, conf_bt),
    }

    # Combine estimates - weight by confidence
    tempos = [tempo_tg, tempo_ac, tempo_bt]
    confs = [conf_tg, conf_ac, conf_bt]

    valid_tempos = [(t, c) for t, c in zip(tempos, confs) if t > 0 and c > 0]

    if not valid_tempos:
        return 0.0, 0.0, details

    # Check if estimates agree (within 5 BPM or octave-related)
    def are_similar(t1: float, t2: float, threshold: float = 5.0) -> bool:
        if abs(t1 - t2) < threshold:
            return True
        # Check octave relationship
        if abs(t1 - t2 * 2) < threshold or abs(t1 * 2 - t2) < threshold:
            return True
        return False

    # If tempogram and autocorr agree, use their weighted average
    if tempo_tg > 0 and tempo_ac > 0 and are_similar(tempo_tg, tempo_ac):
        total_conf = conf_tg + conf_ac
        best_tempo = (tempo_tg * conf_tg + tempo_ac * conf_ac) / total_conf
        best_conf = min(1.0, (conf_tg + conf_ac) / 1.5)  # Boost confidence for agreement
    else:
        # Take the estimate with highest confidence
        best_tempo, best_conf = max(valid_tempos, key=lambda x: x[1])

    return best_tempo, best_conf, details


def compute_window_energy(y: np.ndarray, sr: int) -> float:
    """Compute RMS energy for a window."""
    rms = librosa.feature.rms(y=y)[0]
    return float(np.mean(rms))


def analyze_bpm_windowed(
    y: np.ndarray,
    sr: int,
    window_size_sec: float = 15.0,
    hop_size_sec: float = 5.0,
    min_bpm: float = 80.0,
    max_bpm: float = 180.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Analyze BPM in overlapping windows throughout the recording.

    Returns:
        times: Center time of each window (seconds)
        bpms: Raw BPM estimate for each window
        confidences: Confidence score for each estimate (0-1)
        energies: RMS energy for each window (for music detection)
    """
    window_samples = int(window_size_sec * sr)
    hop_samples = int(hop_size_sec * sr)

    times = []
    bpms = []
    confidences = []
    energies = []

    start = 0
    window_count = 0
    total_windows = (len(y) - window_samples) // hop_samples + 1

    print(f"  Total windows to analyze: {total_windows}")

    while start + window_samples <= len(y):
        window = y[start : start + window_samples]
        center_time = (start + window_samples / 2) / sr

        # Compute energy
        energy = compute_window_energy(window, sr)

        # Get tempo estimate using combined method
        tempo, confidence, _ = estimate_tempo_combined(window, sr, min_bpm, max_bpm)

        times.append(center_time)
        bpms.append(tempo)
        confidences.append(confidence)
        energies.append(energy)

        start += hop_samples
        window_count += 1

        if window_count % 50 == 0:
            progress = window_count / total_windows * 100
            print(f"  Progress: {progress:.1f}% ({center_time / 60:.1f} min)")

    return np.array(times), np.array(bpms), np.array(confidences), np.array(energies)


def detect_music_regions(
    energies: np.ndarray,
    threshold_percentile: float = 25,
) -> np.ndarray:
    """
    Detect which windows contain actual music vs silence/noise.

    Returns:
        has_music: Boolean mask where True = music present
    """
    if len(energies) == 0:
        return np.array([], dtype=bool)

    # Use percentile-based threshold
    threshold = np.percentile(energies, threshold_percentile)
    has_music = energies > threshold

    # Apply smoothing to avoid flickering
    smoothed = uniform_filter1d(has_music.astype(float), size=3)
    has_music = smoothed > 0.5

    return has_music


def correct_octave_errors(
    bpms: np.ndarray,
    confidences: np.ndarray,
    has_music: np.ndarray,
    target_range: tuple[float, float] = (115, 145),
) -> np.ndarray:
    """
    Correct octave errors by normalizing to expected BPM range.

    For electronic music, BPM is typically 120-140.
    Values at half or double this are likely octave errors.
    """
    corrected = bpms.copy()

    # First, estimate the "true" BPM range from high-confidence music regions
    music_mask = has_music & (confidences > 0.3) & (bpms > 0)

    if np.sum(music_mask) < 5:
        # Not enough data, use target range
        target_bpm = np.mean(target_range)
    else:
        # Use median of confident estimates
        confident_bpms = bpms[music_mask]
        target_bpm = np.median(confident_bpms)

        # If median is outside typical DJ range, it might be an octave error itself
        if target_bpm < 90:
            target_bpm *= 2
        elif target_bpm > 160:
            target_bpm /= 2

    # Correct each BPM value
    for i in range(len(corrected)):
        if corrected[i] <= 0:
            continue

        bpm = corrected[i]

        # Check if half or double is closer to target
        options = [bpm, bpm * 2, bpm / 2]
        distances = [abs(opt - target_bpm) for opt in options]
        best_idx = np.argmin(distances)

        # Only correct if it's a clear octave error
        if best_idx != 0 and distances[best_idx] < distances[0] * 0.5:
            corrected[i] = options[best_idx]

    return corrected


def filter_outliers_robust(
    bpms: np.ndarray,
    confidences: np.ndarray,
    has_music: np.ndarray,
    deviation_threshold: float = 8.0,
    confidence_threshold: float = 0.2,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Robust outlier filtering using multiple criteria.

    Args:
        bpms: BPM values (already octave-corrected)
        confidences: Confidence scores
        has_music: Music detection mask
        deviation_threshold: Max allowed deviation from local trend (BPM)
        confidence_threshold: Minimum confidence to trust a measurement

    Returns:
        filtered_bpms: Cleaned BPM values
        is_outlier: Boolean mask of outliers
    """
    n = len(bpms)
    is_outlier = np.zeros(n, dtype=bool)
    filtered_bpms = bpms.copy()

    if n < 5:
        return filtered_bpms, is_outlier

    # Step 1: Mark low-confidence and non-music regions
    is_outlier |= confidences < confidence_threshold
    is_outlier |= ~has_music
    is_outlier |= bpms <= 0

    # Step 2: Compute global statistics from reliable measurements
    reliable_mask = ~is_outlier
    if np.sum(reliable_mask) < 3:
        return filtered_bpms, is_outlier

    reliable_bpms = bpms[reliable_mask]
    global_median = np.median(reliable_bpms)
    global_std = np.std(reliable_bpms)

    # Step 3: Mark values far from global median as outliers
    # Use a generous threshold (3 std or 20 BPM, whichever is larger)
    global_threshold = max(3 * global_std, 20.0)
    is_outlier |= np.abs(bpms - global_median) > global_threshold

    # Step 4: Local median filtering for remaining outliers
    # Use larger window for more stable reference
    window_size = min(21, n // 5 * 2 + 1)  # Odd number, at least 5
    if window_size >= 5:
        local_median = median_filter(bpms, size=window_size, mode="nearest")
        local_deviation = np.abs(bpms - local_median)
        is_outlier |= (local_deviation > deviation_threshold) & reliable_mask

    # Step 5: Replace outliers with interpolated values
    good_indices = np.where(~is_outlier)[0]

    if len(good_indices) >= 2:
        # Interpolate outliers from good values
        for i in range(n):
            if is_outlier[i]:
                # Find nearest good values
                left_idx = good_indices[good_indices < i]
                right_idx = good_indices[good_indices > i]

                if len(left_idx) > 0 and len(right_idx) > 0:
                    # Interpolate
                    left = left_idx[-1]
                    right = right_idx[0]
                    weight = (i - left) / (right - left)
                    filtered_bpms[i] = bpms[left] * (1 - weight) + bpms[right] * weight
                elif len(left_idx) > 0:
                    filtered_bpms[i] = bpms[left_idx[-1]]
                elif len(right_idx) > 0:
                    filtered_bpms[i] = bpms[right_idx[0]]
                else:
                    filtered_bpms[i] = global_median

    # Step 6: Final smoothing pass
    filtered_bpms = uniform_filter1d(filtered_bpms, size=3)

    return filtered_bpms, is_outlier


def compute_statistics(
    bpms: np.ndarray,
    confidences: np.ndarray,
    has_music: np.ndarray,
    is_outlier: np.ndarray,
) -> dict:
    """Compute summary statistics for BPM analysis."""
    # Only consider non-outlier windows with music
    valid_mask = has_music & ~is_outlier & (bpms > 0)
    valid_bpms = bpms[valid_mask]
    valid_confidences = confidences[valid_mask]

    if len(valid_bpms) == 0:
        return {"error": "No valid BPM measurements"}

    # Weight by confidence for mean
    weights = valid_confidences + 0.1
    weighted_mean = np.average(valid_bpms, weights=weights)

    stats = {
        "mean_bpm": float(np.mean(valid_bpms)),
        "weighted_mean_bpm": float(weighted_mean),
        "median_bpm": float(np.median(valid_bpms)),
        "std_bpm": float(np.std(valid_bpms)),
        "min_bpm": float(np.min(valid_bpms)),
        "max_bpm": float(np.max(valid_bpms)),
        "mean_confidence": float(np.mean(valid_confidences)),
        "music_percentage": float(np.mean(has_music) * 100),
        "valid_percentage": float(np.mean(valid_mask) * 100),
        "outlier_percentage": float(np.mean(is_outlier) * 100),
        "num_windows": int(len(bpms)),
        "num_valid_windows": int(np.sum(valid_mask)),
    }

    return stats


def plot_bpm_analysis(
    times: np.ndarray,
    raw_bpms: np.ndarray,
    filtered_bpms: np.ndarray,
    confidences: np.ndarray,
    has_music: np.ndarray,
    is_outlier: np.ndarray,
    stats: dict,
    output_path: str | None = None,
):
    """Create visualization of BPM analysis."""
    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)

    # Convert times to minutes
    times_min = times / 60

    # Masks for different point types
    valid_mask = ~is_outlier & has_music & (raw_bpms > 0)
    outlier_mask = is_outlier & (raw_bpms > 0)

    # Plot 1: BPM over time
    ax1 = axes[0]

    # Plot outliers (red X)
    ax1.scatter(
        times_min[outlier_mask],
        raw_bpms[outlier_mask],
        c="red",
        alpha=0.4,
        s=15,
        marker="x",
        label=f"Excluded ({np.sum(outlier_mask)})",
        zorder=1,
    )

    # Plot valid raw measurements (blue dots)
    ax1.scatter(
        times_min[valid_mask],
        raw_bpms[valid_mask],
        c="blue",
        alpha=0.6,
        s=25,
        label=f"Valid measurements ({np.sum(valid_mask)})",
        zorder=2,
    )

    # Plot filtered/smoothed line (green)
    ax1.plot(
        times_min[has_music],
        filtered_bpms[has_music],
        "g-",
        linewidth=2,
        alpha=0.8,
        label="Smoothed trend",
        zorder=3,
    )

    # Reference lines
    if "median_bpm" in stats:
        ax1.axhline(
            y=stats["median_bpm"],
            color="orange",
            linestyle="--",
            alpha=0.7,
            linewidth=1.5,
            label=f'Median: {stats["median_bpm"]:.1f}',
        )

    ax1.set_ylabel("BPM", fontsize=11)
    ax1.set_title("BPM Analysis Over Time", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(80, 180)

    # Plot 2: Confidence
    ax2 = axes[1]
    colors = np.where(has_music, "green", "lightgray")
    bar_width = (times_min[1] - times_min[0]) * 0.9 if len(times_min) > 1 else 0.05
    ax2.bar(times_min, confidences, width=bar_width, color=colors, alpha=0.7, edgecolor="none")
    ax2.axhline(y=0.2, color="red", linestyle="--", alpha=0.5, linewidth=1, label="Min confidence threshold")
    ax2.set_ylabel("Confidence", fontsize=11)
    ax2.set_title("Detection Confidence (green = music, gray = silence)", fontsize=12)
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1)

    # Plot 3: Music detection
    ax3 = axes[2]
    ax3.fill_between(times_min, has_music.astype(float), alpha=0.5, color="green", step="mid")
    ax3.set_ylabel("Music Present", fontsize=11)
    ax3.set_xlabel("Time (minutes)", fontsize=11)
    ax3.set_title("Music vs Silence Detection", fontsize=12)
    ax3.set_ylim(-0.1, 1.1)
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(["No", "Yes"])
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    # Summary text
    if "error" not in stats:
        summary_text = (
            f"Summary Statistics:\n"
            f"  Median BPM: {stats['median_bpm']:.1f}\n"
            f"  Mean BPM: {stats['mean_bpm']:.1f} (weighted: {stats['weighted_mean_bpm']:.1f})\n"
            f"  Std Dev: {stats['std_bpm']:.1f}\n"
            f"  Range: {stats['min_bpm']:.1f} - {stats['max_bpm']:.1f}\n"
            f"  Valid: {stats['valid_percentage']:.1f}% | Music: {stats['music_percentage']:.1f}%"
        )
        fig.text(0.02, 0.02, summary_text, fontsize=9, family="monospace", verticalalignment="bottom")

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"  Saved plot to: {output_path}")
    else:
        plt.show()

    return fig


def analyze_recording(
    filepath: str,
    window_size_sec: float = 15.0,
    hop_size_sec: float = 5.0,
    output_plot: str | None = None,
    min_bpm: float = 80.0,
    max_bpm: float = 180.0,
) -> dict:
    """
    Main function to analyze BPM throughout a recording.
    """
    print("\n" + "=" * 60)
    print("BPM ANALYSIS (Robust)")
    print("=" * 60)

    # Load audio
    y, sr = load_audio(filepath)

    # Analyze BPM in windows
    print(f"\nAnalyzing BPM in {window_size_sec}s windows with {hop_size_sec}s hop...")
    print(f"  BPM range: {min_bpm} - {max_bpm}")
    times, raw_bpms, confidences, energies = analyze_bpm_windowed(
        y, sr, window_size_sec, hop_size_sec, min_bpm, max_bpm
    )

    # Detect music regions
    print("\nDetecting music regions...")
    has_music = detect_music_regions(energies)
    print(f"  Music detected in {np.sum(has_music)}/{len(has_music)} windows ({np.mean(has_music)*100:.1f}%)")

    # Correct octave errors
    print("\nCorrecting octave errors...")
    corrected_bpms = correct_octave_errors(raw_bpms, confidences, has_music)
    octave_corrections = np.sum(np.abs(corrected_bpms - raw_bpms) > 10)
    print(f"  Corrected {octave_corrections} octave errors")

    # Filter outliers
    print("\nFiltering outliers...")
    filtered_bpms, is_outlier = filter_outliers_robust(corrected_bpms, confidences, has_music)
    print(f"  Identified {np.sum(is_outlier)} outliers ({np.mean(is_outlier)*100:.1f}%)")

    # Compute statistics
    stats = compute_statistics(filtered_bpms, confidences, has_music, is_outlier)

    # Print results
    print("\n" + "-" * 40)
    print("RESULTS")
    print("-" * 40)
    if "error" in stats:
        print(f"  Error: {stats['error']}")
    else:
        print(f"  Median BPM:        {stats['median_bpm']:.1f}")
        print(f"  Weighted Mean BPM: {stats['weighted_mean_bpm']:.1f}")
        print(f"  Mean BPM:          {stats['mean_bpm']:.1f}")
        print(f"  Std Dev:           {stats['std_bpm']:.1f}")
        print(f"  Range:             {stats['min_bpm']:.1f} - {stats['max_bpm']:.1f}")
        print(f"  Mean Confidence:   {stats['mean_confidence']:.2f}")
        print(f"  Music Coverage:    {stats['music_percentage']:.1f}%")
        print(f"  Valid Windows:     {stats['valid_percentage']:.1f}%")

    # Generate plot (skip if output_plot is explicitly set to skip)
    if output_plot != "skip":
        if output_plot is None:
            input_path = Path(filepath)
            output_plot = str(input_path.parent / f"{input_path.stem}_bpm_analysis.png")

        print(f"\nGenerating visualization...")
        plot_bpm_analysis(
            times, corrected_bpms, filtered_bpms, confidences, has_music, is_outlier, stats, output_plot
        )

    return {
        "times": times,
        "raw_bpms": raw_bpms,
        "corrected_bpms": corrected_bpms,
        "filtered_bpms": filtered_bpms,
        "confidences": confidences,
        "has_music": has_music,
        "is_outlier": is_outlier,
        "stats": stats,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze BPM throughout an audio recording (robust version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/bpm_analysis.py recording.mp3
    python scripts/bpm_analysis.py recording.m4a --window-size 20 --hop-size 10
    python scripts/bpm_analysis.py recording.wav -o plot.png --min-bpm 100 --max-bpm 150
        """,
    )
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument(
        "--window-size",
        type=float,
        default=15.0,
        help="Analysis window size in seconds (default: 15)",
    )
    parser.add_argument(
        "--hop-size",
        type=float,
        default=5.0,
        help="Hop between windows in seconds (default: 5)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output path for plot (default: <input>_bpm_analysis.png)",
    )
    parser.add_argument(
        "--min-bpm",
        type=float,
        default=80.0,
        help="Minimum expected BPM (default: 80)",
    )
    parser.add_argument(
        "--max-bpm",
        type=float,
        default=180.0,
        help="Maximum expected BPM (default: 180)",
    )

    args = parser.parse_args()

    if not Path(args.audio_file).exists():
        print(f"Error: File not found: {args.audio_file}")
        sys.exit(1)

    analyze_recording(
        args.audio_file,
        window_size_sec=args.window_size,
        hop_size_sec=args.hop_size,
        output_plot=args.output,
        min_bpm=args.min_bpm,
        max_bpm=args.max_bpm,
    )

    print("\nDone!")


if __name__ == "__main__":
    main()
