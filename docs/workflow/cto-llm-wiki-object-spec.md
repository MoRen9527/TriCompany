# CTO LLM Wiki Object Spec

版本：V0.1
日期：2026-07-13
状态：首版草案（以总助 chief-of-staff-llm-wiki-object-spec V0.2 为模板裁剪，待 CTO 确认）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/cto-llm-wiki-object-spec.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- templateDerivedFrom: TriCompany/docs/workflow/chief-of-staff-llm-wiki-object-spec.md (V0.2)
- lastSyncedAt: 2026-07-13

## 1. 文档定位

本文用于定义 CTO（首席技术官）专属 LLM wiki 的最小对象规范。

目标不是先做复杂技术知识图谱，而是先让下面四类对象稳定下来：

- `inbox/` 原始技术资料对象（架构设计、技术选型、性能数据、安全审计）
- `wiki/` 技术知识页面对象
- `audit/` 审计记录对象
- `workbench/` 前台知识工作台快照对象

当前本文作为 workflow 真源写入 `TriCompany/docs/workflow/`；当前阶段真正运行的知识目录、模板和审计样例仍主要位于 `TriCompany-copilot-host-assets/knowledge/employees/chief-technology-officer/`，这不等于相关运行资产已经整体迁回 `TriCompany/`。

这些知识目录视为 `support-object-set`：属于宿主直接消费的 machine-readable 对象集，不纳入 docs published-copy manifest。

## 2. 当前目录边界

- `knowledge/employees/chief-technology-officer/inbox/`：放原始技术资料
- `knowledge/employees/chief-technology-officer/wiki/`：放整理后的技术 wiki 页面
- `knowledge/employees/chief-technology-officer/audit/`：放整理过程与来源追踪
- `knowledge/employees/chief-technology-officer/workbench/`：放前台知识工作台 HTML 和 JSON 快照

## 3. Inbox 原始资料对象

### 3.1 当前允许的文件类型

- `.md`
- `.txt`
- `.json`

### 3.2 当前最小字段

如果原始资料是 markdown，优先使用 YAML frontmatter：

```yaml
---
sourceId: cto-arch-note-2026-07-13-001
title: 示例技术资料
sourceType: architecture-design
topicHints:
  - architecture
  - tri-mc
  - runtime
trustLevel: raw
capturedAt: 2026-07-13T10:00:00+08:00
---
```

字段说明：

- `sourceId`：资料唯一标识，建议前缀 `cto-`
- `title`：资料标题
- `sourceType`：资料类型。CTO 专属类型包括：
  - `architecture-design`：架构设计草案或变更
  - `tech-selection`：技术选型评估记录
  - `performance-data`：性能测试数据与分析
  - `security-audit`：安全审计发现与修复记录
  - `code-review`：重要代码审查结论
  - `tech-decision`：技术决策记录（ADR 风格）
  - `incident-postmortem`：故障复盘
  - `meeting-note`：技术相关会议纪要
  - `scratch-note`：零散技术思考
  - `fact-sheet`：技术事实汇总
  - `json-record`：结构化技术数据（性能指标、错误率等）
- `topicHints`：主题提示词，用于 page-specs 中 sourceFilter 匹配
- `trustLevel`：`raw`、`curated`、`approved` 三档
- `capturedAt`：资料进入 inbox 的时间

### 3.3 没有 frontmatter 的处理规则

- 如果资料没有 frontmatter，当前允许直接投放。
- 后续整理时，由编译链补默认元数据。
- 默认 `trustLevel = raw`。

### 3.4 当前命名建议

- 建议格式：`YYYY-MM-DD-cto-topic-short-name.ext`
- 示例：`2026-07-13-cto-architecture-tri-mc-runtime-review.md`

## 4. Wiki 页面对象

### 4.1 页面目标

wiki 页面是"可检索、可回看、可继续更新"的 CTO 技术知识整理结果，不等于已签发的正式架构文档或 ADR。

### 4.2 当前最小 frontmatter

```yaml
---
pageId: cto-tech-decisions
title: 技术决策记录
topicTags:
  - architecture
  - decision
  - tech-stack
pageStatus: working
updatedAt: 2026-07-13T10:30:00+08:00
approvalStatus: draft
sourceRefs:
  - cto-arch-note-2026-07-13-001
---
```

字段说明：

- `pageId`：页面唯一标识，建议前缀 `cto-`
- `title`：页面标题
- `topicTags`：主题标签
- `pageStatus`：`working`、`reviewing`、`stable`
- `updatedAt`：最后更新时间
- `approvalStatus`：`draft`、`pending`、`approved`、`rejected`
- `sourceRefs`：来源资料 id 列表

### 4.3 当前最小正文结构

CTO 的 wiki 页面正文结构在技术事实与技术决策上做了区分，以适应技术岗位的判断需求：

```md
## 摘要

## 当前技术事实

## 当前技术决策

## 待确认问题

## 来源
```

五块说明：

- **摘要**：一页读完即可了解页面核心内容
- **当前技术事实**：从 inbox 中提取的客观技术事实（性能数据、安全发现、架构约束、依赖状态等），不做判断
- **当前技术决策**：CTO 基于技术事实做出的判断与决策（架构方案选择、技术栈取舍、重构优先级等），必须标注决策日期、决策依据与替代方案（ADR 风格）
- **待确认问题**：当前资料不足以形成决策的开放技术问题，需进一步调研或实验验证
- **来源**：回链到 inbox 中的具体 sourceId

### 4.4 当前写入边界

- `wiki/` 页面当前可以作为 CTO 专属 LLM wiki 资产。
- `wiki/` 页面当前不能自动替代 `TriCompany/docs/engineering/` 下的正式 DESIGN.md、metacognition-architecture.md 或 ADR。
- CTO wiki 中的技术决策如需落地为正式架构文档，仍需走工程文档更新流程。
- 性能数据类 wiki 页不得包含生产环境敏感信息（密钥、IP、内部拓扑）；此类数据应留在 inbox 层并标记 `trustLevel: raw`，编译时做脱敏处理。

### 4.5 当前 page promotion 规则

与总助保持一致的最小升格规则：

- `working -> reviewing`
  - 页面包含五个必需区块：`摘要`、`当前技术事实`、`当前技术决策`、`待确认问题`、`来源`
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

## 5. Audit 记录对象

### 5.1 当前建议格式

使用 `.json`。

### 5.2 当前最小字段

```json
{
  "runId": "wiki-refresh-2026-07-13-001",
  "triggerMode": "manual",
  "employeeId": "chief-technology-officer",
  "startedAt": "2026-07-13T10:30:00+08:00",
  "inputSources": [
    "cto-arch-note-2026-07-13-001"
  ],
  "outputPages": [
    "cto-tech-decisions"
  ],
  "status": "completed",
  "notes": "initial cto wiki compile"
}
```

字段说明：

- `runId`：本轮整理任务 id
- `triggerMode`：`manual` 或后续的 `scheduled`
- `employeeId`：`chief-technology-officer`（泛化后的必填字段）
- `startedAt`：开始时间
- `inputSources`：输入资料列表
- `outputPages`：输出页面列表
- `status`：`completed`、`partial`、`failed`
- `notes`：补充说明

### 5.3 审计记录类型

- `wiki-refresh-*`：单次 wiki 刷新记录
- `wiki-promotion-*`：页面升格记录（fromStatus、toStatus、ruleId、evidence）
- `wiki-approval-*`：审批决定记录（reviewer、reviewedAt、备注）
- `wiki-recall-checkpoint-*`：recall 模式检查点
- `schedule-run-*`：定时任务执行记录
- `wiki-compile-sanitize-*`：敏感信息脱敏检查记录（CTO 专属，记录 compile 阶段的脱敏动作）

## 6. 当前最小编译规则

- 原始资料先进入 `inbox/`，不要求立即升级为正式架构文档。
- 编译出的 `wiki/` 页面必须带来源回链。
- 同一技术主题可以合并进同一页面，但不能抹掉来源边界。
- 编译过程必须生成 `audit/` 记录。
- 当前阶段先支持"半自动整理 + 人工复核"，不默认自动生效到正式 ENGINEERING.md 或 ADR。
- refresh 更新页面内容时必须保留既有 `pageStatus`，不能把已升格页面自动打回 `working`。
- refresh 更新页面内容时必须保留既有 `approvalStatus` 和人工审批元数据。
- **编译时脱敏**：CTO wiki 页编译时，须检查并移除以下敏感信息：
  - API 密钥、Token、密码
  - 内部 IP 地址、主机名、网络拓扑
  - 生产环境数据库连接串
  - 未公开的漏洞详情（在修复并披露前）
- **技术决策类 wiki 页**（`当前技术决策` 块非空）的 stable promotion 建议经架构评审或 CPO 交叉审批。

## 7. 当前不做的事

- 不要求一开始就支持所有文件格式。
- 不要求一开始就做 embedding 检索。
- 不要求一开始就自动修改 `TriCompany/docs/engineering/` 正式文档。
- 不要求一开始就接真实外部邮件发送。
- 不要求 CTO wiki 自动生成 ADR——wiki 是知识积累，ADR 是正式交付物，二者不可混淆。
- 不要求编译阶段自动执行安全扫描（脱敏检查由编译链做，但深度安全扫描仍由独立安全工具负责）。

## 8. 直接相关文件

- `../workflow/chief-of-staff-llm-wiki-object-spec.md`（模板来源）
- `../workflow/employee-llm-wiki-guide.md`（员工通用操作指南）
- `../../engineering/cognition-runtime-module-plan.md`
- `TriCompany-copilot-host-assets/knowledge/employees/chief-technology-officer/inbox/`
- `TriCompany-copilot-host-assets/knowledge/employees/chief-technology-officer/wiki/`
- `TriCompany-copilot-host-assets/knowledge/employees/chief-technology-officer/audit/`
- `TriCompany/docs/engineering/DESIGN.md`（正式架构设计，wiki 不可替代）
- `TriCompany/docs/engineering/metacognition-architecture.md`（元认知架构，wiki 不可替代）
- `TriMC/docs/engineering/DESIGN.md`（TriMC 模块技术真源，与 CTO wiki 互补）
