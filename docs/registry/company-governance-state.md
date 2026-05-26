# 公司治理状态

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

## 治理说明

- 新增文档、重构文档或吸收上游资料时，先判断该文件是否属于 TriMetaverse / TriCompany 自有资料；自有资料默认中文化。
- 开源吸收链中的 `reference/` 与 `vendor/` 文件默认保持上游原貌；真正进入模块自研文档、registry 或 workflow 后，应转换成中文优先口径。
- Registry 摘要不得只保留英文标题而缺少中文解释，避免新人 agent 和岗位对象误读边界。

## vendor 与 .gitignore 治理规则

- 对存在治理中 `vendor/` 冻结基线的源侧模块，`vendor/` 默认进入模块自己的 `.gitignore`，用于隔离日常本地噪音和主 `CodeGraph` 查询视图。
- 这条规则**不改变** `vendor/` 作为冻结基线、需要被版本控制和审计的事实；已有受治理的 vendor 文件继续受 git 跟踪，后续有意升级 vendor 快照时，由对应 owner 显式纳入提交。
- `vendor/` 默认不进入模块主 `CodeGraph`；只有在开源吸收、差异拆解、adapter 映射或 schema 对照等专项任务下，才临时纳入 vendor 视图。
- `TriCompany-copilot-host-assets/vendor/` 不属于模块真源 `vendor/`；它只允许保留从源侧发布过来的冻结 `reference` 副本或当前宿主验证辅助代码，不得演化成 support 侧独立研发面。

## Git Health 与本地提交治理规则

- `Registry` 负责维护各模块的 `Git Health` 事实：包括 dirty worktree 基线、已知未提交切片、风险说明和升级提示。
- `Registry` **不直接代替 owner 做本地提交**；本地提交责任仍归对应模块 owner 或当前实际开发 owner。
- 活跃模块应在以下任一时点做一次 `Git Health` 收口：形成稳定切片后、切换阶段前、交接 handoff 前，或跨过一个会议周期仍持续 dirty 时。
- 若本地脏改动需要继续保留，必须至少说明：原因、风险、是否已有可提交切片、预计收口时间。
- 跨过一个会议周期仍未收口的本地脏改动，应进入 operating record 的 `blockedItems` 或 `nextActions`，由秘书处和总助催办、由 CTO / owner 收口。

## 开发代码模块标配

- 模块一旦进入真实开发代码阶段，默认必须具备以下标配：
  1. 独立 git 仓。
  2. `README.md`。
  3. `docs/` 文档基线。
  4. 根级 `.gitignore`，至少排除 `.codegraph/`、`.cursor/`、依赖目录、构建产物、环境文件和受治理 `vendor/` 噪音。
  5. 本地 `CodeGraph` 初始化与由对应 `CodeRegistry` 维护的摘要。
- 这里的“进入真实开发代码阶段”是指：模块已经出现现役源码、运行时、构建脚本、测试或持续开发任务；占位 / 待初始化模块在进入该阶段前不强行补齐。
- `CodeGraph` 是本地辅助索引，不替代源码、代码文档、`code-state.md` 或人工收口；允许只把摘要、排除规则、扫描时间和版本锚点写回 registry，不提交 `.codegraph/` 与 `.cursor/` 缓存。
- 若某模块缺失上述标配，应由 CTO 在启动开发当轮或下一轮优先补齐，再继续把它写成现役开发模块。

## 来源

- `../workflow/cyber-company-secretariat.md`
- `README.md`
- `../../.github/source-agents/registries/CompanyGovernanceRegistry.agent.md`
