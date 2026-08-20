# FADE 四实例试卷与首次评分

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/fade-papers/README.md
- syncMode: source-only
- lastSyncedAt: 2026-08-20

依据：[fade-assessment-paper-template.md](../fade-assessment-paper-template.md) v1.0.4（§1.1 必选项六项、§1.3 测试集、§二 双门槛、§三 评分合同）与 [fade-registry.md](../fade-registry.md) 四实例逐段工件表。任务：#24 四实例试卷 + 首次评分（CEO 2026-08-20 启动；CFO 上岗挂起不碰）。

## 一、文件清单

| 文件 | 内容 |
| --- | --- |
| `FADE-001-paper.json` | FADE-001 周工作平面迁移试卷 |
| `FADE-001-report.json` | FADE-001 评分证据（`.shift-ade.json` 五步链转写 + 证据索引） |
| `FADE-001-quality.json` | FADE-001 质量分（Close Skill 语义评定，注入用） |
| `FADE-001-score-2026-08-20.json` | FADE-001 最终评分合同（含质量分） |
| `FADE-002-paper.json` | FADE-002 公司文档管理试卷 |
| `FADE-002-report.json` | FADE-002 评分证据（2026-08-20 现跑 `--project-docs` dry-run envelope 原样 + 证据索引） |
| `FADE-002-quality.json` | FADE-002 质量分 |
| `FADE-002-score-2026-08-20.json` | FADE-002 最终评分合同 |
| `FADE-003-paper.json` | FADE-003 共学周记记录试卷 |
| `FADE-003-report.json` | FADE-003 评分证据（`journal-run-log.jsonl` 两行转写 + W34 周记证据索引） |
| `FADE-003-quality.json` | FADE-003 质量分 |
| `FADE-003-score-2026-08-20.json` | FADE-003 最终评分合同 |
| `FADE-004-paper.json` | FADE-004 候选岗位发布试卷 |
| `FADE-004-report.json` | FADE-004 评分证据（E2E 8/8 记录转写 + staffing.ts / 审计样本证据索引） |
| `FADE-004-quality.json` | FADE-004 质量分 |
| `FADE-004-score-2026-08-20.json` | FADE-004 最终评分合同 |

另存 `FADE-00X-score-2026-08-20.coverage.json`（Score CLI 纯覆盖检查，未注入质量分——覆盖与质量两源分离留痕）。

## 二、试卷结构

四份试卷同构：六必选项（模板 §1.1：触发器配置 / runId 载体 / Skill 承载文档 / CLI 命令与报告 / 审计记录 / 终态样本）按各实例 registry 逐段工件表命名，外加实例特有评分项（权重分摊 Σmax=100，阈值 80 默认）。每项含 `verify_method`（客观可判定），质量分档语义见模板 §1.3（合格=无写入/字段齐全/记录齐全且终态合法；优秀=含 before/after 对照等）。

### 实例特有项与验证方法映射（registry 工件表 → 测试集）

| 实例 | 特有评分项 | 验证方法映射 |
| --- | --- | --- |
| FADE-001 | carry-over-8w | `.shift-ade.json` escalation_8w 列表存在且含 CARRY-* 明细（8w 阈值上报） |
| | notify-close | runbook §1 通知实证记录（notify.json 0600 + QQ SMTP，2026-08 演练二期实证投递） |
| | dedup-guard | runbook §7 runningAtMs 守卫 + 单 systemd 实例（调度防重入） |
| | git-push-close | git log 检出 TriMC Scheduler 身份迁移 commit（b125cf56，00:45 SGT 与 .shift-ade check_time 一致） |
| FADE-002 | dry-run-default | manifest defaultMode=dry-run + 现跑 envelope mode=dry-run 双证据 |
| | metadata-gate | 现跑 envelope requires_candidate（published-summary 的 sourceRevision/lastSyncedAt 门禁实证） |
| | path-safety | source_publish_check.py `_is_protected_target` 硬检查（保护域 ∅） |
| | review-gate | manifest planOwner/closeOwner/reviewers + 联审裁决文档在案 |
| FADE-003 | format-three-check | W34 周记条目结构对照 prompt 固定格式（现象/具体表现/解决方案/问题影响 + 当前经验双条） |
| | sensitive-scan | run log qualify ESCALATED hits=["疑似 API key（sk-…）"] 真实命中记录 |
| | run-chain | run log 中 begin→qualify→append 同 runId 链在案性（本机 log 仅 2 行，缺 begin/append——如实扣分） |
| | five-check-close | C1 路径当周目录 / C2 五件结构 / C3 元信息+记录人 / C4 git 已提交 / C5 回报 CEO |
| FADE-004 | cho-gate | staffing.ts CHO_ALLOWED 白名单 + E2E ④ 非 CHO 审批人 403 实证 |
| | dedup-409 | staffing.ts already_active/already_pending 双分支 + E2E ③b 重复 409 实证 |
| | chain-gate | staffing.ts chain_state_gate + E2E 未开业 409 记录 |
| | roster-readback | staffing.ts getStaffingRoster counts/status + E2E ③⑥ 回读实证 |

## 三、证据充分性说明（2026-08-20 首次评分）

按"真实证据、不编造"原则，各实例本机可得性如实标注：

- **FADE-001**：`.shift-ade.json`（W33→W34 五步链完整，check_time 2026-08-16T16:45Z）+ git commit b125cf56（TriMC Scheduler）+ runbook 均在案。**服务器侧不可得**：`/var/lib/trimc/cron/jobs.json`、per-run 日志 `/var/lib/trimc/cron/logs/<jobId>__<ISO>.log`、邮件投递日志——对应项以 runbook 文档级证据计分并扣分。
- **FADE-002**：评分证据为 2026-08-20 现跑 `--project-docs` dry-run 真实 envelope（partial：1 in_sync + 1 requires_candidate）+ manifest + 规范/联审文档。**无新增执行**（dry-run 不写）；文件/Git 事件自动触发与 runId 显式化仍为 registry 增强项，如实计入。
- **FADE-003**：`journal-run-log.jsonl` 本机仅 2 行（qualify ESCALATED 0f1a4035 + close CLOSED fa623b3d），**缺 begin/append 记录**——registry 所称"完整审计链"未获本机证据支持，run-chain 项按证据不足扣分（3/10），如实上报，不改 registry。
- **FADE-004**：官方审计形态 `dataDir/staffing/CHO-staffing-<requestId>.json` 与 `requests.json` 在隔离 E2E dataDir，**本机不可得**；本机可得对齐形态审计 `CHO-clone-staffing-20260817-001.json`（commit ea05817e）+ staffing.ts 源码 + E2E 8/8 记录（candidate-staffing-fade.md §六）。audit-record 项按近邻证据计 6/10，如实标注。

## 四、运行方式

```powershell
# 覆盖检查（确定性）
python -m runtime.cognition.source_publish_check --score --score-paper docs/engineering/fade-papers/FADE-001-paper.json --score-report docs/engineering/fade-papers/FADE-001-report.json
# 注入质量分（Close Skill 语义）重跑得最终 verdict
python -m runtime.cognition.source_publish_check --score --score-paper docs/engineering/fade-papers/FADE-001-paper.json --score-report docs/engineering/fade-papers/FADE-001-report.json --score-quality-scores docs/engineering/fade-papers/FADE-001-quality.json
```

（在 TriCompany 根目录执行；`--score` 与业务 scope 互斥，评分输出即为 §三 评分合同。）

## 五、评分结果摘要（2026-08-20）

| 实例 | verdict | 总分 | 阈值 | 必选项通过 | 主要扣分项 |
| --- | --- | --- | --- | --- | --- |
| FADE-001 | PASS | 90 | 80 | 6/6 | runId 载体（per-run 日志服务器侧）；notify/dedup 文档级证据 |
| FADE-002 | PASS | 90 | 80 | 6/6 | runId 隐式承载（增强项）；终态 profile 如实 pending |
| FADE-003 | PASS | 80 | 80 | 6/6 | run-chain 证据不足 3/10（begin/append 缺）；三查/五查部分项无独立审计 |
| FADE-004 | PASS | 81 | 80 | 6/6 | audit-record 官方形态不可得 6/10；触发器运行时数据隔离环境 |

四实例均 PASS 但 FADE-003/004 贴近阈值，遗留项见各 score 文件 `items[].evidence_ref` 与质量分——补服务器侧/隔离环境证据后重跑可拉开分差。
