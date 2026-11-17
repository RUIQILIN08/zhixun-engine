"""Read the official public datasets without changing their raw files."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np


GAS_BATCH_RE = re.compile(r"(?:^|/)batch(\d+)\.dat$", re.IGNORECASE)
GAS_FEATURE_COUNT = 128
GAS_CLASS_NAMES = {
    1: "Ethanol",
    2: "Ethylene",
    3: "Ammonia",
    4: "Acetaldehyde",
    5: "Acetone",
    6: "Toluene",
}
CMAPSS_SUBSETS = {"FD001", "FD002", "FD003", "FD004"}


def _gas_members(archive: zipfile.ZipFile) -> dict[int, str]:
    members: dict[int, str] = {}
    for member in archive.namelist():
        match = GAS_BATCH_RE.search(member)
        if match is None:
            continue
        batch_id = int(match.group(1))
        if batch_id in members:
            raise ValueError(f"Duplicate gas batch {batch_id}")
        members[batch_id] = member

    expected = set(range(1, 11))
    if set(members) != expected:
        raise ValueError(
            f"Expected gas batches 1..10, found {sorted(members)}"
        )
    return members


def _parse_gas_line(
    line: str, *, batch_id: int, line_number: int
) -> tuple[int, np.ndarray]:
    tokens = line.split()
    if len(tokens) != GAS_FEATURE_COUNT + 1:
        raise ValueError(
            f"Gas batch {batch_id}, line {line_number}: expected "
            f"{GAS_FEATURE_COUNT + 1} tokens, found {len(tokens)}"
        )

    label = int(tokens[0])
    if label not in GAS_CLASS_NAMES:
        raise ValueError(
            f"Gas batch {batch_id}, line {line_number}: invalid class {label}"
        )

    values = np.empty(GAS_FEATURE_COUNT, dtype=np.float32)
    seen = np.zeros(GAS_FEATURE_COUNT, dtype=bool)
    for token in tokens[1:]:
        feature_text, value_text = token.split(":", maxsplit=1)
        feature_id = int(feature_text)
        if not 1 <= feature_id <= GAS_FEATURE_COUNT:
            raise ValueError(
                f"Gas batch {batch_id}, line {line_number}: "
                f"invalid feature id {feature_id}"
            )
        index = feature_id - 1
        if seen[index]:
            raise ValueError(
                f"Gas batch {batch_id}, line {line_number}: "
                f"duplicate feature id {feature_id}"
            )
        values[index] = float(value_text)
        seen[index] = True

    if not seen.all():
        missing = np.flatnonzero(~seen)[:10] + 1
        raise ValueError(
            f"Gas batch {batch_id}, line {line_number}: "
            f"missing features {missing.tolist()}"
        )
    return label, values


def load_gas(path: str | Path) -> dict[str, Any]:
    """Load and validate the UCI gas-drift ZIP.

    The returned arrays preserve the original order within each batch.
    """

    path = Path(path)
    features: list[np.ndarray] = []
    labels: list[int] = []
    batches: list[int] = []
    batch_counts: dict[int, int] = {}

    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise ValueError(f"Corrupt gas archive member: {corrupt}")

        for batch_id, member in sorted(_gas_members(archive).items()):
            text = archive.read(member).decode("utf-8")
            count = 0
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                label, row = _parse_gas_line(
                    line, batch_id=batch_id, line_number=line_number
                )
                features.append(row)
                labels.append(label)
                batches.append(batch_id)
                count += 1
            batch_counts[batch_id] = count

    return {
        "X": np.vstack(features),
        "y": np.asarray(labels, dtype=np.int64),
        "batch": np.asarray(batches, dtype=np.int64),
        "batch_counts": batch_counts,
        "class_names": GAS_CLASS_NAMES,
        "source": "UCI Gas Sensor Array Drift Dataset (DOI 10.24432/C5RP6W)",
    }


def _read_numeric_member(
    archive: zipfile.ZipFile, member: str
) -> np.ndarray:
    raw = archive.read(member)
    return np.loadtxt(io.BytesIO(raw), dtype=np.float32)


def load_cmapss(path: str | Path, subset: str = "FD001") -> dict[str, Any]:
    """Load one CMAPSS subset and its official test RUL vector."""

    subset = subset.upper()
    if subset not in CMAPSS_SUBSETS:
        raise ValueError(f"subset must be one of {sorted(CMAPSS_SUBSETS)}")

    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise ValueError(f"Corrupt CMAPSS archive member: {corrupt}")
        train = _read_numeric_member(archive, f"train_{subset}.txt")
        test = _read_numeric_member(archive, f"test_{subset}.txt")
        test_rul = _read_numeric_member(archive, f"RUL_{subset}.txt")

    if train.ndim != 2 or train.shape[1] != 26:
        raise ValueError(f"Unexpected train shape: {train.shape}")
    if test.ndim != 2 or test.shape[1] != 26:
        raise ValueError(f"Unexpected test shape: {test.shape}")
    if test_rul.ndim != 1:
        raise ValueError(f"Unexpected RUL shape: {test_rul.shape}")

    train_units = np.unique(train[:, 0]).astype(np.int64)
    test_units = np.unique(test[:, 0]).astype(np.int64)
    if len(test_units) != len(test_rul):
        raise ValueError(
            f"{subset}: {len(test_units)} test units but "
            f"{len(test_rul)} RUL values"
        )

    return {
        "train": train,
        "test": test,
        "test_rul": test_rul.astype(np.float32),
        "train_units": train_units,
        "test_units": test_units,
        "subset": subset,
        "source": "NASA C-MAPSS turbofan degradation simulation",
    }

