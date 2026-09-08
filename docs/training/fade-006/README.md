# FADE-006 执行面自动拾取四版教程（由浅入深）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-006/README.md
- syncMode: source-only
- lastSyncedAt: 2026-09-07

版本：V1.0（2026-09-07，RDT 小吴执笔；规格姊妹篇 [fade-002/](../fade-002/README.md)、[fade-001/](../fade-001/README.md)）

## 这套教程讲什么

FADE-006（执行面自动拾取，公司唯一**完整实例标准档 91 分**）解决一个问题：**计划写完还要人推着做**。
它把"任何符合配方形状的任务包"（计划文档+树注册）变成：**落盘即入队、双通道自动拾取、自治执行到收口、材料全程防篡改、故障分层取证自愈**。

- **配方六步**：F1 铸计划 → F2 拆树封卷 → A 挂平面 → D 自动拾取 → E 自治执行 → Z 收口回执
- **拾取条件**：树文件三重门——`status=active` + `server-executable` + `pending` 无时间门 + `face` 路由
- **防篡改**：原材料卷封制 + campaign Merkle root 收口存档

| 版 | 文件 | 读者与目标 | 预计耗时 |
| --- | --- | --- | --- |
| ① 小白版 | [01-beginner-guide.md](01-beginner-guide.md) | 零基础新人：搞懂"挂单→过门→派工→回执"，看懂一棵真树 | ~30 分钟 |
| ② 产品版 | [02-product-guide.md](02-product-guide.md) | 使用者/编排协作者：六步配方、护栏、故障六面墙 | ~45 分钟 |
| ③ 代码版 | [03-code-map.md](03-code-map.md) | 接手工程师：编排器/工具族/树合同/节点报告代码路径 | ~半天 |
| ④ 深度研究版 | [04-deep-research.md](04-deep-research.md) | 维护者/架构研究者：设计理据、80→91 增评弧线、实战战役复盘 | ~半天 |

## 学习路径与每步验证

1. 读①，验证 = 打开一棵现役树（W37 `trees/duty-night-patrol/tree-op.json`）说出它为什么还没被拾取（status=pending）。
2. 读②，验证 = 能复述六步配方与三重门，遇到"tick 没反应"知道先查哪面墙。
3. 读③，验证 = 能指出编排器三重门代码位与卷封验卷函数，跑通 node-report-check。
4. 读④，验证 = 能复述 P0 战役八实例弧线与 80→91 两处升分原因。

## 与既有培训件的关系

- [fade-006-deep-dive.md](../fade-006-deep-dive.md)（427 行，2026-08-29）：七篇系列中最长一篇，锚定 P0 战役（2026-08-26/27）时点——保留为历史档，版本差以本目录 ③④ 为现行（其注释记的编排机制演进，如通道勘定/harvest-rc 立法后形态，以登记册与现行代码为准）。
- 协议通识课（[FADE 小白](../fade-beginner-course.md)/[产品版](../fade-product-guide.md)/[代码深潜](../fade-code-deep-dive.md)）：本实例是"runtime-owned durable + 多节点树"的标杆样本，§2.7 节点收口报告立法正出自它。
- 姊妹篇：[fade-002/](../fade-002/README.md)（发布域管线）、[fade-001/](../fade-001/README.md)（平面维护）。

## 真源指针（教程不替代真源）

- 规格正身：`TriMetaverse/docs/execution/fade-006-execution-autopick-spec.md`（标准配方+护栏+故障表）
- 上位管线：`TriMetaverse/docs/execution/2026-08-26/fade-pipeline-design.md` v1.1（§六 AC/§八 运行语义/§九 卷封制）
- 反向工程：`TriMetaverse/docs/execution/fade-instances-retrospective.md`
- 登记册：`TriCompany/docs/engineering/fade-registry.md` FADE-006 条（十段表+映射表首行填制+升格记录）
- 工具族：`TriMetaverse/scripts/fade/`（seal-materials / node-report-check / run-root / _fadehash / fade-watch.ps1 等 12 件）
- 试卷评分：`TriCompany/docs/engineering/fade-papers/FADE-006-*`（80→91 两卷）
- 现役样本：`TriMetaverse/docs/workflow/operating-records/<周>/trees/`（W35 首役九树、W37 现役树）

遇到冲突回真源，不回教程。
