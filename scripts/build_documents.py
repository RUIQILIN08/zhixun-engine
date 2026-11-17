"""Build the two submission DOCX files with python-docx."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission"

INK = RGBColor(0x0B, 0x25, 0x45)
BLUE = RGBColor(0x2E, 0x74, 0xB5)
HEAD_DARK = RGBColor(0x1F, 0x4D, 0x78)


def _set_font(run, name="Calibri", size=11, color=None, bold=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def _style_base(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.right_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

    for name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 18, 10),
        ("Heading 2", 13, BLUE, 12, 6),
        ("Heading 3", 12, HEAD_DARK, 8, 4),
    ):
        style = doc.styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = color
        style.font.bold = True
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def _title(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = INK
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def _h1(doc: Document, text: str) -> None:
    doc.add_heading(text, level=1)


def _h2(doc: Document, text: str) -> None:
    doc.add_heading(text, level=2)


def _p(doc: Document, text: str, *, bold=False) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run(text)
    _set_font(run, bold=bold)


def _bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(4)
        run = paragraph.add_run(item)
        _set_font(run)


def _table(doc: Document, rows: list[list[str]]) -> None:
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for row_index, row in enumerate(rows):
        for col_index, text in enumerate(row):
            cell = table.cell(row_index, col_index)
            cell.text = ""
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run(text)
            _set_font(run, size=10, bold=(row_index == 0))


def build_project_description() -> None:
    directory = OUT / "01_项目说明书"
    directory.mkdir(parents=True, exist_ok=True)
    doc = Document()
    _style_base(doc)
    _title(doc, "智训引擎：面向工业数据漂移的自主迭代训练系统")

    _h1(doc, "1. 项目概述")
    _p(
        doc,
        "本方案在无 GPU、无公网、4 核 8 GB 内存的 Linux 环境中，构建由大模型驱动"
        "的自主训练 Harness。系统读取传感器、轴承和发动机数据，在 CPU 上训练轻量"
        "工业模型，并自动完成实验、比较、更新与回滚。",
    )

    _h1(doc, "2. 背景与问题")
    _p(
        doc,
        "传感器老化、设备磨损和工况变化会使输入特征与标签分布逐渐漂移。固定模型"
        "的预测能力会随时间下降。比赛要求系统具备持续发现、诊断、评估和回滚的"
        "闭环能力，而不仅是训练一个模型。",
    )

    _h1(doc, "3. 总体架构")
    _p(doc, "平台数据 → Harness → 千问生成方案 → CPU 工业模型训练与预测 → 公开验证集评估 → 更新或回滚。")
    _bullets(
        doc,
        [
            "Harness 负责读取数据、提交候选、保存状态和最终决策；",
            "千问只负责提出训练方案，不计算指标、不修改权重；",
            "工业模型由本地 NumPy MLP 训练并预测；",
            "验证指标由程序计算，平台负责最终评分。",
        ],
    )

    _h1(doc, "4. 模型方案")
    _p(doc, "工业模型使用官方提供的小型 NumPy MLP，参数少于 100,000，无需 GPU。")
    _table(
        doc,
        [
            ["任务", "输入", "隐藏层", "输出"],
            ["A 气体识别", "128", "32", "6 类 softmax"],
            ["B 轴承寿命", "34", "24", "1 个 RUL 数值"],
            ["C 发动机寿命", "24", "32", "1 个 RUL 数值"],
        ],
    )
    _p(
        doc,
        "大模型 Qwen/Qwen3.8-27B 只负责规划和决策，不直接预测工业标签，也不直接"
        "改写模型权重。",
    )

    _h1(doc, "5. Harness 与 Agent")
    _p(doc, "系统使用 contest_harness 1.0.2 和 contest.harness.workspace.v2 协议。每轮流程：")
    _bullets(
        doc,
        [
            "读取父检查点和公开数据；",
            "调用一次千问生成训练计划；",
            "从父检查点继续训练候选模型；",
            "在公开验证集上计算指标；",
            "与父模型比较，决定更新或回滚；",
            "提交候选并结束本轮。",
        ],
    )

    _h1(doc, "6. 基线复现")
    _table(
        doc,
        [
            ["任务", "指标", "本地复现结果"],
            ["A 气体识别", "Macro-F1", "0.7140"],
            ["B 轴承寿命", "RMSE（分钟）", "681.1598"],
            ["C 发动机寿命", "RMSE（循环）", "52.8686"],
        ],
    )
    _p(doc, "以上为公开验证集的开发参考结果，最终成绩以平台评测为准。")

    _h1(doc, "7. 漂移应对与回滚")
    _p(
        doc,
        "系统采用冠军挑战者机制：候选模型只有在公开验证指标优于父模型时才被采用，"
        "否则保留父模型。状态通过 state_workspace 和 save_state 保存，下一轮以被"
        "选中的 artifact 作为新的父模型。",
    )

    _h1(doc, "8. 资源与合规")
    _bullets(
        doc,
        [
            "不使用 GPU，不在镜像内保存模型权重或 API Key；",
            "只通过 rnd.model() 调用平台模型；",
            "训练日志写 stderr，stdout 只输出协议 JSONL；",
            "数据、模型和代码来源记录在 SOURCE_COMPLIANCE.md。",
        ],
    )

    _h1(doc, "9. 局限与后续")
    _p(
        doc,
        "当前第一版默认使用平台基线续训与简单的指标比较。后续可加入漂移检测器、"
        "更强的候选搜索和更细粒度的回滚策略，但必须先通过平台真实评测并保留可复现"
        "证据。",
    )

    doc.save(directory / "智训引擎项目说明书.docx")
    print(directory / "智训引擎项目说明书.docx")


def build_run_instructions() -> None:
    directory = OUT / "06_系统运行说明"
    directory.mkdir(parents=True, exist_ok=True)
    doc = Document()
    _style_base(doc)
    _title(doc, "智训引擎系统运行说明")

    _h1(doc, "1. 运行环境")
    _bullets(
        doc,
        [
            "Linux，Python 3.10–3.12；",
            "依赖 NumPy 1.26.4；",
            "4 核 CPU、8 GB 内存、无 GPU；",
            "通过 PyTRiO host gateway 调用模型，不在镜像内保存 Key 或权重。",
        ],
    )

    _h1(doc, "2. 固定入口")
    _p(doc, "python3 /app/harness.py describe")
    _p(doc, "python3 /app/harness.py train")
    _p(doc, "python3 /app/harness.py predict")

    _h1(doc, "3. 本地开发")
    _p(doc, "创建虚拟环境：")
    _p(doc, "python -m venv .venv-platform")
    _p(doc, ".venv-platform\\Scripts\\python.exe -m pip install numpy==1.26.4")
    _p(doc, "协议检查：")
    _p(doc, ".venv-platform\\Scripts\\python.exe scripts\\dev_describe.py")
    _p(doc, "预测检查：")
    _p(doc, ".venv-platform\\Scripts\\python.exe scripts\\dev_predict.py")
    _p(doc, "离线训练检查：")
    _p(doc, ".venv-platform\\Scripts\\python.exe scripts\\dev_offline_test.py")

    _h1(doc, "4. 构建镜像")
    _p(doc, "docker build -f harness\\Dockerfile -t zhixun-engine:0.1 .")

    _h1(doc, "5. 镜像内检查")
    _p(doc, "docker run --rm zhixun-engine:0.1 describe")

    _h1(doc, "6. 注意事项")
    _bullets(
        doc,
        [
            "stdout 只输出协议 JSONL，训练日志写 stderr；",
            "每轮必须至少调用一次 rnd.model()；",
            "不能把公开验证集并入训练集；",
            "不能把真实 RUL、寿命比例或未来信息加入模型输入。",
        ],
    )

    doc.save(directory / "智训引擎系统运行说明.docx")
    print(directory / "智训引擎系统运行说明.docx")


if __name__ == "__main__":
    build_project_description()
    build_run_instructions()
