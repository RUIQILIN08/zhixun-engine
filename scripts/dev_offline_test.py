"""PyCharm 友好入口：用 unittest 直接运行 Harness 离线训练测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "harness" / "app"
SDK = ROOT / "platform" / "sdk" / "contest-harness-sdk-1.0.2"
sys.path.insert(0, str(APP))
sys.path.insert(0, str(SDK))


def main() -> None:
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(ROOT / "harness" / "tests"),
        pattern="test_submission_offline.py",
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
