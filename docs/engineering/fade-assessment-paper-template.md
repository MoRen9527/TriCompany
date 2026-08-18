# FADE 试卷模板（Assessment Paper Template）

版本：v1.0.1
日期：2026-08-18
状态：当前工程模板

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/fade-assessment-paper-template.md
- syncMode: source-only
- lastSyncedAt: 2026-08-18

规范依据：[ade-pattern-spec.md](ade-pattern-spec.md) §2.6（收尾对标：试卷—答卷—评分）与 §1.1（FADE 必要条件）

## 一、试卷结构

试卷 = **固定部分**（本模板 + 实例专属规范文档 + 测试集）+ **实时部分**（Plan Skill 阶段由 Agent 按实例声明）。

### 1.1 必选项（FADE 固定考卷，全部通过才能过线）

| 检查项 | 工件证据 | 说明 |
| --- | --- | --- |
| 触发器配置 | 触发配置 / 事件源 | cron、文件 / Git watcher、hook、webhook 或 Agent 检测 |
| runId 载体 | 登记记录 | 事件去重后生成，run 唯一标识 |
| Skill 承载文档 | Plan / Close skill 文档 | 方法与判定标准可指认 |
| CLI 命令与报告 | DCE / Verify / Score / Close 执行记录 | 结构化 JSON 报告（spec §2.2 合同） |
| 审计记录 | sync-log 或等效审计条目 | 含 before/after 与时间戳（spec §2.3） |
| 终态样本 | 终态记录 | APPROVED / FROZEN / ESCALATED / RETRY 之一 |

### 1.2 评分项（实时部分，实例声明）

Plan Skill 阶段按实例声明，每项含：

- `id`：检查项标识
- `label`：检查项名称
- `weight`：权重（总分 100 分摊）
- `standard`：通过标准（客观、可判定的描述）
- `evidence_ref`：证据引用（本次执行的工件路径 / runId 字段）
- `required`：是否必选项（必选项同时纳入 §1.1 全过判定）

### 1.3 测试集（固定部分，提前备好）

测试集列出 CLI 必做工作与验证方法，是评分"是否遗漏 + 每项处理质量"的依据——类比大模型测评：先有评估测试集，事后才好评分。每个 FADE 实例按本实例 CLI 职责填写测试集，每项含：

- `must_do`：CLI 必做工作（如"写入默认 dry-run""变更前后对照落账""终态裁决校验"）
- `verify_method`：验证方法（客观可判定：命令输出断言、文件比对、状态回读、审计条目检查等，不接受主观描述）
- `quality_standard`：质量判定标准（合格 / 优秀的分档描述）

示例：

| must_do | verify_method | quality_standard |
| --- | --- | --- |
| 写入操作默认 dry-run | 不带写参数执行，断言无副作用写入 | 无写入 = 合格 |
| 结构化自检报告 | 解析 CLI 输出 JSON，断言 spec §2.2 字段齐全 | 字段齐全 = 合格；含 before/after 对照 = 优秀 |
| 终态收口 | 检查 Close CLI 审计记录与终态样本 | 记录齐全且终态合法 = 合格 |

## 二、及格线（双门槛）

1. **必选项全部通过**（§1.1 每项都能指到真实工件）
2. **总分达标**：得分 ≥ 实例声明阈值（默认 80 / 100）

两者同时满足才算 PASS；不达线进入 `RETRY`（补齐证据重跑）或 `ESCALATED`（升级裁决），不得写入终态。

## 三、Score CLI 输出合同

```json
{
  "status": "pass|fail|partial",
  "items": [
    { "id": "...", "label": "...", "weight": 10, "score": 10, "max": 10, "evidence_ref": "...", "required": true, "omission": false }
  ],
  "total": { "score": 92, "max": 100, "threshold": 80 },
  "required_all_passed": true,
  "verdict": "PASS|FAIL",
  "scored_at": "ISO8601"
}
```

- `verdict=PASS` ⇔ `required_all_passed=true` 且 `total.score >= total.threshold`
- `omission=true` 表示该项必做工作遗漏（测试集未覆盖）：该项按 0 分计，且若 `required=true` 计入全过判定
- 评分两维度：是否遗漏（`omission` 覆盖检查）+ 每项处理质量（`score` 对照验证方法评级）
- 评分 JSON 作为 Close Skill 裁决的客观证据（spec §2.6），与 CLI 自检报告同级，不得伪造或覆盖

## 四、评分时机与收口

- 位置：Verify CLI（可选）之后、Close Skill 之前
- 收口：Close CLI 核分——不达线回 `RETRY` / `ESCALATED`，不得写终态
- 留存：得分与评分 JSON 随 run 审计存档，作为该次执行效果的量化记录
