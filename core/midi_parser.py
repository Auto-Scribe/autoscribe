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
