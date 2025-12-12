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
    def _simplify(self, piano_roll: PianoRoll) -> PianoRoll:
        """
        Simplify piano roll for lower difficulty.
        
        Args:
            piano_roll: Original piano roll
            
        Returns:
            Simplified piano roll
        """
        notes = piano_roll.notes.copy()
        
        # Step 1: Remove very fast passages
        if self.config.remove_fast_passages:
            print("  - Removing fast passages...")
            notes = self._remove_fast_notes(notes)
        
        # Step 2: Simplify chords
        if self.config.simplify_chords:
            print("  - Simplifying chords...")
            notes = self._simplify_chord_voicings(notes)
        
        # Step 3: Reduce hand stretches
        if self.config.reduce_hand_stretches:
            print("  - Reducing hand stretches...")
            notes = self._reduce_stretches(notes)
        
        # Step 4: Simplify rhythms
        if self.config.simplify_rhythms:
            print("  - Simplifying rhythms...")
            notes = self._simplify_rhythms(notes)
        
        # Step 5: Remove ornaments
        if self.config.remove_ornaments:
            print("  - Removing ornamental notes...")
            notes = self._remove_ornaments(notes)
        
        return PianoRoll(
            notes=notes,
            tempo=min(piano_roll.tempo, self.params['max_tempo']),
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature
        )
    
    def _remove_fast_notes(self, notes: List[Note]) -> List[Note]:
        """Remove notes that are too fast for target level"""
        if not notes:
            return notes
        
        # Calculate note density in time windows
        window_size = 1.0  # 1 second windows
        max_notes = self.params['max_notes_per_second']
        
        # Group notes by time windows
        sorted_notes = sorted(notes, key=lambda n: n.start)
        kept_notes = []
        
        current_window_start = sorted_notes[0].start
        current_window_notes = []
        
        for note in sorted_notes:
            if note.start - current_window_start < window_size:
                current_window_notes.append(note)
            else:
                # Process completed window
                if len(current_window_notes) <= max_notes:
                    kept_notes.extend(current_window_notes)
                else:
                    # Keep only the most important notes
                    kept_notes.extend(self._select_important_notes(
                        current_window_notes, int(max_notes)
                    ))
                
                # Start new window
                current_window_start = note.start
                current_window_notes = [note]
        
        # Process last window
        if len(current_window_notes) <= max_notes:
            kept_notes.extend(current_window_notes)
        else:
            kept_notes.extend(self._select_important_notes(
                current_window_notes, int(max_notes)
            ))
        
        return kept_notes

    def _select_important_notes(self, notes: List[Note], count: int) -> List[Note]:
        """Select the most important notes from a group"""
        # Prioritize by:
        # 1. Velocity (louder = more important)
        # 2. Duration (longer = more important)
        # 3. Pitch extremes (highest/lowest)
        
        scored_notes = []
        for note in notes:
            score = (
                note.velocity / 127.0 * 0.4 +
                min(note.duration, 1.0) * 0.3 +
                (1.0 if note.pitch == max(n.pitch for n in notes) or 
                       note.pitch == min(n.pitch for n in notes) else 0.0) * 0.3
            )
            scored_notes.append((score, note))
        
        # Sort by score and take top N
        scored_notes.sort(reverse=True, key=lambda x: x[0])
        return [note for _, note in scored_notes[:count]]
    
    def _simplify_chord_voicings(self, notes: List[Note]) -> List[Note]:
        """Simplify chord voicings to fewer notes"""
        detector = ChordDetector()
        temp_roll = PianoRoll(notes=notes, tempo=120)
        chords = detector.detect_chords(temp_roll)
        
        max_chord_size = self.params['max_simultaneous_notes']
        
        simplified_notes = []
        processed_times = set()
        
        for chord in chords:
            if len(chord.notes) <= max_chord_size:
                # Keep as is
                simplified_notes.extend(chord.notes)
            else:
                # Simplify: keep root, highest note, and some middle notes
                chord_notes = sorted(chord.notes, key=lambda n: n.pitch)
                
                # Always keep lowest and highest
                kept = [chord_notes[0], chord_notes[-1]]
                
                # Add middle notes if space allows
                remaining = max_chord_size - 2
                if remaining > 0 and len(chord_notes) > 2:
                    middle = chord_notes[1:-1]
                    # Keep notes closest to melody (highest notes)
                    middle.sort(key=lambda n: n.pitch, reverse=True)
                    kept.extend(middle[:remaining])
                
                simplified_notes.extend(kept)
            
            # Mark these times as processed
            processed_times.add(chord.start)
        
        # Add any notes that weren't part of chords
        for note in notes:
            if not any(abs(note.start - t) < 0.05 for t in processed_times):
                simplified_notes.append(note)
        
        return simplified_notes

def _reduce_stretches(self, notes: List[Note]) -> List[Note]:
        """Reduce hand stretches by moving notes or removing them"""
        detector = ChordDetector()
        temp_roll = PianoRoll(notes=notes, tempo=120)
        chords = detector.detect_chords(temp_roll)
        
        max_stretch = self.params['max_hand_stretch']
        
        adjusted_notes = []
        processed_times = set()
        
        for chord in chords:
            if len(chord.notes) <= 1:
                adjusted_notes.extend(chord.notes)
                continue
            
            chord_notes = sorted(chord.notes, key=lambda n: n.pitch)
            pitches = [n.pitch for n in chord_notes]
            stretch = max(pitches) - min(pitches)
            
            if stretch <= max_stretch:
                # Stretch is acceptable
                adjusted_notes.extend(chord.notes)
            else:
                # Reduce stretch by removing middle notes
                # Keep outer voices (bass and melody)
                kept = [chord_notes[0], chord_notes[-1]]
                adjusted_notes.extend(kept)
            
            processed_times.add(chord.start)
        
        # Add single notes
        for note in notes:
            if not any(abs(note.start - t) < 0.05 for t in processed_times):
                adjusted_notes.append(note)
        
        return adjusted_notes
    
    def _simplify_rhythms(self, notes: List[Note]) -> List[Note]:
        """Simplify complex rhythms to simpler note values"""
        # Round durations to simple fractions
        simple_durations = [0.125, 0.25, 0.5, 1.0, 2.0]  # 16th, 8th, quarter, half, whole
        
        simplified = []
        for note in notes:
            # Find closest simple duration
            closest_duration = min(simple_durations, key=lambda d: abs(d - note.duration))
            
            simplified_note = Note(
                pitch=note.pitch,
                start=note.start,
                end=note.start + closest_duration,
                velocity=note.velocity,
                note_type=note.note_type
            )
            simplified.append(simplified_note)
        
        return simplified
    
    def _remove_ornaments(self, notes: List[Note]) -> List[Note]:
        """Remove ornamental notes (grace notes, etc.)"""
        # Remove very short notes (likely grace notes or ornaments)
        min_duration = 0.1  # 100ms
        return [n for n in notes if n.duration >= min_duration]
    
    def _complicate(self, piano_roll: PianoRoll) -> PianoRoll:
        """
        Add complexity to piano roll for higher difficulty.
        
        Args:
            piano_roll: Original piano roll
            
        Returns:
            More complex piano roll
        """
        notes = piano_roll.notes.copy()
        
        # This is more advanced - placeholder for now
        print("  - Adding arpeggiated patterns...")
        print("  - Enhancing chord voicings...")
        print("  - Adding bass movement...")
        
        # TODO: Implement complexity additions
        # For now, just return original
        return piano_roll
    
    def get_difficulty_report(self, piano_roll: PianoRoll) -> dict:
        """
        Generate detailed difficulty analysis report.
        
        Args:
            piano_roll: Piano roll to analyze
            
        Returns:
            Dictionary with difficulty metrics
        """
        duration = piano_roll.get_duration()
        notes_per_second = len(piano_roll.notes) / duration if duration > 0 else 0
        max_simultaneous = self._get_max_simultaneous_notes(piano_roll)
        max_stretch = self._get_max_hand_stretch(piano_roll)
        current_level = self._analyze_difficulty(piano_roll)
        
        return {
            'difficulty_level': current_level.value,
            'notes_per_second': notes_per_second,
            'max_simultaneous_notes': max_simultaneous,
            'max_hand_stretch': max_stretch,
            'tempo': piano_roll.tempo,
            'total_notes': len(piano_roll.notes),
            'duration': duration,
        }


    def adjust_difficulty(piano_roll: PianoRoll, 
                         target_level: DifficultyLevel) -> PianoRoll:
        """
        Convenience function to adjust difficulty.
        
        Args:
            piano_roll: Piano roll to adjust
            target_level: Target difficulty level
            
        Returns:
            Adjusted piano roll
        """
        config = DifficultyConfig(target_level=target_level)
        adjuster = DifficultyAdjuster(config)
        return adjuster.adjust_difficulty(piano_roll)

