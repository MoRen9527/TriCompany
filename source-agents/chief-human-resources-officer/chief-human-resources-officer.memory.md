# ChiefHumanResourcesOfficer 配套记忆

本文件是 TriCompany 源侧认知层契约，只定义 ChiefHumanResourcesOfficer memory 层的用途、写入边界和运行资产落点；不记录具体阶段记忆、任务记录或运行同步摘录。

## 当前原则

- 源码侧只保留 CHO 记忆层的通用规则和边界，不写具体交接流水、人员记录或启用审批过程记录。
- 当前 CHO 员工实例的阶段性记忆写入 support employee workspace 或 runtime cognition state。
- 稳定的组织治理结论优先回写 workflow、registry 或正式制度文档。
- 未经确认的组织变更不自动升级成长期真源。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-human-resources-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- memory 层用于承载当前 CHO 员工实例的组织上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 workflow、CompanyGovernanceRegistry、operating records 或正式制度文档。