# 会话同步 schema 漂移核对表（TMV-P1-8，2026-08-22）

分身：CTO 小狄（p1-68-placement-schema 批）｜性质：核对产出（规格/核对文档，非生产代码）｜R6 风险 17 指定本表为「投影 push 批的验收基线」（R6:215）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/session-sync-schema-alignment.md
- syncMode: source-only
- lastSyncedAt: 2026-08-22

## 〇、核对范围、方法与结论摘要

**对象**：会话云同步死代码的两端契约——发送面（TriLC/src/sync/：sync-engine.ts＋payload-builder.ts＋types.ts）vs 存储面（TriLC/src/session-store/：store.ts DDL/迁移＋types.ts schema v2）。两端从未接线（R2:53），接收端（`{trimcBaseUrl}/internal/v1/sessions/sync`）从未实现。本表核对「发送面承诺的 payload」vs「存储面实际持有的字段」，并据此给 TriRMC PG 接收端目标 schema 建议。

**方法**：全字段逐项实读源码（2026-08-22）；【实证】＝文件行号可查。漂移判定四档：对齐 / 有损 / 未发送（漂移）/ 设计使然不发送。

**结论摘要（技术判断）**：

1. **无阻断性类型冲突**——已发送字段上两端类型兼容；漂移形态是「存储有、发送无」的**字段缺口**（7 项）＋2 项有损变换，不是类型不匹配。激活改造是发送面增量，**session-store 侧零 schema 变更**。
2. **R8 §2.2 缺口 2 关闭**：session_messages **已有** per-session 单调 seq（store.ts:45/:57/:204-214、types.ts:32）——标复用；但 payload 未含 seq，需补发（漂移-6，§二）。
3. **横切风险：时间戳格式分裂**——created_at/updated_at 为 SQLite `datetime('now')` 格式（`YYYY-MM-DD HH:MM:SS`，无时区标记；store.ts:37-38/:100/:105），而 closed_at/last_synced_at（store.ts:158-160/:297）与 payload 的 syncedAt（payload-builder.ts:90）为 JS `toISOString` 格式（带 T/Z/毫秒）。session-store/types.ts:20-21 注释声称 ISO 8601 与实现不符。PG 侧若不归一，无时区标记字符串按 PG 会话时区解释，+8 环境偏移 8 小时。
4. **激活必备三缺口**：写权威元数据（R4:126 护栏）、owner 维度（R6 §〇.5:27）、截断指示（maxMessages 默认 5000 截断且取头弃尾，payload 无 truncated 标记）——当前 payload 均无（§三）。

## 一、会话级字段对齐表（sessions 表 12 字段 vs SyncRequestPayload.session）

缩写：pb＝TriLC/src/sync/payload-builder.ts；st＝TriLC/src/session-store/store.ts；st-types＝TriLC/src/session-store/types.ts。

| # | 存储字段（st） | 类型 | 发送字段（pb） | 两端现状 | 漂移判定 |
| --- | --- | --- | --- | --- | --- |
| 1 | sessions.id（:31） | TEXT PK | session.localSessionId（pb:83） | 透传；幂等键组成（types.ts:55-56） | 对齐（改名映射） |
| 2 | sessions.status（:32） | TEXT 枚举 active/completed/interrupted/error/expired（st-types:7） | session.status（pb:85） | 透传 | 对齐；接收端带同枚举 CHECK |
| 3 | sessions.title（:64，v2 增列，可空） | TEXT NULL | session.title（pb:84） | `?? ''` 空串强转 | **有损**：null→''，接收端无法区分「无标题/空标题」 |
| 4 | sessions.model（:33） | TEXT NOT NULL | —（未发送） | 存储有、发送无 | **漂移-1**：接收端不知会话模型 |
| 5 | sessions.system_prompt（:34） | TEXT NOT NULL | — | 同上 | **漂移-2**：上下文重建缺系统提示（体积大，分级见 §四） |
| 6 | sessions.cwd（:35） | TEXT NOT NULL | — | 同上 | **漂移-3**：缺工作区定位 |
| 7 | sessions.message_count（:36） | INTEGER NOT NULL | — | 同上 | **漂移-4**：截断时接收端不可知真实条数（truncated 指示也缺，§三 #7） |
| 8 | sessions.created_at（:37） | TEXT（datetime('now')） | session.createdAt（pb:86） | 透传 | 对齐＋**格式漂移**（§〇.3） |
| 9 | sessions.updated_at（:38/:105） | TEXT（datetime('now')） | session.updatedAt（pb:87） | 透传 | 对齐＋格式漂移（同上） |
| 10 | sessions.closed_at（:39；写入走 toISOString，st:158-160） | TEXT NULL | —（未发送） | 存储有、发送无 | **漂移-5**：终态时间戳丢失；同表两格式并存＝§〇.3 交叉证据 |
| 11 | sessions.sync_status（:65） | TEXT 默认 local | — | 本地状态机记账（sync-engine.ts:74-96 消费） | 设计使然不发送（本地态非投影数据） |
| 12 | sessions.last_synced_at（:66） | TEXT NULL | — | 同上 | 设计使然不发送 |
| 13 | sessions.cloud_session_id（:67） | TEXT NULL | —（回写方向：响应→本地，sync-engine.ts:123/:135） | 本地记账＋回写 | 设计使然不发送（反向字段） |

## 二、消息级字段对齐表（session_messages 9 字段 vs SyncMessagePayload）

| # | 存储字段（st） | 类型 | 发送字段（pb） | 两端现状 | 漂移判定 |
| --- | --- | --- | --- | --- | --- |
| 1 | session_messages.id（:43） | INTEGER AUTOINCREMENT | — | 全表 rowid，非 per-session | 设计使然不发送（不可移植；per-session 游标是 seq） |
| 2 | session_messages.seq（:45） | INTEGER NOT NULL | —（SyncMessageInput 即排除，pb:13-19） | 存储有、发送无 | **漂移-6（关键）**：R8 §2.2 缺口 2 答案＝存储端已有（§五），发送端需补 |
| 3 | session_messages.session_id（:44） | TEXT FK | —（归并到外层 session.localSessionId） | 结构归并 | 对齐（层级映射） |
| 4 | session_messages.role（:46） | TEXT user/assistant/system/tool | role（pb:44） | 透传 | 对齐 |
| 5 | session_messages.content（:47） | TEXT NULL | content（pb:45） | 透传 | 对齐 |
| 6 | session_messages.tool_calls（:48） | TEXT（JSON 串，OpenAI 形 {id, type, function{name, arguments}}；写入 st:196/:211） | toolCalls（pb:49-69，解析为 {toolName, input}） | 有损变换 | **有损**：丢 id/type；types.ts:75-80 声明的 output/durationMs 从未赋值（契约噪音，处置见 §四） |
| 7 | session_messages.tool_call_id（:49） | TEXT NULL | toolCallId（pb:71-73） | 透传 | 对齐 |
| 8 | session_messages.reasoning_content（:50） | TEXT NULL | —（未发送） | 存储有、发送无 | **漂移-7**：DeepSeek reasoning 兼容字段（st:13 注释）在投影中丢失 |
| 9 | session_messages.created_at（:51） | TEXT（datetime('now')） | timestamp（pb:46，改名） | 透传 | 对齐（改名）＋格式漂移（§〇.3） |

## 三、payload 顶层与激活必备缺口

| # | 项 | 现状 | 判定/建议 |
| --- | --- | --- | --- |
| 1 | nodeId（types.ts:58） | 发送面自有 | 保留——幂等键组成＋投影来源标识 |
| 2 | syncType: 'full'（types.ts:59） | Phase 1 仅全量 | 保留枚举；激活改造扩 'incremental'（基于 sinceSeq，依赖 §五 seq 补发） |
| 3 | syncedAt（pb:90，toISOString） | 发送面自有 | 保留；注意与 created_at 格式不一致（§〇.3） |
| 4 | 消息级 seq 游标 | 缺 | **激活必备**：messages[].seq＋增量 sinceSeq（增量 push＋行级去重判据） |
| 5 | 写权威元数据 | 缺 | **激活必备（R4:126 护栏）**：homeDomain/writeAuthority/authorityEpoch/version 随 payload 携带并落库——代码共享不等于运行时双活写入，本地 owned 会话在 TriRMC 侧是只读投影 |
| 6 | owner 维度 | 缺 | **激活必备（R6 §〇.5:27）**：会话归属主体（今天＝tricompany，明天＝租户）；禁全局单例会话状态 |
| 7 | 截断指示 | 缺（maxMessages 默认 5000，types.ts:37/:48；截断 slice 取头弃尾，pb:39-40） | 激活建议：payload 增 truncated/originalCount；投影语义下「取头弃尾」方向应反转或取消（投影要最新）——登记为激活改造批设计决策点 |
| 8 | 响应契约 | SyncSuccessResponse/409/503 已定义（types.ts:84-112） | 保留；409 幂等语义（sync-engine.ts:121-130）为 PG 接收端必抄工程模式（R4:87 参考实现裁决） |

## 四、TriRMC PG 接收端目标 schema 建议（投影 push 批验收基线）

依据：R6 1.3 bridge-3 ①（R6:73）；R6 风险 17「字段对齐表＝投影 push 批的验收基线」（R6:215）；R4:206「两端 schema 以 session-store v2 的 cloud sync 字段为起点」。

```sql
-- 投影会话主表（建议名 projected_sessions）
CREATE TABLE projected_sessions (
  id               TEXT PRIMARY KEY,      -- TriRMC 生成的 cloud session id
  node_id          TEXT NOT NULL,         -- 来源 TriRLC 节点
  local_session_id TEXT NOT NULL,         -- 来源 sessions.id
  owner            TEXT NOT NULL DEFAULT 'tricompany',  -- R6 §〇.5 owner 维度
  title            TEXT,                  -- 发送端 '' 建议归一为 NULL（§一 #3 处置）
  status           TEXT NOT NULL CHECK (status IN
                     ('active','completed','interrupted','error','expired')),
  model            TEXT,                  -- 漂移-1 补发后落库
  message_count    INTEGER,               -- 来源端真实条数（截断时≠落库条数）
  created_at       TIMESTAMPTZ NOT NULL,  -- 接收端统一归一（§〇.3 处置）
  updated_at       TIMESTAMPTZ NOT NULL,
  closed_at        TIMESTAMPTZ,           -- 漂移-5 补发后落库
  home_domain      TEXT NOT NULL,         -- 写权威元数据（R4:126）
  write_authority  TEXT NOT NULL,
  authority_epoch  INTEGER NOT NULL DEFAULT 1,
  version          INTEGER NOT NULL,      -- 投影版本，每次 push 递增
  last_synced_at   TIMESTAMPTZ,
  CONSTRAINT uq_projection_idempotent UNIQUE (node_id, local_session_id)  -- 409 幂等键
);

-- 投影消息表（建议名 projected_session_messages）
CREATE TABLE projected_session_messages (
  id                BIGSERIAL PRIMARY KEY,
  session_ref       TEXT NOT NULL REFERENCES projected_sessions(id) ON DELETE CASCADE,
  seq               INTEGER NOT NULL,     -- 来源 session_messages.seq（漂移-6 补发）
  role              TEXT NOT NULL CHECK (role IN ('user','assistant','system','tool')),
  content           TEXT,
  tool_calls        JSONB,                -- 建议保留 {toolName,input}＋原始 id/type
  tool_call_id      TEXT,
  reasoning_content TEXT,                 -- 漂移-7 补发后落库
  created_at        TIMESTAMPTZ NOT NULL,
  CONSTRAINT uq_projection_msg_seq UNIQUE (session_ref, seq)  -- 单调游标：增量/重放/去重三用
);
CREATE INDEX idx_proj_sessions_owner ON projected_sessions(owner, updated_at);
```

**验收基线条目**（投影 push 激活批 Definition of Done）：

1. 幂等：UNIQUE(node_id, local_session_id)＋重复 push 返回 409 existingCloudSessionId（沿用 sync-engine.ts:121-130 语义）。
2. 游标：UNIQUE(session_ref, seq)；增量 push 按 sinceSeq 推进；reconnect 重放（R8 §2.3）与 recoverSession 同底座（R8:123 一序号三面）。
3. 只读投影语义：接收端不接受 projected_* 外部写；写权威元数据四字段必填（R4:126）。
4. owner 必填、按 owner 域隔离查询（R6:27）。
5. 时间戳全部 TIMESTAMPTZ 归一（§〇.3 处置：接收端归一为强制，发送端格式修正为建议）。

**发送端补发清单**（激活批发送侧验收线。改动面收敛在 sync/ 模块：SyncMessageInput/SyncMessagePayload/buildSyncPayload——store.getMessages 已返回完整 SessionMessageRecord（含 seq/reasoningContent），存储侧零改动）：

| 级 | 字段 | 理由 |
| --- | --- | --- |
| P0 必补 | messages[].seq；写权威元数据四字段；owner；truncated 指示 | 游标/护栏/租户/完整性，门禁性 |
| P1 应补 | model；closed_at；reasoning_content；message_count | 会话语义完整性 |
| P2 可选 | system_prompt；cwd | 上下文重建完整度（system_prompt 体积大，截断策略随批设计） |
| 裁剪建议 | SyncMessagePayload.toolCalls.output/durationMs（声明未赋值，types.ts:78-79） | 契约噪音；tool 结果已由 role='tool' 行（content＋toolCallId）承载 |

## 五、单调 seq 缺口确认（R8 §2.2 缺口 2 关闭）

- **【实证】存在**：`session_messages.seq INTEGER NOT NULL`（st:45）；per-session 单调赋值＝saveMessages 事务内 `existingCount + i + 1`（st:204-214）；索引 idx_msgs_session(session_id, seq)（st:57）；st-types:32 注释明示 "monotonic within session"。
- **判定：标复用**——存储端已有，无需新增列；缺的是发送端 payload 补 seq（§二漂移-6）。
- **单调性边界**：当前写路径下 seq 稠密单调——无单条消息删除 API（删除仅整会话级联 deleteSession，st:325-328；expireOldSessions 只改 status，st:279-288）。若未来引入消息级删除/编辑，稠密性破坏，游标语义须重审（登记为变更热区）。
- **不可替代项**：id（AUTOINCREMENT rowid，st:43）是全表单调、非 per-session——不可作会话内游标。
- **三面共用**：reconnect SSE 重放游标（R8:116-123）／投影增量 push／recoverSession 消息重放——一个序号底座（R8:123）。

## 六、漂移处置建议与激活前置门（交付计划＋发布姿态）

1. **顺序**：本表（期 1 专项，R6:225 交付物「schema 漂移字段对齐表」）→ 发送端 P0 补发＋PG 接收端落库（期 2 投影 push 批，R6:237）——对齐 R6 §二硬依赖 6「死代码 schema 核对专项 → 投影 push 激活」（R6:141）。
2. **决策三分法**：投影 push 激活批在 P0 清单补齐前 **FREEZE**（漂移未收口＝接口未锁定）；本表自身为核对产出，APPROVE 落盘。
3. **风险与缓解**：最大风险＝时间戳格式分裂（§〇.3）——缓解＝接收端 TIMESTAMPTZ 强制归一＋集成测试覆盖两种输入格式；次风险＝存量 SQLite 历史会话首推全量（走既有 'full' syncType，无增量语义负债）。
4. **发布姿态**：投影 push 上线前必须满足验收基线 1-4（幂等键/游标/写权威/owner 四者缺一不放行）。

## 七、使用依据

- 源码实读（2026-08-22，全【实证】）：TriLC/src/sync/sync-engine.ts（:99-141 读取-构建-发送链、:121-130 409 幂等）；payload-builder.ts（:30-94 字段映射全集）；types.ts（:44-112 payload/响应契约；retry.ts 未逐行——重试面不涉字段漂移）；session-store/store.ts（:29-70 DDL＋v2 迁移、:97-124 写路径、:204-214 seq 赋值、:290-321 sync 记账、:325-328 级联删除）；session-store/types.ts（:7-47 schema v2 类型全集）。
- 分析树（2026-W34/tmv-minimal-restructure-analysis/）：R2:13/:17/:53（死代码现状）；R4:119（投影 push 裁决）、:126（写权威护栏）、:206（schema v2 cloud sync 字段为起点、漂移需核）、:221/:259（风险 3）；R6:27（owner 维度）、:73（bridge-3 ①）、:141（硬依赖 6）、:201（风险 3/8 处置）、:215（风险 17 验收基线）、:225/:237（期 1/期 2 交付物）；R8:106（缺口 2）、:116-123（游标与底座统一）。
- 协议：TriMetaverse/docs/execution/clone-dispatch-protocol.md（本批同期升 v0.3，§十 placement 规格）。
- 备注：R8:106 引「R6:69」指 bridge-3 ①，实测该行在 R6:73（表格行位差，指向不变）。
