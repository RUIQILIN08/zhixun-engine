# 官方 CPU 基线本地复现

复现日期：2026-11-16

## 结论

三套官方包中的 checkpoint 均能原样加载，并在公开验证集上复现包内记录的结果。
复现过程没有训练、没有改动权重、没有合并训练与验证数据。

| Profile | 任务 | 本地复现结果 | 官方包内记录 | 是否一致 |
| --- | --- | --- | --- | --- |
| A | 气体分类 | Accuracy 0.8786，Macro-F1 0.7140 | 相同 | 一致 |
| B | 轴承 RUL 回归 | MAE 563.1058，RMSE 681.1598 | 相同 | 一致 |
| C | 发动机 RUL 回归 | MAE 38.8998，RMSE 52.8686 | 相同 | 一致 |

## 官方包状态

- 所有包的 `official_scoring_ready` 均为 `false`；
- 用途标记为 `development_reference`；
- A 和 C 的标签状态为 `draft`；
- B 的标签状态为 `approved`。

因此这些数字只是开发参考分，不是平台正式成绩。

## 复现命令

```powershell
.\.venv-platform\Scripts\python.exe scripts\reproduce_baseline.py `
  --package platform\packages\A --output platform\reproduction\A

.\.venv-platform\Scripts\python.exe scripts\reproduce_baseline.py `
  --package platform\packages\B --output platform\reproduction\B

.\.venv-platform\Scripts\python.exe scripts\reproduce_baseline.py `
  --package platform\packages\C --output platform\reproduction\C
```

也可一次执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\reproduce_all.ps1
```

## 产物

```text
platform/reproduction/A/reproduction.json
platform/reproduction/B/reproduction.json
platform/reproduction/C/reproduction.json
```

## 尚未完成且待用户自行配置

- `pytrio` 尚未安装；
- Qwen/Qwen3.8-27B 接口尚未接入；
- Harness、三次迭代、Swan Lab、系统镜像尚未实现。
