# TriCompany 需求说明

版本：V0.1
日期：2026-04-16
状态：初版

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/product/REQUIREMENTS.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/product/REQUIREMENTS.md
- supportSyncRule: source 稳定语义变更后，on-demand published-copy 在宿主需要读取时追平
- lastSyncedAt: 2026-06-04

## 1. 背景

TriMetaverse 已经在中央仓形成了赛博公司设计、总助体系和多岗位角色边界，但这些内容仍主要停留在中央真源与宿主试运行层。TriCompany 的建立，是为了给“赛博公司的研发”提供一个独立仓位，把内容、设计、编排和上岗准备先研发清楚，再回到宿主侧做验证。

## 2. 核心需求

### 2.1 仓库基线需求

- 必须是单独 git、单独提交的项目仓。
- 必须建立 docs/product、docs/engineering、docs/registry、docs/workflow、docs/execution、docs/training 六层基线。
- 必须建立 .github 下的当前阶段 Copilot 宿主资产层。
- 必须建立 TriCompanyProductRegistry 与 TriCompanyCodeRegistry。

### 2.2 赛博公司内容需求

- 必须定义 TriCompany 的项目定位、范围、边界和依赖。
- 必须沉淀赛博公司研发阶段的产品目标、阶段路线和当前状态。
- 必须明确哪些内容已经落地，哪些仍待当前阶段验证或中央确认。

### 2.3 技术设计需求

- 必须给出 TriCompany 首版技术设计。
- 必须明确 TriCompany 是研发仓，同时承载当前阶段 Copilot 试运行宿主资产，但不是正式宿主。
- 必须定义总助 agent 的身份层、认知资产层、registry 层、会议编排层、Copilot 宿主层与 Hermes 融合层之间的关系。
- 必须把 Hermes 研究结论体现在设计里：soul 属于身份层，不应和普通记忆混为一层。

### 2.4 总助 agent 需求

- 必须创建首版总助 agent。
- 必须配套 soul、memory、colleagues、social 资产。
- 必须让当前阶段 Copilot 宿主资产落在 TriCompany/.github 下。
- 必须避免让总助本体在对话中显式暴露底层文件路径和“我正在写记忆文件”这一类表述。
- 必须建立会议开始 / 结束的专用 prompt。
- 必须建立维护规则，明确 agent、soul、memory、colleagues、social、prompt 各自负责什么。

### 2.5 编排需求

- 必须定义 TriCompany 当前阶段的总助研发编排。
- 必须定义总助如何路由到 product registry、code registry 和当前已上岗的 CPO / CTO。
- 必须定义 Hermes 融合与 Copilot 宿主迁移的当前阶段执行口径。
- 若后续需要跨仓同步，再定义同步回 TriMetaverse 的口径。

## 3. 非功能要求

- 中文优先，可直接被 CEO 和后续岗位阅读与修改。
- 严格区分草案、待确认、已验证、已落地。
- 不编造上岗状态、正式集成状态和正式运行状态。
- 结构应便于在 TriCompany/.github 试运行，并在需要时再跨仓同步。

## 4. 验收口径

- TriCompany 仓库中存在可读的项目说明、需求、产品路线和产品状态。
- TriCompany 仓库中存在可读的设计、技术路线和技术状态。
- TriCompany 仓库中存在 product/code registry agent 及其 state 文档。
- TriCompany 仓库中存在首版总助 agent 套件与会议 prompt。
- TriCompany 仓库中存在当前阶段 Copilot 宿主资产与 Hermes 融合说明。
- 已写清 TriCompany 与 TriMetaverse 的宿主边界与同步关系。

## 5. 待确认问题

- TriCompany 是否会升级为中央正式模块。
- Hermes 最终采用什么样的 recall / consolidate 运行契约。
- CPO / CTO 上岗后的正式授权矩阵、运行节奏和首轮接管输出如何定义。
- TriCompany 后续是否需要拆出更多岗位 agent。
