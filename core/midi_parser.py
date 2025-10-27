"""
MIDI Parser Module
Handles loading and parsing MIDI files into our internal representation.
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional
import pretty_midi
import warnings

from .data_structures import Note, PianoRoll


class MidiParserError(Exception):
    """Custom exception for MIDI parsing errors"""

    pass


class MidiParser:
    """
    Loads MIDI files and converts them to PianoRoll representation.

    This is the entry point for all MIDI data - everything starts here.
    """

    # Standard piano range (A0 to C8)
    PIANO_MIN_PITCH = 21
    PIANO_MAX_PITCH = 108

    # Supported file extensions
    SUPPORTED_EXTENSIONS = [".mid", ".midi"]

    def __init__(self, strict_piano_range: bool = False, merge_tracks: bool = True):
        """
        Initialize MIDI parser.

        Args:
            strict_piano_range: If True, reject files with notes outside piano range
            merge_tracks: If True, combine all non-drum tracks into one
        """
        self.strict_piano_range = strict_piano_range
        self.merge_tracks = merge_tracks
        self.warnings_list = []

    def load(self, midi_path: str) -> PianoRoll:
        """
        Load MIDI file and convert to PianoRoll.

        Args:
            midi_path: Path to MIDI file

        Returns:
            PianoRoll object containing all musical data

        Raises:
            MidiParserError: If file cannot be loaded or parsed
        """
        # Reset warnings
        self.warnings_list = []

        # Validate file path
        self._validate_path(midi_path)

        # Load MIDI file
        try:
            midi_data = pretty_midi.PrettyMIDI(midi_path)
        except Exception as e:
            raise MidiParserError(f"Failed to load MIDI file: {e}")

        # Validate content
        self._validate_midi_content(midi_data)

        # Extract notes
        notes = self._extract_notes(midi_data)

        # Extract tempo (use first tempo change, or default to 120)
        tempo = self._extract_tempo(midi_data)

        # Extract time signature (use first, or default to 4/4)
        time_signature = self._extract_time_signature(midi_data)

        # Extract key signature (use first, or default to C major)
        key_signature = self._extract_key_signature(midi_data)

        # Create PianoRoll
        piano_roll = PianoRoll(
            notes=notes,
            tempo=tempo,
            time_signature=time_signature,
            key_signature=key_signature,
        )

        # Log statistics
        self._log_statistics(piano_roll)

        return piano_roll

    def _validate_path(self, path: str):
        """Validate file exists and has correct extension"""
        if not os.path.exists(path):
            raise MidiParserError(f"File not found: {path}")

        ext = Path(path).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise MidiParserError(
                f"Unsupported file extension: {ext}. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

    def _validate_midi_content(self, midi: pretty_midi.PrettyMIDI):
        """Validate MIDI has appropriate content for piano transcription"""

        # Check for instruments
        if not midi.instruments:
            raise MidiParserError("MIDI file contains no instruments")

        # Check for non-drum instruments
        non_drum_instruments = [i for i in midi.instruments if not i.is_drum]
        if not non_drum_instruments:
            raise MidiParserError("MIDI file contains only drum tracks")

        # Check for notes
        total_notes = sum(len(inst.notes) for inst in non_drum_instruments)
        if total_notes == 0:
            raise MidiParserError("MIDI file contains no notes")

        # Warn if multiple instruments (when not merging)
        if not self.merge_tracks and len(non_drum_instruments) > 1:
            self._add_warning(
                f"MIDI contains {len(non_drum_instruments)} instruments. "
                "Consider using merge_tracks=True for piano transcription."
            )

    def _extract_notes(self, midi: pretty_midi.PrettyMIDI) -> List[Note]:
        """Extract all notes from MIDI file"""
        notes = []

        for instrument in midi.instruments:
            # Skip drum tracks
            if instrument.is_drum:
                continue

            # Extract notes from this instrument
            for pm_note in instrument.notes:
                # Validate pitch range
                if self.strict_piano_range:
                    if not (
                        self.PIANO_MIN_PITCH <= pm_note.pitch <= self.PIANO_MAX_PITCH
                    ):
                        raise MidiParserError(
                            f"Note pitch {pm_note.pitch} outside piano range "
                            f"({self.PIANO_MIN_PITCH}-{self.PIANO_MAX_PITCH})"
                        )
                else:
                    # Just warn
                    if not (
                        self.PIANO_MIN_PITCH <= pm_note.pitch <= self.PIANO_MAX_PITCH
                    ):
                        self._add_warning(
                            f"Note pitch {pm_note.pitch} outside standard piano range"
                        )

                # Create Note object
                try:
                    note = Note(
                        pitch=pm_note.pitch,
                        start=pm_note.start,
                        end=pm_note.end,
                        velocity=pm_note.velocity,
                    )
                    notes.append(note)
                except ValueError as e:
                    self._add_warning(f"Skipping invalid note: {e}")
                    continue

        return notes
    
    def _extract_tempo(self, midi: pretty_midi.PrettyMIDI) -> float:
        """Extract tempo from MIDI file"""
        tempo_changes = midi.get_tempo_changes()

        if len(tempo_changes[1]) > 0:
            # Use first tempo
            tempo = float(tempo_changes[1][0])

            # Warn if multiple tempo changes
            if len(tempo_changes[1]) > 1:
                self._add_warning(
                    f"MIDI contains {len(tempo_changes[1])} tempo changes. "
                    f"Using first tempo: {tempo:.1f} BPM"
                )

            return tempo
        else:
            # Default tempo
            default_tempo = 120.0
            self._add_warning(f"No tempo found, using default: {default_tempo} BPM")
            return default_tempo

    def _extract_time_signature(self, midi: pretty_midi.PrettyMIDI) -> Tuple[int, int]:
        """Extract time signature from MIDI file"""
        time_signatures = midi.time_signature_changes

        if time_signatures:
            # Use first time signature
            ts = time_signatures[0]
            time_sig = (ts.numerator, ts.denominator)

            # Warn if multiple time signatures
            if len(time_signatures) > 1:
                self._add_warning(
                    f"MIDI contains {len(time_signatures)} time signature changes. "
                    f"Using first: {time_sig[0]}/{time_sig[1]}"
                )

            return time_sig
        else:
            # Default to 4/4
            default_ts = (4, 4)
            self._add_warning(f"No time signature found, using default: 4/4")
            return default_ts
