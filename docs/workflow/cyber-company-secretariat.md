# TriCompany 秘书处机制草案

版本：V0.1
日期：2026-04-16
状态：研发草案

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/cyber-company-secretariat.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/tricompany-secretariat.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-06-08

## 1. 文档定位

本文用于约束 TriCompany 当前阶段的会议组织、会议开始 / 结束口径、动作项回填与跟进方式。

当前仍属于研发草案，不替代 TriMetaverse 侧的正式制度归属。秘书处和行政管理的正式归属应对齐 CAO 与 `CompanyGovernanceRegistry`；人力资源、岗位启用和交接治理归 CHO 侧，不再与 CAO 混写。

## 2. 当前阶段责任

- CAO 已在当前 Copilot-host live 阶段启用，秘书处日常机制、会议制度、纪要归档和行政治理资料归属由 CAO 主责
- 会议开始、会议结束、纪要收口、动作项跟踪仍由总助进行公司级协调和催办；制度 owner 与归档规则由 CAO 维护
- 涉及岗位 / 职责交接的 checklist 与 completion tracking，按 `TriCompany/docs/workflow/chief-human-resources-officer-handoff-governance.md` 执行，并归 CHO 侧治理；CHO 已在当前 Copilot-host live 阶段启用

## 3. 会议开始口径

开始会议时至少要收口：

- 会议名称
- 会议目的
- 参会角色
- 当前背景
- 核心议题
- 预期产物

信息不足时，只补问关键缺口，不做机械式连环提问。

## 4. 会议结束口径

结束会议时至少要收口：

- 已确认结论
- 冻结项
- 升级项
- 动作项
- 责任人
- 截止时间
- 会后需要回填的文档或 registry
- 活跃模块是否存在需要收口的 `Git Health` / dirty worktree / 本地提交事项
- 若涉及 operating record，必须区分“当前周维护面”与“单条事项状态”；默认沿用 `CompanyGovernanceRegistry` 中定义的 `active` / `frozen` / `stale-review` / `closed`

## 5. 会后回填要求

当前阶段优先回填到：

- docs/execution 下对应阶段文档
- 需要变化的 docs/product 或 docs/engineering 文档
- 需要变化的 docs/registry/product-state.md 或 code-state.md
- 需要变化的 `CompanyGovernanceRegistry` 术语、秘书处规则或 operating record 术语对齐说明
- 总助认知资产中确有必要长期保留的部分

如果活跃模块的本地脏改动跨过一个会议周期仍未收口，应同步进入 operating record 的 `blockedItems` 或 `nextActions`，并标明：

- 模块名
- 当前 owner
- dirty worktree 原因
- 是否已有可提交切片
- 预期本地提交或冻结时间
- 若事项进入 operating record，单条事项状态默认只写 `active` / `frozen` / `stale-review` / `closed`；模块状态默认写“现役模块 / 占位模块 / 待初始化模块 / 待迁移模块 / 待归档兼容仓”，不得混成一套
- 若事项进入 operating record 的未决事项清单，至少写出：**事项 ID / 事项名称 / 事项简介 / 事项状态 / 当前进度**；推荐继续补齐来源、当前动作、下一步、恢复条件或截止时间、Owner

## 5.1 待办复查入口

- 当 CEO、总助或秘书处要求对当前未决事项做一次正式复查时，默认使用：
  - `/待办复查`
  - `/review-backlog`（ASCII 兼容入口）
- 该动作默认复查**当前周维护面**，而不是随意抽查历史周；若用户指定其他 `OPERATING_PLAN`，以用户指定为准。
- “超过 3 天未续推”默认触发**复查**，不是自动冻结；复查后才判断维持 `active`、改为 `stale-review`、改为 `frozen`，或直接 `closed`。
- 若复查结论改变了当前周维护面的事项状态、当前进度、下一步或 owner，默认同步更新最新 active `OPERATING_PLAN` 的 Markdown 与 JSON，除非用户明确要求“只分析，不回填”。

## 6. 文档语言规则

- 公司级、模块级、registry、workflow、产品、技术、执行、培训和经营记录文档默认中文优先。
- 专有名词、模块名、命令、代码符号、schema 字段、API 字段、许可证、上游引用、宿主格式字段和对外英文材料可保留英文。
- `reference/` 与 `vendor/` 中的上游文件默认保留原貌；进入自有文档、registry 或 workflow 后，应转换为中文优先口径。
- 若存在特殊原因需要英文为主，应在文档中说明面向对象或宿主格式原因。

## 7. 当前边界

- 不把会中讨论直接写成已确认结论
- 不跳过冻结项、升级项和 owner
- 不把研发草案误写成正式公司制度定稿
- 不把当前 Copilot-host live 上岗写成 TriMC 正式宿主切换或完整授权矩阵完成
