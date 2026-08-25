# 项目真源文档同步 ADE

版本：V1.1
日期：2026-08-07
状态：DCE 可执行；ADE 生命周期 profile 已裁决，runtime / skill / close-cli 待实现

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/project-source-document-sync-ade.md
- syncMode: source-only
- lastSyncedAt: 2026-08-07

## 1. 文档定位

本文定义项目真源文档跨仓发布与追平的 ADE。完整协议由事件登记、Plan Skill、DCE、Close Skill 与 Close CLI 组成；当前已实现 `source_publish_check` DCE 和人工 Agent-owned 流程，其他 lifecycle 组件仍待落地。

它复用既有源侧发布 CLI，不另建第二套同步工具。既有 TriCompany source -> support/live 发布模式继续保留；项目真源文档使用独立的 manifest 驱动域，避免目录扫描绕过 `published-copy`、`published-summary` 与 `audit-record` 分类。

## 2. ADE 角色

| ADE 层 | Owner | 职责 | 当前状态 |
| --- | --- | --- | --- |
| Event / run | Runtime | 登记事件、去重、生成 runId、持有状态与恢复 | 待实现 |
| Plan Skill | CEOChiefOfStaff（小贾） | 判定真源、目标、同步模式、范围和验收标准；为语义摘要准备候选文档 | 当前人工，Skill 待实现 |
| 产品联审 | ChiefProductOfficer（小乔） | 核对产品事实、范围、成熟度和旧口径退役是否正确 | 当前人工 |
| 技术联审 | ChiefTechnologyOfficer（小狄） | 核对路径、同步模式、source revision、安全门和发布姿态 | 当前人工 |
| DCE | `source_publish_check --project-docs` | 读取 manifest、校验路径和 revision、执行复制或候选发布、输出结构化报告 | 已实现 |
| Close Skill | CEOChiefOfStaff（小贾） | 读取 DCE / Verify 证据，形成 APPROVE / FREEZE / ESCALATE / RETRY 裁决 | 当前人工，Skill 待实现 |
| Close CLI | Runtime CLI | 校验裁决与证据、推进终态、持久化审计 | 待实现 |

标准链路：

```text
事件 / Agent 检测 -> Plan Skill -> 小乔/小狄联审
-> source_publish_check DCE -> Verify CLI（可选）
-> Close Skill -> Close CLI -> 终态
```

## 3. 为什么与既有工具合并

### 3.1 复用项

- dry-run 默认安全门
- 显式 execute 写入
- SHA-256 before/after
- JSON 自检报告
- manifest 白名单
- 单元测试与 CLI 回归入口

### 3.2 必须分域的原因

既有 `--check --sync` 面向 TriCompany source -> support 的兼容目录扫描；项目真源同步需要显式 source/target 映射，并且必须区分：

- `published-copy`：CLI 可做字节级确定性复制。
- `published-summary`：CLI 不得自行总结；source revision 变化后必须等待小贾提供候选文档。
- `audit-record`：不是同步目标，不进入项目真源同步 manifest。

因此结论是：**一个 canonical DCE CLI，三个独立执行模式**。保留旧模式兼容，新增 `--project-docs`，不把项目文档逻辑塞回目录扫描。

## 4. Manifest 合同

默认清单：`TriCompany/.github/manifests/project-source-doc-sync-manifest.json`。

每个 entry 至少包含：

```json
{
  "id": "tricompany-central-summary",
  "enabled": true,
  "source": "TriCompany/tricompany.md",
  "target": "TriMetaverse/tricompany.md",
  "syncMode": "published-summary"
}
```

路径必须相对 `--workspace-root`，不允许绝对 target，也不允许通过 `..` 越出工作区。source / target 只接受 `.md`、`.json`、`.yaml`、`.yml` 文档扩展名；live agent、binding profile 与员工五件套等保护目标即使被误写进 manifest，CLI 也会拒绝。

## 5. 两种同步模式

### 5.1 published-copy

- source 与 target 相同哈希：`in_sync`。
- 不同哈希：dry-run 返回 `planned_create` / `planned_update`。
- 显式 execute 后由 CLI 字节级复制并返回 `created` / `updated`。

### 5.2 published-summary

CLI 只用目标头部的以下字段判断是否对应当前真源：

```markdown
## 文档同步元信息

- sourceOfTruth: TriCompany/tricompany.md
- syncMode: published-summary
- sourceRevision: sha256:<current-source-sha256>
- lastSyncedAt: YYYY-MM-DD
```

若 `sourceRevision` 已是当前 source hash，则为 `in_sync`。若 revision 过期且未提供候选，返回 `partial + requires_candidate`，不会写目标。

候选文档必须由小贾在 plan 阶段准备，并经小乔/小狄联审。CLI 只校验候选元信息、哈希和目标路径，然后执行发布。

## 6. 标准命令

在 `TriCompany/` 根目录执行。

### 6.1 全量 dry-run

```powershell
python -m runtime.cognition.source_publish_check `
  --source-root . `
  --workspace-root .. `
  --project-docs
```

### 6.2 指定条目 dry-run

```powershell
python -m runtime.cognition.source_publish_check `
  --source-root . `
  --workspace-root .. `
  --project-docs `
  --project-doc-ids tricompany-central-summary
```

### 6.3 发布摘要候选

先从 dry-run 报告读取当前 `source_hash`，写入候选文档的 `sourceRevision`，再执行：

```powershell
python -m runtime.cognition.source_publish_check `
  --source-root . `
  --workspace-root .. `
  --project-docs `
  --project-doc-ids tricompany-central-summary `
  --project-doc-candidate "tricompany-central-summary=<candidate-path>" `
  --project-docs-execute
```

`--project-docs-execute`、`--project-doc-candidate` 都必须与 `--project-docs` 同时使用。

## 7. DCE JSON 报告合同

顶层输出增加 `project_docs`：

```json
{
  "status": "pass|partial|fail",
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
  },
  "changes": [],
  "errors": [],
  "items": []
}
```

- `pass`：DCE 证据通过，可提交给 Close Skill 裁决，但尚不是 ADE 终态。
- `partial`：交回 Plan Skill 补候选或补规划后重跑。
- `fail`：交给 Close Skill 形成 FREEZE / ESCALATE / RETRY 建议；CLI 返回非零退出码。

`changes[].before` 与 `changes[].after` 分别记录目标写入前和计划 / 执行后的 SHA-256；`published-summary` 的 `after` 是候选文档哈希，不是真源哈希。

## 8. 首个登记实例

当前首个条目为：

- source：`TriCompany/tricompany.md`
- target：`TriMetaverse/tricompany.md`
- mode：`published-summary`
- 当前 profile：`agent-owned-interactive-manual`
- plan / close owner：CEOChiefOfStaff（小贾）
- reviewers：ChiefProductOfficer（小乔）、ChiefTechnologyOfficer（小狄）
- lifecycle：DCE 已实现；Plan / Close Skill、Close CLI 与持久 run 待实现

后续新增项目文档时，只新增 manifest entry，不复制 CLI。

## 9. 验证入口

```powershell
python -m unittest runtime.cognition.source_publish_check_validation.ProjectDocumentSyncTests -v
python -m unittest runtime.cognition.source_publish_check_validation.ProjectDocumentSyncCLITests -v
```

## 10. 两个生命周期 Profile

- `runtime-owned-durable`：文件、Git、cron、CI 等程序事件触发，Runtime 持有 run 到终态。
- `agent-owned-interactive`：Agent 在当前会话检测并登记事件，完成后向用户解释结果。

两个 profile 共用同一状态机、DCE、证据和 `Close Skill -> Close CLI` 终态顺序。行业依据与裁决见 `../engineering/ade-lifecycle-industry-review.md`。
