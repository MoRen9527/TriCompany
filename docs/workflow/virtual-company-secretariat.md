# TriCompany 秘书处机制草案

版本：V0.1
日期：2026-04-16
状态：研发草案

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/virtual-company-secretariat.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: active-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/virtual-company-secretariat.md
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

## 5. 会后回填要求

当前阶段优先回填到：

- docs/execution 下对应阶段文档
- 需要变化的 docs/product 或 docs/engineering 文档
- 需要变化的 docs/registry/product-state.md 或 code-state.md
- 总助认知资产中确有必要长期保留的部分

## 6. 当前边界

- 不把会中讨论直接写成已确认结论
- 不跳过冻结项、升级项和 owner
- 不把研发草案误写成正式公司制度定稿
- 不把当前 Copilot-host live 上岗写成 TriMC 正式宿主切换或完整授权矩阵完成
