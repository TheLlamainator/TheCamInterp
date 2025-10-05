"""
Placeholder for future NVIDIA FRUC integration.
For MVP we do pass-through or simple blend for the mid frame.
"""

import numpy as np
import cv2

def mid_duplicate(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return previous frame as the MID (safe, zero-cost)."""
    return a

def mid_blend(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Simple linear blend for a smoother mid frame (not true motion interpolation)."""
    # Ensure same size/dtype
    if a.shape != b.shape or a.dtype != b.dtype:
        raise ValueError("Frame shape/dtype mismatch")
    return cv2.addWeighted(a, 0.5, b, 0.5, 0.0)
