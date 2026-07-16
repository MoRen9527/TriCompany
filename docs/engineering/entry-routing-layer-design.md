# 入口路由层工程技术方案 V1.0

**Author**: CTO 小狄
**Date**: 2026-07-14
**Status**: 初版
**Reference**: CTO-008（CPO-010 工程技术落地）
**Upstream**: `TriCompany/docs/registry/product-state.md` §§Iteration Strategy, Operational Safety Model

> **产品上游**：CPO-010 定义了入口路由层的产品架构（active_host flag、两种模式、自动回退、Write Master 锁、Shadow workspace、对比引擎）。
> **本文职责**：将产品架构翻译为可实施的工程技术方案——文件布局、协议规格、状态机、门禁和测试策略。

---

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/entry-routing-layer-design.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-07-14
- downstream consumers: TriMetaverse/.github/config/active-host.yaml、TriMC /health endpoint、Copilot-host agent 指令

---

## 1. 设计目标

为 Copilot-host → TriMC 双轨并行提供工程化路由基础设施：

1. **配置驱动切换**：一行 YAML 控制 Copilot-host agent 的 Native / Passthrough 行为
2. **自动容错**：TriMC 不可用时自动回退 Copilot-host，无人工等待
3. **写入安全**：任何时候有且仅有 1 个 Host 持有 TriMetaverse 仓库写入权（G8 防护）
4. **可观测**：Shadow 对比引擎产出量化一致率报告
5. **零侵入降级**：回退不依赖 TriMC 存活，Copilot-host 自给自足

---

## 2. 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│  TriMetaverse/.github/config/active-host.yaml                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  active_host: copilot | triMC                              │  │
│  │  write_master: copilot | triMC   (必须 ≡ active_host)      │  │
│  │  triMC_endpoint: http://localhost:8710                     │  │
│  │  fallback: { max_failures: 3, cooldown_minutes: 15 }       │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │  Copilot-host agent 启动时读取
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Copilot-host Agent（TriMetaverse/.github/agents/）              │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Native Mode  │    │ Passthrough  │    │ Fallback Engine  │   │
│  │ (直接处理)    │    │ Mode (转发)   │    │ (连续3次失败→切换) │   │
│  └──────┬───────┘    └──────┬───────┘    └────────┬─────────┘   │
│         │                   │                     │              │
│         │          ┌────────▼────────┐            │              │
│         │          │  Health Check   │◄───────────┘              │
│         │          │  GET /health    │                           │
│         │          └────────┬────────┘                           │
│         │                   │ OK                                 │
│         │          ┌────────▼────────┐                           │
│         │          │  TriMC Server   │                           │
│         │          │  :8710          │                           │
│         │          └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. active-host.yaml 规格

### 3.1 文件位置

```
TriMetaverse/.github/config/active-host.yaml
```

**选择理由**：
- `.github/config/` 是 Copilot-host 可直接读取的配置层，无需额外部署
- 不在 TriCompany 或 TriMC 内部——这是跨越两个 Host 的中央开关，应放在项目根
- Git 追踪，变更历史可审计

### 3.2 Schema

```yaml
# active-host.yaml — 入口路由中央开关
# 修改此文件 = 切换 Host 路由模式
# 必须与 write_master 字段保持一致；不一致 → G8 阻断

version: 1
active_host: copilot          # copilot | triMC
write_master: copilot         # copilot | triMC（必须 ≡ active_host）

triMC:
  endpoint: http://localhost:8710
  health_path: /health
  timeout_ms: 5000

fallback:
  max_consecutive_failures: 3
  cooldown_minutes: 15
  notification: explicit       # explicit — 显式通知用户含错误原因与建议动作

shadow:
  enabled: false               # true 时开启 Shadow 对比模式
  workspace_path: ../TriMC-shadow-workspace
  comparison:
    engine: diff-based         # diff-based — 基于文件 diff 的一致性对比
    consistency_threshold: 0.95
    sample_rounds: 100         # 连续 N 轮采样
```

### 3.3 字段约束

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `active_host` | enum | ✅ | `copilot` 或 `triMC` |
| `write_master` | enum | ✅ | 必须 ≡ `active_host` |
| `triMC.endpoint` | url | 当 `active_host: triMC` 时必填 | HTTP/HTTPS |
| `triMC.health_path` | string | 否 | 默认 `/health` |
| `triMC.timeout_ms` | int | 否 | 默认 5000，范围 [1000, 30000] |
| `fallback.max_consecutive_failures` | int | 否 | 默认 3，范围 [1, 10] |
| `fallback.cooldown_minutes` | int | 否 | 默认 15，范围 [5, 60] |
| `shadow.enabled` | bool | 否 | 默认 false |
| `shadow.workspace_path` | path | 当 `shadow.enabled: true` 时必填 | 相对于 TriMetaverse 根目录或绝对路径 |
| `shadow.comparison.consistency_threshold` | float | 否 | 默认 0.95，范围 [0.5, 1.0] |

---

## 4. 两种运行模式

### 4.1 Native Mode（active_host: copilot）

```
用户输入 → Copilot-host agent → 直接处理（read/write/edit/shell/glob） → 返回结果
```

- Agent 指令中不包含转发逻辑
- 所有工具调用直接操作 TriMetaverse 仓库
- 等同于当前正常运行模式

### 4.2 Passthrough Mode（active_host: triMC）

```
用户输入 → Copilot-host agent → HTTP POST /v1/messages → TriMC server → agent-loop → 返回结果
```

**转发协议**：

```typescript
// Copilot-host → TriMC 请求体
interface PassthroughRequest {
  user_message: string;
  context: {
    working_directory: string;
    session_id: string;
  };
  mode: "passthrough";
}

// TriMC → Copilot-host 响应体
interface PassthroughResponse {
  result: string;           // agent 最终文本输出
  tool_calls: ToolCall[];   // 工具调用记录（审计用）
  tokens_used: number;
  duration_ms: number;
}
```

**Copilot-host agent 在 Passthrough 模式下的行为**：
1. 读取 `active-host.yaml`，确认 `active_host: triMC`
2. 将用户输入封装为 `PassthroughRequest`
3. HTTP POST 到 `triMC.endpoint + "/v1/messages"`
4. 将 TriMC 返回的 `result` 直接呈现给用户
5. 不自行执行任何工具调用

---

## 5. Health Check 协议

### 5.1 端点规格

```
GET {triMC.endpoint}/health
Timeout: {triMC.timeout_ms}ms
```

### 5.2 响应规格

```json
// 200 OK
{
  "status": "healthy",
  "version": "0.4.0",
  "uptime_seconds": 3600,
  "active_sessions": 3
}

// 非健康状态
{
  "status": "degraded",
  "version": "0.4.0",
  "reason": "model_provider_unreachable"
}
```

### 5.3 判定逻辑

| HTTP 状态码 | body.status | 判定 |
|------------|-------------|------|
| 200 | `healthy` | ✅ 健康 |
| 200 | `degraded` | ⚠️ 降级（计入失败计数） |
| 非 200 | — | ❌ 失败 |
| 超时 | — | ❌ 失败 |
| 连接拒绝 | — | ❌ 失败 |

---

## 6. 自动回退状态机

### 6.1 状态定义

```
            ┌──────────────────────────────┐
            │                              │
            ▼                              │
   ┌───────────────┐    health OK     ┌────┴──────────┐
   │  PASSTHROUGH  │ ───────────────► │  PASSTHROUGH   │
   │  (正常转发)    │                  │  (正常运行)     │
   └───────┬───────┘                  └────────────────┘
           │ health FAIL
           │ consecutive_failures++
           ▼
   ┌───────────────┐
   │  PASSTHROUGH  │  consecutive_failures < max
   │  (累计失败)    │ ──────────────────────────────► 继续转发（无变更）
   └───────┬───────┘
           │ consecutive_failures >= max
           ▼
   ┌───────────────┐
   │  FALLBACK     │  ① 修改 active-host.yaml: active_host=copilot, write_master=copilot
   │  (回退执行)    │  ② 显式通知用户（含错误原因 + 建议动作）
   └───────┬───────┘  ③ 设置 cooldown_until = now + 15min
           │          ④ consecutive_failures = 0
           ▼
   ┌───────────────┐
   │  NATIVE       │  cooldown 期内不尝试切回
   │  (Copilot 直连)│  冷却期过后 → 手动回退流程（CPO/CTO 联合裁决）
   └───────────────┘
```

### 6.2 回退通知格式

回退触发时，Copilot-host agent 向用户输出以下显式通知：

```
⚠️ TriMC Host 不可用，已自动回退至 Copilot-host

原因：连续 {N} 次健康检查失败
最后一次错误：{error_message}
时间：{timestamp}

当前状态：
  active_host: copilot（已自动切换）
  write_master: copilot（已同步）
  cooldown_until: {cooldown_end_time}（此时间内不尝试切回）

建议动作：
  1. 检查 TriMC server 状态：{triMC_endpoint}/health
  2. 确认后可手动切回：修改 .github/config/active-host.yaml active_host=triMC
  3. 或联系 CTO（小狄）排查 TriMC 故障
```

### 6.3 手动回退流程

自动回退后，切回 TriMC 需要 **CPO + CTO 联合裁决**：

1. CTO 确认 TriMC server 健康
2. CPO 确认产品就绪
3. 手动修改 `active-host.yaml`：`active_host: triMC, write_master: triMC`
4. 提交变更，附裁决记录

---

## 7. Write Master 锁（G8 防护）

### 7.1 核心原则

> **任何时候有且仅有 1 个 Host 持有 TriMetaverse 仓库写入权。Write Master 必须与 active_host 一致；不一致 = 最高优先级阻断。**

### 7.2 三层防护

```
Layer 1: active-host.yaml 自洽性检查
  └─ write_master 必须 == active_host
  └─ 不一致 → Copilot-host agent 启动时拒绝运行，显式报错

Layer 2: Copilot-host 写入前检查
  └─ 每次 write/edit 工具调用前检查 write_master
  └─ write_master != copilot → 拒绝写入，返回 "Write Master is triMC; switch to read-only mode"

Layer 3: TriMC 写入前检查
  └─ 每次文件写入前检查 active-host.yaml 中的 write_master
  └─ write_master != triMC → 拒绝写入
```

### 7.3 不一致场景处理

| 场景 | write_master | active_host | 行为 |
|------|-------------|-------------|------|
| 正常（Copilot） | copilot | copilot | ✅ Copilot 读写，TriMC 不存在/只读 |
| 正常（TriMC） | triMC | triMC | ✅ TriMC 读写，Copilot 只读 |
| 配置错误 | copilot | triMC | ❌ Copilot 拒绝启动，报 "write_master/active_host mismatch" |
| 配置错误 | triMC | copilot | ❌ Copilot 拒绝启动 |
| G7 回退后 | copilot | copilot | ✅ 自动同步，无需手动修正 |

---

## 8. Shadow Workspace 设计

### 8.1 目的

在 TriMC 持有 Write Master 前，先在隔离环境验证其输出与 Copilot-host 的一致性。

### 8.2 工作空间布局

```
TriMetaverse/                        ← 生产仓库（Write Master: copilot）
TriMC-shadow-workspace/              ← Shadow 隔离区（Write Master: NONE，只读）
├── .git/                            ← 独立 git clone/checkout
├── ...（TriMetaverse 仓库副本）
└── shadow-logs/
    ├── round-0001/
    │   ├── input.json               ← 用户输入 + 上下文
    │   ├── copilot-output.json      ← Copilot-host 操作日志
    │   ├── trimc-output.json        ← TriMC 操作日志
    │   └── diff.patch               ← 差异对比
    └── ...
```

### 8.3 Shadow 模式数据流

```
用户输入
    │
    ├──→ Copilot-host (Write Master) ──→ 生产结果 + 操作日志
    │
    └──→ TriMC (Shadow, Read-Only)  ──→ shadow 结果 + 操作日志
                │
                │  操作日志写入隔离 workspace
                │  不触碰 TriMetaverse/
                ▼
         对比引擎
                │
                ├── 一致 → 记录 round N: PASS
                └── 不一致 → 记录 diff + 告警
```

### 8.4 Shadow Workspace 初始化

```bash
# 一次性初始化（CTO 执行）
git clone TriMetaverse.git TriMC-shadow-workspace
cd TriMC-shadow-workspace
git remote set-url origin --push /dev/null  # 禁止 push
mkdir -p shadow-logs
```

### 8.5 TriMC Shadow 模式约束

- `write_master: copilot` 期间，TriMC 在 Shadow 模式下运行
- TriMC 的文件写入目标指向 `shadow.workspace_path`，而非 `TriMetaverse/`
- TriMC **不执行** git push
- Shadow workspace 的 `.git/config` 已禁用 push remote

---

## 9. 对比引擎设计

### 9.1 对比维度

| 维度 | 方法 | 权重 |
|------|------|------|
| 文本输出一致性 | 语义相似度（embedding cosine） | 40% |
| 工具调用序列 | 调用类型 + 参数 diff | 35% |
| 文件变更 | unified diff 对比 | 20% |
| 退出原因 | 字符串匹配 | 5% |

### 9.2 一致率计算

```
总一致率 = Σ(维度得分 × 权重)

每轮:   一致率 ≥ threshold → PASS
        一致率 < threshold → FAIL（生成 diff 报告）

总评估: 连续 N 轮 PASS 率 ≥ 95% → Shadow 验证通过（G6）
```

### 9.3 对比引擎实现

**位置**：`TriCompany/runtime/cognition/comparison_engine.py`（Python CLI）
**输入**：`shadow-logs/round-NNNN/` 下的 copilot-output.json + trimc-output.json
**输出**：`consistency_report.json` + `diff-summary.md`

```python
# 核心接口
def compare_round(round_path: str) -> ConsistencyResult:
    """对比单轮 shadow 输出"""
    ...

def aggregate_report(shadow_logs_path: str, rounds: int) -> ConsistencyReport:
    """聚合 N 轮对比结果"""
    ...
```

**CLI 入口**：
```bash
python -m runtime.cognition.comparison_engine --rounds 100 --threshold 0.95
```

---

## 10. 实现阶段

### Phase A：配置层 + Native/Health（当前可执行）

| 步骤 | 产出 | 依赖 |
|------|------|------|
| A1 | 创建 `.github/config/active-host.yaml`（当前值：copilot） | 无 |
| A2 | TriMC 实现 `GET /health` 端点 | TriMC server 已运行 |
| A3 | Copilot-host agent 指令中嵌入 active-host.yaml 读取逻辑 | A1 |
| A4 | Health check 单元测试（mock TriMC endpoint） | A2 |

### Phase B：Passthrough 模式 + 自动回退

| 步骤 | 产出 | 依赖 |
|------|------|------|
| B1 | Copilot-host agent Passthrough 转发逻辑 | A3 |
| B2 | 自动回退状态机实现 | B1 |
| B3 | 回退通知模板 | B2 |
| B4 | Passthrough + fallback 集成测试 | B1-B3 |
| B5 | 手动回退 SOP 文档 | B2 |

### Phase C：Write Master 锁 + Shadow Workspace + 对比引擎

| 步骤 | 产出 | 依赖 |
|------|------|------|
| C1 | Write Master 三层防护实现 | A1 |
| C2 | Shadow workspace 初始化脚本 | C1 |
| C3 | TriMC Shadow 模式（写入目标重定向） | C2 |
| C4 | 对比引擎 Python CLI | C2 |
| C5 | G6/G7/G8 门禁验证脚本 | C1-C4 |

---

## 11. 测试策略

### 11.1 单元测试

| 测试 | 覆盖 |
|------|------|
| `active-host.yaml` schema 验证 | YAML parse + 字段约束 |
| Health check 响应解析 | 200/非200/超时/连接拒绝 |
| Fallback 状态机转换 | 所有状态转换路径 |
| Write Master 不一致检测 | Layer 1/2/3 各自触发条件 |

### 11.2 集成测试

| 测试 | 覆盖 |
|------|------|
| Native → Passthrough 切换 | 修改 YAML → agent 读取 → 模式切换 |
| Health check 连续失败 → 自动回退 | Mock TriMC endpoint 返回 503 |
| Write Master 写入拒绝 | write_master != active_host 时尝试 write |
| Shadow 模式隔离 | 验证 TriMC 输出写入 shadow workspace 而非生产仓 |

### 11.3 端到端测试（Gate 验证）

| Gate | 测试 | 通过标准 |
|------|------|------|
| G6 | Shadow 一致率 | 连续 100 轮 ≥ 95% |
| G7 | 回退演练 | TriMC 故障 → Copilot 接管 ≤ 60s |
| G8 | 并发写入安全 | 证明任何时候只有 1 个 Write Master |

---

## 12. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| active-host.yaml 被误改 | 中 | 高 | Git 追踪 + Layer 1 自洽性检查 |
| TriMC /health 假阳性（200 但实际不可用） | 中 | 中 | 深度健康检查（模型调用可用性）Phase B 后期补齐 |
| Shadow workspace 与生产仓不同步 | 低 | 中 | 对比引擎每轮前 git pull |
| Copilot-host agent 指令不支持条件路由 | 低 | 高 | 先验证 agent.md 中嵌入条件逻辑的可行性；不可行则改用 wrapper script |
| 对比引擎语义相似度误判 | 中 | 低 | 多维度加权 + 人工抽检阈值附近的 case |

---

## 13. 使用依据

- `TriCompany/docs/registry/product-state.md` §Iteration Strategy（CPO-008/010）
- `TriCompany/docs/registry/product-state.md` §Operational Safety Model（CPO-009）
- `TriCompany/docs/registry/code-state.md`（CTO Code Registry）
- `TriCompany/docs/engineering/DESIGN.md`（技术设计初版）
- `TriMC/docs/engineering/deployment-topology.md`（TriMC 部署拓扑）
- `TriMC/docs/engineering/employee-orchestration-design.md`（员工编排层）

---

## 附录：与其他设计文档的关系

| 文档 | 关系 |
|------|------|
| `host-object-generation-design.md` | 上游——员工宿主对象生成管道（本方案依赖已有宿主对象） |
| `employee-orchestration-design.md` | 下游——TriMC 运行时员工派发（本方案的路由层在更上层） |
| `deployment-topology.md` | 互补——TriMC 服务器部署（本方案引用其 /health 端点） |
| `metacognition-architecture.md` | 并列——元认知层（本方案的路由决策可写入审计日志） |
