import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from collections import defaultdict

from .data_structures import Note, PianoRoll, NoteType


@dataclass
class VoiceSeparationConfig:
    """Configuration for voice separation"""

    # Pitch threshold for melody (typically highest notes)
    melody_pitch_threshold: int = 60  # Middle C

    # Pitch threshold for bass (typically lowest notes)
    bass_pitch_threshold: int = 55  # G below middle C

    # Use velocity to help identify melody (louder = more likely melody)
    use_velocity_hints: bool = True

    # Minimum gap between melody and accompaniment (semitones)
    voice_spacing_threshold: int = 3

    # Maximum polyphony in melody voice (usually 1-2)
    max_melody_polyphony: int = 2

    # Whether to track voice leading (smooth transitions)
    track_voice_leading: bool = True


class VoiceSeparator:
    """
    Separates piano music into distinct voices.

    Three main voices:
    - Melody: Top voice, usually the tune
    - Harmony: Middle voice(s), chords and inner voices
    - Bass: Bottom voice, bass line and left hand
    """

    def __init__(self, config: Optional[VoiceSeparationConfig] = None):
        """
        Initialize voice separator.

        Args:
            config: Separation configuration. If None, uses defaults.
        """
        self.config = config or VoiceSeparationConfig()

    def separate_voices(
        self, piano_roll: PianoRoll
    ) -> Tuple[PianoRoll, PianoRoll, PianoRoll]:
        """
        Separate piano roll into melody, harmony, and bass.

        Args:
            piano_roll: Input PianoRoll to separate

        Returns:
            Tuple of (melody_roll, harmony_roll, bass_roll)
        """
        if not piano_roll.notes:
            empty = PianoRoll(
                tempo=piano_roll.tempo,
                time_signature=piano_roll.time_signature,
                key_signature=piano_roll.key_signature,
            )
            return empty, empty, empty

        # Group notes by time windows
        time_windows = self._create_time_windows(piano_roll.notes)

        # Classify notes in each window
        melody_notes = []
        harmony_notes = []
        bass_notes = []

        for window_notes in time_windows:
            m, h, b = self._classify_window(window_notes)
            melody_notes.extend(m)
            harmony_notes.extend(h)
            bass_notes.extend(b)

        # Create separate piano rolls
        melody_roll = PianoRoll(
            notes=melody_notes,
            tempo=piano_roll.tempo,
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature,
        )

        harmony_roll = PianoRoll(
            notes=harmony_notes,
            tempo=piano_roll.tempo,
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature,
        )

        bass_roll = PianoRoll(
            notes=bass_notes,
            tempo=piano_roll.tempo,
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature,
        )

        return melody_roll, harmony_roll, bass_roll

    def _create_time_windows(
        self, notes: List[Note], window_size: float = 0.1
    ) -> List[List[Note]]:
        """
        Group notes into time windows for analysis.

        Args:
            notes: List of notes to group
            window_size: Size of time window in seconds

        Returns:
            List of note groups
        """
        if not notes:
            return []

        sorted_notes = sorted(notes, key=lambda n: n.start)
        windows = []
        current_window = [sorted_notes[0]]
        window_start = sorted_notes[0].start

        for note in sorted_notes[1:]:
            if note.start - window_start <= window_size:
                current_window.append(note)
            else:
                windows.append(current_window)
                current_window = [note]
                window_start = note.start
        if current_window:
            windows.append(current_window)

        return windows

    def _classify_window(
        self, notes: List[Note]
    ) -> Tuple[List[Note], List[Note], List[Note]]:
        """
        Classify notes in a time window into melody, harmony, and bass.

        Args:
            notes: Notes in the time window

        Returns:
            Tuple of (melody_notes, harmony_notes, bass_notes)
        """
        if not notes:
            return [], [], []

        if len(notes) == 1:
            # Single note - classify by pitch
            note = notes[0]
            if note.pitch >= self.config.melody_pitch_threshold:
                return [self._mark_as(note, NoteType.MELODY)], [], []
            elif note.pitch <= self.config.bass_pitch_threshold:
                return [], [], [self._mark_as(note, NoteType.BASS)]
            else:
                return [], [self._mark_as(note, NoteType.HARMONY)], []

        # Multiple notes - use sophisticated separation
        sorted_by_pitch = sorted(notes, key=lambda n: n.pitch, reverse=True)

        melody = []
        harmony = []
        bass = []

        # Highest note(s) are usually melody
        melody_candidates = sorted_by_pitch[: self.config.max_melody_polyphony]

        # If using velocity hints, prefer louder notes for melody
        if self.config.use_velocity_hints:
            melody_candidates = sorted(
                melody_candidates, key=lambda n: n.velocity, reverse=True
            )
            melody_candidates = melody_candidates[: min(2, len(melody_candidates))]

        bass_note = sorted_by_pitch[-1]

        # Everything else is harmony
        for note in notes:
            if note in melody_candidates:
                melody.append(self._mark_as(note, NoteType.MELODY))
            elif note == bass_note and note.pitch <= self.config.bass_pitch_threshold:
                bass.append(self._mark_as(note, NoteType.BASS))
            else:
                harmony.append(self._mark_as(note, NoteType.HARMONY))

        # If bass note is too high, move to harmony
        if bass and bass[0].pitch > self.config.bass_pitch_threshold + 12:
            harmony.extend(bass)
            bass = []

        return melody, harmony, bass

    def _mark_as(self, note: Note, note_type: NoteType) -> Note:
        """
        Create a copy of note with specified type.

        Args:
            note: Original note
            note_type: Type to assign

        Returns:
            New note with type set
        """
        return Note(
            pitch=note.pitch,
            start=note.start,
            end=note.end,
            velocity=note.velocity,
            note_type=note_type,
        )

    def analyze_voices(self, piano_roll: PianoRoll) -> dict:
        """
        Analyze voice distribution in a piano roll.

        Args:
            piano_roll: PianoRoll to analyze

        Returns:
            Dictionary with voice statistics
        """
        melody, harmony, bass = self.separate_voices(piano_roll)

        total_notes = len(piano_roll.notes)

        if total_notes == 0:
            return {
                "total_notes": 0,
                "melody_notes": 0,
                "harmony_notes": 0,
                "bass_notes": 0,
            }

        melody_range = melody.get_pitch_range() if melody.notes else (0, 0)
        harmony_range = harmony.get_pitch_range() if harmony.notes else (0, 0)
        bass_range = bass.get_pitch_range() if bass.notes else (0, 0)

        return {
            "total_notes": total_notes,
            "melody_notes": len(melody.notes),
            "harmony_notes": len(harmony.notes),
            "bass_notes": len(bass.notes),
            "melody_percentage": len(melody.notes) / total_notes * 100,
            "harmony_percentage": len(harmony.notes) / total_notes * 100,
            "bass_percentage": len(bass.notes) / total_notes * 100,
            "melody_range": melody_range,
            "harmony_range": harmony_range,
            "bass_range": bass_range,
            "melody_avg_pitch": (
                np.mean([n.pitch for n in melody.notes]) if melody.notes else 0
            ),
            "harmony_avg_pitch": (
                np.mean([n.pitch for n in harmony.notes]) if harmony.notes else 0
            ),
            "bass_avg_pitch": (
                np.mean([n.pitch for n in bass.notes]) if bass.notes else 0
            ),
        }

    def get_voice_contour(
        self, notes: List[Note], resolution: float = 0.25
    ) -> np.ndarray:
        """
        Extract pitch contour of a voice over time.

        Args:
            notes: Notes in the voice
            resolution: Time resolution in seconds

        Returns:
            Array of pitches over time
        """
        if not notes:
            return np.array([])

        duration = max(n.end for n in notes)
        num_frames = int(duration / resolution) + 1
        contour = np.zeros(num_frames)

        for frame in range(num_frames):
            time = frame * resolution
            # Find active notes at this time
            active = [n for n in notes if n.start <= time < n.end]
            if active:
                # Use highest pitch if multiple notes
                contour[frame] = max(n.pitch for n in active)

        return contour

    def detect_voice_crossings(self, piano_roll: PianoRoll) -> List[dict]:
        """
        Detect when voices cross (bass goes above melody, etc.).
        These usually indicate separation errors.

        Args:
            piano_roll: PianoRoll to analyze

        Returns:
            List of crossing events
        """
        melody, harmony, bass = self.separate_voices(piano_roll)
        crossings = []

        # Check melody-bass crossings
        for m_note in melody.notes:
            for b_note in bass.notes:
                # Check if they overlap in time
                if not (m_note.end <= b_note.start or b_note.end <= m_note.start):
                    # Check if bass is higher than melody
                    if b_note.pitch > m_note.pitch:
                        crossings.append(
                            {
                                "time": m_note.start,
                                "type": "melody-bass crossing",
                                "melody_pitch": m_note.pitch,
                                "bass_pitch": b_note.pitch,
                            }
                        )

        return crossings


def separate_voices(piano_roll: PianoRoll) -> Tuple[PianoRoll, PianoRoll, PianoRoll]:
    """
    Convenience function to separate voices in a piano roll.

    Args:
        piano_roll: PianoRoll to separate

    Returns:
        Tuple of (melody_roll, harmony_roll, bass_roll)
    """
    separator = VoiceSeparator()
    return separator.separate_voices(piano_roll)

