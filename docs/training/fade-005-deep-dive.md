# FADE-005 号深度解读——roster-gating 独立规范、并入 004 的沿革与其独立价值

> 培训真源锚点：本篇所有文件路径、行号、代码、数字均于 2026-08-29 用 Read/Glob 从仓库实读核验；核验不到的一律如实标注「未核验」。本篇不替代任何真源——真源永远是 `fade-005-roster-gating-spec.md`、`candidate-staffing-fade.md`、`fade-registry.md`、`staffing.ts` 本身。

## 〇、培训判断与学习路径

### 培训判断

本篇面向要接手 TriLC 员工域代码与 TriCompany 员工域治理文档的研发新人。它回答三个问题：

1. FADE-005 这个编号是什么？为什么 fade-registry.md 里找不到 FADE-005 条目，却存在一份 `fade-005-roster-gating-spec.md`？（号史）
2. roster-gating（名册门禁）在代码里长什么样？三处门禁怎么改、怎么验、坏了怎么查？（门控语义深读）
3. 为什么它先独立立项、后来又并入 FADE-004？这个「发号又收回」的裁定逻辑对你以后做设计决策有什么可复用的？（整合裁定逻辑）

本篇与 FADE-004 教程的分工声明：**004 篇讲执行体与链路**（staffing 三端点、onboard→decide 链、TriCade 呈现面怎么跑通）；**本篇讲号史与门控语义**（005 号从出生到并入的沿革，以及 roster.active 作为运行态门禁的语义、实现与消费端）。两篇合读才是员工域全貌，任何一篇都不自称完整。

### 学习路径

| 步 | 先读什么 | 验证方式 |
| --- | --- | --- |
| 1 | `D:\Code\ai\TriCompany\docs\engineering\fade-registry.md` 的 FADE-004 条目（114-133 行）+ FADE-006 备注（153 行） | 能复述「为什么编号跳 005」 |
| 2 | `D:\Code\ai\TriMetaverse\docs\execution\fade-005-roster-gating-spec.md` 全文（56 行，短，值得逐行读） | 能画出三处门禁的落点表 |
| 3 | `D:\Code\ai\TriMetaverse\docs\execution\candidate-staffing-fade.md`（65 行） | 能说出八段映射与三层语义分离 |
| 4 | `D:\Code\ai\TriLC\src\company\staffing.ts`（221 行，本篇主战场） | 能指出单一校验函数族在哪几行 |
| 5 | `D:\Code\ai\TriLC\src\cron\timer.ts` 的门禁注入点（48-52 行）与 degraded 语义（161-191 行） | 能解释「skipped 为什么不 incrementError」 |
| 6 | 三个测试文件：`test\roster-gating.test.ts`、`test\agent-tool-roster-gating.test.ts`、`test\cron-role-gating.test.ts`、`test\cron-skipped-degraded.test.ts` | 本机能跑通 `npx tsx --test <文件>` |
| 7 | `D:\Code\ai\TriCompany\docs\engineering\fade-protocol-spec.md` §2.5/§2.7/§2.8 | 能把门禁语义对回协议不变量 |

---

## 一、先讲大的结果：FADE-005 是什么、现在在哪

一句话结果：**FADE-ASSESS-20260819-005 是一个 2026-08-19 由 CEO 定调、08-20 实现并立册的工作包，它把员工名册 roster 从「状态记录 + 徽标」升级为「运行态门禁」——在岗（active）才可被派工、可被 spawn 分身、可被 cron 调度拉起；08-21 勘误裁定其编号并入 FADE-004 员工域，登记册不设独立 FADE-005 条目，但规范文件名保留以兼容历史引用。**

三个关键事实，新人先把这三个钉死：

- **号已并入**：`fade-registry.md`（185 行，v2.1）中不存在 FADE-005 条目。现役编号是 001/002/003/004/006——006 条目备注（153 行）明文写着：「编号跳 005 沿用 08-21 勘误口径（005 已并入 FADE-004 员工域）」。
- **文件保留**：`D:\Code\ai\TriMetaverse\docs\execution\fade-005-roster-gating-spec.md` 仍在，标题第一行就自我声明：「上岗 gating 规范（FADE-ASSESS-20260819-005 工作包 · 并入 FADE-004 员工域，roster.active 运行态门禁）」，第 3 行有完整的编号勘误 blockquote。
- **门禁在跑**：门禁不是纸面文档。`staffing.ts` 头注（7-11 行）写着「FADE-ASSESS-005 上岗 gating（CEO 2026-08-20 启动）」，校验函数族、cron 注入点、三组测试文件全部实读在案（见本文第三节与第六节）。

大图上它在哪：TriCompany 的员工体系有三层语义（candidate-staffing-fade.md 23 行，2026-08-19 live entry 评审裁决）——**决策面 = 在岗名册（roster）、信息面 = 员工 contract、适配面 = live entry**。FADE-004 管这条链的生命周期（上岗怎么发生），FADE-005 工作包管的是**决策面在运行态的消费规则**（上岗状态怎么被执行面尊重）。一个是生产者，一个是消费者合同。

---

## 二、并入沿革：005 号的生与并（号史）

这是本篇独有的内容——把一个编号的完整生命周期讲清楚。按时间线：

### 2.1 前史（08-18 ~ 08-19）：门禁只有「理论上」

FADE-004 于 2026-08-18 立册（规范 v1.1，candidate-staffing-fade.md），当时门禁只存在于文档语义层。注意规范第五节（60 行）的原话：

> 未上岗的 JD **理论上**不应 spawn 分身（名册是分身的组织前提）。

「理论上」三个字就是整个 005 工作包的起点——语义存在，强制不存在。谁都能对一个 candidate 状态的岗位发起派工或 spawn，名册只是展示层的徽标。

### 2.2 整合定调（08-19）：「避免另立 FADE-005」的第一次出现

2026-08-19，CEO 指令做四候选整合分析，产出 `D:\Code\ai\TriCompany\docs\engineering\ade-consolidation-proposal.md`（115 行，v1.0，CEO 当日采纳）。四候选 = 源侧→发布侧同步、项目真源文档同步、Agent live entry 发布、员工对象发布。结论（19-24 行）：**整合为 2 个 ADE，不另立新 FADE**——ADE-A 发布域 = FADE-002 扩容；ADE-B 员工域 = FADE-004 扩容。

对 005 号命运最关键的一句在 61 行：

> 候选 4 是 FADE-004「上岗」后的工件落地段（employee_onboard_stages 第 5-7 段已委托 employee_host_publish 与 `--publish-agents`），本是一条链——合并后员工生命周期一个 FADE，**避免另立 FADE-005**

贡献点标注（112 行）把这条裁定记在小乔（产品语义）名下。同日（08-19），CEO 又定调 FADE-ASSESS-005 为独立工作包（fade-005 规范 15 行「来源：CEO 2026-08-19 定调（FADE-ASSESS-005）」）——注意这两件事并行不矛盾：**整合提案收编的是「员工对象发布」这个候选，防止它另立 005；而 005 号工作包此刻还指别的东西（上岗 gating）**。005 编号后来被 gating 工作包实际使用（文件名与代码注释里的 FADE-ASSESS-20260819-005），这是编号史上的一个错位，勘误正是为收拾这个错位。

### 2.3 实现、验证、立册（08-20）：一天走完全链

fade-005 规范 5-7 行：v1.0，2026-08-20 立册，「CEO 2026-08-20 启动，全链 APPROVED」。当天完成实现、测试、独立验证与终审：

- 24 个新用例（roster 6 / cron 6 / agent-tool 6 / HTTP 6），npm test 452/451（1 fail = TUI 既有 ink 依赖，stash 确认零交集），tsc 零错误（规范 53 行）；
- 小柯独立 HTTP 实测（隔离 daemon + curl）：派工 409 三态 / 可见性全量 / cron skipped 端到端 / degraded 三态（54 行）。

代码侧的落盘证据今天仍可实读：`staffing.ts` 7-11 行头注、`timer.ts` 48-52 行注入点注释，均带「FADE-ASSESS-005」字样。

### 2.4 勘误并入（08-21）：号实分离的收口

2026-08-21，FADE-LEFTOVER 批 2 勘误（fade-005 规范 3 行 blockquote 原文）：

> 本规范是 FADE-ASSESS-20260819-005 工作包产物，编号已并入 **FADE-004（员工域 ADE-B）**——登记册（fade-registry.md）无独立 FADE-005 条目，整合提案明确“避免另立 FADE-005”。文件名保留以兼容历史引用（周平面 / commit 记录）。

处理方式有三个值得学：**改语义不改文件名**（历史引用——周平面任务、commit 记录——都指向这个文件名，改名等于断链）；**登记册不补假条目**（宁可编号跳号，不造一个「并入纪念条目」污染登记册的「完整实例」定义）；**勘误写在文件最显眼处**（第 3 行，读者第一眼就看到），而不是藏在文末。

### 2.5 口径沿用（08-27 ~ 08-28，本周前后）

- 08-27 登记册 v1.2 注记（17 行）：FADE-001..004 登记于四模块架构成立前，**属前标准期实例**——不追溯降格，但须对照新规补课（协议 spec §2.7/§2.8）。
- 08-28 登记册 v2.0 同步注记（20 行）：上位规范迁移 ade-pattern-spec.md → fade-protocol-spec.md v2.0.0，「ADE-A/B 域」历史代号 → **发布域/员工域**。
- 08-28 FADE-006 入册时，153 行备注直接引用 08-21 勘误口径解释自己的编号跳跃——**勘误口径至今仍是活性规则，不是历史注脚**。

---

## 三、协议十段在本实例的落地形态

本篇特殊：005 已并入 004，所以十段落地形态对照 **004 员工域现状**讲，再单独讲 roster-gating 规范自己的段覆盖。

### 3.1 004 员工域的十段现状（对照登记册与规范文档）

先标注一个版本差（接手前人材料必做）：`candidate-staffing-fade.md` 第二节标题是「FADE 生命周期（**八段映射**）」——它立册于 2026-08-18，早于协议 v1.1.2/v1.1.3 把段数升到九再升到十的时间（同日稍后）。现行协议是十段（fade-protocol-spec.md 95 行：事件→登记→Qualify→Plan Skill→DCE→Verify(可选)→Score CLI→Score Skill→Close Skill→Close CLI→终态）。004 条目按登记册 v1.2 注记（17 行）属**前标准期实例**，不追溯降格、须补课。

| 协议十段 | 004 员工域现状载体（实读核验） | 状态 |
| --- | --- | --- |
| 事件触发 | 开业装配 selections / TriCade settings→agents 勾选 /（未来）CHO 增员提案（registry 118 行） | 已落地 |
| 登记 | `POST /internal/v1/staffing/onboard` → requestId+runId，持久 `dataDir/staffing/requests.json`（pending-cho），去重 409（registry 119 行；staffing.ts 154-167 行） | 已落地；requestId+runId 被 spec §2.8 列为合法运行标识载体（253 行） |
| Qualify | 链态门（ready/confirm/sync 才可增员，staffing.ts 139-141 行，409 `chain_state_gate`）+ JD 存在性（404，145 行）+ 重复检查（409 `already_active`/`already_pending`，148/151 行） | 已落地，全部机械可判定 |
| Plan Skill | JD 单一真源映射（TriCompany 合同 displayName/role/description），无需逐次语义规划（candidate-staffing 32 行） | 已落地（静态计划形态） |
| DCE | CHO 批准后 `CompanyInitState.employees` 原子写入（tmp+rename）+ `init:staffing-*` 事件（staffing.ts 192-198 行） | 已落地 |
| Verify | 无独立后置校验段——Close CLI 的 roster 回读承担部分校验职能 | 缺段如实（前标准期补课项） |
| Score CLI / Score Skill | 无独立评分段实现；实例级评分见第八节卷宗（那是入册评估，不是每 run 评分） | 缺段如实 |
| Close Skill | CHO 语义裁决（编制合理性/职责边界），面板代理 approver=panel-cho 审计留痕（registry 122 行） | 已落地（面板代理形态，CHO agent 会话列补齐项） |
| Close CLI | `POST /internal/v1/staffing/decide`：CHO 门 403 → 名册写入 + 审计 json `dataDir/staffing/CHO-staffing-<requestId>.json` → roster 回读（staffing.ts 171-220 行） | 已落地 |
| 终态 | APPROVED（active）/ REJECTED（回 candidate 可再申请）/ BLOCKED（链态/重复/不存在）；E2E 8/8（2026-08-18 隔离环境，candidate-staffing 62-64 行） | 已实跑 |

### 3.2 roster-gating 独立规范自己的段覆盖

关键认知：**fade-005 规范不是又一个生命周期实例——它没有自己的十段**。它定义的是员工域生命周期的**运行态横切面合同**：004 的 DCE 段产出 roster.active 这个产物，005 规范规定「这个产物在三个消费点如何被强制执行」。它六个章节（语义/三处门禁/degraded/兼容性/启用/验证）全是合同条款，不是段。

硬要对回协议，它的段覆盖是这样的：

| 协议概念 | roster-gating 的对应物 |
| --- | --- |
| Qualify 段不变量「机械可判定」（spec §2.8 细则 9 的确定性拾取门精神） | 三处门禁全部机械判定：HTTP 409 / 工具错误 / skipped+原因，零语义推断——它是「确定性拾取门」在员工域的同类实现 |
| 登记段四不变量 | 门禁读取的 roster 状态源自 CompanyInitState.employees（持久、可回读）+ requests.json（pending-cho 可追溯）——门禁判定本身可复算 |
| DCE 段「结构化自检报告」 | 三处门禁的错误语义显式且命名自洽（规范 32 行）：`owner_not_active`（HTTP）/ `role_not_active`（工具）/ `skipped+owner_not_active`（调度日志），**三处均不静默** |
| Verify 段「独立后置校验」 | 未设。门禁是前置校验（协议 2.8 节 Verify 行明文：前置门禁属 Qualify 机械门，不算 Verify） |

### 3.3 三处门禁逐一深读（代码锚）

规范第二节（24-32 行）的三处门禁表，逐行对到代码：

**门一：派工**——`POST /internal/v1/tasks/submit` 可选携带 `ownerRoleId`；非在岗返回 409 `owner_not_active` + roleId + rosterStatus，在 session 创建前短路。兼容性：不携带不校验（普通会话向后兼容）。启用方式：派发侧（TriPilot / 编排层）显式携带才触发（规范 41、48 行）——这是一条能力面边界：**门禁的开关握在调用方手里，daemon 不猜**。

**门二：分身 spawn**——AgentTool 合同岗 spawn 前置校验，通过 `setRosterGate` 注入（解耦设计：`src/tools/agent-tool.ts` 不 import staffing 模块，gate 函数由 daemon 装配时注入）。非在岗报工具错误 `role_not_active`（模型可见，不是静默失败）。豁免与降级：built-in 4 岗豁免；未注入 gate 放行 + warn（规范 29 行）。测试 `test\agent-tool-roster-gating.test.ts`（实读 1-80 行）覆盖六种正反用例，其中 45-54 行两条兼容性用例值得背下来：未注入 gate → 放行；gate 返回 undefined（门禁不可用）→ 放行。**门禁基础设施故障时 fail-open 而不是 fail-closed**——这是有意取舍：daemon 内部门禁挂掉不该把整个 agent 会话锁死，暴露 warn 让人修，而不是让全公司停摆。

**门三：调度**——cron job 可选绑定 `roleId`，拉起前校验；非在岗记 `skipped` + 原因 `owner_not_active`（执行日志），**不 incrementError**（timer.ts 161-170 行，注释明写「FADE-ASSESS-005: skipped（门禁拒绝）记 skipped 且不 incrementError——job 本身未失败，仅本次因非在岗未拉起」）。注入点在 `timer.ts` 48-50 行的 `CronTimerDeps.isRoleActive`（注释：「FADE-ASSESS-005: 员工岗在岗校验（读 CompanyInitState.employees）。job.roleId 设置后拉起 agent 前校验；非在岗 → skipped，不拉起。缺省不校验」）。gate 前移含 command job（规范 30 行）——连确定性 shell job 也过同一道门，现役 command job 均未绑 roleId 所以行为不变（规范 43 行）。

### 3.4 单一校验真源：staffing.ts 函数族

三处门禁共用同一组校验函数（staffing.ts 94-134 行实读）——这是「单一校验真源」原则的教科书实现：

```ts
export type RosterStatus = 'active' | 'pending-cho' | 'candidate' | 'unknown';

export interface RosterGateResult {
  allowed: boolean;
  status: RosterStatus;
  /** 非在岗时的错误码（FADE-ASSESS-005 统一语义，不静默）。 */
  error?: 'owner_not_active';
}

export async function getRoleRosterStatus(deps: StaffingDeps, roleId: string): Promise<RosterStatus> {
  const company = await deps.companyState.load();
  if ((company.employees ?? []).some((e: any) => e.role === roleId)) return 'active';
  const requests = await loadRequests(deps.dataDir);
  if (requests.some((r) => r.roleId === roleId && r.status === 'pending-cho')) return 'pending-cho';
  const catalog = deps.getRoleCatalog();
  if (catalog && (catalog.roles ?? []).some((r: any) => r.roleId === roleId)) return 'candidate';
  return 'unknown';
}

export async function isRoleActive(deps: StaffingDeps, roleId: string): Promise<boolean> {
  return (await getRoleRosterStatus(deps, roleId)) === 'active';
}

export async function enforceRoleActive(deps: StaffingDeps, roleId: string): Promise<RosterGateResult> {
  const status = await getRoleRosterStatus(deps, roleId);
  if (status === 'active') return { allowed: true, status };
  return { allowed: false, status, error: 'owner_not_active' };
}
```

注意四态而不是三态：`unknown`（岗位目录里都不存在）单列——派工门用它给调用方返回精确的 rosterStatus，而不是把「不存在」和「没上岗」混成一个错误。判定优先级：employees（在岗事实）→ requests（待审事实）→ role-catalog（候选目录）→ unknown。

### 3.5 degraded 语义：门禁产生的「跳过」必须可见

这是 005 规范第三节（34-37 行，终审收口 ⑤）最容易被新人忽略、但最有设计含量的一段：

- skipped 计入非 ok 路径：连续 3 次 skipped 触发 `cron:degraded`（阈值常量 `CONSECUTIVE_FAILURE_DEGRADED_THRESHOLD = 3`，timer.ts 22 行实读）；
- **恢复仅以真实 ok 为凭**：skipped 不解除 degraded、不广播 `cron:recovered`（timer.ts 175-183 行：只有 `result.status === "ok"` 分支才清零并广播恢复）。

为什么这样设计？如果把 skipped 当成功，一个岗位被误下岗后，它的定时任务会无限静默空转，没人知道；如果把 skipped 当失败，门禁正常工作也会刷错误计数，污染真正的失败信号。折中方案：skipped 不进错误计数（不 incrementError），但**计入连续非 ok 序列**（timer.ts 184-190 行 else 分支照常 `consecutiveFailures++`）——门禁干活时系统知道「这里有个岗位持续不可用」，通过 degraded 事件把它暴露出来；而恢复信号必须等岗位真回岗、任务真跑成一次才发。**门禁的拒绝要可见，恢复的宣告要保守**。

---

## 四、独立价值：为什么它值得一个号、为什么又并入

### 4.1 为什么值得独立立项（发号的理由）

- **语义升级是质变不是修补**：「上岗」从状态记录（display 层徽标）变成功能门禁（三处运行时强制），横跨 HTTP 面、工具面、调度面三个子系统——这不是 FADE-004 现有代码的小改，是一次跨面合同变更，值得独立工作包管理。
- **它有自己的验证义务**：24 新用例 + 独立 HTTP 实测 + degraded 三态端到端，工作包粒度刚好。
- **「状态 → 门禁」是可复用的通用模式**：任何「决策真源」（名册、manifest、registry）都可能面临同样的升级路径——先有记录、再有徽标、最后长出门禁。这个模式值得一个独立规范文档承载教学。

### 4.2 为什么又并入（收号的逻辑）

整合裁定（ade-consolidation-proposal.md 61 行 + 贡献点 112 行）的逻辑拆开是三条：

1. **同链工件不拆生命周期**：上岗→名册→门禁是一条链上的产物与消费，拆成两个 FADE 意味着两套登记、两套审计、两套评分——四倍成本（提案 45 行原话「同一生命周期缺口……各自补一遍即四倍成本」的变体）。
2. **审批门唯一**：提案 76 行明文「不保留第二道 CHO 门」——审批只设在决策点（上岗：编制合理性/职责边界），执行点只做契约校验。门禁是契约校验，不是第二道审批；它没有资格成为独立生命周期主体。
3. **登记册的「完整实例」定义必须干净**：fade-registry 只登记十段全落地的完整实例。roster-gating 没有独立十段，若立 FADE-005 条目，要么降档登记（污染完整档序列）、要么补齐十个段的空壳（审计负债）。并入是唯一不产生制度垃圾的选项。

### 4.3 收号之后的独立价值仍在

并入只是编号层面的收编，fade-005-roster-gating-spec.md 作为规范文档的独立价值没有消失：它仍是理解「决策面产物如何被运行态消费」的最短教材，也是 TriLC 侧三处门禁代码的唯一语义真源。**编号并了，文档没废**——这是学习本案最该带走的一点。

---

## 五、员工域 ADE-B 完整图景：上岗链 + 发布链同一生命周期域

并入之后，FADE-004 员工域覆盖两段链（registry 132 行：「上岗链 + 发布链同一生命周期域」）。

### 5.1 上岗链（本篇主线）

开业装配发布候选全集 → settings 勾选 → onboard 登记（pending-cho）→ CHO 审批（decide）→ JD 进在岗名册 → **roster.active 被三处门禁消费（005 语义）**。门禁是上岗链的下游出口——没有 005，上岗链的终点只是一个布尔值没人读。

### 5.2 发布链（Ade-B 扩容并入的一半）

员工对象发布段：host object 生成 / binding profile / 委托 publish-agents / 治理回填（registry 132 行）。协议 spec §6.2（336-343 行）落地为多宿主渲染模型：`source_publish_check --publish-agents --host={copilot|claude}`，copilot 为字节保真复制面、claude 为渲染面（工具名映射 + 硬白名单 + tool_drops 审计）。

### 5.3 双部署模型下 roster 的位置（这是 005 语义的坐标系）

提案 69-70 行（CEO 08-19 定调）给了关键映射——**宿主侧 vs runtime 侧**的发布链等价形态：

| 发布链环节 | 宿主侧（Copilot-host / Claude Code） | runtime 侧（TriLC / TriMC） |
| --- | --- | --- |
| binding（在岗绑定） | 渲染产物 + binding profile hostEntries | **roster.active（在岗绑定）——005 门禁读的就是它** |
| live | live entry 文件 | `/agents` API（contract 直读，无渲染文件） |
| manifest | live manifest liveEntries | roster.status 三档（active/pending-cho/candidate） |

也就是说：roster-gating 是 runtime 侧「binding」环节的强制形态。宿主侧的「谁被加载」由发现面文件决定，runtime 侧的「谁可被派工」由 roster 决定——**005 规范就是 runtime 侧 binding 的执行合同**。配套纪律是 D-07（engineering-disciplines.md 52-54 行）：live entry 是 contract 的派生加载壳，禁人工直接编辑；三层语义「名册=决策真源、contract=信息真源、live entry=适配面」。改在岗状态只能走 staffing API（决策面），不能改 live entry（适配面）假装上岗——门禁读的是 CompanyInitState.employees，改适配面文件对门禁无效，这是三端语义分离带来的天然防伪。

---

## 六、本周真实运行证据（核验口径）

**核验方式声明**：本线程只有 Read/Glob，无 git 工具——以下「已核验」均指 2026-08-29 实读文件所得（文件存在性、行号、代码原文、文件内记录的数字）；08-20 实现窗的 commit hash 无法在本线程独立重验，如实标注。

### 已核验证据清单

| 锚点 | 文件（绝对路径） | 核验内容 |
| --- | --- | --- |
| 规范正文 | `D:\Code\ai\TriMetaverse\docs\execution\fade-005-roster-gating-spec.md` | 56 行；v1.0（08-20 立册）；3 行勘误 blockquote；24 新用例/452 通过/1 fail TUI ink/tsc 零错误记录于 51-55 行 |
| 校验函数族 | `D:\Code\ai\TriLC\src\company\staffing.ts` | 221 行；7-11 行 FADE-ASSESS-005 头注；RosterStatus 四态（99 行）；getRoleRosterStatus 114-122；isRoleActive 125-127；enforceRoleActive 130-134；CHO_ALLOWED 四值白名单（181 行：cho / chief-human-resources-officer / ceo / panel-cho）；审计文件名模板 `CHO-staffing-<requestId>.json`（214 行） |
| 调度门禁 | `D:\Code\ai\TriLC\src\cron\timer.ts` | 22 行阈值常量 =3；48-52 行 isRoleActive/onRoleGateDenied 注入点（带 FADE-ASSESS-005/003 注释）；146 行 executeJobScheduled；161-170 行 skipped 不 incrementError；172-191 行 degraded/recovered 语义 |
| 门二测试 | `D:\Code\ai\TriLC\test\agent-tool-roster-gating.test.ts` | 实读 1-80 行：从 `src/tools/agent-tool.js` 导入 enforceRosterGate/setRosterGate/setOnSpawnGateDenied；六正反用例；61 行起「FADE-005 观察项收口：setRosterGate 多实例注入」（last-write-wins + set null 清理回退放行） |
| degraded 测试 | `D:\Code\ai\TriLC\test\cron-skipped-degraded.test.ts` | 实读 1-50 行：头注明写固化规范 §三两条语义；executeJobScheduled 非导出（timer.ts:146）经 runMissedJobs 实测；曾实测 exit=124 超时问题与 mock.timers 兜底；运行命令 `npx tsx --test test/cron-skipped-degraded.test.ts`（20 行） |
| 另两组测试 | `D:\Code\ai\TriLC\test\roster-gating.test.ts`、`D:\Code\ai\TriLC\test\cron-role-gating.test.ts` | Glob 验证存在（对应 roster 6 / cron 6 用例的载体）；内容未逐行读 |
| 登记册 | `D:\Code\ai\TriCompany\docs\engineering\fade-registry.md` | 185 行；FADE-004 条目 114-133（补齐项 130 行仍列「分身 spawn 前置校验『JD 已上岗』」，评分 81→88 弧线 131 行，ADE-B 扩容 132 行）；FADE-006 备注 153 行引用 08-21 勘误 |
| 整合提案 | `D:\Code\ai\TriCompany\docs\engineering\ade-consolidation-proposal.md` | 115 行；「避免另立 FADE-005」61 行；小乔贡献点 112 行；双部署模型 69-70 行 |
| 004 卷宗 | `D:\Code\ai\TriCompany\docs\engineering\fade-papers\` | Glob 验证 8 件存在：FADE-004-paper.json、FADE-004-report.json、FADE-004-score-2026-08-20.json（+.coverage.json）、FADE-004-quality.json、FADE-004-{report,quality,score}-rereview-2026-08-20.json |
| 组织依据 | `D:\Code\ai\TriMetaverse\docs\execution\clone-dispatch-protocol.md` | Glob 验证存在（岗位=JD / 上岗=进名册 / 分身=另一层 HC） |
| E2E 脚本 | `D:\Code\ai\TriLC\scripts\e2e-staffing-repro.mts` | Glob 验证存在；内容未读 |

### 未核验项（如实标注）

- 08-20 实现窗与 08-21 勘误的具体 commit hash：本线程无 git 工具，未核验。文件内记录（规范/registry）是当前可用证据。
- `test\roster-gating.test.ts` 与 `test\cron-role-gating.test.ts` 的用例数（规范记「各 6」）：文件存在已证，逐条数目未重数。
- `src/tools/agent-tool.ts` 中 setRosterGate 的精确行号：未读该文件全文，不给行号（测试文件 8 行的 import 语句证明函数位于该模块）。
- 提醒：TriLC 仓历史上存在本地线与 sg 线分叉的治理记录（记忆索引口径，本线程未重验）——接手 staffing.ts 前先与 owner 核对当前线基线，再动手。

---

## 七、故障弧线与教训（D 系纪律关联）

005 没有 single 大事故，但它身上叠着三条真实的故障弧线，每条都对应可执行的教训。

### 弧线一：从「理论上不应」到强制门禁

candidate-staffing-fade.md 60 行那句「未上岗的 JD **理论上**不应 spawn 分身」是弧线起点。08-18 立册时人人同意这个语义，但没有任何代码强制它——文档语义不会自己长出 409。两天后（08-19 定调、08-20 落地）三处门禁把「理论上」变成「必然」。教训对应协议 §2.8 细则 10 的精神：**审出的语义缺陷，接线 + 实测才算修完**；写在规范里的「不应」只是愿望，跑在代码里的 409 才是规则。

### 弧线二：静默跳过的陷阱

cron 门禁若把「非在岗跳过」实现成静默 return，会出现一类最难查的故障：任务看起来排了、没报错、也永远不执行——连续数周无人发现（这正是 D-02 cron job state 卫生纪律处理过的一类「永不调度」近亲）。005 的收口选择是把 skipped 做成三态之一：执行日志里可见（`skipped + owner_not_active`）、不污染错误计数、但连续 3 次触发 degraded 事件、恢复只认真实 ok。教训与 D 系纪律同构：**异常必须显式标记、不静默处理**（协议 §九 新建 Agent 时第 3 条原话），且「没发生」与「发生了但被拒」必须可区分。

### 弧线三：号实分离的治理勘误

文件名带 005、commit 记录带 005、登记册却无 005——这个错位如果不勘误，三个月后新人（就是你）会对着登记册怀疑仓库里有幽灵实例。08-21 的处理方式（文件名保留 + 显眼处勘误 + 登记册不造假条目）本身值得当作治理模板。教训：**编号的真源是登记册，文件名只是载体**；发现号实分离时修「号」不修「实」，且把勘误写在读者第一眼的位置。

### D 系关联汇总

| 纪律 | 与 005 的关联 |
| --- | --- |
| D-07 live entry 派生壳 | 同一次 08-19 评审裁决的产物；三层语义分离是门禁防伪的根基（改适配面骗不过决策面门禁） |
| D-03 daemon 重启纪律 | 三处门禁全部活在 TriLC daemon 进程内（gate 函数 daemon 启动时注入，timer.ts deps 注入即此）；daemon 重启姿势错误 = 门禁注入缺失 → 回退放行 + warn，此时要按 D-03 排查而不是先怀疑门禁逻辑 |
| D-02 cron job state 卫生 | 调度门禁与 cron state 共用同一套 updateJobRun 通路；手动改 job state 时同样禁抹 nextRunAtMs |
| D-01 subagent 落盘纪律 | 005 的验证基线之所以今天还可信，靠的是当时的证据落盘（规范 §六、测试文件头注）——「先写后报」的纪律让两周后的培训能实读复核 |

### 观察项收口现状（诚实盘点）

规范 55 行挂了三项后续观察项。现状实核：**setRosterGate 多实例注入**——已收口，`test\agent-tool-roster-gating.test.ts` 57 行起明写「FADE-005 观察项收口」，语义定为 last-write-wins + set null 清理；**skipped-degraded 单测固化**——已收口，`test\cron-skipped-degraded.test.ts` 头注明写固化规范 §三两条语义（两项收口的具体日期因无 git 工具未核验）；**分身 spawn 级端到端**——未定位到对应端到端测试文件，如实标记为未见收口载体（可能仍开放）。另外注意 registry 130 行 FADE-004 补齐项仍列着「分身 spawn 前置校验『JD 已上岗』」——单测与注入点已存在，但登记册口径未划销，属「实现先行、登记未销账」的台账差，接手时以登记册为准先核对再动。

---

## 八、卷宗解读（无独立卷——指向 004 卷宗）

如实结论：**FADE-005 没有独立试卷、没有独立评分卷**。fade-papers 目录（Glob 实证 8 件）中不存在 FADE-005-paper.json 或任何 005 命名的卷宗。这与其并入裁定完全自洽：门禁是 004 员工域的段内加强件，不是独立实例，因此没有独立的「考试资格」。

应读的卷宗是 FADE-004 的：

- 入册评估：`FADE-004-paper.json` + 首评与复评证据链（`FADE-004-score-2026-08-20.json` / `.coverage.json`、`FADE-004-quality.json`、`FADE-004-report.json`），复评三件（`FADE-004-{report,quality,score}-rereview-2026-08-20.json`）。
- 分数弧线（registry 131 行）：首评 **PASS 81/100** → 官方审计证据就位后复评 **PASS 88/100**（audit-record 6→9、terminal-sample 9→10 等 4 项升级，无降项）。
- 读卷时注意：004 卷评估的是**上岗链生命周期**（2026-08-20 时点），此刻 005 门禁刚落地一天——卷宗不覆盖门禁的三处消费端验证；门禁的验证证据在 fade-005 规范 §六与 TriLC 测试文件里。两处证据合读，才是员工域当时的完整质量快照。

---

## 九、与 FADE 协议 v2.0.0（§2.7/§2.8）对照

协议于 2026-08-28 重构为 v2.0.0（`D:\Code\ai\TriCompany\docs\engineering\fade-protocol-spec.md`，535 行，当前 v2.0.3）：ADE 概念退役，FADE 升为协议本体，「ADE-A/B 域」改称历史代号「发布域/员工域」（22 行变更记录、20 行登记册注记）。005 规范写于协议前标准期，用旧术语——对照阅读时做术语置换即可，语义不受影响。

### §2.8（段合同与实现绑定）视角

- **协议管不变量，实例管载体**（§2.8 分层模型）。roster-gating 是这条立法的最佳注脚之一：员工域的登记段载体是 requestId+runId + requests.json（spec 253 行明列「requestId+runId（员工域）」为登记段合法载体示例），门禁不关心载体形态，只消费「active 与否」这一个判定结果。
- **细则 9 profile 限定**：确定性拾取门为 runtime-owned/自动触发 profile 的强制不变量；Agent-owned/interactive profile 允许语义判定留痕。roster 三处门禁全部机械判定（HTTP 状态码/工具错误/skipped 原因），是「确定性拾取门」家族在员工域的同类物——可对照 FADE-006 编排层三重门（执行面同族实现）一起学。
- **细则 10 立法完成度**：接线 + 实测才算立法完成。005 的历史顺序恰好是这个细则的先声——08-20 当天实现、测试、独立验证同日闭环，「纸面法」清零入册。

### §2.7（节点收口报告）视角

005/004 是**单节点链**（staffing API 三端点一次走完），无多节点树，因此不承担 §2.7 的节点收口报告义务（该义务按登记册 v1.2 注记的补课范围裁定仅适用多节点树实例）。对照学习：FADE-006 是多节点形态，才有 reports/node-<NODE-ID>.md 十必备字段。想清这一点，你就理解了 §2.7 为什么写「多节点任务包（树）中」——**合同随形态走，不为单节点链强加报告义务**。

### §2.5（终态门）的同构精神

§2.5 有一条（174 行）：「实例映射表声明的确定性载体视为该实例的 Close CLI 形态；**被裁决会话不得自证终值**」。它与 005 的「单一校验真源」完全同构：终态不能由执行会话自己说了算，在岗与否不能由派工方自己说了算——都必须问同一个权威函数（Close CLI / enforceRoleActive）。**「不自证」是这套体系从终态门到名册门一以贯之的宪法条款。**

---

## 十、接手任务：新人上手清单

**读什么**：按第〇节学习路径 1→7。读完能回答：三处门禁在哪、错误码分别是什么、谁注入校验函数。

**跑什么**（在 `D:\Code\ai\TriLC\` 下）：

```bash
npx tsx --test test/agent-tool-roster-gating.test.ts
npx tsx --test test/cron-skipped-degraded.test.ts
npx tsx --test test/roster-gating.test.ts
npx tsx --test test/cron-role-gating.test.ts
```

**改哪里**：改门禁语义只改 `src/company/staffing.ts` 的函数族（单一真源）；改某处门禁的消费行为改对应消费点（HTTP 提交路径 / `src/tools/agent-tool.ts` / `src/cron/timer.ts`），但错误码词表（owner_not_active / role_not_active / skipped+owner_not_active）不许单方面改——三处命名自洽是规范 32 行的合同。改完先补测试再改实现，语义变更须回写 fade-005 规范并同步登记册口径（顺手把 130 行补齐项的台账差与 owner 核对清楚）。

**如何验证**：单测全绿 + tsc 零错误；涉及 HTTP 门用隔离 dataDir 起 daemon 手打 curl 复现 409 三态（active 放行 / pending-cho 与 candidate 拒绝）；涉及 cron 门跑 skipped-degraded 测试确认 degraded/recovered 时序。

**常见误区**：把 roster 当 agent 加载列表（13 岗 contract 常驻加载，名册只治理上岗状态，candidate-staffing 21 行）；改 live entry 假装上岗（门禁只读 CompanyInitState.employees）；把 skipped 当失败报障（先看 errorMessage 是不是 owner_not_active）；去登记册找 FADE-005 条目（它不在，且这是勘误后的正确状态）。

---

## 使用依据

- `D:\Code\ai\TriMetaverse\docs\execution\fade-005-roster-gating-spec.md`（全读，56 行）——本篇第一真源
- `D:\Code\ai\TriCompany\docs\engineering\fade-registry.md`（全读，185 行）——004 条目、FADE-006 备注、v1.2/v2.0 注记
- `D:\Code\ai\TriCompany\docs\engineering\ade-consolidation-proposal.md`（全读，115 行）——并入裁定与 ADE-B 图景
- `D:\Code\ai\TriMetaverse\docs\execution\candidate-staffing-fade.md`（全读，65 行）——004 规范与三层语义分离
- `D:\Code\ai\TriLC\src\company\staffing.ts`（全读，221 行）——校验函数族
- `D:\Code\ai\TriLC\src\cron\timer.ts`（实读 1-219 行）——调度门禁注入与 degraded 语义
- `D:\Code\ai\TriLC\test\agent-tool-roster-gating.test.ts`（实读 1-80 行）、`test\cron-skipped-degraded.test.ts`（实读 1-50 行）、`test\roster-gating.test.ts` 与 `test\cron-role-gating.test.ts`（Glob 存在性）
- `D:\Code\ai\TriCompany\docs\engineering\fade-protocol-spec.md`（全读，535 行，v2.0.3）——§2.5/§2.7/§2.8 对照
- `D:\Code\ai\TriCompany\docs\workflow\engineering-disciplines.md`（全读，84 行）——D-07/D-03/D-02/D-01 关联
- `D:\Code\ai\TriCompany\docs\engineering\fade-papers\`（Glob 8 件）——004 卷宗清单
