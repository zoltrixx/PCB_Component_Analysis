# utils.py
import math
from typing import Tuple

def distance(a: Tuple[float,float], b: Tuple[float,float]) -> float:
    return math.hypot(a[0]-b[0], a[1]-b[1])

# Include rect_overlap, line_segment_intersects_rect etc if you want to split code.
