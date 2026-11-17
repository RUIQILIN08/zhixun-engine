# Harness SDK 1.0.2 实现状态

实现日期：2026-11-17

## 协议版本

- SDK：`contest_harness` 1.0.2
- 协议：`contest.harness.workspace.v2`
- 模型访问：`host_gateway_rpc`
- 提示词版本：`industrial-workspace-flexible-v3`

## 已实现

- `/app/harness.py`：官方模板入口，支持 `describe`、`train`、`predict`。
- `/app/contest_submission.py`：每轮调用一次模型、从父检查点续训、提交候选并选择更新或回滚。
- 镜像内包含官方 CPU MLP 的 `baselines` 代码。
- 分类输出各类标签与分数，且只有一个最高分。
- 回归输出非负数值。
- 状态通过 `state_workspace` 和 `save_state` 保存。
- `finish` 携带真实 `model_call_ids` 和 `history_ids`。
- SwanLab 已接入，默认使用离线模式记录每轮指标、配置和决策。
- 性能门禁 Gate 1：核心指标必须相对父模型提升。
- 单位增益门禁 Gate 2：记录训练耗时与 Token 成本，计算单位成本增益。
- 实验台账 `experiment_ledger.jsonl` 记录每轮全部决策与指标。

## 本地已验证

```text
describe  -> {"protocol":"contest.harness.workspace.v2",...}
predict A -> 6 类标签与分数
train A   -> 模型调用、续训、提交候选、选择或回滚全部通过
```

## 尚未完成

- 镜像已本地构建并导出 `zhixun-engine-0.1.tar`，`describe` 与 `predict` 容器内验证通过；
- 尚未在平台真实 host 上运行；
- 尚未接入平台账号和模型白名单；
- 尚未生成 Docker 镜像；
- 尚未在平台完成 SwanLab 在线同步与公开链接；
- 尚未完成提交说明书、答辩 PPT 和演示备份。

## 关键文件

- [contest_submission.py](C:/Users/15810/Documents/ChatGPT/竞赛项目/zhixun_engine/harness/app/contest_submission.py)
- [Dockerfile](C:/Users/15810/Documents/ChatGPT/竞赛项目/zhixun_engine/harness/Dockerfile)
- [离线测试](C:/Users/15810/Documents/ChatGPT/竞赛项目/zhixun_engine/harness/tests/test_submission_offline.py)
- [官方 SDK 说明](C:/Users/15810/Documents/ChatGPT/竞赛项目/zhixun_engine/platform/sdk/contest-harness-sdk-1.0.2/HARNESS_SDK.md)
