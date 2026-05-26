# Chief Of Staff LLM Wiki Priority Plan

版本：V0.5
日期：2026-04-21
状态：当前第一优先级实现任务，phase-2 的知识工作台、全量 recall、task bus 与人工审批语义已进入可运行骨架

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/chief-of-staff-llm-wiki-priority-plan.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: on-demand-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/engineering/chief-of-staff-llm-wiki-priority-plan.md
- supportSyncRule: 仅在成批发布或当前宿主重新显式依赖时追平 support 副本
- lastSyncedAt: 2026-04-28

## 1. 文档定位

本文用于把“总助专属 LLM wiki”正式提升为当前第一优先级实现任务。

这里的目标不是一句抽象口号，而是形成明确落点：

- 总助有自己的专属文件夹
- 可以持续往里面堆放零散资料
- 系统可以把这些资料逐步整理成 wiki 页面
- 整个整理过程保留审计与来源痕迹

当前本文已回写到 `TriCompany/docs/engineering/` 作为工程真源；但本轮 phase-2 的实际运行骨架、知识目录和验证证据仍主要位于 `TriCompany-copilot-host-assets/`，这不等于相关实现代码已经整体回迁到 `TriCompany/runtime/`。

## 2. 当前目标

当前第一优先级目标已经从最小闭环推进到下面这条可持续链：

1. 把零散资料放入总助专属 `inbox/`
2. 对资料做最小标准化与主题归类
3. 自动生成或更新 `wiki/` 下的主题页面
4. 把来源映射、编译过程和写回痕迹留在 `audit/`
5. 把页状态、审批状态和最近审计聚合进 `workbench/`

当前专属目录已固定为：

- `knowledge/chief-of-staff/inbox/`
- `knowledge/chief-of-staff/wiki/`
- `knowledge/chief-of-staff/audit/`
- `knowledge/chief-of-staff/workbench/`

这组目录与当前宿主直接消费的 `docs/execution/hermes-copilot-host/phase-1/schedules/*.json` 一起，应理解为当前 host 的 `support-object-set` 锚点：这里的路径引用用于说明对象落点与运行骨架，不等于 docs published-copy 目标；若要判断 owner、manifest 或发布纪律，应回到 object spec、runtime module plan 与治理矩阵。

## 3. 这件事为什么要排到第一优先级

- 当前总助已经具备 memory / cognition 底座雏形，但还缺一个能稳定吃进零散资料并沉淀为知识页的入口。
- 如果没有这一步，很多零散事实只能留在会话、草稿或人工回忆里，无法变成可复用的 LLM wiki 资产。
- schedule / cron / automation 仍然重要，但它们更适合建立在“已有可整理、可沉淀的知识对象”之上。

## 4. 与四层记忆系统的关系

- 身份层：总助拥有自己的专属知识空间与连续命名空间。
- 阶段记忆层：`inbox/` 先承接当前阶段仍未整理的零散资料。
- 组织共享层：`wiki/` 承接已经整理成可复用知识页的内容。
- 审计层：`audit/` 记录来源、编译过程、更新原因与写回痕迹。

## 5. 当前建议的最小实现顺序

### 5.1 第一步：目录先固定

- 已固定总助专属目录骨架。
- 先允许手工把资料扔进 `inbox/`。

### 5.2 第二步：建立最小资料对象约定

首批先支持最简单几类对象：

- `.md`
- `.txt`
- `.json`

必要时再扩展到更复杂格式。

当前对象规范主档位于：

- `TriCompany-copilot-host-assets/docs/workflow/chief-of-staff-llm-wiki-object-spec.md`

### 5.3 第三步：做最小 wiki 编译器

目标不是一开始就做通用知识图谱，而是先做：

- 主题识别
- 原文摘录
- 页面合并 / 更新
- 来源回链
- 更新时间戳

### 5.4 第四步：把 wiki 页面接回总助 recall

- 当前已补上 stable-only recall 与 all-pages recall 双模式。
- stable 仍保留更高可信级别，但不再要求只有 stable 页面才能被看见。
- inbox 原始资料仍不能直接替代更高可信 wiki recall 来源。

### 5.5 第五步：把后台自动整理与人工审批接起来

- 当前已补上 resident runner、reminder / email / checkpoint / workbench 的通用 task bus。
- 当前 `reviewing -> stable` 已要求人工审批通过，不能再仅靠 refresh 次数自动升格。
- 后续重点不再是“要不要自动触发”，而是继续扩主题页、审批治理和真实外部投递渠道。

当前这一阶段已经前进到：

- 已补上最小 page promotion 规则
- 已补上 phase-1 的 schedule / cron staging spec
- 已完成真实两轮 staging run，使当前总助页面进入 `stable`
- 已完成 stable recall checkpoint 审计
- 已补上前台知识工作台生成入口
- 已补上 resident runner 和通用 reminder / email / checkpoint 任务总线
- 已补上 all-pages recall 与人工审批语义

## 6. 当前已落地的首版实现

当前已经补上首版半自动链路骨架；当前宿主侧的实际运行实现位于 `TriCompany-copilot-host-assets/runtime/cognition/`，包含：

- `contracts/wiki_source_contract.py`
- `kernel/wiki_source_registry.py`
- `kernel/wiki_frontmatter.py`
- `kernel/wiki_page_registry.py`
- `dispatch/wiki_compiler.py`
- `tasks/wiki_ingest_task.py`
- `tasks/wiki_compile_task.py`
- `runners/wiki_refresh_runner.py`
- `providers/chief_of_staff_wiki.py`
- `tasks/wiki_promotion_task.py`
- `tasks/wiki_recall_checkpoint_task.py`
- `tasks/wiki_approval_task.py`
- `tasks/reminder_task.py`
- `tasks/email_task.py`
- `tasks/checkpoint_task.py`
- `tasks/registry_closeout_task.py`
- `tasks/wiki_workbench_task.py`
- `kernel/schedule_registry.py`
- `dispatch/task_resolver.py`
- `dispatch/failure_policy.py`
- `runners/audit_sink.py`
- `runners/cron_runner.py`
- `runners/resident_runner.py`
- `chief_of_staff_llm_wiki_refresh.py`
- `chief_of_staff_llm_wiki_validation.py`
- `chief_of_staff_wiki_recall_validation.py`
- `chief_of_staff_schedule_staging.py`
- `chief_of_staff_schedule_staging_validation.py`
- `chief_of_staff_knowledge_workbench.py`
- `chief_of_staff_wiki_approval.py`
- `chief_of_staff_resident_runner.py`

当前可从 `TriCompany-copilot-host-assets` 根目录直接执行：

- `python -m runtime.cognition.chief_of_staff_llm_wiki_refresh --page-id PAGE_ID --title TITLE`
- `python -m runtime.cognition.chief_of_staff_llm_wiki_validation`
- `python -m runtime.cognition.chief_of_staff_wiki_recall_validation`
- `python -m runtime.cognition.chief_of_staff_schedule_staging`
- `python -m runtime.cognition.chief_of_staff_schedule_staging_validation`
- `python -m runtime.cognition.chief_of_staff_registry_closeout_validation`
- `python -m runtime.cognition.chief_of_staff_knowledge_workbench`
- `python -m runtime.cognition.chief_of_staff_wiki_approval --page-id PAGE_ID --decision approved --reviewer REVIEWER`
- `python -m runtime.cognition.chief_of_staff_resident_runner --cycles 1 --interval-seconds 60`

这里的含义是：

- 已经具备“读取 inbox -> 编译 wiki -> 写入 audit”的首版可运行代码。
- 已经补上 stable-only 与 all-pages recall 两种可运行模式。
- 已经补上 `working -> reviewing -> stable` 的最小 page promotion 规则与审计动作。
- 已经补上 resident runner、workbench、reminder / email / checkpoint 的通用 task bus。
- 已经补上一条 `CENTRAL_REGISTRY_CLOSEOUT -> dispatcher -> audit` 的最小 bridge，可作为后续中央收口 workflow bridge 的宿主侧入口草案。
- 已经补上 reviewing -> stable 的人工审批语义，但还不是完整治理平台。

当前直接证据位于 `TriCompany-copilot-host-assets/` 下，具体包括：

- `docs/execution/hermes-copilot-host/phase-1/schedules/*.json`
- `knowledge/chief-of-staff/wiki/chief-of-staff-llm-wiki-semi-auto-current-state.md`
- `knowledge/chief-of-staff/audit/wiki-promotion-2026-04-20-172505-698372.json`
- `knowledge/chief-of-staff/audit/wiki-promotion-2026-04-20-172505-988181.json`
- `knowledge/chief-of-staff/audit/wiki-recall-checkpoint-2026-04-20-172506-005925.json`
- `docs/execution/hermes-copilot-host/phase-1/CHIEF-OF-STAFF-SCHEDULE-STAGING-VALIDATION.md`

本段中的路径应读作“当前宿主证据引用”：`schedules/*.json` 与 `knowledge/**` 文件用于证明 staging 链已经跑通，`CHIEF-OF-STAFF-SCHEDULE-STAGING-VALIDATION.md` 用于汇总验证结论；它们不自动提升为独立发布对象清单。

## 7. 当前 MVP 验收标准

- 总助专属目录存在并固定。
- 可以把至少 3 份零散资料放入 `inbox/`。
- 可以把这些资料整理成至少 1 页 `wiki/` 页面。
- `wiki/` 页面带来源指针或来源清单。
- `audit/` 至少能回答这页 wiki 来自哪些原始资料、何时整理、由谁触发。

当前首条验证方案位于：

- `TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/CHIEF-OF-STAFF-LLM-WIKI-MVP-VALIDATION.md`

## 8. 当前不应夸大的范围

当前不应写成：

- 完整 LLM wiki 产品已经实现
- 已有 production 级自动整理引擎
- 已有 production 级邮件 / webhook 投递
- 已有完整 stable 治理平台

当前更准确的写法是：

- “总助专属 LLM wiki 已提升为当前第一优先级实现任务，当前先做 inbox -> wiki -> audit 的最小闭环。”
- “首版半自动编译链骨架已经落地并有独立 validation 命令，但仍不是完整 LLM wiki 产品。”
- “stable-only recall gate 已落地，但是否把某页升格为 stable 仍需要显式判断，不自动等同于正式真源。”
- “当前已补上前台知识工作台、resident runner、all-pages recall 和通用任务总线骨架，但仍不是 production 级知识编排系统。”
- “当前人工审批已进入 stable promotion 语义，但仍只覆盖总助 wiki 路径，不等于全公司治理平台已完成。”

## 9. 直接相关文件

- `docs/engineering/cyber-company-four-layer-memory-collaboration-system.md`
- `docs/engineering/cognition-runtime-module-plan.md`
- `docs/engineering/ROADMAP.md`
- `TriCompany-copilot-host-assets/docs/workflow/chief-of-staff-llm-wiki-object-spec.md`
- `TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/CHIEF-OF-STAFF-LLM-WIKI-MVP-VALIDATION.md`
- `runtime/cognition/README.md`
- `TriCompany/.github/source-agents/ceo-chief-of-staff/ceo-chief-of-staff.memory.md`

