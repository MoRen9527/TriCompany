# ADE 生命周期行业模式联审

版本：V1.0
日期：2026-08-07
状态：CPO / CTO 岗位实例已完成 TriLC 代码复核；双 profile 目标保留，完整 ADE 开工 FREEZE

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/ade-lifecycle-industry-review.md
- syncMode: source-only
- lastSyncedAt: 2026-08-07

## 1. 研究问题

本次联审比较两条候选链：

```text
A. 程序触发 -> Agent 判断 -> Plan Skill -> DCE -> Close Skill -> Close CLI
B. Agent 检测 -> 程序登记事件 -> Plan Skill -> DCE -> Close CLI -> Close Skill
```

需要判断：

1. 行业内是否同时存在程序持有生命周期与 Agent 持有交互循环两类模式。
2. 两类模式是否有独特使用场景。
3. 应保留两套 ADE，还是保留一套协议并提供两个 profile。
4. Close Skill 与 Close CLI 的终态顺序应如何定义。

## 2. 官方资料观察

### 2.1 OpenAI Agents SDK：Agent 持有交互循环

OpenAI Agents SDK 的 Runner 会反复调用模型：模型产生 tool calls 时，运行工具、追加结果并重新进入循环；只有产生没有 tool calls 的 final output 时循环才结束。

这对应 Agent 发起或持有当前交互任务的模式：

```text
Agent -> tool/DCE -> tool result -> Agent final output
```

来源：<https://openai.github.io/openai-agents-python/running_agents/>

### 2.2 AutoGen：同一框架同时支持内部和外部终止

AutoGen 的 termination condition 在每个 Agent 响应后检查；同时提供 `ExternalTermination`，允许程序从运行外部控制终止。

这说明“Agent 产生终止信号”和“程序控制生命周期”可以在同一框架内共存，不要求复制两套 orchestration。

来源：<https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html>

### 2.3 Microsoft Agent Framework：Runtime 持有 durable workflow

Microsoft Agent Framework Workflows 使用 executors 与 edges 描述图式流程，支持条件路由、并行执行、外部 request/response、human-in-the-loop 和 checkpoint；checkpoint 用于服务端长流程恢复与继续执行。

这对应程序 / runtime 持有 run 状态、Agent 只是阶段执行者的模式。

来源：<https://learn.microsoft.com/en-us/agent-framework/workflows/>

### 2.4 LangGraph：同图混合确定性步骤与 Agent 步骤

LangGraph 把 durable execution、human-in-the-loop、持久化和长时有状态 Agent 作为底层 orchestration 能力，并明确支持在同一 graph 中混合 deterministic steps 与 LLM-driven steps。

这支持“一套状态机中同时装配 Skill 与 CLI”，而不是把 Skill 流程和 ADE 流程拆成互斥产品。

来源：<https://docs.langchain.com/oss/python/langgraph/overview>

### 2.5 Temporal：Durable workflow 包裹 Agent 与工具调用

Temporal AI Cookbook 将 LLM、agentic loop、tool calling 和 human-in-the-loop 放入 durable Workflow；其示例包括 durable agent、tool-calling agent 和通过 Signal 接入人工审批。

这支持程序触发、跨会话恢复、失败重试和最终收口由 workflow runtime 保证的场景。

来源：<https://docs.temporal.io/ai-cookbook>

### 2.6 MCP：工具协议不等于 Agent 生命周期协议

MCP 定义 host、client、server 之间的上下文与工具交换，但明确不规定 AI 应用如何使用 LLM 或管理上下文。它可以承载 DCE 工具调用，却不能单独替代 ADE 的触发、状态机、恢复和终态提交。

来源：<https://modelcontextprotocol.io/docs/learn/architecture>

### 2.7 关键词提取

| 关键词 | 行业语义 | ADE 对应能力 |
| --- | --- | --- |
| `checkpoint` | 在稳定边界保存 workflow / graph 状态，以便失败后继续 | 每次状态转换及外部副作用前后的持久快照 |
| 跨会话恢复 | Agent 会话或进程结束后，任务仍可从持久状态恢复 | `runId`、checkpoint、恢复 worker 与幂等重放 |
| `runtime` | 持有 graph、状态、重试、暂停和恢复的生命周期 owner | ADE orchestrator 与 canonical run store |
| `agent loop` | 模型输出 tool call，runtime 执行工具并把结果送回模型，直到 final output | Plan / Close Agent phase 与 Agent-owned interactive profile |
| `graph` | 将 Agent、工具、条件路由、并行和终止组织成可观测节点/边 | ADE 状态机和 profile topology |
| 外部 request / response | Workflow 发出请求并等待外部系统或人工响应 | 持久 `signal`、correlation ID 与 `WAITING_SIGNAL` |
| `human-in-the-loop` | 在关键节点暂停，等待批准、拒绝、补充或取消 | approval signal、Close Skill 输入与权限门 |
| `durable execution` | 进程失败、网络中断或等待很久后仍可继续 | event log、checkpoint、retry budget、recovery scan |
| `deterministic steps` | 同输入产生可复现结果的代码步骤 | DCE、Verify CLI、Close CLI |
| `LLM-driven steps` | 依赖上下文做规划、解释与语义判断 | Qualify Agent、Plan Skill、Close Skill |
| `tool calling` | Agent 通过结构化参数调用外部能力并接收结果 | Agent loop 调用 DCE / Verify adapter |
| `durable agent` | Agent loop 被 durable workflow 包裹，不依赖单次会话存活 | Runtime-owned profile 及 Agent-owned profile 的持久 run |
| `Signal` 人工审批 | 外部事件恢复暂停的 workflow | `ade_signals`、幂等 signal API 与等待状态恢复 |

### 2.8 概念共性

这些资料虽使用不同术语，但共同指向同一个工程模型：

1. **智能步骤和确定性步骤混合**：LLM 负责 Qualify、Plan、Close，代码负责执行、验证和终态写入。
2. **Runtime 而非聊天上下文持有生命周期**：无论由程序还是 Agent 触发，run 都必须有持久标识和状态。
3. **外部副作用必须可重放但不能重复生效**：事件通常至少投递一次，副作用通过 idempotency key 实现 effectively-once。
4. **等待不是失败**：人工审批、外部响应和资源暂缺进入 `WAITING_SIGNAL`，由 Signal 恢复。
5. **checkpoint 与 event log 分工**：event log 解释发生过什么，checkpoint 提供从哪里继续。
6. **终止条件必须机器可校验**：Agent 形成语义裁决，Close CLI 校验证据与状态转换后提交终态。
7. **观测数据不是运行真源**：timeline / replay 可投影 ADE 事件，但不能替代 canonical run store。

### 2.9 对当前实现缺口的映射

| 共性能力 | 当前可复用资产 | 仍缺什么 |
| --- | --- | --- |
| 事件触发 | TriLC cron、heartbeat、local bus、event queue、`fs.watch` 经验 | 文件/Git ADE detector、统一事件 envelope、去重键 |
| Agent loop | `@trimetaverse/agent-core` tool-calling loop | Runtime 主动装载指定 Plan / Close Skill 的 phase runner |
| Skill | TriLC SkillTool 与目录 loader | 版本化 Skill resolver；TriMC 尚无等价装载面 |
| DCE | `source_publish_check --project-docs` | DCE registry、无 shell argv 执行器、probe/resume 合同 |
| checkpoint / 恢复 | TriLC session store、event queue；TriMC replay/observability | 独立 ADE run/event/checkpoint store 与 recovery worker |
| HITL / Signal | TriLC interaction bridge；TriMC approval audit event 映射 | 持久 signal store、等待状态、跨进程 answer API |
| 终态提交 | 当前人工 APPROVE/FREEZE/ESCALATE | Close decision schema 与 Close CLI 事务落账 |
| Trees | `task_trees` / `tree_nodes` 与 Git 导出 | ADE run 引用投影；不得复刻 ADE 内部状态机 |

### 2.10 双域 Runtime 共性

TriLC 与 TriMC 的差别不是“有无完整 Agent runtime”，而是同一 runtime 部署在本地域和服务域后的 adapter 差异。当前 TriLC 已具备类 Claude Code Agent loop、SkillTool、permissions、cron、session、HITL 与本地工具，后续应优先抽象共享能力并同步给 TriMC。

因此 ADE 实施遵循：

- 一套 `agent-core` ADE runtime。
- TriLC SQLite / 本地 trigger / TUI adapter。
- TriMC PostgreSQL / 服务 trigger / 集群 adapter。
- 两域使用相同 conformance suite。
- 每个 run 以 authority 字段防双活，而不是固定假设 TriMC 永远是 canonical writer。

## 3. 小乔产品 owner 视角

结论：两类入口都有独特价值，应保留两种使用 profile。

### 3.1 Runtime-owned durable profile

适用：

- 文件 watcher、Git hook、webhook、cron、CI 事件触发。
- 无人值守、异步或跨会话任务。
- Agent 中断后仍必须恢复并收口的任务。
- 合规、发布、部署、账务等不能靠聊天会话记忆维持的任务。

用户价值：任务即使没有持续对话，也不会丢失生命周期或静默停在执行后。

### 3.2 Agent-owned interactive profile

适用：

- Agent 在当前会话中发现真源漂移、测试缺口或需要同步。
- 用户临时要求执行一次短任务。
- 计划高度依赖当前对话上下文，并希望 Agent 在同一回合解释结果。
- 低延迟、可交互、失败后立即调整计划的任务。

用户价值：不需要等待后台 watcher；Agent 可利用当前上下文即时发起并解释结果。

### 3.3 产品侧建议

保留两个 profile，但不向用户暴露两套重复工具、manifest、状态枚举和审计系统。

## 4. 小狄技术 owner 视角

结论：保留一套 ADE 协议和状态机，两个 profile 只改变触发者与生命周期 owner。

### 4.1 统一不可变顺序

```text
Event/Detection
-> Qualify
-> Plan Skill
-> DCE
-> Verify CLI（可选）
-> Close Skill
-> Close CLI
-> Terminal State
```

Close Skill 是最后的语义裁决者；Close CLI 是最后的确定性状态提交者。

### 4.2 对候选链 B 的修正

若某个 CLI 位于 Close Skill 之前，它只能叫：

- execution report CLI
- verify CLI
- evidence finalizer

它不能把 run 写成终态。真正的 Close CLI 必须位于 Close Skill 之后，否则语义裁决无法阻止错误终态。

Agent 对用户输出最终自然语言回复可以放在 Close CLI 之后；这不改变 Agent-owned profile 的交互属性。

### 4.3 统一状态机

```text
DETECTED
-> QUALIFYING
-> PLANNING
-> PLANNED
-> EXECUTING
-> VERIFYING
-> CLOSING
-> FINALIZING
-> APPROVED | FROZEN | ESCALATED | RETRY
```

### 4.4 Profile 字段

建议每个 run 至少声明：

```json
{
  "triggerProfile": "runtime-event|agent-interactive",
  "triggerOwner": "runtime|agent",
  "lifecycleOwner": "runtime|agent-session",
  "planSkill": "<skill-id>@<version>",
  "dce": "<cli-contract>",
  "closeSkill": "<skill-id>@<version>",
  "closeCli": "<cli-contract>"
}
```

无论 profile 为何，都共用 `runId`、事件去重、source revision、状态转换、重试预算和审计 schema。

## 5. CEOChiefOfStaff 最终裁决

**APPROVE：保留一套 ADE 协议框架，提供两个生命周期 profile。**

| Profile | 触发与持有者 | 独特场景 |
| --- | --- | --- |
| Runtime-owned durable | 程序触发，runtime 持有 run 至终态 | watcher、Git、cron、CI、异步、跨会话、强审计 |
| Agent-owned interactive | Agent 检测并登记 run，当前 Agent/session 驱动 | 会话内临时任务、上下文密集、低延迟、即时解释 |

不批准：

- 复制两套状态机、CLI 实现、manifest 或审计 schema。
- 把 `DCE` 单独称为完整 ADE。
- 在 Close Skill 之前提交不可逆终态。
- 把只有“tool call -> final response”、没有持久 run 与 Close CLI 的普通 agent loop 写成 durable ADE。

## 6. 当前实现成熟度

当前 `source_publish_check --project-docs` 已实现 DCE 与结构化执行报告。

当前尚未实现完整 ADE 生命周期中的：

- 文件 / Git 事件 watcher 与事件去重。
- `runId` 和持久状态机。
- Plan Skill / Close Skill 的版本化装载。
- Close CLI 的终态校验与审计落账。
- Runtime-owned durable profile 的中断恢复。

因此当前项目真源同步应标为：**DCE 已落地，ADE 生命周期设计已裁决，runtime/skill/close-cli 待实现。**

## 7. 完整实施入口

结合 TriLC、TriMC、`@trimetaverse/agent-core` 与 Trees 协议的模块落位、数据模型、API、恢复机制、测试矩阵和 Phase 0-6 门禁，统一见 [ADE 全生命周期实现蓝图](ade-full-lifecycle-implementation-plan.md)；双域同构和能力同步原则见 [TriLC / TriMC 共享 Runtime Parity 决策](trilc-trimc-runtime-parity.md)。
