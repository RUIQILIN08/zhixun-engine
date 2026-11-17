"""CPU-first industrial drift baseline for the training-engine competition."""

from .data import load_cmapss, load_gas
from .modeling import (
    RidgeRegressor,
    SoftmaxRegression,
    Standardizer,
    classification_metrics,
    regression_metrics,
)

__all__ = [
    "RidgeRegressor",
    "SoftmaxRegression",
    "Standardizer",
    "classification_metrics",
    "load_cmapss",
    "load_gas",
    "regression_metrics",
]

