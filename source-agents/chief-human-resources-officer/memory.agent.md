# Memory Layer Contract

## 认知层契约

- **员工名册记忆**：12 名员工的五件套状态、上岗进度、binding profile 状态和 governance 回填状态。
- **岗位定义记忆**：每份岗位 JD、决策权限矩阵、汇报关系和协作关系的当前版本。
- **交接记录记忆**：每次 handoff checklist 的执行状态（drafted→ready-for-execution→in-progress→ready-for-acceptance→accepted）。
- **组织变更记忆**：岗位创建、职责变更、owner 迁移的时间线和审批记录。

## 写入边界

- 不写入员工绩效数据或敏感人事信息。
- 不写入非岗位相关的个人评价——memory 层只记录组织治理事实。
- 岗位定义以源侧五件套和 contract YAML 为准，memory 层是索引和状态追踪。

## 运行资产落点

- 员工名册：`TriCompany/docs/registry/employee-roster.json`
- 岗位治理状态：`TriCompany/docs/registry/staffing-state.md`（待初始化）
- 交接记录：`TriCompany/docs/execution/handoff-records/`
- 宿主 binding 事实由 binding profile 承载，不入本件
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `chief-human-resources-officer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 当前原则

- handoff 事项现势（状态机字段落点/验收窗口/催办时点）是运行数据——写 handoff 机器对象与 runtime cognition 私域，不入本件。
- 记忆层承载验收上下文（在办批次读数/待复审清单/版本差标注）。
- 已闭环交接留痕 handoff 对象与 operating records。
- 事实未定性只记「待确认+定性候方」，不虚构 staffing 确定性。

## 层契约

- memory 层用于承载当前 CHO 员工实例的组织上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 workflow、CompanyGovernanceRegistry、operating records 或正式制度文档。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
