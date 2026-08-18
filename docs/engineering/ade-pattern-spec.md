# ADE 模式：Agent 智能任务确定性执行规范

版本：v1.1.3
日期：2026-08-18
状态：当前工程规范

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/ade-pattern-spec.md
- syncMode: source-only
- lastSyncedAt: 2026-08-18

来源：源侧发布架构实战总结 + 官方行业资料 + CPO/CTO owner contract 视角 + CEOChiefOfStaff 收口
参照标准：Microsoft Conductor（MIT）、MCP Protocol（Anthropic）、Azure Agent Orchestration Patterns
适用：TriCompany 所有涉及 CLI 执行 + 审计要求的研发智能任务

变更记录：

- v1.1.3（2026-08-18）：一致性收口——评分两段全面落位：§2.1 分层表补 Score CLI/Score Skill、§2.2 评分合同例外、§三 业内对应新增试卷/Score CLI/Score Skill/及格线四行、§八 两 profile 与状态机补评分段、§五/§七/§九 反模式与组合原则同步
- v1.1.2（2026-08-18）：评分拆两段——Score CLI 确定性检查测试集覆盖（是否遗漏），Score Skill 语义评定每项处理质量；生命周期与 §1.1 段数九→十同步，评分 JSON 为两源合并
- v1.1.1（2026-08-18）：试卷固定部分补充**测试集**（CLI 必做工作 + 验证方法，类比大模型测评的评估测试集）；评分明确两维度（是否遗漏 + 每项处理质量），评分 JSON 增加 omission 字段；§2.6 更名"首尾对标"（试卷在首、评分在尾）
- v1.1.0（2026-08-18）：新增 §2.6 首尾对标（试卷—答卷—评分）——Plan Skill 声明实例试卷、Score CLI 确定性评分、双门槛及格线；生命周期图与 §1.1 升格口径同步（FADE 必要条件 + 评分通过，段数八→九）；新增试卷模板文档
- 版本号注记（2026-08-18）：按功能演进改采语义化版本，原 v1.0~v1.7 历史条目重编为 v1.0.0~v1.0.7（仅编号重排，内容未动）；跨文档引用同步重编号
- v1.0.7（2026-08-18）：CEO 手工重写 §一——新增背景段（Agent 智能不确定性 → 固定流程确定性收敛的必要性），定义落位 ADE（Agentic Deterministic Execution）协议本体并挂接 FADE（Full-cycle ADE）完整周期实例，增补"智能化确定性执行"定语，明确智能/CLI 分工，强调固定流程的智能、可靠、可审计与可恢复执行
- v1.0.6（2026-08-18）：强化 §一 模式定义——点明 Agent 智能执行结果的不确定性问题，落位 FADE 组合优势（智能发现 → 确定性执行 → 智能审核 → CLI 收口），核心一句话：按固定流程可靠执行和收口
- v1.0.5（2026-08-18）：CEO 定名 FADE（Full-cycle ADE）；新增 §1.1 完整周期实例定义、三档区分与 fade-registry.md 登记册立册（本行补录，原提交遗漏）
- v1.0.4（2026-08-07）：基于行业资料与 CPO/CTO 联审，将 ADE 升级为事件驱动全生命周期协议；新增 runtime-owned durable / Agent-owned interactive 两个 profile，明确 DCE 只是执行阶段，统一 `Close Skill -> Close CLI -> 终态`
- v1.0.3（2026-08-07）：新增项目真源文档同步 ADE；复用 `source_publish_check`，增加 manifest 驱动的 `published-copy` / `published-summary` 分域
- v1.0.2（2026-07-24）：新增自动化测试、自动化部署为典型 ADE 场景；扩展场景选择指南
- v1.0.1（2026-07-24）：新增 §七 ADE vs Skill 对比与边界、§八 组合模式；修正 MCP 对应描述；CEOCS/CPO/CTO 联合评审通过
- v1.0.0-draft（初始稿）：ADE 三层架构、核心原则、业内标准对应、适用场景、反模式、实践案例

---

## 一、模式定义

背景: Agent 智能执行天然存在不确定性，直接依赖 Agent 完成所有任务可能导致结果不可预测、难以审计和恢复。一些固定流程的操作如果能够通过智能/程序化触发、确定性执行和严格收口机制来完成，就可以将不确定性降到最低，从而保证系统的可靠性和可审计性。

定义：**ADE（Agentic Deterministic Execution）是智能化确定性执行的 Agent 全生命周期执行协议，FADE（Full-cycle ADE）即该协议的完整周期实例：采用“智能发现 → 确定性执行 → 智能审核 → CLI 收口”的核心模式，由 Agent 负责发现与审核的智能环节，由 CLI 负责执行与收口的程序环节，从而实现固定流程的智能触发、可靠执行、可审计与可恢复。**

协议的全部机制（runId、状态机、安全门、终态门、恢复与重试）均服务于这一分工。

ADE：

```text
Agent plans -> Deterministic CLI executes -> Agent closes
```

FADE（完整周期 ADE）：

```text
事件或 Agent 检测
-> 程序登记事件、去重并生成 runId
-> Agent Qualify
-> Plan Skill 生成结构化计划（含实例试卷：检查项 + 标准 + 及格线）
-> DCE（Deterministic CLI Executes）
-> Verify CLI（可选）
-> Score CLI 检查测试集覆盖（确定性遗漏检测）
-> Score Skill 评定每项处理质量（语义评分）
-> Close Skill 结合评分形成语义裁决
-> Close CLI 校验裁决并持久化（评分不达线 → RETRY | ESCALATED）
-> APPROVED | FROZEN | ESCALATED | RETRY
```

其中：

- ADE 是整套协议框架。
- DCE 只是确定性执行阶段，不等于 ADE。
- Skill 承载 Plan / Close 阶段的判断方法，可以携带脚本，但不能替代 runtime 状态推进。
- Plan Skill 同时声明实例试卷（检查项、标准、及格线），见 §2.6。
- Score CLI 检查测试集覆盖（确定性遗漏检测），是评分 JSON 的确定性部分。
- Score Skill 按验证方法评定每项处理质量（语义评分），与覆盖检查合并为评分 JSON，作为 Close Skill 裁决的客观证据。
- 评分不达及格线（双门槛）的 run 不得写入终态，回 RETRY 或 ESCALATED。
- Close Skill 是最后的语义判断者；Close CLI 是最后的确定性状态写入者。

### 1.1 FADE：完整周期 ADE 实例（v1.0.5 术语，CEO 2026-08-18 定名）

**FADE（Full-cycle ADE）= 上述完整生命周期十段（事件→登记 runId→Qualify→Plan Skill→DCE→Verify(可选)→Score CLI→Score Skill→Close Skill→Close CLI→终态）全部落地且实跑过、每次执行通过试卷评分（双门槛）的 ADE 实例。**

- ADE 是协议，FADE 是该协议的**成熟实例称号**——就像"ISO 认证"是标准、"通过认证的产线"是实例。
- 区分三档：**FADE**（十段齐、实跑过、评分通过）／ADE 兼容（核心段有、个别段待补，见 §六案例表）／纯 DCE（只有确定性执行，无生命周期）。
- FADE 实例统一登记于 [fade-registry.md](fade-registry.md)（TriCompany 管理）；当前已收编：周工作平面迁移、公司文档管理（tricompany.md 对应的 Agent 监督）、AI共学周记。
- 一个动作升格为 FADE 的验收口径：逐段能指到**真实工件**（触发器配置、runId 载体、skill 承载文档、CLI 命令、审计记录、终态样本），缺段即降档；且必须带**完整试卷**（固定文档 + 实例声明）与**评分通过记录**（Score CLI 覆盖检查 + Score Skill 质量评分 + 双门槛判定），不允许口头宣称。

## 二、核心原则

### 2.1 智能与确定性的分离

| 层 | 负责 | 特点 |
| --- | --- | --- |
| Runtime | 事件、runId、状态机、恢复、重试与强制收口 | 持久、可恢复 |
| Plan / Close / Score Skill | 规划、语义裁决与质量评定 | 灵活但非确定性 |
| DCE / Verify CLI | 执行、校验与证据报告 | 确定、可复现 |
| Score CLI | 覆盖检查（遗漏检测） | 确定、可复现 |
| Close CLI | 裁决校验、状态转换与审计落账 | 终态写入 |

**关键约束**：Agent 不直接执行受治理的副作用或写入终态。业务副作用通过 DCE，最终状态通过 Close CLI；覆盖检查通过 Score CLI，质量评定通过 Score Skill；确定性报告一律出自 CLI。

### 2.2 DCE / Verify CLI 必须输出结构化自检报告（Score CLI 输出评分合同）

任何 ADE 模式下的 CLI 必须输出包含以下字段的 JSON（**Score CLI 例外**：输出 §2.6 评分合同，见[试卷模板](fade-assessment-paper-template.md) §三）：

```json
{
  "status": "pass|fail|partial",
  "summary": { "total": N, "changed": N, "errors": N },
  "changes": [{ "action": "...", "target": "...", "before": "...", "after": "..." }],
  "errors": [{ "item": "...", "reason": "..." }],
  "check_time": "ISO8601"
}
```

Close Skill 以此报告为主要客观证据，可以结合批准的上下文做语义裁决，但不得伪造或覆盖 CLI 证据。

### 2.3 可审计性要求

- CLI 每次执行输出 JSON → 可被 Agent 解析 → 可写入 sync-log
- 变化前后对比（before/after）必须在报告中
- 执行时间戳必须记录
- 异常必须显式标记（errors 数组非空时 status=fail）

### 2.4 安全门

- CLI 必须有 `--dry-run` 或等效模式（默认不写入）
- 写入操作需要显式参数（如 `--sync`、`--agent-execute`）
- 保护目标（protected targets）必须在 CLI 层硬编码，不依赖 Agent 判断

### 2.5 终态门

- Close Skill 先输出结构化裁决：`APPROVE | FREEZE | ESCALATE | RETRY`。
- Close CLI 校验裁决格式、证据引用、source revision、状态转换和权限。
- Close CLI 通过后才写入终态；校验失败进入 `CLOSE_REJECTED`，不得静默完成。
- 位于 Close Skill 之前的 CLI 只能称为 DCE、Verify CLI、Score CLI 或 evidence finalizer，不能提交不可逆终态。

### 2.6 首尾对标：试卷—答卷—评分（FADE 必备）

每个 FADE 实例必须配齐"试卷、答卷、评分"三件套，用于评估每次执行效果：

- **试卷（考什么）**：实例检查清单与评判标准。固定部分：§1.1 工件清单、实例专属规范文档、**测试集**（CLI 必做工作 + 验证方法，提前备好）、[试卷模板](fade-assessment-paper-template.md)；实时部分：Plan Skill 阶段由 Agent 按实例声明的检查项、权重与及格线（具备实时性）。
- **答卷（答得怎样）**：本次执行的证据集——runId 记录、DCE / Verify CLI 结构化报告、Score CLI 覆盖检查与 Score Skill 质量评分输出、审计日志、终态样本。
- **评分（多少分）**：两段合成——**Score CLI** 按测试集**确定性检查覆盖**（是否遗漏 → omission / required_all_passed）；**Score Skill** 按验证方法**语义评定每项处理质量**（逐项 score，灵活但非确定性）。合并输出结构化评分 JSON（item / score / max / evidence_ref / omission + 总分），位于 Close Skill 之前，作为其裁决的客观证据。
- **及格线（多少分过）**：**双门槛**——必选项全部通过（Score CLI 确定性判定）且 总分达标（阈值由实例声明）。不达线进入 `RETRY` 或 `ESCALATED`，不得写入终态。

评分留存即 FADE 每次执行效果的量化记录。

## 三、与业内标准的对应

| 本规范 | Microsoft Conductor | MCP Protocol | Azure Agent Patterns |
| --- | --- | --- | --- |
| Runtime 状态机 | Workflow / graph | Host 层自行实现 | Orchestration runtime |
| Plan / Close / Score Skill | Workflow 中的 Agent step | Host 注入上下文 | Agent plans / closes / judge |
| DCE / Verify CLI | Deterministic step | MCP Tools 可承载调用 | Tool executes |
| Score CLI | Deterministic eval step（断言式检查） | MCP Tools 可承载调用 | Evaluation tool / policy check |
| Score Skill | LLM-as-judge（语义评分） | Host 注入上下文 | Evaluator agent / judge 模式 |
| 试卷 / 测试集 | 评估基准（benchmark / eval set） | MCP 不定义 | AI Foundry 评估基准 / eval set |
| 及格线（双门槛） | Workflow gate / termination | MCP 不定义 | Guardrail / policy gate |
| Close CLI | Workflow terminal transition | Host 负责 | Durable state commit |
| 日志 / 恢复 | Checkpoint / workflow state | MCP 不定义 | Traceability / recovery |

**差异点**：ADE 在同一状态机中混合 Skill 驱动的 Agent 判断与 CLI 驱动的确定性阶段。MCP Tools 可以承载 DCE / Verify / Score CLI，但 MCP 不定义事件去重、run 状态、恢复与强制收口，这些属于 ADE runtime。**评分段的差异**：业界评估多为模型/产物的离线评测（benchmark / eval set 一次性跑分），ADE 的试卷—评分是**运行时内嵌的收口门槛**——试卷在 Plan 阶段按实例声明、评分在每次执行收尾强制执行并留存，及格线作为硬门槛阻断不达标 run 进入终态。

## 四、适用场景

满足以下**任意两项**即应使用 ADE 模式：

1. 涉及文件系统写操作（创建/修改/删除/发布）
2. 需要事后审计（谁改了、改了什么、什么时候）
3. 操作可被自动化重复执行
4. 涉及跨模块/跨仓库同步
5. 操作失败需要可回滚或可追溯
6. 任务需要跨会话恢复、程序唤起或强制进入终态

## 五、反模式（禁止）

| 反模式 | 说明 |
| --- | --- |
| Agent 直接写文件 | 绕过了 CLI 的安全门和自检 |
| CLI 包含 LLM 推理 | 破坏确定性，不可审计 |
| 无自检报告的执行 | 无法验证结果 |
| 无试卷与评分的收尾 | FADE 升格必须带完整试卷与评分通过记录（§1.1） |
| Agent 推断 CLI 结果 | 必须读取结构化报告，不做"猜测" |

## 六、已有实践案例

| 案例 | Agent | CLI | 模式 |
| --- | --- | --- | --- |
| 源侧→发布侧同步 | 小赛 | `source_publish_check --check --sync --scope` | DCE 已实现；完整 ADE 待补 lifecycle |
| 项目真源文档同步 | 小贾（plan/close）+ 小乔/小狄联审 | `source_publish_check --project-docs [--project-docs-execute]` | DCE 已实现；两个 ADE profile 已裁决 |
| Agent live entry 发布 | 小赛 | `source_publish_check --publish-agents --agent-execute` | DCE 已实现；完整 ADE 待补 lifecycle |
| 自动化测试（按用例） | 小柯（TestEngineer） | `pytest --json-report` 或 `validation.py` 输出结构化结果 | 推荐 ADE 模式 |
| 自动化部署（按步骤） | 小布（DeploymentEngineer） | 部署 CLI 按步骤执行、逐步骤自检报告 | 推荐 ADE 模式 |
| IPD 全流程（10 阶段） | CPO/CTO/总助×TriDev | `ipd_case_engine.py` 驱动阶段 + `record_gate()` 门禁 + `ipd_case_validation.py` 校验 | 接近 ADE lifecycle，待统一 Skill / Score / Close CLI 合同 |
| 员工对象发布 | CHO | `employee_host_publish` | DCE 已实现；完整 ADE lifecycle 待补 |

### 6.1 项目真源文档同步 ADE

项目真源同步当前已落地 DCE，与既有 source -> support 发布共用一个 CLI，但不共用目录扫描逻辑：

- `published-copy` 由 CLI 做字节级复制。
- `published-summary` 由小贾规划候选，小乔核产品语义，小狄核 revision 与安全门，CLI 校验后写目标。
- 默认 dry-run；只有 `--project-docs-execute` 才允许写入。
- 清单、命令和收口状态见 `../workflow/project-source-document-sync-ade.md`。

尚待补齐：文件 / Git 事件触发、runId、Plan / Close Skill 装载、Close CLI、持久状态机和恢复机制。行业资料与联审裁决见 [ADE 生命周期行业模式联审](ade-lifecycle-industry-review.md)，跨 TriLC / TriMC / Trees 的完整落位见 [ADE 全生命周期实现蓝图](ade-full-lifecycle-implementation-plan.md)。

### 6.2 IPD 与 ADE 的同构关系

IPD 的 10 阶段（DISCOVERY → INTELLIGENCE → DESIGNING → CODING → VERIFY-INTEGRATION → REDTEAM → QA → DEPLOYMENT → ASSURANCE → DELIVERY）已经具备 ADE 的阶段状态、执行、门禁与审计雏形：

| IPD 组件 | ADE 对应层 | 当前状态 |
| --- | --- | --- |
| `businessOwner` / `actingOwner` 规划阶段目标 | Agent 规划层 | ✅ 已有 |
| `ipd_case_engine.py` 驱动阶段推进 | CLI 执行层 | ✅ 已有 |
| `record_gate()` 门禁通过/冻结记录 | CLI 自检 | ✅ 已有 |
| `ipd_case_validation.py` 校验证据完整性 | CLI 自检 | ✅ 已有 |
| `gateOwner` 审阅证据、放行/冻结 | Agent 收口层 | ✅ 已有 |
| through-pass checklist + gate ledger | 审计日志 | ✅ 已有 |

**待规范化**：阶段输出未统一为 ADE JSON 自检格式；gate 判断仍在 Agent 做语义推断；before/after 未自动记录。

## 七、ADE、Skill 与 CLI 的边界

### 7.1 Skill 的本质

Skill 是供 Agent 装载的方法、知识与能力包。它可以只包含提示规则，也可以携带脚本、schema 和测试。

因此，携带确定性脚本的 Skill 可以封装 DCE 能力；真正不能由 standalone Skill 单独保证的是：

- 外部事件登记与去重。
- 持久 `runId` 和状态机。
- 跨会话恢复、超时与重试预算。
- 执行完成后必定重新唤起 Close Skill。
- Close CLI 成功前不得进入终态。

### 7.2 ADE 与 standalone Skill 对比

| 维度 | ADE 生命周期 | Standalone Skill |
| --- | --- | --- |
| 本质 | 事件驱动、可恢复、必须终态化的 orchestration 协议 | Agent 可按需装载的能力包 |
| 触发 | 文件、Git、cron、webhook、用户或 Agent 检测 | 用户、Agent 或宿主匹配 |
| 生命周期 owner | Runtime 或已登记的 Agent session | 当前 Agent / session |
| 执行 | 可装配 Skill、DCE、Verify / Score CLI、Close CLI | 可含提示、脚本和工具调用 |
| 跨会话恢复 | 协议要求 | 取决于外部宿主 |
| 强制收口 | Close Skill 后必须经 Close CLI | Skill 本身不能保证再次被唤起 |
| 审计 | run 级事件、状态、证据与终态 | 通常是单次 Skill / Agent 执行记录 |

### 7.3 什么时候只用 Skill，什么时候进入 ADE

| 场景 | Standalone Skill | ADE 生命周期 |
| --- | --- | --- |
| 代码审查方法、写作方法、教学话术 | 适合 | 通常不需要 |
| 一次性、无副作用、当前会话内可完成 | 适合 | 可选 |
| 文件同步、发布、部署、账务 | 可作为 Plan / Close 组件 | 应使用 |
| watcher、Git hook、cron、CI 触发 | 不足以持有生命周期 | 应使用 runtime-owned profile |
| Agent 在会话内发现并立即处理 | 可负责检测与规划 | 使用 Agent-owned profile |
| 跨会话、可恢复、必须有最终裁决 | 不能单独保证 | 必须使用 |

### 7.4 Skill、DCE 与 Close CLI 的组合原则

- Skill 可以携带或调用 DCE 脚本，但确定性算法只能有一个 canonical 实现。
- Plan Skill 输出结构化计划；Close Skill 输出结构化语义裁决；Score Skill 输出结构化质量评分。
- DCE / Verify CLI 产生客观证据，不提交不可逆终态；Score CLI 产生确定性覆盖检查（是否遗漏）。
- 评分 JSON 由 Score CLI 覆盖检查与 Score Skill 质量评分合并，是 Close Skill 裁决的客观输入。
- Close CLI 位于 Close Skill 之后，负责最终状态转换和审计落账。
- 业务审批不能被 CLI 安全门替代；CLI 只证明动作与裁决符合机器合同。

## 八、两个 ADE 生命周期 Profile

行业中同时存在 Agent tool loop 与 durable workflow，但通常由一套 orchestration/runtime 通过不同入口和 topology 承载。TriCompany 因此保留一套 ADE 协议、两个 profile，不复制状态机、CLI、manifest 或审计 schema。

### 8.1 Runtime-owned durable

```text
程序事件
-> Runtime 登记、去重并生成 runId
-> Agent Qualify
-> Plan Skill
-> DCE
-> Verify CLI（可选）
-> Score CLI
-> Score Skill
-> Close Skill
-> Close CLI
-> 终态
```

适用：文件 watcher、Git hook、webhook、cron、CI、异步长任务、跨会话恢复和强审计任务。

Runtime 持有 run，Agent 中断或宿主重启后仍须恢复到 `CLOSING` 或终态。

### 8.2 Agent-owned interactive

```text
Agent 检测
-> 程序登记事件并生成 runId
-> Plan Skill
-> DCE
-> Verify / Evidence CLI（可选）
-> Score CLI
-> Score Skill
-> Close Skill
-> Close CLI
-> Agent 向用户输出最终说明
```

适用：当前会话中的临时任务、上下文密集判断、低延迟处理和需要 Agent 立即解释结果的任务。

这里位于 Close Skill 之前的 CLI 是 Verify / Evidence CLI 与 Score CLI，不是终态 Close CLI。Agent 可以负责最终用户说明，但只有 Close CLI 可以把 run 写入终态。

### 8.3 统一状态机

```text
DETECTED
-> QUALIFYING
-> PLANNING
-> PLANNED
-> EXECUTING
-> VERIFYING
-> SCORING
-> CLOSING
-> FINALIZING
-> APPROVED | FROZEN | ESCALATED | RETRY
```

两个 profile 只改变 `triggerOwner`、`lifecycleOwner`、唤起方式和最终展示方式，共用：

- `runId`、source revision 与幂等键。
- Plan / Close / Score Skill 版本引用。
- DCE、Verify / Score CLI 与 Close CLI 合同。
- 重试预算、checkpoint 和审计 schema。

### 8.4 行业依据与联审裁决

官方资料对照、小乔产品视角、小狄技术视角和最终裁决见 [ADE 生命周期行业模式联审](ade-lifecycle-industry-review.md)。

### 8.5 TriLC / TriMC 双域同构

两个 lifecycle profile 与本地域 / 服务域正交：TriLC 和 TriMC 都必须能运行 Runtime-owned 与 Agent-owned profile，并消费同一个 `@trimetaverse/agent-core` ADE runtime。

- TriLC 与 TriMC 共享状态机、Plan / Close / Score Skill runner、DCE / Verify / Score CLI / Close 合同、checkpoint 和 recovery policy。
- 本地域只增加文件/Git/本地 cron、SQLite、TUI 和离线工具 adapter。
- 服务域只增加 webhook/CI、PostgreSQL、服务端 Signal 和集群 worker adapter。
- 每个 run 通过 `homeDomain / writeAuthority / authorityEpoch / version` 维持唯一写主；代码共享不等于运行时双活写入。
- TriLC 已有类 Claude Code 能力优先抽象进共享 runtime，再由 TriMC 同步消费，不在服务域重写第二套。

完整边界见 [TriLC / TriMC 共享 Runtime Parity 决策](trilc-trimc-runtime-parity.md)。

## 九、实施要求

### 新建 CLI 工具时

1. 必须输出结构化 JSON
2. 必须包含 `--help` 和 `--dry-run`（或等效安全默认）
3. 必须有配套的 validation suite（pytest/unittest）
4. 必须在 `sync-log.md` 或等效审计日志中记录每次执行
5. Score CLI 必须输出 §2.6 评分合同（覆盖检查 + 及格线判定）

### 新建 Agent 时

1. 涉及写操作的职责必须声明对应的 CLI 工具
2. 收口时必须读取 CLI 的结构化输出
3. 异常时必须升级到 owner，不静默处理
4. 承载评分职责的 Skill（Score Skill）必须声明评分方法、证据引用与及格线

## 十、演进方向

- **短期**：~~`employee_host_publish` 补齐结构化自检报告~~ ✅ 已完成（2026-07-24）；既有 FADE 实例（FADE-001~004）补齐试卷与评分（周工作平面 FADE-ASSESS-20260818-001 待办）
- **中期**：探索 YAML-based workflow 定义（参照 Conductor），将 Agent 规划层进一步结构化
- **长期**：多宿主适配时，CLI 层增加 host adapter，Agent 层不变

---

> 本规范由 TriCompany 源侧发布架构实战总结，参照 Microsoft Conductor（MIT 协议）、MCP Protocol（Anthropic 开源）、Azure Agent Orchestration Patterns 制定。
