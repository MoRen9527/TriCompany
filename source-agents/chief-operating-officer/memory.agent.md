# Memory Layer Contract

## 认知层契约

- **经营节律记忆**：每周经营节奏、关键里程碑、上线窗口、复盘周期的当前状态。
- **跨项目协调记忆**：各项目的 phase 状态、资源冲突点、关键依赖链——按时间线追踪。
- **复盘闭环记忆**：每次复盘的问题、责任人、改进措施、验证时间——追踪到闭合。
- **运营风险记忆**：当前活跃的风险项、缓解措施、触发条件和责任人。

## 写入边界

- 不写入各项目代码级的技术细节——那是 CTO 和各模块 Code Registry 的领域。
- 不写入产品需求的优先级排序——那是 CPO 的领域。
- 经营节律以周为单位追踪，不进行日内微观调度。

## 运行资产落点

- 经营记录：`docs/workflow/operating-records/` 下当前周
- 运营计划：`TriCompany/docs/execution/operational-plans/`
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主 binding 事实由 binding profile 承载，不入本件
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 节律执行态（周计划进度/窗口倒计时/复盘待办）是运行数据：写 operating records 当前周与 runtime cognition 私域，不入本件。
- 记忆层承载节律规则上下文：哪些节律在生效、owner 与触发条件。
- rollout 计划版本与就绪度判定属运行态；就绪标准沉淀为规则后入本件或 registry。
- readiness 薄弱的链路只记「候条件+缺口」，不记确定交付承诺。

## 层契约

- memory 层用于承载当前 ChiefOperatingOfficer 员工实例的阶段性上下文、待复核判断和任务连续性。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到对应正式真源。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
