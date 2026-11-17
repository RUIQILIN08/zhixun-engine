# Harness 镜像

本目录把官方 `contest_harness` SDK 与 CPU NumPy 工业模型打包成平台可调用的镜像。

## 镜像内容

- `/app/harness.py`：官方模板入口，支持 `describe`、`train`、`predict`。
- `/app/contest_submission.py`：选手模块，实现每轮训练、提交候选和回滚选择。
- `/app/baselines/`：官方 CPU MLP 的模型、训练和预测代码。

## 本地检查

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'harness\app') + ';' + (Join-Path $PWD 'platform\sdk\contest-harness-sdk-1.0.2')
python harness\app\harness.py describe
```

## 构建镜像

在项目根目录执行：

```powershell
docker build -f harness\Dockerfile -t zhixun-engine:0.1 .
```

## 提交提示

- 模型名称填平台白名单里的名称，例如 `Qwen/Qwen3.8-27B`。
- PyTRiO API Key 填在平台密钥栏，不写入镜像、源码或训练记录。
- 每轮必须调用一次 `rnd.model()`，并在 `finish()` 中传入真实 `model_call_ids`。
- stdout 只能写协议 JSONL，训练日志写 stderr。
