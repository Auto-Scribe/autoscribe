import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

from .data_structures import Note, PianoRoll


class Hand(Enum):
    """Which hand plays the note"""

    LEFT = "left"
    RIGHT = "right"
    EITHER = "either"  # Can be played by either hand


@dataclass
class HandAssignment:
    """Stores hand assignment for notes"""

    note: Note
    hand: Hand
    difficulty: float = 0.0  # 0 = easy, 1 = difficult


@dataclass
class HandAssignmentConfig:
    """Configuration for hand assignment"""

    # Middle C (MIDI 60) is the default split point
    default_split_pitch: int = 60  # Middle C

    # Allow crossover (right hand going below left, or vice versa)
    allow_crossover: bool = True

    # Maximum comfortable stretch for one hand (semitones)
    max_hand_stretch: int = 12  # One octave

    # Prefer to keep melody in right hand
    prefer_melody_right: bool = True

    # Maximum notes per hand at once (polyphony)
    max_notes_per_hand: int = 5

    # Optimize for playability vs. traditional notation
    optimize_playability: bool = True

    # Minimum pitch for right hand (avoid too low)
    min_right_hand_pitch: int = 48  # C3

    # Maximum pitch for left hand (avoid too high)
    max_left_hand_pitch: int = 72  # C5


class HandAssigner:
    """
    Assigns notes to left or right hand for piano notation.

    Considers:
    - Pitch ranges (treble vs bass clef)
    - Hand stretches and ergonomics
    - Voice separation (melody vs bass)
    - Playability
    """

    # Standard clef ranges
    TREBLE_CLEF_CENTER = 71  # B4
    BASS_CLEF_CENTER = 50  # D3

    def __init__(self, config: Optional[HandAssignmentConfig] = None):
        """
        Initialize hand assigner.

        Args:
            config: Assignment configuration. If None, uses defaults.
        """
        self.config = config or HandAssignmentConfig()

    def assign_hands(self, piano_roll: PianoRoll) -> Tuple[PianoRoll, PianoRoll]:
        """
        Assign notes to left and right hands.

        Args:
            piano_roll: Input PianoRoll

        Returns:
            Tuple of (right_hand_roll, left_hand_roll)
        """
        if not piano_roll.notes:
            empty = PianoRoll(
                tempo=piano_roll.tempo,
                time_signature=piano_roll.time_signature,
                key_signature=piano_roll.key_signature,
            )
            return empty, empty

        # Group notes by time for simultaneous analysis
        time_groups = self._group_by_time(piano_roll.notes)

        # Assign hands for each time group
        assignments = []
        for group in time_groups:
            group_assignments = self._assign_group(group)
            assignments.extend(group_assignments)

        # Split into two piano rolls
        right_notes = [a.note for a in assignments if a.hand == Hand.RIGHT]
        left_notes = [a.note for a in assignments if a.hand == Hand.LEFT]

        right_hand = PianoRoll(
            notes=right_notes,
            tempo=piano_roll.tempo,
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature,
        )

        left_hand = PianoRoll(
            notes=left_notes,
            tempo=piano_roll.tempo,
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature,
        )

        return right_hand, left_hand

    def _group_by_time(
        self, notes: List[Note], threshold: float = 0.05
    ) -> List[List[Note]]:
        """
        Group notes that occur at approximately the same time.

        Args:
            notes: Notes to group
            threshold: Time threshold for grouping (seconds)

        Returns:
            List of note groups
        """
        if not notes:
            return []

        sorted_notes = sorted(notes, key=lambda n: n.start)
        groups = []
        current_group = [sorted_notes[0]]

        for note in sorted_notes[1:]:
            if note.start - current_group[0].start <= threshold:
                current_group.append(note)
            else:
                groups.append(current_group)
                current_group = [note]

        if current_group:
            groups.append(current_group)

        return groups

    def _assign_group(self, notes: List[Note]) -> List[HandAssignment]:
        """
        Assign hands for a group of simultaneous notes.

        Args:
            notes: Notes occurring at the same time

        Returns:
            List of HandAssignment objects
        """
        if not notes:
            return []

        if len(notes) == 1:
            # Single note - simple pitch-based assignment
            return [self._assign_single_note(notes[0])]

        # Multiple simultaneous notes - more complex logic
        sorted_notes = sorted(notes, key=lambda n: n.pitch)

        # Find split point
        split_idx = self._find_split_point(sorted_notes)

        # Assign based on split
        assignments = []

        for i, note in enumerate(sorted_notes):
            if i < split_idx:
                # Lower notes -> left hand
                hand = Hand.LEFT
            else:
                # Higher notes -> right hand
                hand = Hand.RIGHT

            difficulty = self._calculate_difficulty(note, hand, sorted_notes)
            assignments.append(
                HandAssignment(note=note, hand=hand, difficulty=difficulty)
            )

        # Check if assignment is playable
        assignments = self._validate_and_adjust(assignments)

        return assignments

    def _assign_single_note(self, note: Note) -> HandAssignment:
        """
        Assign hand for a single isolated note.

        Args:
            note: Note to assign

        Returns:
            HandAssignment
        """
        # Simple pitch-based rule
        if note.pitch < self.config.default_split_pitch:
            hand = Hand.LEFT
        else:
            hand = Hand.RIGHT

        return HandAssignment(note=note, hand=hand, difficulty=0.0)

    def _find_split_point(self, sorted_notes: List[Note]) -> int:
        """
        Find optimal split point between left and right hand notes.

        Args:
            sorted_notes: Notes sorted by pitch

        Returns:
            Index where split should occur
        """
        if len(sorted_notes) <= 1:
            return 0

        # Default: split at middle C
        split_pitch = self.config.default_split_pitch

        # Find closest note to split pitch
        best_idx = 0
        min_distance = float("inf")

        for i, note in enumerate(sorted_notes):
            distance = abs(note.pitch - split_pitch)
            if distance < min_distance:
                min_distance = distance
                best_idx = i

        # Ensure at least one note per hand if possible
        if best_idx == 0 and len(sorted_notes) > 1:
            best_idx = 1
        elif best_idx == len(sorted_notes):
            best_idx = len(sorted_notes) - 1

        return best_idx

    def _calculate_difficulty(
        self, note: Note, hand: Hand, all_notes: List[Note]
    ) -> float:
        """
        Calculate how difficult this note is to play with the assigned hand.

        Args:
            note: Note being evaluated
            hand: Assigned hand
            all_notes: All notes in the group

        Returns:
            Difficulty score (0 = easy, 1 = very difficult)
        """
        difficulty = 0.0

        # Check hand stretch
        same_hand_notes = [n for n in all_notes if self._get_expected_hand(n) == hand]
        if len(same_hand_notes) > 1:
            pitches = [n.pitch for n in same_hand_notes]
            stretch = max(pitches) - min(pitches)

            if stretch > self.config.max_hand_stretch:
                difficulty += (stretch - self.config.max_hand_stretch) / 12.0

        # Check polyphony
        if len(same_hand_notes) > self.config.max_notes_per_hand:
            difficulty += 0.3

        # Check if note is outside comfortable range for hand
        if hand == Hand.RIGHT:
            if note.pitch < self.config.min_right_hand_pitch:
                difficulty += 0.2
        elif hand == Hand.LEFT:
            if note.pitch > self.config.max_left_hand_pitch:
                difficulty += 0.2

        return min(difficulty, 1.0)

    def _get_expected_hand(self, note: Note) -> Hand:
        """Get expected hand based on simple pitch rule"""
        return (
            Hand.RIGHT if note.pitch >= self.config.default_split_pitch else Hand.LEFT
        )

    def _validate_and_adjust(
        self, assignments: List[HandAssignment]
    ) -> List[HandAssignment]:
        """
        Validate hand assignments and adjust if unplayable.

        Args:
            assignments: Initial assignments

        Returns:
            Adjusted assignments
        """
        # Check if any hand has too many notes
        right_count = sum(1 for a in assignments if a.hand == Hand.RIGHT)
        left_count = sum(1 for a in assignments if a.hand == Hand.LEFT)

        # If one hand is overloaded, try to redistribute
        if right_count > self.config.max_notes_per_hand:
            # Move some notes to left hand
            assignments = self._redistribute_notes(assignments, Hand.RIGHT, Hand.LEFT)

        if left_count > self.config.max_notes_per_hand:
            # Move some notes to right hand
            assignments = self._redistribute_notes(assignments, Hand.LEFT, Hand.RIGHT)

        return assignments

    def _redistribute_notes(
        self, assignments: List[HandAssignment], from_hand: Hand, to_hand: Hand
    ) -> List[HandAssignment]:
        """
        Redistribute notes from one hand to another.

        Args:
            assignments: Current assignments
            from_hand: Hand to take notes from
            to_hand: Hand to give notes to

        Returns:
            Updated assignments
        """
        # Find notes in the overloaded hand
        overloaded = [a for a in assignments if a.hand == from_hand]

        if not overloaded:
            return assignments

        # Sort by how suitable they are for the other hand
        if to_hand == Hand.RIGHT:
            # Move highest notes from left to right
            overloaded.sort(key=lambda a: a.note.pitch, reverse=True)
        else:
            # Move lowest notes from right to left
            overloaded.sort(key=lambda a: a.note.pitch)

        # Move up to 2 notes
        for assignment in overloaded[:2]:
            assignment.hand = to_hand
            assignment.difficulty += 0.1  # Slight penalty for crossover

        return assignments

    def analyze_hands(self, piano_roll: PianoRoll) -> dict:
        """
        Analyze hand assignment distribution.

        Args:
            piano_roll: PianoRoll to analyze

        Returns:
            Dictionary with hand statistics
        """
        right_hand, left_hand = self.assign_hands(piano_roll)

        right_range = right_hand.get_pitch_range() if right_hand.notes else (0, 0)
        left_range = left_hand.get_pitch_range() if left_hand.notes else (0, 0)

        return {
            "total_notes": len(piano_roll.notes),
            "right_hand_notes": len(right_hand.notes),
            "left_hand_notes": len(left_hand.notes),
            "right_hand_percentage": (
                len(right_hand.notes) / len(piano_roll.notes) * 100
                if piano_roll.notes
                else 0
            ),
            "left_hand_percentage": (
                len(left_hand.notes) / len(piano_roll.notes) * 100
                if piano_roll.notes
                else 0
            ),
            "right_hand_range": right_range,
            "left_hand_range": left_range,
            "right_hand_avg_pitch": (
                np.mean([n.pitch for n in right_hand.notes]) if right_hand.notes else 0
            ),
            "left_hand_avg_pitch": (
                np.mean([n.pitch for n in left_hand.notes]) if left_hand.notes else 0
            ),
        }

    def detect_crossovers(
        self, right_hand: PianoRoll, left_hand: PianoRoll
    ) -> List[dict]:
        """
        Detect when hands cross over each other.

        Args:
            right_hand: Right hand notes
            left_hand: Left hand notes

        Returns:
            List of crossover events
        """
        crossovers = []

        for r_note in right_hand.notes:
            for l_note in left_hand.notes:
                # Check if they overlap in time
                if not (r_note.end <= l_note.start or l_note.end <= r_note.start):
                    # Check if left hand is higher than right
                    if l_note.pitch > r_note.pitch:
                        crossovers.append(
                            {
                                "time": r_note.start,
                                "right_pitch": r_note.pitch,
                                "left_pitch": l_note.pitch,
                                "amount": l_note.pitch - r_note.pitch,
                            }
                        )

        return crossovers


def assign_hands(piano_roll: PianoRoll) -> Tuple[PianoRoll, PianoRoll]:
    """
    Convenience function to assign hands.

    Args:
        piano_roll: PianoRoll to process

    Returns:
        Tuple of (right_hand_roll, left_hand_roll)
    """
    assigner = HandAssigner()
    return assigner.assign_hands(piano_roll)
