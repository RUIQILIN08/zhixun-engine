"""PyCharm 友好入口：加载官方 A 检查点，预测一条公开验证样本。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "harness" / "app"
SDK = ROOT / "platform" / "sdk" / "contest-harness-sdk-1.0.2"
CHECKPOINT = ROOT / "platform" / "packages" / "A" / "checkpoint.npz"
VALIDATION = ROOT / "platform" / "packages" / "A" / "public" / "validation.jsonl"


def main() -> None:
    first_line = VALIDATION.read_text(encoding="utf-8").splitlines()[0]
    row = json.loads(first_line)
    request = json.dumps(
        {"task": "classification", "inputs": row["inputs"]},
        ensure_ascii=False,
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(APP), str(SDK)))
    env["CONTEST_ARTIFACT_PATH"] = str(CHECKPOINT)

    completed = subprocess.run(
        [sys.executable, str(APP / "harness.py"), "predict"],
        input=request + "\n",
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    print("returncode:", completed.returncode)
    print("prediction:", completed.stdout.strip())
    if completed.stderr:
        print("stderr:", completed.stderr.strip())


if __name__ == "__main__":
    main()
