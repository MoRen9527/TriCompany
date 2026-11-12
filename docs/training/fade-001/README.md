# FADE-001 周平面迁移四版教程（由浅入深）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-001/README.md
- syncMode: source-only
- lastSyncedAt: 2026-11-12（拆分归位批注·内容事实基线=2026-09-05 现势）

版本：1.0.0（2026-09-05，RDT 小吴执笔；事实基线=2026-09-05 现势；规格姊妹篇见 [fade-002/](../fade-002/README.md)）

> **拆分注记（2026-11-12·FADE-001 拆审四席一致 4/4·BOD 预授权执行）**：本目录现讲**单域**——
> FADE-001=周平面迁移（域①·周日翻页）。原双域叙事中的**维护域②（每日工作进度）已拆出为独立
> 实例 FADE-012**（编号 BOD 采 CTO 方案·候 CEO 追认·registry 条目拆立候登记）。
> 本文下述 patrol/daily-progress 段落描述的机制**现属 FADE-012**，保留作导读与交叉参考，
> 导航见下方「FADE-012 导航」节。

## 这套教程讲什么

FADE-001（周平面迁移，登记册在册完整档·迁移域首评 PASS 90/100）是 TriCompany 的"工作台自动翻页"实例：

- **迁移域①（周平面迁移）**：每周日 23:00（北京时间）由河源 TriRMC cron（job 9c81c7ec）自动把上周
  operating-records 平移进新周目录——五步确定性链，幂等可重跑。

（原同条目**维护域②（每日工作进度）**=daily-progress.md 双通道维护，最坏丢失窗口 23h→10 分钟、
三点全灭仅凭 GitHub 可重建——**拆分后现属 FADE-012**，见下方导航节。）

四版由浅入深，按起点选入口：

| 版 | 文件 | 读者与目标 | 预计耗时 |
| --- | --- | --- | --- |
| ① 小白版 | [01-beginner-guide.md](01-beginner-guide.md) | 零基础新人：搞懂双域是什么/为什么，跑通自测 | ~30 分钟 |
| ② 产品版 | [02-product-guide.md](02-product-guide.md) | 使用者/协作者：双域工作流、使用旅程、价值主张 | ~45 分钟 |
| ③ 代码版 | [03-code-map.md](03-code-map.md) | 接手工程师：patrol 代码地图/迁移链/TriRMC cron 面（跨河源实勘边界如实标注） | ~半天 |
| ④ 深度研究版 | [04-deep-research.md](04-deep-research.md) | 维护者/架构研究者：设计理据、拓扑演进、今晨三案复盘 | ~半天 |

建议路径：新人 ①→②（半天上手）；接手工程师 ①→②→③（一天接手）；维护者全程 ①→④。

## 学习路径与每步验证

1. 读①，验证 = 能说出拆分后的分工——FADE-001=周日翻页（迁移域①）、FADE-012=每日进度兜底
   （拆分前叙述为维护域②）；并跑通 `python -m runtime.cognition.daily_progress_patrol --self-test`
   （沙箱安全·该自测属 FADE-012 执行体）。
2. 读②，验证 = 能复述"周日晚上会发生什么/冻结窗口为什么存在"两件事（FADE-001 面）；
   平时谁来写进度/机器全灭怎么重建属 FADE-012 面，能指出其归属即达标。
3. 读③，验证 = 能指出 patrol 拓扑门限与 recovery push 的函数位置，并知道本机 clone 与河源部署态的边界。
4. 读④，验证 = 能复述今晨三案（分叉归账/参照系误判/旗标体例）各自根因与防再犯机制。

## FADE-012 导航（拆分后新条目·2026-11-12 起）

原双域叙事中「维护域②（每日工作进度）」的全部机制——patrol 巡检兜底、双笔迹单写者、
23h→10min 重建承诺、Score shadow 评分——拆分后**现属 FADE-012 独立实例**
（编号 BOD 采 CTO 方案·候 CEO 追认；registry 条目拆立随 CTO 拆审清单 #1 在途·候登记）：

- **机制内容导读**：本目录 01-04 各篇 patrol/维护段落（已改挂 FADE-012 口径）；
  深度档 [fade-001-maintenance-deep-dive.md](../fade-001-maintenance-deep-dive.md)
  （维护域双稿合稿·文件更名候 training 目录规范裁后执行）。
- **考卷**：`FADE-001-paper-maintenance.json` 随 FADE-012 迁移——归口 CTO 出卷冻结链
  （拆审清单 #6·时序=⑥出卷规范化候批先行免二次返工），迁移前旧名暂用。
- registry 正式条目立后，本节导览改指正身。

## 第五件·临时依据与记录（draft·2026-11-10 起）

- [05-trigger-chain-draft.md](05-trigger-chain-draft.md)——**本目录 01-04 四文档的更新修正依据源**（draft 形·FADE 规范十阶段制大纲）：第一段「触发执行」已填充=cron 触发七层全链导读（大白话+代码锚+亲手查证命令+CEO 引导问句）+11-08 轮 15 秒死活体实锚+F1-F6 发现全档；第二段起九骨架段候 CEO×BOD 拆解推进逐段丰富（三方完善制同步机制）。四文档后续修订以本稿为依据源——读 01-04 前建议先看 05 现势段，防旧基线与新拆解结论不一致。

## 与既有培训件的关系

- 本目录四版是 **2026-09-05 现势基线**。两件前代深度教程保留为历史档：
  - [fade-001-deep-dive.md](../fade-001-deep-dive.md)（324 行，2026-08-28 基线）：双域深度教程首作，拓扑叙事为 TriMC(sg) cron `59 23` 现役值——已被 08-30 时点迁移（23:00、heyuan TriRMC 9c81c7ec）与 08-31 watcher 槽位移（5,15,…,55）超越，见其头部版本差注记。
  - [fade-001-maintenance-deep-dive.md](../fade-001-maintenance-deep-dive.md)（788 行双稿合稿）：维护域本地全景篇+sg 纵深篇互补归一，同样是 08-28 基线；其 patrol 函数级拆解在现行 951 行版本上仍大体成立（本文 ③ 已按现行版重验锚点）。**拆分后本篇现属 FADE-012**（更名候 training 目录规范裁），见头部拆分注记。
- 姊妹篇 [fade-002/](../fade-002/README.md)：FADE-002 讲发布域管线（源侧→发布面同步）；本目录讲 FADE-001 平面维护实例。两实例共用 FADE 协议通识课（[FADE 小白](../fade-beginner-course.md)/[产品版](../fade-product-guide.md)/[代码深潜](../fade-code-deep-dive.md)）。

## 真源指针（教程不替代真源）

- 登记册：`TriCompany/docs/engineering/fade-registry.md`（FADE-001 条：双域十段表+扩维块+齿条）
- 协议正身：`TriCompany/docs/engineering/fade-protocol-spec.md`（§2.5 终态门/§2.6 试卷冻结/§2.7/§2.8）
- 执行体：`TriCompany/runtime/cognition/daily_progress_patrol.py`（patrol，951 行）+ `weekly_plane_shift`（迁移五步链）
- 迁移域规范：`TriMMC/docs/ops/trimc-cron-plane-shift-runbook.md`（时点修正注记 2026-08-31：现役周日 23:00 heyuan 9c81c7ec）
- 进度文件：`TriMetaverse/docs/workflow/operating-records/<当前周>/daily-progress.md`（头部声明=维护现势·**现属 FADE-012 面**）
- 试卷：`TriCompany/docs/engineering/fade-papers/FADE-001-paper.json`（迁移域 90/100·冻结链零改动）；
  `FADE-001-paper-maintenance.json`（维护域扩维冻结卷·**拆分后随 FADE-012 迁移**，归口 CTO 出卷冻结链候执行）
- 纪律：`TriCompany/docs/workflow/engineering-disciplines.md`（D-02 cron state/D-03 dist/D-04 时刻）

遇到冲突回真源，不回教程。
