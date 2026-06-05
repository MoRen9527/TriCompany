# Chief Of Staff LLM Wiki Object Spec

版本：V0.2
日期：2026-04-20
状态：首版可执行对象规范，已补 page promotion 与 schedule staging 审计口径

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/chief-of-staff-llm-wiki-object-spec.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/chief-of-staff-llm-wiki-object-spec.md
- supportSyncRule: 仅在成批发布或当前宿主重新显式依赖时追平 support 副本
- lastSyncedAt: 2026-04-28

## 1. 文档定位

本文用于定义总助专属 LLM wiki 的最小对象规范。

目标不是先做复杂知识图谱，而是先让下面四类对象稳定下来：

- `inbox/` 原始资料对象
- `wiki/` 页面对象
- `audit/` 审计记录对象
- `workbench/` 前台知识工作台快照对象

当前本文已回写到 `TriCompany/docs/workflow/` 作为 workflow 真源；但当前阶段真正运行的知识目录、模板和审计样例仍主要位于 `TriCompany-copilot-host-assets/knowledge/` 与对应 support root 下，这不等于相关运行资产已经整体迁回 `TriCompany/`。

当前这些知识目录与当前宿主直接消费的 `TriCompany-copilot-host-assets/docs/execution/hermes-copilot-host/phase-1/schedules/*.json` 一起，统一视为 `support-object-set`：它们属于宿主直接消费的 machine-readable 对象目录 / 对象集，不纳入 docs published-copy manifest，也不按 active / on-demand published-copy 的追平纪律处理。

这里需要明确拆开“机制实现”和“对象载荷”：LLM wiki 的对象规范、整理机制、审计规则和运行代码真源仍在 `TriCompany/docs/workflow/`、`TriCompany/docs/engineering/` 与 `TriCompany/runtime/cognition/`；support root 下当前活路径是 `knowledge/employees/ceo-chief-of-staff/**`，它承接当前 Copilot-host 直接消费或生成的总助工作对象集。

只有在同时出现真实跨宿主分发、真实统一枚举需求和真实独立版本发布需求时，才讨论为这组对象单独建立 host object manifest；在它们仍是单宿主 staging 对象或 host-local working set 时，默认不拆独立 manifest。

## 2. 当前目录边界

- `knowledge/employees/ceo-chief-of-staff/inbox/`：放原始资料
- `knowledge/employees/ceo-chief-of-staff/wiki/`：放整理后的 wiki 页面
- `knowledge/employees/ceo-chief-of-staff/audit/`：放整理过程与来源追踪
- `knowledge/employees/ceo-chief-of-staff/workbench/`：放前台知识工作台 HTML 和 JSON 快照

## 3. Inbox 原始资料对象

### 3.1 当前允许的文件类型

当前首批允许：

- `.md`
- `.txt`
- `.json`

### 3.2 当前最小字段

如果原始资料是 markdown，优先使用 YAML frontmatter：

```yaml
---
sourceId: chief-of-staff-note-2026-04-20-001
title: 示例零散资料
sourceType: meeting-note
topicHints:
  - chief-of-staff
  - llm-wiki
trustLevel: raw
capturedAt: 2026-04-20T10:00:00+08:00
---
```

字段说明：

- `sourceId`：资料唯一标识
- `title`：资料标题
- `sourceType`：资料类型，例如 `meeting-note`、`scratch-note`、`fact-sheet`、`json-record`
- `topicHints`：主题提示词
- `trustLevel`：`raw`、`curated`、`approved` 三档
- `capturedAt`：资料进入 inbox 的时间

### 3.3 没有 frontmatter 的处理规则

- 如果资料没有 frontmatter，当前允许直接投放。
- 后续整理时，由编译链补默认元数据。
- 默认 `trustLevel = raw`。

### 3.4 当前命名建议

- 建议格式：`YYYY-MM-DD-topic-short-name.ext`
- 示例：`2026-04-20-chief-of-staff-memory-note.md`

## 4. Wiki 页面对象

### 4.1 页面目标

wiki 页面是“可检索、可回看、可继续更新”的整理结果，不等于 CEO 已签发的正式制度文档。

### 4.2 当前最小 frontmatter

```yaml
---
pageId: chief-of-staff-memory-system
title: 总助记忆系统
topicTags:
  - chief-of-staff
  - memory
pageStatus: working
updatedAt: 2026-04-20T10:30:00+08:00
approvalStatus: draft
sourceRefs:
  - chief-of-staff-note-2026-04-20-001
---
```

字段说明：

- `pageId`：页面唯一标识
- `title`：页面标题
- `topicTags`：主题标签
- `pageStatus`：`working`、`reviewing`、`stable`
- `updatedAt`：最后更新时间
- `approvalStatus`：`draft`、`pending`、`approved`、`rejected`
- `sourceRefs`：来源资料 id 列表

当前 `pageStatus` 与 `approvalStatus` 的语义如下：

- `working`：页面已生成，但还没有足够的 scheduled refresh 证据；当前也会进入 all-pages recall，但可信级别低于 stable。
- `reviewing`：页面满足最小结构与来源要求，且至少已有 1 次 completed 的 scheduled refresh 审计；当前可进入 all-pages recall，并进入人工审批队列。
- `stable`：页面满足最小结构与来源要求、至少已有 2 次 completed 的 scheduled refresh 审计，且人工审批已通过；当前既进入 all-pages recall，也可继续作为高可信 stable recall 来源。
- `approvalStatus = draft`：页面仍在工作态，尚未进入人工审批。
- `approvalStatus = pending`：页面已进入 reviewing，待人工审批。
- `approvalStatus = approved`：人工审批已通过，可支撑 `reviewing -> stable`。
- `approvalStatus = rejected`：人工审批已驳回，页面不得自动升格为 stable。

### 4.3 当前最小正文结构

```md
## 摘要

## 当前整理事实

## 当前判断

## 待确认问题

## 来源
```

### 4.4 当前写入边界

- `wiki/` 页面当前可以作为 LLM wiki 资产。
- `wiki/` 页面当前不能自动替代 `.github` 主档、operating records 或正式 registry。

### 4.5 当前 page promotion 规则

当前已落地的最小升格规则为：

- `working -> reviewing`
  - 页面包含五个必需区块：`摘要`、`当前整理事实`、`当前判断`、`待确认问题`、`来源`
  - `sourceRefs` 至少 3 条
  - 至少已有 1 条 `triggerMode = scheduled` 且 `status = completed` 的 `wiki-refresh-*` 审计记录
  - 升格后默认把 `approvalStatus` 置为 `pending`

- `reviewing -> stable`
  - 继续满足上述结构与来源要求
  - 至少已有 2 条 `triggerMode = scheduled` 且 `status = completed` 的 `wiki-refresh-*` 审计记录
  - `approvalStatus` 必须已经是 `approved`
  - `approvalStatus = rejected` 时应阻塞 stable promotion

- `stable`
  - 不再继续自动升格；后续只允许继续刷新内容，不允许因为 refresh 自动回退为 `working`
  - 仍保留更高可信级别，但不独占 recall 可见性

## 5. Audit 记录对象

### 5.1 当前建议格式

当前首版建议使用 `.json`。

### 5.2 当前最小字段

```json
{
  "runId": "wiki-refresh-2026-04-20-001",
  "triggerMode": "manual",
  "startedAt": "2026-04-20T10:30:00+08:00",
  "inputSources": [
    "chief-of-staff-note-2026-04-20-001"
  ],
  "outputPages": [
    "chief-of-staff-memory-system"
  ],
  "status": "completed",
  "notes": "initial wiki compile"
}
```

字段说明：

- `runId`：本轮整理任务 id
- `triggerMode`：`manual` 或后续的 `scheduled`
- `startedAt`：开始时间
- `inputSources`：输入资料列表
- `outputPages`：输出页面列表
- `status`：`completed`、`partial`、`failed`
- `notes`：补充说明

### 5.3 当前新增审计记录类型

除 `wiki-refresh-*` 之外，当前还新增：

- `wiki-promotion-*`
  - 记录 `fromStatus`、`toStatus`、`ruleId`、`evidence` 和 `reason`

- `wiki-approval-*`
  - 记录审批决定、reviewer、reviewedAt 和审批备注

- `wiki-recall-checkpoint-*`
  - 记录 recall 模式、检查时间和 recall 结果摘录

- `schedule-run-*`
  - 记录一次 schedule / cron staging run 对应的 `scheduleId`、`targetRef`、`status`、`artifactPaths`

- `reminder-delivery-*`、`email-delivery-*`、`checkpoint-*`
  - 记录 task bus 生成的提醒、邮件草稿和检查点结果

## 6. 当前最小编译规则

- 原始资料先进入 `inbox/`，不要求立即升级为项目真源。
- 编译出的 `wiki/` 页面必须带来源回链。
- 同一主题可以合并进同一页面，但不能抹掉来源边界。
- 编译过程必须生成 `audit/` 记录。
- 当前阶段先支持“半自动整理 + 人工复核”，不默认自动生效到正式主档。
- refresh 更新页面内容时必须保留既有 `pageStatus`，不能把已升格页面自动打回 `working`。
- refresh 更新页面内容时必须保留既有 `approvalStatus` 和人工审批元数据。

## 7. 当前不做的事

- 不要求一开始就支持所有文件格式。
- 不要求一开始就做 embedding 检索。
- 不要求一开始就自动修改 `.github` 主档。
- 不要求一开始就接真实外部邮件发送；当前 email 任务仅需先生成可审计草稿。

## 8. 直接相关文件

- `../engineering/chief-of-staff-llm-wiki-priority-plan.md`
- `../engineering/cognition-runtime-module-plan.md`
- `TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/inbox/source-template.md`
- `TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/wiki/page-template.md`
- `TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/audit/record-template.json`
