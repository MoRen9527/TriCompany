# FADE-003 共学周记四版教程（由浅入深）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-003/README.md
- syncMode: source-only
- lastSyncedAt: 2026-09-09

版本：V1.0（2026-09-08，RDT 小吴执笔；规格姊妹篇 [fade-002/](../fade-002/README.md)、[fade-001/](../fade-001/README.md)、[fade-006/](../fade-006/README.md)——四实例=FADE 运行面全覆盖，本单收官）

## 这套教程讲什么

FADE-003（共学周记记录，**98/100 全场最高分**，完整档）把"对话中出现值得沉淀的经验 →
记入当周共学周记"这个动作做成了全公司范本级的确定性流水线：

- **一句话**：agent 负责判断与撰写（什么值得记、写得好不好），格式与落点由确定性 CLI 约束
  （journal-cli.mjs：begin→qualify→append→score→close 一条 runId 贯穿），写后必须收口回报。
- **灵魂设计**：**Close CLI 是校验者而非发起者**——机器可以否决 agent 的"approved"（实案在卷）。
- **98 分弧线**：runId 7a85e3e0（2026-08-28）——score S 满分 80 地板+W 自评 18/20→APPROVED，
  当日升格完整档。

| 版 | 文件 | 读者与目标 | 预计耗时 |
| --- | --- | --- | --- |
| ① 小白版 | [01-beginner-guide.md](01-beginner-guide.md) | 零基础新人：四问/五件/一条 runId，读懂一条真实审计链 | ~30 分钟 |
| ② 产品版 | [02-product-guide.md](02-product-guide.md) | 周记作者/审阅者：记一条周记的完整旅程、去重/脱敏/RETRY 机制 | ~45 分钟 |
| ③ 代码版 | [03-code-map.md](03-code-map.md) | 接手工程师：journal-cli.mjs 489 行命令族/审计合同/校验器代码路径 | ~半天 |
| ④ 深度研究版 | [04-deep-research.md](04-deep-research.md) | 维护者/架构研究者：W34 违规立册史、80 卡线教训、98 分升档弧线复盘 | ~半天 |

## 学习路径与每步验证

1. 读①，验证 = 打开审计日志指出任一 runId 的 begin/close 两行，说出这条 run 走到了哪一步。
2. 读②，验证 = 能复述"记一条周记"的完整动作序（含被脱敏拦截/被去重挡下/RETRY 重评三条岔路）。
3. 读③，验证 = 能指认 qualify 的三种退出码与 close 五查的代码位，手验一条 RETRY→APPROVED 前置。
4. 读④，验证 = 能复述 W34 违规→立册→80 卡线→98 升档的完整制度演进及其教训。

## 与既有培训件的关系

- [fade-003-deep-dive.md](../fade-003-deep-dive.md)（521 行，版本基准 2026-08-29 升档完成日）：七篇系列中最"新"的一篇，98 分弧线已是其核心内容——保留为历史档，版本差=08-29 后 run log 增量与 W36/W37 现势（见其头部注记）。
- 姊妹篇：[fade-002/](../fade-002/README.md)（发布域）、[fade-001/](../fade-001/README.md)（平面维护）、[fade-006/](../fade-006/README.md)（执行拾取）。四实例对照：003 是唯一**Agent-owned 手动触发 + 全链 CLI 化**的标本——触发最弱但链路最完整的升格样本。
- 协议通识课：[FADE 小白](../fade-beginner-course.md)/[产品版](../fade-product-guide.md)/[代码深潜](../fade-code-deep-dive.md)。

## 真源指针（教程不替代真源）

- 规范正身：`TriMetaverse/docs/workflow/operating-records/项目级 AI 共学周记/ade-journal-recording-spec.md`（v1.1：四问/三查/五查/Score 段/RETRY 状态机）
- 执行体：`TriMetaverse/scripts/journal/journal-cli.mjs`（489 行）+ 审计 `同目录/journal-run-log.jsonl`
- 格式真源：`.github/prompts/项目级 AI 共学周记.prompt.md`（固定五件结构）+ 周记目录 README（归档/版本规则）
- 周记实件：`docs/workflow/operating-records/<周>/project-ai-community-weekly-<周>.md`（现存 W35）
- 登记册：`TriCompany/docs/engineering/fade-registry.md` FADE-003 条（完整档+升档五销账）
- 试卷评分：`TriCompany/docs/engineering/fade-papers/FADE-003-*`（paper/score/coverage/upgrade 卷）
- 纪律：D-06（周记纪律，W34 违规的制度源头）

遇到冲突回真源，不回教程。
