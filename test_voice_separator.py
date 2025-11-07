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

def visualize_combined_voices(melody, harmony, bass, max_duration=10.0):
    """
    Show all voices on one plot with different colors.
    
    Args:
        melody: Melody PianoRoll
        harmony: Harmony PianoRoll
        bass: Bass PianoRoll
        max_duration: Maximum time to display
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot all voices with different colors
    for note in melody.notes:
        if note.start < max_duration:
            ax.add_patch(plt.Rectangle(
                (note.start, note.pitch), note.duration, 0.8,
                facecolor='red', edgecolor='darkred',
                alpha=0.7, linewidth=0.5, label='Melody' if note == melody.notes[0] else ''
            ))
    
    for note in harmony.notes:
        if note.start < max_duration:
            ax.add_patch(plt.Rectangle(
                (note.start, note.pitch), note.duration, 0.8,
                facecolor='blue', edgecolor='darkblue',
                alpha=0.6, linewidth=0.5, label='Harmony' if note == harmony.notes[0] else ''
            ))
    
    for note in bass.notes:
        if note.start < max_duration:
            ax.add_patch(plt.Rectangle(
                (note.start, note.pitch), note.duration, 0.8,
                facecolor='green', edgecolor='darkgreen',
                alpha=0.7, linewidth=0.5, label='Bass' if note == bass.notes[0] else ''
            ))
    
    # Calculate pitch range from all voices
    all_pitches = []
    all_pitches.extend([n.pitch for n in melody.notes])
    all_pitches.extend([n.pitch for n in harmony.notes])
    all_pitches.extend([n.pitch for n in bass.notes])
    
    if all_pitches:
        ax.set_ylim(min(all_pitches) - 2, max(all_pitches) + 2)
    
    ax.set_xlim(0, max_duration)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('MIDI Pitch', fontsize=12)
    ax.set_title('Voice Separation (Combined View)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=10)
    
    plt.tight_layout()
    plt.show()


def plot_pitch_contours(separator, melody, harmony, bass):
    """
    Plot pitch contours over time for each voice.
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
    
    # Get contours
    melody_contour = separator.get_voice_contour(melody.notes, resolution=0.1)
    harmony_contour = separator.get_voice_contour(harmony.notes, resolution=0.1)
    bass_contour = separator.get_voice_contour(bass.notes, resolution=0.1)
    
    time_axis = np.arange(len(melody_contour)) * 0.1
    
    # Plot melody contour
    axes[0].plot(time_axis, melody_contour, 'r-', linewidth=2, label='Melody')
    axes[0].fill_between(time_axis, melody_contour, alpha=0.3, color='red')
    axes[0].set_ylabel('Pitch', fontsize=11)
    axes[0].set_title('Melody Contour', fontweight='bold', color='darkred')
    axes[0].grid(True, alpha=0.3)
    
    # Plot harmony contour
    axes[1].plot(time_axis[:len(harmony_contour)], harmony_contour, 'b-', linewidth=2, label='Harmony')
    axes[1].fill_between(time_axis[:len(harmony_contour)], harmony_contour, alpha=0.3, color='blue')
    axes[1].set_ylabel('Pitch', fontsize=11)
    axes[1].set_title('Harmony Contour', fontweight='bold', color='darkblue')
    axes[1].grid(True, alpha=0.3)
    
    # Plot bass contour
    axes[2].plot(time_axis[:len(bass_contour)], bass_contour, 'g-', linewidth=2, label='Bass')
    axes[2].fill_between(time_axis[:len(bass_contour)], bass_contour, alpha=0.3, color='green')
    axes[2].set_ylabel('Pitch', fontsize=11)
    axes[2].set_xlabel('Time (seconds)', fontsize=11)
    axes[2].set_title('Bass Contour', fontweight='bold', color='darkgreen')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()