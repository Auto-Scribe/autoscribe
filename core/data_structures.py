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


@dataclass
class Chord:
    """
    Represents a group of notes played simultaneously.

    Attributes:
        notes: List of Note objects that form the chord
        start: Start time of the chord (derived from notes)
        root_pitch: Optional root note of the chord
    """

    notes: List[Note] = field(default_factory=list)
    root_pitch: Optional[int] = None

    @property
    def start(self) -> float:
        """Start time is the earliest note start"""
        return min(n.start for n in self.notes) if self.notes else 0.0

    @property
    def pitches(self) -> List[int]:
        """Get sorted list of unique pitches in the chord"""
        return sorted(set(n.pitch for n in self.notes))

    @property
    def interval_structure(self) -> List[int]:
        """Get intervals between consecutive pitches (semitones)"""
        pitches = self.pitches
        if len(pitches) < 2:
            return []
        return [pitches[i + 1] - pitches[i] for i in range(len(pitches) - 1)]

    def __repr__(self) -> str:
        pitches = [n.midi_note_name for n in self.notes]
        return f"Chord(notes={pitches}, start={self.start:.3f}s)"


@dataclass
class PianoRoll:
    """
    Intermediate representation between MIDI and notation.
    Contains all musical information in a normalized format.

    Attributes:
        notes: List of all Note objects
        tempo: Tempo in BPM
        time_signature: Tuple of (numerator, denominator)
        key_signature: Key signature (number of sharps/flats, -7 to +7)
    """

    notes: List[Note] = field(default_factory=list)
    tempo: float = 120.0
    time_signature: Tuple[int, int] = (4, 4)
    key_signature: int = 0  # 0 = C major, positive = sharps, negative = flats,

    def __post_init__(self):
        """Validate and sort notes"""
        if self.tempo <= 0:
            raise ValueError(f"Tempo must be positive: {self.tempo}")
        if self.time_signature[0] <= 0 or self.time_signature[1] <= 0:
            raise ValueError(f"Invalid time signature: {self.time_signature}")
        self.sort_by_time()

    def sort_by_time(self):
        """Sort notes chronologically, then by pitch"""
        self.notes.sort(key=lambda n: (n.start, n.pitch))

    def get_notes_at_time(self, time: float, tolerance: float = 0.01) -> List[Note]:
        """
        Get all notes starting at approximately the same time.

        Args:
            time: Target time in seconds
            tolerance: Time window in seconds (default 10ms)

        Returns:
            List of notes starting within tolerance of target time
        """
        return [n for n in self.notes if abs(n.start - time) < tolerance]

    def get_notes_in_range(self, start_time: float, end_time: float) -> List[Note]:
        """Get all notes that start within a time range"""
        return [n for n in self.notes if start_time <= n.start < end_time]

    def get_duration(self) -> float:
        """Total duration of the piano roll in seconds"""
        if not self.notes:
            return 0.0
        return max(n.end for n in self.notes)

    def get_pitch_range(self) -> Tuple[int, int]:
        """Get minimum and maximum pitches used"""
        if not self.notes:
            return (0, 0)
        pitches = [n.pitch for n in self.notes]
        return (min(pitches), max(pitches))

    def filter_by_pitch_range(self, min_pitch: int, max_pitch: int) -> "PianoRoll":
        """Create new PianoRoll with only notes in specified pitch range"""
        filtered_notes = [n for n in self.notes if min_pitch <= n.pitch <= max_pitch]
        return PianoRoll(
            notes=filtered_notes,
            tempo=self.tempo,
            time_signature=self.time_signature,
            key_signature=self.key_signature,
        )

    def get_statistics(self) -> dict:
        """Get statistical summary of the piano roll"""
        if not self.notes:
            return {"note_count": 0}

        pitches = [n.pitch for n in self.notes]
        durations = [n.duration for n in self.notes]
        velocities = [n.velocity for n in self.notes]

        return {
            "note_count": len(self.notes),
            "duration": self.get_duration(),
            "pitch_range": self.get_pitch_range(),
            "avg_pitch": sum(pitches) / len(pitches),
            "avg_duration": sum(durations) / len(durations),
            "avg_velocity": sum(velocities) / len(velocities),
            "tempo": self.tempo,
            "time_signature": self.time_signature,
        }

    def __repr__(self) -> str:
        return (
            f"PianoRoll(notes={len(self.notes)}, "
            f"duration={self.get_duration():.2f}s, "
            f"tempo={self.tempo}bpm)"
        )
