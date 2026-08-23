# 原版 Claude Code spawn/resume/context 机制结论与 TriCompany 公司化改进创新记录

版本：V1.0
日期：2026-08-23
状态：初版登记（CEO 会话直落；归口 CTO 技术真源域，待 CTO 复核）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/claude-code-spawn-resume-context-innovation-record.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-08-23

## 1. 文档定位

本文有双重身份：

1. **外部机制事实登记**：对原版 Claude Code（CC）2.1.88 源码的 spawn / resume / 上下文机制调查结论，全部带 file:line 证据。
2. **公司化改进创新记录**：把 TriCompany 在"员工连续性与记忆治理"上相对原版 CC 的设计改进，正式登记为创新点，作为赛博公司改造原版宿主的创新资产之一。

调查起点：2026-08-23 CEO 会话提问"员工（如小贾）作为 subagent 的上下文究竟多大、长任务多轮 SendMessage 会不会自己爆掉"。调查方法：`../TriMetaverse/reference/claude-code-2.1.88/` 源码静态阅读 + claude-api 权威参考（缓存日期 2026-06-24）交叉验证。

本文只登记机制结论与创新对应关系；TriLC / TriMC 移植侧的对应缺口（如 auto-compact 未移植）由 cc-fidelity 审计线另行跟踪，不混入本记录。

## 2. 原版 Claude Code 机制结论（外部事实登记）

### 2.1 上下文窗口事实

| 模型 | 上下文窗口 | 备注 |
| --- | --- | --- |
| Claude Fable 5 | 1M | 1M 即默认，无需配置；128K max output |
| Claude Opus 5 / 4.8 / 4.7 / 4.6 | 1M | 现役 Opus 全系 |
| Claude Sonnet 5 / 4.6 | 1M | 现役 Sonnet 全系 |
| Claude Haiku 4.5 | 200K | 现役表中唯一 200K |

来源：claude-api 权威参考模型表（缓存 2026-06-24）。

> 勘误留痕：2026-08-23 之前某会话（GLM-4.7-Flash 执行）曾连续三轮误报 Fable 5 / Opus 4.8 为 200K，且在网搜无结果时伪造过来源链接。该教训已存入项目记忆 `llm-limits-never-from-memory`（模型上下文/价格/发布事实禁凭训练记忆回答）。此处登记以防结论再次被旧先验污染。

### 2.2 三条生成路径的上下文语义

核心规则：**subagent 的上下文窗口 = 它运行的那个模型的窗口，与"怎么生出来的"无关。**

| 生成路径 | 模型解析 | 窗口 | 起始占用量 | 证据 |
| --- | --- | --- | --- | --- |
| Agent tool fork（省略 subagent_type 或 subagent_type: "fork"） | 强制继承父模型，model 覆盖被忽略 | = 父模型（1M） | = 父会话当前 token 占用量（父用 400K 则子带 400K 起跑，剩 ~600K 干活） | `forkSubagent.ts:51-52`（注释原话 "model: 'inherit' keeps the parent's model for context length parity"）、`:60-71`（FORK_AGENT 定义）、`:65`（maxTurns: 200） |
| Agent tool spawn（subagent_type 指定，如小贾/小狄） | 解析顺序：调用方 model 参数 > agent 定义 frontmatter model > 继承父 | 解析结果模型的窗口 | ≈ 0（自身 system prompt + 任务指令起步） | `AgentTool.tsx:86`（schema 描述）；本仓 18 个员工 frontmatter 均未写 model 字段 → 全部继承会话模型 |
| /branch 会话 fork | 会话模型不变 | = 模型窗口 | = 全部历史（transcript 整体复制到新 session） | `commands/branch/branch.ts`（297 行，纯 FS 操作；结论引自 cc-fidelity p6 审计 `p6-architecture-plan.md:225-232`） |

唯一降到 200K 的路径：spawn 时显式 `model: "haiku"` → Haiku 4.5。

### 2.3 SendMessage → resume：全量回灌机制

这是本轮调查的关键发现，也是常驻员工的累积根源：

- 给命名 agent 发 SendMessage，若该 agent 已结束，**会从其 transcript 恢复（resume）后再执行**（环境 Agent tool 规格原文："a send resumes it from its transcript"）。
- resume 读取**全部累积 transcript**，仅过滤三类残缺消息（纯空白 assistant / 孤儿 thinking-only / 未解决 tool_use），**没有任何压缩步骤**。
- 因此：命名 agent = 跨 SendMessage 单调增长的累积会话。每次 send = 全历史回灌 + 新消息追加。

证据：`resumeAgent.ts:63-74`（`getAgentTranscript` 全量读取 + 三重过滤后整链作为起始上下文）。

### 2.4 三层防线与各自盲区

| 防线 | 机制 | 证据 | SendMessage 常驻场景下的盲区 |
| --- | --- | --- | --- |
| auto-compact | 阈值 ≈ 967K（1M − 20K 摘要预留 − 13K buffer）；位于共享 `query()` 循环，subagent 经 `runAgent()` 走同一循环 → **subagent 同样有 auto-compact**；compact 服务按 agentId 感知设计 | `autoCompact.ts:28-49`（有效窗口公式）、`:62-91`（阈值）、`query.ts:453-468`（循环内触发）、`runAgent.ts:15`（复用 query）、`compact.ts:1471-1497`（agentId 感知） | ① 单轮巨量注入（如读入大文件）：历史一轮内跳过窗口 → 压缩自身的摘要请求携带超窗历史 → `prompt_too_long` → 连败 3 次熔断；② 单条消息 > 窗口：无压缩可救；③ resume 回灌：累积 transcript + 新消息可能在首次调 API 前已超窗（部分推断：全量回灌已实证，首调前的检查时序未逐行追踪） |
| maxTurns（fork 默认 200） | 限制单次运行的轮数 | `forkSubagent.ts:65` | 管单 run 不管跨 resume 累积；每次 send 各有额度，累积无上限 |
| 熔断器 / 硬错误 | 连续压缩失败 3 次后停止重试 | `autoCompact.ts:67-70` | 不是防线，是失败终点——熔断打开后停在错误态 |

**生产实锤**（熔断器注释原文，`autoCompact.ts:67-70`）：BQ 2026-03-10 统计，1,279 个会话出现 50 次以上连续压缩失败（单会话最高 3,272 次），全局每天浪费约 25 万次 API 调用——熔断器正是为此事后新增。证明"突破防线"在原版生产环境中真实、大量发生。

### 2.5 爆掉之前先退化、先烧钱

- **有损退化**：每次 compact 丢细节。常驻 agent 被压缩数轮后遗忘早期裁决、口径漂移——不是报错式"爆"，是质量塌方式"爆"。
- **缓存全 miss**：每次 resume 本可靠 prompt cache 缓解全历史重付，但压缩会改写前缀 → cache 全部失效 → 下次全价重算。满窗 resume 输入成本 ≈ $10/次（1M × Fable 5 输入价 $10/1M tokens）。

## 3. TriCompany 公司化改进创新记录

### 3.1 原版的结构性缺口（对赛博公司场景）

原版 CC 的 subagent 设计假设是**一次性任务执行器**：spawn → work → report → done，上下文随结束释放。在该假设下三层防线自洽。

但赛博公司需要的是**员工连续性**：一旦用"命名常驻 agent + SendMessage"承载员工，就进入原版未治理的区域——上下文跨任务单调累积、被动有损压缩、缓存反复全 miss、可熔断。原版没有"员工连续性不依赖会话上下文"的制度层，这正是公司化改造要补的位。

### 3.2 创新点登记

| # | 创新点 | 内容 | 相对原版的价值 | 落点 |
| --- | --- | --- | --- | --- |
| 1 | 记忆外置原则 | 员工连续性由 employee knowledge workspace、registry、OP records 等文件资产承载，不依赖 session transcript 存活 | 规避 2.3 全量回灌累积与 2.5 退化/烧钱双风险 | `docs/workflow/tricompany-agent-roles.md` §3.6（"每个 Agent 必须可替换，不能靠隐性上下文生存"，V0.1 2026-03-24 即确立）；`docs/engineering/cyber-company-four-layer-memory-collaboration-system.md`（身份/阶段/共享/审计四层） |
| 2 | 任务作用域员工实例（spawn-per-task） | 每次任务新 spawn 近空上下文起步，读文件重建认知；不用"一条命到底"的常驻命名 agent 承载全部工作 | 起点即规避跨 resume 累积；1M 窗口留给当前任务而非历史包袱 | 各员工 agent 定义"认知分层约束"节（如 `source-agents/ceo-chief-of-staff/` 五件套：阶段记忆/工作关系由 workspace 承载，不靠会话） |
| 3 | 收口落盘 → 重生循环 | 任务结束即收口落盘（会议收口/日常收口 prompt + 收口 commit 卫生 + 长任务分段落盘），agent 完结；下次新实例接手 | 用**主动、显式、无损**的落盘替代原版**被动、有损**的 auto-compact 作为记忆延续机制 | `.github/prompts/结束会议.prompt.md`、`日常收口.prompt.md`；`docs/workflow/cyber-company-secretariat.md` |
| 4 | registry 认知重建入口 | 重生实例的认知重建走 registry 路由（治理/产品/代码三层），不靠会话回忆 | 实例可替换性与认知完整性解构；重建成本 = 定向读文件，非全历史重付 | TriMetaverse `CLAUDE.md` Registry Routing；`docs/registry/*.md` |
| 5 | 分身 HC 编制机制（分身派工协议） | 岗位-员工分离：岗位说明 = JD 固定资产，分身实例 = 在岗员工；小贾需求判定提交 CLONE_STAFFING_REQUEST → CHO 增员审批（HC 总量 + 按域分账 placement）→ 编排层 spawn；超时回收 + 裁撤审批 | 把"开新空白上下文实例"从编排层技术技巧升格为 CHO 治理的组织编制流程；长任务拆为多个短命分身 + checkpoint 接续，正面化解 2.4 熔断风险（协议根问题原文即"长任务 transcript 膨胀 context 耗尽，三次实证事故"） | `../TriMetaverse/docs/execution/clone-dispatch-protocol.md`（v0.3，2026-08-22）+ `clone-dispatch-technical-plan.md` + `candidate-staffing-fade.md`（FADE 评估） |

### 3.3 机制对照表

| 原版机制 | 公司化对应 | 效果 |
| --- | --- | --- |
| session transcript 跨 send 累积 | 四层记忆外置 | 员工连续性不受会话生死影响 |
| 常驻命名 agent（SendMessage 累积） | spawn-per-task + 收口落盘 | 无跨任务累积、无退化、无熔断风险 |
| auto-compact（被动、有损、可熔断） | 主动落盘收口（显式、无损、可控） | 记忆不丢细节，触发时机由制度而非阈值决定 |
| prompt cache miss 全价重付 | 近空上下文起步 + registry 定向读取 | 每次只付增量认知成本 |
| 单 agent 长任务（3-5h）累积爆窗 / 熔断 | 分身 HC 机制：多短命实例并行 + checkpoint 接续 | 长任务不靠单会话续命，风险在节点边界切断 |

### 3.4 边界声明（不夸大）

- 不声称原版 CC"设计错误"：其一次性任务执行假设自洽，三层防线在该假设内有效。
- 公司化改进是**场景适配**：赛博公司的员工连续性 + 低成本 + 可审计需求，决定了必须外置记忆；这是需求驱动的架构选择，不是对原版的纠错。
- 创新点 1-5 均为**既有制度的显式命名与登记**（最早可溯 2026-03-24 agent-roles V0.1；创新点 5 可溯 2026-08-17 clone-dispatch v0.2），本文首次把它们与原版机制逐项对齐成对照关系。

## 4. 验证与置信度标注

| 结论 | 置信度 | 依据 |
| --- | --- | --- |
| 模型窗口表（Fable 5 / Opus 4.8 = 1M） | 高 | claude-api 权威参考（缓存 2026-06-24） |
| 三条生成路径的模型解析与起始占用 | 高 | 源码静态证据（2.2 表内 file:line） |
| SendMessage → resume 全量回灌、无压缩 | 高 | `resumeAgent.ts:63-74` 源码 |
| auto-compact 阈值公式、熔断器、生产数据 | 高 | `autoCompact.ts` 源码及注释 |
| subagent 亦有 auto-compact | 高（静态）/ 未运行时实测 | 共享 `query()` 循环 + compact 服务 agentId 感知设计 |
| resume 回灌首次调 API 前的压缩检查时序 | 中（推断） | 全量回灌已实证；时序未逐行追踪 |

**后续观察项**：spawn 一个 subagent 持续读大文件逼近 1M，实测 sidechain transcript 是否出现 compact_boundary 消息（`runAgent.ts:238` 的 `SystemCompactBoundaryMessage` 即记录此事件），闭环验证"subagent 亦有 auto-compact"。

## 5. 证据清单

- 模型窗口与 API 行为：claude-api 权威参考（缓存 2026-06-24；含 Fable 5 "1M context window (the maximum is also the default), 128K max output" 原文）
- CC 2.1.88 源码（`../TriMetaverse/reference/claude-code-2.1.88/`）：
  - `src/tools/AgentTool/forkSubagent.ts:51-52, 60-71, 93, 107-169`
  - `src/tools/AgentTool/AgentTool.tsx:86`（model 参数 schema）
  - `src/tools/AgentTool/resumeAgent.ts:63-74`
  - `src/tools/AgentTool/runAgent.ts:15, 238`
  - `src/utils/forkedAgent.ts:131-141, 345-462, 489-524`
  - `src/services/compact/autoCompact.ts:28-49, 62-91`（含 :67-70 生产数据注释）
  - `src/services/compact/compact.ts:1471-1497`
  - `src/query.ts:453-468`
- TriCompany 制度真源：`docs/workflow/tricompany-agent-roles.md` §3.6；`docs/engineering/cyber-company-four-layer-memory-collaboration-system.md`
- cc-fidelity 审计（branch 机制旁证）：TriMetaverse `docs/workflow/operating-records/2026-W31/cc-fidelity/p6-architecture-plan.md:225-232`
- 调查过程记录：2026-08-23 CEO 会话（UTC 12:16 / +08 20:16），本文件即其收口产物

## 变更记录

- 2026-08-23：初版。CEO 会话直落，登记外部机制结论四组（窗口事实/生成路径/resume 回灌/防线盲区）与创新点四项；归口 CTO 技术真源域，待 CTO 复核。
- 2026-08-23：v1.0.1 增量——CEO 提示补全创新点 5（分身 HC 编制机制，clone-dispatch-protocol v0.3）；同根问题（防单 agent context 耗尽）的既有最成型方案纳入对照。
