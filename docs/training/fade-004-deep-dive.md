# FADE-004 员工域深度教程：候选岗位发布（员工上岗）——从 HTTP 链到评分卷宗

> 培训真源归档位：`TriCompany/docs/training/`（本篇为教程，不是事实裁决；所有事实以文中标注的真源文件为准）
> 读者：技术研发新人。目标：读完能复述 FADE-004 十段链路、读懂 `TriLC/src/company/staffing.ts` 全部代码路径、独立复现 E2E、看懂评分卷宗、知道接手后改哪里找谁。

---

## 〇、培训判断

- **学习者画像**：会 TypeScript/Node、刚接触 TriCompany 的研发新人。不要求提前懂 FADE 协议，本篇自带最小协议背景。
- **接手目标**：能独立维护员工上岗链（三端点）、能跑通 E2E 八分支、能按现行 FADE 协议（v2.0.0+）为 004 的新 run 建卷评分。
- **成熟度声明**：FADE-004 为**前标准期实例**（登记于四模块架构成立前，见登记册 v1.2 注记），首评 81→复评 88 通过，但按 2026-08-27 立法的新规（§2.7/§2.8）仍挂补课项。教程如实标注"已实现 / 待补课 / 待初始化"三态。
- **教学顺序**：先大结果 → 再协议 → 三端点代码细读 → 证据与评分 → 故障教训 → 接手清单。符合"项目大图 → 模块 → 文件 → 代码"的讲解纪律。

---

## 一、先讲大结果：FADE-004 到底实现了什么

### 1.1 一句话

**FADE-004 把"一家 AI 公司里一个岗位从候选到正式上岗"做成了一条可审计的 HTTP 生命周期链**：候选岗位全集可见 → 勾选提交上岗申请（登记 requestId+runId，pending-cho）→ CHO 审批（非 CHO 一律 403）→ 批准则写入在岗名册并落审计 JSON，驳回则回到候选态。全程有结构化证据，评分 88/100 PASS。

### 1.2 全局位置：三层语义分离

这是理解本实例最重要的一张心智图（真源：`TriMetaverse/docs/execution/candidate-staffing-fade.md` §一，2026-08-19 live entry 评审裁决）：

| 层 | 治理对象 | 真源载体 | 谁管 |
| --- | --- | --- | --- |
| 决策面 | 谁在岗（编制/派工资格） | 在岗名册 `CompanyInitState.employees` + staffing requests | **本 FADE（004）** |
| 信息面 | 员工身份/职责/权限 | 员工 contract（三端可读） | 员工域发布链（并入 004，见第五节） |
| 适配面 | 当前宿主的派生加载壳 | live entry（`.github/agents/*.agent.md`） | 发布管线渲染，禁人工编辑（D-07） |

**关键澄清（新人最常误解的点）**：在岗名册**不是** agent 加载列表。13 个岗位合同全部常驻加载；名册只治理"上岗"这个组织状态——谁可被派工、谁可被 spawn 分身。个人名是开业/上岗时赋予的实例属性，未在岗一律 `null`（"岗位=固定资产，名字=流动资产"，`staffing.ts:73-74` 注释，CEO 2026-08-18 口径）。

### 1.3 真源地图（先收藏，遇到冲突按此排序）

| 内容 | 真源 |
| --- | --- |
| 实例登记（段表/评分/补齐项） | `TriCompany/docs/engineering/fade-registry.md` FADE-004 条目（第 114-132 行） |
| 实例规范 | `TriMetaverse/docs/execution/candidate-staffing-fade.md`（v1.1） |
| 组织依据 | `TriMetaverse/docs/execution/clone-dispatch-protocol.md`（岗位=JD；上岗=进名册；分身 spawn=另一层 HC） |
| 上位协议 | `TriCompany/docs/engineering/fade-protocol-spec.md`（v2.0.3，§2.7/§2.8/§6.2） |
| 执行体代码 | `TriLC/src/company/staffing.ts`（3 端点 + 门禁函数） |
| 状态持久层 | `TriLC/src/company/init-state.ts`（CompanyInitState） |
| 链态机 | `TriLC/src/company/init-chain.ts`（七态状态机） |
| 试卷与评分 | `TriCompany/docs/engineering/fade-papers/FADE-004-*.json` |
| 域扩容沿革 | `TriCompany/docs/engineering/ade-consolidation-proposal.md`（ADE-B 员工域） |

---

## 二、理论框架：十段协议与"协议管不变量、实例管载体"

FADE（Full-cycle Agentic Deterministic Execution）十段（spec §1.1）：**事件触发 → 登记（运行标识）→ Qualify → Plan Skill → DCE → Verify（可选）→ Score CLI → Score Skill → Close Skill → Close CLI → 终态**。

一条 v2.0.0 的核心立法必须先记住（spec §2.8）：

> **协议层只约束每段职责不变量与产物合同；实现载体由 FADE 实例自由选择并在入册时声明"段-实现映射表"。**

落到 004：协议不要求你叫什么字段名，但登记段四不变量（唯一性/去重性/关联性/恢复锚）必须满足。004 的载体选择是 `requestId + runId` 双标识 + `dataDir/staffing/requests.json` 持久文件——spec §2.8 的合法载体示例里明确列了"requestId+runId（员工域）"。

---

## 三、必备节一：协议十段在本实例的逐段落地形态

每段给"协议不变量 → 004 的载体 → 真实文件与行号 → 为什么这样设计"。

### 段 1：事件触发

- **不变量**：可重放、可归因（谁/何时/何事件）。
- **004 载体**：三个触发源（registry 第 118 行、规范 §二）——① 开业装配 selections；② TriCade settings→agents 勾选；③（未来）CHO 主动增员提案。呈现面行为在规范 §四：候选全集可见、打钩+"在岗"徽标（锁定）、勾选提交后"CHO 审批中"徽标、未开业勾选被 409 拒绝并 toast 提示。
- **代码落点**：`staffing.ts:137` `requestOnboarding(deps, roleId, requester, employeeName?)` 的 `requester` 参数即归因锚（谁发起），`staffing.ts:159` 缺省落 `'ceo-panel'`，`staffing.ts:161` 记 `requestedAt` ISO 时刻。
- **为什么**：触发源是"面板/人为动作"而非 cron，所以归因靠请求载荷里的 requester+requestedAt，不靠调度日志。

### 段 2：登记（运行标识）

- **不变量**：唯一性/去重性/关联性/恢复锚四项（spec §2.8 登记合同）。
- **004 载体**：`POST /staffing/onboard` → 生成 `requestId + runId` 双标识，持久到 `dataDir/staffing/requests.json`，状态 `pending-cho`。
- **代码落点**：
  - 标识生成：`staffing.ts:39` `RID = () => \`staffing_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}\`` ——base36 毫秒戳 + 4 位随机。 Evidence 卷里你能看到 `staffing_mt1bgj61_xeiq` 这种形态：`mt1bgj61` 是时间戳、`xeiq` 是随机尾巴。
  - 持久化：`staffing.ts:41-47` `loadRequests()`（读文件、坏数据兜底空数组）、`staffing.ts:49-53` `saveRequests()`（mkdir 递归 + 两空格缩进 JSON 全量写回）。
  - 双标识语义：`requestId`（`staffing.ts:155`）= 审批单元标识（decide 按它寻址）；`runId`（`staffing.ts:156`）= 运行标识（审计 JSON 载荷携带它，对应 spec 细则 6"被评分卷宗引用的 run 必须可被单一显式标识引用"）。
- **为什么双标识**：requestId 面向"这一次审批"，runId 面向"这一次运行"的审计链。两者同刻生成但互不派生，任何一个都能独立定位现场（恢复锚）。

### 段 3：Qualify（机械准入门）

- **不变量**：机械可判定或语义判定留痕。
- **004 载体**：四道机械门，全部在 `requestOnboarding` 内前置（`staffing.ts:138-153`）：
  1. **链态门**（`staffing.ts:138-141`）：`chainState` 不在 `['ready','confirm','sync']` → 409 `chain_state_gate`。链态七态机见 `init-chain.ts:26-33`（uninitialized→selfcheck→onboarding→project-link→sync→confirm→ready，线性单步转移，`init-chain.ts:116-124`）。注意：门在 sync/confirm/ready 三态就开，不是只等 ready 终态——registry 第 120 行"ready 后才可增员"是压缩表述，以规范 §二与代码为准。
  2. **目录可用性**（`staffing.ts:142-143`）：role-catalog 未加载 → 503 `role_catalog_unavailable`。
  3. **JD 存在性**（`staffing.ts:144-145`）：roleId 不在目录 → 404 `role_not_found`。
  4. **重复检查**（`staffing.ts:146-153`）：已在岗 → 409 `already_active`；已有 pending-cho 请求 → 409 `already_pending`。
- **为什么**：这些判定零语义、纯机械，放在 daemon 代码里而不是让 agent 判断，正是 FADE"智能与确定性分离"（spec §2.1）的体现。

### 段 4：Plan Skill

- **不变量**：结构化计划；004 的岗位定义固定，**无需逐次语义规划**（规范 §二 Plan 行）。
- **004 载体**：JD 单一真源映射——TriCompany 合同的 displayName/role/description。代码落点是 `getStaffingRoster` 的映射段（`staffing.ts:65-72`）：`displayName`/`role`/`description` 三字段按 `r.displayName ?? r.roleName ?? r.roleId` 等回退链从 role-catalog 单一真源取值，不做第二份拷贝。
- **为什么**：岗位 JD 只在 TriCompany 合同维护一份，roster 只是投影。有回退链说明历史字段名有演进，真源字段以 role-catalog 为准。

### 段 5：DCE（确定性执行）

- **不变量**：确定性、可复现、结构化自检。
- **004 载体**：CHO 批准后 `CompanyInitState.employees` 持久写入 + `init:staffing-*` 事件发布。
- **代码落点**：
  - 名册写入：`staffing.ts:192-198` ——拷贝 employees 数组、按 role 去重追加 `{ role, name: employeeName || displayName }`、`deps.companyState.save(...)`。
  - 持久层：`init-state.ts:52-111` `CompanyInitState` 类，状态文件 `{dataDir}/company/state.json`（`init-state.ts:58`）。`save()` 见 `init-state.ts:87-111`；**写盘语义细节见第八节 8.3（已知偏差，务必读）**。
  - 事件发布：`staffing.ts:166` `init:staffing-request`、`staffing.ts:215` `init:staffing-approved`、`staffing.ts:217` `init:staffing-rejected`。发布通道是注入的 `deps.publish`（`staffing.ts:21`），与 init 链同一 localbus 事件族（`init-chain.ts:157-159` 注释："localbus 事件族，含 init:* 类型"；`init-chain.ts:18`："事件发布通过注入的 publisher（app.ts publish）"）。
- **为什么**：写名册是业务副作用，按 spec §2.1 关键约束"Agent 不直接执行受治理的副作用"，它必须落在确定性代码路径里，agent 只触发不亲手写。

### 段 6：Verify（可选段）

- **004 的处理**：**未单独设 Verify CLI 段**——终态核验（roster 回读）折叠进了 Close CLI 的 decide 路径。这与 FADE-006 的"诚实空缺不凑段"同一精神，但形态不同：006 是整段空缺如实标注，004 是回读证据内嵌在 decide 的 200 返回与 roster 端点里。
- **代码落点**：`getStaffingRoster`（`staffing.ts:56-92`）返回 `status` 三态 + `counts`（total/active/pending，`staffing.ts:86-90`）+ `chainState`，E2E ③⑥ 两步就是用它做回读断言的。
- **试卷对应**：`roster-readback` 是实例特有检查项（试卷第 94-100 行），E2E ③⑥ 回读 counts 实证。

### 段 7：Score CLI（覆盖遗漏检测，确定性）

- **不变量**：覆盖检查确定性可复算（spec §2.8 十段合同）。
- **004 载体**：覆盖率卷 `fade-papers/FADE-004-score-2026-08-20.coverage.json`——10 项检查全部 `score: 10.0`、`omission: false`、总分 100/100、`verdict: PASS`（`scored_at: 2026-08-20T04:29:17Z`，即北京时间 12:29:17）。`required_all_passed: true` 是 Score CLI 的确定性判定输出。
- **为什么拆两段**：CLI 查"有没有漏项"，Skill 评"每项做得好不好"（spec §2.6）。混在一起就无法区分"漏做"和"做糙"。

### 段 8：Score Skill（逐项语义评分）

- **不变量**：逐项语义分 + evidence_ref。
- **004 载体**：首评质量分并卷在 `FADE-004-score-2026-08-20.json`（总分 81），复评在 `FADE-004-score-rereview-2026-08-20.json`（总分 88），每项都带 `evidence_ref` 指到真实文件。逐项对照见第七节。
- **评分合同**：按 spec §2.6，Score Skill 输出与 Score CLI 覆盖检查合并为一份结构化评分 JSON，作为 Close Skill 裁决的客观证据。

### 段 9：Close Skill（语义裁决）

- **不变量**：语义终裁引用评分证据。
- **004 载体**：**CHO 语义裁决**——编制合理性、职责边界判断。当前由面板代理 `panel-cho` 执行并审计留痕，未来由 CHO agent 会话执行（registry 第 122 行、规范 §二 Close Skill 行）。
- **代码落点**：CHO 白名单 `CHO_ALLOWED = ['cho', 'chief-human-resources-officer', 'ceo', 'panel-cho']`（`staffing.ts:181`），`note` 字段（`staffing.ts:189`）承载裁决理由，审计 JSON 原样落档。
- **为什么 CEO 也在白名单里**：开业期 CHO 尚未上岗时由 CEO 代行审批是现实需要；`panel-cho` 是面板代理身份，让"人肉点批准"也有归因主体。这正是补齐项"CHO agent 会话自动审批"存在的原因。

### 段 10：Close CLI（终态持久化）与终态

- **不变量**：终态持久化 + 合同校验（spec §2.5：校验裁决格式、证据引用、状态转换和权限，失败进 `CLOSE_REJECTED` 不得静默完成）。
- **004 载体**：`POST /staffing/decide`（`staffing.ts:171-220`）：
  - 权限校验：非 CHO 白名单 → 403 `cho_gate`（`staffing.ts:182-184`）——这就是 Close CLI 的"权限门"。
  - 寻址与防重放：requestId 不存在或已不处于 pending-cho → 404 `request_not_found`（`staffing.ts:178-180`）——同一请求二次 decide 会被 404 拒绝，天然防重复终态写入。
  - 终态写入：改 `status`/`decidedAt`/`approver`/`approverRole`/`note` 后全量写回 requests.json（`staffing.ts:185-190`）；批准分支追加名册写入 + 审计 JSON `dataDir/staffing/CHO-staffing-<requestId>.json`（`staffing.ts:199-214`）。
- **终态词表**（规范 §二）：`APPROVED`（名册 active）/ `REJECTED`（回 candidate 可再申请）/ `BLOCKED`（链态/重复/不存在）。驳回路径上 requests.json 保留 `rejected` 记录，而 roster 的 pending 映射只收 `pending-cho`（`staffing.ts:61-63`），所以驳回岗位自动回落 `candidate`——E2E ⑦ 验证的就是这个"可再申请"。

---

## 四、staffing 三端点全解（接手视角）

规范 §三（`candidate-staffing-fade.md` 第 38-45 行）定义 API 面；执行体函数与 HTTP 路由的挂载关系见 registry 第 127 行"执行体：TriLC src/company/staffing.ts + 3 端点"。

### 4.1 GET /internal/v1/staffing/roster

```ts
// staffing.ts:56-92（节选）
const roster = roles.map((r: any) => {
  const emp = active.get(r.roleId);
  const req = pending.get(r.roleId);
  return {
    roleId: r.roleId,
    displayName: r.displayName ?? r.roleName ?? r.roleId,
    ...
    employeeName: emp?.name ?? null,
    status: emp ? 'active' : req ? 'pending-cho' : 'candidate',
    onboardedAt: company.onboardedAt ?? null,
    requestId: req?.requestId ?? null,
  };
});
return { chainState, companyState, roster, counts: { total, active, pending } };
```

读法：三个数据源合成一份投影——role-catalog（JD 全集）、company.employees（在岗 Map，按 role 索引）、requests（pending Map，按 roleId 索引）。状态判定一行三元式。**注意**：一个 roleId 同刻只可能呈现一种状态，active 优先于 pending——代码里 `already_active` 409 门（`staffing.ts:146-149`）保证了不会同时出现在岗和待审。

### 4.2 POST /staffing/onboard

门禁顺序（全部命中即短路返回，`staffing.ts:137-168`）：

| 顺序 | 条件 | 状态码 | error 码 |
| --- | --- | --- | --- |
| 1 | 链态不在 ready/confirm/sync | 409 | chain_state_gate |
| 2 | role-catalog 未加载 | 503 | role_catalog_unavailable |
| 3 | roleId 不存在 | 404 | role_not_found |
| 4 | 已在岗 | 409 | already_active |
| 5 | 已有待审请求 | 409 | already_pending |

全过后构造请求对象（双标识 + `pending-cho`）落盘，发布 `init:staffing-request`，返回 `202` + `requestId`/`runId`/`statusText: 'pending-cho'`（`staffing.ts:167`）。**202 而非 200 的语义**：受理了但终局未定，等 CHO 裁决。

### 4.3 POST /staffing/decide

请求体 `{requestId, decision, approver, note}`，decision ∈ `approved | rejected`。处理序：404（找不到/非 pending）→ 403（CHO 门）→ 状态机变更 + 落盘 → 批准分支（名册写入 + 审计 JSON + `init:staffing-approved`）/ 驳回分支（`init:staffing-rejected`）→ 200。

审计 JSON 是"官方形态"的落点（`staffing.ts:200-211` 构造、`staffing.ts:212-214` 写 `CHO-staffing-<requestId>.json`），字段与分身编制审批单 CHO-clone-staffing 形态对齐：`requestType / approver / approverRole / decision / employee / requester / runId / note / conditions / auditAt`。`conditions` 里固化了一条边界："岗位 JD 单一真源（TriCompany 合同）；分身 spawn 走 clone-dispatch 协议另批"——上岗批准不自动给分身编制，两层 HC 分开批。

### 4.4 运行态门禁三函数（FADE-ASSESS-005）

`staffing.ts:7-11` 头注释记载：2026-08-20 CEO 启动"上岗 gating"——roster 三态从"状态记录+徽标"升级为**运行态门禁真源**。

```ts
// staffing.ts:114-134（三函数关系）
export async function getRoleRosterStatus(deps, roleId): Promise<'active'|'pending-cho'|'candidate'|'unknown'>
export async function isRoleActive(deps, roleId): Promise<boolean>        // === 'active'
export async function enforceRoleActive(deps, roleId): Promise<RosterGateResult>
// 非 active → { allowed: false, status, error: 'owner_not_active' }
```

设计意图（`staffing.ts:9-11`）：派工 owner 校验、分身 spawn 前置、cron 拉起前置**三处门禁共用这一个校验函数**，保证错误语义一致（`owner_not_active`，不静默）。接手提示：registry 第 130 行补齐项仍列着"分身 spawn 前置校验「JD 已上岗」"——门函数本体已在执行体落地，spawn 侧接线进度以 registry 补齐项口径为准核对，不要凭本教程断言已全接线。

---

## 五、员工对象发布段：多宿主渲染模型衔接（spec §6.2）

2026-08-19 整合定调（`ade-consolidation-proposal.md`，CEO 采纳）把"员工对象发布"并入 FADE-004，扩为 **ADE-B 员工域**（registry 第 132 行）：**上岗链 + 发布链同一生命周期域**。发布链四段衔接：

1. **host object 生成**：声明面 `HostObjectSetDefinition`（live_entry_status/host_stage/live_entry_ref）驱动生成式渲染——"声明面渲染是生成式而非复制式"（提案 §二，这是它与发布域字节复制面的本质区别，属"实例特有不可合并"项）。
2. **binding profile**：定性为发布绑定关系的**派生记录**（liveEntry 绑定关系 + supportObjects 资产清单 + runtimeNamespaces），**禁人工编辑、由生成管线重建**（提案 §三 ADE-B"binding profile 收敛"节）——与 D-07 同构。
3. **委托 publish-agents**：员工发布 CLI `employee_host_publish` 内部经 `_delegate_agent_publish` 子进程桥接 `source_publish_check --publish-agents`（提案 §一，employee_host_publish.py:281）；员工域经 `employee_host_publish` 委托复用 publish-agents scope，不产生第四 scope（spec §2.2）。
4. **治理回填**：CHO 审批门只在决策点（上岗），执行点只做契约校验，**不保留第二道 CHO 门**——"重复审批是产品噪音"（提案 §四）。发布链 runtime 侧等价映射：`roster.active` 即上岗绑定、`roster.status` 三档即 manifest 等价物（提案 §三"发布链 runtime 侧等价映射"节）。

多宿主渲染模型本体（spec §6.2，第 336-343 行）：宿主注册表 `HOST_RENDER_REGISTRY` 每宿主一条（渲染模板+live manifest+保护白名单）；copilot 是字节保真复制面、claude 是渲染面（工具名映射+硬白名单+`tool_drops` 审计）；`--host={copilot|claude}` 显式参数；未来新宿主=注册表加条目，**发布流程零新增**。运行时纪律对照 `engineering-disciplines.md` **D-07**：live entry 是派生加载壳，禁人工直接编辑，改动一律走源侧后 `--publish-agents` 重新发布覆盖+审计留痕。

---

## 六、必备节二：E2E 8/8 与真实运行证据

### 6.1 E2E 八分支（2026-08-18，隔离 dataDir + 种子开业态，8/8 PASS）

真源：`candidate-staffing-fade.md` §六。逐条对照代码门：

| # | 分支 | 期望 | 代码落点 |
| --- | --- | --- | --- |
| ① | 开业选定打钩 | 总助 active | 开业装配写入 employees；roster 回读 |
| ② | CMO onboard | 202 pending（requestId+runId） | `staffing.ts:154-167` |
| ③ | pending 可见 | roster 含 pending + counts 回读 | `staffing.ts:61-63,86-90` |
| ③b | 重复 onboard | 409 already_pending | `staffing.ts:150-153` |
| ④ | 非 CHO 审批 | 403 cho_gate | `staffing.ts:181-184` |
| ⑤ | CHO 批准 | 200（名册写入+审计落盘） | `staffing.ts:185-215` |
| ⑥ | roster 回读 | CMO → active（2/13 在岗） | `staffing.ts:56-92` |
| ⑦ | 驳回 | 回 candidate 可再申请 | `staffing.ts:216-218` + pending 过滤 `61-63` |
| ⑧ | 审计 json | 官方形态文件落盘 | `staffing.ts:212-214` |

复评报告卷 `FADE-004-report-rereview-2026-08-20.json` 把这 8 步逐条封装进了 envelope（scope=`candidate-staffing`，`run_id: "e2e-20260818-isolated"`，8 items，status pass）——注意 ③b/④ 两项以 `action: "error"` 记录，`errors: 0` 的口径是"预期拒绝路径如实发生"，不是故障。

### 6.2 隔离环境证据两件（批次 2 复现产物）

`fade-papers/FADE-004-evidence/` 下有两份从隔离 dataDir 回放的官方形态证据：

- **`CHO-staffing-staffing_mt1bgj61_xeiq.json`**（CMO 批准审计单）：`requestType: STAFFING_ONBOARDING_APPROVAL`、`approver: panel-cho`、`approverRole: ChiefHumanResourcesOfficer`、`decision: APPROVED`、`employee: { roleId: chief-marketing-officer, displayName: 市场总裁（CMO）}`、`requester: ceo-panel`、`runId: staffing_mt1bgj61_07kw`、`note: "E2E 复现（批次2 验证）"`、`auditAt: 2026-08-20T09:26:51.207Z`（北京时间 17:26:51）。与 `staffing.ts:200-211` 的审计构造逐字段对齐。
- **`requests.json`**（三条请求全谱系）：CMO `staffing_mt1bgj61_xeiq`/`staffing_mt1bgj61_07kw` **approved**；CFO `staffing_mt1bgjbf_qmvv`/`staffing_mt1bgjbf_hnfp` **rejected**（note"驳回演示"）；CFO `staffing_mt1bgjby_jomu`/`staffing_mt1bgjby_xhm6` **pending-cho**。一个文件里三态俱全，是读代码时最好的对照样本。

### 6.3 commit 与时间线（机器轨 UTC Z + 人读轨北京时间，D-04 v4）

| 时刻（UTC Z） | 北京时间 | 事件 |
| --- | --- | --- |
| 2026-08-17 12:33:33 +0800 | 同左 | commit `ea05817e`：`docs(hc): CHO 分身编制审批单 001 — APPROVED 3 小柯分身`（首评期的"近邻证据"锚，见 report 卷 scope_specific.git_commit） |
| 2026-08-18 | — | E2E 8/8 首跑（隔离环境） |
| 2026-08-20T04:29:17Z | 12:29 | Score CLI 覆盖卷：100/100 PASS |
| 2026-08-20T04:29:26Z | 12:29 | 首评合成卷：81/100 PASS |
| 2026-08-20T09:26:51Z | 17:26 | 批次 2 E2E 复现，官方形态审计+requests.json 证据落盘 |
| 2026-08-20T10:52:52Z | 18:52 | 复评合成卷：88/100 PASS |

同一时刻弧线 04:29Z → 09:26Z → 10:52Z 讲了一个完整故事：**首评 → 证据补齐 → 复评升级**。卷内一切 JSON 时间戳保持 UTC Z 机器轨（D-04 v4 机器轨不改），面向人的叙述对齐北京时间。

---

## 七、必备节四：评分卷宗解读（首评 81 → 复评 88 两卷对照）

### 7.1 试卷结构

试卷 `FADE-004-paper.json`：10 项 × 权重 10 = 满分 100，及格线 threshold **80**，双门槛（必选项全过 且 总分达标，spec §2.6）。前 6 项 `required: true`（trigger-config / run-id-carrier / skill-docs / cli-report / audit-record / terminal-sample），后 4 项是实例特有项（cho-gate / dedup-409 / chain-gate / roster-readback）。试卷 notes 里有一条**诚实的评分口径**：官方审计形态文件当时在隔离 E2E dataDir 本机不可得，audit-record"按近邻证据计分"——这条注记直接解释了下面的 6 分。

### 7.2 逐项对照表（数据取自两份 score JSON，可逐数复核）

| 检查项 | 必选 | 首评 | 复评 | 变化 | 复评 evidence_ref |
| --- | --- | --- | --- | --- | --- |
| trigger-config | 是 | 8 | 8 | — | candidate-staffing-fade.md |
| run-id-carrier | 是 | 7 | 9 | **+2** | TriLC/src/company/staffing.ts |
| skill-docs | 是 | 9 | 9 | — | candidate-staffing-fade.md |
| cli-report | 是 | 8 | 9 | **+1** | candidate-staffing-fade.md |
| audit-record | 是 | 6 | 9 | **+3** | FADE-004-evidence/CHO-staffing-staffing_mt1bgj61_xeiq.json |
| terminal-sample | 是 | 9 | 10 | **+1** | candidate-staffing-fade.md |
| cho-gate | 否 | 9 | 9 | — | TriLC/src/company/staffing.ts |
| dedup-409 | 否 | 9 | 9 | — | TriLC/src/company/staffing.ts |
| chain-gate | 否 | 8 | 8 | — | TriLC/src/company/staffing.ts |
| roster-readback | 否 | 8 | 8 | — | TriLC/src/company/staffing.ts |
| **合计** | | **81** | **88** | +7 | 4 项升级，**无降项**（registry 第 131 行口径复核一致） |

复核练习：首评 8+7+9+8+6+9+9+9+8+8=81；复评 8+9+9+9+9+10+9+9+8+8=88。建议新人亲手加一遍——评分卷宗必须可复算。

### 7.3 为什么 audit-record 首评只有 6：证据可回放性教训

首评卷 audit-record 的 evidence_ref 指向 `operating-records/2026-W34/CHO-clone-staffing-20260817-001.json`（分身编制审批单，`ea05817e`）——这是**形态对齐的近邻证据**，不是 004 自己的官方形态文件。官方形态 `CHO-staffing-<requestId>.json` 当时只存在于隔离 E2E dataDir，评分者拿不到。批次 2 复现（08-20 17:26 北京）把官方形态审计与 requests.json 回放到 `fade-papers/FADE-004-evidence/`，复评时 evidence_ref 才换成了真证据，6→9。

教训（已沉淀为制度）：**证据必须在评分时点实际可得、可被卷宗引用**。这正呼应 D-01"口头已落盘不可信"的评分版——隔离环境里跑出来的东西，不回放到可归档位置，就等于没跑。也注意试卷本身（`FADE-004-paper.json` 第 54 行）早就把目标证据形态声明为 `FADE-004-evidence/CHO-staffing-...`——试卷先行声明目标形态、证据后到位、复评对卷，这就是 spec §2.6"试卷—答卷—评分"三件套的实战样本。

---

## 八、必备节三：故障弧线与教训（D 系纪律关联）

### 8.1 隔离环境证据缺口 → D-01 与评分制度

首评 81 的 7 分缺口几乎全部来自"证据不可得"。弧线：E2E 在隔离 dataDir 跑通（08-18）→ 评分时官方证据不在本机（08-20 12:29）→ 近邻证据计 6 分 → 批次 2 回放证据（17:26）→ 复评对卷升级（18:52）。**教训**：跑通不等于可审计，落盘位置决定证据资格。关联 D-01（先写后报、收稿三查）——score JSON 的 evidence_ref 就是"收稿三查"的制度化。

### 8.2 CompanyInitState 缓存失效缺陷（DEFECT-RESET-CACHE）

`init-state.ts:81-84`：reset 删除状态文件后未失效内存 cache，导致 assemble 的幂等检查（`employees_mismatch 409`）读到**陈旧的 employees 缓存**——"补丁没生效"类假故障的缓存版。教训：任何破坏性操作（reset/删档）必须同步失效内存缓存；读路径带 cache 的服务，排查先怀疑缓存。这与 D-03 v2"shell env 快照"是同一类病：**进程内存里的旧快照掩盖了磁盘/注册表的新事实**。

### 8.3 tmp+rename 注释与实现漂移（已知缺陷，读码必看）

`init-state.ts:86` 注释声称 `atomic write: tmp → rename`，但 `init-state.ts:91-94` 实际是 **tmp 直写 → 目标直写 → unlink tmp**——没有 rename 调用，中断窗口内 state.json 可能半写。这不是教程新发现：`init-chain.ts:248-249` 注释明确记载这是**已知缺陷且链路态不复刻**：

```ts
// init-chain.ts:247-249（节选）
const tmp = `${this.statePath}.tmp`;
// 真原子写：tmp 直写 → rename 覆盖（与 init-state.ts 的「tmp 直写 + 目标直写
// + 删 tmp」假原子写区分——那是公司态已知缺陷，链路态不复刻）
```

`init-chain.ts:241-258` 给出了正确范式的完整实现：tmp 直写 → `rename` 覆盖 → **校验读回**（eventSeq/chainState 不符即抛错）。规范里"tmp+rename 原子"的表述（candidate-staffing-fade.md DCE 行）对应的是设计意图；公司态实现滞后。**培训立场**：如实记录偏差，修复裁决归 CTO 技术真源，本教程不改代码。接手者排查 state.json 写坏问题时，这里应第一个想到。

### 8.4 时刻引用（D-04 v4 双轨时刻制）

本实例所有 JSON 合同（requests.json 的 `requestedAt/decidedAt`、审计 JSON 的 `auditAt`、评分卷的 `scored_at`）一律 ISO8601 UTC Z 机器轨；本文档叙述性时间用北京时间并括注 Z 原值。D-04 v3 的"僵了 8 小时"误报（UTC 数值与北京钟读数直接相减）在本链路同样适用：比较任何两个时刻前，先确认同一时区帧。

### 8.5 派生壳与双真源漂移（D-07）

员工域发布链里 live entry 与 binding profile 都是派生物、禁人工编辑（第五节）。反面场景：有人直接改 `.github/agents/*.agent.md` 而不动源侧 contract——下次 publish 会覆盖回渲染结果并审计留痕，改动无声丢失。新人记住一句：**要改员工，改源侧，走发布管线**。

### 8.6 链态机的两笔历史修复（读 init-chain.ts 的赠品）

`init-chain.ts:434-436` DEFECT-RESET-PATH：reset 用 `dirname(init-chain.json)`（=company/）当 dataDir，导致兄弟路径全部双嵌套（company/company/state.json），state.json 永远删不掉。`init-chain.ts:453-455` 竞态修复：reset 时**不 unlink init-chain.json**——unlink 会开"文件不存在窗口"，并发 load() 命中 catch 写回默认帧，覆盖 reset 的 selfcheck 终态（CEO 手测"重置后自检卡不出现"的根因）。教训：并发读路径下，删文件比改文件危险；原子覆写优于先删后写。

---

## 九、必备节五：与 FADE 协议 v2.0.0（§2.7/§2.8）对照

### 9.1 为什么 004 是"节点收口报告按段适用"的唯一样本

登记册 v1.2 注记（fade-registry.md 第 17 行，2026-08-27 六实例反向工程）裁定：§2.7 节点收口报告仅适用多节点实例——**001/002/003 单段脚本/CLI 实例豁免，004 HTTP 链多节点按段适用**。004 的"多节点"指 HTTP 链天然跨越多个执行体边界：TriCade 呈现面 → daemon onboard 端点 → CHO 面板裁决 → daemon decide 端点 → CompanyInitState 持久层 → 审计落盘 → 员工发布委托链。每个边界都是"节点完成"的时刻。

**如实标注现状**：§2.7 立法于 2026-08-27，而 004 的 E2E/评分跑于 2026-08-18/20——属前标准期。004 现存证据（E2E 八分支记录、report 卷 envelope、审计 JSON、requests.json）已覆盖 §2.7 十字段中"动作序列/工件清单/门禁结果"的实质，但**没有** `reports/node-<NODE-ID>.md` 形态的逐节点文件，也未过 `node-report-check` 校验器。按 spec 细则 10"不溯及既往"：既有 run 不追改，**004 的下一个 run 起按现行法逐节点落收口报告**。这是接手者最容易踩的时点坑——别拿 2026-08-27 的法去否定 08-18 的卷，也别拿 08-18 的卷宣称满足 08-27 的法。

### 9.2 §2.8 登记四不变量在 004 的满足

| 不变量 | 004 实现 | 证据锚 |
| --- | --- | --- |
| 唯一性 | 一次申请一个 requestId（RID 毫秒戳+随机） | requests.json 三条记录 ID 互异 |
| 去重性 | already_active / already_pending 双 409 门 | `staffing.ts:146-153`；E2E ③b |
| 关联性 | runId 贯穿 requests.json → 审计 JSON → 评分 evidence_ref | 审计单 `runId: staffing_mt1bgj61_07kw` 与 requests.json 同值 |
| 恢复锚 | requests.json 持久 + 状态字段，daemon 重启后 loadRequests 原样恢复 | `staffing.ts:41-47` |

判例对照（spec 细则 6）：runId 单一字段非必须，等价聚合键必须——004 是"显式双标识"形态，spec §2.8 合法载体清单里点名"requestId+runId（员工域）"。

### 9.3 004 对照 v2.0.0 的差距清单（补课挂账，不粉饰）

1. Verify 段未独立设段（回读折叠进 Close CLI）——现行法下可选段允许空缺，如实声明即可；
2. §2.7 节点收口报告与校验器未在 004 实跑——下一个 run 强制；
3. §2.8"段-实现映射表"未在 004 条目内 schema 化填制（登记册仅 006 首行填制）——补课范围以联审裁定为准；
4. Score 双段（coverage + quality）已齐且双门槛判定在卷——这一项 004 是达标的。

---

## 十、005 编号沿革与补齐项

### 10.1 为什么编号跳过 005

三个真源互相印证：① registry 第 153 行备注"编号跳 005 沿用 08-21 勘误口径（005 已并入 FADE-004 员工域）"；② `ade-consolidation-proposal.md` §三："候选 4 是 FADE-004'上岗'后的工件落地段……本是一条链——合并后员工生命周期一个 FADE，**避免另立 FADE-005**"（小乔贡献点，§贡献点标注节）；③ spec v1.2.1 变更记录（2026-08-21）：案例表移除与 FADE-004 扩容重复的"员工对象发布"行。**结论：005 不是被废棄的实例，而是从未独立立项——它的内容成了 004 员工域的发布链段。** 新人看到仓库里没有 FADE-005 文件，不要当悬案去"找回来"。

### 10.2 补齐项现状（registry 第 130 行，截至登记册 v2.1）

| 补齐项 | 现状 | 说明 |
| --- | --- | --- |
| CHO agent 会话自动审批 | 待实现 | 当前由面板代理 `panel-cho` 人工点批（CHO_ALLOWED 白名单第 4 项就是它）；CHO agent 上岗后可自动裁决 |
| 分身 spawn 前置校验「JD 已上岗」 | 门函数已落地，spawn 侧接线按 registry 口径核对 | `enforceRoleActive`/`isRoleActive` 即该门（FADE-ASSESS-005，2026-08-20 启动） |

---

## 十一、接手任务清单（新人 7 天路径）

1. **Day 1 读真源**：candidate-staffing-fade.md 全文 → fade-registry.md FADE-004 条目 → 本教程第三节。验证：能不看书画出十段-代码映射。
2. **Day 2 读执行体**：`TriLC/src/company/staffing.ts` 全文 221 行 → `init-state.ts` → `init-chain.ts:240-258`（原子写范式）。验证：说出 5 个门禁的触发条件与状态码。
3. **Day 3 读卷宗**：试卷 → 首评两卷 → 复评三卷 → 证据两件。验证：亲手复算 81 与 88，找到 4 处升级项。
4. **Day 4 复现 E2E**：隔离 dataDir + 种子开业态，按第六节表格逐步打（onboard 202 → 重复 409 → 非 CHO 403 → 批准 200 → roster 回读 active → 驳回回 candidate → 审计文件落盘）。验证：requests.json 出现三态记录。
5. **Day 5 对照新法**：对照 spec §2.7 十字段，为你的 E2E run 补写 `reports/node-*.md` 并自建段-实现映射表——这就是 004 的补课实操。
6. **Day 6 摸发布链**：读 `ade-consolidation-proposal.md` §三 ADE-B + spec §6.2 + D-07；找到 `employee_host_publish` 委托点。
7. **Day 7 答辩**：回答三个问题——为什么双标识？audit-record 为什么 6→9？004 下一 run 必须新增什么工件？答不全就回 Day 1。

红线提醒：改员工相关任何面，先分清决策面（名册，走 staffing API）/信息面（contract，走源侧）/适配面（live entry，禁手改）；时刻一律现查系统时钟；评分数字必须可复算后才可引用。

---

## 十二、心智模型沉淀（可复用骨架）

给下一门研发课直接复用的四条骨架：

1. **HTTP 链生命周期骨架**：呈现面触发 → 端点受理（202+双标识）→ 机械门链（链态/存在性/重复）→ 语义裁决门（角色白名单 403）→ 确定性落盘（状态文件+审计文件双写）→ 投影回读（roster 三态合一）。任何"申请-审批-生效"类功能都可套。
2. **证据资格骨架**：跑通 ≠ 可审计；证据必须落在评分时点可引用的位置（evidence_ref 实际可达），试卷先声明目标形态，证据后到位则复评对卷。
3. **不变量/载体分层骨架**：协议管四不变量（唯一/去重/关联/恢复锚），实例自选载体并入册声明；评审时先问不变量是否满足，再争论载体好坏。
4. **读码四查骨架**（本实例专属）：查注释与实现是否一致（tmp+rename 案例）、查缓存与磁盘是否同帧（DEFECT-RESET-CACHE）、查删文件是否开竞态窗口（init-chain reset 案例）、查时间戳是否同轨（D-04）。

---

## 使用依据

本教程全部事实取自以下真源（Read 工具逐文件取证，未采信任何记忆性数字）：

- `D:/Code/ai/TriCompany/docs/engineering/fade-registry.md`（FADE-004 条目第 114-132 行、v1.2 注记第 17 行、005 备注第 153 行）
- `D:/Code/ai/TriLC/src/company/staffing.ts`（全文 221 行）
- `D:/Code/ai/TriLC/src/company/init-state.ts`、`D:/Code/ai/TriLC/src/company/init-chain.ts`
- `D:/Code/ai/TriMetaverse/docs/execution/candidate-staffing-fade.md`
- `D:/Code/ai/TriCompany/docs/engineering/fade-papers/`：`FADE-004-paper.json`、`FADE-004-score-2026-08-20.json`、`FADE-004-score-2026-08-20.coverage.json`、`FADE-004-score-rereview-2026-08-20.json`、`FADE-004-quality-rereview-2026-08-20.json`、`FADE-004-report-rereview-2026-08-20.json`、`FADE-004-evidence/CHO-staffing-staffing_mt1bgj61_xeiq.json`、`FADE-004-evidence/requests.json`
- `D:/Code/ai/TriCompany/docs/engineering/fade-protocol-spec.md`（§1.1/§2.1/§2.5/§2.6/§2.7/§2.8/§6.2）
- `D:/Code/ai/TriCompany/docs/engineering/ade-consolidation-proposal.md`
- `D:/Code/ai/TriCompany/docs/workflow/engineering-disciplines.md`（D-01/D-03/D-04/D-07）

声明：本篇是培训材料，不是事实裁决。第八节 8.3 的 tmp+rename 偏差与第九节补课清单的执行裁决，分别归 CTO 技术真源与协议三方联审；教程只负责如实呈现与指路。
