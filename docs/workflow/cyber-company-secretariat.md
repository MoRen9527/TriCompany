# TriCompany 秘书处机制草案

版本：V0.1
日期：2026-04-16
状态：研发草案

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/cyber-company-secretariat.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: active-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/cyber-company-secretariat.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-04-28

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

## 5. 会后回填要求

当前阶段优先回填到：

- docs/execution 下对应阶段文档
- 需要变化的 docs/product 或 docs/engineering 文档
- 需要变化的 docs/registry/product-state.md 或 code-state.md
- 总助认知资产中确有必要长期保留的部分

如果活跃模块的本地脏改动跨过一个会议周期仍未收口，应同步进入 operating record 的 `blockedItems` 或 `nextActions`，并标明：

- 模块名
- 当前 owner
- dirty worktree 原因
- 是否已有可提交切片
- 预期本地提交或冻结时间

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
