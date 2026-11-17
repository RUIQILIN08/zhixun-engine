"""Workspace-v2 participant module.

The platform calls train(rnd) once per round and predict(sample, model_dir)
line by line. This first version continues the supplied NumPy MLP, asks the
platform model for a small training plan, submits the result as a candidate
artifact, and selects the better of candidate or parent for the next round.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import numpy as np

from baselines.data import flatten, read_dataset
from baselines.model import Model
from baselines.train import metrics, train_run
from drift_detector import compute_feature_drift
from gates import evaluate_gates


PREDICT_ARGV = ["python3", "/app/harness.py", "predict"]
TASKS = ("classification", "regression")

APP_DIR = Path(__file__).resolve().parent


def _work_dir() -> Path:
    return Path(os.environ.get("CONTEST_WORK", "/workspace"))


def _config_path(profile: str) -> Path:
    return APP_DIR / "baselines" / "configs" / f"{profile}.json"


def _default_plan(profile: str) -> dict:
    config = json.loads((_config_path(profile)).read_text(encoding="utf-8"))
    return {
        "epochs": 1,
        "learning_rate": float(config.get("learning_rate", 0.003)),
        "batch_size": int(config.get("batch_size", 128)),
    }


def _parse_plan(text: str, profile: str) -> dict:
    """Read a JSON training plan from the model reply with safe fallback."""

    fallback = _default_plan(profile)
    if not text:
        return fallback
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        return fallback
    if not isinstance(value, dict):
        return fallback

    epochs = value.get("epochs")
    learning_rate = value.get("learning_rate")
    batch_size = value.get("batch_size")
    if isinstance(epochs, int) and 1 <= epochs <= 10000:
        fallback["epochs"] = epochs
    if isinstance(learning_rate, (int, float)) and not isinstance(learning_rate, bool):
        if 0 < float(learning_rate) <= 1:
            fallback["learning_rate"] = float(learning_rate)
    if isinstance(batch_size, int) and 1 <= batch_size <= 65536:
        fallback["batch_size"] = batch_size
    return fallback


def _rows_preview(rows, limit: int = 4) -> list[dict]:
    preview = []
    for index, row in enumerate(rows):
        if index >= limit:
            break
        preview.append({"id": row["id"], "inputs": row.get("inputs")})
    return preview


def _metrics_for(checkpoint: str | Path, validation_path: str) -> dict:
    model = Model.load(Path(checkpoint))
    validation = read_dataset(
        validation_path,
        model.meta["task"],
        model.meta["classes"],
        model.meta["paths"],
    )
    return metrics(model, validation)


def _extract_token_usage(receipt) -> int:
    try:
        usage = receipt.response.get("usage") or {}
        total = usage.get("total_tokens", 0)
        return int(total) if isinstance(total, (int, float)) else 0
    except (AttributeError, TypeError):
        return 0


def _log_swanlab(
    rnd,
    work: Path,
    plan: dict,
    parent_metrics: dict,
    candidate_metrics: dict,
    selected_id: str,
    decision: str,
    drift: dict,
    gates: dict,
) -> None:
    """Write this round to SwanLab in offline mode; never log API keys."""

    try:
        import swanlab
    except ImportError:
        return

    mode = os.environ.get("SWANLAB_MODE", "offline")
    try:
        run = swanlab.init(
            mode=mode,
            project=os.environ.get("SWANLAB_PROJECT", "zhixun-engine"),
            name=f"{rnd.dataset_key}-round-{rnd.round_index}",
            log_dir=str(work / "swanlog"),
            public=True,
            config={
                "dataset_key": rnd.dataset_key,
                "round_index": rnd.round_index,
                "metric": rnd.task.get("metric"),
                "metric_direction": rnd.task.get("metric_direction"),
                "plan": plan,
                "model_name": rnd.model_name,
                "drift": drift,
                "gates": gates,
            },
        )
    except Exception:
        return

    try:
        data = {
            f"parent_{key}": value
            for key, value in parent_metrics.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        data.update(
            {
                f"candidate_{key}": value
                for key, value in candidate_metrics.items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            }
        )
        data["decision"] = 1 if decision == "采用本轮新候选" else 0
        data["selected_artifact_id"] = selected_id
        if isinstance(drift.get("score"), (int, float)):
            data["drift_score"] = drift["score"]
        if isinstance(gates.get("gate1_pass"), bool):
            data["gate1_pass"] = 1 if gates["gate1_pass"] else 0
        if isinstance(gates.get("gate2_pass"), bool):
            data["gate2_pass"] = 1 if gates["gate2_pass"] else 0
        if isinstance(gates.get("gain_per_cost"), (int, float)):
            data["gain_per_cost"] = gates["gain_per_cost"]
        run.log(data, step=rnd.round_index)
    finally:
        run.finish()


def _prepare_candidate(work: Path, train_output: Path, code_paths: list[str]) -> Path:
    candidate = work / "candidate"
    if candidate.exists():
        raise RuntimeError("candidate directory already exists")
    candidate.mkdir()
    shutil.copyfile(train_output / "checkpoint.npz", candidate / "checkpoint.npz")
    for relative in code_paths:
        source = APP_DIR / relative
        target = candidate / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return candidate


def train(rnd):
    """Run one round and select either the new candidate or the parent."""

    history = rnd.history()
    work = _work_dir()
    work.mkdir(parents=True, exist_ok=True)

    state = rnd.state_workspace(str(work / "state"))
    parent_checkpoint = rnd.parent.path("checkpoint.npz")
    parent_model = Model.load(parent_checkpoint)
    parent_seed = int(parent_model.meta["seed"])

    projection = rnd.task.get("public_projection") or {}
    train_path = str(projection.get("train_path", "/data/train.jsonl"))
    validation_path = str(projection.get("validation_path", "/data/validation.jsonl"))

    drift = compute_feature_drift(
        train_path,
        validation_path,
        parent_model.meta["task"],
        parent_model.meta["classes"],
    )

    preview = _rows_preview(rnd.data.training_rows())
    prompt = (
        "请只输出一个 JSON 对象，不要输出其他文字。JSON 字段固定为："
        '{"epochs": 整数, "learning_rate": 小数, "batch_size": 整数}。'
        "epochs 在 1 到 5 之间，learning_rate 在 0.0001 到 0.01 之间，"
        "batch_size 在 32 到 512 之间。"
        "本数据集为 %s，当前第 %d 轮，训练样本预览：%s。"
        "验证集相对训练集的特征漂移均值为 %.4f，最大漂移特征索引 %d（漂移量 %.4f）。"
        % (
            rnd.dataset_key,
            rnd.round_index,
            json.dumps(preview, ensure_ascii=False),
            float(drift["score"]),
            int(drift["max_feature_index"]),
            float(drift["max_feature_shift"]),
        )
    )
    receipt = rnd.model(
        [{"role": "user", "content": prompt}],
        max_tokens=min(256, rnd.max_output_tokens),
        temperature=0,
    )
    plan = _parse_plan(receipt.text, rnd.dataset_key)

    train_output = work / "train_output"
    if train_output.exists():
        raise RuntimeError("train output directory already exists")

    report = train_run(
        profile=rnd.dataset_key,
        train_path=train_path,
        validation_path=validation_path,
        output=str(train_output),
        resume=str(parent_checkpoint),
        epochs=plan["epochs"],
        learning_rate=plan["learning_rate"],
        batch_size=plan["batch_size"],
        stage_id=f"round-{rnd.round_index}",
    )

    code_paths = ["baselines/model.py", "baselines/data.py"]
    candidate = _prepare_candidate(work, train_output, code_paths)
    candidate_metrics = _metrics_for(candidate / "checkpoint.npz", validation_path)
    parent_metrics = metrics(
        parent_model,
        read_dataset(
            validation_path,
            parent_model.meta["task"],
            parent_model.meta["classes"],
            parent_model.meta["paths"],
        ),
    )

    total_tokens = _extract_token_usage(receipt)
    gates = evaluate_gates(
        candidate_metrics,
        parent_metrics,
        rnd.task,
        float(report.get("training_seconds", 0.0)),
        total_tokens,
    )
    gate1_pass = gates["gate1_pass"]
    gate2_pass = gates["gate2_pass"]

    hypothesis = "用父检查点继续训练，并让平台模型选择一个 CPU 预算内的训练计划。"
    change_summary = (
        "从父检查点续训 %d 个 epoch，学习率 %.6f，批大小 %d。"
        % (plan["epochs"], plan["learning_rate"], plan["batch_size"])
    )
    configuration = {
        "plan": plan,
        "parent_metrics": parent_metrics,
        "candidate_metrics": candidate_metrics,
        "model_call_id": receipt.call_id,
        "model_plan_text": receipt.text[:2000],
        "drift": drift,
        "gates": gates,
    }

    submitted = rnd.submit_candidate(
        candidate,
        hypothesis=hypothesis,
        change_summary=change_summary,
        configuration=configuration,
        seed=parent_seed,
        checkpoint_paths=["checkpoint.npz"],
        code_paths=code_paths,
        predict_argv=PREDICT_ARGV,
    )

    selected_id = rnd.parent.artifact_id
    decision = "保留父模型"
    if gate1_pass and gate2_pass:
        selected_id = submitted["artifact_id"]
        decision = "采用本轮新候选"
    elif gate1_pass and not gate2_pass:
        decision = "拒绝候选（单位增益不足）"
    reason = (
        "%s。父模型指标 %s，候选模型指标 %s。"
        % (decision, json.dumps(parent_metrics, ensure_ascii=False),
           json.dumps(candidate_metrics, ensure_ascii=False))
    )
    reason += " Gate1=%s，Gate2=%s。" % (
        "通过" if gate1_pass else "未通过",
        "通过" if gate2_pass else "未通过",
    )
    _log_swanlab(
        rnd,
        work,
        plan,
        parent_metrics,
        candidate_metrics,
        selected_id,
        decision,
        drift,
        gates,
    )

    champion_record = {
        "dataset_key": rnd.dataset_key,
        "round_index": rnd.round_index,
        "selected_artifact_id": selected_id,
        "candidate_metrics": candidate_metrics,
        "parent_metrics": parent_metrics,
        "decision": decision,
        "drift": drift,
        "gates": gates,
    }
    (state / "champion.json").write_text(
        json.dumps(champion_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with (state / "experiment_ledger.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(champion_record, ensure_ascii=False) + "\n")
    rnd.save_state(state)

    rnd.finish(
        selected_artifact_id=selected_id,
        hypothesis=hypothesis,
        change_summary=change_summary,
        reason=reason,
        configuration=configuration,
        seed=parent_seed,
        history_ids=[item["id"] for item in history],
        model_call_ids=list(rnd.call_ids),
    )


def predict(sample, model_dir):
    """Predict one sample using the selected artifact's checkpoint."""

    del model_dir
    checkpoint = os.environ.get("CONTEST_ARTIFACT_PATH")
    if not checkpoint:
        raise RuntimeError("CONTEST_ARTIFACT_PATH is not set")
    model = Model.load(checkpoint)
    paths, values = flatten(sample.inputs)
    if paths != model.meta["paths"]:
        raise RuntimeError("prediction feature schema differs from checkpoint")
    prediction = model.predict(np.asarray([values], dtype=np.float64))[0]

    if sample.task == "regression":
        return {"value": float(max(0.0, float(prediction)))}

    scores = np.asarray(prediction, dtype=np.float64)
    scores /= scores.sum()
    maximum = scores.max()
    top_indices = np.flatnonzero(scores == maximum)
    if len(top_indices) > 1:
        scores[top_indices[0]] += 1e-9
        scores /= scores.sum()
    return [
        {"label": label, "score": float(score)}
        for label, score in zip(model.meta["classes"], scores)
    ]

