# TriCompany 总助研发编排

版本：V0.2
日期：2026-04-27
状态：补充多负责人分诊、耐久记忆升级与源仓/宿主边界口径

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: active-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/chief-of-staff-rd-orchestration.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-05-24

## 1. 文档定位

本文用于定义 TriCompany 当前阶段的总助研发编排方式。它描述的是“在模块源仓里，总助如何协同文档、registry、宿主资产发布与后续岗位”，不是正式宿主 runtime 说明。

本文默认以 `TriCompany/` 为模块真源，以 `TriCompany-copilot-host-assets/` 为当前 Copilot 宿主支撑包，以 `TriMetaverse/.github/` 为当前 live 宿主入口；因此它讨论的是源仓侧编排，不等于 live 入口本身，也不等于 TriMC 正式宿主切换。

## 2. 当前编排目标

1. 让总助成为 TriCompany 当前阶段的研发协调中枢。
2. 让产品、技术和执行层文档保持同步。
3. 让当前阶段 Copilot 宿主相关源码资产统一在 TriCompany/.github 收口，并通过 manifest / 发布动作进入当前 live 宿主入口。
4. 把 Hermes 融合结论沉淀到可直接调用的总助套件里。
5. 协调当前已上岗的 CPO / CTO 接手产品 / 技术真源，并保留未来宿主迁移接口。
6. 以正式签发形式让 CEO 与总助的阶段性对齐结论可以稳定升级到项目真源，而不是停留在会话里。

## 3. 当前参与角色

- TriCompanyCEOChiefOfStaff：当前总调度与收口中枢。
- TriCompanyProductRegistry：产品真源与产品状态；经营 owner 为 ChiefProductOfficer（CPO，小乔）。
- TriCompanyCodeRegistry：技术真源、结构状态、CodeGraph 摘要与执行层纪律；经营 owner 为 ChiefTechnologyOfficer（CTO，小狄）。
- RAndDTrainer：项目培训内容、模块导读、代码导读和新人学习路径。
- TriCompany/.github：模块侧 `.github` 研发与发布真源。
- TriCompany-copilot-host-assets：当前 Copilot 宿主支撑包与发布后验证支撑层。
- TriMetaverse/.github：当前 live 宿主入口。
- CEO / 当前操作者：当前最高输入来源。
- ChiefProductOfficer：当前 Copilot-host live 阶段已上岗，接手产品范围、MVP、需求优先级、Product Registry 与产品真源持续优化。
- ChiefTechnologyOfficer：当前 Copilot-host live 阶段已上岗，接手技术方案、交付架构、测试 / 发布 readiness、Code Registry 与技术真源持续优化。
- ChiefHumanResourcesOfficer：当前 Copilot-host live 阶段已上岗，接手岗位启用、staffing governance、职责交接流程与 completion tracking。
- ChiefAdministrativeOfficer：当前 Copilot-host live 阶段已上岗，接手行政管理、秘书处机制、会议制度、CompanyGovernanceRegistry 和治理文档归属。

## 4. 当前编排流

### 4.1 事项进入

- 任何关于虚拟公司研发、总助设计、Hermes 融合、.github 宿主资产、岗位准备或会议节奏的事项，先进入总助判断。

### 4.2 总助分诊

总助收到事项后，先判断属于哪一类：

- 产品范围、角色定位、路线优先级、Product Registry 事实维护：先路由 ChiefProductOfficer（小乔），并回链产品真源与 Product Registry。
- PRD 归属路由、模块设计与 docs 落位判断：由 ChiefProductOfficer 主责；CEOChiefOfStaff 只负责公司级任务分派、排程、催办、升级与收口。
- 技术设计、结构边界、CodeGraph、Hermes 融合与 .github 宿主资产：先路由 ChiefTechnologyOfficer（小狄），并回链技术真源与 Code Registry。
- 会议协调、纪要收口、动作项推进：走会议 prompt 与秘书处草案。
- 项目培训、模块讲解、代码导读、小白 onboarding：同步给 RAndDTrainer，并要求回链真源。
- 跨域问题：由总助组织产品与技术两侧共同收口。

在更多负责人正式上岗后，分诊口径继续扩成：

- COO：经营节奏、rollout、跨部门执行窗口、恢复与复盘闭环。
- CFO：预算、成本护栏、价格例外、结算映射与财务风险。
- CMO：品牌叙事、渠道规划、内容分发与需求捕获。
- CSO：线索管道、成交策略、商机推进与收入执行。
- CHO：岗位启用、人力资源、staffing governance、角色评分卡、跨岗位职责交接流程设计与完成度监督。
- CAO：行政管理、秘书处机制、会议制度、组织制度、CompanyGovernanceRegistry、治理文档归属和公司治理资料维护。

总助对这些事项的职责仍然是：先分诊、再对齐 owner、必要时升级给 CEO，不替代对应负责人长期代管。

固定 owner 分工：`ProductRegistry` 由 CPO 小乔管理，`CodeRegistry` 由 CTO 小狄管理，中央 `CompanyGovernanceRegistry` 由 CAO 管理；`CEOChiefOfStaff` 只负责路由、协调、催办、升级和中央收口，不长期代管具体 registry owner。

### 4.3 会议入口

- 开始正式讨论时，使用“开始会议”进入正式会议口径。
- 收口结论与动作项时，使用“结束会议”进入纪要与回填口径。

### 4.4 当前阶段宿主资产层

当前阶段宿主相关资产按三层组织：

- `TriCompany/.github/`：模块侧宿主源码与发布前收口资产。
- `TriCompany-copilot-host-assets/`：当前 Copilot 宿主支撑包、验证入口、baseline 与回滚材料。
- `TriMetaverse/.github/`：当前实际生效的 live 宿主入口。

模块侧至少要维护：

- 当前总助 contract 版本。
- 当前 soul / memory / colleagues / social 分层结论。
- 当前会议编排规则。
- 当前 registry 事实与待确认缺口。
- 当前 Hermes 融合与迁移清单。
- 当前 RAndDTrainer 培训目录、模块导读和新人学习路径。

后续新增固定员工、现有员工职责变动、owner 迁移或源侧五件套增量更新时，应先在 TriCompany 源侧完成岗位 / 员工定义、agent 资产、四层记忆资产、岗位职责、协作关系、流程 owner 与 role knowledge workspace 机制，再发布到当前宿主支撑包生成实际消费的 inbox、wiki、audit、workbench、schedule JSON 等对象载荷，并同步核对 binding profile、host object manifest、live discovery 与治理回填。CPO / CTO 本轮采用已有 `TriMetaverse/.github` live entry，不新建第二个 live agent 文件，而是补齐 TriCompany 源侧五件套与 role / employee support object payload。换宿主时迁移的是完整虚拟公司源侧定义和流程，而不是在新宿主重新招聘员工或重建流程。

`ChiefHumanResourcesOfficer`（CHO）与 `ChiefAdministrativeOfficer`（CAO）已按源侧链路完成当前 Copilot-host live 启用。CHO 主责制定岗位 / 职责交接流程、handoff checklist 与 completion tracking，并监督交接闭环；CAO 主责行政管理、秘书处机制、会议制度、CompanyGovernanceRegistry 和公司治理资料归属。CEOChiefOfStaff 保留公司级协调、催办、升级与收口职责，不再长期代管这些 owner。

本轮已为 `ChiefHumanResourcesOfficer` 和 `ChiefAdministrativeOfficer` 补齐 TriCompany 源侧岗位定义、五件套、binding profile、host object generation declaration 与 live discovery 入口；该状态只代表当前 Copilot-host live 启用，不等于 TriMC 正式宿主切换或完整授权矩阵生产化。

对应的最小交接治理真源当前落在 `TriCompany/docs/workflow/chief-human-resources-officer-handoff-governance.md`；后续若出现岗位启用、职责移交或长期 owner 切换，应按该文档的 checklist、状态机和验收口径执行。

员工生命周期变更的发布真源落在 `TriCompany/docs/workflow/host-object-publish-flow.md`。当前调试阶段岗位职责和公司流程允许快速迭代；成熟后，同类职责变动、岗位变动和流程变动应由 CHO / CAO / CPO / CTO / CEO 或 BusinessStrategy 按 owner 边界签字确认后再进入正式 live。

RAndDTrainer 当前已作为技术研发培训岗位进入 Copilot-host live 阶段；当前先由 CEOChiefOfStaff 同步项目新增设计、开发实现、模块边界和治理规则。已上岗 CPO / CTO 可分别同步产品、技术和工程流程培训输入。RAndDTrainer 的 role / employee workspace 对象生成、support payload 和 live 入口已具备最小闭环。

### 4.5 跨仓同步条件

当 TriCompany 内形成稳定跨仓结论后，总助才需要准备对外发布与同步，至少包括：

- 哪些结论已稳定。
- 哪些仍待验证。
- 哪些属于当前阶段本地正式接管资产。
- 哪些需要先发布到 `TriCompany-copilot-host-assets/` 再进入 live 宿主。
- 哪些需要升级为跨仓长期规则或中央层摘要。

### 4.6 耐久记忆升级规则

- 如果某项会议结论、边界判断或阶段性工作法需要进入项目耐久真源或岗位耐久记忆，先由总助提出写入建议。
- 建议里至少说明：写入内容、目标文件、写入原因、预计影响范围。
- 由 CEO 明确确认后，再执行仓库回填。
- 未确认的内容可以保留在会话记录、草稿或运行时层，但不自动升级成长期真源。

## 5. 当前约束

- TriCompany 当前既做研发，也承载模块侧宿主源码与发布准备资产，但不等于当前 live 宿主，更不宣称 TriMC 正式宿主运行。
- 总助可以组织与收口，但不长期代管产品、技术和公司治理 registry owner；CPO / CTO / CAO 已在当前 Copilot-host live 阶段分别接手 ProductRegistry、CodeRegistry 与 CompanyGovernanceRegistry 的管理入口。
- CPO / CTO 当前上岗不等于 TriMC 正式宿主切换，也不等于产品 / 技术授权矩阵已经全部生产化。
- RAndDTrainer 当前已进入 Copilot-host live 阶段；培训内容不替代项目真源，也不代表 TriMC 正式宿主切换。
- 未经 CEO 明确确认，不把会话记忆、运行时缓存或宿主侧临时补丁直接写成模块真源。

## 6. 下一阶段切换条件

当以下条件满足时，可进入下一阶段：

1. 总助首版 contract 在 TriCompany 内已稳定。
2. 模块侧 `.github` 宿主资产已收拢，且发布方向清晰。
3. Hermes 融合与迁移清单已明确。
4. 可持续 cognition 验证与会议回填链已稳定。
5. 最小 schedule / cron / automation staging 路线已明确，并至少完成一条闭环验证。

稳定后，由 CPO / CTO 输出首轮产品 / 技术接管判断，并决定哪些结论继续发布到支撑包、哪些进入 live 宿主、哪些只同步回 TriMetaverse 中央层。
