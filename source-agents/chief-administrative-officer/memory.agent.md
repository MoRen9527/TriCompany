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
- Employee workspace：`TriCompany-copilot-host-assets/knowledge/employees/chief-administrative-officer/`
