# Memory Layer Contract

## 认知层契约

- **经营节律记忆**：每周经营记录（operating records）、未决事项（unresolved items）、next actions 的当前状态——按周索引，跨周平移时保持连续性。
- **任务分派记忆**：当前阶段公司级任务、模块级任务、跨岗位协调事项的分配人、deadline 和完成状态。
- **授权矩阵记忆**：各岗位的决策权限边界、升级条件、签字权范围——当前版本由 `authorization-matrix.md` 定义。
- **协调链路记忆**：跨 C-suite 依赖链（CPO→CTO→Execution）、阻塞项和协调历史。
- **宿主资产记忆**：当前 Copilot-host 的 host-object manifest、support payload、binding profile 状态——追踪到每份资产的源侧版本。

## 写入边界

- 不写入具体模块的实现细节——那是 CTO 和各模块 Code Registry 的领域。
- 不写入产品需求排序——那是 CPO 的领域。
- 不写入岗位边界和 staffing 裁决——那是 CHO 的领域。
- 经营记录以周为单位维护，当前周文件是主要写入目标。

## 运行资产落点

- 经营记录：`docs/workflow/operating-records/` 下当前周
- 授权矩阵：`docs/workflow/ceo-chief-of-staff-authorization-matrix.md`
- 编排真源：`docs/workflow/chief-of-staff-rd-orchestration.md`
- Employee workspace：`TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/`
