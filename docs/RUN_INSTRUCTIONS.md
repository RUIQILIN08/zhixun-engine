# 系统运行说明

## 运行环境

- 平台镜像：Linux，Python 3.10–3.12；
- 依赖：NumPy 1.26.4；
- 资源：4 核 CPU、8 GB 内存、无 GPU；
- 模型：通过 PyTRiO host gateway 调用，不在镜像内保存 Key 或权重。

## 固定入口

```text
python3 /app/harness.py describe
python3 /app/harness.py train
python3 /app/harness.py predict
```

## 本地开发

创建虚拟环境：

```powershell
python -m venv .venv-platform
.\.venv-platform\Scripts\python.exe -m pip install numpy==1.26.4
```

协议检查：

```powershell
.\.venv-platform\Scripts\python.exe scripts\dev_describe.py
```

预测检查：

```powershell
.\.venv-platform\Scripts\python.exe scripts\dev_predict.py
```

离线训练检查：

```powershell
.\.venv-platform\Scripts\python.exe scripts\dev_offline_test.py
```

## 构建镜像

在项目根目录：

```powershell
docker build -f harness\Dockerfile -t zhixun-engine:0.1 .
```

## 镜像内检查

```powershell
docker run --rm zhixun-engine:0.1 describe
```

## 注意事项

- stdout 只输出协议 JSONL，训练日志写 stderr；
- 每轮必须至少调用一次 `rnd.model()`；
- 不能把公开验证集并入训练集；
- 不能把真实 RUL、寿命比例或未来信息加入模型输入。

