from __future__ import annotations

import math


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (small samples; no interpolation guessing)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if pct <= 0:
        return ordered[0]
    if pct >= 100:
        return ordered[-1]
    return ordered[max(1, math.ceil(pct / 100 * len(ordered))) - 1]
