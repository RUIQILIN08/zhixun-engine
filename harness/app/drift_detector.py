"""Lightweight input-drift signal computed without labels or future data."""

from __future__ import annotations

import numpy as np

from baselines.data import read_dataset


def compute_feature_drift(
    train_path: str,
    validation_path: str,
    task: str,
    classes: list[str],
) -> dict:
    """Compare training and validation feature means using training std."""

    train = read_dataset(train_path, task, classes)
    validation = read_dataset(
        validation_path, task, classes, expected_paths=train["paths"]
    )
    x_train = np.asarray(train["x"], dtype=np.float64)
    x_validation = np.asarray(validation["x"], dtype=np.float64)

    mean_train = x_train.mean(axis=0)
    std_train = x_train.std(axis=0)
    mean_validation = x_validation.mean(axis=0)
    epsilon = 1e-9
    shift = np.abs(mean_validation - mean_train) / (std_train + epsilon)
    max_index = int(np.argmax(shift))

    return {
        "score": float(np.mean(shift)),
        "max_feature_index": max_index,
        "max_feature_shift": float(shift[max_index]),
        "train_rows": int(x_train.shape[0]),
        "validation_rows": int(x_validation.shape[0]),
    }

