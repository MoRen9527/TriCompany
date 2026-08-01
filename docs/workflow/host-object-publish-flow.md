# Host Object Publish Flow

版本：V0.1
日期：2026-04-29
状态：员工生命周期对象发布流程；覆盖新员工入职、岗位职责变动、owner 迁移与源侧五件套增量更新

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/host-object-publish-flow.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/host-object-publish-flow.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-06-03

## 1. 文档定位

本文定义 TriCompany 源侧岗位 / 员工五件套、知识空间发布到当前 Copilot-host support root 的最小流程。它不只是“入职发布流程”，也是现有员工职责变动、owner 迁移和源侧五件套增量更新进入正式 live 的标准流程。

它覆盖三段内容：

1. 源侧员工五件套 scaffold / validation，即 `.agent.md`、`.soul.md`、`.memory.md`、`.colleagues.md`、`.social.md` 的最小合格模板与源码 / 消费资产边界检查。
2. host object payload，即 role / employee knowledge workspace 的 inbox、wiki、audit、workbench 目录和 host object manifest。
3. binding profile、live discovery、host object manifest 与 governance / handoff 回填的增量更新闭环。

它不覆盖 docs published-copy，也不自动启用 live `.github` agent。

岗位 / 职责交接流程的治理 owner 不由 source kit scaffold 自动承担：这部分由已启用的 `ChiefHumanResourcesOfficer`（CHO）设计 handoff checklist 并监督完成度；行政管理、秘书处制度和公司治理资料归已启用的 `ChiefAdministrativeOfficer`（CAO）/ `CompanyGovernanceRegistry` 侧管理。`CEOChiefOfStaff` 保留公司级协调、催办、升级与收口职责。

当前 TriCompany 仍处于研发调试阶段，岗位变动、岗位职责变动和公司流程变动允许作为正常迭代推进；但每次进入当前 live 前，仍必须走本文的 source -> support -> binding -> live -> manifest -> governance 回填链路。待流程成熟并进入正式授权矩阵后，同类变更需要由对应 owner 做显式验收或签字确认。

## 1.1 适用场景

以下变更必须使用本文流程：

1. 新固定员工入职或岗位启用。
2. 现有员工 `.agent.md`、`.soul.md`、`.memory.md`、`.colleagues.md`、`.social.md` 任一源侧五件套发生稳定职责、人格契约、协作关系或运行资产边界变更。
3. 岗位职责、长期 owner、registry owner、workflow owner 或专业判断 owner 发生迁移。
4. support object、binding profile、host object manifest、live discovery 或 live publish manifest 需要跟随源侧职责变化更新。
5. 当前 live 入口不变，但员工源侧定义或 support payload 需要增量刷新。

以下变更可不完整执行本文流程，但必须保留必要记录：

- 单次临时任务分派，且不改变长期 owner。
- 文案修订、不改变职责边界和 binding 的小修。
- 运行态 employee knowledge workspace 消费记录更新；这类记录属于 runtime / employee workspace，不回写源侧五件套。

## 2. 发布顺序

1. 先判断变更类型：新员工入职、现有员工职责变动、owner 迁移、源侧五件套增量更新，或 support / binding / live discovery 同步。
2. 若是新招聘固定员工，先用 source kit scaffold 生成源侧五件套；若是现有员工变更，先定位并更新 `TriCompany/source-agents/<employee-id>/<employee-id>.(agent|soul|memory|colleagues|social).md`。这些文件是源侧员工契约，不是 live agent-discovery 入口。
3. 再在 `TriCompany/` 源侧确认岗位 / 员工定义、agent 资产、四层记忆资产、岗位职责、协作关系和流程 owner；职责变动必须说明 previous owner、incoming owner、acting owner、生效边界和验收条件。
4. 再通过 source kit validator 确认 `.agent.md`、`.memory.md`、`.colleagues.md`、`.social.md` 只保留源侧员工契约，不混入运行消费记录，也不把当前宿主的具体 binding 路径写回源侧五件套；TriCompany 源侧五件套必须保留在 `source-agents/`，不得混入 `.github/agents/` 这个可发现 live discovery 目录。
5. 再通过 `runtime/cognition/knowledge_workspace.py` 确认 role / employee / org shared / audit workspace 的路径抽象。
6. 再通过 host object generator 或 `employee_host_publish` 生成 / 刷新 `TriCompany-copilot-host-assets/` 下的对象载荷。
7. 再确认 `TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json` 声明源侧生成规则。
8. 再登记或更新 `TriCompany-copilot-host-assets/host-object-manifest.json`。
9. 再更新 `TriCompany/.github/binding-profiles/<employee-id>.json`，让当前宿主 binding 事实跟随源侧职责变化。
10. 再判断是否需要更新 `TriMetaverse/.github` 或模块 `.github/agents/` 的唯一 live discovery 入口；如果 live entry 不变，也必须确认不需要新增第二个 discoverable agent。
11. 最后由 CHO / CAO / 对应专业 owner 完成 governance 或 handoff 回填；调试阶段可记录为当前阶段验收，成熟后必须按授权矩阵留下 owner 签字或等价批准记录。

补充治理：若该员工启用会引发岗位 / 职责交接、handoff checklist 或 completion tracking，相关流程设计与完成度监督由 `ChiefHumanResourcesOfficer`（CHO）主责；若事项属于秘书处、会议制度、行政流程或公司治理资料归属，则归 `ChiefAdministrativeOfficer`（CAO）/ `CompanyGovernanceRegistry` 治理侧处理。`CEOChiefOfStaff` 负责公司级协调和升级，但不改变本文件的源侧发布顺序。

职责变动的专业 owner 分工：

- ProductRegistry、PRD 归属、产品范围或用户价值相关变更，由 CPO 小乔确认。
- CodeRegistry、CodeGraph、工程门禁、测试 / 发布 readiness 或技术 owner 相关变更，由 CTO 小狄确认。
- 岗位启用、岗位职责、handoff checklist、completion tracking 或 owner 迁移，由 CHO 确认。
- CompanyGovernanceRegistry、秘书处机制、会议制度、治理文档归属或行政流程，由 CAO 确认。
- 中央战略、正式宿主边界、模块长期边界或授权矩阵变化，升级 CEO / BusinessStrategy。

## 2.1 增量更新门禁

增量更新不是“只改一个文件”。现有员工职责变动至少要检查：

1. 源侧五件套是否需要更新。
2. `docs/workflow/**`、`docs/registry/**`、`docs/product/**`、`docs/engineering/**` 是否需要回链或更新。
3. `TriCompany/.github/binding-profiles/<employee-id>.json` 是否需要重新生成。
4. `TriCompany-copilot-host-assets/knowledge/{roles,employees}/<employee-id>/**` 是否需要重新发布。
5. `TriCompany-copilot-host-assets/host-object-manifest.json` 是否反映最新 object set。
6. `TriMetaverse/.github` 或模块 `.github/agents/` live discovery 是否仍唯一且正确。
7. handoff / completion tracking 是否进入 `ready-for-acceptance` 或 `accepted`，以及是否需要后续成熟期签字。

若任一项无法判断，当前变更应标记为 `待确认` 或 `blocked`，不得写成已完成 live 变更。

## 3. 新员工源侧五件套命令

新招聘固定员工时，可先生成源侧五件套模板。示例：

```powershell
python -m runtime.cognition.employee_source_kit generate --source-root . --employee-id customer-success-officer --agent-name CustomerSuccessOfficer --role-title "客户成功负责人" --description "适用场景：客户成功、试点跟进、用户反馈收集、续费风险识别。" --role-scope "你负责把试点客户反馈整理成可复核的产品、交付和运营输入。" --display-name "小成"
```

该命令只生成源侧五件套模板，不登记 support host object manifest，也不启用 live agent。

如已手工创建五件套，至少应运行：

```powershell
python -m runtime.cognition.employee_source_kit validate --source-root . --employee-id customer-success-officer
```

validator 当前检查：

- 五件套文件是否齐全。
- `agent.md` 是否包含 frontmatter、认知分层约束，以及 employee knowledge workspace 与 runtime cognition state 的边界说明。
- `soul.md` 是否包含角色气质、对话风格和禁止退化。
- `memory.md`、`colleagues.md`、`social.md` 是否包含 `当前原则`、`运行资产落点`、`层契约` 与 `TRICOMPANY_COGNITION_HOME`。
- 源侧五件套是否误含 `阶段记忆记录`、`工作关系人物档案`、`社交事项记录`、`记录时间`、`最近整理时间` 等运行消费记录标记。
- 源侧五件套是否误含 `当前 live 入口位于`、`TriMetaverse/.github/agents/**`、`TriCompany-copilot-host-assets/knowledge/employees/**` 或 `.tricompany-cognition/employee/**` 这类 host binding marker。

当前 source kit 的 canonical 口径是：源侧五件套可以声明岗位稳定规则与 runtime 机制边界，但当前 live 入口、当前 support payload 路径和当前宿主阶段状态属于 host binding 事实，应登记到 `TriCompany/.github/binding-profiles/<employee-id>.json`；`TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json` 只保留生成规则与 binding 索引，而不是继续充当员工级宿主绑定正文。

当前 agent discovery 口径是：`TriCompany/source-agents/` 只是源侧五件套和中央发布源存放区，不是 live agent-discovery 入口；`TriCompany/.github/agents/` 可以作为 TriCompany 模块自己的可发现 agents 目录存在，但只能放已经明确发布为 live discovery 的 module registry agent 或代码 / 文档维护类 module-local agent，不得放 source-agent 五件套草稿，也不得放任何员工 discoverable live agent。中央 role、strategy 与 governance agent 当前仍以 `TriMetaverse/.github/agents/` 作为 live 面；模块级 registry agent 的目标形态是迁回对应模块自己的 `.github/agents/`。

所有可发现 live agent 都必须有明确的 canonical source 与唯一 discovery target：人格岗位 agent 对应 `TriCompany/source-agents/<employee-id>/`，并发布到 `TriMetaverse/.github/agents/` 当前 live 面；中央 strategy / governance agent 对应 `TriCompany/source-agents/registries/` 和 `trimetaverse-live-agent-publish-manifest.json`；已迁移的模块级 registry agent 以对应模块 `.github/agents/` 为 canonical live entry。源侧未发布或未绑定的岗位、监督类 agent 不得留在任何 `.github/agents/` 被发现。

动态 operating/support data 纪律同步固定为：`workbench/`、`ipd/cases/`、运行中案例、过程记录、临时笔记、runtime memory、会话沉淀等只允许落在 `TriCompany-copilot-host-assets/` 或 `.tricompany-cognition/**`。这类数据不得放回 `TriCompany/source-agents/`、`TriCompany/.github/agents/` 或 `TriCompany/knowledge/**` 源侧目录；一旦发现误放，必须先迁回 support/runtime，再复核 binding、manifest 与 live discovery 状态。相对地，IPD 规则文档、培训文档、流程说明和 `runtime/cognition/**` 下的规则实现代码继续保留在 `TriCompany` source 侧，它们不属于需要迁出的动态运营数据。

当前若在 `TriCompany/knowledge/**` 看到预创建空目录或旧迁移残留，也应按同一纪律清理掉，避免把它误判成现役 knowledge payload 承载面。当前现役 payload 以 `TriCompany-copilot-host-assets/knowledge/**` 和 `.tricompany-cognition/**` 为准。

### 3.1 模块 registry agent 迁移门禁

模块级 `<Module>BusinessStrategyRegistry`、`<Module>ProductRegistry`、`<Module>CodeRegistry` 的目标归属是对应模块，而不是长期集中在 `TriMetaverse/.github/agents/`。

迁移一个模块时必须按以下顺序执行：

1. 先确认模块事实真源：模块 `AGENTS.md`、`README.md`、`docs/registry/`、产品 / 技术文档和代码树。
2. 若模块侧已有 Product / Code registry agent，先把中央收口字段、BusinessStrategy 上游约束和治理口径合并进模块侧文件，不新建第二个同名 agent。
3. 若模块侧缺 BusinessStrategyRegistry，补齐模块侧 `BusinessStrategyRegistry.agent.md`，并明确它只负责模块级商业定位，不替代中央 `BusinessStrategy`。
4. 删除或退役 `TriMetaverse/.github/agents/` 下同名模块 registry agent，确保同一个逻辑 registry 在多 root workspace 中只有一个 discoverable live entry。
5. 更新 `TriCompany/source-agents/registries/trimetaverse-live-agent-publish-manifest.json`，把该模块标记为 module-local live entry。
6. 由 `CompanyGovernanceRegistry` 记录发布纪律、单一 discovery 和 CHO/CAO 边界；商业边界仍由中央 `BusinessStrategy` 裁决，产品 / 代码事实仍由模块 registry 输出。

当前 pilot 已扩展到 `Triavatar`、`Tristaciss`、`TriMC`、`Tride`、`Tripilot`、`Trideployment`、`TriTest`、`TriLC`、`TriWeb4`、`TriChain`、`TriMobile`、`TriMem`、`TriDev`、`vscodium` 与 `TriCompany` 的 registry 三件套；这些 registry 以各自模块 `.github/agents/` 为 canonical live entry，并要求中央同名 discovery 文件不再保留。

## 4. 当前员工对象发布命令

在 `TriCompany/` 仓库根目录执行。新员工入职、现有员工职责变动和源侧五件套增量更新，都应优先使用统一 publish wrapper：

```powershell
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee all
```

如只刷新单个员工对象集，可使用：

```powershell
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee rd-trainer
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee ceo-chief-of-staff
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee chief-product-officer
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee chief-technology-officer
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee chief-human-resources-officer
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee chief-administrative-officer
```

如需要拆分验证或局部排查，仍可分别执行底层命令：

```powershell
python -m runtime.cognition.employee_host_object_generation --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee all
python -m runtime.cognition.employee_host_binding_profile_generation --source-root . --employee all
```

该命令生成：

- `TriCompany-copilot-host-assets/knowledge/roles/rd-trainer/**`
- `TriCompany-copilot-host-assets/knowledge/employees/rd-trainer/**`
- `TriCompany-copilot-host-assets/knowledge/roles/ceo-chief-of-staff/**`
- `TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/**`
- `TriCompany-copilot-host-assets/knowledge/roles/chief-product-officer/**`
- `TriCompany-copilot-host-assets/knowledge/employees/chief-product-officer/**`
- `TriCompany-copilot-host-assets/knowledge/roles/chief-technology-officer/**`
- `TriCompany-copilot-host-assets/knowledge/employees/chief-technology-officer/**`
- `TriCompany-copilot-host-assets/knowledge/roles/chief-human-resources-officer/**`
- `TriCompany-copilot-host-assets/knowledge/employees/chief-human-resources-officer/**`
- `TriCompany-copilot-host-assets/knowledge/roles/chief-administrative-officer/**`
- `TriCompany-copilot-host-assets/knowledge/employees/chief-administrative-officer/**`
- `TriCompany-copilot-host-assets/knowledge/org/shared/**`
- `TriCompany-copilot-host-assets/knowledge/audit/**`
- `TriCompany-copilot-host-assets/host-object-manifest.json`
- `TriCompany/.github/binding-profiles/*.json`

canonical wrapper 可用于只刷新 RAndDTrainer；旧 `project_trainer_host_object_generation` module 仅作为兼容 alias：

```powershell
python -m runtime.cognition.rd_trainer_host_object_generation --support-root ..\TriMetaverse\TriCompany-copilot-host-assets
```

源侧等价发布清单是：

- `TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json`
- `TriCompany/.github/binding-profiles/*.json`

## 5. 当前不做

- 不把 source kit scaffold 单独写成完整招聘审批、授权矩阵或 live 启用流程；完整员工生命周期变更必须同时经过 source kit、support object、binding profile、live discovery 判断、manifest 与治理回填。
- 不让 source kit scaffold 自动更新 `TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json`；manifest 仍需在岗位 / 员工定义确认后显式登记。
- 不让 source kit scaffold 直接写入员工级 binding profile；binding profile 应由 `employee_host_binding_profile_generation` 基于已声明的 HostObjectSetDefinition 显式导出。
- 不把 RAndDTrainer、CHO 或 CAO 的当前 Copilot-host live 启用写成 TriMC 正式宿主切换。
- 不把 CEOChiefOfStaff 的新 role / employee payload 写成 live 入口替换；当前 live 入口仍是 `TriMetaverse/.github/agents/ceo-chief-of-staff.agent.md`，四层认知契约由 TriCompany 源侧五件套和 support employee workspace 承接。
- 不为 CPO / CTO 新建第二个 live agent 文件；当前 live 入口沿用 `TriMetaverse/.github/agents/chief-product-officer.agent.md` 与 `TriMetaverse/.github/agents/chief-technology-officer.agent.md`。
- 不把 ChiefHumanResourcesOfficer 或 ChiefAdministrativeOfficer 的源侧岗位定义、binding profile 或 support object 声明单独当作 live 上岗完成；live 状态必须同时以 source kit、binding profile、support manifest 和 live publish manifest 对齐为准。
- 不把 RAndDTrainer 的 support object payload 写入 docs published-copy manifest。
- 不把已退役的 `TriCompany-copilot-host-assets/knowledge/chief-of-staff/**` 重新恢复为活 support payload；当前总助对象只允许落在 `knowledge/roles/ceo-chief-of-staff/**` 与 `knowledge/employees/ceo-chief-of-staff/**`。
- 不预创建或跟踪 `.tricompany-cognition/employee/rd-trainer.md`；`.tricompany-cognition/**` 是运行态，只在实际 cognition 写入后出现。
- 不在尚未实现跨员工 LLM wiki refresh 和 schedule 模板前，声明完整 role / employee workspace 生产化。
- 不把当前调试阶段的快速职责调整写成成熟期免签流程；成熟后同类变更必须按 CHO / CAO / CPO / CTO / CEO 或 BusinessStrategy 的 owner 边界留下验收或签字记录。

## 6. 验证命令

在 `TriCompany/` 仓库根目录执行：

```powershell
python -m unittest runtime.cognition.employee_source_kit_validation
python -m unittest runtime.cognition.role_employee_workspace_validation
python -m unittest runtime.cognition.rd_trainer_host_object_generation_validation
```

CEOChiefOfStaff 的 legacy compatibility path 已完成 closeout 并退役；后续新增员工上岗仍应沿用 source kit scaffold / validation -> source definition -> support object -> live binding -> governance 回填的顺序。若该员工承担交接治理 owner，handoff checklist 与 completion tracking 由 `ChiefHumanResourcesOfficer`（CHO）负责设计和监督；若涉及秘书处或行政治理制度，则由 `ChiefAdministrativeOfficer`（CAO）/ `CompanyGovernanceRegistry` 侧负责归属。

后续现有员工职责变动、owner 迁移或五件套增量更新也应沿用同一顺序；区别只在于“生成 source kit”可替换为“更新并验证现有 source kit”，其余 support object、binding profile、manifest、live discovery 判断和 governance 回填不得跳过。
