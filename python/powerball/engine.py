"""Core analysis and prediction engine for Powerball numbers."""

import random
from collections import Counter
from typing import List, Tuple, Dict

import numpy as np

from .data_loader import load_draws, DATE_COL, N1_COL, N2_COL, N3_COL, N4_COL, N5_COL, PB_COL

# Powerball ranges
WHITE_MIN, WHITE_MAX = 1, 69
POWERBALL_MIN, POWERBALL_MAX = 1, 26
NUM_WHITE = 5


def _extract_white_numbers(draws: List[dict]) -> List[int]:
    nums = []
    for d in draws:
        nums.extend([d[N1_COL], d[N2_COL], d[N3_COL], d[N4_COL], d[N5_COL]])
    return nums


def _extract_powerballs(draws: List[dict]) -> List[int]:
    return [d[PB_COL] for d in draws]


def frequency_analysis(draws: List[dict]) -> Tuple[Dict[int, int], Dict[int, int]]:
    """Analyze frequency of white balls and Powerballs.

    Returns:
        (white_freq, powerball_freq) — each is dict mapping number -> count.
    """
    white_nums = _extract_white_numbers(draws)
    pb_nums = _extract_powerballs(draws)
    white_freq = dict(Counter(white_nums))
    pb_freq = dict(Counter(pb_nums))
    for n in range(WHITE_MIN, WHITE_MAX + 1):
        white_freq.setdefault(n, 0)
    for n in range(POWERBALL_MIN, POWERBALL_MAX + 1):
        pb_freq.setdefault(n, 0)
    return white_freq, pb_freq


def hot_numbers(freq: Dict[int, int], top_n: int = 15) -> List[Tuple[int, int]]:
    """Return the most frequently drawn numbers (hot)."""
    return sorted(freq.items(), key=lambda x: -x[1])[:top_n]


def cold_numbers(freq: Dict[int, int], top_n: int = 15) -> List[Tuple[int, int]]:
    """Return the least frequently drawn numbers (cold)."""
    return sorted(freq.items(), key=lambda x: x[1])[:top_n]


def due_numbers(draws: List[dict]) -> Tuple[List[int], List[int]]:
    """Find numbers that haven't appeared in the longest time.

    Returns:
        (due_white, due_powerball) — lists sorted by most overdue.
    """
    white_nums = _extract_white_numbers(draws)
    pb_nums = _extract_powerballs(draws)

    white_last = {}
    for i, n in enumerate(reversed(white_nums)):
        if n not in white_last:
            white_last[n] = i
    pb_last = {}
    for i, n in enumerate(reversed(pb_nums)):
        if n not in pb_last:
            pb_last[n] = i

    due_white = sorted(
        range(WHITE_MIN, WHITE_MAX + 1),
        key=lambda n: white_last.get(n, -1), reverse=True,
    )
    due_pb = sorted(
        range(POWERBALL_MIN, POWERBALL_MAX + 1),
        key=lambda n: pb_last.get(n, -1), reverse=True,
    )
    return due_white, due_pb


def generate_prediction(
    draws: List[dict],
    strategy: str = "balanced",
    num_predictions: int = 5,
) -> List[Dict]:
    """Generate Powerball predictions based on historical analysis.

    Strategies:
        - "balanced": Weighted random favoring hot numbers slightly.
        - "hot": Strongly favors most frequently drawn numbers.
        - "cold": Favors least frequently drawn (cold) numbers.
        - "random": Pure random selection (no analysis weighting).
    """
    if not draws:
        return [_random_prediction() | {"strategy": strategy} for _ in range(num_predictions)]

    white_freq, pb_freq = frequency_analysis(draws)

    predictions = []
    for _ in range(num_predictions):
        if strategy == "random":
            pred = _random_prediction()
        elif strategy == "hot":
            pred = _weighted_prediction(white_freq, pb_freq, exponent=2.5)
        elif strategy == "cold":
            pred = _weighted_prediction(white_freq, pb_freq, exponent=-1.5)
        else:  # balanced
            pred = _weighted_prediction(white_freq, pb_freq, exponent=1.2)
        pred["strategy"] = strategy
        predictions.append(pred)

    return predictions


def _random_prediction() -> Dict:
    """Generate a pure random prediction."""
    white = sorted(random.sample(range(WHITE_MIN, WHITE_MAX + 1), NUM_WHITE))
    powerball = random.randint(POWERBALL_MIN, POWERBALL_MAX)
    return {"white": white, "powerball": powerball}


def _weighted_prediction(white_freq, pb_freq, exponent=1.0) -> Dict:
    """Generate prediction using weighted random selection with an exponent bias."""
    white_nums = np.arange(WHITE_MIN, WHITE_MAX + 1)
    pb_nums = np.arange(POWERBALL_MIN, POWERBALL_MAX + 1)

    def calculate_probs(freq_dict, nums, exp):
        counts = np.array([freq_dict.get(n, 0) for n in nums], dtype=float)
        # Add a small epsilon to avoid zero weights, especially for negative exponents
        weights = (counts + 0.1) ** exp
        return weights / weights.sum()

    white_probs = calculate_probs(white_freq, white_nums, exponent)
    pb_probs = calculate_probs(pb_freq, pb_nums, exponent)

    selected_white = np.random.choice(white_nums, size=NUM_WHITE, replace=False, p=white_probs)
    selected_pb = np.random.choice(pb_nums, p=pb_probs)

    return {"white": sorted(selected_white.tolist()), "powerball": int(selected_pb)}

def analyze_draws(draws: List[dict]) -> Dict:
    """Return a comprehensive analysis report of historical draws.

    Returns dict with keys: total_draws, white_freq, pb_freq,
    hot_white, cold_white, hot_pb, cold_pb, due_white, due_pb,
    top_pairs, date_range.
    """
    white_freq, pb_freq = frequency_analysis(draws)
    pairs = Counter()
    for d in draws:
        whites = sorted([d[N1_COL], d[N2_COL], d[N3_COL], d[N4_COL], d[N5_COL]])
        for i in range(len(whites)):
            for j in range(i + 1, len(whites)):
                pairs[(whites[i], whites[j])] += 1

    due_white, due_pb = due_numbers(draws)
    dates = [d[DATE_COL] for d in draws]

    hot_w = hot_numbers(white_freq, 15)
    cold_w = cold_numbers(white_freq, 15)
    hot_p = hot_numbers(pb_freq, 10)
    cold_p = cold_numbers(pb_freq, 10)

    all_white = _extract_white_numbers(draws)
    all_pb = _extract_powerballs(draws)
    avg_w = sum(all_white) / len(all_white) if all_white else 0
    avg_p = sum(all_pb) / len(all_pb) if all_pb else 0

    return {
        "total_draws": len(draws),
        "date_range": (min(dates), max(dates)),
        "span": f"{min(dates)} to {max(dates)}",
        "white_freq": white_freq,
        "pb_freq": pb_freq,
        "white_freq_list": [white_freq.get(n, 0) for n in range(WHITE_MIN, WHITE_MAX + 1)],
        "pb_freq_list": [pb_freq.get(n, 0) for n in range(POWERBALL_MIN, POWERBALL_MAX + 1)],
        "powerball_freq": [pb_freq.get(n, 0) for n in range(POWERBALL_MIN, POWERBALL_MAX + 1)],  # alias for templates
        "hot_white": hot_w,
        "cold_white": cold_w,
        "hot_pb": hot_p,
        "cold_pb": cold_p,
        "hot_powerball": [n for n, _ in hot_p[:10]],  # alias for templates
        "cold_powerball": [n for n, _ in cold_p[:10]],  # alias for templates
        "due_white": due_white[:15],
        "due_pb": due_pb[:10],
        "top_pairs": pairs.most_common(20),
        "most_common_pb": hot_p[0][0] if hot_p else None,
        "avg_white": round(avg_w, 1),
        "avg_powerball": round(avg_p, 1),
    }

