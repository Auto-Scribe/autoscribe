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
    print(f"✓ Created {output_path} - a simple C major scale")

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
    print(f"✓ Created {output_path} - simple chord progression (C-Am-F-G)")

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
    print(f"✓ Created {output_path} - melody with bass and harmony")

    return midi
