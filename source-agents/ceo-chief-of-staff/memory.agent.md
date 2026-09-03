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

- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME`（认知层状态与派生资产落点）

- 经营记录：`docs/workflow/operating-records/` 下当前周
- 授权矩阵：`docs/workflow/ceo-chief-of-staff-authorization-matrix.md`
- 编排真源：`docs/workflow/chief-of-staff-rd-orchestration.md`
- Employee workspace：`TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/`

## 当前原则
## 当前原则

- 源码侧只保留通用记忆管理规则、边界说明和迁移约束。
- 具体员工阶段记忆、任务上下文、命名记录和运行同步摘录写入 support employee workspace 或 runtime cognition state。
- 已稳定且需要成为项目事实的内容，按文档纪律回写 `docs/`、`docs/registry/` 或 operating records，不反向堆回本文件。
- `soul` 属于身份气质层，不与普通记忆混写。

## 层契约

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
## 层契约

- memory 层用于承载员工实例的阶段性记忆、任务上下文、运行同步摘录和待复核判断。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 当记忆内容沉淀为稳定事实时，应升级到对应产品、技术、workflow、registry 或 operating record 文档。
