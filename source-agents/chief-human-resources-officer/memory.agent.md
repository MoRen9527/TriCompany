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
