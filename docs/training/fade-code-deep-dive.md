# FADE 代码深潜：从 CLI 到门禁的实现地图

版本：V1.1
日期：2026-08-20（原立）/ 2026-08-28（对齐规范重构）
状态：当前教程（规范 v2.0.x 对齐版；2026-08-20 实现基线：统一报告合同、生命周期骨架、多宿主渲染、event-watch、知识注入、上岗 gating 全落地；2026-08-28 补 FADE-006 编排面行）
维护人：RAndDTrainer（小吴）
适用对象：需要接手、扩展或评审 FADE 相关代码的研发新人——先有全局，再进代码

> **版本对齐标注（2026-08-28）**：工程规范已完成 ade-pattern-spec.md → **fade-protocol-spec.md v2.0.0** 架构重构（ADE 概念退役，FADE 升为协议本体，FADE-XXX 为协议实例的具体实现；envelope 降格为发布域参考实现；旧规范文件保留为重定向桩）。本文已同步迁移：术语与合同表述（§2.2）、实例清单（§1 补 FADE-006）、真源链接均已对齐 v2.0.x。**本教程随 fade-protocol-spec.md 与代码更新而联动更新**，后续不再保留滞后差异注记。

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-code-deep-dive.md
- syncMode: follow-spec（本教程讲 FADE 代码实现；工程规范真源 = `../engineering/fade-protocol-spec.md`（v2.0.0 起，替代 ade-pattern-spec.md），实例登记真源 = `../engineering/fade-registry.md`，实现事实以代码为准；教程随规范与代码联动更新——规范每升版，本文同步核对修订）
- syncWith: docs/engineering/fade-protocol-spec.md, docs/engineering/fade-registry.md, ../../runtime/cognition/source_publish_check.py
- lastSyncedAt: 2026-08-28

## 1. 代码地图：FADE 的实现分布

FADE 不是单一程序，是"一个协议、两类执行体、四个仓"：

| 仓 | 模块 | 承担 FADE 的哪一段 |
| --- | --- | --- |
| TriCompany | `runtime/cognition/source_publish_check.py`（3916 行，2026-08-28 复核） | FADE-002 全 CLI 面：DCE 三 scope + Close CLI + Score CLI + event-watch |
| TriCompany | `runtime/cognition/employee_host_publish.py` | FADE-004 员工对象发布（委托 `--publish-agents`） |
| TriCompany | `docs/engineering/fade-papers/` | 实例试卷 + 评分 + 证据（001..004/006） |
| TriLC | `src/company/staffing.ts` | FADE-004 上岗链执行体（onboard/decide/roster）+ 上岗 gating |
| TriLC | `src/knowledge-injector/`（4 文件） | 知识注入链路（knowledge.db 同步/注入/指标） |
| TriLC | `src/company/session-initializer.ts`、`src/server/app.ts`、`src/heartbeat/agent-runner.ts` | 知识注入三挂接点 |
| TriMetaverse | `scripts/journal/journal-cli.mjs` | FADE-003 周记链（begin/qualify/append/close） |
| TriMetaverse | 执行面编排链（规范 `docs/execution/fade-006-execution-autopick-spec.md` + 管线 `fade-pipeline-design.md`） | FADE-006 执行面自动拾取：sg-bare post-receive hook 派 tick + trimc cron 兜底 + CC 编排会话派工 + 树文件/tick 台账（Close CLI 载体 = tick 台账回收器 rc 终值 + 树 status=done commit，spec §2.5 映射表声明形态；本教程不展开，见上述两文档） |
| TriMC | cron 平面迁移链 | FADE-001（本教程不展开，见 `TriMC/docs/ops/trimc-cron-plane-shift-runbook.md`） |

> **注意（spec §2.8 段-实现映射表）**：FADE 协议只约束每段职责不变量；各实例的确定性载体由实例在登记册声明，**并不都长成"一个 CLI 命令"**——FADE-006 的 Close CLI 形态就是"commit + tick 台账 rc 终值"（spec §2.5 明文）。查某实例的载体先看登记册，再看代码。

**先记住全局分工**：Agent（智能）通过 Skill 做 Plan/Close/Score 语义判断；CLI（确定性）做 DCE/Verify/Score/Close 执行与收口。代码里"Agent 直接写文件"的模式是被禁止的反模式——所有写入都走 CLI。

## 2. FADE-002 CLI 面：source_publish_check.py

> **范围消歧**：本节标题讲的是 **FADE-002（发布域）的 CLI 面**——这个实例恰好把 DCE 三 scope + Close CLI + Score CLI + event-watch 全部承载在 `source_publish_check.py` 一个文件里。它**不是** FADE 整体的 CLI 全貌：其他实例各有自己的确定性载体（FADE-003 的 `journal-cli.mjs`、FADE-004 的 staffing 端点、FADE-006 的 tick 台账回收器等，见 §1 表与登记册段-实现映射表）。

### 2.1 参数矩阵（build_parser，main 内互斥校验）

| 面 | 参数 | 语义 | 安全门 |
| --- | --- | --- | --- |
| sync（目录扫描） | `--check` / `--sync` | 四路 diff（hash/git/codegraph/JSON semantic）→ 机械复制 | 默认 dry-run；`--sync` 显式写 |
| project-docs（manifest 域） | `--project-docs` / `--project-docs-execute` | 真源文档同步，published-copy 机械 / published-summary 需候选 | 默认 dry-run；execute 才写 |
| publish-agents（声明面） | `--publish-agents` / `--agent-execute` / `--host={copilot\|claude}` / `--employees` | AI 员工档案发布（多宿主渲染） | 默认 dry-run；`--agent-execute` 才写 |
| lifecycle（Close） | `--close --verdict --evidence-ref --source-revision` | 终态门：校验裁决 + 写终态审计 | 永远 execute（收口本来就是写） |
| lifecycle（Score） | `--score --score-paper --score-report --score-quality-scores --score-threshold` | 评分：覆盖检查 + 质量合并 + 双门槛 | 只读 |
| event-watch | `--event-watch` / `--watch --interval --auto-sync --sync-threshold --audit-dir --state-file` | 文件/Git 事件自动触发 | 默认 dry-run；`--auto-sync` 才写；project-docs 永不自动写 |
| 通用 | `--run-id`（显式覆盖时间戳 id） | 所有 envelope 的 run_id | — |

**互斥规则（main() 第 3270-3305 行，2026-08-28 复核）**：`--close` / `--score` / `--event-watch` / `--watch` 是独占 lifecycle/触发模式，与业务 scope 互斥；`--run-id` 与 `--watch` 互斥（watch 每批自动派生 id）；`--agent-execute` 必须配 `--publish-agents`。违规直接 rc=1。

**退出码契约**：任何 scope `errors>0` → rc=1（CI 可感知拒绝路径）；Score CLI 以 `verdict != PASS` 为 rc=1；Close CLI 以 `CLOSE_REJECTED` 为 rc=1。

### 2.2 报告合同（envelope v1.0，spec §2.2——v2.0.0 起为发布域参考实现）

三个业务 scope + close lifecycle scope + event-watch 触发面全部序列化为同一壳：

```json
{
  "protocol": "ade-report", "version": "1.0",
  "scope": "sync|project-docs|publish-agents|close|event-watch",
  "run_id": "...", "mode": "dry-run|execute", "check_time": "ISO8601",
  "status": "pass|fail|partial",
  "summary": { "total": N, "changed": N, "skipped": N, "errors": N },
  "items": [ { "action", "source", "target", "before_hash", "after_hash", "scope_key", "error" } ],
  "scope_specific": {}
}
```

实现要点：

- **合同分层（v2.0.0 envelope 降格）**：envelope v1.0 从普适强制降格为**发布域参考实现**（FADE-002 声明载体）；协议普适条款抽出为四条不变量——①结构化、②可守恒校验、③errors>0 时非零退出码、④action 词表契约化（spec §2.2）。其他域经段-实现映射表声明各自报告合同，**不必复用 envelope**（如 FADE-006 的 tick 台账）。
- **守恒不变量**：`summary.total == len(items)` 且 `total == changed + skipped + errors`。publish-agents 序列化时把 `derived_*`（渲染面非写入动作）计入 skipped 保持守恒（`_serialize_agent_publish_report` 第 1233-1243 行）。
- **action 词表契约化**：`ADE_ACTIONS`（15 个）+ `ADE_ACTIONS_PER_SCOPE`（每 scope 白名单子集），validation 强制（`source_publish_check.py:218/:236`，校验点 `source_publish_check_validation.py:1443`）。`close` 是 lifecycle scope，复用 envelope 但不在业务词表内；常量名 `ADE_*` 为代码级冻结合同（历史命名，语义即 FADE 词表）。
- **组合运行**：`--check --publish-agents` 输出 reports 容器（`_serialize_combined_container`），顶层聚合：任一域 errors>0 → fail > 任一 partial → partial > pass；summary 直和守恒。
- **UTF-8 出口**：`_reconfigure_stdout_utf8()` 在 main 开头与每个 JSON 出口强制 stdout UTF-8（Windows GBK 控制台会毁掉 `ensure_ascii=False` 的 JSON，这是机器合同必须防的）。

## 3. 渲染管线（publish-agents 面，ADE-B 核心）

### 3.1 数据结构：HOST_RENDER_REGISTRY

`HostRenderSpec` 注册每个宿主的渲染模板（第 122-187 行），当前两个：

| 字段 | copilot | claude |
| --- | --- | --- |
| target_root | `.github/agents/` | `.claude/agents/` |
| target_suffix | `.agent.md` | `.md` |
| frontmatter_fields | name/description/tools/user-invocable | 同左（顺序化输出） |
| tool_name_map | {}（原样） | `read→Read`、`search→Glob`…（小写→PascalCase） |
| protected_prefix | `.github/agents/` | `.claude/agents/` |
| default_extra_section | — | CLAUDE_DERIVED_MARKER（"本文件由统一发布管线渲染生成…禁人工编辑"） |

**扩展点**：未来支持新宿主 = 注册表加一个条目（模板 + 目标根 + 白名单），管线零改动。

### 3.2 渲染调用链

```text
run_agent_publish()                              # 面入口
  -> _load_publish_manifest()                    # 读 manifest（liveEntries）
  -> _derive_allowed_agent_targets()             # 白名单：仅 eligible status 条目
  -> _derive_host_target(target, host_id)        # manifest 目标 → 宿主面最终写入目标
  -> _is_agent_publish_target_protected()        # 白名单 ∩ 禁区 = ∅ 硬检查（整 run 拒绝）
  -> _filter_agent_publish_entries()             # status + --employees 过滤
  -> _publish_single_agent()                     # 单条：渲染 → SHA-256 → 与 target 比对
       -> _is_render_entry()                     # copy 面（无渲染元数据+copilot）字节透传
       -> _render_agent_payload()                # 源 + 模板 → 渲染产物
            -> _split_frontmatter()              # 拆 frontmatter/body（尾换行约定保字节稳定）
            -> _render_frontmatter_for_host()    # 工具名映射/剔除/白名单
```

**关键设计点**：

1. **复制 vs 渲染**：copy 面（旧 manifest 条目 + host=copilot）字节透传，零回归；渲染面（任何非 copilot host 或带 renderTemplate/extraSections 元数据）走"源 + 模板 → 产物"。渲染面统一 LF 归一（CRLF→LF，渲染产物字节稳定）。
2. **映射/剔除双态（定案 2）**：claude 面未映射的源工具名**剔除**（dropped_tools 进报告 scope_specific.tool_drops，审计可见非静默）；映射值必须 ∈ `CLAUDE_HOST_TOOL_ALLOWLIST`（11 个工具硬白名单），映射到白名单外 = error 不落盘。
3. **派生一致校验**：渲染面比较的是"渲染产物 hash"与"live 文件 hash"——`derived_identical`（一致）/ `derived_drift`（漂移，dry-run 意图）。这就是"live entry 是派生壳，禁人工编辑"的机器实现：人工改 live 会立即漂移，重跑 publish 会覆盖 + 审计留痕。
4. **白名单反向禁区校验（阶段 0 修复 2）**：`_is_agent_publish_target_protected` 翻转逻辑——只有宿主注册的 protected_prefix 是合法落点，其余一律 `protected_target_rejected`（含 binding-profiles、五件套后缀、路径逃逸形态、兄弟变体目录 `.github/agents-backup` 等）。manifest 被污染时整 run 拒绝，绝不部分执行。

### 3.3 渲染报告的目标是最终写入面

`run_agent_publish` 第 1198-1199 行：报告的 target 是宿主派生后的最终写入目标（`result.target == entry.target` 时替换为 `final_target`），消费方读到的是真实写入面而非 copilot 面 manifest 值。

## 4. Close CLI：终态门（spec §2.5）

```text
run_close()                                       # 面入口
  -> _validate_close_inputs()                     # verdict ∈ 四词表 / runId 格式 / evidence-ref 可解析 / source-revision 单 token
  -> _close_data_dir()                            # 默认 <source-root>/.ade/
  -> 写审计记录 <run_id>.close-ade.json           # 幂等：已存在 → run_already_closed 拒绝
  -> _serialize_close_envelope()                  # CLOSED（pass）/ CLOSE_REJECTED（fail，rc=1）
```

- 四终态词表：`ADE_CLOSE_VERDICTS = (APPROVED, FROZEN, ESCALATED, RETRY)`（与 spec §8.3 一致）。
- 失败永不静默：任何校验失败都产出 `CLOSE_REJECTED` envelope（非零 rc + 机器可读 error 拼接）。
- 状态转换校验：同一 runId 的审计记录已存在 → 拒绝二次 close（run_already_closed）。
- evidence-ref 可解析性：绝对/相对路径必须存在，http(s)/file URL 放行。

## 5. Score CLI：试卷评分（spec §2.6 / 模板 §三）

```text
run_score()                                       # 入口：输入错误映射 fail 合同 + rc=1
  -> score_assessment()                           # 核心
       -> _iter_report_envelopes()                # 单 envelope 或 reports 容器归一化
       -> _find_item_evidence(paper_item, envs)   # 覆盖检查（确定性）：probe 匹配 items/scope_specific
       -> _normalize_quality_scores()             # Score Skill 质量分归一：{items:[{id,score}]} 或平铺 map
       -> 双门槛判定                               # verdict = PASS ⇔ required_all_passed ∧ total >= threshold
```

- **覆盖检查语义**（`_find_item_evidence`）：按 `evidence_ref`（声明的优先）→ `id` → `label` 三序 probe；匹配规则 = scope_key/source/target 相等、`/`+probe 后缀、或文件 stem 相等（`docs/dry-run-gate.md` 匹配 id `dry-run-gate`）；scope_specific 顶层键/值相等也算。找不到 → `omission=true`，该项 0 分，必选项计入全过判定。
- **质量分合并**：无 Score Skill 评分时，已覆盖项按满分计（无依据不扣分），`quality_score=null` 留在明细里可见。
- **阈值解析链**：CLI `--score-threshold` → 试卷 `threshold` → 默认 80（`ADE_SCORE_DEFAULT_THRESHOLD`）。
- **三态映射**：PASS → status=pass；必选全过但总分不足 → partial（"覆盖 ok，质量不足"）；必选有遗漏 → fail。
- 评分 JSON 是 Close Skill 裁决的客观证据，与 CLI 自检报告同级，不得伪造或覆盖。

## 6. event-watch：事件自动触发（FADE-002 补齐项落位）

```text
main() --event-watch（单次）
  -> _event_scan_from_args()
    -> run_event_scan_once()                      # 一次扫描批次
         -> _event_scan_fingerprints()            # 监听目录全文件 SHA-256
         -> _event_git_state()                    # HEAD sha（worktree）/ refs 指纹（bare）/ none
         -> _event_load_state() / _event_save_state()  # state.json 持久基线
         -> 变更计算                              # 文件 hash 变化/删除 ∪ Git head/refs 变化（去重合并）
         -> _event_derive_scopes()                # 变更 → 检查面（manifest→publish-agents+project-docs；source-agents/→publish-agents；docs/→check）
         -> _event_run_scope_check()              # 默认 dry-run 检查；project-docs 永不 execute
         -> 审计落盘                              # events.jsonl + reports/<run_id>.json + state.json
```

关键语义：

- **首扫只建基线不触发**（state 文件不存在 → kind=none）：避免 daemon 每次启动触发无意义检查。
- **幂等**：指纹未变 → deduped 批次，不写事件日志。
- **建议 sync 判据**：变更数 ≥ 阈值（默认 5）或含关键文件（manifest、`.agent.md` 源）。`--auto-sync` 显式传入才实际写入；project-docs 面硬编码永不自动写（published-summary 需 planner 候选 + 联审）。
- **scope 边界**：event-watch 是第四个 envelope scope（触发面审计 scope），与 close 同构——复用合同但不在 `ADE_SCOPES` 三业务域内（代码注释明确；spec §2.2 未提及此面，属文档待补项，见第 11 节）。
- 前台循环 `--watch` 每批 JSON 输出 stdout，供 daemon/cron 消费（spec §8.6 定时巡检链交接点）。

## 7. 上岗 gating：TriLC src/company/staffing.ts

### 7.1 FADE-004 链（上岗全生命周期）

```text
GET  /internal/v1/staffing/roster      # 13 岗 JD 全集 + status（active/pending-cho/candidate）+ counts
POST /internal/v1/staffing/onboard     # {roleId} → 202 pending-cho；链态门/已在岗/已待审 → 409/404
POST /internal/v1/staffing/decide      # {requestId, decision, approver, note} → CHO 门 403 → 名册写入 + 审计 json
```

- `requestOnboarding()`：链态门（ready/confirm/sync 才可增员，开业前 409）→ JD 存在性（role-catalog 单一真源）→ 已在岗/已待审去重 409 → 生成 `requestId + runId` 双 ID，落 `dataDir/staffing/requests.json`。
- `decideOnboarding()`：`CHO_ALLOWED = ['cho', 'chief-human-resources-officer', 'ceo', 'panel-cho']`——非 CHO 审批 403；批准 → `CompanyInitState.employees` 原子写入 + 审计 `CHO-staffing-<requestId>.json`（对齐 CHO-clone-staffing 形态）+ `init:staffing-*` 事件发布。
- 终态：APPROVED（active）/ REJECTED（回 candidate 可再申请）/ BLOCKED（链态/重复/不存在）。

### 7.2 上岗 gating（FADE-ASSESS-005）：名册从状态记录升级为功能门禁

**单一校验真源**（三处门禁共用）：

```text
getRoleRosterStatus(deps, roleId)     # active = employees 含该 role；pending-cho = 有待审请求；candidate = 目录存在未上岗；unknown
isRoleActive(deps, roleId)            # == 'active'
enforceRoleActive(deps, roleId)       # 非在岗 → { allowed: false, error: 'owner_not_active' }
```

| 门禁 | 落点 | 非在岗语义 | 兼容性 |
| --- | --- | --- | --- |
| 派工 | tasks/submit 可选 `ownerRoleId` | 409 `owner_not_active`（session 创建前短路） | 不携带不校验 |
| 分身 | AgentTool 合同岗 spawn 前置（`setRosterGate` 注入） | 工具错误 `role_not_active`（模型可见） | built-in 4 岗豁免；未注入 gate 放行 + warn |
| 调度 | cron job 可选 `roleId` → `shouldRunJob` | `skipped` + `owner_not_active`（不 incrementError） | 未绑定/未注入 → 放行 |

- **degraded 语义**：skipped 计入非 ok 路径——连续 3 次 skipped 触发 `cron:degraded`（有意设计：连续非在岗应暴露）；恢复仅以真实 ok 为凭，skipped 不解除 degraded、不广播 `cron:recovered`。
- **错误语义自洽**：`owner_not_active`（HTTP）/ `role_not_active`（工具）/ `skipped + 原因`（调度）三处命名一致，均不静默。
- 验证基线：24 新用例 + npm test 452/451（1 fail = TUI 既有 ink 依赖，stash 确认零交集）+ tsc 零错误 + 小柯独立 HTTP 实测。

## 8. 知识注入链路：TriLC src/knowledge-injector/

### 8.1 存储：knowledge.db（schema v3）

`{projectRoot}/.tricompany-cognition/knowledge.db`（multi-project-router 每项目隔离，WAL + user_version 迁移）。三表：

| 表 | 面 | 关键约束 |
| --- | --- | --- |
| knowledge_documents | 契约注入面 | `UNIQUE(namespace, layer, agent_id, content_hash)`——content_hash 是 SHA-256 幂等键；layer ∈ memory/colleagues/social/wiki/inbox |
| knowledge_consumption | 消费记录面 | namespace / content_hash / session_id / injection_mode（boot\|reload）/ consumed_at |
| knowledge_metrics | 验证指标分子面 | event ∈ escalation_blocked / routing_error |

层域语义：`layerDomain()`——memory/colleagues/social = contract（契约层五件套），wiki/inbox = content（内容层 curated）。命名空间：`employee/<id>` 注入；`org/shared` 预留；`org/audit` 不注入（kernel 写回面）。

### 8.2 同步：syncKnowledgeFromSource()（sync.ts）

```text
契约层：source-agents/<id>/*.{memory,colleagues,social}.md
内容层：TriCompany-copilot-host-assets/knowledge/employees/<id>/{wiki,inbox}/
  wiki  = md 全文注入（frontmatter + 正文原样）
  inbox = JSON 单据 → parseInboxRecord()（字段裁剪：7 元数据 + body 知识正文）
        → shouldInjectInboxRecord()（仅 open 或近 7 天 closed；陈旧 closed 过滤）
```

- 安全门：源只读（仅 readFileSync/statSync）；dry-run 不建库不写库；`getKnowledgeDbPath` + enforceProjectIsolation 跨项目拒绝。
- 幂等：content_hash 唯一键 upsert；hash 变更按 source_path 重写；**空文件 → 删除既有行**（防陈旧知识注入）。
- `agentFilter`：watch 增量按目录名过滤（契约层与内容层同过滤）。
- 内容根解析 `resolveContentRoot()`：四候选路径推导（覆盖 sourceRoot 为仓根或 source-agents 根的生产形态），内容层未部署 → null 不阻断契约层。
- 报告 `KnowledgeSyncReport`：scanned/inserted/skipped/removed/filtered/wouldInsert/errors——dry-run 下 wouldInsert=scanned（不查库的保守口径）。

### 8.3 注入：injectKnowledgeContext()（inject.ts）

boot injection（非检索）：`listLatestDocuments(namespace, agentId)` → `buildKnowledgeContextBlock()` 组装 `<knowledge-context namespace sources>` 块 → 追加 systemPrompt 之后 → 每文档写一行 knowledge_consumption（消费记录是审计面）。

- **层序**：Memory → Colleagues → Social → Wiki → Inbox（knowledge-db.ts `KNOWLEDGE_LAYERS` 定义顺序）。
- **来源语义标签**：块头 `sources` 属性列实际注入层；节标题带域后缀 `(contract)` / `(content)`——消费侧凭此区分 curated 内容层与契约层。
- **降级语义**：知识库不存在 / 无该员工知识 / 注入异常 → 原 prompt 原样返回（injected=false），不阻断会话。
- **注入不污染身份真源**：contract-resolver.getSystemPrompt 保持 soul+agent_body 不变，注入只发生在消费挂接点。

**三挂接点**：

| 挂接点 | 位置 | 说明 |
| --- | --- | --- |
| ① 主路径 | `src/company/session-initializer.ts` `initializeSession()` | SessionConfig 组装后追加注入块 |
| ② system-prompt 端点 | `src/server/app.ts`（GET /agents/{id}/system-prompt） | 直接调用注入 |
| ③ heartbeat 会话 | `src/heartbeat/agent-runner.ts` `injectHeartbeatKnowledge()` | 会话创建前注入（session_id 可知） |

### 8.4 指标：metrics.ts

- `recordKnowledgeMetric()`：轻量埋点（开库→写→关库；失败降级 warn 不阻断），event ∈ escalation_blocked / routing_error。
- `isEscalationBlockReason()`：tool_blocked reason 是否越权类——权限引擎/合同边界拒绝计入；用户交互拒绝（"User denied permission"）排除；执行异常/重复失败不计。
- `getKnowledgeMetricSnapshot()`：分子（counts）+ 分母（consumptionTotal / documentsTotal）+ 会话覆盖素材（withSession / distinctSessions / total）。端点 `GET /internal/v1/knowledge/metrics` 只读。
- 验证基线：29/29 新用例 + 475/474（TUI 既有 fail）+ tsc 零错误；真实数据冒烟 11 agent × 3 层 = 33 文档同步。

## 9. 调用链速查表（新人查路用）

| 我想…… | 读什么 |
| --- | --- |
| 看 CLI 有哪些参数 | `build_parser()`（source_publish_check.py:2691） |
| 看参数怎么互斥 | `main()` 第 3270-3305 行 |
| 改渲染形状 | `HOST_RENDER_REGISTRY` / `_render_frontmatter_for_host` |
| 加一个新宿主 | `HostRenderSpec` 注册 + 白名单；管线零改动 |
| 改报告合同 | `ADE_ACTIONS` / `ADE_ACTIONS_PER_SCOPE` / 各 `_serialize_*_report` |
| 看 Close 校验规则 | `_validate_close_inputs` / `run_close` |
| 看评分判定 | `score_assessment` / `_find_item_evidence` |
| 看事件触发 | `run_event_scan_once` / `_event_derive_scopes` / `_event_run_scope_check` |
| 改知识同步 | `syncKnowledgeFromSource`（sync.ts） |
| 改注入块形状 | `buildKnowledgeContextBlock` / `knowledgeContextTag`（inject.ts） |
| 改上岗门禁 | `getRoleRosterStatus` / `enforceRoleActive`（staffing.ts） |

## 10. 测试与验证方式

| 层 | 命令 / 方式 | 基线 |
| --- | --- | --- |
| CLI 回归 | `python -m unittest runtime.cognition.source_publish_check_validation -v` | 43+（项目文档域）；全量含 event-watch 等 |
| 上岗 gating | `npm test`（TriLC）+ 小柯独立 HTTP 实测 | 24 新用例 + 452/451 |
| 知识注入 | knowledge-injector 单测 | 29/29 + 475/474 |
| 评分实证 | `docs/engineering/fade-papers/` 评分 JSON（FADE-001..004/006） | 五实例 PASS（90 / 93 复评 / 80 / 88 复评 / 91 增评） |
| 端到端 | 小柯 FADE 端到端测试（隔离 daemon + curl） | 派工 409 三态 / 可见性全量 / cron skipped / degraded 三态 |

手动验证建议：先跑 dry-run 断言"无写入"，再跑 execute 断言"before/after 哈希 + 审计记录"；评分先跑纯覆盖（无 quality scores）看 omission，再合并质量分看 verdict 翻转。

## 11. 成熟度标注与观察项（写教程时的诚实记录）

以下为 2026-08-20 写教程时发现的实现/文档差异，如实列出（这正是手动审核的价值）：

1. **spec §6.1 滞后**：spec v1.1.9 案例表已并两行（§六），但 §6.1"项目真源文档同步 ADE"一节仍写"尚待补齐：文件/Git 事件触发、runId、Plan/Close Skill 装载、Close CLI、持久状态机"——与实现现状（event-watch、显式 run-id、Close CLI、Score CLI 全落地）冲突，该节未随 v1.1.8/1.1.9 同步。（**2026-08-21 spec v1.2.1 已核销**：§6.1 对齐实现现状，已落地项划销、自动触发增强独立立项。）
2. **spec §10 过时**："既有 FADE 实例补齐试卷与评分（FADE-ASSESS-20260818-001 待办）"已过时——2026-08-20 四实例均已评分（90/90/80/88）。（**2026-08-21 spec v1.2.1 已核销**：§10 短期待办标注完成 + 两复评〔FADE-004 88 / FADE-002 93〕登记。）
3. **FADE-005 编号漂移**：`TriMetaverse/docs/execution/fade-005-roster-gating-spec.md` 自述"上岗 gating 规范（FADE-005）"，但整合提案（§三 ADE-B）与登记册明确"避免另立 FADE-005，并入 FADE-004 员工域"；登记册无 FADE-005 条目。文件名/标题编号与登记册不一致，建议改名或加注"FADE-ASSESS-005 工作包，并入 FADE-004"。（**2026-08-21 批 2 已收敛**：文件名保留兼容历史引用，标题与头注已标"FADE-ASSESS-20260819-005 工作包 · 并入 FADE-004"。）
4. **event-watch scope 未入 spec**：`EVENT_WATCH_SCOPE="event-watch"` 是第四个 envelope scope（触发面审计 scope），spec §2.2 只写三业务域；代码注释已声明"复用合同不进 ADE_SCOPES"，spec 未提及此面，建议 §2.2 补一行。（**2026-08-21 spec v1.2.1 已核销**：§2.2 补 event-watch 触发面审计 scope 一行。）
5. **知识注入消费记录粒度**：spec（knowledge-injection-spec.md §五）写"每次注入写 knowledge_consumption 一行"，实现为"每文档写一行"（consumed=docs.length，inject.ts 第 133-142 行）；实现更细粒度属合理演进，spec 表述待同步。
6. **注入层序文档差**：spec §五写注入块"按 Memory→Colleagues→Social 顺序"（三层），实现已扩展五层（+wiki/inbox 内容层，KNOWLEDGE_LAYERS）；内容层为批次 3-2 新增，spec 未同步。（**2026-08-21 已收敛**：knowledge-injection-spec v2.0 五层顺序已同步。）
7. **CHO_ALLOWED 含 ceo**：staffing.ts 审批白名单含 `'ceo'`（第 181 行），spec/规范文档只写"CHO 门（非 CHO 审批人 403）"；CEO 代批是超集行为，文档未声明，建议明确"CEO 代批为兼容行为"或收紧。
8. **旧教程状态过时**：`project-source-document-sync-ade-tutorial.md` 状态仍为"当前 DCE 可用教程；完整 ADE 生命周期待实现"，与实际（runId/Close CLI/Score CLI/event-watch 全落地）不符，建议更新或标注版本差。（**2026-08-28 已收敛**：改名 `project-source-document-sync-fade-tutorial.md`，状态句与真源链接对齐 v2.0.x + 实现现状，V2.0。）
9. **本教程自身基线滞后（已收口）**：v1.0 对应 v1.1.9 时代基线，遗留 §2 标题"CLI 面总览"歧义（实为 FADE-002 单实例）、envelope 未标降格、FADE-006 缺行、ADE_ACTIONS 计数过时（13→15）——2026-08-28 v1.1 同步全部处理，本条留档。

## 12. 真源回链与学习顺序

1. 规范：[FADE 协议：Agent 确定性执行全生命周期规范](../engineering/fade-protocol-spec.md)（先读 §一、§2、§8；v2.0.0 起替代 ade-pattern-spec.md，旧路径为重定向桩）
2. 历史整合设计：[ADE 四候选整合提案](../engineering/ade-consolidation-proposal.md)（理解发布域/员工域两域为什么这么分，ADE-A/ADE-B 为历史代号）
3. 登记册：[FADE 成熟实例登记册](../engineering/fade-registry.md)（每实例的段-实现映射表——查某实例载体先看这里）
4. 试卷模板：[FADE 试卷模板](../engineering/fade-assessment-paper-template.md)（评分合同的结构真源）
5. 实现：`TriCompany/runtime/cognition/source_publish_check.py` → `TriLC/src/company/staffing.ts` → `TriLC/src/knowledge-injector/`；编排面（FADE-006）：`TriMetaverse/docs/execution/fade-pipeline-design.md`
6. 测试：`runtime/cognition/source_publish_check_validation.py` + TriLC 各模块单测
7. 入门篇：[fade-beginner-course.md](fade-beginner-course.md)；使用篇：[fade-product-guide.md](fade-product-guide.md)
