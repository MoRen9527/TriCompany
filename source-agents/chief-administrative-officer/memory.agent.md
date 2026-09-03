# Memory Layer Contract

## 认知层契约

- **文档归属记忆**：公司治理文档的归属岗位、维护责任和版本历史——哪个文档归谁管、最近谁改了、是否需要更新。
- **会议制度记忆**：会议类型（周会/专题会/评审会）、参与岗位、频次、产出物的归档路径。
- **行政流程记忆**：审批流程（谁→谁→谁）、签核标准、当前 pending 事项的状态追踪。
- **公司治理真源索引**：`CompanyGovernanceRegistry` 中所有治理文档的路径映射和版本。

## 写入边界

- 不写入会议讨论的具体业务内容——只记录会议制度本身（谁参与、何时开、产出放哪）。
- 不替代各个岗位自己的 registry 维护——CAO 维护的是治理制度的"元信息"，而非每个 registry 的业务内容。
- 不写入个人评价或绩效信息。

## 运行资产落点

- 公司治理真源：`TriMetaverse/docs/registry/company-governance-state.md`
- 行政流程记录：`TriCompany/docs/execution/administrative-records/`
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-administrative-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则
## 当前原则

- 源码侧只保留 CAO 记忆层的通用规则和边界，不写具体会议纪要、行政执行流水或审批过程记录。
- 当前 CAO 员工实例的阶段性记忆写入 support employee workspace 或 runtime cognition state。
- 稳定的行政治理结论优先回写 workflow、CompanyGovernanceRegistry、operating records 或正式制度文档。
- 未经确认的组织制度变更不自动升级成长期真源。

## 层契约
## 层契约

- memory 层用于承载当前 CAO 员工实例的行政上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 workflow、CompanyGovernanceRegistry、operating records 或正式制度文档。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
