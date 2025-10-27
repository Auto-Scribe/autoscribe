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
