# Hermes Memory 子系统对照与技能缺口

版本：V0.1
日期：2026-04-18
状态：已存档；由 TriCompanyCodeRegistry 按明确要求维护

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/hermes-memory-subsystem-comparison.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: on-demand-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/engineering/hermes-memory-subsystem-comparison.md
- supportSyncRule: 仅在成批发布或当前宿主重新显式依赖时追平 support 副本
- lastSyncedAt: 2026-04-28

## 1. 文档定位

本文用于把“原版 Hermes memory 子系统 vs 当前总助融合版”的长期技术结论存档到源代码仓库中，供后续实现、代码评审和 registry 更新直接引用。

本文只覆盖以下范围：

- 原版 Hermes 冻结参考副本中的 `memory_provider.py`、`memory_manager.py`、`memory_tool.py`
- 当前 `TriCompany-copilot-host-assets/runtime/cognition/` 原型
- 当前 `CEOChiefOfStaff` 总助五件套、会议 prompt 与 Code Registry 的融合边界

本文不回答以下问题：

- Hermes 全量 CLI / web / gateway / cron 宿主能力是否全部吸收
- TriMC 正式宿主是否已切换
- 是否已完成 production 级 Hermes 集成

## 2. 当前结论摘要

- 当前已吸收 Hermes 的 memory / metacognition 主干，不是只借了概念名词。
- 当前最成熟的吸收结果是跨会话长记忆、统一 recall/consolidate 契约、私域/共享/审计三层命名空间，以及单外部 provider 约束。
- 当前尚未形成“复杂任务完成后自动提炼技能，再在后续任务里自动命中复用”的闭环。
- 当前也尚未形成覆盖 skill、提醒、邮件、检查点等通用定时任务的 schedule / cron 运行时，更没有把它与子代理观察结果、技能注册、自主进化串成一体化闭环。
- 在 TriMC 尚未进入正式宿主切换前，若要把 skill 做到真正可用，当前阶段的最后一跳应先在本地正式接管的 copilot 宿主跑通。
- 若要给总助 agent 融合 Hermes 风格的通用 schedule / cron 能力，也应先借助当前 copilot 宿主做试运行验证，再在未来正式上线切换阶段迁入 TriMC。

## 3. 总表：原版 Hermes memory 子系统 vs 当前总助融合版

| 维度 | 原版 Hermes memory 子系统 | 当前总助融合版 | 当前判断 |
| --- | --- | --- | --- |
| 核心目标 | 给 agent 提供跨会话记忆、回忆、写回、会话结束提炼能力 | 给总助与后续员工提供统一 cognition 内核、私域/共享/审计三层记忆、会议链路收口和外部后端接入能力 | 已吸收主干目标，但当前范围聚焦虚拟公司总助与本地正式接管 |
| memory_provider | 定义记忆后端统一接口：可用性、初始化、prefetch、sync_turn、tool schema、session_end、delegation 等 | 已重写成 TriCompany 自己的 provider contract，但更窄，主要保留 recall、sync、session_end、命名空间约束 | 已有简化版，不是 1:1 全量复刻 |
| memory_manager | 统一调度 builtin 与 external provider，限制最多一个外部 provider，并做 recall context fencing | 已由 MetaCognitionKernel 承担 actor、provider、prefetch、sync_turn、session_end 和单外部 provider 限制 | 这块已经非常接近 Hermes 主干 |
| memory_tool | 提供可编辑的长期记忆工具，维护 MEMORY.md 与 USER.md，两者均可跨会话持久化 | 当前没有整套引入显式 memory_tool；现阶段更偏 provider 自动写私域/共享/审计，而不是给总助暴露显式长期记事工具 | 未全量吸收 |
| 记忆结构 | builtin memory + 单 external provider 的双层结构 | 统一内核 + 员工私域 + 组织共享 + 审计空间的三层拓扑 | 当前组织级结构比原版双层更贴合虚拟公司语义 |
| recall 注入 | 由 MemoryManager 统一清洗并包进 fenced `<memory-context>` | 已在 recall_context 中落实统一清洗、fencing 与系统说明注入 | 已有，且已验证 |
| 跨会话长记忆 | 明确支持跨会话 recall 与 turn 后写回 | 已完成本地私域/共享/审计落盘、跨实例 recall，以及 Supermemory schema / SDK seam / live smoke | 这是当前最成熟的一条 |
| 外部记忆后端 | builtin + 1 external provider | 当前也限制单外部 provider，并实现了 external adapter、HTTP backend、Supermemory backend、SDK seam | 已有原型，验证深度较高 |
| 自动提炼技能 | 通过 on_session_end、on_pre_compress、on_delegation 等钩子为技能提炼留口子，但并非自动技能工厂 | 当前只有会后收口、session_end consolidate、会议复盘和经营对象，没有自动技能文档提炼与复用链路 | 当前没有 |
| 自主进化闭环 | 从接口上支持“做完后沉淀”，但闭环依赖更上层逻辑 | 当前更像“会记、会回忆、会收口”，还不是“自动形成并修正技能系统” | 当前没有完整闭环 |
| 子代理结果观察 | 有 `on_delegation` 钩子，可在父代理侧观察子代理结果 | 当前自定义 provider contract 没有把这条观察链直接带过来 | 当前没有 |
| Cron / 定时任务 | provider 初始化参数兼容 cron 平台语境，但 memory 子系统本身不是完整 cron 执行器 | 当前只有经营流程和会议编排语义，没有完整通用定时任务执行器；当前阶段若要补齐，应先在 copilot 宿主验证覆盖 skill、reminder、email、checkpoint 的可用闭环 | 当前没有完整实现 |
| 总助接入深度 | 通用 memory 骨架，不关心具体岗位 | 当前已接到总助五件套、会议 prompt、registry 路由、support root 和 phase-1 验证链里 | 这是当前融合版相对原版的增强点 |

## 4. 为什么“自动提炼技能”现在还没有

当前没有自动提炼技能，不是因为我们完全没吸收 Hermes，而是因为当前只把 memory / metacognition 主干接进了总助，没有把“任务经验 -> 技能资产 -> 自动命中复用”的后半段工程化出来。

具体缺口有 6 个：

1. 当前 `runtime/cognition` 的 contract 重点是 recall、sync、session-end consolidate，不是任务经验抽象。
2. 当前 session-end 写回的是私域摘要、共享结论和审计轨迹，不是 SkillDraft 或 SkillSpec 这种独立技能对象。
3. 当前仓库里没有独立的技能注册表、技能 schema、技能版本和批准门禁。
4. 当前没有“下一次任务进来时，自动匹配历史技能并注入”的命中机制。
5. 当前没有“自动提炼后必须经谁审阅、谁批准、何时升级为稳定技能”的治理规则。
6. 当前自定义 contract 还没有把原版 Hermes 中 `on_delegation` 这类对子代理结果的观察钩子纳进来，因此无法稳定吸收复杂任务分工的结果。

换句话说：

- 我们已经有“会记住做过什么”的能力。
- 我们还没有“把这件事自动抽象成可复用技能并在下次自动调用”的能力。

## 5. 最短实现路径

如果目标不是一次性做完整自主进化系统，而是最短路径把“自动提炼技能”做出来，当前最短实现路径如下。

### 第一步：先生成 SkillDraft，而不是直接自动生效

- 在 `session_end` 之后新增一个可选的 SkillDraft 提炼步骤。
- 只对明确完成的复杂任务生成草稿，例如：部署、修 bug、验证链路、回迁、宿主迁移验证。
- SkillDraft 最少包含：
  - 触发条件
  - 前置条件
  - 执行步骤
  - 失败护栏
  - 证据引用
  - 适用范围与不适用范围

建议先把草稿落在文档层，而不是直接作为运行时自动技能：

- `TriCompany-copilot-host-assets/docs/execution/skills-drafts/`

这样可以先建立证据链，不会把未审阅内容直接变成自动行为。

当前已补齐最小对象规范入口：

- `TriMetaverse/docs/workflow/skill-spec.schema.json`
- `TriMetaverse/docs/workflow/schedule-spec.schema.json`
- `docs/engineering/cognition-runtime-module-plan.md`

### 第二步：把 Code Registry 作为批准门禁，而不是让总助自我批准

- TriCompanyCodeRegistry 负责判断某份 SkillDraft 是：
  - 草稿
  - 可试运行
  - 已稳定
- CTO 上岗后，再把批准权逐步转交给技术负责人。
- 当前阶段总助只负责触发草稿生成和协调收口，不负责单独宣布“技能已经稳定”。

### 第三步：建立最小技能索引，而不是先做全自动自主进化

- 为已批准技能建立一个最小索引文件，记录：
  - 关键词
  - 适用任务类型
  - 前置条件
  - 关联实现文件
- 在任务进入前，由内核做一次轻量匹配；命中后把技能内容作为附加 context 注入。

最初不需要做复杂 embedding 检索；先做规则命中和关键词命中就够了。

### 第三步半：先让 skill 在 copilot 宿主可用，再谈未来迁移

- 当前阶段不要把“最终正式归属”写死在 copilot 宿主，但应把“当前最后一跳可用实现”先落在 copilot 宿主。
- 具体含义是：技能命中后，当前由本地正式接管的 copilot 宿主负责把技能 context 注入到总助实际工作流中，并跑通一次真实任务闭环。
- 只有当这条链在当前宿主里可用，未来迁移到 TriMC 才有意义；否则只是把未验证的设计平移到新宿主。

### 第三步半之后：补最小 cron / 定时复杂任务能力

- 不要一上来实现全功能调度器，先做最小 schedule 对象。
- schedule 对象应服务所有已定义定时任务，不只 SkillDraft / SkillSpec；它至少要能表达 skill、reminder、email 和 checkpoint 四类目标。
- 首批 cron 场景只建议覆盖：
  - 周期性验证
  - 经营提醒
  - 会前邮件与固定邮件投递
  - 固定检查点回放
  - 已批准复杂任务或已批准技能的定时触发
- 当前阶段执行器仍以 copilot 宿主为承载，重点是验证“能定时、能执行、能落审计、能冻结失败”，不是先追求大规模自动化。

### 第四步：最后再补自动闭环，而不是一开始就宣称“自主进化”

只有在以下条件都满足后，才适合继续往自主进化闭环推进：

1. SkillDraft 模板稳定。
2. Code Registry 审阅门禁稳定。
3. 技能命中误报率可接受。
4. 技能内容不会越权改写正式边界。
5. CTO 已上岗或已有明确技术 owner。

在这之前，最合理的定位是：

- “半自动技能草稿提炼 + 人工批准 + 规则命中注入”

而不是：

- “总助已经可以自主进化”

## 6. 当前建议

当前最值得优先推进的，不是继续扩大 provider 数量，而是先把下面这条链补齐：

1. 复杂任务完成
2. session_end 生成 SkillDraft
3. Code Registry 审阅并登记
4. 下次任务前轻量命中
5. 命中后再决定是否真正自动调用

这样做的原因是：

- 它与当前 docs-first + registry 治理模式兼容。
- 它复用现有 recall / consolidate 内核，不必重做宿主。
- 它能在不夸大“自主进化”的前提下，尽快把“经验复用”做成真实能力。

## 6.1 当前宿主口径

- 当前不能写成“copilot 等同于 TriMC”。
- 当前可以写成：在 TriMC 尚未进入正式宿主切换前，copilot 宿主承担当前阶段 Task Main Controller 与 Autonomy Main Controller 的本地正式接管承载语义。
- 因此，skill 的当前阶段最后一跳可用实现应先在 copilot 宿主跑通。
- 同理，总助 agent 融合 Hermes 的通用 schedule / cron 能力，也应先借助 copilot 宿主完成试运行验证，再在未来正式上线切换阶段迁入 TriMC。
- 上述口径不改变这条硬边界：当前本地正式接管不等于 TriMC 正式宿主切换。

## 7. 主要证据入口

- `vendor/reference/hermes-agent-memory/src/memory_provider.py`
- `vendor/reference/hermes-agent-memory/src/memory_manager.py`
- `vendor/reference/hermes-agent-memory/src/memory_tool.py`
- `TriMetaverse/docs/workflow/skill-spec.schema.json`
- `TriMetaverse/docs/workflow/schedule-spec.schema.json`
- `docs/engineering/cognition-runtime-module-plan.md`
- `runtime/cognition/contracts/provider_contract.py`
- `runtime/cognition/kernel/meta_cognition_kernel.py`
- `runtime/cognition/kernel/recall_context.py`
- `runtime/cognition/providers/`
- `runtime/cognition/integration_validation.py`
- `runtime/cognition/backend_validation.py`
- `runtime/cognition/supermemory_live_validation.py`
- `TriMetaverse/.github/agents/ceo-chief-of-staff.agent.md`
- `docs/registry/code-state.md`
