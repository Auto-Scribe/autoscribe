from typing import Optional, Tuple
from pathlib import Path
import os

from music21 import stream, note, chord, clef, meter, tempo, key, layout, bar
from music21 import duration as m21_duration

from .data_structures import Note, PianoRoll, Chord
from .rhythm_quantizer import RhythmQuantizer, quantize_piano_roll
from .chord_detector import ChordDetector, detect_chords
from .voice_separator import VoiceSeparator, separate_voices
from .hand_assigner import HandAssigner, assign_hands


class MusicXMLExporter:
    """
    Exports PianoRoll data to MusicXML format.

    Creates professional piano scores with:
    - Two staves (treble and bass clef)
    - Proper time signatures and key signatures
    - Chord grouping
    - Voice separation
    """

    def __init__(
        self,
        auto_quantize: bool = True,
        auto_detect_chords: bool = True,
        auto_separate_voices: bool = True,
        auto_assign_hands: bool = True,
    ):
        """
        Initialize MusicXML exporter.

        Args:
            auto_quantize: Automatically quantize rhythm before export
            auto_detect_chords: Group simultaneous notes into chords
            auto_separate_voices: Separate into melody/harmony/bass
            auto_assign_hands: Assign notes to left/right hand
        """
        self.auto_quantize = auto_quantize
        self.auto_detect_chords = auto_detect_chords
        self.auto_separate_voices = auto_separate_voices
        self.auto_assign_hands = auto_assign_hands

    def export(
        self, piano_roll: PianoRoll, output_path: str, title: Optional[str] = None
    ) -> str:
        """
        Export piano roll to MusicXML file.

        Args:
            piano_roll: PianoRoll to export
            output_path: Path for output file
            title: Optional piece title

        Returns:
            Path to created file
        """
        print(f"\n{'='*70}")
        print("Exporting to MusicXML")
        print(f"{'='*70}")

        # Step 1: Preprocessing
        processed_roll = self._preprocess(piano_roll)

        # Step 2: Create music21 score
        score = self._create_score(processed_roll, title)

        # Step 3: Export to MusicXML
        output_path = self._write_musicxml(score, output_path)

        print(f"\nSuccessfully exported to: {output_path}")
        return output_path

    def _preprocess(self, piano_roll: PianoRoll) -> PianoRoll:
        """
        Preprocess piano roll (quantize, etc.).

        Args:
            piano_roll: Original piano roll

        Returns:
            Processed piano roll
        """
        print("\n--- Preprocessing ---")

        if self.auto_quantize:
            print("Quantizing rhythm...")
            piano_roll = quantize_piano_roll(piano_roll, grid_resolution="16th")
            print(f"Quantized {len(piano_roll.notes)} notes")

        return piano_roll

    def _create_score(
        self, piano_roll: PianoRoll, title: Optional[str]
    ) -> stream.Score:
        """
        Create music21 Score from piano roll.

        Args:
            piano_roll: Piano roll to convert
            title: Optional title

        Returns:
            music21 Score object
        """
        print("\n--- Creating Score ---")

        # Create score
        score = stream.Score()

        # Add metadata
        from music21 import metadata

        score.metadata = metadata.Metadata()
        if title:
            score.metadata.title = title
        score.metadata.composer = "AutoScribe"

        # Assign hands
        if self.auto_assign_hands:
            print("Assigning hands...")
            right_hand, left_hand = assign_hands(piano_roll)
            print(f"Right hand: {len(right_hand.notes)} notes")
            print(f"Left hand: {len(left_hand.notes)} notes")
        else:
            # Simple split at middle C
            right_hand, left_hand = self._simple_split(piano_roll)

        # Create parts for each hand
        right_part = self._create_part(right_hand, "Piano RH", clef.TrebleClef())
        left_part = self._create_part(left_hand, "Piano LH", clef.BassClef())

        # Add parts to score
        score.append(right_part)
        score.append(left_part)

        print("Score created successfully")

        return score

    def _simple_split(self, piano_roll: PianoRoll) -> Tuple[PianoRoll, PianoRoll]:
        """
        Simple split at middle C if auto_assign_hands is False.

        Args:
            piano_roll: Piano roll to split

        Returns:
            Tuple of (right_hand, left_hand)
        """
        middle_c = 60
        right_notes = [n for n in piano_roll.notes if n.pitch >= middle_c]
        left_notes = [n for n in piano_roll.notes if n.pitch < middle_c]

        right_hand = PianoRoll(
            notes=right_notes,
            tempo=piano_roll.tempo,
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature,
        )

        left_hand = PianoRoll(
            notes=left_notes,
            tempo=piano_roll.tempo,
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature,
        )

        return right_hand, left_hand

    def _create_part(
        self, piano_roll: PianoRoll, part_name: str, part_clef: clef.Clef
    ) -> stream.Part:
        """
        Create a music21 Part from a piano roll.

        Args:
            piano_roll: Piano roll for this part
            part_name: Name of the part
            part_clef: Clef to use

        Returns:
            music21 Part object
        """
        part = stream.Part()
        part.partName = part_name

        # Add clef
        part.append(part_clef)

        # Add key signature
        part.append(key.KeySignature(piano_roll.key_signature))

        # Add time signature
        ts = meter.TimeSignature(
            f"{piano_roll.time_signature[0]}/{piano_roll.time_signature[1]}"
        )
        part.append(ts)

        # Add tempo marking
        mm = tempo.MetronomeMark(number=piano_roll.tempo)
        part.append(mm)

        if not piano_roll.notes:
            # Empty part - add a whole rest
            r = note.Rest()
            r.duration.type = "whole"
            part.append(r)
            return part

        # Group simultaneous notes into chords
        if self.auto_detect_chords:
            note_groups = self._group_simultaneous_notes(piano_roll.notes)
        else:
            note_groups = [[n] for n in piano_roll.notes]

        # Convert note groups to music21 objects
        for group in note_groups:
            m21_obj = self._notes_to_music21(group, piano_roll.tempo)
            if m21_obj:
                part.append(m21_obj)

        # Add bar lines
        part.makeMeasures(inPlace=True)

        return part

    def _group_simultaneous_notes(self, notes: list, threshold: float = 0.05) -> list:
        """
        Group notes that start at approximately the same time.

        Args:
            notes: List of notes
            threshold: Time threshold for grouping (seconds)

        Returns:
            List of note groups
        """
        if not notes:
            return []

        sorted_notes = sorted(notes, key=lambda n: (n.start, n.pitch))
        groups = []
        current_group = [sorted_notes[0]]

        for note in sorted_notes[1:]:
            if abs(note.start - current_group[0].start) <= threshold:
                current_group.append(note)
            else:
                groups.append(current_group)
                current_group = [note]

        if current_group:
            groups.append(current_group)

        return groups

    def _notes_to_music21(
        self, notes: list, tempo: float
    ) -> Optional[note.GeneralNote]:
        """
        Convert a group of notes to music21 Note or Chord.

        Args:
            notes: List of Note objects (same start time)
            tempo: Tempo in BPM

        Returns:
            music21 Note or Chord object
        """
        if not notes:
            return None

        # Calculate duration in beats
        beat_duration = 60.0 / tempo  # seconds per beat
        duration_seconds = notes[0].duration
        duration_beats = duration_seconds / beat_duration

        if len(notes) == 1:
            # Single note
            n = note.Note(notes[0].pitch)
            n.offset = notes[0].start / beat_duration
            n.volume.velocity = notes[0].velocity

            # Set duration
            try:
                n.duration.quarterLength = duration_beats
            except:
                n.duration.quarterLength = 1.0  # Default to quarter note

            return n
        else:
            # Chord
            pitches = [n.pitch for n in notes]
            c = chord.Chord(pitches)
            c.offset = notes[0].start / beat_duration
            c.volume.velocity = notes[0].velocity

            # Set duration
            try:
                c.duration.quarterLength = duration_beats
            except:
                c.duration.quarterLength = 1.0

            return c

    def _write_musicxml(self, score: stream.Score, output_path: str) -> str:
        """
        Write score to MusicXML file.

        Args:
            score: music21 Score
            output_path: Output file path

        Returns:
            Final output path
        """
        print("\n--- Writing MusicXML File ---")

        # Ensure .musicxml extension
        output_path = str(output_path)
        if not output_path.endswith(".musicxml") and not output_path.endswith(".xml"):
            output_path += ".musicxml"

        # Create directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write file
        score.write("musicxml", fp=output_path)

        print(f"Wrote MusicXML to: {output_path}")

        # Check file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"File size: {file_size:,} bytes")

        return output_path
def export_to_musicxml(
    piano_roll: PianoRoll,
    output_path: str,
    title: Optional[str] = None,
    auto_quantize: bool = True,
) -> str:
    """
    Convenience function to export piano roll to MusicXML.

    Args:
        piano_roll: PianoRoll to export
        output_path: Output file path
        title: Optional piece title
        auto_quantize: Whether to quantize rhythm

    Returns:
        Path to created MusicXML file
    """
    exporter = MusicXMLExporter(auto_quantize=auto_quantize)
    return exporter.export(piano_roll, output_path, title)
