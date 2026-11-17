from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from zhixun_engine import (  # noqa: E402
    SoftmaxRegression,
    classification_metrics,
    load_cmapss,
    load_gas,
    regression_metrics,
)


class DatasetContractTest(unittest.TestCase):
    def test_gas_contract(self) -> None:
        dataset = load_gas(ROOT / "data" / "raw" / "gas" / "gas.zip")
        self.assertEqual(dataset["X"].shape, (13910, 128))
        self.assertEqual(len(dataset["y"]), 13910)
        self.assertEqual(sorted(dataset["batch_counts"]), list(range(1, 11)))
        self.assertEqual(set(np.unique(dataset["y"])), set(range(1, 7)))

    def test_cmapss_contract(self) -> None:
        dataset = load_cmapss(
            ROOT / "data" / "raw" / "cmapss" / "cmapss.zip", "FD001"
        )
        self.assertEqual(dataset["train"].shape[1], 26)
        self.assertEqual(dataset["test"].shape[1], 26)
        self.assertEqual(len(dataset["train_units"]), 100)
        self.assertEqual(len(dataset["test_units"]), 100)
        self.assertEqual(dataset["test_rul"].shape, (100,))


class MetricsTest(unittest.TestCase):
    def test_classification_metrics(self) -> None:
        result = classification_metrics(
            np.asarray([0, 0, 1, 1]), np.asarray([0, 1, 1, 1])
        )
        self.assertAlmostEqual(result["accuracy"], 0.75)
        self.assertAlmostEqual(result["balanced_accuracy"], 0.75)

    def test_regression_metrics(self) -> None:
        result = regression_metrics(
            np.asarray([1.0, 2.0]), np.asarray([2.0, 2.0])
        )
        self.assertAlmostEqual(result["mae"], 0.5)
        self.assertAlmostEqual(result["rmse"], float(np.sqrt(0.5)))

    def test_softmax_smoke(self) -> None:
        X = np.asarray(
            [[-2.0, -1.0], [-1.0, -2.0], [1.0, 2.0], [2.0, 1.0]],
            dtype=np.float32,
        )
        y = np.asarray([0, 0, 1, 1])
        model = SoftmaxRegression(epochs=80, learning_rate=0.05)
        predictions = model.fit(X, y).predict(X)
        self.assertGreaterEqual(np.mean(predictions == y), 0.75)


if __name__ == "__main__":
    unittest.main()

