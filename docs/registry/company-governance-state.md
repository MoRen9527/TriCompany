# 公司治理状态

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/registry/company-governance-state.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-09-03（D-13 条 4 勘误追平：spawn 型现值 FSD/STE，LG-029；2026-09-02 BL 席增设）

## Registry 职责

- 本文件是 `CompanyGovernanceRegistry` 的公司治理事实工作层。
- 本文件记录组织制度、秘书处机制、会议治理、岗位边界、agent 发布纪律和治理文档归属。
- 经营 owner 为 ChiefAdministrativeOfficer（CAO）；CEOChiefOfStaff 只负责路由、协调、催办、升级和中央收口。

## Current Ownership

- 本节是公司级职责域 owner 分工的治理真源；`TriMetaverse/docs/workflow/github-repo-governance.md` §8（Owner 分工）是本节的中央摘要消费方，只做摘要不做替代。
- 当前职责归属矩阵：

| 职责 | Owner |
| --- | --- |
| 模块产品事实与 PRD 归属 | CPO（小乔） |
| 模块代码事实与技术门禁 | CTO（小狄） |
| 公司治理、秘书处与行政制度 | CAO |
| 人力资源、岗位启用与交接 | CHO |
| 公司级任务分派、协调、催办与升级 | CEOChiefOfStaff（小贾） |
| 中央战略与模块边界裁决 | BusinessStrategy |

- 本表只登记公司级职责域的 owner 分工边界；单岗位职责细节以源侧岗位合同与 JD 基线为准，岗位启用与交接治理走 CHO 侧 handoff 流程，不在本表重复维护。
- 矩阵发生变更时，先改本节，再同步 `github-repo-governance.md` §8 摘要；两处不一致时以本节为准。

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

## 动态任务树协议归属

- 动态任务树描述公司岗位、总助持树、执行节点流转、升级和收口，属于 TriCompany 公司维度 workflow。
- 公司级真源固定为 `TriCompany/docs/workflow/dynamic-task-tree-protocol.md`，可被多个项目实例和宿主复用。
- 各项目只维护本项目 operating records、tree directories、数据库 / 导出文件与同名 `published-summary`；不得在项目摘要中独立改写公司核心状态语义。
- TriLC 与 TriMC 应消费同一共享 Trees / ADE runtime 合同；本地域和服务域只保留 adapter 差异，并通过 run authority 防止双活写入。

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
- 分派枢纽（2026-09-01 起，D-15 立法）：开发与测试分派枢纽=CTO——FD 承接开发、ST 承接测试，一律从 CTO 手里派，不接受越手直派；必要功能和模块=CPO+CTO 双席联审门（单席不得自决）。真源：`TriCompany/docs/workflow/engineering-disciplines.md` D-15。

## 来源

- `../workflow/cyber-company-secretariat.md`
- `README.md`
- `../../../TriMetaverse/docs/workflow/operating-records/README.md`
- `../../../TriMetaverse/docs/三元宇宙架构与模块说明.md`
- `../../source-agents/registries/CompanyGovernanceRegistry.agent.md`

## 模块命名权威对照表（quad-migration alias 真源）

- 生效：2026-08-24，CEO 四模块迁移指令（quad-migration-spec v1.0 §三.2 授权本表为唯一真源）
- **命名对齐决议（2026-08-31，CEO 终态裁决·单 B）**：采 **C 档双名并书+物理冻结**——叙事名（TriMMC/TriRMC/TriMLC/TriRLC）=文档与 registry 正名；物理目录（/srv/fleet/TriMC、/srv/fleet/TriRMC）及全部 systemd units **永久冻结不改**（「物理旧名照用」自 quad-migration v1.0 的过渡兼容**升格为终态冻结**，正名权归叙事面）；对旧决策的取代关系与理由（刚稳态的同步链回归风险>改名收益，勘验六面+A/B/C 分档=naming-alignment-survey-20260831.md）入册留痕。B 档项（cron payload/hook 内嵌路径）仅在自然编辑窗顺手对齐，不排停机窗。
- 规则：各文档只许引用本表（标注 as-of 版本），禁自由复述副本；操作命令语境（ssh/bash/systemctl/git）只允许兼容面旧名原样出现；大写连写=叙事名，小写标识符=兼容面旧名

| 叙事名 | 读法·口播 | 一句话角色锚 | 兼容面载体（冻结至物理迁移窗） |
| --- | --- | --- | --- |
| TriMMC | Tri-双M-C | 元虚拟教练系统的服务端（驱动成熟宿主 claude code 的壳） | systemd trimc.service、TRIMC_CONFIG_DIR=/var/lib/trimc、/srv/fleet/TriMC、/srv/git/TriMC.git 及全体 remotes、healthz 8710 |
| TriMLC | Tri-M-L-C（4 音节，勿混 TriModel=Tri-Model 2 音节） | 元虚拟教练系统的本地腿（承载本地研发仓宿主；FADE 灌人+成果落盘） | D:/Code/ai/TriMLC（新仓即新名） |
| TriRMC | Tri-R-M-C | 元现实落地队的服务端（自持生产面，与 TriRLC 共用 agent-core） | D:/Code/ai/TriRMC；未来部署面 trirmc.service/:8712 物理名一次定终身 |
| TriRLC | Tri-R-L-C | 元现实落地队的本地控制器（原 TriLC daemon） | D:/Code/ai/TriLC 目录名、trilc bin/npm 名 |

- 维护 owner：CAO（本表）；变更须 CEO 或 quad-migration-spec 升版联动

## 通信名址与命名宪法（席位正名指针节，2026-09-01）

- 生效：2026-09-01，CEO 裁定（命名宪法全文）；同日 COS→CAO 治理路由移交（今后工程纪律/文档治理/公司治理/项目治理内容归 CAO 写入治理真源）。
- 正名原则=职位代号；别名=中文名/职位全称/英文名，可空缺候补。
- 15 席正名别名全表真源：`TriCompany/docs/workflow/engineering-disciplines.md` D-13（BOD/COS/CPO/CTO/CHO/CAO/COO/CFO/CMO/CSO/FD/ST/RDT/DE/BL）；本节只留原则与指针，禁自由复述副本。
- spawn 面 frontmatter name 不改原则，CEO 方案 v3 对 FSD/STE 两席显式破例随批改（LG-029 勘误）；FD/ST/RDT/DE ↔ spawn 型现值 FSD/STE（SeniorTestEngineer）/RAndDTrainer/DeploymentEngineer，四映射真源随 D-13 条 4。
- 通信纪律配套：发件前 ListAgents 对名址+双向纪律（呈报方核通道/转呈方核结论），随 D-13。
- BL 席（业务组长，daemon 常驻信件督办岗，挂 COS 麾下）2026-09-02 增设：格式 `BL-<项目代号>` 冻结、首任=BL 无后缀（CAO 裁）、扩展评估触发线随 D-13 注记；实际岗位启用走 CHO 侧 handoff 流程。
- 待办注记：各员真源 description 批量补别名关键词=CHO 域同批（LG-024 fast-follow 同窗）。
