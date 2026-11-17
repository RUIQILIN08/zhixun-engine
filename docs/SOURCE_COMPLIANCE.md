# 数据、模型与代码来源

## 官方数据包

- A：UCI Gas Sensor Array Drift Dataset
  - 来源：https://archive.ics.uci.edu/dataset/224/gas
  - 官方包 label_status：draft
- B：XJTU-SY Bearing Datasets
  - 来源：https://github.com/WangBiaoXJTU/xjtu-sy-bearing-datasets
  - 官方包 label_status：approved
- C：NASA C-MAPSS
  - 来源：https://catalog.data.gov/dataset/cmapss-jet-engine-simulated-data
  - 官方包 label_status：draft

## 大模型

- Qwen/Qwen3.8-27B，通过 PyTRiO 平台调用。
- 不下载、不打包、不重新分发模型权重。

## 代码

- `contest_harness` 1.0.2：主办方提供的选手 SDK。
- `baselines/`：官方包提供的 CPU NumPy MLP 训练代码。
- 本项目 Harness 代码：团队自行编写。

## 许可与使用边界

- 数据仅用于本赛事，保留原始出处；
- 不把公开数据结果冒充平台正式成绩；
- 不将第三方数据重新分发或用于商业用途；
- 模型与工具使用遵守平台许可和赛事规则。

