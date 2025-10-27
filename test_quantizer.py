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