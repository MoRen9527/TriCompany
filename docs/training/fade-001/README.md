<!-- GOVERNANCE: 本教程卷真源在 TriCompany/docs/training/fade-001/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-001 周平面迁移教程（由浅入深·纯迁移域）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-001/README.md
- syncMode: source-only
- lastSyncedAt: 卷面时点锚=git commit 时戳（零手打·D-47 增补款正形）

版本：2.0.0（2026-11-14，RDT 小吴执笔；规格姊妹篇见 [fade-002/](../fade-002/README.md)）

> **重写批（2026-11-14·CEO 19:48:54 直令「fade-001 重写」·COS 19:49 派工·台账 609 笔）**：
> 两条不合格点对表修正——①入门篇（01）此前只加头注未见十阶段全景正文 → 本批 **01 全部重写**，
> 十阶段链全景（十段问题链表+触发面+横切保障）为入门主体；②fade-012（每日工作进度）内容此前
> 掺和在 fade-001 文档内 → 本批**全部实际拆出**至 [../fade-012/](../fade-012/README.md) 草稿卷
> （机制面/工作流与理据两聚合稿+两历史档 git mv 迁入），**本目录现纯 FADE-001 迁移域零混装**。
> 01-04 内容面以 [05 稿](05-trigger-chain-draft.md) 十阶段总览为基准下沉对齐现役终态。

## 现役终态速览（2026-11-14）

FADE-001 现役=**十阶段链**：bash payload 触发（段 1 preflight/段 2 qualify·基座）+段 3-10 Python CLI 全家（plan_scope/dce_steps/verify/score_cli+score_engine/score_rubric/close_skill/close_cli/notify_done·`runtime/cognition/` 全实装+测试全绿 184 passed）。
关键态：十阶段形 payload 在役（2026-11-13 22:12 换锚·cmd_len=2750/md5=4e1c7df5）+vB 形备档（复原判定面专用）·托转序列事件驱动（候 CEO 锁定）；**score 引擎实弹态**（run_state ok≠评分 pass·engine_absent=缺件异常）；段 5 verify **γ 终态形**（旧周 trees/ 目录存在性判据·δ 分叉消除）；首拍=**周日 23:50 硬锚**+首拍预期态判读表 v2；**两层窗**：预演形（验证毕·零生产触）≠生产形真值（候首拍）。

## 这套教程讲什么

FADE-001（周平面迁移，登记册在册完整档·迁移域首评 PASS 90/100）是 TriCompany 的"工作台自动翻页"实例：

- **周日自动翻页**：河源 TriRMC cron 到点（首拍硬锚 23:50）起跑十阶段链——该不该跑→有资格吗→迁什么→跑→迁对没→有没有分→怎么评→复盘收口→有终点→到达人，每段一问一卷面，fail-closed，幂等可重跑。

五篇由浅入深，按起点选入口：

| 版 | 文件 | 读者与目标 | 预计耗时 |
| --- | --- | --- | --- |
| ① 小白版 | [01-beginner-guide.md](01-beginner-guide.md) | 零基础新人：十阶段全景入门，跑通全链自测 | ~30 分钟 |
| ② 产品版 | [02-product-guide.md](02-product-guide.md) | 使用者/协作者/运维值班：十段工作流、使用旅程、值守判读、价值主张 | ~45 分钟 |
| ③ 代码版 | [03-code-map.md](03-code-map.md) | 接手工程师：十阶段执行体地图/迁移器本体/TriRMC cron 面（跨河源实勘边界如实标注） | ~半天 |
| ④ 深度研究版 | [04-deep-research.md](04-deep-research.md) | 维护者/架构研究者：设计理据、拓扑演进、真实事件复盘 | ~半天 |
| ⑤ 主卷（draft） | [05-trigger-chain-draft.md](05-trigger-chain-draft.md) | 全体：十段逐段现役终态正文（01-04 的更新修正依据源） | 按段查阅 |

建议路径：新人 ①→②（半天上手）；接手工程师 ①→②→③（一天接手）；维护者全程 ①→⑤。

## 学习路径与每步验证

0. 读①，验证 = 能背出十段问题链（该不该跑→有资格吗→迁什么→跑→迁对没→有没有分→怎么评→复盘收口→有终点→到达人），并跑通全链自测 `python -m pytest runtime/cognition/ -q`（TriCompany 仓根·基线 184 passed·smoke 口径）。
1. 读②，验证 = 能复述"周日首拍会发生什么（十段）/冻结窗口为什么存在/首拍异常怎么分级上报"三件事，并对判读表 v2 说出"run_state ok≠评分 pass"。
2. 读③，验证 = 能说出十段链段 3-10 五件主段产物文件名与 run_id 贯穿语义；能指出本机 clone 与河源部署态的边界（运行态以 API 读数为准）。
3. 读④，验证 = 能复述幂等链与十段分立两条设计理据，及案 b（参照系误判）/案 c（旗标体例）各自根因与防再犯机制。
4. 读⑤（按段查阅），验证 = 能对任一段说出"大白话干什么/代码在哪/亲手查证命令"三件套。

## 姊妹实例：FADE-012（每日工作进度维护）

原双域叙事中「维护域②（每日工作进度）」的全部机制——patrol 巡检兜底、双笔迹单写者、23h→10min 重建承诺、Score shadow 评分——**已拆出为独立实例 FADE-012**（registry 条目 v2.2.0·0c54864·候 CEO 追认），其培训草稿卷见 **[../fade-012/](../fade-012/README.md)**（机制面/工作流与理据两聚合稿+两历史档·2026-11-14 随重写令落位）。本目录不再混讲 012 内容。

## 05 稿·临时依据与记录（draft·2026-11-10 起）

- [05-trigger-chain-draft.md](05-trigger-chain-draft.md)——**本目录 01-04 四文档的更新修正依据源**（draft 形·FADE 规范十阶段制大纲）：第一段「触发执行」已填充=cron 触发七层全链导读+11-08 轮 15 秒死活体实锚+F1-F6 发现全档；段 2-10 已填充现役终态正文（2026-11-14 重更新批）。四文档后续修订以本稿为依据源——读 01-04 前建议先看 05 现势段，防旧基线与新拆解结论不一致。

## 真源指针（教程不替代真源）

- 登记册：`TriCompany/docs/engineering/fade-registry.md`（FADE-001 条：十段表+档位+齿条）
- 协议正身：`TriCompany/docs/engineering/fade-protocol-spec.md`（§2.5 终态门/§2.6 试卷冻结/§2.7/§2.8）
- 执行体：`TriCompany/runtime/cognition/` 十件 CLI（§见 [03 代码版](03-code-map.md)）+ `weekly_plane_shift`（迁移器本体·段 4 内核）
- 迁移域规范：`TriMMC/docs/ops/trimc-cron-plane-shift-runbook.md`（时点修正注记+§7 冻结窗口）
- 试卷：`TriCompany/docs/engineering/fade-papers/FADE-001-paper.json`（迁移域 90/100·冻结链零改动）
- 纪律：`TriCompany/docs/workflow/engineering-disciplines.md`（D-02 cron state/D-04 时刻）
- **现役终态卷（TriMetaverse 仓 W46 树·git 在链）**：判据锚卷 `.../trees/fade001-phase1-build-20261114/值守预期形-十阶段形判据锚-20261113.md`（在役五条族）·payload 供形正形 `.../trees/fade001-tenstage-deploy-20261115/cto-fsd-payload-supply-20261113.md`·首拍预期态判读表 v2 `.../trees/fade001-tenstage-deploy-20261115/cto-firstshot-expected-state-brief-20261114.md`·γ 终态定谳 `.../trees/fade001-tenstage-review-20261114/cto-gamma-impl-acceptance-20261114.md`

遇到冲突回真源，不回教程。

## 与既有培训件的关系

- 本目录五篇现役基线=**2026-11-14 十阶段链终态**；05 稿为依据源，01-04 以其为基准下沉。
- 双域时代两篇深度教程已迁 [../fade-012/](../fade-012/README.md)（deep-dive/maintenance-deep-dive·08-28 基线历史档）。
- 姊妹篇 [fade-002/](../fade-002/README.md)：FADE-002 讲发布域管线（源侧→发布面同步）；本目录讲 FADE-001 平面迁移实例。两实例共用 FADE 协议通识课（[FADE 小白](../fade-beginner-course.md)/[产品版](../fade-product-guide.md)/[代码深潜](../fade-code-deep-dive.md)）。
