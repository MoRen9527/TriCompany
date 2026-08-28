# FADE 协议：Agent 确定性执行全生命周期规范

版本：v2.0.0（2026-08-28：架构重构——**ADE 概念退役**，FADE（Full-cycle Agentic Deterministic Execution）升为协议本体，FADE-XXX 为协议实例的具体实现；运行标识术语统一；envelope 降格为发布域参考实现；六实例联审（CPO/CTO/CEOCS 常设席位）全部裁决整合）
日期：2026-08-21（原立）/ 2026-08-28（重构）
状态：当前工程规范

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/fade-protocol-spec.md（**自 v2.0.0 起替代 ade-pattern-spec.md**，旧文件为重定向桩）
- syncMode: source-only
- lastSyncedAt: 2026-08-28

来源：源侧发布架构实战总结 + 官方行业资料 + CPO/CTO owner contract 视角 + CEOChiefOfStaff 收口；v2.0.0 整合 FADE 六实例反向工程（CPO/CTO 联审常设席位机制首跑）
参照标准：Microsoft Conductor（MIT）、MCP Protocol（Anthropic）、Azure Agent Orchestration Patterns
适用：TriCompany 所有涉及 CLI 执行 + 审计要求的研发智能任务
**联审机制（CEO 2026-08-27 立）**：本规范及 fade-registry 等协议类文档的立法与修订，须 **CPO（小乔）/CTO（小狄）/CEOCS（小贾）三方常设席位**联审；审毕方可修改——席位常设，缺位须记录原因。

变更记录：

- v2.0.1（2026-08-28，CEO 提案：双轨时刻制）：§2.3 补机器轨/人读轨分轨口径（JSON 合同 UTC Z 不变；面向人的 markdown 报告/台账对齐北京时间，可括注 UTC 原值；§2.7 机读核心与散文节两轨并存合法）
- **v2.0.0（2026-08-28，架构重构·CEO 提案）**：① **ADE 概念退役**——"FADE（Full-cycle Agentic Deterministic Execution）是 Agent 确定性执行的全生命周期协议的泛化部分，FADE-XXX 是该协议实例的具体实现"；原"ADE 协议框架 / FADE 成熟实例称号"双层表述废止，三档改为 FADE 完整实例 / FADE 兼容档 / 纯确定性执行脚本；② **运行标识术语统一**——协议层一律称「运行标识」（=登记段四不变量聚合键；显式 runId 字符串为其实现形态之一，§2.8），正文 14 处 runId 硬编码全部泛化，`--run-id` 参数名 / envelope `run_id` 字段名 / 历史变更条目按冻结口径保留；③ **envelope 降格**——envelope v1.0 从普适强制降格为发布域参考实现（FADE-002 声明载体），协议不变量抽出为"结构化/守恒/退出码/action 契约化"四条普适条款（CPO R-B1）；④ **节点收口报告分类裁定**（CPO R-B2）与答卷/工件清单纳入（R-C3）；⑤ 收编清单对齐登记册五实例（R-B3）；⑥ profile 与载体绑定正交声明（R-C2）、Skill 承载段枚举补 Score（R-C1）、载体示例与 002 补齐项时效修正（R-C5/C6）、登记册头部版本卫生（R-C7）；⑦ §2.8 细则 10「立法完成度」候选条款随册（定级于下次联审）；⑧ 文件迁移 ade-pattern-spec.md → fade-protocol-spec.md（旧路径重定向桩）
- v1.4.2（2026-08-28）：§2.8 新增细则 10「立法完成度」**候选条款**——接线+实测才算立法完成，纸面法不得计入已强制（与 retrospective §三-8 同源，定级于下次联审）；常设联审机制入头部
- v1.4.1（2026-08-27，CPO/CTO 联审修后放行）：§2.7 补校验器强制（node-report-check 前置翻转门+编排双门+Merkle root 纳入 reports/）与条件必填字段（影响面/回滚方法/下游失效范围）；§2.8 补 DCE 载体降级合同、runId 判例收口（等价聚合键+被引用 run 须显式标识）、validation 边界句与齿条三条（入册证据/周检漂移核对/降回扩展）、最小映射 schema、006 复审触发条款、§八 profile 限定升级件；变更记录补 v1.3.0/v1.4.0 两条与本次联审记录
- v1.4.0（2026-08-27）：§2.8 段合同与实现绑定——"协议管不变量、实例管载体"分层立法，裁定 runId 字段非必须而四不变量必须
- v1.3.0（2026-08-27）：§2.7 节点收口报告——FADE 六实例反向工程第一次立法
- v1.2.1（2026-08-21）：册内勘误（CTO 终审批 2 裁决 3①②，FADE-LEFTOVER 关闭条件登记项）——§六 案例表重排（blockquote 移表后修复断表渲染、移除与 FADE-004 扩容重复的"员工对象发布"行、已收编/未收编两区）；§6.1"尚待补齐"对齐实现现状（event-watch/runId/Close CLI 已落地划销，自动触发增强独立立项）；§2.2 补 event-watch 触发面审计 scope（deep-dive 观察项 4）；§10 短期待办核销（四实例评分+两复评）与长期多宿主 adapter 落地标注
- v1.2.0（2026-08-21）：FADE 加固文档收口（FADE-LEFTOVER-20260821-001 批 2，素材取 fade-quality-lessons.md §四）——§2.2 补内容归属校验与跨管线派生（组件-合成）校验入合同；§2.6 评分补治理对齐/内容归属语义维度、试卷固定部分补治理对齐项；§6.2 新增员工域多宿主渲染模型（原 ADE-B，现员工域）；§8.6 补 event-watch 触发探测落地形态
- v1.1.9（2026-08-20）：阶段 3 落位——§六 案例表四行并两行（FADE-002 扩容发布域 / FADE-004 扩容员工域）
- v1.1.8（2026-08-20）：阶段 2 收口勘误——§2.5 终态词表对齐 §8.3（APPROVED/FROZEN/ESCALATED/RETRY）、§2.2 补 close lifecycle scope 与组合容器顶层聚合规则（阶段 2：runId/Close CLI/Score CLI 落位）
- v1.1.7（2026-08-20）：§2.2 统一报告合同（envelope v1.0）落位——三 scope 单解析器可消费、守恒不变量、items 七字段基座、action 词表契约化、errors>0→rc=1、四业务域经三 scope 表达（阶段 1 收口同步落文档）
- v1.1.6（2026-08-19）：§8.6 补 daemon 层触发链两模式——定时巡检链（cron 唤起小赛巡检→写入周平面待办标注闲时执行→daemon 与小贾定期取任务自动执行）／即时触发链（指令→小赛立即触发→小贾建树）
- v1.1.5（2026-08-19）：新增 §8.6 Trees 任务树融合——Agent 探测机制（指令 / registry / codegraph / 文件修改扫描 / 探测）扩展触发源、编排层建树多员工参与、checkpoint 与运行标识状态机衔接、触发与执行解耦；§四 适用场景补多员工协作项
- v1.1.4（2026-08-19）：§六 案例表滞后修正——候选 1/2 标注已收编、候选 3 标注并入发布域；挂接四候选整合提案（发布域 + 员工域两域，CEO 采纳）
- v1.1.3（2026-08-18）：一致性收口——评分两段全面落位：§2.1 分层表补 Score CLI/Score Skill、§2.2 评分合同例外、§三 业内对应新增试卷/Score CLI/Score Skill/及格线四行、§八 两 profile 与状态机补评分段、§五/§七/§九 反模式与组合原则同步
- v1.1.2（2026-08-18）：评分拆两段——Score CLI 确定性检查测试集覆盖（是否遗漏），Score Skill 语义评定每项处理质量；生命周期与 §1.1 段数九→十同步，评分 JSON 为两源合并
- v1.1.1（2026-08-18）：试卷固定部分补充**测试集**（CLI 必做工作 + 验证方法，类比大模型测评的评估测试集）；评分明确两维度（是否遗漏 + 每项处理质量），评分 JSON 增加 omission 字段；§2.6 更名"首尾对标"（试卷在首、评分在尾）
- v1.1.0（2026-08-18）：新增 §2.6 首尾对标（试卷—答卷—评分）——Plan Skill 声明实例试卷、Score CLI 确定性评分、双门槛及格线；生命周期图与 §1.1 升格口径同步（评分通过，段数八→九）；新增试卷模板文档
- 版本号注记（2026-08-18）：按功能演进改采语义化版本，原 v1.0~v1.7 历史条目重编为 v1.0.0~v1.0.7（仅编号重排，内容未动）；跨文档引用同步重编号
- v1.0.7（2026-08-18）：CEO 手工重写 §一——新增背景段（Agent 智能不确定性 → 固定流程确定性收敛的必要性），定义落位协议本体并挂接完整周期实例，增补"智能化确定性执行"定语，明确智能/CLI 分工，强调固定流程的智能、可靠、可审计与可恢复执行
- v1.0.6（2026-08-18）：强化 §一 模式定义——点明 Agent 智能执行结果的不确定性问题，落位组合优势（智能发现 → 确定性执行 → 智能审核 → CLI 收口），核心一句话：按固定流程可靠执行和收口
- v1.0.5（2026-08-18）：CEO 定名 FADE（Full-cycle ADE，v2.0.0 起全称 Full-cycle Agentic Deterministic Execution）；新增完整周期实例定义、三档区分与 fade-registry.md 登记册立册（本行补录，原提交遗漏）
- v1.0.4（2026-08-07）：基于行业资料与 CPO/CTO 联审，升级为事件驱动全生命周期协议；新增 runtime-owned durable / Agent-owned interactive 两个 profile，明确 DCE 只是执行阶段，统一 `Close Skill -> Close CLI -> 终态`
- v1.0.3（2026-08-07）：新增项目真源文档同步；复用 `source_publish_check`，增加 manifest 驱动的 `published-copy` / `published-summary` 分域
- v1.0.2（2026-07-24）：新增自动化测试、自动化部署为典型场景；扩展场景选择指南
- v1.0.1（2026-07-24）：新增 §七 Skill 对比与边界、§八 组合模式；修正 MCP 对应描述；CEOCS/CPO/CTO 联合评审通过
- v1.0.0-draft（初始稿）：三层架构、业内标准对应、适用场景、反模式、实践案例

---

## 一、FADE 协议定义

背景：Agent 智能执行天然存在不确定性，直接依赖 Agent 完成所有任务可能导致结果不可预测、难以审计和恢复。一些固定流程的操作如果能够通过智能/程序化触发、确定性执行和严格收口机制来完成，就可以将不确定性降到最低，从而保证系统的可靠性和可审计性。

定义：**FADE（Full-cycle Agentic Deterministic Execution，Agent 确定性执行全生命周期）是 Agent 确定性执行的全生命周期协议本体**——由「段合同」（每段职责不变量 + 产物合同）与「实现绑定」（实例声明载体，§2.8）构成；**FADE-XXX 是该协议实例的具体实现**。协议采用"智能发现 → 确定性执行 → 智能审核 → CLI 收口"的核心模式，由 Agent 负责发现与审核的智能环节，由 CLI 负责执行与收口的程序环节，从而实现固定流程的智能触发、可靠执行、可审计与可恢复的全生命周期。

协议的全部机制（**运行标识**、状态机、安全门、终态门、恢复与重试）均服务于这一分工。

> **运行标识**：登记段产出的满足唯一性/去重性/关联性/恢复锚四不变量的聚合键（§2.8 登记合同）。显式 runId 字符串是其一种实现形态；jobs.json jobId、manifest 条目、registry 三元组等均为合法形态。实现载体由实例声明（段-实现映射表）。

**分层总纲**：协议层只约束每段职责不变量与产物合同；实现载体由 FADE 实例自由选择并在入册时声明段-实现映射表（§2.8）。

FADE 协议生命周期：

```text
任务说明书拟定与投送（Agent交互/成熟文档+程序化投送；投送后即本 run 的 Plan 输入；触发源：指令 / registry / codegraph / 文件修改扫描 / 探测）
-> 程序登记事件、去重并锚定运行标识、触发执行
-> Agent Qualify 资格审查（机械准入门为其确定性载体，如执行面三重门）
-> Plan Skill（实例化点：协议在此落入具体实例 FADE-XXX，实例间各异）生成结构化执行计划——任务树分解、原材料卷封（sourceMaterials 预封＋开工验卷项）、语义作业方案卷封（智能处理方式与语义检查方法预封，收口对卷基准）、试卷声明（评分标准＋及格线双门槛，§2.6）
-> DCE（Deterministic CLI Executes，确定性执行段；开工验卷为卷封制开工不变量，逐节点门禁随节点收口报告留痕）
-> Verify CLI（可选，独立于执行者的后置校验：构建/测试/一致性门禁）
-> Score CLI 检查测试集覆盖（确定性遗漏检测）
-> Score Skill 评定每项处理质量（语义评分）
-> Close Skill 结合评分形成语义裁决
-> Close CLI 校验裁决并持久化（评分不达线 → RETRY | ESCALATED）
-> APPROVED | FROZEN | ESCALATED | RETRY
```

> 计数注解：任务说明书拟定与投送为生命周期**前置输入**（事件触发段的触发材料与归因锚）；十段计数自事件触发/登记起算。**任务说明书**：发起方拟定的委托文书，承载目标、范围边界、原材料指针与验收期望——拟定途径自由（Agent 交互或既有成熟文档），须经程序化投送方成为生命周期工件；说明书是范围基线，Plan/DCE 期间不得改写，执行中发现冲突即漂移走二选一裁决。历史文档中"计划文档/源计划文档"即其 FADE-006 实例形态（别名注记，历史条目不改）。

其中：

- FADE 是协议本体；**FADE-XXX 是协议实例的具体实现**（登记册在册，如 FADE-001 周平面迁移 … FADE-006 执行面自动拾取）。
- DCE 只是确定性执行段，不等于 FADE。
- Skill 承载 Plan / Score / Close 阶段的判断方法，可以携带脚本，但不能替代 runtime 状态推进。
- Plan Skill 同时声明实例试卷（检查项、标准、及格线），见 §2.6。
- Score CLI 检查测试集覆盖（确定性遗漏检测），是评分 JSON 的确定性部分。
- Score Skill 按验证方法评定每项处理质量（语义评分），与覆盖检查合并为评分 JSON，作为 Close Skill 裁决的客观证据。
- 评分不达及格线（双门槛）的 run 不得写入终态，回 RETRY 或 ESCALATED。
- 检测与执行解耦：探测 Agent（如小赛维护 tricompany）只负责开启触发，执行由编排层按 Trees 任务树拉起对应角色（§8.6）。
- Close Skill 是最后的语义判断者；Close CLI 是最后的确定性状态写入者。

### 1.1 FADE-XXX：协议实例（v2.0.0 术语重构）

**FADE-XXX = FADE 协议的具体实现实例**——十段（事件→登记（运行标识）→Qualify→Plan Skill→DCE→Verify(可选)→Score CLI→Score Skill→Close Skill→Close CLI→终态）全部落地且实跑过、每次执行通过试卷评分（双门槛）。

- 三档：**FADE 完整实例**（十段齐、实跑过、评分通过）／**FADE 兼容档**（核心段有、个别段待补，见 §六案例表）／**纯确定性执行脚本**（只有 DCE，无生命周期）。
- FADE 实例统一登记于 [fade-registry.md](fade-registry.md)（TriCompany 管理）；当前在册五实例：FADE-001 周平面迁移 / 002 发布域 / 003 共学周记 / 004 员工域 / 006 执行面自动拾取（全量与状态见登记册）。
- 升格验收口径：逐段能指到**真实工件**（触发器配置、登记载体、skill 承载文档、CLI 命令、审计记录、终态样本；多节点实例另需节点收口报告 §2.7），缺段即降档；且必须带**完整试卷**（固定文档 + 实例声明）与**评分通过记录**（Score CLI 覆盖检查 + Score Skill 质量评分 + 双门槛判定），不允许口头宣称。

## 二、核心原则

### 2.1 智能与确定性的分离

| 层 | 负责 | 特点 |
| --- | --- | --- |
| Runtime | 事件、运行标识、状态机、恢复、重试与强制收口 | 持久、可恢复 |
| Plan / Close / Score Skill | 规划、语义裁决与质量评定 | 灵活但非确定性 |
| DCE / Verify CLI | 执行、校验与证据报告 | 确定、可复现 |
| Score CLI | 覆盖检查（遗漏检测） | 确定、可复现 |
| Close CLI | 裁决校验、状态转换与审计落账 | 终态写入 |

**关键约束**：Agent 不直接执行受治理的副作用或写入终态。业务副作用通过 DCE，最终状态通过 Close CLI；覆盖检查通过 Score CLI，质量评定通过 Score Skill；确定性报告一律出自 CLI。
**分类裁定（v2.0.0，CPO R-B2）**：节点收口报告（§2.7）为执行会话落盘的审计叙述件，不属于"确定性报告"范畴；其确定性证据（commit/退出码/hash）必须可由 CLI/台账独立复核，报告存在性与齐备性由确定性环节校验（§2.7 校验器）。

### 2.2 结构化报告合同（v2.0.0 拆两层）

**协议不变量（普适，任何 FADE 实例必须满足）**：确定性报告必须 ①结构化、②可守恒校验、③errors>0 时非零退出码（CI 可感知拒绝路径）、④action 词表契约化。**Score CLI 段产物合同为 §2.6 评分合同（试卷模板 §三），与载体无关；发布域经 envelope 时同样适用**（v2.0.1 A9 上移）。

**发布域参考实现（FADE-002 声明载体，其他域经段-实现映射表声明各自报告合同，不必复用 envelope）**——envelope v1.0（实现于 `source_publish_check` 三 scope；**Score CLI 例外**：输出 §2.6 评分合同，见[试卷模板](fade-assessment-paper-template.md) §三）：

```json
{
  "protocol": "ade-report",
  "version": "1.0",
  "scope": "sync|project-docs|publish-agents",
  "run_id": "...（运行标识的显式形态之一，承载规则见 §2.8 细则 6）",
  // 注：protocol 字段值 "ade-report" 为代码级冻结合同，保留历史命名（语义即 FADE 报告合同）
  "mode": "dry-run|execute",
  "check_time": "ISO8601",
  "status": "pass|fail|partial",
  "summary": { "total": N, "changed": N, "skipped": N, "errors": N },
  "items": [ { "action": "...", "source": "...", "target": "...", "before_hash": "...", "after_hash": "...", "scope_key": "...", "error": "..." } ],
  "scope_specific": {}
}
```

参考实现细则（仅约束选择 envelope 的域）：

- **守恒不变量**：`summary.total == len(items)` 且 `summary.total == changed + skipped + errors`，validation 强制
- `items` 七字段为合同基座；域扩展字段为可选附加，消费者状态裁决只可依赖七字段
- `before_hash` / `after_hash` 可为空串；sync 域 hash 证据以 `scope_specific` 为准
- `action` 词表契约化：`ADE_ACTIONS` + 每 scope 允许子集（`ADE_ACTIONS_PER_SCOPE`），validation 强制（action ∈ 词表 ∧ 域白名单）——**常量名保留历史命名**（代码级冻结合同），语义即 action 词表
- 四业务域（sync / project-docs / agent-publish / employee-publish）经三报告 scope 表达——员工域经 `employee_host_publish` 委托复用 publish-agents scope
- `close` 为 lifecycle scope（Close CLI 输出，终态审计），复用合同但不进三业务域词表（`ADE_LIFECYCLE_SCOPES`）
- `event-watch` 为触发面审计 scope（`--event-watch` 单次扫描 / `--watch` 循环输出，fingerprint 与基线语义见 §8.6），同样复用合同不进三业务域词表（`EVENT_WATCH_SCOPE`）——scope 枚举随 lifecycle/watch 扩展以词表常量为准（CTO-F11）
- **内容归属校验入合同**（v1.2.0，FADE 加固 B 项）：角色定义载体（agent-body 组件 / `<id>.agent.md` 合成文件）不得含模板通用纪律句——白名单清单（`FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS`）在 source kit validation 承载，入册条件=该句在现役角色定义中零出现（fade-quality-lessons 建议 2）
- **跨管线派生校验入合同**（v1.2.0，FADE 加固 D 项）：组件（agent-body/soul/contract）→ 合成（`<id>.agent.md`）单向传导逐行校验（改组件必须同步合成，防"改组件不传导渲染"）；多宿主发布 ↔ binding hostEntries 派生一致（B 族校验）；registry 类单文件区经 `SYNTHETIC_PATH_OVERRIDES` 映射覆盖；批量校验 `check-sync --all` 仅枚举组件目录（fade-quality-lessons 建议 3）
- 组合运行输出 `{protocol, version, run_id?, check_time, status, summary, reports: [envelope...]}` 容器——顶层聚合：任一域 `errors>0` → fail（errors 优先）> 任一 partial → partial > pass；summary 四字段直和守恒
- **退出码**：任何 scope `errors>0` → 非零（rc=1），CI 可感知拒绝路径
- 组合运行输出容器时消费方逐 envelope 处理（阶段 2 定聚合决策）

Close Skill 以此报告为主要客观证据，可以结合批准的上下文做语义裁决，但不得伪造或覆盖 CLI 证据。

### 2.3 可审计性要求

- CLI 每次执行输出 JSON → 可被 Agent 解析 → 可写入 sync-log
- 变化前后对比（before/after）必须在报告中
- 执行时间戳必须记录（**机器轨**：ISO8601 UTC Z；**人读呈现**走 D-04 v4 双轨时刻制——面向人的报告/台账对齐北京时间，可括注 UTC 原值）
- 异常必须显式标记（errors 数组非空时 status=fail）

### 2.4 安全门

- CLI 必须有 `--dry-run` 或等效模式（默认不写入）
- 写入操作需要显式参数（如 `--sync`、`--agent-execute`）
- 保护目标（protected targets）必须在 CLI 层硬编码，不依赖 Agent 判断

### 2.5 终态门

- Close Skill 先输出结构化裁决：`APPROVED | FROZEN | ESCALATED | RETRY`（与 §8.3 终态词表一致）。
- Close CLI 校验裁决格式、证据引用、source revision、状态转换和权限。
- Close CLI 通过后才写入终态；校验失败进入 `CLOSE_REJECTED`，不得静默完成。
- 位于 Close Skill 之前的 CLI 只能称为 DCE、Verify CLI、Score CLI 或 evidence finalizer，不能提交不可逆终态。
- **实例映射表声明的确定性载体（如 FADE-006 的 tick 台账回收器）视为该实例的 Close CLI 形态**；被裁决会话不得自证终值（v1.4.1 CTO-F7）。

### 2.6 首尾对标：试卷—答卷—评分（FADE 必备）

每个 FADE 实例必须配齐"试卷、答卷、评分"三件套，用于评估每次执行效果：

- **试卷（考什么）**：实例检查清单与评判标准。固定部分：§1.1 工件清单、实例专属规范文档、**测试集**（CLI 必做工作 + 验证方法，提前备好）、**治理对齐项**（v1.2.0：职责范围 / 绑定事实与最新治理定调一致——防"评分查证据存在性、不查内容与治理事实对齐"的漏过，fade-quality-lessons 案例 1）、[试卷模板](fade-assessment-paper-template.md)；实时部分：Plan Skill 阶段由 Agent 按实例声明的检查项、权重与及格线（具备实时性）。
- **答卷（答得怎样）**：本次执行的证据集——运行标识记录、节点收口报告（多节点实例，§2.7）、DCE / Verify CLI 结构化报告、Score CLI 覆盖检查与 Score Skill 质量评分输出、审计日志、终态样本。
- **评分（多少分）**：两段合成——**Score CLI** 按测试集**确定性检查覆盖**（是否遗漏 → omission / required_all_passed）；**Score Skill** 按验证方法**语义评定每项处理质量**（逐项 score，灵活但非确定性），评定维度含**治理对齐 / 内容归属**（v1.2.0：内容是否属于该角色、职责范围与绑定事实是否与最新治理定调一致——fade-quality-lessons 建议 2）。合并输出结构化评分 JSON（item / score / max / evidence_ref / omission + 总分），位于 Close Skill 之前，作为其裁决的客观证据。
- **及格线（多少分过）**：**双门槛**——必选项全部通过（Score CLI 确定性判定）且 总分达标（阈值由实例声明）。不达线进入 `RETRY` 或 `ESCALATED`，不得写入终态。

评分留存即 FADE 每次执行效果的量化记录。

### 2.7 节点收口报告（v1.3.0 增补，2026-08-27 六实例反向工程立法）

多节点任务包（树）中，**每个节点完成时必须在任务目录内落结构化收口报告** `reports/node-<NODE-ID>.md`——它是 DCE 与 Close 之间的强制接口，承载两大职能：

- **断电恢复**：任意新会话接续时，读该报告即可在节点粒度无损接续（树状态给"到哪一步"，节点报告给"那一步内部发生了什么"）；
- **审计**：逐节点动作/工件/门禁证据链，杜绝"过程黑箱"。

必备十字段（缺任一即视为节点未收口，状态翻转无效）：

| # | 字段 | 说明 |
| --- | --- | --- |
| 1 | nodeId / agent | 节点标识与执行角色 |
| 2 | startedAt / finishedAt | 起止时刻，UTC Z 后缀 |
| 3 | 基线 commit | 开工时工作仓 HEAD |
| 4 | 触发来源 | tick id + trigger（hook/cron/manual） |
| 5 | 动作序列表 | 时刻 \| 动作 \| 对应 commit 三列 |
| 6 | 工件清单 | 每件 path + 行数/字节数或 hash（先写后报证据） |
| 7 | 门禁结果 | 实际执行的命令 + 退出码（npm test/tsc 等） |
| 8 | 异常与处置 | 发生了什么阻塞/异常、如何处置、若 blocked 引用分层取证记录 |
| 9 | 断点交接 | 若中途被回收：接续者需要知道的最小上下文 |
| 10 | 使用依据 | 本报告引用的源文件/日志清单 |

出处：FADE-006 执行面自动拾取实例（P0 战役八实例）暴露的过程黑箱缺口；反向工程全文见 `TriMetaverse/docs/execution/fade-instances-retrospective.md`。

**执行与校验（v1.4.1 联审强制，CTO-F1/CPO-F15）**：
- 状态翻转前置门——置 done 前必须运行校验器 `node-report-check`（exit≠0 不得翻转）；编排层收口对全部节点复跑（双门）；
- **结构化核心**：报告内嵌 ```json fenced 块承载机读核心（nodeId/agent/startedAt/finishedAt/baselineCommit/trigger/actions/artifacts/gateResults 九键），散文节承载异常处置/断点交接/使用依据——机器可校验与叙事并存；
- **条件必填**：节点产物进入发布面或真源时，报告必须标注影响面与回滚方法；有下游依赖必须声明失效范围；
- 战役 Merkle root 快照范围**纳入 reports/ 目录**（报告本身入完整性基线）。

### 2.8 段合同与实现绑定（v1.4.0 立法，v2.0.0 术语对齐）

**动机**：前六实例同段异构——登记段就有显式 runId / manifest / registry 三元组 / jobs.json 四种载体。实践证明这**不违反协议**，但长期缺乏明文判据（"runId 是否必须"争议即源于此）。立法原则：**协议管不变量，实例管载体**。

**分层模型**：

```text
协议层（FADE）  ：十段各定义「职责不变量 + 产物合同」——必须满足，与载体无关
实例层（FADE-XXX）：每段选择具体实现载体，入册时声明「段-实现映射表」
```

**十段合同速写**（每段的不变量底线）：

| 段 | 合同不变量 |
| --- | --- |
| 事件触发 | 可重放、可归因（谁/何时/何事件）；首要载体=任务说明书程序化投送 |
| 登记 | **四不变量：唯一性（一次运行单一标识可引用）/ 去重性（同事件重复到达不产生新运行）/ 关联性（十段工件可据此聚合成审计链）/ 恢复锚（断点续接可据此定位现场）** |
| Qualify | 机械可判定或语义判定留痕（按 profile 限定，细则 9） |
| Plan | 结构化计划（任务树分解＋两类卷封：原材料/语义作业方案）+ 试卷声明（§2.6） |
| DCE | 确定性、可复现、结构化自检报告（发布域参考实现 envelope 见 §2.2；agent 会话载体降级合同见细则 4） |
| Verify | （可选）独立于执行者的**后置**校验；前置门禁属 Qualify 机械门（细则 9）与 DCE 开工验卷（卷封制） |
| Score CLI | 覆盖遗漏检测确定性可复算 |
| Score Skill | 逐项语义分 + evidence_ref |
| Close Skill | 语义终裁引用评分证据 |
| Close CLI | 终态持久化 + 合同校验（§2.5） |

> **语义作业方案卷封**：Plan 阶段对每个工作项预封的智能处理方式与语义检查方法清单——"做完且做对"的语义判定基准；与原材料卷封（输入完整性基准）构成对偶。不变量：Plan 时点冻结、DCE 期间不可变、收口必须对卷。

**合法载体示例（非穷尽）**——登记段：显式运行标识 --run-id（发布域，2026-08-21 复评核销）/ journal runId（共学周记）/ requestId+runId（员工域）/ jobs.json jobId + per-run 日志（周迁移）/ registry (treeId,tick,pid) 三元组 + hook.log（执行面）。

**立法细则**（v1.4.1 联审修订；v2.0.0 术语对齐）：

1. 每段协议只约束不变量与产物合同，**不约束载体命名与形态**；
2. 实例入册时附「段-实现映射表」——最小 schema 三字段：`段名 / 载体类型与形态 / 不变量满足证据引用`（CPO-F11：以最小交付替代"schema 化"宣称）；
3. **validation 边界（CTO-F5/F11）**：产物合同层（envelope/评分合同）封闭可校验、validation 强制；**载体层开放枚举不入 validation**——合规性=映射表声明 + 周检"声明载体 vs 实际载体"漂移核对；
4. **载体降级合同（CTO-F2）**：agent 会话承载 DCE 时，DCE 不变量降级为"先写后报 + 原子即提交 + §2.7 节点收口报告即产物合同"，envelope 义务仅及于会话内调用的确定性 CLI（FADE-006 即此形态）；
5. 载体显式度分级：**单一显式标识 > 分散组合**——多段复杂实例推荐显式运行标识（FADE-002 复评 7→10 实证）；
6. **判例收口（CTO-F4/CPO 有界例外）**：runId **单一字段非必须，等价聚合键必须**——无显式 runId 实例，其 envelope `run_id` 必须承载映射表声明的等价键（如 jobId+ISO 时间戳）；**被评分卷宗/周检报告/跨实例战役引用的 run 必须可被单一显式标识引用**，跨实例战役强制战役级关联键（战役 Merkle root 惯例正式化）；
7. **齿条三条（CPO-F5）**：(a) 入册映射表须附不变量满足证据（机器可复算检查或工件引用，对齐 §1.1 口径）；(b) 周检增加声明/实际载体漂移核对；(c) "两次周检未补即降回"规则扩展覆盖不变量违反情形；
8. **006 复审触发（CPO-F6）**：§2.7/§2.8 反向自 FADE-006，而 006 首评 80 卡线且完整评分挂周检——006 补评若暴露结构性缺陷（非扣分修补），本两节强制回联审复审；补评期限对齐两次周检齿条；
9. **profile 限定（CPO-F2 和解）**：确定性拾取门为 runtime-owned/自动触发 profile 的强制不变量；Agent-owned/interactive profile 允许语义判定留痕（本节 Qualify 行与 §8 两 profile 的和解口径）；
10. **★立法完成度（候选条款，v1.4.2 增补——与 retrospective §三-8 同源，定级于下次联审）**：审出的缺陷写进法条只是及格线——**接线（执行路径真实存在）+ 实测（模拟或真跑证伪过）才算立法完成**。未接线的法条一律标注"纸面法"并列入工程窗清单跟踪，不得计入"已强制"。判例×2：§2.7 节点报告（纸面法被 CTO-F1 证伪 → node-report-check 校验器+翻转前置门+双门落地）；harvest-rc 匹配器（首版被模拟证伪 → 数字前 14 位对齐修正）。

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

**差异点**：FADE 在同一状态机中混合 Skill 驱动的 Agent 判断与 CLI 驱动的确定性阶段。MCP Tools 可以承载 DCE / Verify / Score CLI，但 MCP 不定义事件去重、run 状态、恢复与强制收口，这些属于 FADE runtime。**评分段的差异**：业界评估多为模型/产物的离线评测（benchmark / eval set 一次性跑分），FADE 的试卷—评分是**运行时内嵌的收口门槛**——试卷在 Plan 阶段按实例声明、评分在每次执行收尾强制执行并留存，及格线作为硬门槛阻断不达标 run 进入终态。

## 四、适用场景

满足以下**任意两项**即应使用 FADE 协议：

1. 涉及文件系统写操作（创建/修改/删除/发布）
2. 需要事后审计（谁改了、改了什么、什么时候）
3. 操作可被自动化重复执行
4. 涉及跨模块/跨仓库同步
5. 操作失败需要可回滚或可追溯
6. 任务需要跨会话恢复、程序唤起或强制进入终态
7. 任务需多员工协作或跨角色交接（Trees 任务树编排，见 §8.6）

## 五、反模式（禁止）

| 反模式 | 说明 |
| --- | --- |
| Agent 直接执行业务副作用写操作 | 绕过了 CLI 的安全门和自检（审计叙述件除外，见 §2.1 分类裁定） |
| CLI 包含 LLM 推理 | 破坏确定性，不可审计 |
| 无自检报告的执行 | 无法验证结果 |
| 无试卷与评分的收尾 | FADE 升格必须带完整试卷与评分通过记录（§1.1） |
| Agent 推断 CLI 结果 | 必须读取结构化报告，不做"猜测" |

## 六、已有实践案例

**已收编（登记册在册实例域，全量清单见登记册）**：

| 案例 | Agent | CLI | 模式 |
| --- | --- | --- | --- |
| 公司发布管理（发布域：源侧→发布侧同步 + 项目真源文档同步 + Agent live entry 发布） | 小赛 / 小贾·小乔·小狄联审 | `source_publish_check --check / --project-docs / --publish-agents [--host=...]` | FADE-002（历史域代号发布域-A） |
| 员工上岗与对象发布（员工域：候选岗位发布 + 员工对象发布） | CHO / 小贾 | staffing API + `employee_host_publish` | FADE-004（历史域代号员工域-B）；多宿主渲染模型见 §6.2 |

> 四候选整合评估（发布域 + 员工域两域，CEO 2026-08-19 采纳）见 [ade-consolidation-proposal.md](ade-consolidation-proposal.md)。（原"员工对象发布"独立行已并入上行 FADE-004 扩容〔2026-08-19 整合定调〕，v1.2.1 勘误移除重复行并修复本注切断表格的渲染。）

**未收编候选（推荐 FADE 模式 / 候补升格观察区）**：

| 案例 | Agent | CLI | 模式 |
| --- | --- | --- | --- |
| 自动化测试（按用例） | 小柯（TestEngineer） | `pytest --json-report` 或 `validation.py` 输出结构化结果 | 推荐 FADE 模式 |
| 自动化部署（按步骤） | 小布（DeploymentEngineer） | 部署 CLI 按步骤执行、逐步自检报告 | 推荐 FADE 模式 |
| IPD 全流程（10 阶段） | CPO/CTO/总助×TriDev | `ipd_case_engine.py` 驱动阶段 + `record_gate()` 门禁 + `ipd_case_validation.py` 校验 | 接近 FADE lifecycle，待统一 Skill / Score / Close CLI 合同（同构分析见 §6.3） |

### 6.1 项目真源文档同步

项目真源同步当前已落地 DCE，与既有 source -> support 发布共用一个 CLI，但不共用目录扫描逻辑：

- `published-copy` 由 CLI 做字节级复制。
- `published-summary` 由小贾规划候选，小乔核产品语义，小狄核 revision 与安全门，CLI 校验后写目标。
- 默认 dry-run；只有 `--project-docs-execute` 才允许写入。
- 清单、命令和收口状态见 `../workflow/project-source-document-sync-ade.md`。

尚待补齐（v1.2.1 勘误更新，对齐实现现状）：Plan / Close Skill 结构化装载、持久状态机与跨会话恢复机制（落位见实现蓝图）。~~文件 / Git 事件触发、runId、Close CLI~~ 已落地——触发探测 event-watch（§8.6，单次扫描 + 循环）、运行标识显式化（`--run-id`，FADE-002 复评核销）、Close CLI（`--close` 终态审计）；文件 / Git 事件**自动触发增强**为独立工程项（automation-backlog，CTO 2026-08-21 裁决）。行业资料与联审裁决见 [生命周期行业模式联审](ade-lifecycle-industry-review.md)，跨 TriLC / TriMC / Trees 的完整落位见 [全生命周期实现蓝图](ade-full-lifecycle-implementation-plan.md)。

### 6.2 员工域多宿主渲染模型（v1.2.0）

员工 / registry 定义发布到宿主侧采用多宿主渲染模型——当前两宿主（copilot / claude）是该模型的实例，未来任何新宿主 = 宿主注册表新增条目，不新增发布流程：

- **宿主注册表（HOST_RENDER_REGISTRY）**：每宿主一条——渲染模板 + live manifest + 保护白名单。copilot 为**字节保真复制面**（byte-preserve copy-surface，源侧合成文件原样落盘）；claude 为**渲染面**（render-surface：工具名映射 + `CLAUDE_HOST_TOOL_ALLOWLIST` 硬白名单，未映射工具剔除并记 `tool_drops` 审计）。
- **发布 CLI**：`--host={copilot|claude}`，默认 dry-run、`--agent-execute` 才写入；显式 `--run-id` 承载运行标识（发布域 run 的核销证据）。
- **派生纪律**：live 产物带派生标记禁人工编辑（claude 面 CLAUDE_DERIVED_MARKER）；binding profile `hostEntries` 与发布管线派生一致（B 族校验）；组件 → 合成 → live 三层单向传导（§2.2 跨管线派生校验）。
- **保护链**：白名单 ∩ 保护域 = ∅ 硬校验；非精确落区即禁区（翻转逻辑）；路径逃逸防护（resolve + relative_to + 静态 `..` 检查）。

### 6.3 IPD 与 FADE 的同构关系

IPD 的 10 阶段（DISCOVERY → INTELLIGENCE → DESIGNING → CODING → VERIFY-INTEGRATION → REDTEAM → QA → DEPLOYMENT → ASSURANCE → DELIVERY）已经具备 FADE 的阶段状态、执行、门禁与审计雏形：

| IPD 组件 | FADE 对应层 | 当前状态 |
| --- | --- | --- |
| `businessOwner` / `actingOwner` 规划阶段目标 | Agent 规划层 | ✅ 已有 |
| `ipd_case_engine.py` 驱动阶段推进 | CLI 执行层 | ✅ 已有 |
| `record_gate()` 门禁通过/冻结记录 | CLI 自检 | ✅ 已有 |
| `ipd_case_validation.py` 校验证据完整性 | CLI 自检 | ✅ 已有 |
| `gateOwner` 审阅证据、放行/冻结 | Agent 收口层 | ✅ 已有 |
| through-pass checklist + gate ledger | 审计日志 | ✅ 已有 |

**待规范化**：阶段输出未统一为协议 JSON 自检格式；gate 判断仍在 Agent 做语义推断；before/after 未自动记录。

## 七、FADE、Skill 与 CLI 的边界

### 7.1 Skill 的本质

Skill 是供 Agent 装载的方法、知识与能力包。它可以只包含提示规则，也可以携带脚本、schema 和测试。

因此，携带确定性脚本的 Skill 可以封装 DCE 能力；真正不能由 standalone Skill 单独保证的是：

- 外部事件登记与去重。
- 持久运行标识和状态机。
- 跨会话恢复、超时与重试预算。
- 执行完成后必定重新唤起 Close Skill。
- Close CLI 成功前不得进入终态。

### 7.2 FADE 与 standalone Skill 对比

| 维度 | FADE 生命周期 | Standalone Skill |
| --- | --- | --- |
| 本质 | 事件驱动、可恢复、必须终态化的 orchestration 协议 | Agent 可按需装载的能力包 |
| 触发 | 文件、Git、cron、webhook、用户或 Agent 检测 | 用户、Agent 或宿主匹配 |
| 生命周期 owner | Runtime 或已登记的 Agent session | 当前 Agent / session |
| 执行 | 可装配 Skill、DCE、Verify / Score CLI、Close CLI | 可含提示、脚本和工具调用 |
| 跨会话恢复 | 协议要求 | 取决于外部宿主 |
| 强制收口 | Close Skill 后必须经 Close CLI | Skill 本身不能保证再次被唤起 |
| 审计 | run 级事件、状态、证据与终态 | 通常是单次 Skill / Agent 执行记录 |

### 7.3 什么时候只用 Skill，什么时候进入 FADE

| 场景 | Standalone Skill | FADE 生命周期 |
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

## 八、两个 FADE 生命周期 Profile

行业中同时存在 Agent tool loop 与 durable workflow，但通常由一套 orchestration/runtime 通过不同入口和 topology 承载。TriCompany 因此保留一套 FADE 协议、两个 profile，不复制状态机、CLI、manifest 类载体或审计 schema。

> **正交声明（CPO R-C2）**：两 profile 与 §2.8 段-实现绑定相互正交——profile 定义 triggerOwner / lifecycleOwner（谁触发、谁持有生命周期）；实例仍按 §2.8 声明各段载体。

### 8.1 Runtime-owned durable

```text
程序事件
-> Runtime 登记、去重并锚定运行标识
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
-> 程序登记事件并锚定运行标识
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

两 profile 共享合同：运行标识（含幂等键）、source revision 与终态词表；Plan / Close / Score Skill 版本引用；各段产物合同（§2.2 / §2.6 / §2.5）；重试预算、checkpoint 与审计 schema。

### 8.4 行业依据与联审裁决

官方资料对照、小乔产品视角、小狄技术视角和最终裁决见 [生命周期行业模式联审](ade-lifecycle-industry-review.md)。

### 8.5 TriLC / TriMC 双域同构

两个 lifecycle profile 与本地域 / 服务域正交：TriLC 和 TriMC 都必须能运行 Runtime-owned 与 Agent-owned profile，并消费同一个 `@trimetaverse/agent-core` runtime。

- TriLC 与 TriMC 共享状态机、Plan / Close / Score Skill runner、DCE / Verify / Score CLI / Close 合同、checkpoint 和 recovery policy。
- 本地域只增加文件/Git/本地 cron、SQLite、TUI 和离线工具 adapter。
- 服务域只增加 webhook/CI、PostgreSQL、服务端 Signal 和集群 worker adapter。
- 每个 run 通过 `homeDomain / writeAuthority / authorityEpoch / version` 维持唯一写主；代码共享不等于运行时双活写入。
- TriLC 已有类 Claude Code 能力优先抽象进共享 runtime，再由 TriMC 同步消费，不在服务域重写第二套。

完整边界见 [TriLC / TriMC 共享 Runtime Parity 决策](trilc-trimc-runtime-parity.md)。

### 8.6 Trees 任务树融合（多员工编排）

FADE 生命周期与 Trees 动态任务树协议互补：FADE 定义"run 如何确定性推进到终态"，Trees 定义"多员工如何协作、交接与恢复"（协议见 `docs/workflow/dynamic-task-tree-protocol.md`）。

**检测即触发**：Agent 探测是触发源的扩展——维护型专属 Agent（如小赛维护 tricompany）可通过 指令、registry diff、codegraph 扫描、文件修改扫描、健康探测 等方式主动发现变化，开启完整触发条件（源→发布→live entry→上岗候选），事件交编排层（小贾）锚定运行标识。

**触发探测落地形态（event-watch，v1.2.0）**：`source_publish_check --event-watch` 单次扫描（定时巡检链的交接点）/ `--watch` 循环（`--interval` / `--watch-dirs`）——指纹 = 文件 hash ∪ git HEAD/refs，首扫建立基线（state_known），此后指纹变化即触发完整链；审计落 `.ade/event-watch/`。文件 / Git 事件自动触发增强为独立工程项（automation-backlog，CTO 2026-08-21 裁决）。

**触发链两种模式**（与 §8.1 / §8.2 两个 profile 一一对应）：

- **定时巡检链（runtime-owned durable）**：cron 定时唤起维护 Agent（小赛）全模块检查 → 发现可安排的 tricompany FADE 任务 → **写入周工作平面待办并标注"闲时执行"** → daemon 与小贾配合定期从周平面取任务 → 到执行窗口（闲时）自动启动 → 触发条件满足时小贾建 trees 执行完整 FADE。周平面是持久任务载体，daemon cron 是调度器，任务不依赖单次会话存活。
- **即时触发链（Agent-owned interactive）**：指令（CEO / 编排层直接要求）→ 小赛立即触发 → 小贾建树 → 完整 FADE 即时执行。

**编排层建树**：小贾（根节点）按 Trees 协议建任务树，按节点拉起对应角色——发布/内容联审（小乔、小狄）、上岗/职责变动（CHO）、执行（小全/小柯）等；多员工按节点参与各段（Plan / DCE / Close 可分属不同节点），节点间以 routedInput（checkpoint 引用）与 brief 显式交接。

**恢复衔接**：Trees 的 checkpoint + brief 交接承载跨节点恢复与幂等续跑，与 FADE 的运行标识状态机互补——Trees 管"谁做什么、交接点在哪"，FADE 管"run 如何按固定流程推进到终态"。

**触发与执行解耦**：触发探测员 ≠ 执行者——源→发布、live entry 发布、上岗链均可由小贾按 trees 流程拉起对应角色完成，不绑定特定 Agent。示例：小赛探测到 tricompany 变化 → 事件交小贾 → 建树拉起小乔/小狄联审（发布域）或 CHO（员工域上岗/职责变动）→ 各节点按 FADE 段执行与收口。

（v2.0.1 恢复注记：本三节在 v2.0.0 重构中误删，自 ade-pattern-spec 历史版本 e6ac7af 找回并做运行标识/FADE 术语对齐；§8.5 核心已部分被 §一 正交声明收编，保留全文以维完整性。）

## 九、立册与升格

FADE 实例登记于 [fade-registry.md](fade-registry.md)。入册需附逐段工件证据与段-实现映射表（§2.8 细则 2）；缺段实例列"补齐项"，两次周检未补即降回兼容档；升格须附试卷与评分通过记录（§2.6）。
