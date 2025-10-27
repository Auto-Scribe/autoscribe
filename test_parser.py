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

def analyze_midi(midi_path: str):
    """
    Load and analyze a MIDI file.
    """
    print(f"Loading MIDI file: {midi_path}")
    print("=" * 60)

    try:
        piano_roll = load_midi(midi_path)

        print("\n--- Detailed Analysis ---")
        stats = piano_roll.get_statistics()

        print("\nBasic Info:")
        print(f"  Total Notes: {stats['note_count']}")
        print(f"  Duration: {stats['duration']:.2f} seconds")
        print(f"  Tempo: {stats['tempo']:.1f} BPM")
        print(
            f"  Time Signature: {stats['time_signature'][0]}/{stats['time_signature'][1]}"
        )

        print("\nPitch Analysis:")
        print(f"  Range: {stats['pitch_range'][0]} - {stats['pitch_range'][1]}")
        print(f"  Average Pitch: {stats['avg_pitch']:.1f}")

        print("\nTiming Analysis:")
        print(f"  Average Note Duration: {stats['avg_duration']:.3f} seconds")
        print(f"  Average Velocity: {stats['avg_velocity']:.1f}")

        print("\nFirst 5 Notes:")
        for i, note in enumerate(piano_roll.notes[:5], 1):
            print(f"  {i}. {note}")

        out_of_range = [n for n in piano_roll.notes if not n.is_piano_range]
        if out_of_range:
            print(f"\nWarning: {len(out_of_range)} notes outside piano range")

        print("\nGenerating visualization...")
        visualize_piano_roll(
            piano_roll,
            duration=min(10, stats["duration"]),
            title=f"Piano Roll: {Path(midi_path).name}",
        )

        return piano_roll

    except MidiParserError as e:
        print(f"\nError parsing MIDI: {e}")
        return None
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        return None
    
def compare_notes(piano_roll, start_time=0, duration=2):
    """
    Show notes in a time window.
    """
    end_time = start_time + duration
    notes_in_window = piano_roll.get_notes_in_range(start_time, end_time)

    print(f"\n--- Notes between {start_time:.2f}s and {end_time:.2f}s ---")
    print(f"Found {len(notes_in_window)} notes:")

    for note in notes_in_window:
        print(f"  {note}")

    # Group notes that start at the same time (within 10ms)
    if notes_in_window:
        print("\nSimultaneous note groups (within 10ms):")
        processed = set()
        for i, note in enumerate(notes_in_window):
            if i in processed:
                continue

            simultaneous = [note]
            for j, other in enumerate(notes_in_window[i + 1 :], i + 1):
                if abs(other.start - note.start) < 0.01:
                    simultaneous.append(other)
                    processed.add(j)

            if len(simultaneous) > 1:
                pitches = [n.midi_note_name for n in simultaneous]
                print(f"  Time {note.start:.3f}s: {pitches}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test MIDI Parser")
    parser.add_argument("midi_file", help="Path to MIDI file")
    parser.add_argument("--no-viz", action="store_true", help="Skip visualization")
    parser.add_argument(
        "--analyze-window",
        nargs=2,
        type=float,
        metavar=("START", "DURATION"),
        help="Analyze time window (start, duration in seconds)",
    )

    args = parser.parse_args()

    if not Path(args.midi_file).exists():
        print(f"File not found: {args.midi_file}")
        return 1

    piano_roll = analyze_midi(args.midi_file)
    if piano_roll is None:
        return 1

    if args.analyze_window:
        start, duration = args.analyze_window
        compare_notes(piano_roll, start, duration)

    print("\nParser test completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())