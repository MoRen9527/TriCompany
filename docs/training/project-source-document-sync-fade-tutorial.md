# 项目真源文档同步 FADE 教程

版本：V2.0
日期：2026-08-07（原立）/ 2026-08-28（改名迁移 + 现状对齐）
状态：当前教程（FADE 全链落地，规范 v2.0.x 对齐版）
维护人：RAndDTrainer（小吴）
适用对象：需要维护跨仓项目文档的研发、产品、技术与总助协作者

> **版本对齐标注（2026-08-28）**：① 工程规范已完成 ade-pattern-spec.md → **fade-protocol-spec.md v2.0.0** 架构重构（ADE 概念退役，FADE 升为协议本体，FADE-XXX 为协议实例的具体实现），本文随迁改名 `project-source-document-sync-fade-tutorial.md`；② 原 v1.1"完整 ADE 生命周期待实现"的状态句已过时——运行标识、Score CLI、Close CLI、event-watch 已于 2026-08-20 前后全链落地（FADE-002 复评 93/100），本文状态类表述已同步对齐实现现状。**本教程随 fade-protocol-spec.md 更新而联动更新。**

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/project-source-document-sync-fade-tutorial.md
- syncMode: follow-spec（本教程讲 FADE-002 发布域的项目真源文档同步面；工程规范真源 = `../engineering/fade-protocol-spec.md`（v2.0.0 起，替代 ade-pattern-spec.md），实例规范 = `../workflow/project-source-document-sync-ade.md`（文件名为历史命名），实例登记真源 = `../engineering/fade-registry.md`；教程随三者联动更新——规范每升版，本文同步核对修订）
- syncWith: docs/engineering/fade-protocol-spec.md, docs/workflow/project-source-document-sync-ade.md, docs/engineering/fade-registry.md
- lastSyncedAt: 2026-08-28

## 1. 学完能做什么

学完这份教程，你应该能独立完成五件事：

1. 分清项目真源、发布副本、发布摘要和审计记录。
2. 用 manifest 找到真源与目标文档之间的映射。
3. 先执行无副作用 dry-run，再判断是否需要写入。
4. 看懂 `pass`、`partial`、`fail` 三种 FADE 报告状态。
5. 在真源变化时，知道什么时候可以让 CLI 直接复制，什么时候必须由 Agent 先整理摘要候选。

当前成熟度是"FADE 全链落地"（生命周期骨架 2026-08-20 收口，FADE-002 复评 93/100）：

- 已实现 manifest 驱动的跨仓文档检查（DCE）。
- 已实现 `published-copy` 的确定性复制。
- 已实现 `published-summary` 的 source revision 校验和候选发布。
- 已实现 dry-run、显式写入、安全门、结构化 JSON 报告合同（envelope v1.0，发布域参考实现）与回归测试。
- 已实现运行标识（显式 `--run-id` / 时间戳派生 id）、Score CLI 试卷评分（`--score`）、Close CLI 终态门（`--close`）。
- 已实现 event-watch 触发面（`--event-watch` 单次扫描 / `--watch` 循环，state.json 基线）。
- 尚未实现：daemon 自动唤起链（automation-backlog 立项）、自动生成摘要候选、联审自动化、`audit-record` 同步。

## 2. 这项能力在全局哪里

项目文档常常同时存在两个位置：

1. 模块源仓保存完整真源。
2. 中央仓或宿主支撑包保存发布副本或中央摘要。

如果只靠人记忆，很容易发生三种问题：

- 真源已变化，中央摘要仍停在旧版本。
- 操作者直接修改发布侧，形成第二真源。
- 语义摘要被当成同名副本直接覆盖，丢失中央层结构。

完整的项目真源文档同步 FADE-002 实例使用下面这条链：

```text
事件或 Agent 检测 -> 程序登记运行标识（runId 为其显式形态之一）
  -> Plan Skill（小贾）
  -> 小乔核产品语义 / 小狄核技术与安全门
  -> source_publish_check DCE
  -> Close Skill（小贾）
  -> Close CLI 写入终态
```

它遵循：

```text
FADE = Agent 发现与规划 -> DCE 确定性执行 -> Agent 审核裁决 -> Close CLI 收口终态
```

这里的 DCE 不替 Agent 做语义判断，Agent 也不绕过 CLI 直接执行跨仓发布；Close Skill 之后还必须由 Close CLI 校验并持久化终态。

## 3. 先认清四类文档

### 3.1 项目真源

项目真源是完整事实的长期维护位置。

本教程的真实案例中：

- 真源：`TriCompany/tricompany.md`
- 中央摘要：`TriMetaverse/tricompany.md`

### 3.2 `published-copy`

发布副本与真源内容应完全相同。CLI 可以做字节级复制，因为这个动作不需要语义推理。

### 3.3 `published-summary`

发布摘要不是全文复制。它会根据中央层用途压缩、重组或突出部分事实。

因此：

- CLI 只检查摘要对应的真源版本。
- 真源变化后，小贾必须先准备新候选。
- 小乔核对产品语义，小狄核对 revision、路径和发布安全。
- CLI 验证候选后才允许写入目标。

### 3.4 `audit-record`

审计记录是一次运行、验证或决策的证据，不属于真源副本。

它不进入项目真源同步 manifest，也不能被自动追平成当前文档。

## 4. 生命周期组件怎么配合

| 阶段 | 负责人 | 做什么 | 当前状态 |
| --- | --- | --- | --- |
| Event / 登记 | Runtime | 登记事件、锚定运行标识（`--run-id` 显式 / 时间戳派生） | 已实现（watch 面含 state.json 去重基线） |
| Plan Skill | 小贾 | 确认真源、目标、同步模式、条目范围和验收标准 | 当前人工（实例口径） |
| 产品联审 | 小乔 | 核对范围、成熟度、产品事实和旧口径退役 | 当前人工 |
| 技术联审 | 小狄 | 核对路径、source revision、安全门和发布姿态 | 当前人工 |
| DCE | `source_publish_check` | 读 manifest、算哈希、校验候选、执行写入、输出 JSON | 已实现 |
| Score CLI | `--score` | 检查测试集覆盖（遗漏检测）+ 合并质量分出双门槛 verdict | 已实现 |
| Score Skill | 评分会话 | 按验证方法语义评定每项质量（含治理对齐/内容归属） | 当前人工（试卷在 fade-papers/） |
| Close Skill | 小贾 | 读取证据，形成 APPROVED、FROZEN、ESCALATED 或 RETRY | 当前人工 |
| Close CLI | `--close` | 校验裁决、推进终态并写审计 | 已实现 |

最重要的分工是：

- Skill / Agent 决定“应该同步什么”和“证据支持什么裁决”。
- DCE 决定“声明的动作是否能安全、确定地执行”。
- Close CLI 决定“裁决是否满足机器合同并可落为终态”。

## 5. 先跑 DCE 最小 MVP

第一次学习时，不修改任何文件，只检查当前真实条目。

在 `TriCompany/` 根目录执行：

```powershell
python -m runtime.cognition.source_publish_check `
  --source-root . `
  --workspace-root .. `
  --project-docs `
  --project-doc-ids tricompany-central-summary
```

这条命令默认是 dry-run，不会写文件。

### 5.1 当前成功结果

重点查看顶层 `project_docs`：

```json
{
  "status": "pass",
  "mode": "project-doc-sync",
  "plan_owner": "CEOChiefOfStaff",
  "close_owner": "CEOChiefOfStaff",
  "dry_run": true,
  "summary": {
    "total": 1,
    "changed": 0,
    "planned": 0,
    "in_sync": 1,
    "needs_plan": 0,
    "skipped": 0,
    "errors": 0
  }
}
```

实际哈希和时间会随真源版本变化，不要把示例值写死到脚本里。

### 5.2 为什么这是完整 DCE 检查

虽然没有写文件，但这条命令已经完成 DCE 检查：

1. 读取默认 manifest。
2. 按 ID 找到 `tricompany-central-summary`。
3. 定位 source 与 target。
4. 计算当前真源 SHA-256。
5. 读取目标的 `sourceRevision`。
6. 判断摘要对应当前真源。
7. 输出结构化报告供小贾收口。

这条命令是一次确定性检查切片：没有显式指定运行标识（Runtime 会派生默认 id），也没有做终态收口。完整生命周期由 `--run-id` 登记、Score/Close 链承载（见第 10 节）。

### 5.3 两个 Profile 都复用这条 DCE

- `runtime-owned-durable`：文件 watcher、Git hook、cron 或 CI 触发，Runtime 持有 run 并保证跨会话恢复。
- `agent-owned-interactive`：Agent 在当前会话发现问题并登记 run，Close CLI 之后由 Agent 向用户解释结果。

两个 profile 不复制同步算法，都调用同一个 `source_publish_check` DCE，并统一使用 `Close Skill -> Close CLI -> 终态`。

## 6. Manifest 怎么读

默认 manifest 位于：

- `TriCompany/.github/manifests/project-source-doc-sync-manifest.json`

当前条目结构：

```json
{
  "id": "tricompany-central-summary",
  "enabled": true,
  "source": "TriCompany/tricompany.md",
  "target": "TriMetaverse/tricompany.md",
  "syncMode": "published-summary",
  "planOwner": "CEOChiefOfStaff",
  "reviewers": [
    "ChiefProductOfficer",
    "ChiefTechnologyOfficer"
  ],
  "closeOwner": "CEOChiefOfStaff"
}
```

新人先记住四个字段：

| 字段 | 含义 |
| --- | --- |
| `id` | 命令筛选条目时使用的稳定标识 |
| `source` | 工作区根下的真源路径 |
| `target` | 工作区根下的发布目标路径 |
| `syncMode` | `published-copy` 或 `published-summary` |

路径相对于 `--workspace-root`。本工作区中 `TriCompany` 与 `TriMetaverse` 是同级仓库，所以命令使用 `--workspace-root ..`。

## 7. `published-summary` 为什么需要 `sourceRevision`

中央摘要的头部必须包含：

```markdown
## 文档同步元信息

- sourceOfTruth: TriCompany/tricompany.md
- syncMode: published-summary
- sourceRevision: sha256:<current-source-sha256>
- lastSyncedAt: YYYY-MM-DD
```

`sourceRevision` 回答的是：

> 这份摘要是根据哪个真源版本整理的？

它不是目标文档自己的哈希，也不是 Git commit；当前合同使用真源文件的 SHA-256。

如果真源哈希与 `sourceRevision` 一致，CLI 返回 `in_sync`。如果不一致，CLI 不会猜测摘要该怎么改，而会返回：

```text
status = partial
action = requires_candidate
```

这正是 Agent 与确定性 CLI 的边界。

## 8. 真源变化后的标准流程

下面讲真实维护流程。不要为了练习故意修改正式真源；先理解步骤，实际变更时再执行。

### 8.1 第一步：小贾 dry-run

运行第 5 节命令，读取：

- `project_docs.status`
- `project_docs.items[].action`
- `project_docs.items[].source_hash`
- `project_docs.errors`

如果结果是 `partial + requires_candidate`，进入下一步。

### 8.2 第二步：准备摘要候选

候选可暂存在被忽略的目录：

- `TriCompany/.ade/candidates/tricompany.md`

候选必须：

1. 根据当前真源重新整理。
2. 保持中央摘要定位，而不是复制整份源侧宪章。
3. 把 `sourceRevision` 更新为 dry-run 返回的 `source_hash`。
4. 更新 `lastSyncedAt`。

### 8.3 第三步：小乔与小狄联审

小乔重点检查：

- 产品事实是否准确。
- “已实现 / 待验证 / 规划中”是否混写。
- 是否误删仍有效的中央摘要结论。

小狄重点检查：

- source / target 与 manifest 是否一致。
- `sourceRevision` 是否等于当前真源哈希。
- 是否触碰 live agent、binding profile 或员工五件套等保护目标。
- 是否仍保持“Copilot-host live 不等于 TriMC 正式宿主”的技术边界。

### 8.4 第四步：先验证候选，不写入

```powershell
python -m runtime.cognition.source_publish_check `
  --source-root . `
  --workspace-root .. `
  --project-docs `
  --project-doc-ids tricompany-central-summary `
  --project-doc-candidate "tricompany-central-summary=.ade/candidates/tricompany.md"
```

预期动作是 `planned_update`，目标文件仍不变化。

### 8.5 第五步：显式执行

只有候选联审和 dry-run 都通过，才增加写入参数：

```powershell
python -m runtime.cognition.source_publish_check `
  --source-root . `
  --workspace-root .. `
  --project-docs `
  --project-doc-ids tricompany-central-summary `
  --project-doc-candidate "tricompany-central-summary=.ade/candidates/tricompany.md" `
  --project-docs-execute
```

执行后应看到：

- `dry_run: false`
- `action: updated` 或 `created`
- `changed: 1`
- `errors: 0`

### 8.6 第六步：小贾重跑并人工收口

再次运行不带候选、不带 execute 的 MVP 命令。

只有结果回到：

```text
status = pass
in_sync = 1
errors = 0
```

回到 pass 后，小贾读回结果做语义裁决，再由 Close CLI 校验并写入终态（命令见第 10 节）。

## 9. `published-copy` 有什么不同

`published-copy` 不需要摘要候选。Manifest 示例：

```json
{
  "id": "example-copy",
  "enabled": true,
  "source": "ModuleA/docs/workflow/example.md",
  "target": "Central/docs/workflow/example.md",
  "syncMode": "published-copy"
}
```

CLI 行为：

1. 哈希相同：`in_sync`。
2. 哈希不同且 dry-run：`planned_update`。
3. 目标不存在且 dry-run：`planned_create`。
4. 显式 execute：字节级复制，并返回 `updated` 或 `created`。

不要把语义摘要登记成 `published-copy`，否则显式 execute 会按合同覆盖目标。

## 10. 评分与终态提交

Close Skill 形成语义裁决后，由 Close CLI 校验并落账。裁决词表为四词（与 spec §8.3 终态词表一致）：`APPROVED` / `FROZEN` / `ESCALATED` / `RETRY`。

```powershell
python -m runtime.cognition.source_publish_check --close `
  --run-id <runId> --verdict APPROVED `
  --evidence-ref <证据文件路径> --source-revision <源修订标识>
```

- 校验通过 → 写审计记录 `<source-root>/.ade/<runId>.close-ade.json`，报告 `CLOSED`。
- 校验失败 → 报告 `CLOSE_REJECTED`，非零退出码，绝不静默完成。
- 同一运行标识只能 close 一次（防重复收口）。

DCE 状态与裁决方向的对应关系：

| DCE 状态 | Close Skill 裁决方向 | Close CLI 动作 |
| --- | --- | --- |
| `pass` | 结合业务证据决定 APPROVED 或继续检查 | 校验裁决后写终态 |
| `partial` | RETRY 或 FROZEN | 保持非终态，记录补规划要求 |
| `fail` | FROZEN、ESCALATED 或 RETRY | 校验失败证据并落账 |

常见 item action：

| Action | 含义 |
| --- | --- |
| `in_sync` | 当前目标已对应真源 |
| `planned_create` | dry-run 判断需要创建 |
| `planned_update` | dry-run 判断需要更新 |
| `requires_candidate` | 摘要过期，需要 Agent 候选 |
| `created` / `updated` | 显式 execute 已写入 |
| `error` | 合同、安全门或文件系统错误 |

## 11. CLI 内部是怎么工作的

当前 DCE 核心代码位于：

- `TriCompany/runtime/cognition/source_publish_check.py`

调用链可以先按下面顺序读：

```text
build_parser()
  -> main()
  -> run_project_doc_sync()
     -> _resolve_project_doc_path()
     -> _summary_metadata_errors()
     -> _finalize_project_doc_report()
  -> _serialize_project_doc_sync_report()
```

### 11.1 参数层

`build_parser()` 注册：

- `--project-docs`
- `--project-docs-execute`
- `--project-docs-manifest`
- `--workspace-root`
- `--project-doc-ids`
- `--project-doc-candidate ID=PATH`

### 11.2 业务层

`run_project_doc_sync()` 负责：

1. 读取 manifest。
2. 校验 entry 与筛选 ID。
3. 把相对路径限制在 workspace 内。
4. 拒绝非文档扩展名和保护目标。
5. 根据 sync mode 选择复制或摘要 revision 流程。
6. 记录每个 item 的 action、hash、reason 和 error。

### 11.3 报告层

`_serialize_project_doc_sync_report()` 把运行结果变成 FADE 报告 JSON（envelope v1.0，发布域参考实现）：

- `summary` 提供计数。
- `changes` 提供 before / after 哈希。
- `errors` 提供机器可读失败原因。
- `items` 保留逐条完整证据。

对 `published-summary`，`changes[].after` 是候选文档哈希，不是真源哈希。

## 12. 安全门为什么不能省

CLI 当前会拒绝：

1. 绝对 source / target 路径。
2. 通过 `..` 越出 workspace 的路径。
3. `.github/agents/` 和 `.github/binding-profiles/` 等保护目标。
4. 员工五件套保护目标。
5. 非 `.md`、`.json`、`.yaml`、`.yml` 文档路径。
6. 不存在的 entry ID。
7. 缺失或错误的摘要元信息。
8. 没有同时给出 `--project-docs` 的 execute / candidate 参数。

这些规则必须由 CLI 执行，不能只写在教程里提醒操作者。

## 13. 不碰正式文档的安全实验

你可以直接运行项目文档同步测试，不修改真实文档：

```powershell
python -m unittest `
  runtime.cognition.source_publish_check_validation.ProjectDocumentSyncTests `
  -v
```

它覆盖：

- copy dry-run 与 execute
- summary revision 匹配
- stale summary 等候候选
- 合法候选发布
- workspace 越界拦截
- protected target 拦截
- 未知 ID 拦截
- before / after 哈希审计

再运行 CLI 合同测试：

```powershell
python -m unittest `
  runtime.cognition.source_publish_check_validation.ProjectDocumentSyncCLITests `
  -v
```

最后需要确认旧发布模式没有回归时，运行全量测试：

```powershell
python -m unittest runtime.cognition.source_publish_check_validation -v
```

当前基线为 43+ 项测试通过（项目文档域，2026-08-20 口径；全量运行另含 close / score / event-watch 等生命周期用例）。

## 14. 最容易踩的坑

### 14.1 用旧 `--check --sync` 代替 `--project-docs`

旧模式是 TriCompany source -> support 的兼容目录扫描，不消费项目文档 manifest。跨项目真源同步必须用 `--project-docs`。

### 14.2 把摘要当全文副本

摘要需要语义判断，不能为了省事改成 `published-copy`。

### 14.3 只更新日期，不更新 revision

`lastSyncedAt` 不是版本证明。CLI 以 `sourceRevision` 对照当前真源哈希。

### 14.4 看见 `planned_update` 就以为写入完成

dry-run 只报告计划，不写目标。执行后必须再次 dry-run，直到回到 `in_sync`。

### 14.5 让 CLI 自动写摘要

CLI 不包含 LLM 推理。摘要必须由小贾规划，并经过小乔、小狄联审。

### 14.6 把教程当真源

本教程负责教你怎么做，不定义最终工程合同。发生差异时回到第 16 节列出的工程真源。

## 15. 当前边界与后续扩展

当前已实现：

- 一个 canonical CLI 下的独立项目文档模式（`--project-docs` 面）。
- `published-copy` / `published-summary` 两种同步合同。
- 当前 `tricompany-central-summary` 真实映射。
- dry-run、显式 execute、candidate、哈希审计和安全门。
- 运行标识（显式 `--run-id` / 时间戳派生）与 envelope v1.0 报告合同。
- Score CLI（`--score` 试卷评分、双门槛判定）与 Close CLI（`--close` 终态门）。
- event-watch 触发面（`--event-watch` / `--watch`，state.json 基线）。

当前未实现：

- 自动生成摘要候选。
- 自动替代小乔、小狄的语义与技术联审。
- daemon 自动唤起 event-watch 的常驻自动化链（automation-backlog 立项）。
- 中断恢复的完整持久状态机（event-watch 已有 state.json 基线，业务面增强挂 automation-backlog）。
- `audit-record` 同步。
- 文档侧多宿主发布 adapter。
- 自动提交 Git 或自动创建 PR。

## 16. 真源回链与学习顺序

建议按以下顺序继续阅读：

1. FADE 总规范：[FADE 协议：Agent 确定性执行全生命周期规范](../engineering/fade-protocol-spec.md)（v2.0.0 起替代原 ADE 模式规范，旧路径 ade-pattern-spec.md 为重定向桩）
2. 实例登记册：[FADE 成熟实例登记册](../engineering/fade-registry.md)（FADE-002 段-实现映射表）
3. 项目文档同步实例规范：[项目真源文档同步 ADE](../workflow/project-source-document-sync-ade.md)（FADE-002 项目文档面；文件名为历史命名）
4. 生命周期行业联审（历史）：[ADE 生命周期行业模式联审](../engineering/ade-lifecycle-industry-review.md)
5. 机器清单：[project-source-doc-sync-manifest.json](../../.github/manifests/project-source-doc-sync-manifest.json)
6. DCE 实现：[source_publish_check.py](../../runtime/cognition/source_publish_check.py)
7. 回归测试：[source_publish_check_validation.py](../../runtime/cognition/source_publish_check_validation.py)
8. 当前源侧宪章：[TriCompany 赛博公司宪章](../../tricompany.md)
9. 当前中央摘要：[TriCompany 赛博公司中央摘要](../../../TriMetaverse/tricompany.md)

## 17. 最后记住四句话

1. FADE 是完整生命周期协议本体（FADE-XXX 是实例实现），DCE 只是确定性执行阶段。
2. 两个 profile 共用一套状态机，只改变触发者与生命周期 owner。
3. 全文复制交给 DCE，语义摘要与裁决交给 Skill / Agent。
4. Close Skill 最后判断，Close CLI 最后落账，之后才算终态。
