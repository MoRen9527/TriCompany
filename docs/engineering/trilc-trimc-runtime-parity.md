# TriLC / TriMC 共享 Runtime Parity 决策

版本：V1.1
日期：2026-08-13（V1.0：2026-08-07）
状态：CPO / CTO 岗位实例代码审计完成；目标边界保留，当前 parity 未成立；V1.1 刷新 agent-core 物理路径（R7 迁移后现状）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/trilc-trimc-runtime-parity.md
- syncMode: source-only
- lastSyncedAt: 2026-08-13

## 1. 核心结论

TriLC 是本地域 Host，TriMC 是服务域 Host。除域特有能力外，两者应运行同一套 Agent / ADE runtime，并保持行为 parity。

“TriLC 向 TriMC 同步”统一解释为：

```text
TriLC 已验证的宿主无关能力
-> 抽取 / 泛化到 @tricompany/agent-core
-> TriLC 与 TriMC 同时消费共享实现
-> 各自只保留 local / service adapter
-> 用同一 conformance suite 验证 parity
```

禁止把它实现成：

- 复制一份 `TriLC/src` 到 `TriMC/src`。
- 在 TriMC 重新编写第二套 Agent loop、Skill runner、ADE orchestrator 或 Close finalizer。
- 把 TriLC 永久降级成只有离线 fallback 的弱 runtime。
- 因代码共享而允许两个域同时写同一个 run。

## 2. 当前事实

已成立：

- `@tricompany/agent-core` 位于 `TriCompany/packages/agent-core/`（V1.1 刷新：2026-08-12 经 CPO/CTO 归属审核 + CEO 批准，从 `TriMC/packages/agent-core/` + `@trimetaverse` scope 迁移至公司维度，见 R7 记录），TriLC 通过 `file:` 依赖并在构建时 bundle，运行时不依赖 TriMC 网络在线。
- 共享 core 已包含 Agent loop、tool registry、permissions、sub-agent、contracts、process supervisor 和 scheduler。
- TriLC 已具有类 Claude Code 的本地 Agent loop、SkillTool、permissions、session、cron、HITL、daemon 与本地工具等基础组件；部分生产接线与完整产品语义仍有缺口。
- TriMC 已具有服务端 HTTP/SSE、pipeline、observability、PostgreSQL 和集群部署面。

物理代码路径位于 TriCompany workspace（公司维度）是已批准的治理选择（V1.1），不表示任何项目域天然拥有每个运行实例的写权威。

当前 parity 只在共享 Agent loop、tool registry、权限抽象和部分 process/scheduler 能力成立；Skill 约束、pipeline、持久化、调度恢复、HITL、ADE lifecycle 和 Trees runtime parity 均未成立。

## 3. 共享面

必须进入共享 runtime 或共享合同：

- Agent loop 与 tool-calling loop。
- Skill resolver、Plan / Close phase runner。
- permissions / tool gating。
- ADE 状态机、orchestrator、DCE registry、Verify 和 Close finalizer。
- checkpoint / recovery policy。
- retry、idempotency、lease 和 authority transfer 合同。
- Trees 投影接口与 observability event 合同。
- Agent / ADE API schema 和 conformance tests。

## 4. 差异面

| 能力 | TriLC 本地域 adapter | TriMC 服务域 adapter |
| --- | --- | --- |
| 数据库 | SQLite WAL | PostgreSQL |
| Trigger | 文件、Git、本地 cron、heartbeat、TUI | webhook、CI、服务 cron、API、cluster event |
| Tool | 本地文件、shell、桌面、设备 | 服务 API、集群、服务域资源 |
| HITL | TUI / 本地通知 | API / Web UI / 消息通道 |
| Runtime 进程 | 本地 daemon / watchdog | K8s worker / service |
| Offline | 本地独立运行与 outbox | 服务端高可用与队列 |
| Observability | 本地 timeline，后续同步 | 服务端 timeline / dashboard |
| 部署 | PC bundle | Server / K8s |

差异面通过 dependency injection / adapter interface 实现，不进入共享状态语义。

## 5. ADE 双域写权威

TriLC 和 TriMC 都能完整运行 ADE，但同一 run 只能有一个写主：

```json
{
  "homeDomain": "local|service",
  "writeAuthority": "trilc:<node-id>|trimc:<cluster-id>",
  "authorityEpoch": 1,
  "version": 12
}
```

- local-owned run 可在 TriLC 完整终态化，并向 TriMC 同步只读投影。
- service-owned run 可由 TriMC 完整终态化，需要本地 DCE 时委托 TriLC，但写权仍在 TriMC。
- authority 转移必须 checkpoint、撤销旧 lease、递增 epoch 后显式完成。
- 旧 epoch、低 version 或非 authority 的状态写入必须被拒绝。

## 6. 能力同步节律

### 6.1 Local-first 能力

适用于文件/Git、TUI、桌面工具、本地开发和离线场景：

1. 先在 TriLC 用真实本地工作流验证。
2. 抽取宿主无关部分到 `agent-core`。
3. TriLC 改为共享 core + local adapter。
4. TriMC 接入共享 core + service adapter。
5. 跑双域 conformance suite。

### 6.2 Service-first 能力

适用于 K8s、服务 webhook、PostgreSQL、集群 lease 和服务域 observability：

1. 先在 TriMC service adapter 验证。
2. 共享合同和可复用逻辑进入 `agent-core`。
3. TriLC 对不适用能力显式声明 `not-applicable`，而不是伪实现。
4. 共享行为继续跑 parity tests。

## 7. Parity Gate

每个共享能力至少通过：

1. 相同输入事件产生相同状态转换。
2. Plan / Close Skill 输出 schema 一致。
3. DCE / Verify / Close 报告合同一致。
4. SQLite / PostgreSQL adapter 通过同一 repository conformance suite。
5. 进程中断后从相同 checkpoint 恢复到等价状态。
6. 重复 event / signal / DCE 不产生重复副作用。
7. authority 转移和旧 epoch 拒绝行为一致。
8. Trees 与 observability 投影语义一致。

域特有能力单独测试，不计入共享 parity 缺口。

## 8. 与 Trees 的关系

Trees 是公司级组织协议，由 `TriCompany/docs/workflow/dynamic-task-tree-protocol.md` 维护。

TriLC / TriMC 使用同一 Trees 投影接口：

- runtime 只更新已有节点的 ADE 投影和 delivery 建议。
- 新组织节点仍由 CEOChiefOfStaff 创建。
- 项目 adapter 决定 tree-op、数据库和导出路径。
- 双域同步不得生成两份相互竞争的 Trees 真源。

## 9. 实施顺序

1. 先完成 TriLC P0 事实基线修复：权限、Agent API、cron、event producer、全量测试和 Trees validator。
2. 扩展 `agent-core` 为完整可注入 ADE runtime。
3. 利用 TriLC 基础组件完成单项目、单定义、单写主的 local durable MVP。
4. TriMC 接入同一 runtime 并补 service adapter。
5. 完成双域 authority sync。
6. 接入公司 Trees 投影与项目 adapter。
7. 通过生产 chaos / parity gate。

详细差距见 [ADE 与 TriLC 当前实现差距评估](ade-trilc-current-gap-assessment.md)，阶段和 schema 见 [ADE 全生命周期实现蓝图](ade-full-lifecycle-implementation-plan.md)。

## 10. Owner

- CEOChiefOfStaff：公司协议、Trees、跨项目复用和 owner 路由。
- CTO：共享 runtime、双域 adapter、authority、安全与 parity gate。
- CPO：本地/服务入口体验、错误解释和 profile 默认策略。
- CAO：公司级协议归属与项目 published-summary 治理。
