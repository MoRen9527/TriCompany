# 双向心跳契约 v1.0 — TriLC ↔ TriMC 生产双跑

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/heartbeat-dualrun-contract.md
- syncMode: source-only
- lastSyncedAt: 2026-08-13T22:30:00+08:00
- 作者: CTO 小狄（r14-production-dualrun / r14-1）
- 关联: `trilc-trimc-runtime-parity.md` §5（写权威）、`trilc-capability-checklist.md` 2.4/2.5、CTO-008-M §3.5

## 一、背景与目标

M3 生产双跑：TriLC（本地执行面）与 TriMC（服务器舰队面）互为 fallback。双向心跳是 fallback 契约的判定基础——任何一侧必须能独立判定对方可达性，并在恢复后对齐状态。

**目标**：定义双面统一的 interval / timeout / degraded 判定 / 恢复对齐语义，消除"只有 TriLC 知道自己降级"的单向盲区。

## 二、现状事实（2026-08-13 实测盘点）

### 2.1 TriLC 侧（已具备，2.5 已验）

`src/server/app.ts` ConnectionManager：

| 参数 | 值 | 说明 |
| --- | --- | --- |
| healthCheckIntervalMs | 10_000 | 正常心跳间隔 10s |
| failThreshold | 3 | connected 下连续 3 次失败 → degraded |
| recoverThreshold | 2 | degraded 下连续 2 次成功 → connected |
| DEGRADED_BACKOFF_MS | 5 min | degraded 超 5 分钟 → 慢心跳 |
| DEGRADED_SLOW_INTERVAL_MS | 60_000 | 慢心跳间隔 60s |
| 初始状态 | degraded | 未验证前按降级处理 |
| local 模式 | state=local | TRIMC_BASE_URL 未配置时 |

- 心跳端：`POST /internal/v1/heartbeat`，payload `{nodeId, state, queueSize, uptimeSeconds, agentCoreVersion}`。
- 恢复对齐：恢复后 `_performReplay()` 重放 pending 事件 + TaskMirrorPusher.onReconnected() 全量推送（30s mirror 心跳与连接心跳错开 15s）。
- 持久化：persistState 落盘 stateFile（重启不丢状态）。

### 2.2 TriMC 侧（盲区，本契约要补）

- `POST /internal/v1/heartbeat`（src/server/app.ts:471-503）：**回显式应答** `{ok, serverTime, nodeId, commands: []}`——不登记节点状态、不更新任何 lastSeen。
- `mirror/store.ts` `markNodeUnknown(nodeId)`：存在但**零调用方**（注释"由 heartbeat handler 在检测到节点超时时调用"，该 handler 未实现）。
- task 维度 lastSeenAt 仅由 `/internal/v1/tasks/mirror` push 被动更新。
- **结论**：TriMC 侧无节点级可达性判定。TriLC 降级/恢复时，TriMC 不知情；节点失联时 TriMC 无法把任务标 unknown。双向契约当前是单向的。

### 2.3 联通面

- TriMC 服务器监听 `*:8710`（docker/.env TRIMC_PORT=8710，实测 node 监听中）。
- TriLC 默认 `TRIMC_BASE_URL=http://127.0.0.1:8710`——连服务器需显式设置环境变量 + 服务器防火墙放行 8710。
- REQ-006（heartbeat tier 行为）为 TriMC 工具 tier 体系变更（08-05），与本契约的通道判定正交，不冲突。

## 三、契约 v1.0 定义

### 3.1 双面状态机

| 侧 | 状态 | 转移 | 判定参数 |
| --- | --- | --- | --- |
| TriLC 连接视图 | local → connected → degraded → connected | 3 败降级 / 2 成恢复 | failThreshold=3, recoverThreshold=2 |
| TriMC 节点视图（新增） | known → unknown → known | 心跳超时标 unknown / 心跳回归标 known | stale 阈值见 3.2 |

### 3.2 统一参数表

| 参数 | 值 | 双面语义 |
| --- | --- | --- |
| heartbeatIntervalMs | 10_000 | TriLC 发送节律；TriMC 判定的基准 |
| nodeStaleThresholdMs | 30_000 | TriMC：连续 3×interval 无心跳 → markNodeUnknown（与 failThreshold=3 对称） |
| nodeStaleThresholdDegradedMs | 180_000 | TriMC：心跳 state=degraded 的节点用宽松阈值（覆盖 60s 慢心跳 ×3，防误判） |
| nodeRecoverThreshold | 2 | TriMC：连续 2 次心跳回归 → known（与 recoverThreshold=2 对称） |
| degradedBackoffMs | 300_000 | TriLC：degraded 超 5min → 60s 慢心跳（现有，保留） |
| heartbeatTimeoutMs | 5_000 | 单次心跳 HTTP timeout（与 mirror postMirror 一致） |

### 3.3 心跳通道（复用现有端点，接线升级）

- 请求（TriLC → TriMC，不变）：`POST /internal/v1/heartbeat`，payload 同上。
- 响应（升级）：`{ok, serverTime, nodeId, commands: []}`——commands 为预留命令下发通道，M3 首批不启用（记扩展点）。
- **TriMC 侧接线（本契约新增）**：收到合法心跳 → 登记 `nodeHeartbeat{nodeId, lastSeenAt, state}` → 若节点此前 unknown 且连续 2 次心跳 → known（并触发 unknown 任务回流标记，见 3.4）。
- 定时扫描：每 10s 扫节点心跳表，超 stale 阈值 → `markNodeUnknown(nodeId)`（接线现有零调用方法）。

### 3.4 恢复对齐（双向）

- TriLC → TriMC：恢复后 replay pending 事件 + mirror 全量推送（现有机制，保留）。
- TriMC → TriLC（新增）：节点 known 回归后，该节点 unknown 状态任务回流——`markNodeUnknown` 的反向 `markNodeRecovered(nodeId)` 将 unknown 任务标记回原状态或待重放；M3 首批可简化为"unknown 任务在节点回归后由 TriLC 端 replay 覆盖"（TriLC 恢复 replay 已含全量事件），TriMC 侧回流标记为可选增强。

### 3.5 degraded 判定统一语义（一句话）

"**心跳超时 3 次或 3×interval 无心跳 → degraded/unknown；连续 2 次成功或心跳回归 → 恢复；恢复后双方各自对齐状态（replay / 回流），恢复动作幂等。**"双面参数对称（3/2），任一侧可独立判定对方不可达。

## 四、落地指引（r14-2 小全）

### 4.1 TriMC 侧改动（本契约核心，均在本地 TriMC 仓）

1. `src/mirror/store.ts`：新增节点心跳表（`nodeHeartbeats: Map<nodeId, {lastSeenAt, state}>`）+ `recordNodeHeartbeat()` + `markNodeRecovered()`（可选）。
2. `src/server/app.ts` heartbeat 端点：解析后调 `recordNodeHeartbeat()`；响应结构不变（向后兼容）。
3. 新增超时扫描：定时器（10s 或挂 cron）扫描心跳表 → 超阈值调 `markNodeUnknown()`（按 3.2 双阈值，state=degraded 节点用 180s）。
4. 单测：心跳登记、30s 标 unknown、180s 宽松、2 次回归 known、commands 字段回显。

### 4.2 TriLC 侧（核对即可，预期零改动）

现有 ConnectionManager 参数已与契约一致（10s/3/2/5min/60s）。核对项：① 心跳 payload 已带 state（TriMC 双阈值依赖）——已带 ✅；② 恢复 replay 幂等 ✅（2.5 已验）。

### 4.3 测试门禁

- TriMC 新增单测全绿 + 全量回归（455 基线，预存失败沿用 r7-2 归因）。
- TriLC 回归 14/14 实载 + 2.5 degraded 相关测试不退化。

## 五、服务器面就绪清单（r14-1 盘点）

### 5.1 事实

| 项 | 状态 |
| --- | --- |
| ssh sg-ecs-server | 可达（BatchMode OK） |
| git remote sg-server | 可达（ls-remote OK，HEAD 182de4d） |
| TriMC 服务 | systemd trimc.service enabled + active（08-11 起，1d12h） |
| 部署形态 | **M1 dev 直跑**：/srv/fleet/TriMC 源码 + `npx tsx src/index.ts`（日志 /tmp/trimc-run.log），非生产形态（无 dist 构建、无版本化） |
| 监听 | `*:8710`（node，与 docker/.env TRIMC_PORT 一致） |
| 服务器 git | 落后本地 3 commits（本地领先 3） |
| /srv/fleet/ | 六仓镜像齐（TriCode/TriCompany/TriLC/TriMC/TriMetaverse/TriModel） |
| k8s manifests | 本地仓 k8s/trimc/ 齐全，但服务器未用 k8s（以 systemd 为准） |

### 5.2 就绪项 vs 硬卡

**本树可做（r14-2 本地）**：TriMC 心跳接线代码 + 单测 + 本地全量回归。

**硬卡（blocked → CEO 一次执行）**：
1. push sg-server（git 写权限）
2. 服务器 git pull + tsx 服务重启（服务器操作权限）
3. 本地 TriLC `TRIMC_BASE_URL` 指向服务器 + 服务器防火墙放行 8710（联通面启用）
4. M3 生产形态改造（dist 构建 + 版本化部署替代 dev tsx 直跑）——本树不做，记 M3 后续里程碑动作
5. UAC 提权安装（r14-2 提权清单，CEO）

## 六、验收口径（r14-3 小柯可测）

1. 契约参数表与两端代码实读一致（10s/3/2/30s/180s/2）。
2. TriMC 心跳接线单测全绿：登记 → 30s 标 unknown → degraded 节点 180s 不误判 → 2 次回归 known。
3. `markNodeUnknown` 从零调用变为有调用方（grep 验证）。
4. 心跳响应结构向后兼容（TriLC 现有客户端无改动即对接）。
5. TriMC 全量回归无新增失败（预存失败沿用 r7-2 归因）。
6. TriLC 侧核对项两项（payload 带 state、replay 幂等）验证通过，零改动成立。
7. 服务器面清单事实与实测一致（ssh 可达 / systemd active / 8710 监听 / 服务器落后 3 commits）。
8. 硬卡清单完整登记 OP（push / 服务器操作 / 联通面 / 生产形态 / UAC 五项）。

## 七、决策记录

- 复用现有心跳端点，不新建通道（commands 字段留扩展点，首批不启用）。
- 双阈值设计：degraded 节点宽松阈值防慢心跳误判（与 TriLC 5min 退避配合）。
- markNodeRecovered 首批可选（TriLC replay 已覆盖状态对齐主路径）。
- 服务器生产形态改造不入本树（记 M3 里程碑动作）。
