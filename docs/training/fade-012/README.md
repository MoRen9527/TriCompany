<!-- GOVERNANCE: 本教程卷真源在 TriCompany/docs/training/fade-012/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-012 每日工作进度维护——草稿卷（draft）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-012/README.md
- syncMode: source-only
- lastSyncedAt: 卷面时点锚=git commit 时戳（零手打·D-47 增补款正形）

> **建卷性质（2026-11-14·CEO 19:48:54 fade-001 重写令随批）**：本目录系 **FADE-012 培训草稿卷**——重写令原文：
> 「fade-001 纯净性——fade-012 内容不得掺和在 fade-001 文档内；决定拆分的内容怕丢了：另建 fade-012 草稿卷单独存（与 fade-001 文档族分立·互不混装）」。
> 本卷聚合 FADE-012（每日工作进度维护）的全部培训材料。**现态=素材聚合+出处锚，非正式教程**——正式教程候编制（编制时按 FADE 教学协议重写）。

## FADE-012 是什么（一段话）

FADE-012=**每日工作进度维护**实例（registry 已立条 v2.2.0/0c54864·候 CEO 追认——FADE-001 拆审四席一致 4/4·BOD 采 CTO 编号方案）：
每天由两支笔维护 `TriMetaverse/docs/workflow/operating-records/<周>/daily-progress.md`——
**助理事件驱动主叙事**（销账/交付/裁决后随手记，质量最高）+ **patrol 巡检兜底补写**（sg watcher 每 10 分钟，确定性脚本只追加 commit 清单块、绝不改写别人内容）；
三端持久（本地 / sg-bare 必达 / GitHub 尽力而为），最坏丢失窗口 23h→10 分钟，机器全灭仅凭 GitHub 可重建；Score shadow 评分观测中（T1-T8·CLI 确定性六项 80+Skill 语义两项 20）。

拆分沿革：拆分前叙述为 FADE-001「维护域②」（双域时代）→ 2026-11-12 FADE-001 拆审四席一致、FADE-001 单域化（=周日翻页）→ 2026-11-14 本卷随重写令落位。

## 卷内文件

| 文件 | 性质 | 来源 |
| --- | --- | --- |
| [mechanics-patrol.md](mechanics-patrol.md) | 机制面聚合（小白入门段落/双通道与安全设计/评分 shadow/patrol 代码地图/四大机制/评分实现/接手起步） | 从 fade-001/ 01/02/03 三篇拆出·2026-11-14 重写令 |
| [workflow-and-rationale.md](workflow-and-rationale.md) | 工作流与设计理据聚合（双通道工作流/灾后重建/理据三题/演进档/案 a 分叉归账复盘/验证方式） | 从 fade-001/ 02/04 两篇拆出·2026-11-14 重写令 |
| [maintenance-deep-dive.md](maintenance-deep-dive.md) | 历史档（788 行双稿合稿·08-28 基线·git mv 保历史） | 原 `fade-001-maintenance-deep-dive.md` 迁入 |
| [deep-dive.md](deep-dive.md) | 历史档（324 行双域时代首作·08-28 基线·git mv 保历史） | 原 `fade-001-deep-dive.md` 迁入 |
| 试卷 `TriCompany/docs/engineering/fade-papers/FADE-012-paper-maintenance.json` | 冻结卷（已随拆分迁移毕·git mv+冻结仪式重走 3f92dfc4） | CTO 出卷冻结链 |

## 学习路径（草稿态）

1. 读本 README「一段话」定位。验证：能说出 FADE-012 与 FADE-001 的分工边界——012=每日进度兜底、001=周日翻页。
2. 读 [mechanics-patrol.md](mechanics-patrol.md) 小白段落与四大机制。验证：能指出拓扑门限（commits_since）与 recovery push 的函数位置。
3. 跑自测（TriCompany 仓根，沙箱安全）：`python -m runtime.cognition.daily_progress_patrol --self-test`——基线 30 用例全 ok、EXIT=0（2026-09-05 实测）。
4. 深入：[workflow-and-rationale.md](workflow-and-rationale.md) 理据三题+案 a 复盘；历史档两篇按需读（08-28 基线，行号接手时以现行版实读为准）。

## 真源指针（教程不替代真源）

- registry：`TriCompany/docs/engineering/fade-registry.md` FADE-012 条（v2.2.0·0c54864·候 CEO 追认）
- 执行体：`TriCompany/runtime/cognition/daily_progress_patrol.py`（patrol 951 行·2026-09-05 实读基线）
- 试卷：`TriCompany/docs/engineering/fade-papers/FADE-012-paper-maintenance.json`（冻结·3f92dfc4）
- 进度文件：`TriMetaverse/docs/workflow/operating-records/<当前周>/daily-progress.md`
- 拆条与考卷随迁锚：TriCompany 0c54864（registry 拆条 v2.2.0）/ 3f92dfc4（冻结重走）/ dea32d1（考卷改名对表现役名）

## 候办（编制正式教程时）

- 按 FADE 教学协议（大图→协议→MVP→原理→丰富→生产级）重写正式四版教程；本卷聚合件的行号锚以接手时现行版实读为准。
- registry FADE-012 条候 CEO 追认后，对表本卷与正式教程。
- 对外培训引用 FADE-012 材料时先走授权边界过滤（本卷含内网拓扑与运行细节）。
