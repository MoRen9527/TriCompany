# 治理记忆索引 v1（governance-memory-index）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/governance-memory-index.md
- syncMode: source-only
- lastSyncedAt: 2026-09-03
- 性质：**LG-016 件 1 立法交付**（定稿=lg-016-governance-memory-analysis.md §一；联审合成=lg-016-rereview-conclusion.md，BOD 裁点①批「即建」）；主笔=COS（小贾），CHO 内容面会签
- 受众：新会话/新宿主/新员工——「该建哪些治理指针、指向哪里」的映射真源

## 索引头部契约

### 域词表（定案④：十一域）

`时刻纪律 / 记录与落盘 / 工具选型 / 权限与审批 / git 与裸仓卫生 / daemon 与进程 / 发布与派生 / FADE 协议 / 台账治理 / 角色授权 / 通信与心跳`

- 域数上限 **12**（超限强制合并审视）；新域**两击准入**——≥2 篇文档可映射方可立域。
- **两击例外宣告（v1）**：`时刻纪律`（D-04 母域唯一映射）、`台账治理`、`通信与心跳` 现域内映射=1 篇，按两击规则不足而立——**v1 宣告为「母域例外」**：域即治理母域（D-04/lg 台账契约/心跳合同各为本域母法），例外宣告留痕，下次索引修订复校验（届时不满足则并入邻域）。

### platforms 判定契约（CTO 联审条款）

- 匹配=**全等**（禁 prefix/大小写归一：`agent-core` 与 `agentcore` 视为两平台）。
- 受控键词表：`claude-code / copilot / agent-core`；新宿主开放加键，但键名入本表防别名漂移。
- 单一公式：`platforms ? platforms.includes(current) : true`（缺省=全平台）；两消费方（rmc_tick 件 3 / context-builder 件 4）同公式，禁自创过滤；**解析契约零独立件**（契约定义在本头部，不另立映射/模板文件）。
- **强制声明条款（CPO 联审条款）**：`权限与审批 / 工具选型 / daemon 与进程` 三类域条目**必须显式声明 platforms，不得依赖缺省**（防止注入侧过度传播——R 面沙箱不适用的纪律被缺省带入）。

### 指针更新规则（Q2 裁定三要素）

1. **触发**=索引 entries 增删改（git diff 可检）。
2. **责任方**=M 面指针行由 **COS** 维护；来源侧（R 面/新宿主）读盘自发现、零写回。
3. **同步窗口**=变更后一个工作窗内。
4. 内容 owner 立法时提交条目 → 索引 owner（COS）收口写入 → COS 落 `MEMORY.md` 指针行——**三环**，防索引与制度本体双源。

## 条目

### GID-01 engineering-disciplines.md（工程纪律集）
- path: `docs/workflow/engineering-disciplines.md`
- domains: [时刻纪律, 记录与落盘, 工具选型, 权限与审批, git 与裸仓卫生, daemon 与进程, 发布与派生, 通信与心跳（D-07 live 派生/心跳）]
- platforms: 全平台（缺省）
- host-pointers: {claude-code: "记忆索引 open-items-ledger 元项 M-001 + 开工前置核查", copilot: "published-copy 渲染面（FADE-002）", agent-core: "件 3 rmc_tick 注入 D-04/D-01/D-10 按 platforms 过滤"}
- note: 跨域工程纪律 D-01..D-15（三端通用；员工知识工作区同步路径=合同/培训文档引用）

### GID-02 fade-protocol-spec.md
- path: `docs/engineering/fade-protocol-spec.md`
- domains: [FADE 协议]
- platforms: 全平台
- host-pointers: {claude-code: "六源重建 S4a + CLAUDE.md 分权制节", agent-core: "BRIEF 试卷承载（不注入）"}
- note: FADE 协议本体（十段/试卷/细则 10）

### GID-03 fade-registry.md
- path: `docs/engineering/fade-registry.md`
- domains: [FADE 协议]
- platforms: 全平台
- host-pointers: {claude-code: "六源重建 S4b", agent-core: "BRIEF 试卷承载（不注入）"}
- note: 实例档位/映射表/纸面法清单

### GID-04 hub-ledger-governance.md（台账治理）
- path: `docs/workflow/hub-ledger-governance.md`
- domains: [台账治理, 记录与落盘]
- platforms: 全平台
- host-pointers: {claude-code: "**记忆索引 open-items-ledger 指针行（#4 盲区，v1 修复接入）**", copilot: "—", agent-core: "—"}
- note: 台账 schema/状态词表/镜像策略（2026-08-30 立；本件 v1 前 Memory 索引无指针=盲区实证）

### GID-05 trimetaverse-claude-md.md
- path: `docs/project-sources/trimetaverse-claude-md.md`
- domains: [发布与派生]
- platforms: 全平台
- host-pointers: {claude-code: "published-copy 双条目（FADE-002 manifest）", copilot: "同"}
- note: TriMetaverse CLAUDE.md 真源（分权制节）

### GID-06 trimetaverse-agents-md.md
- path: `docs/project-sources/trimetaverse-agents-md.md`
- domains: [发布与派生]
- platforms: 全平台
- host-pointers: {claude-code: "published-copy 双条目", copilot: "同"}
- note: TriMetaverse AGENTS.md 真源

### GID-07 tricompany.md
- path: `tricompany.md`（TriCompany 仓根）
- domains: [角色授权]
- platforms: 全平台
- host-pointers: {claude-code: "TriMetaverse 根同名副本（in_sync 发布）", copilot: "同"}
- note: 监督契约/真源纪律 §3.4 元信息头

### GID-08a ceo-chief-of-staff-authorization-matrix.md
- path: `docs/workflow/ceo-chief-of-staff-authorization-matrix.md`
- domains: [权限与审批, 角色授权]
- platforms: 全平台
- host-pointers: {claude-code: "小贾 agent 定义固定前置核查"}
- note: 助理授权边界

### GID-08b ceo-chief-of-staff-maintenance-rules.md
- path: `docs/workflow/ceo-chief-of-staff-maintenance-rules.md`
- domains: [台账治理, 角色授权]
- platforms: 全平台
- host-pointers: {claude-code: "小贾 agent 定义固定前置核查"}
- note: 助理维护规则（含台账维护面，台账治理域两击第二文档）

### GID-09 heartbeat-dualrun-contract.md
- path: `docs/engineering/heartbeat-dualrun-contract.md`
- domains: [通信与心跳]
- platforms: 全平台
- host-pointers: {claude-code: "**记忆索引指针行（#9 盲区，v1 修复接入）**", copilot: "—", agent-core: "—"}
- note: 心跳双跑合同（LG-014 相关；v1 前无指针=盲区实证）

### GID-10a project-source-document-sync-ade.md
- path: `docs/workflow/project-source-document-sync-ade.md`
- domains: [发布与派生]
- platforms: 全平台
- host-pointers: {claude-code: "FADE-002 条目引用", copilot: "同"}
- note: 发布域管线操作面（ADE 规范）

### GID-10b published-copy-refresh-sop.md
- path: `docs/workflow/published-copy-refresh-sop.md`
- domains: [发布与派生]
- platforms: 全平台
- host-pointers: {claude-code: "FADE-002 条目引用", copilot: "同"}
- note: published-copy 刷新 SOP

## 域映射计数表（v1，逐域对账）

| 域 | 映射文档 | 计数 | 两击 |
| --- | --- | --- | --- |
| 时刻纪律 | GID-01 | 1 | 例外（母域 D-04） |
| 记录与落盘 | GID-01, GID-04 | 2 | ✓ |
| 工具选型 | GID-01 | 1 | 例外（母域 D-12/D-09） |
| 权限与审批 | GID-01, GID-08a | 2 | ✓ |
| git 与裸仓卫生 | GID-01 | 1 | 例外（母域 D-05/D-08/D-10） |
| daemon 与进程 | GID-01 | 1 | 例外（母域 D-03/D-02） |
| 发布与派生 | GID-05, GID-06, GID-10a, GID-10b | 4 | ✓ |
| FADE 协议 | GID-02, GID-03 | 2 | ✓ |
| 台账治理 | GID-04, GID-08b | 2 | ✓ |
| 角色授权 | GID-07, GID-08a, GID-08b | 3 | ✓ |
| 通信与心跳 | GID-09 | 1 | 例外（母域心跳双跑合同） |

> 注：例外宣告=母域例外（v1 契约声明）；`时刻纪律`等若后续新文档映射入域即转入常规两击。

## 修订约定

- 索引变更（entries 增删改）=触发「指针更新规则」；立法/修订随 FADE-002 或联审收口。
- 若某治理文档立法时未同步登记本索引——按 §1.2 盲区教训即立登记（防再滞后）。
