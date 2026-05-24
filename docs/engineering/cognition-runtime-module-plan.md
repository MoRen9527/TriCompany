# TriCompany Cognition Runtime 模块落点

版本：V0.6
日期：2026-04-21
状态：chief-of-staff LLM wiki 已推进到 all-pages recall、workbench、resident runner、task bus 与人工审批语义阶段

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/cognition-runtime-module-plan.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: on-demand-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/engineering/cognition-runtime-module-plan.md
- supportSyncRule: 仅在成批发布或当前宿主重新显式依赖时追平 support 副本
- lastSyncedAt: 2026-04-28

## 1. 文档定位

本文把 `SkillSpec` 与通用 `ScheduleSpec` 在 `runtime/cognition` 的最小落点直接列出来，供后续实现、评审和 code-state 同步使用。

本文只回答两个问题：

- `runtime/cognition` 下一批应该新增哪些模块
- 这些模块怎样把 skill 命中与通用定时任务执行接到当前 copilot 宿主

除特别说明外，本文中的 skill 与更广泛 host-dispatch 相关模块仍属于未实现计划；chief-of-staff LLM wiki 的 phase-2 任务总线骨架已落地。

当前本文已回写到 `TriCompany/docs/engineering/` 作为技术真源与后续代码收敛锚点；但 chief-of-staff LLM wiki 的 phase-2 运行骨架当前仍主要位于 `TriCompany-copilot-host-assets/runtime/cognition/`。

与这条运行骨架直接协同的 `TriCompany-copilot-host-assets/knowledge/chief-of-staff/**` 和 `TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/schedules/*.json`，当前统一视为 `support-object-set`：它们属于宿主直接消费的 machine-readable 对象目录 / 对象集，不纳入 docs published-copy manifest，也不按 active / on-demand published-copy 的追平纪律处理。

只有在同时出现真实跨宿主分发、真实统一枚举需求和真实独立版本发布需求时，才讨论为这组对象单独建立 host object manifest；在它们仍是单宿主 staging 对象或 host-local working set 时，默认不拆独立 manifest。

## 1.1 当前第一优先级任务：Chief-of-staff LLM wiki

当前第一优先级不是继续扩 provider 数量，而是先把总助专属 LLM wiki 做出来。

目标是固定一套最小知识目录：

- `knowledge/chief-of-staff/inbox/`
- `knowledge/chief-of-staff/wiki/`
- `knowledge/chief-of-staff/audit/`
- `knowledge/chief-of-staff/workbench/`

并尽快跑通这条链：

1. 把零散资料投入 `inbox/`
2. 对资料做标准化、主题识别和来源登记
3. 生成或更新 `wiki/` 页面
4. 把编译结果和来源痕迹写入 `audit/`

当前阶段先允许手工投放 + 半自动整理，不要求一开始就后台全自动。

## 1.2 已落地的首批 chief-of-staff LLM wiki 模块

当前已经落地；当前宿主侧实现位于 `TriCompany-copilot-host-assets/runtime/cognition/` 下：

- `contracts/wiki_source_contract.py`
- `kernel/wiki_source_registry.py`
- `kernel/wiki_frontmatter.py`
- `kernel/wiki_page_registry.py`
- `dispatch/wiki_compiler.py`
- `tasks/wiki_ingest_task.py`
- `tasks/wiki_compile_task.py`
- `tasks/wiki_promotion_task.py`
- `tasks/wiki_recall_checkpoint_task.py`
- `tasks/wiki_approval_task.py`
- `tasks/reminder_task.py`
- `tasks/email_task.py`
- `tasks/checkpoint_task.py`
- `tasks/wiki_workbench_task.py`
- `runners/wiki_refresh_runner.py`
- `runners/audit_sink.py`
- `runners/cron_runner.py`
- `runners/resident_runner.py`
- `providers/chief_of_staff_wiki.py`
- `kernel/schedule_registry.py`
- `dispatch/task_resolver.py`
- `dispatch/failure_policy.py`
- `contracts/schedule_spec_contract.py`
- `contracts/run_record_contract.py`
- `chief_of_staff_llm_wiki_refresh.py`
- `chief_of_staff_llm_wiki_validation.py`
- `chief_of_staff_wiki_recall_validation.py`
- `chief_of_staff_schedule_staging.py`
- `chief_of_staff_schedule_staging_validation.py`
- `chief_of_staff_knowledge_workbench.py`
- `chief_of_staff_wiki_approval.py`
- `chief_of_staff_resident_runner.py`

这代表当前已经有一条可显式触发的半自动链：

1. 扫描 `knowledge/chief-of-staff/inbox/`
2. 标准化原始资料
3. 编译 wiki 页面
4. 写入 `knowledge/chief-of-staff/audit/`
5. 支持 stable-only 与 all-pages 两种 recall 模式
6. 允许通过 phase-2 schedule spec 连续执行 refresh -> promotion -> approval -> workbench / reminder / email / checkpoint

这不代表：

- 已有 production 级前台产品
- 已有真实外部邮件 / webhook 投递
- 已有完整多角色治理与审批平台
- 已把通用 skill 调度和 host dispatcher 一并完成

说明：当前虽已补上最小 page promotion 规则，但它仍只覆盖总助 wiki 当前状态页的 staging 路径，不等于更通用的审批 / 门禁平台已经完成。

## 2. 当前缺口

当前 `runtime/cognition` 已有三层：

- `contracts/`
- `kernel/`
- `providers/`

这三层足够支撑记忆、recall、session_end consolidate 和外部 provider 接入，但还缺四类能力：

1. 仍缺通用 `SkillSpec` 运行时契约与技能索引 / 命中层。
2. `host_dispatcher.py` 仍未落地；当前 schedule staging 仍直接在当前 copilot 宿主内执行。
3. 当前 delivery channel 仍只以文件落盘为主，未扩成 email / calendar / webhook 等真实多通道投递。
4. 当前人工审批只覆盖总助 wiki 稳定化路径，尚未扩成更广泛的 stable 治理平台。

这意味着当前可以“记住并回忆”，但还不能稳定地“命中技能”或“执行通用定时任务”。

同时还缺一类能力：

1. 仍缺更多主题页 promotion 策略、审批人路由和长期治理报表，而不只是单页审批语义。

## 3. 最小新增模块

### 3.1 contracts/

- `contracts/wiki_source_contract.py`
  - 作用：定义一份 inbox 原始资料进入整理链时的最小形状。
  - 最小字段：`source_id`、`source_path`、`source_type`、`captured_at`、`topic_hints`、`trust_level`。

- `contracts/wiki_page_contract.py`
  - 作用：定义一份 wiki 页面的最小运行时形状。
  - 最小字段：`page_id`、`title`、`topic_tags`、`source_refs`、`updated_at`、`summary`。

  当前实现说明：当前首版直接把页面对象并入 `contracts/wiki_source_contract.py` 中的 `WikiPage`，后续如页面契约继续扩张，再拆成独立文件。

- `contracts/skill_spec_contract.py`
  - 作用：定义已批准 `SkillSpec` 的最小运行时形状。
  - 最小字段：`skill_id`、`skill_version`、`trigger_patterns`、`execution_steps`、`failure_guards`、`allowed_hosts`。

- `contracts/schedule_spec_contract.py`
  - 作用：定义通用 `ScheduleSpec` 的最小运行时形状。
  - 当前已补 `task_config`，可把 wiki/reminder/email/checkpoint/workbench 的执行参数挂进统一 payload。

- `contracts/task_target_contract.py`
  - 作用：统一不同定时任务目标的执行接口。
  - 覆盖目标：`skill`、`reminder`、`email`、`checkpoint`、`custom`。
  - 最小方法：`build_execution_payload()`、`validate_preconditions()`、`describe_audit_fields()`。

- `contracts/run_record_contract.py`
  - 作用：统一一次 schedule run 的审计形状。
  - 最小字段：`run_id`、`schedule_id`、`status`、`delivery_status`、`started_at`、`ended_at`、`freeze_reason`。

### 3.2 kernel/

- `kernel/wiki_source_registry.py`
  - 作用：扫描并登记 `knowledge/chief-of-staff/inbox/` 下的可整理资料。
  - 边界：只负责索引资料与基础元数据，不直接生成 wiki 页面。

- `kernel/wiki_page_registry.py`
  - 作用：加载、查找和更新 `wiki/` 下的已生成页面。
  - 当前已补页索引、审批状态和 frontmatter 元数据更新能力。
  - 边界：只维护页面索引，不负责决定业务结论是否自动生效。

- `kernel/skill_registry.py`
  - 作用：加载已批准技能，支持按 `id/version` 查找。
  - 边界：只读已批准技能，不负责自动批准。

- `kernel/skill_matcher.py`
  - 作用：在新任务进入前做关键词/规则级轻量命中。
  - 边界：只负责命中建议，不直接触发自动执行。

- `kernel/schedule_registry.py`
  - 作用：加载、启停和枚举已批准 `ScheduleSpec`。
  - 当前已可解析 `taskConfig` 并驱动通用 targetType 分发。
  - 边界：只维护 schedule 元数据，不直接运行任务。

### 3.3 dispatch/

- `dispatch/wiki_compiler.py`
  - 作用：把 inbox 原始资料编译成 wiki 页面更新计划，并生成对应 audit 元数据。
  - 边界：当前阶段先支持最小主题归类、页面合并与来源回链，不直接替代人工主档。

- `dispatch/task_resolver.py`
  - 作用：按 `target_type` 把一个 `ScheduleSpec` 解析到具体任务目标实现。
  - 当前已覆盖：`wiki-refresh`、`wiki-promotion`、`wiki-approval`、`wiki-workbench`、`reminder`、`email`、`checkpoint`、`registry-closeout`。

- `dispatch/host_dispatcher.py`
  - 作用：把执行请求桥接到当前 copilot 宿主；未来再平移到 `TriMC`。
  - 边界：当前阶段不能把它写成 `TriMC` 已经接管。

- `dispatch/failure_policy.py`
  - 作用：统一执行失败后的 `freeze`、`retry-then-freeze`、`escalate` 决策。

### 3.4 runners/

- `runners/wiki_refresh_runner.py`
  - 作用：以手工触发或后续 schedule 触发方式执行一轮 wiki 刷新。
  - 关键约束：当前阶段优先支持可审计的显式触发，不先做隐式后台常驻自动化。

- `runners/cron_runner.py`
  - 作用：负责 due-check、锁、并发策略、重试、失败冻结。
  - 关键约束：它是通用定时任务执行器，不是 skill 专属 runner。

- `runners/resident_runner.py`
  - 作用：以固定时隙循环调用 cron runner，形成后台常驻自动整理入口。
  - 当前已补同一时隙去重，避免在同一分钟重复执行同一 schedule。

- `runners/audit_sink.py`
  - 作用：统一落盘 run 结果、delivery 结果和 freeze/escalate 事件。

### 3.5 tasks/

- `tasks/wiki_ingest_task.py`
  - 作用：读取 inbox 原始资料并转成标准化 source 对象。

- `tasks/wiki_compile_task.py`
  - 作用：根据 source 对象生成或更新 wiki 页面，并把来源映射写入 audit。

- `tasks/skill_task.py`
  - 作用：装载已批准技能并生成注入 context。

- `tasks/reminder_task.py`
  - 作用：构建提醒类任务的执行负载。

- `tasks/email_task.py`
  - 作用：构建邮件类任务的内容、收件目标和 delivery 元数据。
  - 当前阶段仅生成可审计草稿，不直接发送外部邮件。

- `tasks/checkpoint_task.py`
  - 作用：执行固定检查点、周期验证和回放类任务。

- `tasks/registry_closeout_task.py`
  - 作用：读取 `CENTRAL_REGISTRY_CLOSEOUT` 对象、做最小结构校验，并桥接到当前宿主 dispatcher 与 audit 落盘。

- `tasks/wiki_workbench_task.py`
  - 作用：把 wiki 页面、审批队列、schedule 和最近审计聚合成前台知识工作台快照。

- `tasks/custom_task.py`
  - 作用：为后续非标准但已批准的定时任务留最小扩展口。

## 4. 最小执行链

建议先按下面这条链实现，不要一开始就做全自动大系统：

1. 先把零散资料投到 `knowledge/chief-of-staff/inbox/`。
2. `kernel/wiki_source_registry.py` 读取资料并建立最小 source 索引。
3. `dispatch/wiki_compiler.py` 生成 wiki 页面更新计划。
4. `tasks/wiki_compile_task.py` 把结果写入 `wiki/`，并把来源写入 `audit/`。
5. 当前已可通过在 `TriCompany-copilot-host-assets` 根目录执行 `python -m runtime.cognition.chief_of_staff_llm_wiki_refresh --page-id PAGE_ID --title TITLE` 显式触发这一链。
6. 当前已可通过 `include_stable_wiki_recall=True` 或 `include_all_wiki_recall=True` 选择 recall 模式。
7. 当前已可通过在 `TriCompany-copilot-host-assets` 根目录执行 `python -m runtime.cognition.chief_of_staff_resident_runner` 执行常驻时隙整理。
8. 在此基础上，再继续 `SkillDraft`、`SkillSpec`、真实 delivery channel 与 host dispatcher。

## 5. 为什么 cron runner 必须是通用的

如果把 cron runner 设计成 skill 专属，会直接产生三个问题：

1. 日历提醒与邮件投递不得不绕开统一审计链。
2. 固定检查点和周期验证会被错误地伪装成“技能调用”。
3. 未来迁到 `TriMC` 时会把任务目标语义和调度语义耦死，增加迁移成本。

因此，这里必须明确：

- `SkillSpec` 负责复用经验。
- `ScheduleSpec` 负责声明何时触发什么任务。
- `cron_runner` 负责调度一切已批准定时任务，而不是只调度 skill。

## 6. 当前宿主口径

- 当前不能写成“copilot 等同于 TriMC”。
- 当前可以写成：在 TriMC 尚未进入正式宿主切换前，copilot 宿主承担当前阶段 Task Main Controller 与 Autonomy Main Controller 的本地正式接管承载语义。
- 因此，skill 的当前阶段最后一跳可用实现应先在 copilot 宿主跑通。
- 同理，总助 agent 融合 Hermes 的通用 schedule / cron 能力，也应先借助 copilot 宿主完成试运行验证，再在未来正式上线切换阶段迁入 TriMC。
- 上述口径不改变这条硬边界：当前本地正式接管不等于 TriMC 正式宿主切换。

当前最后一跳执行桥应先落在本地正式接管的 copilot 宿主。

- 这代表当前阶段在 copilot 宿主验证技能注入、提醒、邮件与 checkpoint 的真实闭环。
- 这不代表 `TriMC` 已经完成正式宿主切换。
- 等这条链在当前宿主验证稳定后，才谈平移到 `TriMC`。

## 7. 直接相关文件

- `runtime/cognition/README.md`
- `TriMetaverse/docs/workflow/skill-spec.schema.json`
- `TriMetaverse/docs/workflow/schedule-spec.schema.json`
- `TriMetaverse/docs/workflow/virtual-company-handoff-objects.md`
- `docs/engineering/hermes-memory-subsystem-comparison.md`
- `docs/registry/code-state.md`
