# 动态任务树协议

版本：V0.5
日期：2026-08-12
状态：公司级 workflow 真源；TriMetaverse 当前项目实例按 adapter 适配

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/dynamic-task-tree-protocol.md
- syncMode: source-only
- lastSyncedAt: 2026-08-12

## 1. 文档定位

动态任务树是 TriCompany 的公司级组织编排协议，用于描述公司员工如何接收、流转、升级和收口跨项目任务。它属于公司维度，可被 TriMetaverse 及未来其他项目实例复用。

协议真源只定义：

- 公司角色与组织责任。
- 树、节点、信号和状态合同。
- 项目实例、宿主运行时与 ADE run 的引用关系。
- 持久化、恢复和收口的最低要求。
- 执行交接、存档检查点和幂等续跑的公司级规则。
- 多树并行调度的组织约束。

具体项目的周索引、`tree-op.json`、Git 导出文件、数据库路径和校验脚本属于项目实例 adapter，不回写为公司协议本身。

## 2. 公司角色

| 层级 | 默认角色 | 职责 |
| --- | --- | --- |
| 最终裁决层 | CEO | 方向、重大风险、跨 C-Level 分歧和保留事项裁决 |
| 组织编排层 | CEOChiefOfStaff | 持树、创建节点、路由、升级、跨周期迁移和收口检查 |
| 机器路由层 | 当前宿主 runtime | 读取树投影、发现 `in_progress` 节点、调用对应员工、提交状态变化建议 |
| 专业 owner | CPO / CTO / CHO / CAO / CMO / COO / CFO | 在各自决策权内判断、交付、建议下一节点或升级 |
| 执行节点 | FullStackDeveloper / TestEngineer / DeploymentEngineer / RAndDTrainer / CustomerSuccessOfficer 等 | 完成节点动作、提供交付证据、尽力判断 `next_agent` |

机器路由层不替代 CEOChiefOfStaff 创建组织节点，也不绕过对应 owner 做专业裁决。

## 3. 树结构

每棵任务树对应一个公司经营事项、项目动作或跨项目交付目标。树可以包含主树和子树，但默认不超过三层。

建议考虑拆子树的条件：

- 预计节点数不少于 8；并且
- 至少包含 2 条相互独立的并行轨。

该阈值是当前 Copilot-host 阶段的经验基线；宿主并发、持久化和冲突隔离能力变化后，可由 CPO / CTO 联审调整。

## 4. 数据模型

### 4.1 `task_trees`

| 字段 | 说明 |
| --- | --- |
| `id` | 树主键 |
| `op_action_id` | 可选经营事项引用 |
| `title` | 树标题 |
| `root_agent` | 根节点角色，默认 `CEOChiefOfStaff` |
| `status` | `active / done / escalated` |
| `project_id` | 当前项目实例标识 |
| `created_at / updated_at` | 时间戳 |

### 4.2 `tree_nodes`

| 字段 | 说明 |
| --- | --- |
| `id` | 节点主键 |
| `tree_id` | 所属树 |
| `parent_node_id` | 父节点；根节点为 `null` |
| `agent` | 执行角色 |
| `action` | 节点动作 |
| `status` | `pending / in_progress / done / escalated` |
| `delivery` | 完成交付描述或证据引用 |
| `next_agent` | 执行节点建议的下一角色 |
| `seq` | 排序序号 |
| `routedInput` | V0.5 新增。前节点 checkpoint 引用（如 `"<nodeId>:checkpoint"`），作为交接输入。开工前必读；首节点为空 |
| `checkpoint` | V0.5 新增。存档结构，包含：`progress`（已完成部分描述）、`artifactCommit`（产物 git 证据 SHA，无产物可留空但需说明）、`resumePoint`（崩溃后可续跑的位置描述） |
| `execution_protocol` | 可选，当前支持 `ade` |
| `ade_run_id` | 可选 ADE run 引用 |
| `ade_profile` | 可选 `runtime-owned-durable / agent-owned-interactive` |
| `ade_terminal_status` | 可选 ADE 终态投影 |
| `ade_evidence_ref` | 可选 ADE close evidence 引用 |

#### 4.2.1 routedInput 规则

- 引用前一节点的 `nodeId`（如 `"r7-1:checkpoint"`）。
- 节点状态变更为 `in_progress` 前，执行 agent 必须已读取并理解 routedInput。
- 首节点（根节点直接创建）routedInput 为空。
- routedInput 不存储完整上下文——仅存引用，上下文从对应节点 checkpoint 读取。

#### 4.2.2 checkpoint 规则

- `progress`：每次状态变更同步更新（存档即提交）。描述节点已完成的部分，不包含未执行内容。
- `artifactCommit`：节点产物的 git commit SHA。无产物节点可留空，但必须在 progress 中说明。
- `resumePoint`：描述从何处续跑，是幂等续跑的依据。格式为自然语言描述（如 "已完成 TriMC /tasks/result 端点代码审查，下一步写 TriLC 侧回传调用"）。

ADE 内部的 `PLANNING / EXECUTING / VERIFYING / CLOSING`、checkpoint、attempt、lease 和 signal 不进入 Trees 状态机。Trees 只保留组织投影。

## 5. 状态枚举

| 层级 | 有效枚举 |
| --- | --- |
| 树级 | `active / done / escalated` |
| 节点级 | `pending / in_progress / done / escalated` |

节点状态机：`pending → in_progress → done | escalated`。禁止跳变（`in_progress` 前必须经过 `pending`）。

历史节点状态 `active` 统一映射为 `in_progress`；`closed` 不再作为树或节点状态使用。

ADE 投影约束：

- 节点 `done` 且 `execution_protocol=ade` 时，`ade_terminal_status` 必须为 `APPROVED`。
- ADE `FROZEN` 默认不自动改变组织节点状态，由 CEOChiefOfStaff 判断继续 `in_progress` 还是升级。
- ADE `ESCALATED` 可建议节点转 `escalated`，但组织分支仍由 CEOChiefOfStaff 创建。
- ADE `RETRY` 不改变 Trees 状态。

## 6. 信号协议

### 6.1 流转信号

```text
CEOChiefOfStaff: #<tree-id> <current-node> -> <next-agent>
```

标准动作：

1. 校验当前节点交付（含 checkpoint 完整性）。
2. 当前节点转 `done`。
3. 已存在的下一节点转 `in_progress`；节点不存在时由 CEOChiefOfStaff 创建。
4. 更新树时间戳和项目实例投影。

### 6.2 Git 触发交接（V0.5 新增）

当项目实例以 Git 作为交接通道时，commit 即交接信号：

- 节点状态变更（`pending → in_progress → done`）均通过 commit 记录。
- 每个节点的 `done` commit 是下一节点 `in_progress` 的前置条件。
- 项目实例 adapter 负责确保 commit 可被发现和消费（如通过 hook、轮询 tree-op.json 或 CI 触发）。
- Git 交接不替代 §6.1 的信号协议——CEOChiefOfStaff 仍负责路由和收口，Git 是机器可读的交接证据。

### 6.3 路由兜底

执行节点应先尽力判断 `next_agent`。只有跨模块边界不清、存在多个 owner 或需要 CEO 裁决时才允许留空。

`next_agent = null` 时默认回到 `CEOChiefOfStaff` 做路由评估，不静默结束。

### 6.4 升级信号

```text
ESCALATE <tree-id> <node-id>: <reason>
```

CEOChiefOfStaff 负责组织讨论、延伸分支、回退、冻结或升级 CEO。

### 6.5 查询信号

```text
<tree-id> status
list active trees
```

项目实例 adapter 负责将结构化状态渲染给当前宿主。

## 7. 执行恢复机制（V0.5 新增）

### 7.1 崩溃恢复流程

当进程、会话或网络中断导致节点执行中断时，按以下顺序恢复：

1. 按 `treeId` 定位 tree-op.json（Git 永不丢）。
2. 扫描全部节点，找到第一个 `status = in_progress` 的节点——即崩溃节点。
3. 读取该节点的 `checkpoint`（progress / artifactCommit / resumePoint）。
4. 从 `resumePoint` 描述的位置幂等续跑（已存档进度不重做）。
5. 续跑完成后更新 checkpoint → 进入正常流转。

### 7.2 幂等要求

节点执行必须可重入：
- 已完成的子步骤可跳过或覆盖（基于 checkpoint.progress 判断）。
- 禁止"重跑产生重复副作用"——重复 commit 通过新 commit + 说明处理，不得 amend/force-push 已交下游的节点 evidence。
- 节点 `escalated` 时，根节点裁决：修后重跑（保留 checkpoint）或改路由（换 agent / 换节点分支）。

### 7.3 恢复优先级

恢复时优先从 runtime store 读取非终态树与节点；runtime 不可用时从项目导出副本重建。若节点绑定 ADE run，查询共享 ADE runtime 的 canonical / authority 状态。恢复结果由 CEOChiefOfStaff 决定继续、回退、重新路由或升级。

## 8. 多树并行调度（V0.5 新增）

### 8.1 并行约束

- 每树独立 `treeId` 和独立 tree-op.json（`trees/<treeId>/tree-op.json`）。
- 根节点（CEOChiefOfStaff）统一资源调度：多树并行时不重复分配同一 agent 到时间冲突的节点。
- 树间无共享可变状态。共享只读资产（如清单文档、registry 文件）可并发读。

### 8.2 树间协调

- 一棵树的节点交付可作为另一棵树的 routedInput（通过引用）。
- 树间依赖由 CEOChiefOfStaff 在建树或路由时显式声明，不通过隐含的共享状态推导。

## 9. ADE 与 Trees

ADE 是执行生命周期协议，Trees 是组织任务协议。

```text
Tree node（谁负责、交付什么）
  -> ade_run_id（如何可靠执行）
  -> ADE terminal / close evidence
  -> Tree node delivery / status projection
```

Trees 不创建 ADE 内部 checkpoint；ADE 也不擅自创建组织节点。

### 9.1 与 TriMC / 交付板的接口

| 层 | 机制 |
| --- | --- |
| 交付板 | 节点状态 commit = 交付信号（收口门禁的正式形态由项目实例 adapter 定义） |
| ADE | Agent plans（建树/规划）→ Deterministic CLI executes（节点执行）+ Agent closes（判定收口） |
| TriMC（中期） | cron / dispatch 直接读 tree-op.json 驱动节点调度；git 事件 = 节点变更触发 |
| 崩溃检测（中期） | 心跳 / 超时机制 → 标记 running 节点为可疑 → 触发 §7 恢复流程 |

## 10. 持久化与项目实例

### 10.1 公司协议与项目数据分离

- 公司真源：`TriCompany/docs/workflow/dynamic-task-tree-protocol.md`。
- 项目实例：各项目自己的 operating records、tree directories、数据库与导出文件。
- 中央摘要：项目可保留同名 `published-summary`，说明本项目落位和当前 adapter。

### 10.2 最低持久化要求

项目实例至少持久化：

- 树与节点当前状态（含 routedInput 和 checkpoint）。
- 每次状态变更时间和 actor。
- 节点交付与证据引用（含 artifactCommit）。
- ADE run 引用（如适用）。
- 可在宿主或会话丢失后重建的导出 / API。

Git JSON 可以作为审计、交换和灾难恢复副本，但正式 runtime 可使用 SQLite、PostgreSQL 或其他事务 store。

### 10.3 TriLC / TriMC 等价运行原则

TriLC 与 TriMC 使用同一共享 Trees / ADE runtime 合同和状态机：

- TriLC 使用本地域 adapter，例如 SQLite、本地文件/Git 触发、TUI 和离线队列。
- TriMC 使用服务域 adapter，例如 PostgreSQL、webhook/CI、服务端 Signal 和集群 worker。
- 两域同步时由 `homeDomain / writeAuthority / version` 确定唯一写主，禁止双活写入。
- 除本地与服务域特殊 adapter 外，Agent loop、Skill、DCE、Close、checkpoint、恢复和 Trees 投影行为保持 parity。

## 11. 收口检查

完成节点或关闭树时，CEOChiefOfStaff 至少检查：

1. 树与项目实例目录 / 数据记录一致。
2. 状态枚举合法（含节点状态机跳变顺序）。
3. `done` 节点具有 `delivery` 和完整的 `checkpoint`。
4. `routedInput` 引用的前一节点 checkpoint 可追溯。
5. ADE 节点满足终态投影约束。
6. 项目周索引或等价项目索引已同步。
7. Git 审计副本、数据库或 API 投影可恢复。

## 12. 当前 TriMetaverse 实例

TriMetaverse 当前项目实例继续使用：

- `docs/workflow/operating-records/<week>/trees/<tree-id>/tree-op.json`
- `docs/workflow/tree-nodes-export.json`
- `scripts/export-tree-nodes.ps1`
- `scripts/validate-tree-status-enums.ps1`

TriMetaverse 端的适配文档路径：
- 协议发布摘要：`docs/workflow/dynamic-task-tree-protocol.md`（published-summary，sourceOfTruth 指向本文件）
- 原始错误创建的 `docs/execution/trees-execution-protocol.md` 已按治理移除，内容合并入本协议 V0.5

这些路径是 TriMetaverse adapter，不属于公司协议的跨项目固定路径。

## 13. 变更治理

- 公司协议 owner：CEOChiefOfStaff；行政与制度归属由 CAO 复核。
- 产品体验与拆树阈值：CPO 复核。
- 数据模型、runtime parity、恢复与 ADE 映射：CTO 复核。
- 项目实例只能扩展 adapter 字段，不得在中央副本中独立改写公司核心状态语义。

## 变更记录

- V0.5（2026-08-12）：治理修正——合并 TriMetaverse `trees-execution-protocol.md` 中公司级协议内容；新增 routedInput/checkpoint 字段（§4.2）；新增 Git 触发交接（§6.2）；新增执行恢复机制与幂等要求（§7）；新增多树并行调度（§8）；收口检查扩展（§11）；ADE 接口层更新（§9.1）；TriMetaverse 实例路径修正（§12）。CPO + CTO 联审通过。
- V0.4（2026-08-07）：当前公司级基线；ADE V0.4 映射。
