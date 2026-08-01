# 公司治理状态

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/registry/company-governance-state.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-06-08

## Registry 职责

- 本文件是 `CompanyGovernanceRegistry` 的公司治理事实工作层。
- 本文件记录组织制度、秘书处机制、会议治理、岗位边界、agent 发布纪律和治理文档归属。
- 经营 owner 为 ChiefAdministrativeOfficer（CAO）；CEOChiefOfStaff 只负责路由、协调、催办、升级和中央收口。

## 公司级文档规则

- 默认文档语言：中文优先。
- 除非有明确特殊原因，所有公司级、模块级、registry、workflow、产品、技术、执行、培训和经营记录文档应优先使用中文书写。
- 允许保留英文的情况：
  1. 专有名词、产品名、模块名、文件名、命令、代码符号、schema 字段、API 字段、错误类型、许可证和上游原文引用。
  2. 上游开源项目 `vendor/` 或 `reference/` 中保留原貌的文件。
  3. 对外发布、国际化、双语教程、英文 prompt / agent frontmatter 等确有目标读者或宿主格式要求的内容。
  4. 需要与第三方工具、协议、SDK、模型平台或文档规范保持英文一致的技术材料。
- 若同一文档同时面向内部治理和外部英文读者，应至少保证中文主说明完整，英文内容作为对照、引用或附录存在。

## 公司级状态术语

- **当前周维护面**：指同一时点唯一允许继续维护 active 未决事项的最新周 `OPERATING_PLAN` 与配套未决事项清单。它是维护入口，不是单条事项状态名。
- **单条事项状态**：指单个经营事项在当前周维护面中的推进状态。公司级规范默认只使用以下四类：
  1. `active`：当前正在推进，本周存在明确 owner 动作与预期产物。
  2. `frozen`：当前暂停推进，但未结项；必须保留 owner、恢复条件或升级路径。
  3. `stale-review`：因超过约定时间未续推而进入审查池，尚未完成 `active` / `frozen` / `closed` 定性。
  4. `closed`：事项已结项、取消或已从当前周维护面移出；若仍需追溯，只保留历史事实与 successor ref。
- 若需要描述 `frozen` 的更细原因，应写成正文补充说明或 `statusDetail`，例如“收口待定”“范围刷新待定”“等待重启裁定”，不额外新增新的公司级主状态名。
- **模块成熟度状态**：用于描述模块当前生命周期，不与单条事项状态混写。公司级规范默认使用以下标签：
  1. **现役模块**：已进入当前正式模块面，允许承接当前主线任务与持续治理。
  2. **占位模块**：已进入架构面，但当前不承诺现役能力，不得虚构实现进度。
  3. **待初始化模块**：占位模块的具体状态，表示 git / `README.md` / `docs/` 六件套 / CodeGraph 骨架或首个可验证切片尚待补齐。
  4. **待迁移模块**：历史能力仍在旧模块、旧路径或旧 owner 下，当前目标是向新的 canonical 归属收敛。
  5. **待归档兼容仓**：仅保留历史兼容、回放或迁移缓冲，不再作为长期独立主模块扩张。
- 当同一模块既是“占位”又能确定更具体边界时，正文优先使用更具体状态（如“待初始化模块”“待迁移模块”“待归档兼容仓”），必要时再补一句“当前仍属占位面”。
- 经营记录、会议纪要、秘书处回填和 registry 审稿时，必须先区分“当前周维护面”与“单条事项状态”，不得因为某周是 latest active week 就把其中每条事项都写成 `active`。

### 单条经营事项标准头

- 写入 operating record、会议纪要回填面或治理性 backlog 时，单条经营事项至少应显式标注以下字段，且字段名保持稳定：
  1. **事项 ID**
  2. **事项名称**
  3. **事项简介**
  4. **事项状态**
  5. **当前进度**
- 公司级推荐字段顺序为：
  1. 事项 ID
  2. 事项名称
  3. 事项简介
  4. 事项状态
  5. 状态说明（如有）
  6. 当前进度
  7. 来源
  8. 跨周情况 / 预警级别（如有）
  9. 当前动作
  10. 下一步
  11. 恢复条件或截止时间（按需）
  12. Owner
- 其中：
  - **事项简介** 用一句话说明“这件事是什么、为什么还留在当前周维护面”。
  - **当前进度** 用一句话说明已完成到哪里、当前卡在什么位置。
  - **事项状态** 只使用 `active` / `frozen` / `stale-review` / `closed` 四个公司级主状态。
  - **状态说明** 只用于补充 `frozen` 或 `stale-review` 的具体原因，例如“收口待定”“范围刷新待定”“等待重启裁定”。
- 若使用结构化 JSON，推荐字段映射为：`id`、`title`、`summary`、`status`、`statusDetail`、`currentProgress`、`nextAction`、`resumeCondition`、`owner`。
- 若使用 Markdown 未决事项清单，默认按上述字段顺序书写，避免每次重新发明标题或遗漏最基本的上下文。

### 单条经营事项 ID 前缀标准

- 下列前缀只用于**单条经营事项 ID**，不替代 `OPERATING_PLAN`、`BOARD_DIRECTIVE`、`PRD_OWNERSHIP_ROUTING` 等对象级编号。
- 公司级默认前缀如下：
  1. `ITEM-YYYYMMDD-序号`：当前周期新建的一般事项，默认前缀。
  2. `CARRY-YYYYMMDD-序号`：从前一周、前一月或更早周期平移过来的跨周续记项。
  3. `BLOCK-YYYYMMDD-序号`：明确阻塞主线推进、需要 owner 解阻的阻塞事项。
  4. `RISK-YYYYMMDD-序号`：需持续观察、可能升级但尚未进入正式升级链的风险事项。
  5. `ESC-YYYYMMDD-序号`：已经进入升级链、等待 CEO 或对应 owner 裁定的升级事项。
- **前缀表达的是事项来源或治理类型，不等于事项状态。**
  例如：`CARRY-*` 可以是 `active`，也可以是 `frozen` 或 `stale-review`；不能因为它是 `CARRY` 就默认等于 `frozen`。
- 若同一事项同时满足多个语义，优先顺序为：`ESC` > `BLOCK` > `RISK` > `CARRY` > `ITEM`；同一事项 ID 不叠加多个前缀。
- 当前经营记录若只是一般跨周事项，默认继续使用 `CARRY-*`；不要为了细分原因把前缀无限扩张。

### IPD case ID 治理标准

- `IPD case` 不沿用一般事项前缀，而是使用独立前缀：`IPD-*`。
- 自 2026-06-11 起，公司级治理要求 `IPD case` 统一采用 **`IPD-YYYYMMDD-文字简称-序号`**；不再新建 `IPD-001`、`IPD-002` 这类纯序号对象。
- `文字简称` 用于表达当前事项的最小可读主题，优先使用全大写 ASCII 短词；`序号` 固定三位，在同日同简称下从 `001` 开始递增。
- canonical 示例：`IPD-20260611-PLATFORM-001`。
- 一条 case 只允许存在一个 live canonical id；`case.json`、`intake-brief.json`、阶段 work item、reference 目录和会议纪要必须共用同一 id。
- 已存在的 legacy case 不强制重写历史档案，但新建 case、重放 case 或重新进入 live 流程时，应优先迁到日期前置命名。

## 治理说明

- 新增文档、重构文档或吸收上游资料时，先判断该文件是否属于 TriMetaverse / TriCompany 自有资料；自有资料默认中文化。
- 开源吸收链中的 `reference/` 与 `vendor/` 文件默认保持上游原貌；真正进入模块自研文档、registry 或 workflow 后，应转换成中文优先口径。
- Registry 摘要不得只保留英文标题而缺少中文解释，避免新人 agent 和岗位对象误读边界。

## vendor 与 .gitignore 治理规则

- 对存在治理中 `vendor/` 冻结基线的源侧模块，`vendor/` 默认进入模块自己的 `.gitignore`，用于隔离日常本地噪音和主 `CodeGraph` 查询视图。
- 这条规则**不改变** `vendor/` 作为冻结基线、需要被版本控制和审计的事实；已有受治理的 vendor 文件继续受 git 跟踪，后续有意升级 vendor 快照时，由对应 owner 显式纳入提交。
- `vendor/` 默认不进入模块主 `CodeGraph`；只有在开源吸收、差异拆解、adapter 映射或 schema 对照等专项任务下，才临时纳入 vendor 视图。
- `TriCompany-copilot-host-assets/vendor/` 不属于模块真源 `vendor/`；它只允许保留从源侧发布过来的冻结 `reference` 副本或当前宿主验证辅助代码，不得演化成 support 侧独立研发面。
- 新增正式模块时，`Discovery` 阶段的 `NewModuleBaselineRelease` 必须带上 `vendor-extraction-profile`，最少包含 source、version anchor、subpath 映射、patch 策略、回滚点与 license / 审计说明。

## Git Health 与本地提交治理规则

- `Registry` 负责维护各模块的 `Git Health` 事实：包括 dirty worktree 基线、已知未提交切片、风险说明和升级提示。
- `Registry` **不直接代替 owner 做本地提交**；本地提交责任仍归对应模块 owner 或当前实际开发 owner。
- 活跃模块应在以下任一时点做一次 `Git Health` 收口：形成稳定切片后、切换阶段前、交接 handoff 前，或跨过一个会议周期仍持续 dirty 时。
- 若本地脏改动需要继续保留，必须至少说明：原因、风险、是否已有可提交切片、预计收口时间。
- 跨过一个会议周期仍未收口的本地脏改动，应进入 operating record 的 `blockedItems` 或 `nextActions`，由秘书处和总助催办、由 CTO / owner 收口。

## 模块标配

- 架构表中的模块一旦被写成正式模块面，默认必须具备以下标配：
  1. 独立 git 仓。
  2. `README.md`。
  3. `docs/` 六件套文档基线：`product`、`engineering`、`execution`、`registry`、`workflow`、`training`。
  4. 根级 `.gitignore`，至少排除 `.codegraph/`、`.cursor/`、依赖目录、构建产物、环境文件和受治理 `vendor/` 噪音。
  5. 本地 `CodeGraph` 初始化与由对应 `CodeRegistry` 维护的摘要。
- 这条规则同样适用于占位 / 待初始化模块：即使模块暂时还没有现役源码，也应先补齐 git、README、docs 六件套和 CodeGraph 骨架，避免继续把模块资料散落在聊天、临时目录或中央仓。
- `CodeGraph` 是本地辅助索引，不替代源码、代码文档、`code-state.md` 或人工收口；允许只把摘要、排除规则、扫描时间和版本锚点写回 registry，不提交 `.codegraph/` 与 `.cursor/` 缓存。
- 若某模块缺失上述标配，应由 CTO 在发现当轮或下一轮优先补齐，再继续把它写成正式模块。
- 既有正式模块参与新任务时，`Discovery` 阶段也必须先形成 `ModuleTargetingReport`，并由 `TriDev` 完成 `ModuleReadinessInit`（标配审计与缺口 init）后，再进入后续开发阶段。
- 正式新模块必须走 `NewModuleBaselineRelease` 单项发布：在 `Discovery` 阶段先形成 `candidate`，完成 CPO/CTO/CAO 与总助/CEO 签核后升级 `approved`，再由 `TriDev init` 执行 `init` 落地模块骨架。
- `Registry` 在该流程里只负责事实登记与风险提示，不代替 owner 做模块初始化提交。

## 员工工具权限默认策略

- 赛博公司全员上岗默认持有 `execute`（bash/shell 执行）权限。
- `execute` 在 Agent 契约中统一标记为 `risk_level: high`、`requires_approval: true`。
- 后续由公司按岗位、模块和运行面需要，逐岗制定细则：决定是否禁用、缩窄 scope 或追加审批链条；细则未出前不收回默认权限。
- 当前已落地的四份人格 agent 合同（CEOChiefOfStaff、ChiefProductOfficer、ChiefTechnologyOfficer、RAndDTrainer）均已完成 `execute` 工具登记；未来新增固定员工上岗时同步补齐。
- 本策略的细则制定与维护由 CAO 主责，CHO 配合岗位启用侧执行。

## CTO 技术交付委托规则

- 生效日期：2026-07-16，CEO 口头指令，记录于 TriOPC Phase C 启动前。
- 标准技术交付流水线：**小全（FullStackDeveloper）编码 → 小柯（TestEngineer）测试 → 小狄（CTO）审核收口**。
- CTO 职责：审定技术方案（DESIGN.md）、审查代码变更（PR review）、定义质量门禁、最终签核交付。
- FullStackDeveloper 职责：在 CTO 审定的技术方案内执行编码实现，决策权限限于编码方案；架构决策、产品范围或测试判定必须升级至 CTO。
- TestEngineer 职责：在 CTO 定义的工程门禁内执行测试验证，决策权限限于测试用例设计和测试报告格式；质量门禁判定、阻塞性缺陷或发布 readiness 判定必须升级至 CTO。
- 该流水线适用于吸收管道（Phase 0–C 及后续阶段）的代码交付；IPD 管道的交付规则由 IPD case 独立定义。
- 规则维护：CTO（技术交付 owner），变更需 CEO 或 CAO 确认。

## 来源

- `../workflow/cyber-company-secretariat.md`
- `README.md`
- `../../../TriMetaverse/docs/workflow/operating-records/README.md`
- `../../../TriMetaverse/docs/三元宇宙架构与模块说明.md`
- `../../source-agents/registries/CompanyGovernanceRegistry.agent.md`
