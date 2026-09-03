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
- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-operating-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 源码侧只保留 记忆 的通用规则和边界，不写运行消费数据。
- ChiefOperatingOfficer 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。
- 若某条内容经复核后成为稳定事实，应晋升到 对应 product、engineering、workflow、registry、training 或 operating record 真源。
- employee id 固定为 `chief-operating-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。

## 层契约

- memory 层用于承载当前 ChiefOperatingOfficer 员工实例的阶段性上下文、待复核判断和任务连续性。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到对应正式真源。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
