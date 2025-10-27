import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from .data_structures import Note, PianoRoll


@dataclass
class QuantizationConfig:
    """Configuration for rhythm quantization"""

    # Grid resolution options
    grid_resolution: str = "16th"  # '8th', '16th', '32nd', 'triplet'
    # Quantization strength (0.0 = no quantization, 1.0 = full snap)
    strength: float = 1.0
    # Minimum note duration (in beats)
    min_duration: float = 0.0625  # 1/16 note
    # Whether to quantize note offsets (endings) as well
    quantize_offsets: bool = True
    # Swing factor (0.0 = straight, 0.5 = maximum swing)
    swing: float = 0.0


class RhythmQuantizer:
    """
    Quantizes note timings to a musical grid.

    This is critical for converting expressive MIDI performances into
    readable sheet music notation.
    """

    # Grid size definitions (in fractions of a beat)
    GRID_SIZES = {
        "whole": 1.0,
        "half": 0.5,
        "quarter": 0.25,
        "8th": 0.125,
        "16th": 0.0625,
        "32nd": 0.03125,
        "triplet": 1 / 12,  # 8th note triplets
    }

    def __init__(self, config: Optional[QuantizationConfig] = None):
        """
        Initialize rhythm quantizer.

        Args:
            config: Quantization configuration. If None, uses defaults.
        """
        self.config = config or QuantizationConfig()
        self._validate_config()

    def _validate_config(self):
        """Validate configuration parameters"""
        if self.config.grid_resolution not in self.GRID_SIZES:
            raise ValueError(
                f"Invalid grid resolution: {self.config.grid_resolution}. "
                f"Must be one of: {list(self.GRID_SIZES.keys())}"
            )

        if not 0.0 <= self.config.strength <= 1.0:
            raise ValueError(
                f"Strength must be between 0 and 1, got {self.config.strength}"
            )

        if not 0.0 <= self.config.swing <= 0.5:
            raise ValueError(
                f"Swing must be between 0 and 0.5, got {self.config.swing}"
            )

    def quantize(self, piano_roll: PianoRoll) -> PianoRoll:
        """
        Quantize all notes in a piano roll.

        Args:
            piano_roll: Input PianoRoll to quantize

        Returns:
            New PianoRoll with quantized timing
        """
        if not piano_roll.notes:
            return piano_roll

        # Calculate timing parameters
        beat_duration = 60.0 / piano_roll.tempo  # seconds per beat
        grid_size_beats = self.GRID_SIZES[self.config.grid_resolution]
        grid_duration = beat_duration * grid_size_beats  # seconds per grid unit

        # Quantize each note
        quantized_notes = []
        for note in piano_roll.notes:
            q_note = self._quantize_note(note, grid_duration, beat_duration)
            quantized_notes.append(q_note)

        # Create new PianoRoll with quantized notes
        return PianoRoll(
            notes=quantized_notes,
            tempo=piano_roll.tempo,
            time_signature=piano_roll.time_signature,
            key_signature=piano_roll.key_signature,
        )

    def _quantize_note(
        self, note: Note, grid_duration: float, beat_duration: float
    ) -> Note:
        """
        Quantize a single note.

        Args:
            note: Note to quantize
            grid_duration: Duration of one grid unit in seconds
            beat_duration: Duration of one beat in seconds

        Returns:
            New Note with quantized timing
        """
        # Quantize start time
        quantized_start = self._quantize_time(note.start, grid_duration, beat_duration)

        # Quantize duration or offset
        if self.config.quantize_offsets:
            # Quantize the end time
            quantized_end = self._quantize_time(note.end, grid_duration, beat_duration)

            # Ensure minimum duration
            min_duration_seconds = self.config.min_duration * beat_duration
            if quantized_end - quantized_start < min_duration_seconds:
                quantized_end = quantized_start + min_duration_seconds
        else:
            # Keep original duration
            quantized_end = quantized_start + note.duration

        # Create quantized note
        return Note(
            pitch=note.pitch,
            start=quantized_start,
            end=quantized_end,
            velocity=note.velocity,
            note_type=note.note_type,
        )

    def _quantize_time(
        self, time: float, grid_duration: float, beat_duration: float
    ) -> float:
        """
        Quantize a single time value to the nearest grid position.

        Args:
            time: Time in seconds to quantize
            grid_duration: Grid spacing in seconds
            beat_duration: Beat duration in seconds

        Returns:
            Quantized time in seconds
        """
        # Find nearest grid position
        grid_position = round(time / grid_duration)
        snapped_time = grid_position * grid_duration

        # Apply swing if configured
        if self.config.swing > 0:
            snapped_time = self._apply_swing(snapped_time, grid_duration, beat_duration)

        # Apply quantization strength (blend between original and snapped)
        quantized_time = (
            time * (1 - self.config.strength) + snapped_time * self.config.strength
        )

        return max(0.0, quantized_time)  # Ensure non-negative

    def _apply_swing(
        self, time: float, grid_duration: float, beat_duration: float
    ) -> float:
        """
        Apply swing timing adjustment.

        Swing delays every second note in a pair (e.g., 8th notes).

        Args:
            time: Time to adjust
            grid_duration: Grid spacing
            beat_duration: Beat duration

        Returns:
            Time with swing applied
        """
        # Determine position within beat pair
        beat_pair_duration = grid_duration * 2
        position_in_pair = (time % beat_pair_duration) / beat_pair_duration

        # Apply swing to second note in pair
        if 0.4 < position_in_pair < 0.6:  # Second note
            swing_delay = self.config.swing * grid_duration
            return time + swing_delay

        return time

    def analyze_timing_distribution(self, piano_roll: PianoRoll) -> dict:
        """
        Analyze how far notes are from grid positions.
        Useful for determining if quantization is needed.

        Args:
            piano_roll: PianoRoll to analyze

        Returns:
            Dictionary with timing statistics
        """
        if not piano_roll.notes:
            return {}

        beat_duration = 60.0 / piano_roll.tempo
        grid_size_beats = self.GRID_SIZES[self.config.grid_resolution]
        grid_duration = beat_duration * grid_size_beats

        # Calculate deviation from grid for each note
        deviations = []
        for note in piano_roll.notes:
            # Distance to nearest grid point
            grid_position = round(note.start / grid_duration)
            grid_time = grid_position * grid_duration
            deviation = abs(note.start - grid_time)
            deviations.append(deviation)

        deviations = np.array(deviations)

        return {
            "mean_deviation": float(np.mean(deviations)),
            "max_deviation": float(np.max(deviations)),
            "std_deviation": float(np.std(deviations)),
            "grid_duration": grid_duration,
            "notes_analyzed": len(deviations),
            "percent_on_grid": float(
                np.sum(deviations < 0.001) / len(deviations) * 100
            ),
        }


def quantize_piano_roll(
    piano_roll: PianoRoll, grid_resolution: str = "16th", strength: float = 1.0
) -> PianoRoll:
    """
    Convenience function to quantize a piano roll.

    Args:
        piano_roll: PianoRoll to quantize
        grid_resolution: Grid size ('8th', '16th', '32nd', 'triplet')
        strength: Quantization strength (0.0 to 1.0)

    Returns:
        Quantized PianoRoll
    """
    config = QuantizationConfig(grid_resolution=grid_resolution, strength=strength)
    quantizer = RhythmQuantizer(config)
    return quantizer.quantize(piano_roll)
