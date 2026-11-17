from __future__ import annotations

from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission" / "_qa"
OUT.mkdir(parents=True, exist_ok=True)

pdfs = [
    ROOT / "submission" / "01_项目说明书" / "智训引擎项目说明书.pdf",
    ROOT / "submission" / "06_系统运行说明" / "智训引擎系统运行说明.pdf",
]

for pdf in pdfs:
    prefix = pdf.parent.name
    document = fitz.open(pdf)
    for page in document:
        pixmap = page.get_pixmap(dpi=110)
        target = OUT / f"{prefix}-{page.number + 1}.png"
        pixmap.save(target)
        print(target)
