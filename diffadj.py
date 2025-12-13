"""
Test script for Difficulty Adjuster.
Shows before and after comparison of difficulty adjustment.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from autoscribe import load_midi
from autoscribe.core.difficulty_adjuster import (
    DifficultyAdjuster, 
    DifficultyConfig, 
    DifficultyLevel,
    adjust_difficulty
)
from autoscribe.core.musicxml_exporter import export_to_musicxml
import matplotlib.pyplot as plt


def visualize_difficulty_comparison(original, adjusted, title="Difficulty Adjustment"):
    """
    Visualize original vs adjusted difficulty.
    
    Args:
        original: Original PianoRoll
        adjusted: Adjusted PianoRoll
        title: Plot title
    """