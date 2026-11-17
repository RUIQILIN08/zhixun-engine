"""PyCharm 友好入口：直接运行本文件即可看到 describe 输出。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "harness" / "app"
SDK = ROOT / "platform" / "sdk" / "contest-harness-sdk-1.0.2"

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, str(APP))
sys.path.insert(0, str(SDK))

from contest_harness.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["harness.py", "describe"]))
