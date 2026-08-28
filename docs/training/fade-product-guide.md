# FADE 产品版教程：使用方操作指南

版本：V1.1
日期：2026-08-20（原立）/ 2026-08-28（对齐规范重构）
状态：当前教程（FADE 已全链落地，规范 v2.0.x 对齐版）
维护人：RAndDTrainer（小吴）
适用对象：使用 FADE 实例的协作者——CEO、总助、CHO、CPO/CTO、各岗位员工，以及需要发起或审批 FADE 流程的任何角色

> **版本对齐标注（2026-08-28）**：工程规范已完成 ade-pattern-spec.md → **fade-protocol-spec.md v2.0.0** 架构重构（ADE 概念退役，FADE 升为协议本体，FADE-XXX 为协议实例的具体实现；envelope 降格为发布域参考实现；旧规范文件保留为重定向桩）。本文已同步迁移：术语（运行标识）、域称（发布域/员工域，历史代号 ADE-A/B）、实例清单（五实例）、真源链接均已对齐 v2.0.x。**本教程随 fade-protocol-spec.md 更新而联动更新**，后续不再保留滞后差异注记。

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-product-guide.md
- syncMode: follow-spec（本教程讲 FADE 实例的使用方法与操作口径；工程规范真源 = `../engineering/fade-protocol-spec.md`（v2.0.0 起，替代 ade-pattern-spec.md），实例登记真源 = `../engineering/fade-registry.md`，试卷模板真源 = `../engineering/fade-assessment-paper-template.md`；教程随三者联动更新——规范每升版，本文同步核对修订）
- syncWith: docs/engineering/fade-protocol-spec.md, docs/engineering/fade-registry.md, docs/engineering/fade-assessment-paper-template.md
- lastSyncedAt: 2026-08-28

## 1. 这份教程解决什么问题

你不需要写代码，但你需要知道：

1. 手头的活属于哪个 FADE 实例，走哪条链。
2. 什么时候需要你出手（触发 / 出试卷 / 审批 / 评分 / 收口）。
3. 评分结果怎么看、卡在哪儿、下一步找谁。

FADE 对使用方的承诺是：**你只需要做"人的判断"（要不要干、干得对不对、批不批），机器会做"确定的事"（执行、记账、收口）。** 本教程告诉你"人的判断"在哪些节点出现。

## 2. 五实例使用总览

| 实例 | 你什么时候用它 | 你的角色 | 入口 |
| --- | --- | --- | --- |
| FADE-001 周工作平面迁移 | 每周日 23:00 自动发生 | 无操作（纯自动） | TriMC cron（`0 23 * * 0`） |
| FADE-002 公司文档管理 | 真源文档变了要发副本/摘要；AI 员工档案要发布 | 发起者（小贾/小赛）；联审者（小乔/小狄） | `source_publish_check` CLI |
| FADE-003 共学周记记录 | 要记本周 AI 共学周记 | 发起者（任何人） | `journal-cli.mjs` / 共学周记 prompt |
| FADE-004 候选岗位发布 | 有新岗位要上岗 / 要审批上岗 | 发起者（CEO 勾选）；审批者（CHO） | TriCade settings→agents / staffing API |
| FADE-006 执行面自动拾取 | 本地定好计划（任务说明书→拆树）投送后，执行面自动接单 | 计划方（M 面 TriMLC+CEO 拟说明书、拆树、材料预封卷）；收口对账（小贾） | 本地 `git push sg-bare`（hook 秒级派 tick，trimc cron 慢通道兜底） |

**先判断你的活属于哪条链**：要发文件走 FADE-002，要记周记走 FADE-003，要上人走 FADE-004，定好的计划要执行面自动接单走 FADE-006。不要混用入口（比如不要用 FADE-002 的命令去记周记）。

## 3. FADE-002 发布链怎么用（文件/档案发布）

FADE-002 是"公司文档管理"（发布域，历史代号 ADE-A），CLI 是 `source_publish_check`，一个命令三个面：

| 面 | 干什么 | 关键参数 |
| --- | --- | --- |
| sync | 源侧→发布侧目录同步（机械复制） | `--check` / `--check --sync` |
| project-docs | 项目真源文档同步（含语义摘要） | `--project-docs [--project-docs-execute]` |
| publish-agents | AI 员工档案发布（多宿主渲染） | `--publish-agents [--agent-execute] [--host=copilot|claude]` |

**使用铁律：默认是演练（dry-run），不写任何文件。** 确认演练结果符合预期，才加写入参数。

### 3.1 先演练（任何发布的第一步）

在 `TriCompany/` 根目录执行（以下命令均默认不写入）：

```powershell
python -m runtime.cognition.source_publish_check --source-root . --workspace-root .. --project-docs
```

输出是 JSON 报告（ade-report envelope）。你只需要看三个值：

- `status`：`pass`（全部一致）/ `partial`（有摘要需要候选）/ `fail`（有错误）
- `summary.errors`：大于 0 说明有错，先解决再继续
- `items[].action`：逐条动作（`in_sync` 无需处理；`requires_candidate` 需要小贾准备摘要候选）

### 3.2 发 AI 员工档案（多宿主渲染）

```powershell
# 发布到 Copilot-host 面（.github/agents/，默认）
python -m runtime.cognition.source_publish_check --publish-agents

# 发布到 Claude Code 面（.claude/agents/，走渲染管线）
python -m runtime.cognition.source_publish_check --publish-agents --host=claude
```

先跑不带 `--agent-execute` 的版本看 `derived_identical`（已一致）/ `derived_drift`（有漂移）计数。确认无误后再加 `--agent-execute`。

**重要**：`.github/agents/`、`.claude/agents/`、`.github/binding-profiles/` 是保护目标，只有这条发布链的显式执行能写；你手工改它们是违规的（live entry 是渲染产物，禁人工编辑）。

### 3.3 自动触发面（event-watch）

FADE-002 已支持事件自动触发：

```powershell
# 单次扫描批次（默认 dry-run，无写入）
python -m runtime.cognition.source_publish_check --event-watch
```

- 监听 `source-agents/`、`docs/engineering/`、`.github/manifests/` 的文件变化 + Git HEAD/refs 变化。
- 首次运行只建立基线不触发；之后有变更才触发检查。
- 写入必须显式加 `--auto-sync`；`project-docs` 面永不自动写（摘要必须人工候选 + 联审）。
- 审计落在 `<source-root>/.ade/event-watch/`（events.jsonl + reports/ + state.json）。

使用建议：这个面交给 daemon 定时唤起（定时巡检链），人不直接操作。

## 4. FADE-003 周记链怎么用（记录归档）

入口有两个：`.github/prompts/项目级 AI 共学周记.prompt.md`（Copilot-host 可直接调），或 CLI。

CLI 操作三步（每步都带同一个 runId，单号要对得上）：

```powershell
# 1. 开启一笔记录（生成 runId）
node journal-cli.mjs begin --title "W35 共学周记"

# 2. AI 起草后机械资格检查 + 追加（qualify 不通过会提示修改）
node journal-cli.mjs qualify --entry <entry.json> --run <runId>
node journal-cli.mjs append --entry <entry.json> --run <runId>

# 3. 语义裁决 + 收口（verdict 当前实现为 approved / escalated 两态；
#    升四态 RETRY/FROZEN 已立项登记 R-C4，落地后此处同步）
node journal-cli.mjs close --run <runId> --verdict approved --note "..."
```

- 去重：同一题目重复记录会被拦截（同题去重）。
- 审计：`journal-run-log.jsonl` 记录每一步，收口前会做"五查"。
- 触发链：现在以手动 prompt 为主；cron 自动触发是补齐项（依赖 TriMC resident 链路）。

## 5. FADE-004 上岗链怎么用（人员上岗）

链路：**候选全集 → CEO 勾选 → 待 CHO 审批 → 进在岗名册**。

呈现面是 TriCade settings→agents（或 daemon API）：

| 操作 | 谁做 | 现象 |
| --- | --- | --- |
| 开业勾选 | CEO | 选定岗位直接进名册（"在岗"徽标锁定） |
| 后补勾选 | CEO | 提交上岗申请 → "CHO 审批中"徽标 |
| 审批 / 驳回 | CHO | 批准 → 进在岗名册；驳回 → 回候选可再申请 |
| 未开业勾选 | 任何人 | 409 拒绝（"开业完成后才允许增员"） |

门禁语义（2026-08-20 上岗 gating）：**在岗 = 可被派工 / 可被 spawn 分身 / 可被调度拉起；未上岗只可见不可用**。

- 派工：派发请求携带 `ownerRoleId` 才会校验在岗；未在岗返回 409 `owner_not_active`。
- 调度：cron job 绑定 `roleId` 才会校验；未在岗任务 skipped 并记原因，不静默。
- 权限：审批人必须是 CHO（或代批面板 panel-cho）；非 CHO 审批 403。

错误码速查：`owner_not_active`（派工 409）/ `role_not_active`（分身工具错误）/ `skipped + owner_not_active`（调度跳过）——三处都不静默。

## 6. 试卷怎么出（FADE 实例的"考卷"）

每个 FADE 实例要配齐"试卷—答卷—评分"。**出试卷是你的职责之一**（通常由实例 owner + 联审人出，格式见 `fade-assessment-paper-template.md`）。

试卷 = 固定部分 + 实时部分：

- **固定部分**（每实例都有，见模板 §1.1）：六项必查——触发器配置、运行标识载体（如 runId）、Skill 承载文档、CLI 命令与报告、审计记录、终态样本。这六项是"必选项"，任何一次评分都全查。另有**治理对齐项**（v1.2.0 起，spec §2.6）：职责范围与绑定事实是否与最新治理定调一致——防"只查证据存在性、不查内容对不对"。
- **实时部分**（按实例声明）：评分项清单，每项含 `id / label / weight（权重，总分 100）/ standard（通过标准）/ evidence_ref（证据引用）/ required（是否必选）`。
- **测试集**（提前备好）：列出 CLI 必做工作（must_do）+ 验证方法（verify_method）+ 质量判定标准。它是事后评分"有没有漏做、做得好不好"的依据。

实操建议：新开一个 FADE 实例时，在 Plan Skill 阶段就声明好试卷（检查项 + 权重 + 及格线）；每次执行完跑一次评分留存。及格线默认 80/100，阈值声明要 ≤ 总分上限（否则永远过不了线）。

## 7. 评分怎么读

评分命令（Score CLI，TriCompany 侧）：

```powershell
python -m runtime.cognition.source_publish_check --score `
  --score-paper <试卷.json> --score-report <本次执行报告.json> `
  [--score-quality-scores <Score Skill 质量评分.json>] [--score-threshold 80]
```

输出评分合同（JSON），只读四个关键值：

| 字段 | 含义 | 你要看的 |
| --- | --- | --- |
| `verdict` | PASS / FAIL | 最终结论 |
| `required_all_passed` | 必选项是否全过 | false 即 FAIL，不看总分 |
| `total.score / total.max / total.threshold` | 总分 / 满分 / 及格线 | score ≥ threshold 才过第二门槛 |
| `items[].omission` | 该项是否遗漏（Score CLI 确定性判定） | true 的项目按 0 分计；必选项遗漏直接不过 |

**评分是两段合成**：Score CLI（机器）查"是否遗漏"（omission/required_all_passed，确定性）；Score Skill（AI）评"每项质量"（score，语义；评定维度含**治理对齐/内容归属**——内容是否属于该角色、职责范围与绑定事实是否与最新治理定调一致）。合并后按双门槛判 `verdict`。PASS ⇔ 必选项全过 且 总分 ≥ 及格线。

**读了评分之后**：

- PASS → 可以进入 Close 收口。
- FAIL 且是遗漏 → 补做漏掉的工作（RETRY）。
- FAIL 且是质量分不足 → 改进后重跑或升级裁决（ESCALATED）。
- 评分 JSON 是 Close Skill 裁决的客观证据，不能伪造或覆盖。

## 8. 终态与收口怎么走

Close CLI 是最后一道门（终态门），只有它能写入终态：

```powershell
python -m runtime.cognition.source_publish_check --close `
  --run-id <runId> --verdict APPROVED `
  --evidence-ref <证据文件路径> --source-revision <源修订标识>
```

- `--verdict` 只接受四词：`APPROVED`（通过）/ `FROZEN`（冻结）/ `ESCALATED`（升级）/ `RETRY`（重试）。
- 校验通过 → 写入终态审计记录 `<source-root>/.ade/<runId>.close-ade.json`，报告 `CLOSED`。
- 校验失败 → 报告 `CLOSE_REJECTED`，**绝不静默完成**（非零退出码 + 机器可读错误）。
- 同一 runId 只能 close 一次（防重复收口）。

使用方的判断点：**Close Skill（AI）给出语义裁决，Close CLI（机器）校验并落账。** 你（人）在 Close Skill 之前的裁决可以表达意见，但最终落账以 Close CLI 通过为准。

## 9. 触发链怎么走（什么时候开始）

| 场景 | 走哪条链 | 谁触发 | 说明 |
| --- | --- | --- | --- |
| 定时例行（周平面、巡检发布） | 定时巡检链（runtime-owned durable） | cron 唤起维护 Agent（小赛）→ 写周平面待办标注闲时执行 → daemon 闲时自动启动 | 任务不依赖单次会话存活 |
| 你现在就要办 | 即时触发链（Agent-owned interactive） | 指令 → 维护 Agent 立即触发 → 小贾建树 | 完整 FADE 即时执行 |
| 文件/Git 变化自动发现 | FADE-002 event-watch | `--event-watch` 单次扫描 / `--watch` 前台循环 | 默认 dry-run；`--auto-sync` 显式才写 |
| 计划投送后执行面自动接单 | FADE-006 执行面自动拾取 | 本地定计划拆树后 `git push sg-bare` → post-receive hook 秒级派 tick；trimc cron（:18/:48）慢通道兜底 | hook 快通道 + cron 慢通道双保险；计划即卷封，收口后 commit/push 回流 |

两条链的后续流程完全一致，区别只在"谁开的头"。触发探测与执行解耦：探测 Agent 只负责开启触发，执行由编排层（小贾）按 Trees 任务树拉起对应角色。

## 10. 常见问题（使用方）

**Q：我可以直接手工编辑发布侧的 AI 员工档案吗？**
不可以。`.github/agents/`、`.claude/agents/`、binding-profiles 是渲染/派生产物，禁人工编辑；不一致时用 `--publish-agents --agent-execute` 重新渲染覆盖（自动审计留痕）。

**Q：评分 FAIL 了还能收口吗？**
不能。评分不达线只能 RETRY 或 ESCALATED，不得写入终态（spec §2.6 硬门槛）。

**Q：谁有权审批上岗？**
CHO（首席人力官）或代批面板 panel-cho；CEO 代批为既有兼容行为。非 CHO 审批人一律 403。

**Q：daemon 的 cron 任务被跳过是坏事吗？**
要看原因。因岗位未在岗被 skipped 是有意设计（连续 3 次 skipped 会触发 degraded 告警，提醒岗位长期无人）；只有真实执行成功才解除 degraded。

**Q：我看到报告里 status=partial 是什么意思？**
部分通过。典型情况：published-summary 摘要过期，需要小贾准备候选 + 小乔/小狄联审后重跑。不是失败，是"等你出手"。

## 11. 真源回链

- 规范真源：[FADE 协议：Agent 确定性执行全生命周期规范](../engineering/fade-protocol-spec.md)（v2.0.0 起替代原 ADE 模式规范；旧路径 ade-pattern-spec.md 为重定向桩）
- 实例登记册（含各实例规范链接）：[FADE 成熟实例登记册](../engineering/fade-registry.md)
- 试卷模板：[FADE 试卷模板](../engineering/fade-assessment-paper-template.md)
- 历史整合设计（发布域/员工域两域由来，ADE-A/ADE-B 为历史代号）：[ADE 四候选整合提案](../engineering/ade-consolidation-proposal.md)
- FADE-006 规范：[fade-006-execution-autopick-spec.md](../../../TriMetaverse/docs/execution/fade-006-execution-autopick-spec.md)（管线设计：`fade-pipeline-design.md` 同目录）
- 知识注入规范：[knowledge-injection-spec.md](../../../TriMetaverse/docs/execution/knowledge-injection-spec.md)（FADE-ASSESS-003）
- 上岗 gating 规范：[fade-005-roster-gating-spec.md](../../../TriMetaverse/docs/execution/fade-005-roster-gating-spec.md)（FADE-ASSESS-005）
- 上岗链规范：[candidate-staffing-fade.md](../../../TriMetaverse/docs/execution/candidate-staffing-fade.md)
- 小白入门：[fade-beginner-course.md](fade-beginner-course.md)；实现细节：[fade-code-deep-dive.md](fade-code-deep-dive.md)