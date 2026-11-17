from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "submission"
STAGE = SUB / "_staging"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def zip_directory(source: Path, target: Path, *, include_root: bool = False):
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                relative = path.relative_to(source)
                archive_name = str(relative)
                if include_root:
                    archive_name = str(source.name) + "/" + archive_name
                info = zipfile.ZipInfo(archive_name, date_time=FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())


def build_harness_zip() -> None:
    zip_directory(
        STAGE / "03_harness_build",
        SUB / "03_Harness镜像" / "harness_build.zip",
        include_root=True,
    )


def build_prototype_zip() -> None:
    zip_directory(
        STAGE / "04_prototype",
        SUB / "04_可复现最小原型" / "智训引擎可复现最小原型.zip",
    )


def build_source_zip() -> None:
    zip_directory(
        STAGE / "05_source",
        SUB / "05_项目源代码" / "智训引擎项目源代码.zip",
    )


def build_experiment_zip() -> None:
    staging = STAGE / "07_experiments"
    staging.mkdir(parents=True, exist_ok=True)
    for profile in ("A", "B", "C"):
        destination = staging / profile
        destination.mkdir(parents=True, exist_ok=True)
        package = ROOT / "platform" / "packages" / profile
        reproduction = ROOT / "platform" / "reproduction" / profile / "reproduction.json"
        for source in (
            reproduction,
            package / "training.json",
            package / "history.jsonl",
            package / "baseline-info.json",
        ):
            if source.exists():
                (destination / source.name).write_bytes(source.read_bytes())
    zip_directory(
        staging,
        SUB / "07_实验日志" / "智训引擎实验日志.zip",
    )


def build_final_zip() -> None:
    target = SUB / "智训引擎-参赛队伍-校赛提交材料.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(SUB.rglob("*")):
            if not path.is_file():
                continue
            if path.name.startswith("~$"):
                continue
            if path == target:
                continue
            if path.is_relative_to(STAGE) or path.is_relative_to(SUB / "_qa"):
                continue
            relative = path.relative_to(SUB)
            info = zipfile.ZipInfo(str(relative), date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(target)


if __name__ == "__main__":
    build_harness_zip()
    build_prototype_zip()
    build_source_zip()
    build_experiment_zip()
    build_final_zip()
