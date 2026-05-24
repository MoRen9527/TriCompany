# TriCompany Agent Rules

## Module Role

- TriCompany 是虚拟公司的研发仓与经营编排孵化仓。
- 它负责沉淀虚拟公司的产品文档、技术设计、registry、总助 agent 草案、Hermes 融合草案和当前阶段 Copilot 试运行宿主资产。
- 它不是中央战略仓，不是正式运行宿主，也不是当前阶段的 Task Main Controller 或 Autonomy Main Controller 正式承载仓。

## Current Status

- 当前仓库为 V0.1 初版研发基线。
- 当前已进入“试运行中的新仓”状态，但是否升级为正式模块待确认。
- 当前路线已调整为先在 TriCompany 融合 Hermes，再把当前阶段 Copilot 宿主资产落到 .github。
- 这代表 TriCompany 承载试运行宿主资产，不代表正式宿主已经切换到 TriCompany。
- CPO / CTO 已在当前 Copilot-host live 入口上岗，并已补入 TriCompany 源侧五件套与 role / employee support object 生成链；这不代表 TriMC 正式宿主切换，也不代表生产级 Hermes 接入完成。

## Strategy Delegation

- 总商业模式、正式模块地位、宿主切换、TriCompany 是否升级为中央正式模块，先咨询 TriMetaverse/BusinessStrategy。
- 秘书处、行政管理和公司治理资料归属，先对齐 CompanyGovernanceRegistry；人力资源、岗位启用和职责交接治理归 ChiefHumanResourcesOfficer（CHO）侧，二者不要混写。

## Local Fact Sources

- 产品事实优先看：README.md、docs/product/、docs/registry/product-state.md
- 技术事实优先看：docs/engineering/、docs/workflow/、docs/registry/code-state.md
- agent、Hermes 融合与 Copilot 宿主事实优先看：.github/source-agents/、.github/agents/、.github/binding-profiles/、.github/instructions/、.github/prompts/

## Current Registries

- TriCompanyBusinessStrategyRegistry
- TriCompanyProductRegistry
- TriCompanyCodeRegistry

当前 registry agent canonical discovery 位于 `TriCompany/.github/agents/`。`TriCompany/.github/source-agents/` 是源侧发布与员工五件套区域，不是模块 live discovery；两者可以同仓并存，但不得混放 source-agent 草稿与可发现 module agent。中央同名 discovery 文件不应在 `TriMetaverse/.github/agents/` 并行保留；中央只通过 manifest 和 registry closeout 工作流路由本模块 registry。

## Update Discipline

- 必须明确区分“已落地”“草案中”“待确认”“待宿主验证”。
- 不要把“已完成生产级 Hermes 接入”“已完成正式宿主部署”“CPO / CTO 当前 Copilot-host live 上岗”等同于“TriMC 正式宿主上岗”“TriCompany 已成为正式主控宿主”，除非仓库里已经有真实证据。
- 形成跨仓长期有效的边界结论后，再同步回 TriMetaverse 的 registry 与制度层。
