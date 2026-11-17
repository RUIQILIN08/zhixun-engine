from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "harness" / "app"
SDK = ROOT / "platform" / "sdk" / "contest-harness-sdk-1.0.2"
sys.path.insert(0, str(APP))
sys.path.insert(0, str(SDK))

import contest_submission  # noqa: E402


class FakeParent:
    def __init__(self, checkpoint: Path):
        self.artifact_id = "parent-a"
        self.checkpoint_sha256 = "sha256:" + hashlib.sha256(
            checkpoint.read_bytes()
        ).hexdigest()
        self._checkpoint = checkpoint

    def path(self, relative: str):
        if relative != "checkpoint.npz":
            raise AssertionError(relative)
        return self._checkpoint


class FakeData:
    def __init__(self, train_path: Path):
        self._train = train_path

    def training_rows(self):
        yield from self._iter(self._train)

    def validation_rows(self):
        yield from self._iter(self._train)

    @staticmethod
    def _iter(path: Path):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


class FakeRound:
    def __init__(self, work: Path, parent: FakeParent, profile: str, package: Path):
        self.dataset_key = profile
        self.round_index = 1
        self.max_output_tokens = 128
        task = "classification" if profile == "A" else "regression"
        metric = "macro_f1" if profile == "A" else "rmse"
        direction = "higher" if profile == "A" else "lower"
        self.task = {
            "dataset_key": profile,
            "task": task,
            "metric": metric,
            "metric_direction": direction,
            "public_projection": {
                "train_path": str(package / "public" / "train.jsonl"),
                "validation_path": str(package / "public" / "validation.jsonl"),
            },
        }
        self.parent = parent
        self.data = FakeData(package / "public" / "train.jsonl")
        self.call_ids = []
        self.finished = None
        self._work = work

    def history(self):
        return []

    def model(self, messages, **options):
        self.call_ids.append("call-1")
        return SimpleNamespace(
            call_id="call-1",
            text='{"epochs":1,"learning_rate":0.003,"batch_size":128}',
        )

    def state_workspace(self, directory):
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=False)
        return path

    def submit_candidate(self, directory, **kwargs):
        self.submitted_dir = Path(directory)
        return {"artifact_id": "cand-1"}

    def save_state(self, directory):
        return "sha256:" + "22" * 32

    def finish(self, **kwargs):
        self.finished = kwargs


class OfflineSubmissionTest(unittest.TestCase):
    def test_train_round_completes_and_uses_model(self):
        profiles = {
            "A": ROOT / "platform" / "packages" / "A",
            "B": ROOT / "platform" / "packages" / "B",
            "C": ROOT / "platform" / "packages" / "C",
        }
        for profile, package in profiles.items():
            with self.subTest(profile=profile):
                self._run_profile(profile, package)

    def _run_profile(self, profile: str, package: Path):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            work.mkdir()
            previous = Path(tmp) / "previous"
            previous.mkdir()
            checkpoint = previous / "checkpoint.npz"
            shutil.copyfile(package / "checkpoint.npz", checkpoint)

            previous_env = os.environ.get("CONTEST_WORK")
            os.environ["CONTEST_WORK"] = str(work)
            try:
                rnd = FakeRound(work, FakeParent(checkpoint), profile, package)
                contest_submission.train(rnd)
                self.assertIsNotNone(rnd.finished)
                self.assertEqual(rnd.finished["model_call_ids"], ["call-1"])
                self.assertIn(
                    rnd.finished["selected_artifact_id"], {"cand-1", "parent-a"}
                )
                self.assertTrue((rnd.submitted_dir / "checkpoint.npz").exists())
                self.assertTrue(
                    (rnd.submitted_dir / "baselines" / "model.py").exists()
                )
            finally:
                if previous_env is None:
                    os.environ.pop("CONTEST_WORK", None)
                else:
                    os.environ["CONTEST_WORK"] = previous_env


if __name__ == "__main__":
    unittest.main()
