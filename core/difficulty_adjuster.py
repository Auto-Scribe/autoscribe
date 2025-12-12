import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .data_structures import Note, PianoRoll, Chord
from .chord_detector import ChordDetector


class DifficultyLevel(Enum):
    """Difficulty levels for piano music"""

    BEGINNER = "beginner"
    EASY = "easy"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class DifficultyConfig:
    """Configuration for difficulty adjustment"""

    # Target difficulty level
    target_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE

    # Simplification options (for lowering difficulty)
    remove_fast_passages: bool = True
    simplify_chords: bool = True
    reduce_hand_stretches: bool = True
    remove_ornaments: bool = True
    simplify_rhythms: bool = True

    # Complication options (for raising difficulty)
    add_arpeggios: bool = True
    enhance_voicing: bool = True
    add_bass_movement: bool = True

    # Thresholds
    max_notes_per_second: float = 8.0  # For beginners
    max_simultaneous_notes: int = 3  # For beginners
    max_hand_stretch: int = 7  # Semitones for beginners


class DifficultyAdjuster:
    """
    Adjusts piano music difficulty to target level.

    Can simplify for beginners or add complexity for advanced players.
    """

    # Difficulty parameters by level
    LEVEL_PARAMS = {
        DifficultyLevel.BEGINNER: {
            "max_notes_per_second": 4.0,
            "max_simultaneous_notes": 2,
            "max_hand_stretch": 5,
            "allow_black_keys": False,
            "max_tempo": 100,
        },
        DifficultyLevel.EASY: {
            "max_notes_per_second": 6.0,
            "max_simultaneous_notes": 3,
            "max_hand_stretch": 7,
            "allow_black_keys": True,
            "max_tempo": 120,
        },
        DifficultyLevel.INTERMEDIATE: {
            "max_notes_per_second": 8.0,
            "max_simultaneous_notes": 4,
            "max_hand_stretch": 9,
            "allow_black_keys": True,
            "max_tempo": 140,
        },
        DifficultyLevel.ADVANCED: {
            "max_notes_per_second": 12.0,
            "max_simultaneous_notes": 5,
            "max_hand_stretch": 12,
            "allow_black_keys": True,
            "max_tempo": 180,
        },
        DifficultyLevel.EXPERT: {
            "max_notes_per_second": 20.0,
            "max_simultaneous_notes": 8,
            "max_hand_stretch": 15,
            "allow_black_keys": True,
            "max_tempo": 240,
        },
    }

    def __init__(self, config: Optional[DifficultyConfig] = None):
        """
        Initialize difficulty adjuster.

        Args:
            config: Difficulty configuration
        """
        self.config = config or DifficultyConfig()
        self.params = self.LEVEL_PARAMS[self.config.target_level]
