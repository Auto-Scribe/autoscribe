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

    def adjust_difficulty(self, piano_roll: PianoRoll) -> PianoRoll:
        """
        Adjust piano roll to target difficulty level.
        
        Args:
            piano_roll: Original piano roll
            
        Returns:
            Adjusted piano roll
        """
        # Analyze current difficulty
        current_level = self._analyze_difficulty(piano_roll)
        
        print(f"\nCurrent difficulty: {current_level.value}")
        print(f"Target difficulty: {self.config.target_level.value}")
        
        if current_level == self.config.target_level:
            print("Already at target difficulty!")
            return piano_roll
        
        # Determine if we need to simplify or complicate
        level_order = [
            DifficultyLevel.BEGINNER,
            DifficultyLevel.EASY,
            DifficultyLevel.INTERMEDIATE,
            DifficultyLevel.ADVANCED,
            DifficultyLevel.EXPERT
        ]
        
        current_idx = level_order.index(current_level)
        target_idx = level_order.index(self.config.target_level)
        
        if target_idx < current_idx:
            # Simplify
            print("Simplifying...")
            return self._simplify(piano_roll)
        else:
            # Complicate
            print("Adding complexity...")
            return self._complicate(piano_roll)
        
    def _analyze_difficulty(self, piano_roll: PianoRoll) -> DifficultyLevel:
        """
        Analyze current difficulty level of piano roll.
        
        Args:
            piano_roll: Piano roll to analyze
            
        Returns:
            Estimated difficulty level
        """
        if not piano_roll.notes:
            return DifficultyLevel.BEGINNER
        
        # Calculate metrics
        duration = piano_roll.get_duration()
        notes_per_second = len(piano_roll.notes) / duration if duration > 0 else 0
        
        # Check simultaneous notes
        max_simultaneous = self._get_max_simultaneous_notes(piano_roll)
        
        # Check hand stretches
        max_stretch = self._get_max_hand_stretch(piano_roll)
        
        # Score based on metrics
        scores = []
        
        for level in [DifficultyLevel.BEGINNER, DifficultyLevel.EASY, 
                      DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED, 
                      DifficultyLevel.EXPERT]:
            params = self.LEVEL_PARAMS[level]
            
            # Calculate how well it fits this level
            score = 0
            if notes_per_second <= params['max_notes_per_second']:
                score += 1
            if max_simultaneous <= params['max_simultaneous_notes']:
                score += 1
            if max_stretch <= params['max_hand_stretch']:
                score += 1
            
            scores.append((level, score))
        
        # Return level with highest score
        best_level = max(scores, key=lambda x: x[1])[0]
        return best_level
    
    def _get_max_simultaneous_notes(self, piano_roll: PianoRoll) -> int:
        """Get maximum number of simultaneous notes"""
        detector = ChordDetector()
        chords = detector.detect_chords(piano_roll)
        
        if not chords:
            return 1
        
        return max(len(chord.notes) for chord in chords)
    
    def _get_max_hand_stretch(self, piano_roll: PianoRoll) -> int:
        """Get maximum hand stretch required"""
        detector = ChordDetector()
        chords = detector.detect_chords(piano_roll)
        
        if not chords:
            return 0
        
        max_stretch = 0
        for chord in chords:
            if len(chord.notes) >= 2:
                pitches = [n.pitch for n in chord.notes]
                stretch = max(pitches) - min(pitches)
                max_stretch = max(max_stretch, stretch)
        
        return max_stretch
