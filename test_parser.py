"""
Test script for MidiParser
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from autoscribe import load_midi, MidiParserError
import matplotlib.pyplot as plt


def visualize_piano_roll(piano_roll, duration=None, title="Piano Roll Visualization"):
    """
    Visualize the piano roll.
    """
    if not piano_roll.notes:
        print("No notes to visualize.")
        return

    max_duration = duration or piano_roll.get_duration()

    fig, ax = plt.subplots(figsize=(14, 7))

    # Draw each note as a rectangle
    for note in piano_roll.notes:
        if note.start < max_duration:
            alpha = 0.3 + (note.velocity / 127) * 0.6
            ax.add_patch(
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

    ax.set_xlim(0, max_duration)
    pitch_range = piano_roll.get_pitch_range()
    ax.set_ylim(pitch_range[0] - 1, pitch_range[1] + 1)

    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel("MIDI Pitch", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3, linestyle="--")

    info_text = (
        f"Tempo: {piano_roll.tempo:.1f} BPM | "
        f"Time Sig: {piano_roll.time_signature[0]}/{piano_roll.time_signature[1]}"
    )
    ax.text(
        0.02,
        0.98,
        info_text,
        transform=ax.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    plt.show()