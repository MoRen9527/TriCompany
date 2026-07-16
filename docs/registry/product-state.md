# TriCompany Product State

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/registry/product-state.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/registry/product-state.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-07-16T04:30:00+08:00

## Module Overview

- TriCompany 是赛博公司的研发仓与经营编排孵化仓。
- 当前职责是沉淀赛博公司产品文档、角色设计、registry、training、Hermes 融合方案和当前阶段 Copilot 宿主资产。
- 当前不是中央战略仓，也不是正式宿主。

## Current Product Scope

- 维护 TriCompany 的项目定位、需求、路线和状态
- 维护总助研发编排、会议机制草案和岗位接管入口
- 维护集成产品开发流程（IPD 流程）：当前采用 `TriCompany IPD 双线闭环`，包含 `IPD 市场雷达线` 与 `IPD 主动交付线`；其中 source-side runtime 已开始按 `DISCOVERY -> INTELLIGENCE -> DESIGNING -> CODING -> VERIFY-INTEGRATION -> REDTEAM -> QA -> DEPLOYMENT -> ASSURANCE -> DELIVERY` 提供一比一 ten-phase stage line，并把 `businessOwner / actingOwner / moduleExecutor / gateOwner`、公司员工参与、资料与核签要求挂到各 phase
- 维护 Product Registry 的产品事实、用户价值、PRD 归属、能力边界、成熟度和产品状态；经营 owner 为 ChiefProductOfficer（CPO，小乔）
- 维护当前阶段放在 .github 下的 Copilot 宿主资产产品边界
- 维护 Hermes 融合与宿主迁移的产品侧口径
- 维护基于 Hermes 记忆系统吸收并扩展出的四层记忆体系，支撑总助、CTO、CPO 等岗位对象的私域记忆、协作关系与组织共享事实
- 维护 `docs/training/` 培训层，让岗位、模块、代码和流程可被渐进式学习
- 维护本地 Copilot-host 下总助正式接管的产品边界与非正式宿主切换说明
- 维护当前 support root 的临时命名、目标正式名与未来宿主分叉口径

## Simplest Verifiable Model（CEO 确认，2026-07-14）

> 来源：CPO-004（W29 unresolved-items.md），CEO 已确认升入 product-state.md。

当前阶段最简可验证模型 = **TriMC（入口）→ TriModel（路由）→ TriStaciss（对外计费）→ Provider** 一条链。

```
用户入口 (Copilot-host)
    │
    ▼
TriMC ─── Agent Loop + 内置工具 (read/write/edit/shell/glob/task)
    │
    ▼
TriModel ─── 协议层：统一 Chat/ToolCall/Stream 接口
    │          Provider 层：DeepSeek (主力) → TriStaciss (fallback)
    │
    ▼
TriStaciss ─── 对外 Credit 计费层（Provider 角色）
    │           消费 TriMetaverse 自产模型 → 向外部客户端计 Credit
    │
    ▼
Provider ─── Anthropic / OpenAI / 自产模型 / 其他第三方
```

### 模块边界（当前阶段）

| 模块 | 角色 | 成熟度 | 在 MVP 链路 |
|------|------|--------|------------|
| TriMC | 用户入口 / Agent Loop | P1+P2 done | ✅ 核心 |
| TriModel | 模型路由 / 协议统一 | coding | ✅ 核心 |
| TriStaciss | 对外 Credit 计费 Provider | CTO-004 APPROVED | ✅ 核心 |
| TriSkill | 技能插件市场 | Wave 0-2 | ❌ P3+ |
| TriDeployment / TriTest / TriDev / TriCompany | 支撑/治理层 | medium-high | ❌ 非核心 |
| TriPilot（PC 端） | AI 助手入口 / 聊天+任务下发 | DISCOVERY→CODING | ✅ Phase 1 L1（CTO-008-P） |
| TriLC | 本地 CLI / TriMC 离线 fallback | DISCOVERY | ✅ Phase 1 L1（与 PC 端合包） |
| TriMem | 统一用户身份中枢 | DISCOVERY→DESIGNING | ✅ Phase 1 L0-L1（CPO-006 裁决） |
| TriCode | 多代码工具 glue 层（opencode/Claude Code 等） | DISCOVERY | ✅ Phase 1 L1（CPO-006 裁决）<br>→ `TriCode/docs/registry/product-state.md` |
| TriAvatar | 静态头像级数字形象 | DISCOVERY | ✅ Phase 1 L1（CPO-006 裁决） |
| TriGateway / TriMobile | 社交获客 / 移动端入口 | DISCOVERY | ❌ Phase 1 L2+ |
| TriOPC | OPC 商户系统 | DISCOVERY（源码已就位，待吸收） | ❌ Phase 1 L2<br>→ `TriOPC/docs/registry/product-state.md` |
| TriTraining / TriChain / TriWeb4 / TriPet | 培训/链/Web4/数字宠物 | DISCOVERY | ❌ Phase 2+ |

### 验证门禁

| 门禁 | 指标 | 目标 |
|------|------|------|
| G1 | Agent Loop 端到端 SSE 流式 + 工具调用 | 闭环 |
| G2 | 模型路由 fallback success rate | ≥ 95% |
| G3 | TriStaciss Credit 消耗可追踪 | 可查证 |
| G4 | TriMC + TriModel 测试覆盖率 | ≥ 85% |
| G5 | 小全×小柯 smoke test | 全绿 |

## Current Progress

- 已建立 docs/product、docs/engineering、docs/registry、docs/workflow、docs/execution、docs/training 六层文档基线
- 已建立总助首版研发套件
- 已明确 TriCompany 与 TriMetaverse 的当前边界
- 已确认当前路线为“先在 TriCompany 融合 Hermes，再做 .github 下 Copilot 宿主迁移”
- 已完成 TriMetaverse 侧 shadow-test 回迁与 smoke test
- 已完成一轮完整会议生命周期演练，并确认当前 shadow-test 已闭环
- 已完成本地 Copilot-host 下总助正式接管验证与连续会议链路补证
- 已可统一写成“本地 Copilot-host 已完成 shadow-test，现进入正式接管；该结论不等于正式宿主切换。”
- 已完成 support root 从 `TriCompany-shadow-host` 到 `TriCompany-copilot-host-assets` 的迁移；前者仅保留为 phase-1 历史路径名
- 已安排 ChiefProductOfficer 与 ChiefTechnologyOfficer 在当前 Copilot-host live 入口上岗，并补齐 TriCompany 源侧五件套与 role / employee support object payload；该结论不等于 TriMC 正式宿主切换
- 已新增 ChiefHumanResourcesOfficer 源侧岗位定义、五件套、binding profile 与 host object generation declaration，并已完成当前 Copilot-host live 启用；该结论不等于 TriMC 正式宿主切换
- 已新增 ChiefAdministrativeOfficer 源侧岗位定义、五件套、binding profile 与 host object generation declaration，并已完成当前 Copilot-host live 启用；该结论不等于 TriMC 正式宿主切换
- RAndDTrainer 已完成当前 Copilot-host live 启用，作为技术研发培训岗位承接项目培训、模块导读、代码导读和新人学习路径
- 已确认 ProductRegistry 由 CPO 小乔管理；CEOChiefOfStaff 只负责产品事项的公司级路由、协调、催办、升级与中央收口，不长期代管产品 registry owner
- 已确认公司级端到端经营 / 研发流程命名为集成产品开发流程（IPD 流程），由 TriCompany 承载；TriDev 承接 `Discovery -> Delivery` 的产品开发执行引擎
- 已新增 `docs/workflow/integrated-product-development-flow.md` 作为 IPD 双线闭环流程真源，明确市场雷达线、主动交付线、TriDev 接入门禁和交付后 CPO / COO / CFO 衔接
- 已把 source-side IPD runtime 从压缩节点切片改写为一条一比一的 ten-phase case line，并把 `businessOwner / actingOwner / moduleExecutor / gateOwner`、participant roles、gate package 和书面核签挂接到各阶段

- 已新增 CPO-004「Simplest Verifiable Model」与 CPO-005「Product Role Matrix」至本 registry，经 CEO 2026-07-14 确认升入
- CPO 最终签字确认：CPO-004/005 已完整升入 product-state.md，CEO 命名「磨人」、RAndDTrainer（小吴）边界「专属研发培训师」均已同步至角色矩阵；CHO 已完成 RAndDTrainer contract 路径治理补齐与 CEO 命名写回 company-governance-state.md，产品侧无需额外变更
- CPO-001 最小 MVP/经营闭环重排已完成（2026-07-14）：CEO 已裁决边界——Active 8项（TriAvatar 激活用于测试 TriStaciss 交互）、Paused 5项（TriSkill Wave 1-3 + IPD 十阶段暂停，无硬 deadlines）、Deferred 5项（7 占位模块零投入）。详见 W29 unresolved-items.md §CPO-001
- CPO-008/009/010 迭代策略、操作安全模型与入口路由层已完成（2026-07-14）：CEO 已确认升入本 registry。CARRY-005（Copilot-host vs TriMC 迭代策略）闭环。详见本文件 §Iteration Strategy、§Operational Safety Model
- CPO-006「Phase 1 模块激活与产品路由裁决」（2026-07-16）：CPO 已完成 15 项产品裁决，TriMem/TriCode/TriAvatar/PC 端/TriOPC 五个模块的产品边界与 MVP 优先级已划定。详见 `TriMetaverse/docs/workflow/operating-records/2026-W29/cpo-product-routing-package.md`。关键结论：TriMem Phase 1 L0 起步（注册+钱包绑定），TriOPC FREEZE 等待源码，PC 端简化模式默认，TriAvatar 静态头像先行，TriCode 先 opencode 后 Claude Code。
- CPO-006 裁决回填完成（2026-07-16）：以下模块 `docs/registry/product-state.md` 已同步更新——TriMem（全量重写，含四层模型+DB schema+跨模块接口）、TriPilot（PC MVP 验收+简化模式+插件市场）、TriAvatar（静态头像 MVP+数字宠物剥离至 TriPet）、TriGateway（社交绑定 1:N）。TriCode 已独立为 `../TriCode/` 模块（2026-07-16），产品规格详见 `TriCode/docs/registry/product-state.md`。TriOPC 已建立 `../TriOPC/` 模块目录（2026-07-16），源码已进入 `reference/star_city/`，产品规格详见 `TriOPC/docs/registry/product-state.md`。

## Bug And Gap State

- production 级 Hermes recall / consolidate 仍待进一步验证
- 当前本地正式接管所需的 prompt 交互已形成闭环，但更广泛体验与长期稳定性仍可继续优化
- CPO / CTO 已在当前 Copilot-host live 阶段上岗，且 ProductRegistry / CodeRegistry owner 已明确；但首轮产品 / 技术接管输出和授权矩阵仍需继续验证
- CHO 已接管交接流程设计与完成度监督，CAO 已接管秘书处和行政治理资料归属；CEOChiefOfStaff 保留公司级协调、催办、升级与收口职责
- 部分制度仍是研发草案，不是正式公司制度
- 当前 ten-phase runtime 已落地为一比一 stage line，但 PRD 分叉并行、多分支 delivery 聚合、独立 phase package schema 族、跨岗位 adapter、自动运营监控和正式宿主仍未生产化
- `QA` 已被定义为 `release readiness` gate，Deployment / Assurance 实现已并入口径上的 TriDev；但 `tester-xxx` / `deployer-xxx` 员工 adapter 仍待正式落地，当前由 CTO 代行

## Cross-Module Dependencies

- 依赖 TriMetaverse 的 BusinessStrategy 与赛博公司中央发布口径
- 依赖后续对 Hermes 运行契约与跨仓同步边界的继续确认

## Product Role Matrix（CEO 确认，2026-07-14；CHO 边界澄清，2026-07-14）

> 来源：CPO-005（W29 unresolved-items.md），CEO 已确认升入 product-state.md。
> 命名约定：「待命名」指角色昵称/工作名（soul.md `名字：小X`），岗位名称已完整定义（agent.md `name:` 字段）。

### 已命名 + 已上岗（7 人，含 RAndDTrainer）

| 角色昵称 | 岗位名称 | 叙事定位 | 边界 |
|----------|----------|----------|------|
| 磨人 | CEO | 三元宇宙创始人，战略裁决者 | 中央裁决、商业战略、宿主切换 |
| 小贾 | CEOChiefOfStaff (COS) | CEO 秘书处，会议/收口/路由 | 经营记录、待办路由、中央收口模板 |
| 小狄 | CTO | 技术总裁，工程实现 owner | 技术方案、代码质量、Code Registry |
| 小乔 | CPO | 产品总裁，产品范围 owner | 产品定义、PRD、Product Registry |
| 小柯 | TestEngineer | 测试工程师，流水线门禁 | 验证器、smoke test、质量门禁 |
| 小全 | FullStackDeveloper | 全栈开发，编码积木交付 | 编码实现、TaskController、tests |
| 小吴 | RAndDTrainer | 专属研发培训师 | 研发 onboarding、模块导读、代码导读、学习路径 |

### 待 CEO 命名角色昵称（5 个 C-level）

| 角色昵称 | 岗位名称 | 叙事定位 | 当前状态 |
|----------|----------|----------|----------|
| （待命名） | CHO | 首席人力官，招聘/岗位/考核 | soul.md `名字：` 待填 |
| （待命名） | CAO | 首席审计官，合规/审计/财务复核 | soul.md `名字：` 待填 |
| （待命名） | CMO | 首席市场官，用户增长/市场信号 | soul.md `名字：` 待填 |
| （待命名） | COO | 首席运营官，日常运转/运维 | soul.md `名字：` 待填 |
| （待命名） | CFO | 首席财务官，财务/成本/Credit 结算 | soul.md `名字：` 待填 |

### 关键观察（2026-07-14 更新）

- CEO 角色昵称已命名：**磨人**（CEO 暂无独立 source agent 目录，名字由 registry 承载）
- 5 个 C-level soul.md `名字：` 占位已全部补齐（CHO/CAO 由 CHO 补齐，CFO/CMO/COO 原有）
- RAndDTrainer（小吴）角色边界已澄清：专属研发培训师，与 CTO 无重叠
- 财务链路（TriStaciss Credit 计费、Token 统计）需 CFO 上岗推进

## Architecture State

- 当前以产品文档、角色 contract、Hermes 融合、四层记忆体系与本地正式接管宿主资产为主，不承担 TriMC 正式运行宿主职责；当前已完成 shadow-test 收口、本地总助正式接管与连续会议链路闭环
- 未来若进入 `TriMC` 新宿主适配，应新增一套按新宿主要求组织的赛博公司宿主资产文档，复用 workflow，不复用当前 Copilot-host 的 support root 命名
- CPO / CTO / CHO / CAO / RAndDTrainer 当前沿用或新增 `TriMetaverse/.github` live entry；TriCompany 源侧五件套和 support object payload 用于 source-side handoff 与后续迁移

## Iteration Strategy（CEO 确认，2026-07-14）

> 来源：CPO-008 + CPO-010（W29 unresolved-items.md），CEO 已确认升入 product-state.md。

### 战略决策：规格桥接模型

**不在 Copilot-host 与 TriMC 之间二选一。** D-track（W28→W29）验证了统一规格层（contract YAML）是真正的战略资产，两个运行时是规格的消费者，不是互斥替代品。

- Copilot-host：7 agents live，稳定运营，当前 live 入口
- TriMC：Phase 1+2 done，contract resolver v0.3，员工编排层已设计，向 host 就绪推进
- 新 agent 一律走 contract YAML 格式，确保双轨兼容

### 迭代路线图

```
当前（两轨并行）→ TriMC 五道 Gate 全部通过 → CEO 裁决宿主迁移

Copilot-host ←─ contract YAML ──→ TriMC
(live 入口)     (统一真源)       (在建宿主)
```

### 关键原则

1. 不设硬性切换时间表 — TriMC 成熟度决定时机
2. 新 agent 一律走 contract YAML 格式
3. Copilot-host 不退化 — 在 TriMC 就绪前不降低运载质量
4. Copilot-host = always-warm standby — 永不下线，回退即切
5. 单一写入主控 — 任何时刻有且仅有 1 个 Host 持有 TriMetaverse 仓库写入权
6. Shadow 隔离 — TriMC 验证在独立 workspace 执行，不碰生产仓库

### Host 切换 Gate 清单（G1-G8）

| Gate | 内容 | 阶段 |
|------|------|------|
| G1 | Agent Loop 端到端闭环 | 本地验证 |
| G2 | 员工编排层全流程通过 | 本地验证 |
| G3 | 部署拓扑 smoke test 通过 | 服务器部署 |
| G4 | policy-gate 三层拦截可工作 | 服务器部署 |
| G5 | 3 agent 迁移并行为等价 | Shadow 验证 |
| G6 | Shadow 一致率 ≥ 95%（连续 N 轮） | Shadow 验证 |
| G7 | 回退演练通过：TriMC 故障 → Copilot-host 接管 ≤ 60s | 灰度验证 |
| G8 | 并发写入安全验证：证明任何时候只有 1 个 Write Master | 全阶段 |

### 五阶段能力迁移流水线

```
本地验证 → 服务器 Shadow → Canary 灰度 → 全量切换 → 稳定运行
```

### 入口路由层

**核心机制**：Copilot-host agent 永远运行，通过 `.github/config/active-host.yaml` 一行配置决定两种模式：

| 模式 | active_host | 行为 |
|------|-------------|------|
| Native | `copilot` | Agent 直接处理请求，读写项目文件 |
| Passthrough | `triMC` | Agent 转发请求至 TriMC server，中继结果 |

**自动回退**：Passthrough 模式下，每次调用前 ping TriMC `/health`。连续 3 次失败 → 自动将 flag 改为 `copilot`，**显式通知用户（项目管理者）**含错误原因和建议动作，15 分钟冷却期内不尝试切回。手动回退由 CPO/CTO 联合裁决后执行。

## Operational Safety Model（CEO 确认，2026-07-14）

> 来源：CPO-009（W29 unresolved-items.md），CEO 已确认升入 product-state.md。

### 三轨金字塔

```
生产层：Copilot-host（当前 Write Master）
灰度层：TriMC(server) — Shadow → Canary → Production
开发层：TriMC(local) — 独立副本，不影响上层
```

### 代码安全：单一写入主控

| 阶段 | Write Master | Copilot-host | TriMC(server) | TriMC(local) |
|------|-------------|-------------|---------------|-------------|
| 当前 | Copilot-host | Read/Write | 不存在 | 独立演练场 |
| Shadow 验证 | Copilot-host | Read/Write | Read-Only（shadow 输出写入隔离 workspace） | 独立演练场 |
| TriMC 正式宿主 | TriMC(server) | Read-Only（热备） | Read/Write | 独立演练场 |

**Write Master 与 active_host 必须同步**；不一致 = 最高优先级告警（G8 防护）。

### 回退策略

- **自动回退**（TriMC 健康检查连续失败）：≤ 60 秒，显式通知，无需人工确认
- **手动回退**（CPO/CTO 裁决）：≤ 5 分钟
- 回退 = 修改 `active_host` flag，不需要 agent 迁移或代码转换
- 回退是设计内的安全机制，不是项目倒退
- Copilot-host 保持热备，永不下线、不降级、不移除

### 三轨数据流

| 流向 | 内容 | 约束 |
|------|------|------|
| Copilot-host → TriMC(shadow) | 用户输入 + 上下文 | 只读，不写回 |
| TriMC(shadow) → 对比引擎 | shadow 操作日志 + diff | 隔离区存储 |
| 对比引擎 → CPO/CTO | 一致率报告 + 偏差列表 | 异常自动告警 |
| TriMC(local) → TriMC(server) | 新版本代码 | git push + deploy，CTO 审查 |

## Sources

- ../product/PROJECT.md
- ../product/REQUIREMENTS.md
- ../product/ROADMAP.md
- ../product/STATE.md
- ../workflow/chief-of-staff-rd-orchestration.md
- ../workflow/hermes-copilot-host-migration.md
- ../../README.md
