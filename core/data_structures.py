"""
Core data structures for AutoScribe.
All other modules build on these fundamental classes.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class NoteType(Enum):
    """Classification of note types for analysis"""

    MELODY = "melody"
    HARMONY = "harmony"
    BASS = "bass"
    UNKNOWN = "unknown"


@dataclass
class Note:
    """
    Core note representation - the fundamental unit of musical data.

    Attributes:
        pitch: MIDI pitch number (0-127, piano is typically 21-108)
        start: Start time in seconds
        end: End time in seconds
        velocity: Note velocity (0-127, represents volume/dynamics)
        note_type: Classification of the note's musical function
    """

    pitch: int
    start: float
    end: float
    velocity: int = 64
    note_type: NoteType = NoteType.UNKNOWN

    def __post_init__(self):
        """Validate note parameters"""
        if not 0 <= self.pitch <= 127:
            raise ValueError(f"Invalid MIDI pitch: {self.pitch} (must be 0-127)")
        if self.start < 0:
            raise ValueError(f"Start time cannot be negative: {self.start}")
        if self.end <= self.start:
            raise ValueError(
                f"End time ({self.end}) must be after start time ({self.start})"
            )
        if not 0 <= self.velocity <= 127:
            raise ValueError(f"Invalid velocity: {self.velocity} (must be 0-127)")

    @property
    def duration(self) -> float:
        """Duration in seconds"""
        return self.end - self.start

    @property
    def midi_note_name(self) -> str:
        """Convert MIDI pitch to note name (e.g., 60 -> 'C4')"""
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (self.pitch // 12) - 1
        note_name = notes[self.pitch % 12]
        return f"{note_name}{octave}"

    @property
    def is_piano_range(self) -> bool:
        """Check if note is within standard piano range (A0 to C8)"""
        return 21 <= self.pitch <= 108

    def __repr__(self) -> str:
        return (
            f"Note(pitch={self.pitch} [{self.midi_note_name}], "
            f"start={self.start:.3f}s, dur={self.duration:.3f}s, vel={self.velocity})"
        )
