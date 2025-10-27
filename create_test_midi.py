import pretty_midi
import os


def create_simple_melody():
    """simple C major scale melody for testing"""

    # Create a PrettyMIDI object
    midi = pretty_midi.PrettyMIDI()

    # Create a piano instrument
    piano = pretty_midi.Instrument(program=0, name="Piano")

    # C major scale: C, D, E, F, G, A, B, C
    notes = [60, 62, 64, 65, 67, 69, 71, 72]  # MIDI note numbers

    # Add notes (each lasts 0.5 seconds)
    for i, note_num in enumerate(notes):
        start_time = i * 0.5
        end_time = start_time + 0.4  # Slight gap between notes

        note = pretty_midi.Note(
            velocity=100, pitch=note_num, start=start_time, end=end_time
        )
        piano.notes.append(note)

    # Add the instrument to the MIDI object
    midi.instruments.append(piano)

    # Save the MIDI file
    output_path = "test_melody.mid"
    midi.write(output_path)
    print(f" Created {output_path} - a simple C major scale")

    return midi


def create_simple_chord_progression():
    """simple chord progression for testing"""

    midi = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0, name="Piano")

    # Simple chord progression: C - Am - F - G
    chords = [
        [60, 64, 67],  # C major (C-E-G)
        [57, 60, 64],  # A minor (A-C-E)
        [53, 57, 60],  # F major (F-A-C)
        [55, 59, 62],  # G major (G-B-D)
    ]

    # Add chords (each lasts 1 second)
    for i, chord in enumerate(chords):
        start_time = i * 1.0
        end_time = start_time + 0.8

        for note_num in chord:
            note = pretty_midi.Note(
                velocity=80, pitch=note_num, start=start_time, end=end_time
            )
            piano.notes.append(note)

    midi.instruments.append(piano)

    output_path = "test_chords.mid"
    midi.write(output_path)
    print(f" Created {output_path} - simple chord progression (C-Am-F-G)")

    return midi


def create_complex_example():
    """more complex example with melody and accompaniment"""

    midi = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0, name="Piano")

    # Melody line (right hand)
    melody_notes = [
        (72, 0.0, 0.5, 90),  # C5
        (74, 0.5, 1.0, 85),  # D5
        (76, 1.0, 1.5, 90),  # E5
        (77, 1.5, 2.0, 95),  # F5
        (79, 2.0, 3.0, 100),  # G5 (longer)
    ]

    # Bass line (left hand)
    bass_notes = [
        (48, 0.0, 1.0, 70),  # C3
        (43, 1.0, 2.0, 70),  # G2
        (48, 2.0, 3.0, 70),  # C3
    ]

    # Harmony (middle voice)
    harmony_notes = [
        (64, 0.0, 1.0, 60),  # E4
        (62, 1.0, 2.0, 60),  # D4
        (64, 2.0, 3.0, 60),  # E4
    ]

    # Add all notes
    for pitch, start, end, velocity in melody_notes + bass_notes + harmony_notes:
        note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
        piano.notes.append(note)

    midi.instruments.append(piano)

    output_path = "test_complex.mid"
    midi.write(output_path)
    print(f"Created {output_path} - melody with bass and harmony")

    return midi


def create_rhythm_test():
    """file with various note durations for rhythm testing"""

    midi = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0, name="Piano")

    # Various note durations
    note_data = [
        # (pitch, start, duration, velocity)
        (60, 0.0, 1.0, 80),  # Whole note
        (62, 1.0, 0.5, 80),  # Half note
        (64, 1.5, 0.5, 80),  # Half note
        (65, 2.0, 0.25, 80),  # Quarter note
        (67, 2.25, 0.25, 80),  # Quarter note
        (69, 2.5, 0.25, 80),  # Quarter note
        (71, 2.75, 0.25, 80),  # Quarter note
        (72, 3.0, 0.125, 90),  # Eighth note
        (71, 3.125, 0.125, 90),
        (69, 3.25, 0.125, 90),
        (67, 3.375, 0.125, 90),
        (65, 3.5, 0.125, 90),
        (64, 3.625, 0.125, 90),
        (62, 3.75, 0.125, 90),
        (60, 3.875, 0.125, 90),
    ]

    for pitch, start, duration, velocity in note_data:
        note = pretty_midi.Note(
            velocity=velocity, pitch=pitch, start=start, end=start + duration
        )
        piano.notes.append(note)

    midi.instruments.append(piano)

    output_path = "test_rhythm.mid"
    midi.write(output_path)
    print(f" Created {output_path} - various note durations")

    return midi


def create_out_of_range_test():
    """file with notes outside piano range for error testing"""

    midi = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0, name="Piano")

    # Mix of normal and out-of-range notes
    notes = [
        (20, 0.0, 0.5, 80),  # Below piano range (A0 is 21)
        (60, 0.5, 0.5, 80),  # Normal
        (109, 1.0, 0.5, 80),  # Above piano range (C8 is 108)
        (72, 1.5, 0.5, 80),  # Normal
    ]

    for pitch, start, duration, velocity in notes:
        note = pretty_midi.Note(
            velocity=velocity, pitch=pitch, start=start, end=start + duration
        )
        piano.notes.append(note)

    midi.instruments.append(piano)

    output_path = "test_out_of_range.mid"
    midi.write(output_path)
    print(f" Created {output_path} - includes notes outside piano range")

    return midi


def create_sloppy_timing_test():
    """file with intentionally imperfect timing to test quantization"""

    import random

    random.seed(42)  # Consistent randomness for reproducibility

    midi = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0, name="Piano")

    # C major scale with humanized timing (should be on 16th note grid)
    # Perfect timing would be: 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75
    base_times = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75]
    pitches = [60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65]  # Up and down scale

    print("\n  Creating sloppy timing test:")
    print("  Perfect vs Actual timing (first 8 notes):")

    for i, (perfect_time, pitch) in enumerate(zip(base_times, pitches)):
        # Add random timing error: -30ms to +30ms
        timing_error = random.uniform(-0.03, 0.03)
        actual_start = perfect_time + timing_error

        # Add slight duration variation too
        duration = 0.2 + random.uniform(-0.02, 0.02)

        # Velocity variation (70-100)
        velocity = random.randint(70, 100)

        if i < 8:  # Print first 8 for comparison
            print(
                f"    Note {i+1}: Perfect={perfect_time:.3f}s, Actual={actual_start:.3f}s, Error={timing_error*1000:+.1f}ms"
            )

        note = pretty_midi.Note(
            velocity=velocity,
            pitch=pitch,
            start=actual_start,
            end=actual_start + duration,
        )
        piano.notes.append(note)

    midi.instruments.append(piano)

    output_path = "test_sloppy_timing.mid"
    midi.write(output_path)
    print(f"   Created {output_path} - humanized timing with ±30ms errors")

    return midi


def create_extreme_sloppy_test():
    """file with very sloppy timing to stress-test quantization"""

    import random

    random.seed(123)

    midi = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0, name="Piano")

    # Chord progression with very sloppy timing
    # Each chord should be on beat, but notes are rolled/spread out
    chord_times = [0.0, 1.0, 2.0, 3.0]
    chords = [
        [60, 64, 67],  # C major
        [57, 60, 64],  # A minor
        [53, 57, 60],  # F major
        [55, 59, 62],  # G major
    ]

    print("\n  Creating extreme sloppy timing test (rolled chords):")

    for chord_time, chord_pitches in zip(chord_times, chords):
        print(f"    Chord at {chord_time}s:")
        for j, pitch in enumerate(chord_pitches):
            # Simulate rolled chord - notes spread over 50-100ms
            roll_delay = random.uniform(0.0, 0.1)
            actual_start = chord_time + roll_delay

            # Random duration
            duration = 0.7 + random.uniform(-0.1, 0.1)

            velocity = random.randint(60, 90)

            print(
                f"      Note {j+1}: starts at {actual_start:.3f}s (delay: {roll_delay*1000:.1f}ms)"
            )

            note = pretty_midi.Note(
                velocity=velocity,
                pitch=pitch,
                start=actual_start,
                end=actual_start + duration,
            )
            piano.notes.append(note)

    midi.instruments.append(piano)

    output_path = "test_extreme_sloppy.mid"
    midi.write(output_path)
    print(f"Created {output_path} - extreme timing variations (rolled chords)")

    return midi


def main():
    """Create all test MIDI files"""

    print("\nCreating test MIDI files for AutoScribe...")
    print("=" * 60)

    # Create output directory if needed
    output_dir = "tests/fixtures"
    if os.path.exists(output_dir):
        print(f"Saving to: {output_dir}/")
        os.chdir(output_dir)
    else:
        print(f"Saving to current directory")

    print()

    create_simple_melody()
    create_simple_chord_progression()
    create_complex_example()
    create_rhythm_test()
    create_out_of_range_test()
    create_sloppy_timing_test()
    create_extreme_sloppy_test()

    print()
    print("=" * 60)
    print("All test MIDI files created successfully!")


if __name__ == "__main__":
    main()
