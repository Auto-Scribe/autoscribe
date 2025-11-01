"""
Script for voice separator w/ color code
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from autoscribe import load_midi
from autoscribe.core.voice_separator import VoiceSeparator, VoiceSeparationConfig
from autoscribe.core.rhythm_quantizer import quantize_piano_roll
import matplotlib.pyplot as plt
import numpy as np


def visualize_voice_separation(original, melody, harmony, bass, max_duration=10.0):
    """
    Visualize voice separation with color-coded voices.

    Args:
        original: Original PianoRoll
        melody: Melody PianoRoll
        harmony: Harmony PianoRoll
        bass: Bass PianoRoll
        max_duration: Maximum time to display
    """
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

    # Define colors for each voice
    colors = {"original": "gray", "melody": "red", "harmony": "blue", "bass": "green"}

    # Plot original
    ax = axes[0]
    for note in original.notes:
        if note.start < max_duration:
            alpha = 0.5 + (note.velocity / 127) * 0.4
            ax.add_patch(
                plt.Rectangle(
                    (note.start, note.pitch),
                    note.duration,
                    0.8,
                    facecolor=colors["original"],
                    edgecolor="black",
                    alpha=alpha,
                    linewidth=0.5,
                )
            )
    ax.set_title("Original (All Notes)", fontweight="bold", fontsize=12)
    ax.set_ylabel("Pitch")
    ax.grid(True, alpha=0.3)

    # Plot melody
    ax = axes[1]
    for note in melody.notes:
        if note.start < max_duration:
            alpha = 0.6 + (note.velocity / 127) * 0.3
            ax.add_patch(
                plt.Rectangle(
                    (note.start, note.pitch),
                    note.duration,
                    0.8,
                    facecolor=colors["melody"],
                    edgecolor="darkred",
                    alpha=alpha,
                    linewidth=0.5,
                )
            )
    ax.set_title("Melody (Top Voice)", fontweight="bold", fontsize=12, color="darkred")
    ax.set_ylabel("Pitch")
    ax.grid(True, alpha=0.3)

    # Plot harmony
    ax = axes[2]
    for note in harmony.notes:
        if note.start < max_duration:
            alpha = 0.5 + (note.velocity / 127) * 0.3
            ax.add_patch(
                plt.Rectangle(
                    (note.start, note.pitch),
                    note.duration,
                    0.8,
                    facecolor=colors["harmony"],
                    edgecolor="darkblue",
                    alpha=alpha,
                    linewidth=0.5,
                )
            )
    ax.set_title(
        "Harmony (Inner Voices)", fontweight="bold", fontsize=12, color="darkblue"
    )
    ax.set_ylabel("Pitch")
    ax.grid(True, alpha=0.3)

    # Plot bass
    ax = axes[3]
    for note in bass.notes:
        if note.start < max_duration:
            alpha = 0.6 + (note.velocity / 127) * 0.3
            ax.add_patch(
                plt.Rectangle(
                    (note.start, note.pitch),
                    note.duration,
                    0.8,
                    facecolor=colors["bass"],
                    edgecolor="darkgreen",
                    alpha=alpha,
                    linewidth=0.5,
                )
            )
    ax.set_title(
        "Bass (Bottom Voice)", fontweight="bold", fontsize=12, color="darkgreen"
    )
    ax.set_ylabel("Pitch")
    ax.set_xlabel("Time (seconds)")
    ax.grid(True, alpha=0.3)

    # Set consistent y-axis range
    pitch_range = original.get_pitch_range()
    for ax in axes:
        ax.set_ylim(pitch_range[0] - 2, pitch_range[1] + 2)
        ax.set_xlim(0, max_duration)

    plt.tight_layout()
    plt.show()