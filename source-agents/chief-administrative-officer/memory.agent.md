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

- 公司治理真源：`TriCompany/docs/registry/company-governance-state.md`（TriMetaverse 侧同路径为字节级副本，本席同步）
- 行政流程记录：`TriCompany/docs/execution/administrative-records/`（候初始化——目录未建，B3/B4 执行波 2026-09-14 标注）
- 学习腿（知识工作区）：`TriCompany-copilot-host-assets/knowledge/employees/chief-administrative-officer/`（inbox/wiki/workbench/audit 四区，hermes-gov-p2 员工层管道落点）
- 宿主 binding 事实由 binding profile 承载，不入本件
- 运行腿：`TRICOMPANY_COGNITION_HOME`（.tricompany-cognition：employee 私域运行态/org 运行共享记忆/org 运行审计——机器写入，runtime cognition backend 驱动，复活时初始化）
- 学习腿（知识工作区）：`TriCompany-copilot-host-assets/knowledge/employees/chief-administrative-officer/`（inbox/wiki/workbench/audit 四区，hermes-gov-p2 员工层管道落点）

## 当前原则

- 纪要现势、归档队列、制度修订在途态是运行数据——写 runtime cognition 私域与治理工作面，不入本件。
- 记忆层承载制度流程上下文（生效版本/在途修订/归属裁决记录）。
- 已定稿制度晋升治理 registry。
- 归属不清只记「待裁归属+依据缺口」，不记臆断归属。

## 层契约

- memory 层用于承载当前 CAO 员工实例的行政上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 workflow、CompanyGovernanceRegistry、operating records 或正式制度文档。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
