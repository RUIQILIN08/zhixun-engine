"""Quantified promotion gates for champion vs challenger."""

from __future__ import annotations

import os


def metric_delta(candidate: dict, parent: dict, task: dict) -> float | None:
    metric = task.get("metric", "macro_f1")
    direction = str(task.get("metric_direction", "higher")).lower()
    candidate_value = candidate.get(metric)
    parent_value = parent.get(metric)
    if candidate_value is None or parent_value is None:
        return None
    delta = float(candidate_value) - float(parent_value)
    if direction in ("lower", "min", "minimize", "down"):
        return -delta
    return delta


def evaluate_gates(
    candidate: dict,
    parent: dict,
    task: dict,
    training_seconds: float,
    model_total_tokens: int,
) -> dict:
    direction = str(task.get("metric_direction", "higher")).lower()
    metric = task.get("metric", "macro_f1")
    delta = metric_delta(candidate, parent, task)
    gate1_pass = delta is not None and delta > 0

    cost = float(training_seconds) + float(max(int(model_total_tokens), 0))
    gain_per_cost = (delta / cost) if delta is not None and cost > 0 else 0.0
    threshold = float(os.environ.get("GATE2_MIN_GAIN_PER_COST", "0.0"))
    gate2_pass = gate1_pass and gain_per_cost >= threshold

    return {
        "metric": metric,
        "direction": direction,
        "gate1_pass": gate1_pass,
        "gate2_pass": gate2_pass,
        "delta": delta,
        "cost": cost,
        "training_seconds": training_seconds,
        "model_total_tokens": model_total_tokens,
        "gain_per_cost": gain_per_cost,
        "threshold": threshold,
    }

