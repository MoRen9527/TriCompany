# ADE 模式：Agent 智能任务确定性执行规范

> **版本**：v1.2  
> **来源**：本次会话源侧发布架构实战总结 + 业内标准参照 + CPO/CTO 联合评审  
> **参照标准**：Microsoft Conductor（MIT）、MCP Protocol（Anthropic）、Azure Agent Orchestration Patterns  
> **适用**：TriCompany 所有涉及 CLI 执行 + 审计要求的研发智能任务  
> **变更记录**：
> - v1.2（2026-07-24）：新增自动化测试、自动化部署为典型 ADE 场景；扩展场景选择指南
> - v1.1（2026-07-24）：新增 §七 ADE vs Skill 对比与边界、§八 组合模式；修正 MCP 对应描述；CEOCS/CPO/CTO 联合评审通过
> - v1.0-draft（初始稿）：ADE 三层架构、核心原则、业内标准对应、适用场景、反模式、实践案例

---

## 一、模式定义

**ADE = Agent plans → Deterministic CLI executes → Agent closes**

```
┌─────────────────────────────────────────────────────────────┐
│  Agent（智能规划层）                                          │
│  ├─ 理解任务 → 拆解步骤 → 选择工具 → 设定验收标准              │
│  └─ 不直接执行有副作用的操作                                   │
├─────────────────────────────────────────────────────────────┤
│  CLI（确定性执行层）                                          │
│  ├─ 接收参数 → 执行操作 → 输出结构化结果（JSON）                │
│  ├─ 自检报告（pass/fail/gaps）                                │
│  └─ 不包含 LLM 推理、不消耗 token                              │
├─────────────────────────────────────────────────────────────┤
│  Agent（收口层）                                              │
│  ├─ 读取 CLI 自检报告 → 验证结果 → 更新状态                    │
│  ├─ 写日志/审计记录 → 通知相关方                               │
│  └─ 异常时升级给 owner                                        │
└─────────────────────────────────────────────────────────────┘
```

## 二、核心原则

### 2.1 智能与确定性的分离

| 层 | 负责 | 特点 |
|----|------|------|
| Agent | 规划、判断、收口 | 智能但不可靠 |
| CLI | 执行、校验、报告 | 可靠但无智能 |

**关键约束**：Agent **不直接**做有副作用的操作（文件写入、发布、删除）。所有写操作必须通过 CLI，CLI 提供确定性的自检报告。

### 2.2 CLI 必须输出结构化自检报告

任何 ADE 模式下的 CLI 必须输出包含以下字段的 JSON：

```json
{
  "status": "pass|fail|partial",
  "summary": { "total": N, "changed": N, "errors": N },
  "changes": [{ "action": "...", "target": "...", "before": "...", "after": "..." }],
  "errors": [{ "item": "...", "reason": "..." }],
  "check_time": "ISO8601"
}
```

Agent 收口时只读取此报告，不做二次推断。

### 2.3 可审计性要求

- CLI 每次执行输出 JSON → 可被 agent 解析 → 可写入 sync-log
- 变化前后对比（before/after）必须在报告中
- 执行时间戳必须记录
- 异常必须显式标记（errors 数组非空时 status=fail）

### 2.4 安全门

- CLI 必须有 `--dry-run` 或等效模式（默认不写入）
- 写入操作需要显式参数（如 `--sync`、`--agent-execute`）
- 保护目标（protected targets）必须在 CLI 层硬编码，不依赖 agent 判断

## 三、与业内标准的对应

| 本规范 | Microsoft Conductor | MCP Protocol | Azure Agent Patterns |
|--------|-------------------|--------------|---------------------|
| Agent 拆解任务 | YAML 定义 workflow | Host 层 | Agent Plans |
| CLI 确定性执行 | Deterministic orchestration | MCP Tools 层（确定性工具调用） | Tool Executes |
| CLI 自检报告 | — | — | — |
| Agent 收口 | — | — | Agent Closes |
| 日志/审计 | Version-controllable YAML | Result hashing + replay | Traceability logging |

**差异点**：Conductor 用 YAML 定义流程（纯确定性），我们保留 Agent 做智能规划（灵活性）。这是「半结构化编排」——Agent 在结构化的 CLI 约束内做智能决策。MCP 的 Tools 层提供确定性工具调用的传输协议，但 MCP 不原生定义自检报告和收口语义——这是 ADE 额外构建的。

## 四、适用场景

满足以下**任意两项**即应使用 ADE 模式：

1. 涉及文件系统写操作（创建/修改/删除/发布）
2. 需要事后审计（谁改了、改了什么、什么时候）
3. 操作可被自动化重复执行
4. 涉及跨模块/跨仓库同步
5. 操作失败需要可回滚或可追溯

## 五、反模式（禁止）

| 反模式 | 说明 |
|--------|------|
| Agent 直接写文件 | 绕过了 CLI 的安全门和自检 |
| CLI 包含 LLM 推理 | 破坏确定性，不可审计 |
| 无自检报告的执行 | 无法验证结果 |
| agent 推断 CLI 结果 | 必须读取结构化报告，不做"猜测" |

## 六、已有实践案例

| 案例 | Agent | CLI | 模式 |
|------|-------|-----|------|
| 源侧→发布侧同步 | 小赛 | `source_publish_check --check --sync --scope` | ADE 完整实现 |
| Agent live entry 发布 | 小赛 | `source_publish_check --publish-agents --agent-execute` | ADE 完整实现 |
| 自动化测试（按用例） | 小柯（TestEngineer） | `pytest --json-report` 或 `validation.py` 输出结构化结果 | 推荐 ADE 模式 |
| 自动化部署（按步骤） | 小布（TriDeployer）⚠️ 待上岗 | 部署 CLI 按步骤执行、逐步骤自检报告 | 推荐 ADE 模式 |
| IPD 全流程（10 阶段） | CPO/CTO/总助×TriDev | `ipd_case_engine.py` 驱动阶段 + `record_gate()` 门禁 + `ipd_case_validation.py` 校验 | 本质即 ADE，待规范化 |
| 员工对象发布 | CHO | `employee_host_publish` | ADE 完整实现 |
| 员工对象发布 | CHO | `employee_host_publish` | ADE 完整实现 |

### 6.1 IPD 与 ADE 的同构关系

IPD 的 10 阶段（DISCOVERY → INTELLIGENCE → DESIGNING → CODING → VERIFY-INTEGRATION → REDTEAM → QA → DEPLOYMENT → ASSURANCE → DELIVERY）**本质上就是 ADE 在项目生命周期级的实例**：

| IPD 组件 | ADE 对应层 | 当前状态 |
|-----------|-----------|----------|
| `businessOwner` / `actingOwner` 规划阶段目标 | Agent 规划层 | ✅ 已有 |
| `ipd_case_engine.py` 驱动阶段推进 | CLI 执行层 | ✅ 已有 |
| `record_gate()` 门禁通过/冻结记录 | CLI 自检 | ✅ 已有 |
| `ipd_case_validation.py` 校验证据完整性 | CLI 自检 | ✅ 已有 |
| `gateOwner` 审阅证据、放行/冻结 | Agent 收口层 | ✅ 已有 |
| through-pass checklist + gate ledger | 审计日志 | ✅ 已有 |

**待规范化**：阶段输出未统一为 ADE JSON 自检格式；gate 判断仍在 agent 做语义推断；before/after 未自动记录。

## 七、ADE 与 Skill 的对比与边界

### 7.1 Skill 的本质（从真源定义提取）

在 TriCompany 体系中，**Skill** 的定义来自 `cognition-runtime-module-plan.md` 和 `skill-spec.schema.json`：

> **Skill** = 复用经验/知识的 **LLM 注入模式**。Agent 匹配触发模式 → 装载已批准 SkillSpec → 生成注入 context → Agent 解释并执行步骤。执行仍是 LLM 驱动的，**非确定性**。

SkillSpec 运行时契约包含：`skillName`、`skillVersion`、`triggerPatterns`、`preconditions`、`executionSteps`、`successEvidence`、`failureGuards`、`allowedHosts`、`reviewGate`。

### 7.2 ADE vs Skill 对比表

| 维度 | ADE | Skill |
|------|-----|-------|
| **本质** | 确定性执行模式 | LLM 注入模式 |
| **执行主体** | CLI（无 LLM、不消耗 token） | Agent（LLM 驱动、消耗 token） |
| **确定性** | 高——同输入必同输出 | 低——LLM 推理不可复现 |
| **审计能力** | 强——结构化 JSON + before/after + timestamp | 弱——依赖 Agent 输出质量，无可编程自检 |
| **安全门** | CLI 层硬编码 protected targets | reviewGate 审批 + allowedHosts |
| **失败处理** | CLI 自检报告 → Agent 升级给 owner | failureGuards（Agent 解释执行） |
| **灵活性** | 低——参数化，不做语义判断 | 高——Agent 自由解释执行步骤 |
| **审批机制** | 无需审批（CLI 本身即安全门） | reviewGate（code-registry / cto / manual-approval） |
| **定时执行** | 通过外部调度触发（如 cron） | scheduleEligible 标记 + cron runner |

### 7.3 场景选择指南

满足以下条件时，应使用 **ADE**（同时满足任意两项即应使用，见 §四）：

| 场景 | 选 ADE | 选 Skill | 理由 |
|------|--------|---------|------|
| 源侧→发布侧文件同步 | ✅ | ❌ | 确定性操作，需要 before/after 审计链 |
| Agent live entry 发布 | ✅ | ❌ | 跨路径写操作，必须通过 CLI 安全门 |
| 跨模块脚手架/初始化 | ✅ | ❌ | 文件系统写操作，可参数化 |
| **自动化测试（按用例）** | ✅ | ❌ | 确定性执行，结构化通过/失败/覆盖率报告，需审计门禁 |
| **自动化部署（按步骤）** | ✅ | ❌ | 每步可参数化、需逐步骤自检、失败需可回滚 |
| "代码审查模式"复用 | ❌ | ✅ | 经验注入，需要 Agent 灵活判断上下文 |
| 跨 Agent 共享行为模板 | ❌ | ✅ | LLM 注入，非文件操作 |
| "遇到 X 错误时怎么处理" | ❌ | ✅ | 需要语义理解和上下文判断 |
| 产品发布检查清单 | ✅ | ❌ | 确定性检查，结构化自检报告 |
| 新员工 onboarding 话术 | ❌ | ✅ | 经验注入，Agent 按对话自然执行 |

### 7.4 为什么源侧发布同步用 ADE 而非 Skill

1. **确定性要求**：文件从源侧同步到发布侧是可参数化的机械操作（scope、target、sync mode），不需要 LLM 做语义判断。用 Skill 会让同一操作每次产生不同结果。
2. **审计要求**：每条变更必须有 before/after + timestamp 的结构化记录。Skill 依赖 Agent 输出文本，无法保证自检报告的可解析性。
3. **安全要求**：protected targets（如 `.env`、`.tricompany-cognition`、binding-profiles）必须在 CLI 层硬编码。Skill 的 Agent 执行存在被 prompt injection 或幻觉绕过的风险。
4. **Token 经济**：跨模块同步可能涉及数十个文件。Skill 需要把全部文件内容注入 context + 执行推理，大量消耗 token 且不可预测；ADE 的 CLI 执行零 token 消耗。
5. **可复现性**：同样的 source → publish 参数在不同时间执行应产生等价结果。Skill 做不到这一点。

### 7.5 边界划分

```
           ┌──────────────────────────────┐
           │        「做什么」判断           │
           │    Agent 规划层               │
           │    └─ 可用 Skill 辅助判断      │
           ├────────────┬─────────────────┤
           │            │                 │
           ▼            ▼                 ▼
     ┌──────────┐ ┌──────────┐    ┌──────────┐
     │  ADE     │ │  Skill   │    │  混合    │
     │「怎么做」  │ │「怎么想」  │    │ Skill    │
     │ 确定性执行 │ │ 经验注入  │    │ 触发 ADE │
     │ CLI 执行  │ │ Agent 执行│    │ CLI 执行 │
     └──────────┘ └──────────┘    └──────────┘
```

- **ADE 管"怎么做"**：操作执行面，关心确定性、可审计、安全门
- **Skill 管"怎么想"**：行为模式面，关心经验复用、灵活判断、跨 Agent 共享
- **不互相替代**：ADE 不替代 Skill 的经验注入能力；Skill 不替代 ADE 的审计和安全门

## 八、ADE 与 Skill 的组合模式

### 8.1 Skill 触发 ADE

Skill 的 `triggerPatterns` 可用于识别"现在需要执行 ADE 操作"。当 Agent 通过 Skill 判断当前场景满足 ADE 触发条件时，Agent 路由到对应的 ADE CLI 执行：

```
Skill 匹配 trigger → Agent 识别场景 → 调用 ADE CLI → CLI 输出自检报告 → Agent 收口
```

**典型案例**：Agent 识别到"用户要求同步文档"→ Skill 确认这是发布同步场景 → Agent 调用 `source_publish_check --sync --scope docs` → CLI 输出自检 JSON → Agent 读取报告并通知用户。

### 8.2 ADE 输出触发 Skill

CLI 自检报告中的 `errors` 或 `gaps` 字段可被 Agent 作为输入，触发对应的处理 Skill：

```
CLI 输出 errors → Agent 读取 → Skill 匹配错误模式 → Agent 执行处理流程
```

**典型案例**：`source_publish_check` 报告 publish target 不存在 → Agent 匹配到 "missing-publish-target" Skill → Agent 按 Skill 步骤创建目录、更新 manifest、重新执行同步。

### 8.3 组合约束

- Skill 可以建议调用 ADE CLI，但不能替代 CLI 执行写操作
- ADE CLI 的输出可以触发 Skill，但 CLI 自身不包含 Skill 推理
- 组合链的审计记录必须同时包含 CLI 自检报告（确定性）和 Skill 执行记录（非确定性），两者分开存储

## 九、实施要求

### 新建 CLI 工具时
1. 必须输出结构化 JSON
2. 必须包含 `--help` 和 `--dry-run`（或等效安全默认）
3. 必须有配套的 validation suite（pytest/unittest）
4. 必须在 `sync-log.md` 或等效审计日志中记录每次执行

### 新建 Agent 时
1. 涉及写操作的职责必须声明对应的 CLI 工具
2. 收口时必须读取 CLI 的结构化输出
3. 异常时必须升级到 owner，不静默处理

## 十、演进方向

- **短期**：~~`employee_host_publish` 补齐结构化自检报告~~ ✅ 已完成（2026-07-24）
- **中期**：探索 YAML-based workflow 定义（参照 Conductor），将 agent 规划层进一步结构化
- **长期**：多宿主适配时，CLI 层增加 host adapter，agent 层不变

---

> 本规范由 TriCompany 源侧发布架构实战总结，参照 Microsoft Conductor（MIT 协议）、MCP Protocol（Anthropic 开源）、Azure Agent Orchestration Patterns 制定。
