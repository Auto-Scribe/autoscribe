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
        # Load original
    print("\n--- Loading Original MIDI ---")
    original = load_midi(midi_path)
    
    # Analyze original difficulty
    print("\n--- Original Difficulty Analysis ---")
    adjuster = DifficultyAdjuster(DifficultyConfig(target_level=target_level))
    original_report = adjuster.get_difficulty_report(original)
    
    print(f"Current Level: {original_report['difficulty_level']}")
    print(f"Notes per Second: {original_report['notes_per_second']:.2f}")
    print(f"Max Simultaneous Notes: {original_report['max_simultaneous_notes']}")
    print(f"Max Hand Stretch: {original_report['max_hand_stretch']} semitones")
    print(f"Tempo: {original_report['tempo']:.0f} BPM")
    print(f"Total Notes: {original_report['total_notes']}")
    
    # Adjust difficulty
    print(f"\n--- Adjusting to {target_level.value.upper()} ---")
    adjusted = adjuster.adjust_difficulty(original)
    
    # Analyze adjusted difficulty
    print("\n--- Adjusted Difficulty Analysis ---")
    adjusted_report = adjuster.get_difficulty_report(adjusted)
    
    print(f"New Level: {adjusted_report['difficulty_level']}")
    print(f"Notes per Second: {adjusted_report['notes_per_second']:.2f}")
    print(f"Max Simultaneous Notes: {adjusted_report['max_simultaneous_notes']}")
    print(f"Max Hand Stretch: {adjusted_report['max_hand_stretch']} semitones")
    print(f"Tempo: {adjusted_report['tempo']:.0f} BPM")
    print(f"Total Notes: {adjusted_report['total_notes']}")

    # Show changes
    print("\n--- Changes ---")
    note_reduction = original_report['total_notes'] - adjusted_report['total_notes']
    reduction_pct = (note_reduction / original_report['total_notes'] * 100) if original_report['total_notes'] > 0 else 0
    
    print(f"Notes removed: {note_reduction} ({reduction_pct:.1f}%)")
    print(f"Tempo change: {original_report['tempo']:.0f} → {adjusted_report['tempo']:.0f} BPM")
    
    # Visualize
    print("\n--- Generating Visualization ---")
    visualize_difficulty_comparison(
        original, adjusted,
        f"Difficulty: {original_report['difficulty_level']} → {adjusted_report['difficulty_level']}"
    )
    
    # Export if requested
    if export_result:
        output_path = Path(midi_path).stem + f"_{target_level.value}.musicxml"
        print(f"\n--- Exporting to {output_path} ---")
        export_to_musicxml(adjusted, output_path, 
                          title=f"{Path(midi_path).stem} ({target_level.value})")
        print(f"✓ Exported simplified version")
    
    return original, adjusted

def compare_all_levels(midi_path: str):
    """
    Compare all difficulty levels side by side.
    
    Args:
        midi_path: Path to MIDI file
    """
    print(f"\n{'='*70}")
    print("Comparing All Difficulty Levels")
    print(f"{'='*70}")
    
    original = load_midi(midi_path)
    
    levels = [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.EASY,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED,
    ]
    
    results = []
    
    for level in levels:
        adjuster = DifficultyAdjuster(DifficultyConfig(target_level=level))
        adjusted = adjuster.adjust_difficulty(original)
        report = adjuster.get_difficulty_report(adjusted)
        results.append((level, report, adjusted))

        # Print comparison table
    print(f"\n{'Level':<15} {'Notes':<10} {'Notes/s':<10} {'Max Chord':<12} {'Max Stretch':<12}")
    print("-" * 70)
    
    for level, report, _ in results:
        print(f"{level.value:<15} "
              f"{report['total_notes']:<10} "
              f"{report['notes_per_second']:<10.2f} "
              f"{report['max_simultaneous_notes']:<12} "
              f"{report['max_hand_stretch']:<12}")
    
    # Visualize all levels
    fig, axes = plt.subplots(len(levels), 1, figsize=(14, 12), sharex=True)
    max_duration = min(10, original.get_duration())
    
    for i, (level, report, adjusted) in enumerate(results):
        ax = axes[i]
        
        for note in adjusted.notes:
            if note.start < max_duration:
                ax.add_patch(plt.Rectangle(
                    (note.start, note.pitch), note.duration, 0.8,
                    facecolor='steelblue', edgecolor='black',
                    alpha=0.6, linewidth=0.5
                ))
        
        pitch_range = original.get_pitch_range()
        ax.set_ylim(pitch_range[0] - 2, pitch_range[1] + 2)
        ax.set_ylabel('Pitch')
        ax.set_title(f"{level.value.title()} ({report['total_notes']} notes)", 
                    fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel('Time (seconds)')
    axes[-1].set_xlim(0, max_duration)
    
    fig.suptitle('Difficulty Level Comparison', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()