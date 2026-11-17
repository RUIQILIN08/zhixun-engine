# 智训引擎真实数据基线

这个目录先完成一个可运行的最小闭环：

1. 读取比赛公开数据；
2. 复现一个 CPU 预测基线；
3. 输出逐批次指标和预测明细；
4. 保存数据版本、实验配置和结果哈希。

当前只使用 `numpy`，不依赖 GPU、外部模型或 Embedding。PyArrow/Qwen 接入和 Swan Lab
记录会在平台接口与实验规范确认后加入。

## 官方基线复现状态

三套官方 CPU 基线已原样加载并完成公开验证集复现，详细结果见
[BASELINE_REPRODUCTION.md](docs/BASELINE_REPRODUCTION.md)。

## Harness

已按 `contest_harness` 1.0.2 的 `workspace.v2` 协议搭建第一版
Harness，入口与实现状态见 [HARNESS_STATUS.md](docs/HARNESS_STATUS.md)。

## 数据位置

```text
data/raw/gas/gas.zip
data/raw/cmapss/cmapss.zip
data/raw/bearing/       # 目前缺少真实 XJTU-SY 振动数据
```

气体数据为 UCI Gas Sensor Array Drift Dataset，原始 ZIP 包中共有
`batch1.dat` 到 `batch10.dat`。CMAPSS 原始 ZIP 包包含 FD001 到 FD004。

## 本地运行

当前桌面环境的系统 Python 不可直接使用，可以使用：

```powershell
$py = 'C:\Users\15810\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py scripts\run_baseline.py --task gas
& $py scripts\run_baseline.py --task cmapss --subset FD001
& $py -m unittest discover -s tests
```

## 当前基线的边界

- 气体任务使用 `batch1` 训练，其余批次按时间顺序作为本地漂移流评估。
- CMAPSS 使用训练轨迹最后周期构造 RUL 标签，并以官方测试轨迹的最后一周期预测 RUL。
- 这些划分是本项目的本地冒烟验证，不冒充官方评测划分。
- 结果只能用于验证代码链路，不能直接写成平台正式成绩。

