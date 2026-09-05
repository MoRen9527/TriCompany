# FADE-002 发布域四版教程（由浅入深）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-002/README.md
- syncMode: source-only
- lastSyncedAt: 2026-09-05

版本：V1.0（2026-09-05，RDT 小吴执笔；CEO 目标：新人半天能上手、工程师一天能接手）

## 这套教程讲什么

FADE-002（公司文档管理 / 真源-发布同步管线，登记册历史代号"发布域"）是 TriCompany
最成熟的一条确定性发布管线：源侧（TriCompany）真源改了之后，发布侧（TriMetaverse
的 CLAUDE.md、AGENTS.md、`.claude/agents/`、`.claude/hub/` 等消费面）怎么可靠地跟平。

四版由浅入深，读者按自己的起点选入口：

| 版 | 文件 | 读者与目标 | 预计耗时 |
| --- | --- | --- | --- |
| ① 小白版 | [01-beginner-guide.md](01-beginner-guide.md) | 零基础新人：搞懂"是什么/为什么"，跑通一条命令 | ~30 分钟 |
| ② 产品版 | [02-product-guide.md](02-product-guide.md) | 使用者/协作者：功能面、工作流、使用旅程、价值主张 | ~45 分钟 |
| ③ 代码版 | [03-code-map.md](03-code-map.md) | 接手工程师：命令族、manifest schema、保护链、发布流程代码路径 | ~半天 |
| ④ 深度研究版 | [04-deep-research.md](04-deep-research.md) | 维护者/架构研究者：设计理据、决策演进、真实失败案例复盘 | ~半天 |

建议路径：新人 ①→②（半天上手）；接手工程师 ①→②→③（一天接手）；维护者全程 ①→④。

## 学习路径与每步验证

1. 读①，验证 = 在 TriCompany 根跑通 `python -m runtime.cognition.source_publish_check --project-docs` 并读懂输出的 status 与 items。
2. 读②，验证 = 能向别人复述"三类资产、三道安全门、一次发布走哪些角色和命令"。
3. 读③，验证 = 跑通校验套件全绿，能指出任一 scope 的保护链代码位置。
4. 读④，验证 = 能复述今夜三案（字节漂移/幻影真源/写根 bug）各自的根因与防再犯机制。

## 与既有培训件的关系

- [FADE 小白教程](../fade-beginner-course.md) / [FADE 产品版](../fade-product-guide.md) / [FADE 代码深潜](../fade-code-deep-dive.md)：讲 **FADE 协议本体**（十段生命周期、试卷评分），协议通识课——本目录讲 **FADE-002 实例**（发布域管线本身），实例专讲课。先通识后实例，交叉不重复。
- [fade-002-deep-dive.md](../fade-002-deep-dive.md)（2026-08-29 版）：本实例上一代深度教程，保留为历史档；其代码行号锚基于当时 4344 行版 CLI（现行 4688 行），且不含 claude-session 渲染面、M-001 公共段注入通道与 2026-09-04/05 三案——以本目录 ③④ 为现行版。
- [项目真源文档同步 FADE 教程](../project-source-document-sync-fade-tutorial.md)：早期同步域专讲课，读其流程思想，现行命令与合同以本目录 ③ 为准。

## 真源指针（教程不替代真源）

- 协议正身：`TriCompany/docs/engineering/fade-protocol-spec.md`（v2.0.3，envelope v1.0 的声明载体就是 FADE-002）
- 登记册：`TriCompany/docs/engineering/fade-registry.md`（FADE-002 条目，评分 90→93 记录）
- 发布域规范：`TriCompany/docs/workflow/project-source-document-sync-ade.md`
- 执行体：`TriCompany/runtime/cognition/source_publish_check.py`（DCE CLI）+ `source_publish_check_validation.py`（校验套件）
- manifest：`TriCompany/.github/manifests/project-source-doc-sync-manifest.json`
- 纪律册：`TriCompany/docs/workflow/engineering-disciplines.md`（D-01 先写后报 / D-04 双轨时刻 / D-07 派生壳）

遇到冲突回真源，不回教程。培训内容不替代 registry、协议裁决或代码事实。
