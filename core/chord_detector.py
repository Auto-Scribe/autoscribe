from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from collections import defaultdict

from .data_structures import Note, Chord, PianoRoll


@dataclass
class ChordDetectionConfig:
    """Configuration for chord detection"""

    # Time window for considering notes simultaneous (seconds)
    simultaneity_threshold: float = 0.05  # 50ms

    # Minimum notes to form a chord (2 or 3 typically)
    min_chord_size: int = 2

    # Whether to analyze chord types (major, minor, etc.)
    analyze_chord_types: bool = True

    # Whether to merge broken chords (arpeggios played quickly)
    merge_arpeggios: bool = False
    arpeggio_threshold: float = 0.15  # 150ms between notes


class ChordDetector:
    """
    Detects and groups simultaneous notes into chords.
    Also identifies chord types for harmonic analysis.
    """

    # Chord type definitions (intervals from root in semitones)
    CHORD_TYPES = {
        "major": [0, 4, 7],
        "minor": [0, 3, 7],
        "diminished": [0, 3, 6],
        "augmented": [0, 4, 8],
        "major7": [0, 4, 7, 11],
        "minor7": [0, 3, 7, 10],
        "dominant7": [0, 4, 7, 10],
        "sus2": [0, 2, 7],
        "sus4": [0, 5, 7],
    }

    def __init__(self, config: Optional[ChordDetectionConfig] = None):
        """
        Initialize chord detector.

        Args:
            config: Detection configuration. If None, uses defaults.
        """
        self.config = config or ChordDetectionConfig()

    def detect_chords(self, piano_roll: PianoRoll) -> List[Chord]:
        """
        Detect all chords in a piano roll.

        Args:
            piano_roll: Input PianoRoll

        Returns:
            List of Chord objects
        """
        if not piano_roll.notes:
            return []

        # Group notes by onset time
        onset_groups = self._group_by_onset(piano_roll.notes)

        # Convert groups to Chord objects
        chords = []
        for onset_time, notes in sorted(onset_groups.items()):
            if len(notes) >= self.config.min_chord_size:
                chord = self._create_chord(notes)
                chords.append(chord)

        # Optionally merge arpeggios
        if self.config.merge_arpeggios:
            chords = self._merge_arpeggios(chords)

        return chords

    def _group_by_onset(self, notes: List[Note]) -> Dict[float, List[Note]]:
        """
        Group notes that start at approximately the same time.

        Args:
            notes: List of notes to group

        Returns:
            Dictionary mapping onset times to note lists
        """
        groups = defaultdict(list)

        for note in notes:
            # Find if there's an existing group within threshold
            found_group = False
            for onset_time in list(groups.keys()):
                if abs(note.start - onset_time) <= self.config.simultaneity_threshold:
                    groups[onset_time].append(note)
                    found_group = True
                    break

            # Create new group if needed
            if not found_group:
                groups[note.start].append(note)

        return groups

    def _create_chord(self, notes: List[Note]) -> Chord:
        """
        Create a Chord object from a group of notes.

        Args:
            notes: Notes that form the chord

        Returns:
            Chord object
        """
        chord = Chord(notes=sorted(notes, key=lambda n: n.pitch))

        # Analyze chord type if configured
        if self.config.analyze_chord_types:
            chord.root_pitch = self._find_root(chord)

        return chord

    def _find_root(self, chord: Chord) -> Optional[int]:
        """
        Attempt to identify the root note of a chord.

        Args:
            chord: Chord to analyze

        Returns:
            MIDI pitch of likely root, or None if unclear
        """
        if len(chord.notes) < 2:
            return chord.notes[0].pitch if chord.notes else None

        # Simple heuristic: lowest note is often the root
        # (This is naive but works for many cases)
        return min(n.pitch for n in chord.notes)

    def identify_chord_type(self, chord: Chord) -> Optional[str]:
        """
        Identify the type of a chord (major, minor, etc.).

        Args:
            chord: Chord to identify

        Returns:
            Chord type name, or None if unrecognized
        """
        if len(chord.pitches) < 2:
            return None

        # Get intervals from lowest note
        root = min(chord.pitches)
        intervals = [p - root for p in chord.pitches]

        # Normalize to single octave
        intervals = [i % 12 for i in intervals]
        intervals = sorted(set(intervals))

        # Match against known chord types
        for chord_type, pattern in self.CHORD_TYPES.items():
            if intervals == pattern:
                return chord_type

        # Try inversions (rotate the pattern)
        for chord_type, pattern in self.CHORD_TYPES.items():
            for rotation in range(1, len(pattern)):
                rotated = pattern[rotation:] + [p + 12 for p in pattern[:rotation]]
                rotated_normalized = sorted([p % 12 for p in rotated])
                if intervals == rotated_normalized:
                    return f"{chord_type} (inversion)"

        return "unknown"

    def _merge_arpeggios(self, chords: List[Chord]) -> List[Chord]:
        """
        Merge rapidly played broken chords (arpeggios) into single chords.

        Args:
            chords: List of detected chords

        Returns:
            List with arpeggios merged
        """
        if not chords:
            return chords

        merged = []
        current_group = [chords[0]]

        for chord in chords[1:]:
            # Check if this chord is close enough to merge
            last_chord_time = current_group[-1].start
            if chord.start - last_chord_time <= self.config.arpeggio_threshold:
                current_group.append(chord)
            else:
                # Merge current group and start new one
                merged.append(self._merge_chord_group(current_group))
                current_group = [chord]

        # Don't forget the last group
        merged.append(self._merge_chord_group(current_group))

        return merged

    def _merge_chord_group(self, chord_group: List[Chord]) -> Chord:
        """
        Merge multiple chords into one.

        Args:
            chord_group: Chords to merge

        Returns:
            Single merged chord
        """
        if len(chord_group) == 1:
            return chord_group[0]

        # Combine all notes from all chords
        all_notes = []
        for chord in chord_group:
            all_notes.extend(chord.notes)

        # Use earliest start time
        earliest_start = min(c.start for c in chord_group)

        # Adjust note start times to earliest
        adjusted_notes = []
        for note in all_notes:
            adjusted_note = Note(
                pitch=note.pitch,
                start=earliest_start,
                end=note.end,
                velocity=note.velocity,
                note_type=note.note_type,
            )
            adjusted_notes.append(adjusted_note)

        return Chord(notes=adjusted_notes)

    def analyze_piano_roll(self, piano_roll: PianoRoll) -> dict:
        """
        Analyze chord content in a piano roll.

        Args:
            piano_roll: PianoRoll to analyze

        Returns:
            Dictionary with chord statistics
        """
        chords = self.detect_chords(piano_roll)

        if not chords:
            return {
                "total_chords": 0,
                "chord_types": {},
                "avg_chord_size": 0,
                "polyphony_ratio": 0,
            }

        # Count chord types
        chord_type_counts = defaultdict(int)
        chord_sizes = []

        for chord in chords:
            chord_type = self.identify_chord_type(chord)
            chord_type_counts[chord_type] += 1
            chord_sizes.append(len(chord.notes))

        # Calculate polyphony ratio
        total_notes = len(piano_roll.notes)
        notes_in_chords = sum(len(c.notes) for c in chords)
        polyphony_ratio = notes_in_chords / total_notes if total_notes > 0 else 0

        return {
            "total_chords": len(chords),
            "chord_types": dict(chord_type_counts),
            "avg_chord_size": sum(chord_sizes) / len(chord_sizes) if chord_sizes else 0,
            "chord_size_range": (
                (min(chord_sizes), max(chord_sizes)) if chord_sizes else (0, 0)
            ),
            "polyphony_ratio": polyphony_ratio,
            "single_notes": total_notes - notes_in_chords,
        }


def detect_chords(
    piano_roll: PianoRoll, simultaneity_threshold: float = 0.05
) -> List[Chord]:
    """
    Convenience function to detect chords in a piano roll.

    Args:
        piano_roll: PianoRoll to analyze
        simultaneity_threshold: Time window for simultaneous notes (seconds)

    Returns:
        List of Chord objects
    """
    config = ChordDetectionConfig(simultaneity_threshold=simultaneity_threshold)
    detector = ChordDetector(config)
    return detector.detect_chords(piano_roll)


def get_chord_name(chord: Chord) -> str:
    """
    Get a human-readable name for a chord.

    Args:
        chord: Chord to name

    Returns:
        Chord name (e.g., "C major", "Am7")
    """
    detector = ChordDetector()
    chord_type = detector.identify_chord_type(chord)

    if not chord_type or chord_type == "unknown":
        # Just list the notes
        note_names = [n.midi_note_name for n in chord.notes]
        return f"Chord: {', '.join(note_names)}"

    # Get root note name
    root_pitch = chord.root_pitch or min(n.pitch for n in chord.notes)
    root_name = Note(pitch=root_pitch, start=0, end=1).midi_note_name[
        :-1
    ]  # Remove octave

    return f"{root_name} {chord_type}"
