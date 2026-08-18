# FADE 试卷模板（Assessment Paper Template）

版本：v1.0.0
日期：2026-08-18
状态：当前工程模板

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/fade-assessment-paper-template.md
- syncMode: source-only
- lastSyncedAt: 2026-08-18

规范依据：[ade-pattern-spec.md](ade-pattern-spec.md) §2.6（收尾对标：试卷—答卷—评分）与 §1.1（FADE 必要条件）

## 一、试卷结构

试卷 = **固定部分**（本模板 + 实例专属规范文档）+ **实时部分**（Plan Skill 阶段由 Agent 按实例声明）。

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

## 二、及格线（双门槛）

1. **必选项全部通过**（§1.1 每项都能指到真实工件）
2. **总分达标**：得分 ≥ 实例声明阈值（默认 80 / 100）

两者同时满足才算 PASS；不达线进入 `RETRY`（补齐证据重跑）或 `ESCALATED`（升级裁决），不得写入终态。

## 三、Score CLI 输出合同

```json
{
  "status": "pass|fail|partial",
  "items": [
    { "id": "...", "label": "...", "weight": 10, "score": 10, "max": 10, "evidence_ref": "...", "required": true }
  ],
  "total": { "score": 92, "max": 100, "threshold": 80 },
  "required_all_passed": true,
  "verdict": "PASS|FAIL",
  "scored_at": "ISO8601"
}
```

- `verdict=PASS` ⇔ `required_all_passed=true` 且 `total.score >= total.threshold`
- 评分 JSON 作为 Close Skill 裁决的客观证据（spec §2.6），与 CLI 自检报告同级，不得伪造或覆盖

## 四、评分时机与收口

- 位置：Verify CLI（可选）之后、Close Skill 之前
- 收口：Close CLI 核分——不达线回 `RETRY` / `ESCALATED`，不得写终态
- 留存：得分与评分 JSON 随 run 审计存档，作为该次执行效果的量化记录
