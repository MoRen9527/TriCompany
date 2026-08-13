# Agent Contract Schema v3.0 收敛规格

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/agent-contract-v3-spec.md
- syncMode: source-only
- lastSyncedAt: 2026-08-13T21:00:00+08:00
- 作者: CTO 小狄（r13-contract-convergence / r13-1）
- 关联: `trilc-trimc-runtime-parity.md` §6.2、`docs/registry/code-state.md`（CodeRegistry 登记）、r13 树（M3-R1 O2-A）

## 一、背景与目标

合同体系当前两代并存、互不互通，另有 agent-core 死 schema 残留：

| 代际 | 位置 | 数量 | 形状 | 消费方 |
| --- | --- | --- | --- | --- |
| v2 | `source-agents/*.contract.yaml` | 14 份 | contract{agent_id,family}+paths+decision_rights+runtime_baseline(对象) | TriLC `src/config/contract-resolver.ts` |
| v1 | `docs/registry/*.contract.yaml` | 11 份 | contract+identity+responsibilities+decision_rights+collaborators+tools+io_contract+instructions | TriMC `src/contracts/resolver.ts` |
| 死形状 | `packages/agent-core/src/contracts/` | 15 文件（3 .ts + 12 dist） | metadata/capabilities/instances/rules | 零消费方（O2-B 已 @deprecated） |

- 员工覆盖差 3 份：business-strategy、customer-success-officer、deployment-engineer 无 v1 合同（TriMC 编排层对这 3 员工缺合同输入）。
- 两代关键字段互缺：v2 无 identity/io_contract（TriMC 必需），v1 无 paths（TriLC 必需）。
- M3 生产双跑要求任何一侧加载对方域合同都不挂——本规格定义单一权威 schema v3.0 并给出迁移序列。

**目标**：source-agents 为唯一合同真源；全部合同收敛为 v3.0；agent-core 承载唯一 zod schema + 解析入口；双域 resolver 迁 thin adapter；v1 11 份退役（内容并入对应 3.0 合同）。

## 二、Schema v3.0 定义

### 2.1 版本与兼容策略

- `contract.version` 固定 `"3.0"`（literal），`contract.type` 固定 `"agent-contract"`（literal）。
- **无向后兼容分支**：1.0/2.0 形状输入解析必须失败（负路径可测），错误信息指向迁移指引。理由：兼容分支会保留双重真源语义，破坏"真源唯一"。
- 迁移完成即切换：双域 adapter 与合同文件在同树内完成迁移，切换以 commit 序列原子推进。

### 2.2 完整形状（示例）

```yaml
# Agent Contract v3
contract:
  version: "3.0"
  type: agent-contract
  agent_id: "chief-technology-officer"
  family: "Role"          # Role | Registry（v2 位置为准）
identity:                 # ← 从 v1 并入（TriMC 编排所需）
  display_name: "小狄"
  role: "ChiefTechnologyOfficer"
  description: "CTO，负责..."
  user_invocable: true
paths:                    # ← v2 保留（TriLC 五件套）
  soul: "chief-technology-officer/soul.agent.md"
  agent_body: "chief-technology-officer/agent-body.agent.md"
  agent_frontmatter: "chief-technology-officer/agent-frontmatter.agent.md"
  memory: "chief-technology-officer/memory.agent.md"
  colleagues: "chief-technology-officer/colleagues.agent.md"
  social: "chief-technology-officer/social.agent.md"
responsibilities:         # ← 从 v1 并入（union 形状保留）
  - description: "把 MVP 范围翻译成交付路径"
    priority: "high"
decision_rights:          # v2/v1 合并：四键统一
  approve: []
  freeze: []
  escalate: []
  forbidden: []
collaborators:            # ← 从 v1 并入
  reports_to: "CEO"
  peers: ["CEOChiefOfStaff"]
  supervises: []
tools:                    # ← 从 v1 并入
  - name: "read"
    scope: ["docs/"]
    risk_level: "low"     # low | medium | high | critical
    requires_approval: false
    runtime_equivalent: "openclaw:fs:read"
io_contract:              # ← 从 v1 并入（TriMC 编排 I/O 契约）
  inputs:
    - type: "user_message"
      description: "CEO 或 CPO 技术询问/任务"
      source: ""          # 可选
  outputs:
    - type: "tech_judgment"
      description: "技术判断"
      source: ""          # 可选
instructions: |           # ← 从 v1 保留（可选）
  当前角色定位...
runtime_baseline:         # ← v2 保留（对象形状，见 2.4 裁决）
  host: copilot-host
  tri_mc_status: planned
  tri_mc_migration_ready: false
```

### 2.3 zod 规则（agent-core 实现）

- 顶层 `.strict()`：未知字段报错（③ strict 形状一致验收项）。
- 必填：`contract.*`（version/type 为 literal）、`identity.display_name/role/description`、`paths` 六文件路径（非空字符串）、`responsibilities` 非空数组、`collaborators.reports_to`、`io_contract.inputs/outputs` 各非空数组。
- 默认值（解析时填充）：`identity.user_invocable=true`、`decision_rights` 四键空数组、`collaborators.peers/supervises` 空数组、`tools=[]`、`tools[].scope=[]`、`tools[].requires_approval=false`、`tools[].runtime_equivalent=''`、`runtime_baseline` 缺省 undefined。
- 枚举：`family: Role|Registry`、`priority: high|medium|low`、`risk_level: low|medium|high|critical`。
- 负路径错误信息格式：`contract v3 parse failed at <path>: <message>`（含 agent_id 上下文），1.0/2.0 输入报"unsupported contract version X.Y，expected 3.0 — 迁移指引见 docs/engineering/agent-contract-v3-spec.md"。

### 2.4 形状冲突裁决

| 冲突 | v2 现实 | v1/TriMC 期望 | v3 裁决 | 理由 |
| --- | --- | --- | --- | --- |
| `family` 位置 | contract.family | identity.family | **contract.family** | v2 已消费，TriLC 零改动方向 |
| `runtime_baseline` | 对象（host/tri_mc_status/tri_mc_migration_ready） | TriMC 期望 `{name,description}[]` | **对象 `z.record(z.unknown())`，可选** | v2 现实为准；TriMC 侧该字段目前 v1 无数据恒为 undefined，B 段调整为对象形状或弃用 |
| `decision_rights` 键集 | approve/freeze/escalate/forbidden | approve/escalate/forbidden（无 freeze） | **四键统一 + 默认空数组** | 超集收敛，无信息损失 |
| `responsibilities` 形状 | 无（v2 无此字段） | string 或 {description,priority} 混合 | **union 保留** | TriMC normalizeResponsibilities 逻辑直接复用 |

## 三、字段映射表

### 3.1 v1 → v3（docs/registry 11 份，内容搬运）

| v1 字段 | v3 字段 | 规则 |
| --- | --- | --- |
| contract.version "1.0" | contract.version "3.0" | literal 替换 |
| contract.agent_id | contract.agent_id | 值保留；`ChiefTechnologyOfficer` → `chief-technology-officer`（kebab-case 对齐 source-agents 目录名） |
| — | contract.family | 从 identity.family 迁入 |
| identity.* | identity.*（去 family） | 值保留 |
| — | paths | 新写：指向 source-agents 五件套相对路径（`<agent-id>/<五件套文件名>`） |
| responsibilities | responsibilities | 值保留 |
| decision_rights | decision_rights（四键） | 值保留，freeze 缺省 [] |
| collaborators | collaborators | 值保留 |
| tools | tools | 值保留 |
| io_contract | io_contract | 值保留（inputs/outputs 必填） |
| instructions | instructions | 值保留 |
| — | runtime_baseline | 按 2.4 对象形状补齐（host/tri_mc_status/tri_mc_migration_ready） |

### 3.2 v2 → v3（source-agents 14 份，补字段）

| v2 字段 | v3 字段 | 规则 |
| --- | --- | --- |
| contract.*（version 改 3.0） | contract.* | version literal 替换，其余保留 |
| paths | paths | 值保留 |
| decision_rights | decision_rights | 值保留 |
| runtime_baseline | runtime_baseline | 值保留 |
| — | identity | 11 份有 v1 对应者搬运；3 份缺口（business-strategy、customer-success-officer、deployment-engineer）新写 |
| — | responsibilities/collaborators/tools/io_contract/instructions | 同上：搬运或新写 |

### 3.3 员工覆盖矩阵（14 份 3.0 合同全集）

13 员工 + 1 registries 特殊目录（registries 目录非 agent，不进合同全集；如确认为 registry agent 再补）。**r13-2 执行者先核对 source-agents 实际 14 份清单与 employee-roster.json 的 14 员工一致**，缺口员工（有 v2 无 v1 的 3 份）的 identity/io_contract 内容以 employee-roster.json + 对应 source-agents 五件套为源新写。

## 四、迁移序列（5 步，每步一个 commit + 测试门禁）

- **Step 0 golden 基线冻结**（r13-1，CTO）：旧 resolver 对现有 11 份 v1（TriMC loadContract）+ 14 份 v2（TriLC loadAll）解析快照 JSON 落盘 `trees/r13-contract-convergence/golden/`。此后任何等价性比对以此为基准。
- **Step 1 agent-core 新 schema**（r13-1，CTO）：`src/contracts/` 原位重写为 v3.0 实现（`loadContractV3` / `resolveContractsV3`），旧符号与 @deprecated 双清零，单元测试全绿。零消费方，纯增量。
- **Step 2 合同迁移**（r13-2，小全）：14 份 source-agents 合同转 3.0（按 3.2 补字段）+ 3 份缺口新写；v1 11 份暂留（Step 4 前不动）。
- **Step 3 TriLC adapter 切换**（r13-2，小全）：`src/config/contract-resolver.ts` 的 YAML 解析+校验换 agent-core `loadContractV3`；14/14 实载回归（4.2 基准不退化）+ 等价性比对（vs golden 关键字段零 diff）。
- **Step 4 TriMC 切换 + v1 退役**（r13-2，小全）：`src/contracts/resolver.ts` 重写为 thin wrapper（validate/normalize 换 agent-core）；employee-registry 的 registryDir 从 docs/registry 改指 source-agents；编排 suites 回归 + 等价性比对；v1 11 份 `git rm` 退役。

### thin adapter 边界

| 域 | 保留（域逻辑） | 替换（解析校验） |
| --- | --- | --- |
| TriLC | 目录遍历、watcher、五件套路径组装、employee-roster 加载、system prompt 组装 | `ContractYaml` 接口 + 类型断言 → `loadContractV3` |
| TriMC | employee-registry 包装、soul-loader 六要素→prompt、编排层字段消费 | `ContractYamlRaw` + `validateRequiredFields` + `normalizeResponsibilities` + `normalizeTools` → `loadContractV3` |

旧 resolver 处置：**删除，不留兼容路径**（TriLC `ContractYaml` 接口删除；TriMC `resolver.ts` 的 validate/normalize 删除）。git 历史即归档。

## 五、可检验性章节（r13-3 小柯验收口径 10 项）

1. **迁移等价性零 diff**：golden 基线（Step 0 快照）vs 迁移后 3.0 解析，关键字段（agentId/identity/decisionRights/ioContract/paths）逐字段零 diff（脚本自动比对）。
2. **负路径明确拒绝**：1.0/2.0 形状输入 `safeParse=false` 且错误信息含版本与迁移指引。
3. **strict 形状一致**：14 份 3.0 合同无缺字段、无未定义字段（`.strict()` 全绿）。
4. **死 schema 双清零**：agent-core src/dist 旧符号（ContractMetadata/ContractCapability/ContractInstance/旧 AgentContractSchema）与 @deprecated grep 为零；TriMC/TriLC `tsc --noEmit` 零错误。
5. **TriLC 回归**：14/14 实载 + system prompt 非空 14/14（4.2 基准不退化）。
6. **TriMC 切换**：employee-registry 从 source-agents 加载 14 员工合同成功 + contract 相关 suites 全绿。
7. **双域字段级一致**：同一合同 TriLC/TriMC 解析出的 agentId/decisionRights/ioContract 关键字段一致（parity §7 适用项）。
8. **O3 W_OK 校验**：TriMC initializeSession 含 W_OK 工作目录校验 + 负路径测试（基准：TriLC `src/company/session-initializer.ts:44`）。
9. **O4 发布包零残留**：打包产物 grep 旧 schema 符号为零（死 schema 15 文件随重建自然清零）。
10. **迁移序列可追溯**：Step 0-4 各自独立 commit，commit message 可对应迁移步骤。

## 五.2 验证执行细节（2026-08-13 CTO 定准，r13-3 小柯三问）

### ② grep 范围（三层定准）

| 层 | 范围 | 对象 | 判定 |
| --- | --- | --- | --- |
| A（agent-core 仓内） | src + dist（含 .d.ts 声明面） | 死 schema 旧符号：`ContractMetadata`、`ContractCapability`、`ContractInstance`、旧 `AgentContractSchema`（metadata 形状）、旧 `ContractResolver` 类；@deprecated 标注 | grep 为零（双清零） |
| B（TriLC/TriMC 仓内） | src/ | 旧解析路径实现符号：TriLC `ContractYaml`；TriMC `ContractYamlRaw`、`validateRequiredFields`、`validateFamily`、`validateRiskLevel`、`normalizeResponsibilities`、`normalizeTools` | grep 为零（不留兼容分支） |
| C（TriMC 允许保留） | — | 本地类型投影（`agent-contract.ts` 的 AgentContract 等类型定义） | 不强制零；须为 agent-core re-export 或与 v3 字段一致的本域投影；tsc 零错误为准；推荐直接 re-export |

### ④ contract suites 清单（TriMC 存量 + 新增）

- **存量回归**：全量 `npm test` 全绿。contract 消费链 suites：`contract-resolver.test.ts`（Step 4 改写为 v3）、`soul-loader/soul-loader.test.ts`、`orchestration/employee-registry.test.ts`（registryDir 指向 source-agents 后 14 员工）、`orchestration/capability-router|dispatch-proxy|employee-scheduler|cost-controller`、`pipeline-integration/pipeline.test.ts`、`http-agent-endpoint.test.ts`（contract pipeline 路径）、`session-initializer.test.ts`（O3 W_OK 负路径）、`memory-injector/`、`context-builder/`（合同派生消费）。
- **新增 v3 套件**（Step 4 由执行者写）：14 份 source-agents 3.0 合同 `loadContractV3` 全绿 + employee-registry 实载 14 + golden 等价性比对断言。
- **预存失败归因**：沿用 r7-2 归因口径（TUI yoga-layout 缺失、pipeline REQ-006 断言漂移为预存项），不计 B 段失败，但需在验证简报中显式列出。

### ⑤ 双域字段一致清单（完整 11 组）

比对对象 = `AgentContractV3` 全部字段组：`contract.agent_id`、`contract.family`、`identity`（display_name/role/description/user_invocable）、`paths`（6 路径）、`responsibilities`（union 归一后）、`decision_rights`（4 键）、`collaborators`（3 键）、`tools`（含默认值填充后）、`io_contract`（inputs/outputs）、`instructions`（存在性一致）、`runtime_baseline`（对象）。

- 实现方式：同一份 3.0 合同在 TriLC 与 TriMC 两条加载路径产出的解析对象逐字段深度相等（同一 zod schema 天然保证），比对脚本输出 diff。
- 命名归一说明：域内 camelCase/snake_case（agentId vs agent_id）属各自 adapter 投影，比对在 schema 输出层做（agent_id 统一），不算差异。
- golden 等价性比对（①）与⑤的区别：① 是迁移前后（旧解析 vs 新解析）关键字段零 diff；⑤ 是迁移后双域（TriLC vs TriMC 加载同一合同）解析一致。

## 六、决策记录

- 真源落点：source-agents 唯一合同真源；docs/registry v1 退役（治理口径同步已由 CEOChiefOfStaff 路由，OP nextActions）。
- 无兼容分支：schema 只接受 3.0。
- 死 schema 处置：原位重建，删除而非归档。
- runtime_baseline 对象形状裁决（2.4）：TriMC 侧 B 段适配，不迁就数组旧期望。
- 本规格为 r13-2（B 段）执行指引与 r13-3 验证依据，变更需 CTO 批准。
