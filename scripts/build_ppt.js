const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

pptx.layout = "LAYOUT_WIDE";
pptx.author = "智训引擎团队";
pptx.title = "智训引擎答辩";

const NAVY = "1E2761";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const INK = "0B2545";
const MUTED = "5A637A";
const CARD = "EEF2FB";

function card(slide, x, y, w, h, title, body, accent) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    fill: { color: WHITE },
    line: { color: ICE, width: 1 },
    shadow: { type: "outer", color: "A0A8C0", blur: 6, offset: 2, angle: 90, opacity: 0.35 },
  });
  slide.addText(title, {
    x: x + 0.22, y: y + 0.18, w: w - 0.44, h: 0.4,
    fontFace: "Arial", fontSize: 17, bold: true, color: accent || INK, margin: 0,
  });
  slide.addText(body, {
    x: x + 0.22, y: y + 0.62, w: w - 0.44, h: h - 0.8,
    fontFace: "Arial", fontSize: 12.5, color: MUTED, margin: 0, valign: "top",
  });
}

// Slide 1: title
let s = pptx.addSlide();
s.background = { color: NAVY };
s.addText("智训引擎", {
  x: 0.8, y: 1.45, w: 11.7, h: 1.2, fontFace: "Arial", fontSize: 52, bold: true, color: WHITE, margin: 0,
});
s.addText("面向工业数据漂移的自主迭代训练系统", {
  x: 0.82, y: 2.7, w: 11.5, h: 0.8, fontFace: "Arial", fontSize: 24, color: ICE, margin: 0,
});
s.addText("Harness · Qwen3.8-27B · CPU 工业模型 · 冠军挑战者回滚", {
  x: 0.82, y: 4.35, w: 11.5, h: 0.5, fontFace: "Arial", fontSize: 14, color: "DDE5FA", margin: 0,
});
s.addNotes("开场说明题目：不是训练大模型，而是做一套能自动训练并回滚工业小模型的系统。");

// Slide 2: problem
s = pptx.addSlide();
s.background = { color: WHITE };
s.addText("问题：数据会漂移，固定模型会失效", {
  x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: "Arial", fontSize: 28, bold: true, color: INK, margin: 0,
});
card(s, 0.7, 1.6, 3.7, 2.8, "输入漂移", "传感器老化、设备磨损导致特征分布变化，训练时和上线时不一样。", NAVY);
card(s, 4.65, 1.6, 3.7, 2.8, "概念漂移", "工况改变后，同样的特征可能对应不同的标签或寿命关系。", NAVY);
card(s, 8.6, 1.6, 3.7, 2.8, "资源约束", "无 GPU、无公网，4 核 8G，只能用 CPU 小模型和平台模型服务。", NAVY);
s.addText("目标：系统能自主发现变化、重新训练，并在变差时自动回滚。", {
  x: 0.7, y: 4.75, w: 11.6, h: 0.6, fontFace: "Arial", fontSize: 16, bold: true, color: INK, margin: 0,
});
s.addNotes("说明三个漂移来源，并强调核心目标是闭环，不是单一模型精度。");

// Slide 3: architecture
s = pptx.addSlide();
s.background = { color: WHITE };
s.addText("系统架构：教练与运动员分离", {
  x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: "Arial", fontSize: 28, bold: true, color: INK, margin: 0,
});
const arch = [
  ["平台数据", "公开训练与验证 JSONL"],
  ["Harness", "读数据、提交候选、保存状态"],
  ["Qwen3.8-27B", "生成训练计划，不预测工业标签"],
  ["CPU MLP", "真正训练、推理工业模型"],
  ["验证与回滚", "程序算分，更好才更新"],
];
arch.forEach((item, index) => {
  const y = 1.55 + index * 0.86;
  s.addShape(pptx.ShapeType.roundRect, {
    x: 1.0, y, w: 2.6, h: 0.68, fill: { color: index === 1 ? NAVY : CARD },
    line: { color: ICE, width: 1 },
  });
  s.addText(item[0], {
    x: 1.1, y, w: 2.4, h: 0.68, fontFace: "Arial", fontSize: 14, bold: true,
    color: index === 1 ? WHITE : INK, align: "center", valign: "middle", margin: 0,
  });
  s.addText(item[1], {
    x: 3.95, y, w: 8.0, h: 0.68, fontFace: "Arial", fontSize: 13, color: MUTED,
    valign: "middle", margin: 0,
  });
});
s.addNotes("强调职责边界：千问只做规划，程序执行和打分，避免幻觉分数。");

// Slide 4: baseline
s = pptx.addSlide();
s.background = { color: WHITE };
s.addText("先复现官方基线，再谈优化", {
  x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: "Arial", fontSize: 28, bold: true, color: INK, margin: 0,
});
const stats = [
  ["A 气体识别", "Macro-F1", "0.7140"],
  ["B 轴承 RUL", "RMSE", "681.16"],
  ["C 发动机 RUL", "RMSE", "52.87"],
];
stats.forEach((item, index) => {
  const x = 0.7 + index * 4.0;
  s.addShape(pptx.ShapeType.roundRect, {
    x, y: 1.65, w: 3.6, h: 2.5, fill: { color: CARD }, line: { color: ICE, width: 1 },
  });
  s.addText(item[0], { x: x + 0.2, y: 1.85, w: 3.2, h: 0.5, fontFace: "Arial", fontSize: 15, bold: true, color: INK, margin: 0 });
  s.addText(item[1], { x: x + 0.2, y: 2.4, w: 3.2, h: 0.5, fontFace: "Arial", fontSize: 12, color: MUTED, margin: 0 });
  s.addText(item[2], { x: x + 0.2, y: 2.85, w: 3.2, h: 0.9, fontFace: "Arial", fontSize: 34, bold: true, color: NAVY, margin: 0 });
});
s.addText("这些是公开验证集开发参考分，最终以平台评测为准。", {
  x: 0.7, y: 4.5, w: 11.6, h: 0.5, fontFace: "Arial", fontSize: 13, color: MUTED, margin: 0,
});
s.addNotes("强调基线的意义：统一起点，复现后才能公平比较。");

// Slide 5: three iterations
s = pptx.addSlide();
s.background = { color: WHITE };
s.addText("三次迭代：一次只改一个主变量", {
  x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: "Arial", fontSize: 28, bold: true, color: INK, margin: 0,
});
card(s, 0.7, 1.55, 3.7, 2.7, "第 1 轮", "沿官方检查点小幅续训，确认链路和基线水平。", NAVY);
card(s, 4.65, 1.55, 3.7, 2.7, "第 2 轮", "只调学习率或训练轮数，寻找稳定改进。", NAVY);
card(s, 8.6, 1.55, 3.7, 2.7, "第 3 轮", "冠军挑战者比较，变差自动回滚。", NAVY);
s.addText("每轮都记录假设、改动、指标、耗时、Token 和决策。", {
  x: 0.7, y: 4.55, w: 11.6, h: 0.6, fontFace: "Arial", fontSize: 15, bold: true, color: INK, margin: 0,
});
s.addNotes("说明实验证据链，平台多轮调用形成多次真实迭代。");

// Slide 6: rollback and quantified decisions
s = pptx.addSlide();
s.background = { color: NAVY };
s.addText("回滚与量化决策", {
  x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: "Arial", fontSize: 30, bold: true, color: WHITE, margin: 0,
});
s.addText("父 Macro-F1 0.7140 → 候选 0.7201 → 变化 +0.0061", {
  x: 0.8, y: 1.65, w: 11.4, h: 0.8, fontFace: "Arial", fontSize: 20, bold: true, color: ICE, margin: 0,
});
s.addText("程序依据指标方向和阈值决定部署或回滚，不靠口头判断。", {
  x: 0.8, y: 2.55, w: 11.4, h: 0.7, fontFace: "Arial", fontSize: 16, color: "DDE5FA", margin: 0,
});
s.addText("deploy 保留新模型   ·   rollback 回到父模型   ·   save state 保存冠军", {
  x: 0.8, y: 3.6, w: 11.4, h: 0.8, fontFace: "Arial", fontSize: 16, color: WHITE, margin: 0,
});
s.addNotes("说明决策可量化、可复现，防止模型自报成绩。");

// Slide 7: conclusion
s = pptx.addSlide();
s.background = { color: NAVY };
s.addText("结论", {
  x: 0.7, y: 0.9, w: 11, h: 0.9, fontFace: "Arial", fontSize: 34, bold: true, color: WHITE, margin: 0,
});
s.addText("一套可复现、可回滚、决策可追溯的自主训练闭环。", {
  x: 0.75, y: 2.0, w: 11, h: 0.9, fontFace: "Arial", fontSize: 22, bold: true, color: ICE, margin: 0,
});
s.addText("下一步：平台真实评测 → SwanLab 公开记录 → 漂移检测与更细回滚。", {
  x: 0.75, y: 3.3, w: 11, h: 0.8, fontFace: "Arial", fontSize: 16, color: "DDE5FA", margin: 0,
});
s.addNotes("收束到可验证结论，不夸大效果。");

pptx.writeFile({ fileName: "submission/08_答辩PPT/智训引擎答辩PPT.pptx" });
