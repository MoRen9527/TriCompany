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
- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-human-resources-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `chief-human-resources-officer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 当前原则
## 当前原则

- 源码侧只保留 CHO 记忆层的通用规则和边界，不写具体交接流水、人员记录或启用审批过程记录。
- 当前 CHO 员工实例的阶段性记忆写入 support employee workspace 或 runtime cognition state。
- 稳定的组织治理结论优先回写 workflow、registry 或正式制度文档。
- 未经确认的组织变更不自动升级成长期真源。

## 层契约
## 层契约

- memory 层用于承载当前 CHO 员工实例的组织上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 workflow、CompanyGovernanceRegistry、operating records 或正式制度文档。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
