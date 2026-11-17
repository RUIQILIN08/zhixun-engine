"""Run deterministic CPU baselines on the official public datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from zhixun_engine import (  # noqa: E402
    RidgeRegressor,
    SoftmaxRegression,
    classification_metrics,
    load_cmapss,
    load_gas,
    regression_metrics,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def run_gas() -> dict[str, Any]:
    data_path = ROOT / "data" / "raw" / "gas" / "gas.zip"
    started = time.perf_counter()
    dataset = load_gas(data_path)
    X = dataset["X"]
    y = dataset["y"]
    batch = dataset["batch"]

    train_mask = batch == 1
    model = SoftmaxRegression()
    model.fit(X[train_mask], y[train_mask])

    evaluation_mask = batch >= 2
    predictions = model.predict(X[evaluation_mask])
    y_eval = y[evaluation_mask]
    batches_eval = batch[evaluation_mask]
    summary = classification_metrics(y_eval, predictions)

    by_batch: dict[str, Any] = {}
    for batch_id in range(2, 11):
        mask = batches_eval == batch_id
        by_batch[str(batch_id)] = {
            "rows": int(mask.sum()),
            **classification_metrics(y_eval[mask], predictions[mask]),
        }

    prediction_path = ROOT / "results" / "gas_predictions.csv"
    prediction_path.parent.mkdir(parents=True, exist_ok=True)
    with prediction_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["batch_id", "y_true", "y_pred", "correct"])
        for batch_id, expected, actual in zip(
            batches_eval, y_eval, predictions, strict=True
        ):
            writer.writerow(
                [int(batch_id), int(expected), int(actual), int(expected == actual)]
            )

    payload = {
        "experiment_id": "gas_batch1_to_batch2_10_softmax_v1",
        "task": "gas",
        "split_warning": (
            "Local smoke-test split: batch 1 train, batches 2-10 evaluation. "
            "It is not the official platform split."
        ),
        "input": {
            "path": str(data_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(data_path),
            "rows": int(len(y)),
            "features": int(X.shape[1]),
            "batch_counts": dataset["batch_counts"],
        },
        "model": {
            "type": "multinomial logistic regression",
            "epochs": model.epochs,
            "learning_rate": model.learning_rate,
            "l2": model.l2,
            "balanced_sample_weights": model.balanced,
            "final_loss": model.loss_history[-1],
        },
        "metrics": summary,
        "by_batch": by_batch,
        "output": {
            "predictions": str(prediction_path.relative_to(ROOT)).replace("\\", "/"),
            "predictions_sha256": sha256(prediction_path),
        },
        "elapsed_seconds": time.perf_counter() - started,
    }
    write_json(ROOT / "results" / "gas_metrics.json", payload)
    return payload


def _cmapss_training_matrix(
    train: np.ndarray, *, rul_cap: float = 125.0
) -> tuple[np.ndarray, np.ndarray]:
    features = train[:, 2:26]
    unit = train[:, 0]
    cycle = train[:, 1]
    max_cycle = {
        int(value): float(cycle[unit == value].max())
        for value in np.unique(unit)
    }
    remaining = np.asarray(
        [max_cycle[int(value)] - float(current) for value, current in zip(unit, cycle)],
        dtype=np.float32,
    )
    return features, np.minimum(remaining, rul_cap)


def _last_cycle_rows(test: np.ndarray) -> np.ndarray:
    rows: list[np.ndarray] = []
    for unit_id in np.unique(test[:, 0]):
        unit_rows = test[test[:, 0] == unit_id]
        rows.append(unit_rows[int(np.argmax(unit_rows[:, 1]))])
    return np.vstack(rows)


def run_cmapss(subset: str) -> dict[str, Any]:
    data_path = ROOT / "data" / "raw" / "cmapss" / "cmapss.zip"
    started = time.perf_counter()
    dataset = load_cmapss(data_path, subset)
    X_train, y_train = _cmapss_training_matrix(dataset["train"])
    test_last = _last_cycle_rows(dataset["test"])
    X_test = test_last[:, 2:26]
    y_test = dataset["test_rul"]

    model = RidgeRegressor(l2=10.0)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    metrics = regression_metrics(y_test, predictions)

    prediction_path = ROOT / "results" / f"cmapss_{subset}_predictions.csv"
    prediction_path.parent.mkdir(parents=True, exist_ok=True)
    with prediction_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["unit_id", "y_true_rul", "y_pred_rul", "absolute_error"])
        for unit_id, expected, actual in zip(
            dataset["test_units"], y_test, predictions, strict=True
        ):
            writer.writerow(
                [
                    int(unit_id),
                    float(expected),
                    float(actual),
                    float(abs(expected - actual)),
                ]
            )

    payload = {
        "experiment_id": f"cmapss_{subset}_ridge_v1",
        "task": "cmapss",
        "subset": subset,
        "split_warning": (
            "Uses the official CMAPSS train/test files. RUL labels for training "
            "are reconstructed as final_cycle-current_cycle and capped at 125."
        ),
        "input": {
            "path": str(data_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(data_path),
            "train_rows": int(dataset["train"].shape[0]),
            "test_rows": int(dataset["test"].shape[0]),
            "train_units": int(len(dataset["train_units"])),
            "test_units": int(len(dataset["test_units"])),
        },
        "model": {
            "type": "ridge regression",
            "l2": model.l2,
            "rul_cap": 125.0,
        },
        "metrics": metrics,
        "output": {
            "predictions": str(prediction_path.relative_to(ROOT)).replace("\\", "/"),
            "predictions_sha256": sha256(prediction_path),
        },
        "elapsed_seconds": time.perf_counter() - started,
    }
    write_json(ROOT / "results" / f"cmapss_{subset}_metrics.json", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["gas", "cmapss"], required=True)
    parser.add_argument("--subset", default="FD001")
    args = parser.parse_args()

    if args.task == "gas":
        result = run_gas()
        print("[OK] gas metrics:", json.dumps(result["metrics"], indent=2))
        print("[OK] output:", ROOT / "results" / "gas_metrics.json")
    else:
        result = run_cmapss(args.subset)
        print("[OK] cmapss metrics:", json.dumps(result["metrics"], indent=2))
        print(
            "[OK] output:",
            ROOT / "results" / f"cmapss_{args.subset.upper()}_metrics.json",
        )


if __name__ == "__main__":
    main()

