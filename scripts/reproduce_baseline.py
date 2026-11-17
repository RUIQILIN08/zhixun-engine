"""Reproduce the supplied CPU baseline on public validation, without training.

The official packages mark their results as development references, not
official platform scores. This script loads the supplied checkpoint unchanged
and re-computes the same metrics on public validation so the team has a
traceable local reproduction before starting any iteration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_baselines(package_root: Path) -> tuple[object, object]:
    """Import one official package's baselines package without bytecode writes."""

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(package_root))
    from baselines.data import read_dataset
    from baselines.model import Model

    return read_dataset, Model


def classification_metrics(
    model: object, validation: dict
) -> dict[str, float]:
    predicted = model.predict(validation["x"])
    labels = predicted.argmax(axis=1)
    expected = validation["y"]
    observed = sorted(set(expected.tolist()) | set(labels.tolist()))
    f1_values = []
    for label in observed:
        true_positive = int(np.sum((labels == label) & (expected == label)))
        predicted_positive = int(np.sum(labels == label))
        expected_positive = int(np.sum(expected == label))
        denominator = predicted_positive + expected_positive
        f1_values.append(
            2 * true_positive / denominator if denominator else 0.0
        )
    return {
        "accuracy": float(np.mean(labels == expected)),
        "macro_f1": float(np.mean(f1_values)),
    }


def regression_metrics(model: object, validation: dict) -> dict[str, float]:
    predicted = np.asarray(model.predict(validation["x"])).ravel()
    error = predicted - validation["y"]
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package",
        default=str(ROOT / "platform" / "packages" / "A"),
        help="Root directory of one official baseline package.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Directory for the reproduction report. Defaults under platform/reproduction.",
    )
    args = parser.parse_args()

    package_root = Path(args.package)
    checkpoint_path = package_root / "checkpoint.npz"
    train_path = package_root / "public" / "train.jsonl"
    validation_path = package_root / "public" / "validation.jsonl"
    baseline_info_path = package_root / "baseline-info.json"
    training_path = package_root / "training.json"

    for path in (
        checkpoint_path,
        train_path,
        validation_path,
        baseline_info_path,
        training_path,
    ):
        if not path.exists():
            raise FileNotFoundError(f"missing required file: {path}")

    baseline_info = json.loads(baseline_info_path.read_text(encoding="utf-8"))
    training_report = json.loads(training_path.read_text(encoding="utf-8"))
    profile = baseline_info.get("dataset_key")
    if profile is None:
        profile = training_report.get("profile")

    output_root = Path(args.output) if args.output else (
        ROOT / "platform" / "reproduction" / str(profile)
    )
    output_root.mkdir(parents=True, exist_ok=True)

    read_dataset, Model = import_baselines(package_root)
    model = Model.load(checkpoint_path)
    model.validate()
    validation = read_dataset(
        validation_path,
        model.meta["task"],
        model.meta["classes"],
        model.meta["paths"],
    )

    if model.meta["task"] == "classification":
        metrics = classification_metrics(model, validation)
    elif model.meta["task"] == "regression":
        metrics = regression_metrics(model, validation)
    else:
        raise ValueError(f"unsupported task: {model.meta['task']!r}")

    expected = training_report.get("validation_after", {})
    comparison = {}
    for key, value in metrics.items():
        if key in expected:
            comparison[key] = {
                "expected": expected[key],
                "reproduced": value,
                "absolute_difference": value - float(expected[key]),
            }

    report = {
        "format": "local-baseline-reproduction.v1",
        "package_root": str(package_root),
        "profile": profile,
        "baseline_id": baseline_info.get("id"),
        "baseline_label_status": baseline_info.get("label_status"),
        "official_scoring_ready": training_report.get(
            "official_scoring_ready", False
        ),
        "purpose": training_report.get("purpose"),
        "method": "load supplied checkpoint unchanged; predict public validation",
        "checkpoint": {
            "path": str(checkpoint_path),
            "sha256": sha256(checkpoint_path),
        },
        "validation": {
            "path": str(validation_path),
            "sha256": sha256(validation_path),
            "rows": len(validation["ids"]),
        },
        "metrics": metrics,
        "comparison_to_packaged_report": comparison,
    }

    report_path = output_root / "reproduction.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    print(f"[OK] report: {report_path}")


if __name__ == "__main__":
    main()

