# ADE 与 TriLC 当前实现差距评估

版本：V1.0
日期：2026-08-07
状态：CPO / CTO 岗位实例审计完成；完整 ADE 开工 FREEZE，裁剪版 local-first MVP APPROVE

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/ade-trilc-current-gap-assessment.md
- syncMode: source-only
- lastSyncedAt: 2026-08-07

## 1. 审计范围

CEOChiefOfStaff 分别调用 ChiefProductOfficer（小乔）与 ChiefTechnologyOfficer（小狄），独立审计 TriLC 的 README、registry、`src/`、`test/`、`package.json`，并交叉核对 `agent-core`、ADE 蓝图、runtime parity 和 Trees 协议。

审计规则：代码与测试优先于 registry 和设计文档；严格区分组件存在、生产接线、可恢复运行语义和完整 ADE lifecycle。

独立验证基线：

- `npm run check`：通过。
- `npm test`：197 tests，195 pass，2 fail。
- 失败文件：`test/tui/components.test.ts`、`test/tui/components-smoke.test.ts`。
- 已确认 `components.test.ts` 缺少 `ink-testing-library`；`components-smoke.test.ts` 的根因待 P0 单独诊断，不在本报告中猜测。

## 2. 联合结论

TriLC 当前准确定位是：

> 共享 Agent loop 驱动的本地 daemon，已经具备一批类 Claude Code 基础组件和局部持久化能力，但尚未形成完整、可恢复、可终态化的 ADE Host。

决策：

- **FREEZE**：直接按当前全量蓝图同时开工两个 profile、双域同步和 Trees projector。
- **APPROVE**：先做 P0 事实基线修复，再实现一个单项目、单定义、TriLC 单写主的 runtime-owned durable MVP。
- **后置**：Agent-owned interactive、TriMC PostgreSQL parity、双域 authority transfer、Trees runtime projector。

## 3. 产品成熟度

| 能力 | 当前成熟度 | 当前用户价值 | 不能承诺 |
| --- | --- | --- | --- |
| Agent tool loop | 已实现 | 本地多轮 Agent、工具调用、流式输出 | 完整 Claude Code 等价体验 |
| Skill | 部分实现 | Agent 可加载 Skill prompt | `allowedTools`、model、output schema 已被 runtime 强制 |
| Permissions / HITL | 部分实现 | TUI 可询问权限 | 持久审批、角色鉴权、崩溃恢复和完整安全门 |
| Conversation session | 已实现 | 可保存、查询并人工恢复历史会话 | 恢复到 DCE / tool 副作用中断点 |
| Cron / heartbeat / daemon | 部分实现 | 本地定时与常驻基础设施 | 完整 crash-safe job lifecycle |
| Event queue / replay | 组件存在 | 离线事件存储与回放积木 | 生产事件不丢、自动重试和 DLQ |
| Planner / task runtime | 骨架 | 可做简单规划与状态跟踪 | 持久任务编排和服务主链接入 |
| 多项目隔离 | 局部实现 | 路径 router 已有测试 | 所有 production store 已按项目隔离 |
| ADE lifecycle | 未实现 | 无 | durable run、checkpoint、Signal、Close CLI、authority |
| Trees runtime | 未实现 | Git 文档可组织追踪 | v0.4 runtime projector 和自动一致性 |

## 4. 技术成熟度矩阵

| 能力 | 状态 | 代码事实 |
| --- | --- | --- |
| `agent-core` loop | 实现 | TriLC server、LocalNode、heartbeat runner 消费共享 `agentLoop` |
| TriMC pipeline parity | 部分 | TriMC 注入 soul/memory/context/gater；TriLC local fallback 仍偏 raw mode |
| Skill loader / SkillTool | 部分 | `SKILL.md` 可解析，但执行结果只是 inline prompt JSON |
| 权限规则持久化 | 部分 | 只持久化按工具名的 always-allow |
| HITL Signal | 未实现 | 当前 pending interaction、FIFO queue、correlation 都在内存 |
| Session store | 实现 | SQLite 保存 session/message/sync metadata |
| ADE run/event/checkpoint store | 未实现 | 无 schema、store、API 或 recovery worker |
| Event queue | 部分 | SQLite store / replay helper 存在；生产主链没有 enqueue producer |
| Cron | 部分 | CRUD、日志、timer 存在；首次调度与 crash-running 恢复有缺口 |
| Planner / task runtime | 部分 | 有类和内存状态；未接 server 主链且不持久 |
| DCE executor | 未实现 | ProcessSupervisor 可作为积木，但无 DCE registry/probe/report contract |
| Authority / lease / version | 未实现 | 无唯一写主、epoch、乐观锁或转移事务 |
| Close Skill / Close CLI | 未实现 | 无 phase runner、decision schema 执行和终态事务 |
| Trees projector | 未实现 | TriLC runtime 零接线 |

## 5. P0 代码偏差

### 5.1 Skill 约束未执行

`TriLC/src/tools/skill-tool.ts` 只把 `allowedTools` 和 `model` 返回到 JSON；没有修改 Agent loop 的工具集合、模型或输出 schema。因此当前 Skill 是 prompt injection，不是 ADE phase runner。

### 5.2 权限工具名和安全顺序不一致

TriLC 注册工具名为 `Write` / `Edit`，共享安全检查识别的是 `write_file` / `edit_file`。同时 decision pipeline 在 safety 之前返回 `ask`；用户允许后若不重新执行 safety，存在绕过强安全检查的风险。

### 5.3 Contract Agent 列表合同不一致

TriLC agents API 返回 `{ agents, count, scope, tricompanyEnabled }`，而 AgentTool 按 `{ ok, agents }` 判断，导致 contract agents 可能不进入显示列表。

### 5.4 Session 不是 checkpoint

Session store 保存消息并可标记 `interrupted`，但不保存 ADE phase、DCE 幂等键、副作用状态、attempt、lease 或 Close decision。

### 5.5 Event queue 没有生产闭环

event queue 的 SQLite store、replay request 和 response helper 已实现，但生产代码未形成稳定的 `enqueue -> retry -> replay -> acknowledgement -> DLQ` 链。

### 5.6 Cron 恢复不完整

新建 job 的首次 `nextRunAt`、崩溃遗留 `running` job 和 timeout 后底层 Agent 取消都需要补证或修复。

### 5.7 Trees 现实数据落后 v0.4

公司协议已升级到 v0.4，但 TriMetaverse 当前导出仍是 v1.0 项目实例数据，存在历史状态与 delivery 完整性问题。它不能作为 ADE runtime 已接入证据。

## 6. Local-first MVP

唯一用户故事：

> 用户在单一项目中显式启动 `project-source-doc-sync@1.0.0`；TriLC daemon 即使在 DCE 前后被杀死，也能从 SQLite checkpoint 恢复，经持久审批和 Close CLI 形成唯一终态与可查证报告。

首期只做：

- `runtime-owned-durable` 一个 profile。
- 一个项目、一个 daemon、TriLC 唯一写主。
- 一个固定 DCE：`project-source-doc-sync@1.0.0`。
- SQLite `run/event/checkpoint/signal/artifact`。
- `run/status/signal/cancel/recover` API。
- 固定 argv、probe、execute、verify、幂等键和 Close CLI。
- 审批超时 fail closed。

首期不做：Agent-owned interactive、TriMC 同步、authority transfer、通用 DCE 市场、文件/Git 自动触发、多项目 runtime store、Trees projector、PostgreSQL 和集群 lease。

## 7. 优先级

### P0：事实基线与安全

1. 修复工具名与 safety / permission alias。
2. 确保 `ask -> allow` 后仍执行 bypass-immune safety。
3. 修复 contract Agent API / AgentTool 合同。
4. 修复 cron 首次调度、running recovery 和 timeout cancel。
5. 接入真实 event producer；定义 retry / acknowledgement / DLQ。
6. 清零当前全量测试失败。
7. 修复 Trees 项目实例 validator 和历史状态问题。

### P1：单定义 durable MVP

1. `agent-core/src/ade` 状态机和 store contract。
2. TriLC SQLite ADE store。
3. 固定 DCE executor、probe、verify。
4. 持久 Signal、Close decision 和 Close CLI。
5. daemon kill / restart 恢复测试。

### P2：扩展生命周期

Agent-owned interactive、文件/Git/cron trigger、多项目 store、Trees 投影、TriMC PostgreSQL parity、authority transfer、observability 和 chaos tests。

## 8. 硬门禁

- 重复 trigger 不产生重复 run 或副作用。
- DCE 前后 kill daemon 均可恢复。
- 高风险审批超时不得默认 allow。
- Close Skill 之前不能写终态。
- 终态 evidence hash 可追溯。
- 文件与 DCE 不能越出项目根。
- 当前 Agent session 关闭后 run 仍可完成或明确冻结。
- 全量 typecheck 与 tests 通过。

## 9. 证据入口

- `TriLC/src/server/app.ts`
- `TriLC/src/tools/skill-tool.ts`
- `TriLC/src/server/interactions.ts`
- `TriLC/src/session-store/store.ts`
- `TriLC/src/event-queue/queue.ts`
- `TriLC/src/cron/store.ts`
- `TriLC/src/cron/timer.ts`
- `TriLC/src/runtime/daemon.ts`
- `TriLC/src/tools/agent-tool.ts`
- `TriMC/packages/agent-core/src/loop.ts`
- `TriMC/packages/agent-core/src/permissions-engine/decision-pipeline.ts`
- `TriMC/packages/agent-core/src/permissions-engine/safety-check.ts`
- `TriMetaverse/docs/workflow/tree-nodes-export.json`

## 10. 小贾收口

- 小乔结论：完整 ADE / 双域 parity 就绪声明 `FREEZE`；裁剪版 local-first MVP `APPROVE`。
- 小狄结论：当前为共享 Agent loop + 局部基础设施，完整 ADE Host 与 parity 均未成立；必须先完成 P0。
- 总助裁决：更新设计成熟度与 Phase 顺序；未完成 P0 前不创建完整 ADE TriDev run。
