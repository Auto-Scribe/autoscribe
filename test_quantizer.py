import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from autoscribe import load_midi
from autoscribe.core.rhythm_quantizer import (
    RhythmQuantizer,
    QuantizationConfig,
    quantize_piano_roll,
)
import matplotlib.pyplot as plt


def visualize_quantization_comparison(
    original: "PianoRoll", quantized: "PianoRoll", max_duration: float = 5.0
):
    """
    Show before/after quantization.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Original
    for note in original.notes:
        if note.start < max_duration:
            alpha = 0.3 + (note.velocity / 127) * 0.6
            ax1.add_patch(
                plt.Rectangle(
                    (note.start, note.pitch),
                    min(note.duration, max_duration - note.start),
                    0.8,
                    facecolor="indianred",
                    edgecolor="black",
                    alpha=alpha,
                    linewidth=0.5,
                )
            )

    # Quantized
    for note in quantized.notes:
        if note.start < max_duration:
            alpha = 0.3 + (note.velocity / 127) * 0.6
            ax2.add_patch(
                plt.Rectangle(
                    (note.start, note.pitch),
                    min(note.duration, max_duration - note.start),
                    0.8,
                    facecolor="steelblue",
                    edgecolor="black",
                    alpha=alpha,
                    linewidth=0.5,
                )
            )

    # Axes setup
    pitch_range = original.get_pitch_range()
    for ax in [ax1, ax2]:
        ax.set_xlim(0, max_duration)
        ax.set_ylim(pitch_range[0] - 1, pitch_range[1] + 1)
        ax.set_ylabel("MIDI Pitch", fontsize=12)
        ax.grid(True, alpha=0.3, linestyle="--")

    ax1.set_title("Original (Unquantized)", fontsize=14, fontweight="bold")
    ax2.set_title("Quantized", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Time (seconds)", fontsize=12)

    plt.tight_layout()
    plt.show()


def show_timing_shifts(original: "PianoRoll", quantized: "PianoRoll"):
    """
    Print timing shifts for the first 10 notes.
    """
    print("\n--- Timing Shifts (first 10 notes) ---")
    print(f"{'Original Start':<15} {'Quantized Start':<15} {'Shift (ms)':<12} {'Pitch':<8}")
    print("-" * 60)

    for orig_note, quant_note in zip(original.notes[:10], quantized.notes[:10]):
        shift_ms = (quant_note.start - orig_note.start) * 1000
        print(
            f"{orig_note.start:<15.4f} {quant_note.start:<15.4f} "
            f"{shift_ms:>+11.2f} {orig_note.midi_note_name:<8}"
        )

def analyze_and_quantize(midi_path: str, grid_resolution: str = "16th", strength: float = 1.0):
    """
    Load, analyze, quantize, and compare a MIDI file.
    """
    print(f"\n{'='*70}")
    print("Testing Rhythm Quantization")
    print(f"{'='*70}")
    print(f"File: {Path(midi_path).name}")
    print(f"Grid Resolution: {grid_resolution}")
    print(f"Strength: {strength}")

    # Load MIDI
    print("\n--- Loading Original MIDI ---")
    original = load_midi(midi_path)

    # Analyze before quantization
    config = QuantizationConfig(grid_resolution=grid_resolution, strength=strength)
    quantizer = RhythmQuantizer(config)

    print("\n--- Timing Analysis (Before Quantization) ---")
    timing_stats = quantizer.analyze_timing_distribution(original)
    print(f"Mean deviation from grid: {timing_stats['mean_deviation']*1000:.2f} ms")
    print(f"Max deviation from grid: {timing_stats['max_deviation']*1000:.2f} ms")
    print(f"Std deviation: {timing_stats['std_deviation']*1000:.2f} ms")
    print(f"Notes already on grid: {timing_stats['percent_on_grid']:.1f}%")
    print(f"Grid spacing: {timing_stats['grid_duration']*1000:.1f} ms")

    # Quantize
    print("\n--- Quantizing ---")
    quantized = quantizer.quantize(original)
    print(f"Quantized {len(quantized.notes)} notes")

    # Show timing shifts
    show_timing_shifts(original, quantized)

    # Analyze after quantization
    print("\n--- Timing Analysis (After Quantization) ---")
    post_stats = quantizer.analyze_timing_distribution(quantized)
    print(f"Mean deviation from grid: {post_stats['mean_deviation']*1000:.2f} ms")
    print(f"Notes on grid: {post_stats['percent_on_grid']:.1f}%")

    # Visualize
    print("\n--- Generating Visualization ---")
    visualize_quantization_comparison(
        original, quantized, max_duration=min(10, original.get_duration())
    )

    return original, quantized


def test_different_resolutions(midi_path: str):
    """
    Compare several grid resolutions.
    """
    print(f"\n{'='*70}")
    print("Testing Different Grid Resolutions")
    print(f"{'='*70}")

    original = load_midi(midi_path)
    resolutions = ["8th", "16th", "32nd"]

    fig, axes = plt.subplots(len(resolutions) + 1, 1, figsize=(14, 12), sharex=True)
    max_duration = min(5.0, original.get_duration())

    # Original
    ax = axes[0]
    for note in original.notes:
        if note.start < max_duration:
            ax.add_patch(
                plt.Rectangle(
                    (note.start, note.pitch),
                    note.duration,
                    0.8,
                    facecolor="gray",
                    edgecolor="black",
                    alpha=0.6,
                )
            )
    ax.set_title("Original", fontweight="bold")
    ax.set_ylabel("Pitch")
    ax.grid(True, alpha=0.3)

    # Each resolution
    for idx, resolution in enumerate(resolutions, 1):
        quantized = quantize_piano_roll(original, grid_resolution=resolution)
        ax = axes[idx]
        for note in quantized.notes:
            if note.start < max_duration:
                ax.add_patch(
                    plt.Rectangle(
                        (note.start, note.pitch),
                        note.duration,
                        0.8,
                        facecolor="steelblue",
                        edgecolor="black",
                        alpha=0.6,
                    )
                )
        ax.set_title(f"Quantized to {resolution} notes", fontweight="bold")
        ax.set_ylabel("Pitch")
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Time (seconds)")
    plt.tight_layout()
    plt.show()