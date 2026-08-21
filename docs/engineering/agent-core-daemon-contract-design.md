# agent-core 进件合同设计稿：daemon 骨架／会话存储／多 agent 注册表／上下文聚合（TMV-P1-7，2026-08-22）

分身：CTO 小狄（TMV-P1-7）｜性质：**设计稿，非实施**——本稿=期 1「agent-core 合同设计」批交付物（R6:227），全部实现批归期 4（CEO 决策③批 4 期框架；R6 §五期 4，会话管理线可整体缓做 R6:86）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/agent-core-daemon-contract-design.md
- syncMode: source-only
- lastSyncedAt: 2026-08-22

## 〇、定位与读法

**目标**：把 R4 §3.2 五项进件裁决（R4:149-155）落成可评审的接口级合同，使期 4 实现批开工时零再设计。命名按 R5 叙事面即刻原则用新名：TriRLC（原 TriLC）、TriRMC（新建服务域主控，种子=路径 B 资产 R4:165-169）、TriMMC（收窄后元虚拟主控）。

**输入**：R2-trilc-agentcore-inventory（缺口清单）、R4-architecture-analysis（§3.2 裁决表／§五可见性／§七安全表）、R6-workload-phasing（§〇.5 owner 约束／1.4 会话管理线／风险 15）、R8-scenario2-design（§二 reconnect）、trilc-trimc-runtime-parity V1.1。本篇另做两项补核【实证】：TriLC/src/session-store/types.ts 与 store.ts（种子 API 面，§二）。

**读法约定**：TypeScript 接口为草案形态，不要求可编译、不要求最终命名；每节末标依据行号。【实证】=文件可查；【推断】=设计判断。

**落点（实现期）**：`TriCompany/packages/agent-core/src/` 增四模块——`daemon/`（骨架）、`session/`（合同+conformance kit）、`registry/`（内存实现）、`context-aggregation/`（引擎）。共享包改动走独立变更通道（r1-2 纪律：不就地改共享包，R6:86）。

## 一、daemon 骨架合同

### 1.1 抽象边界（进 / 不进）

R4:151 裁决「骨架进 agent-core（路由注册、SSE 流、生命周期、鉴权中间件位），绑定/部署配置留端」。展开为进出清单：

| 进 agent-core 骨架 | 留端 |
| --- | --- |
| 路由表注册与分发（替代两仓手写 if-链：TriLC 约 50 条 R2:23／TriMC 691 行 app.ts R2 §一） | node:http server 创建、host/port 绑定（TriRLC 回环 R4:246／TriRMC 收环或内网 R4:245） |
| SSE 流生命周期（open/event/keepalive/close/清理） | 部署形态（schtasks 守护 vs systemd/compose/k8s，parity §4 Runtime 进程行） |
| 中间件管线与鉴权中间件位（§1.3） | 路由 handler 业务体（init 链/staffing/cron 等全留端） |
| 会话广播器＋会话级单写者锁（运行时协调原语，§1.4） | 部署侧 probe/资源画像（k8s manifests 留 TriRMC） |
| 优雅停机序列（停收新连接→排空 SSE→关存储） | observability 后端 |

判断依据：parity §4 差异面表——进程形态与触发器是端差异，HTTP/SSE 骨架不在差异面内；两仓 app.ts 重复是 parity 最大面（R4:151）。

### 1.2 接口草案

```ts
interface DaemonRequest {
  method: string; url: string;
  params: Record<string, string>;     // '/sessions/:id/stream' 的路径参数
  query: URLSearchParams;
  body: unknown;                      // 骨架负责读取解析
  auth: AuthContext;                  // 鉴权中间件产物（§1.3）
}

interface DaemonResponse {
  status(code: number): DaemonResponse;
  json(value: unknown): Promise<void>;
  sse(): SseStream;                   // 一次性升级为 SSE 流
}

interface SseStream {
  eventId(seq: number): SseStream;            // SSE id: = 消息 seq（§4.2 底座）
  event(name: string, data: unknown): Promise<void>;   // 具名事件（现六事件形态沿用 R2:44）
  comment(text: string): Promise<void>;       // keepalive
  lastEventId(): string | null;               // 客户端重连游标（SSE 原生 header）
  close(): void;
  onClose(cb: () => void): void;              // 连接清理挂点
}

interface RouteDef {
  method: 'GET' | 'POST' | 'DELETE' | 'PUT';
  path: string;                              // 冒号参数形态
  auth: AuthPolicy;                          // 鉴权中间件位（§1.3）
  handler: (req: DaemonRequest, res: DaemonResponse) => Promise<void>;
}

interface Middleware {
  (req: DaemonRequest, res: DaemonResponse, next: () => Promise<void>): Promise<void>;
}

interface DaemonApp {
  use(mw: Middleware): void;                 // 全局中间件（日志/错误恢复/鉴权）
  route(def: RouteDef): void;                // 单条注册
  routes(defs: RouteDef[]): void;            // 批量注册（strangler 分片迁移用，§1.5）
  listen(opts: { host: string; port: number }): Promise<void>;
  shutdown(timeoutMs: number): Promise<void>; // 优雅停机序列
}
```

### 1.3 鉴权中间件位（必选件）

R4:249「agent-core daemon 骨架的鉴权中间件位为必选件」。现状两仓零鉴权（R2:23/R2:56）——骨架把鉴权从「安全模型=回环绑定」升级为路由级声明：

```ts
type AuthPolicy =
  | 'none'                                   // /healthz 等探针面
  | 'loopback'                               // TriRLC 主形态：回环绑定即边界（现状语义保留）
  | 'token:read'                             // 只读投影面（TriRMC 独立只读 token，R4:245）
  | 'token:write';                           // 写面与 bridge push 面（心跳/镜像/投影 push 共享 secret，R4:249）

interface AuthContext {
  policy: AuthPolicy;
  principal: string;                         // 客户端身份声明（takeover 用，R8 缺口 5）
}
```

端注入 token 校验函数（`use(authMiddleware({ verify }))`）；agent-core 只定管线位与策略枚举，不定 token 生成与轮换（部署面留端）。

### 1.4 会话广播器与单写者锁

reconnect 设计的两个运行时原语归骨架层（R8:119「reconnect 语义归 daemon 骨架层与存储 repository 合同」）：

```ts
interface SessionBroadcaster {
  publish(sessionId: string, ev: { name: string; seq: number; data: unknown }): void; // 多读者广播（R8 缺口 3）
  subscribe(sessionId: string, stream: SseStream): () => void;                       // 返回退订函数
}

interface SessionWriteLock {
  acquire(sessionId: string, holder: AuthContext['principal']): Promise<
    { ok: true; tookOverFrom: string | null } | { ok: false; reason: 'conflict' }>;
  release(sessionId: string, holder: string): void;   // 抢占式 takeover：后连者得锁，被顶替方收通知（R8:118）
  currentHolder(sessionId: string): string | null;
}
```

**验收线（继承 R8 风险 3）**：单写者锁以「现役 TriPilot 单客户端零回归」为验收——首持锁者无感知，锁仅在第二写入者出现时生效。

### 1.5 防大爆炸策略（R6 风险 15）

合同先行＋单端试点＋conformance suite 再推第二端（R6:213）。具体形态=**strangler 分片**：骨架与旧 app.ts 并存，`routes(defs)` 按片迁移（探针片→会话流片→业务片），未迁移路由仍走旧 if-链；每片过 E2E 矩阵回归（28 条 A 级脚本，R6:196）后才迁下一片。禁止「一步抽象 4387 行」。

**依据**：R4:151；R6:81（骨架批构成）、R6:213（风险 15）；R2:8/23/44。

## 二、会话存储合同

### 2.1 种子事实（本篇补核）

TriLC session-store 为本地 adapter 种子（R4:152）。补核其 API 面【实证，TriLC/src/session-store/】：

- schema v2：`sessions` + `session_messages`，`PRAGMA user_version` 逐版迁移机制在（store.ts:27-93）；cloud sync 字段（title/sync_status/last_synced_at/cloud_session_id）已备（types.ts:22-26）。
- **`session_messages.seq` 已存在且为 per-session 单调**（types.ts:32 注释 `monotonic within session`；DDL store.ts:45 + 索引 `(session_id, seq)` store.ts:57）。**这直接关闭 R8 缺口 2（「单调 seq 是否存在未核」R8:106）**；R8 缺口 1（SSE Last-Event-ID 重放是否已实现）仍待核，归 reconnect 批前探查（R8:232）。
- 种子方法面（store.ts:126-321）：createSession / getSession / updateSessionStatus / listSessions（status+limit+offset 过滤）/ saveMessages（事务内批量、seq=existingCount+i+1 分配 store.ts:201-215）/ getMessages / findInterruptedSessions / getSessionSummary / expireOldSessions / updateSyncStatus / markPendingSync / getPendingSyncSessions / getSessionByCloudId。
- 种子缺口（对合同而言）：无 `getMessagesSince` 重放窗口查询；无 owner 维度；无写权威元数据（parity §5 四字段）。

### 2.2 repository 接口草案

```ts
interface OwnerScope { kind: 'company' | 'tenant'; ownerId: string; }   // 今天仅 {kind:'company', ownerId:'tricompany'}，见 §五

interface SessionRecord {
  id: string; owner: OwnerScope;
  status: 'active' | 'completed' | 'interrupted' | 'error' | 'expired';
  model: string; title?: string; messageCount: number;
  createdAt: string; updatedAt: string; closedAt: string | null;
  homeDomain: 'local' | 'service';       // ─ parity §5 写权威四字段
  writeAuthority: string;                //   'trirlc:<node-id>' | 'trirmc:<cluster-id>'
  authorityEpoch: number;                //   旧 epoch/非 authority 写入必须拒绝（parity §5）
  version: number;                       // ┘
}

interface SessionMessage {
  sessionId: string; seq: number;        // per-session 单调（种子已有）
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string | null; toolCalls?: unknown | null;
  toolCallId?: string | null; reasoningContent?: string | null;
  createdAt: string;
}

interface SessionRepository {
  createSession(cmd: { id: string; owner: OwnerScope; model: string;
    systemPrompt?: string; cwd?: string; title?: string;
    homeDomain: SessionRecord['homeDomain']; writeAuthority: string }): Promise<SessionRecord>;
  getSession(owner: OwnerScope, id: string): Promise<SessionRecord | null>;
  listSessions(owner: OwnerScope, filter?: { status?; limit?; offset? }): Promise<SessionRecord[]>;
  appendMessages(sessionId: string, msgs: MessageInput[]):
    Promise<{ fromSeq: number; toSeq: number }>;        // seq 分配归 adapter：per-session 事务内单调无洞
  getMessages(sessionId: string): Promise<SessionMessage[]>;
  getMessagesSince(sessionId: string, afterSeq: number, opts?: { limit?: number }):
    Promise<SessionMessage[]>;                          // 重放窗口：reconnect/投影 push/recoverSession 三面共用（R8:123）
  currentSeq(sessionId: string): Promise<number>;       // 游标校验/重连握手
  updateSessionStatus(sessionId: string, status: SessionRecord['status']): Promise<void>;
  findInterrupted(owner: OwnerScope): Promise<SessionRecord[]>;
  markProjectionPushed(sessionId: string, remoteId?: string): Promise<void>;   // 投影 push 发送侧记账
  pendingProjectionPush(owner: OwnerScope, limit?: number): Promise<SessionRecord[]>;
}
```

`systemPrompt`/`cwd` 从种子 record 字段降为 create 参数（端自行决定是否另存）——合同只约定读写面，不锁存储列。【推断】

### 2.3 conformance suite 约定

suite 以测试套件工厂形态随合同发布（`runSessionRepositoryConformance(makeRepo)`），两端测试各自 import 跑自己的 adapter（parity §7.4「SQLite/PostgreSQL 通过同一 repository conformance suite」）。必测断言：

1. **seq 无洞单调**：任意批量子集追加后 seq 连续递增，无重复无空洞（种子行为 store.ts:201-215 为基准）。
2. **重放窗口精确**：`getMessagesSince(s, n)` 恰返回 `> n` 且按 seq 升序；`limit` 截断可续拉。
3. **并发写序列化**：两个写者交错 append 不产生重复 seq（SQLite WAL 单写天然满足；PG 用 `(session_id, seq)` 唯一约束+重试）——注意：会话级单写者锁在骨架层（§1.4），本断言是 repository 的兜底护栏，两层各守一半。
4. **owner 隔离**：两个 OwnerScope 同构数据互不可见（多租户种子的回归线，§五）。
5. **中断检测语义**：active 无 close 事件 → findInterrupted 命中（种子注释行为 store.ts:11）。
6. **写权威拒绝**：旧 authorityEpoch / 低 version / 非 writeAuthority 的状态更新被拒绝（parity §5）。
7. **迁移兼容**：schema v2 存量库升 v3（加 owner/权威字段）不丢数据、`user_version` 逐版走（机制已在 store.ts:83-93）。
8. **幂等重放**：同一批消息重复 append（同幂等键）不产生重复副作用（parity §7.6 精神）。

### 2.4 实现留端

SQLite adapter=TriRLC session-store 包装（增量：getMessagesSince 查询、owner/权威四列、schema v3 迁移）；PG adapter=TriRMC 新写（conformance 全过为验收）。expire/reap 策略（现 72h store.ts:279-288）与 cron 联动留端。**依据**：R4:152；parity §4/§5/§7.4；R8:106/123；本篇补核 store.ts。

## 三、多 agent 注册表合同

### 3.1 边界：contracts resolver 与 runtime registry

R4:154 裁决「合同＋内存实现进，持久化留端」。两层分界：

- **contracts resolver（已有，不动）**：`loadContractV3` 加载文件态 JD 合同（AgentContractV3，r13 收敛入口 R2 §二）——岗位定义的静态真源，随 git 五维同步流转（R2 §五）。
- **runtime registry（本合同新增）**：运行态实例注册表——谁在跑、在哪跑、什么状态。**只存 contractRef 指针不内嵌 JD 细节**，避免与文件态真源形成双源。

### 3.2 接口草案与内存实现约定

```ts
interface AgentRegistryEntry {
  agentId: string;                                   // 员工名或分身实例 id
  owner: OwnerScope;
  contractRef: { contractId: string; version: string };  // 指向 loadContractV3 产物
  kind: 'employee' | 'builtin' | 'clone-instance';
  placement?: 'mainControllerOnly' | 'preferServer' | 'preferLocal' | 'either';  // R4:187 四值
  status: 'active' | 'pending-cho' | 'candidate' | 'retired';  // 与 staffing roster 三态对齐（R4:181）
  lastSeenAt?: string;
  metadata: Record<string, unknown>;                 // displayName/tools/decisionRights 摘要等展示字段
}

interface AgentRegistry {
  register(entry: AgentRegistryEntry): void;
  unregister(owner: OwnerScope, agentId: string): void;
  get(owner: OwnerScope, agentId: string): AgentRegistryEntry | null;
  list(owner: OwnerScope, filter?: { kind?; status? }): AgentRegistryEntry[];
  snapshot(owner: OwnerScope): AgentRegistryEntry[];  // 只读深拷贝——供投影/观测，不构成持久化
}
```

内存实现约定：`Map` 以 `(ownerId, agentId)` 复合键；进程内生命周期（重启即空，由端自行重灌——TriRLC 从合同文件+心跳重建，TriRMC 同构）；registry 不做持久化、不做 roster 门禁决策（isRoleActive 三处门禁留 staffing 层，R4:181——registry 只供状态查询，不成为第二门禁真源）。**依据**：R4:154/181/187；R2 §二（contracts/ 模块）。

## 四、上下文聚合引擎＋源 adapter 合同

### 4.1 从注入类型到聚合引擎

现状：agent-core `ContextSources` 仅注入接口类型（R2:39），TriMC context-builder 是单 agent 上下文装配。R4:153 裁决「引擎进 agent-core（多源枚举、统一 schema、过滤分页），源 adapter 留端」：

```ts
interface ContextItem {
  kind: 'message' | 'roster-entry' | 'task-summary';
  sourceId: string;                      // 'local-repo' | 'trirmc-projection' | 'trimmc-bridge'
  owner: OwnerScope;
  sessionId?: string;
  seq?: number;                          // message 类游标=会话 seq（§4.2）
  payload: unknown;                      // 统一 schema 后的消息/名册/摘要
  occurredAt: string;
}

interface ContextSource {
  id: string;
  kind: 'session-store' | 'projection-api' | 'roster-bridge';
  capabilities: { messageLevel: boolean; liveStream: boolean };
  list(owner: OwnerScope, q: { filter?; cursor?; limit? }): Promise<ContextItem[]>;
  fetch(owner: OwnerScope, sessionId: string, opts?: { afterSeq?; limit? }): Promise<ContextItem[]>;
}

interface ContextAggregator {
  registerSource(source: ContextSource): void;
  query(owner: OwnerScope, q: { kinds?; sessionIds?; cursor?; limit? }): Promise<{ items: ContextItem[]; nextCursor?: string }>;
}
```

**能力位即边界线**：元虚拟源（trimmc-bridge，经 bridge-1 list）`messageLevel:false`——名册/摘要级承诺、正文级不承诺（R4:217 可见性分级表，问题④/⑤ 边界）；聚合引擎按 capability 降级，不向元虚拟源发正文级查询。**依据**：R4:153/217；R2:39。

### 4.2 与 R8 seq 底座的共享关系

一个序号底座喂三个能力面（R8:123）：reconnect 重放游标（R8:115-117）、投影 push（R4 §五）、recoverSession（R2:44）。本合同把它扩成四面——**聚合引擎 message 类分页游标同样用会话 seq**：`ContextSource.fetch(afterSeq)` 本地实现=repository `getMessagesSince`（§2.2），远端实现=TriRMC 投影 API 同语义端点。seq 已在种子 schema 存在（§2.1 补核），故四面共用零新增存储语义，只新增查询与 SSE `id:` 写入。**依据**：R8:113-123；R4:202-208。

### 4.3 源 adapter 留端清单

TriRLC：local-repo 源（包 repository）＋trirmc-projection 源（HTTP pull 投影 API）＋trimmc-bridge 源（bridge-1 list 代理）；TriRMC：自有 PG 源＋接收的投影数据源。引擎不感知 HTTP——远端源的 fetch 实现是端的 outbound client。**依据**：R4:207（TriPilot 不直连公网单一出口原则）；R6:106（薄代理先行不等聚合引擎——引擎归期 4 不阻塞可见性线）。

## 五、owner 维度贯穿（R6 §〇.5 约束）

会话=一等调度与记账单元、租户无全局单例（R6:25-27）。落地方式：

1. **`OwnerScope` 是所有合同的第一参数**：repository/registry/aggregator 的每个读写面都显式携带（§2.2/§3.2/§4.1 草案已体现）；无任何「默认 owner」便捷重载——多租户是扩展不是重写的前提就在签名里。
2. **存储落列**：SQLite schema v3 增 `owner_kind`/`owner_id` 两列（迁移断言 §2.3-7）；PG adapter 同列。registry 复合键含 ownerId。
3. **禁全局单例会话状态**：daemon 层不持有模块级会话 map；广播器/锁（§1.4）以 `(owner, sessionId)` 为键；一切会话态访问经 owner 域隔离的 repository。
4. **投影与记账同口径**：投影 push payload 携带 ownerScope；FADE 评分段 per-owner 记账口径在合同层预留（图 3-2 步 4-6 种子，R6:27）。

今天恒为 `{kind:'company', ownerId:'tricompany'}`——价值不在当下取值，在「换取值不动结构」。**依据**：R6:25-27。

## 六、期 4 adoption 路线与验收门

R6:153 已选边：TriRMC 期 2 先用现骨架落座，骨架进件归期 4 渐进 adoption。顺序建议：

| 步 | 内容 | 试点端 | 验收门 |
| --- | --- | --- | --- |
| 1 | 存储合同＋SQLite adapter 包装（种子加 getMessagesSince/owner/权威列，schema v3） | TriRLC | conformance 1-8 绿（SQLite）；现有 session-store 测试零回归；r2x E2E 会话面过 |
| 2 | PG adapter 新写 | TriRMC | 同一 conformance 全绿——parity §7.4 首次在存储面成立 |
| 3 | 注册表合同＋内存实现 | 双端同批 | 两端 listAgents 经 registry 出（TriPilot 行为零变化）；roster 门禁仍走 staffing（不旁路） |
| 4 | daemon 骨架＋鉴权中间件位 | **TriRMC（试点端）** | 全路由上骨架；周平面链过一个完整周日 23:00 周期；回滚演练（旧镜像重部署）在案 |
| 5 | 骨架 adoption 第二端 | TriRLC | strangler 分片迁移，每片过 E2E 矩阵（28 条 R6:196）＋TriPilot smoke |
| 6 | 聚合引擎＋两端源 adapter | 双端 | 聚合查询与直接 recoverSession 结果一致（同数据双路径对拍）；元虚拟源无正文级泄漏 |

**试点端选 TriRMC 的理由**：HTTP 面最小（691 行 vs 4387 行）；PG adapter 本就是净新代码，合同先行零浪费（否则=第二套手写层，违 parity §1）；周平面 cron 自然触发即运营验收门；服务器侧重启回滚=镜像回退，无装机存量回归。TriRLC 作第二端：面最大＋r20 装机存量＋TriPilot 耦合，让最大回归面吃 conformance 已固化后的成熟合同。排序另一收益：步 1-2 存储先行，使 reconnect 线（R8:218，3-4 批）可与之并行复用 seq/重放底座。

每步独立成批走共享包变更通道（R6:86）；任何一步验收不过即停，不留半迁移态（R6 风险 11 半迁移教训同族）。**依据**：R6:77-87/153/196/213；parity §1/§7.4；R8:218。

## 七、风险与观察项

| # | 风险/观察项 | 依据 | 处置 |
| --- | --- | --- | --- |
| 1 | SSE 现实现是否已带 Last-Event-ID 重放仍未核（seq 已核闭，R8 缺口 1 留存） | §2.1；R8:106/232 | 归 P1-8 schema 核对专项＋reconnect 批前探查（半日） |
| 2 | 抽象跨度：骨架接口在 4387 行 richest 面上可能再变形 | R6 风险 15 | 试点选小面（TriRMC）先行；第二端 strangler 分片容许合同小修订，修订走共享包变更通道 |
| 3 | 单写者锁对现役 TriPilot 链路回归 | R8 风险 3 | 验收线=单客户端零回归（§1.4） |
| 4 | schema v3 迁移碰装机存量（r20 现役库） | store.ts:83-93 机制在 | conformance 断言 7＋装机迁移独立成批实测（R6 风险 11 同族） |
| 5 | registry 与 staffing roster 双真源化 | §3.2 | registry 只查询不门禁——staging 层 isRoleActive 三处门禁不动（R4:181） |
| 6 | 本稿接口为草案形态，期 4 开工前需一次合同定稿评审 | §〇 | 期 4 首批前置：本稿评审＋按届时 R9-R11 收口结论修订（元虚拟可见性边界若 CEO 改口，§4.1 capability 位随之） |

## 八、使用依据

- 同目录树（2026-W34/trees/tmv-minimal-restructure-analysis/）：R2-trilc-agentcore-inventory.md（:8 app.ts 行数／:13 session-store／:23 路由与无鉴权／:39 缺口五项／:44 能力面／§五五维同步）；R4-architecture-analysis.md（:149-155 §3.2 裁决表／:153 聚合／:154 注册表／:165-169 §3.3／:181-190 placement 与 roster／:202-221 §五三步与可见性分级／:244-249 §七安全表）；R6-workload-phasing.md（:25-27 §〇.5 owner／:77-87 1.4 会话管理线／:86 可缓做／:153 排期权衡／:196 E2E 矩阵／:213 风险 15／§五期次）；R8-scenario2-design.md（:101-110 缺口表／:113-123 reconnect 与底座统一／:218 批数／:232 风险 1-2）
- TriCompany/docs/engineering/trilc-trimc-runtime-parity.md V1.1（§1 禁复制重写／§3 共享面／§4 差异面 adapter／§5 写权威／§6 能力同步节律／§7 parity gate）
- 本篇补核实证：D:/Code/ai/TriLC/src/session-store/types.ts（:12-39 record/seq 定义）、store.ts（:27-93 DDL 与迁移、:126-321 方法面、:201-215 seq 分配事务）——2026-08-22 读
- 置信度总标注：现状事实【实证】（引行号＋补核）；接口形态与试点端选择为【推断】（设计判断，期 4 开工前可再裁）；本稿不改变任何现役运行时行为
