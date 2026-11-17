# 数据状态

## 已可用

### A：气体识别

- 文件：`data/raw/gas/gas.zip`
- 原始规模：13910 条记录、128 个特征、6 个类别、10 个批次
- 原始格式：`batch1.dat` 到 `batch10.dat`
- 读取器会验证类别、特征编号、缺失特征和重复特征。

### C：发动机寿命预测

- 文件：`data/raw/cmapss/cmapss.zip`
- 子集：FD001、FD002、FD003、FD004
- 原始文件：训练轨迹、测试轨迹和官方测试 RUL
- 读取器会验证 26 列结构以及测试发动机数与 RUL 行数一致。

## 尚缺

### B：轴承健康识别

当前下载的 `xjtu-sy-bearing-datasets-master.zip` 只有约 1.6 KB，包含：

- `README.md`
- `_config.yml`

它没有振动信号。需要从 README 中的网站、Google Drive、Dropbox、MediaFire、
MEGA 或百度网盘入口下载实际数据。也可以直接使用比赛平台提供的训练包。

收到数据后应放入：

```text
data/raw/bearing/
```

并在确认实际文件结构后再编写适配器，不能先假定列名、采样率或标签定义。

