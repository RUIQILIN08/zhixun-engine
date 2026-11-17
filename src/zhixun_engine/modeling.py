"""Deterministic CPU models and metrics with small memory footprints."""

from __future__ import annotations

from typing import Any

import numpy as np


class Standardizer:
    """Standardize active non-constant features using fit data only."""

    def __init__(self) -> None:
        self.mean: np.ndarray | None = None
        self.scale: np.ndarray | None = None
        self.active: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "Standardizer":
        if X.ndim != 2:
            raise ValueError("X must be two-dimensional")
        mean = X.mean(axis=0)
        scale = X.std(axis=0)
        self.active = scale > max(float(scale.max()) * 1e-9, 1e-12)
        self.mean = mean[self.active]
        self.scale = scale[self.active]
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.mean is None or self.scale is None or self.active is None:
            raise RuntimeError("Standardizer must be fitted before transform")
        selected = X[:, self.active]
        return ((selected - self.mean) / self.scale).astype(np.float32)


class SoftmaxRegression:
    """Small deterministic multinomial logistic model optimized with Adam."""

    def __init__(
        self,
        *,
        epochs: int = 240,
        learning_rate: float = 0.03,
        l2: float = 1e-3,
        balanced: bool = True,
    ) -> None:
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.l2 = l2
        self.balanced = balanced
        self.scaler = Standardizer()
        self.weights: np.ndarray | None = None
        self.classes: np.ndarray | None = None
        self.loss_history: list[float] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SoftmaxRegression":
        X_scaled = self.scaler.fit(X).transform(X)
        Xb = np.column_stack([np.ones(len(X_scaled)), X_scaled])
        self.classes = np.unique(y)
        class_to_index = {value: index for index, value in enumerate(self.classes)}
        y_index = np.asarray([class_to_index[value] for value in y])

        targets = np.zeros((len(y), len(self.classes)), dtype=np.float32)
        targets[np.arange(len(y)), y_index] = 1.0

        sample_weights = np.ones(len(y), dtype=np.float32)
        if self.balanced:
            counts = targets.sum(axis=0)
            class_weights = len(y) / (len(self.classes) * counts)
            sample_weights = class_weights[y_index].astype(np.float32)
        sample_weights /= sample_weights.mean()

        weights = np.zeros((Xb.shape[1], len(self.classes)), dtype=np.float32)
        first_moment = np.zeros_like(weights)
        second_moment = np.zeros_like(weights)
        beta1 = 0.9
        beta2 = 0.999
        epsilon = 1e-8

        for step in range(1, self.epochs + 1):
            logits = Xb @ weights
            logits -= logits.max(axis=1, keepdims=True)
            exp_logits = np.exp(logits)
            probabilities = exp_logits / exp_logits.sum(axis=1, keepdims=True)

            weighted_targets = targets * sample_weights[:, None]
            weighted_probabilities = probabilities * sample_weights[:, None]
            loss = -(
                weighted_targets * np.log(np.maximum(probabilities, 1e-12))
            ).sum() / len(y)
            loss += 0.5 * self.l2 * float(np.square(weights[1:]).sum())
            self.loss_history.append(float(loss))

            gradient = Xb.T @ (weighted_probabilities - weighted_targets)
            gradient /= len(y)
            gradient[1:] += self.l2 * weights[1:]

            first_moment = beta1 * first_moment + (1 - beta1) * gradient
            second_moment = beta2 * second_moment + (1 - beta2) * gradient**2
            corrected_first = first_moment / (1 - beta1**step)
            corrected_second = second_moment / (1 - beta2**step)
            weights -= (
                self.learning_rate
                * corrected_first
                / (np.sqrt(corrected_second) + epsilon)
            )

        self.weights = weights
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.weights is None or self.classes is None:
            raise RuntimeError("SoftmaxRegression must be fitted before predict")
        Xb = np.column_stack([np.ones(len(X)), self.scaler.transform(X)])
        scores = Xb @ self.weights
        return self.classes[np.argmax(scores, axis=1)]


class RidgeRegressor:
    """Closed-form ridge regression followed by non-negative clipping."""

    def __init__(self, *, l2: float = 1.0) -> None:
        self.l2 = l2
        self.scaler = Standardizer()
        self.weights: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RidgeRegressor":
        X_scaled = self.scaler.fit(X).transform(X)
        Xb = np.column_stack([np.ones(len(X_scaled)), X_scaled])
        penalty = np.eye(Xb.shape[1], dtype=np.float32) * self.l2
        penalty[0, 0] = 0.0
        self.weights = np.linalg.solve(
            Xb.T @ Xb + penalty, Xb.T @ y.astype(np.float32)
        )
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.weights is None:
            raise RuntimeError("RidgeRegressor must be fitted before predict")
        Xb = np.column_stack([np.ones(len(X)), self.scaler.transform(X)])
        return np.maximum(Xb @ self.weights, 0.0)


def classification_metrics(
    y_true: np.ndarray, y_pred: np.ndarray
) -> dict[str, Any]:
    classes = np.unique(np.concatenate([y_true, y_pred]))
    recalls: list[float] = []
    f1_scores: list[float] = []
    per_class: dict[str, dict[str, float | int]] = {}

    for label in classes:
        true_positive = int(np.sum((y_true == label) & (y_pred == label)))
        false_positive = int(np.sum((y_true != label) & (y_pred == label)))
        false_negative = int(np.sum((y_true == label) & (y_pred != label)))
        support = int(np.sum(y_true == label))
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        recalls.append(recall)
        f1_scores.append(f1)
        per_class[str(int(label))] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    return {
        "accuracy": float(np.mean(y_true == y_pred)),
        "balanced_accuracy": float(np.mean(recalls)),
        "macro_f1": float(np.mean(f1_scores)),
        "per_class": per_class,
    }


def regression_metrics(
    y_true: np.ndarray, y_pred: np.ndarray
) -> dict[str, float]:
    error = y_pred.astype(np.float64) - y_true.astype(np.float64)
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "max_absolute_error": float(np.max(np.abs(error))),
    }

