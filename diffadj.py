"""
Test script for Difficulty Adjuster.
Shows before and after comparison of difficulty adjustment.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from autoscribe import load_midi
from autoscribe.core.difficulty_adjuster import (
    DifficultyAdjuster, 
    DifficultyConfig, 
    DifficultyLevel,
    adjust_difficulty
)
from autoscribe.core.musicxml_exporter import export_to_musicxml
import matplotlib.pyplot as plt


def visualize_difficulty_comparison(original, adjusted, title="Difficulty Adjustment"):
    """
    Visualize original vs adjusted difficulty.
    
    Args:
        original: Original PianoRoll
        adjusted: Adjusted PianoRoll
        title: Plot title
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    max_duration = min(10, original.get_duration())
    
    # Plot original
    for note in original.notes:
        if note.start < max_duration:
            alpha = 0.5 + (note.velocity / 127) * 0.4
            ax1.add_patch(plt.Rectangle(
                (note.start, note.pitch), note.duration, 0.8,
                facecolor='red', edgecolor='darkred',
                alpha=alpha, linewidth=0.5
            ))
    
    # Plot adjusted
    for note in adjusted.notes:
        if note.start < max_duration:
            alpha = 0.5 + (note.velocity / 127) * 0.4
            ax2.add_patch(plt.Rectangle(
                (note.start, note.pitch), note.duration, 0.8,
                facecolor='green', edgecolor='darkgreen',
                alpha=alpha, linewidth=0.5
            ))
    
    # Formatting
    pitch_range = original.get_pitch_range()
    for ax in [ax1, ax2]:
        ax.set_ylim(pitch_range[0] - 2, pitch_range[1] + 2)
        ax.set_xlim(0, max_duration)
        ax.set_ylabel('Pitch')
        ax.grid(True, alpha=0.3)
        ax1.set_title(f'Original ({len(original.notes)} notes)', fontweight='bold')
    ax2.set_title(f'Adjusted ({len(adjusted.notes)} notes)', fontweight='bold')
    ax2.set_xlabel('Time (seconds)')
    
    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()


def test_difficulty_adjustment(midi_path: str, 
                               target_level: DifficultyLevel,
                               export_result: bool = False):
    """
    Test difficulty adjustment on a MIDI file.
    
    Args:
        midi_path: Path to MIDI file
        target_level: Target difficulty level
        export_result: Whether to export adjusted version to MusicXML
    """
    print(f"\n{'='*70}")
    print("Difficulty Adjustment Test")
    print(f"{'='*70}")
    print(f"File: {Path(midi_path).name}")
    print(f"Target Level: {target_level.value}")