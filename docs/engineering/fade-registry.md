# FADE 成熟实例登记册

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/fade-registry.md
- syncMode: source-only
- lastSyncedAt: 2026-08-18

版本：v1.0（2026-08-18 立册；CEO 定名 FADE = Full-cycle ADE 并指定首批三实例收编）

定义：见 [ade-pattern-spec.md §1.1](ade-pattern-spec.md)——完整生命周期十段全部落地且实跑过、评分通过的 ADE 实例。本册只登记 FADE 档；ADE 兼容/纯 DCE 档见 spec §六案例表，升格后移入本册。

登记/升降格规则：新实例入册需附逐段工件证据；缺段实例先列"补齐项"，两次周检未补即降回 spec §六。

v1.1.0 注记（2026-08-18）：spec 新增 §2.6 收尾对标（试卷—答卷—评分），入册/升格须附试卷与评分通过记录；既有四实例的试卷与评分已列入各自补齐项，限期补齐。

---

## FADE-001 周工作平面迁移（weekly plane shift）

| 段 | 工件 |
| --- | --- |
| 事件触发 | TriMC cron `0 23 * * 0`（周日 23:00 Asia/Singapore），jobs.json 持久 |
| 登记 | jobId + per-run 日志 `/var/lib/trimc/cron/logs/<jobId>__<ISO>.log`（去重=调度引擎防重入） |
| Qualify/Plan Skill | 五段链脚本内置（迁移段序固定：OP index→unresolved→trees→carry-over→通知，无需逐次语义规划） |
| DCE | `python3.8 五段链 --sync`（runAs fleet，写 operating-records）+ git commit（身份 TriMC Scheduler）+ push `/srv/git/TriMetaverse.git HEAD:dev` |
| Close Skill | 迁移完成后邮件通知语义摘要（notify.json 0600 + QQ SMTP，2026-08 演练二期实证真实投递） |
| Close CLI | `.shift-ade.json` 审计文件 + git commit 哈希为确定性收口载体 |
| 终态 | 实跑样本：W33→W34 迁移（2026-08-17 00:45 由服务域 TriMC 独立完成，E 阶段验证） |

- 规范：`TriMC/docs/ops/trimc-cron-plane-shift-runbook.md`
- 树：`TriMetaverse/.../2026-W33/trees/prod-grade-1-trimc-weekly-cron`
- owner：TriMC 侧小全（实现）/ 小柯（独立验证）/ 小贾（收口）
- 补齐项：无（十段齐）
- 评分记录（2026-08-20 首次）：**PASS 90/100**，必选项 6/6，试卷见 [fade-papers/FADE-001-paper.json](fade-papers/FADE-001-paper.json)；遗留：服务器侧 jobs.json / per-run 日志回流后复评

## FADE-002 公司文档管理（tricompany.md 监督的真源-发布同步）

| 段 | 工件 |
| --- | --- |
| 事件触发 | 源侧发布事件（source publish）；CEO/员工发起发布指令 |
| 登记 | manifest 驱动（`project-source-doc-sync-manifest.json` + `published-copy`/`published-summary` 分域清单） |
| Qualify/Plan Skill | 小贾规划候选 + 小乔核产品语义 + 小狄核 revision 与安全门（联审裁决，见 ade-lifecycle-industry-review.md）；监督契约 = `TriMetaverse/tricompany.md`（真源纪律：sourceOfTruth/syncMode/元信息头 §3.4 规范） |
| DCE | `source_publish_check --check --sync --scope` / `--project-docs [--project-docs-execute]`（`TriCompany/runtime/cognition/source_publish_check.py`；默认 dry-run，execute 才写入） |
| Close Skill | 联审语义裁决（approve/freeze 记录于 manifest 状态） |
| Close CLI | 同 CLI 的校验输出 + manifest 收口状态 + `source_publish_check_validation.py` |
| 终态 | 实跑样本：source→support 发布同步多轮（小赛执行）；project-docs 域已裁决两 profile |

- 规范：`TriCompany/docs/workflow/project-source-document-sync-ade.md` + spec §6.1
- owner：小贾（plan/close）+ 小赛（执行）+ 小乔/小狄（联审）
- 补齐项：文件/Git 事件自动触发、runId 字段显式化（现为 manifest 状态隐式承载）——不影响 FADE 档判定（十段均有真实工件），列为增强项
- 评分记录（2026-08-20 首次）：**PASS 90/100**，必选项 6/6，试卷见 [fade-papers/FADE-002-paper.json](fade-papers/FADE-002-paper.json)；遗留：runId 显式化与事件自动触发增强后复评
- 范围（2026-08-19 整合定调）：扩容为 **ADE-A 发布域**——覆盖 源侧→发布侧同步、项目真源文档同步、Agent live entry 发布三候选域；CLI `source_publish_check` 三 scope（--check / --project-docs / --publish-agents），`--host` 参数扩展宿主侧发布；spec §六 案例表已并入本条目

## FADE-003 共学周记记录（journal recording）

| 段 | 工件 |
| --- | --- |
| 事件触发 | prompt 手动（`.github/prompts/项目级 AI 共学周记.prompt.md`，Copilot-host 可直调）；cron 自动 ⏳ 待 resident 能力 |
| 登记 | `node journal-cli.mjs begin --title "…"` → runId + 去重提示（run log 落 begin 记录） |
| Qualify/Plan Skill | agent 语义四问（可复述/有产出/可对外/有共学价值）+ 草拟 entry.json 七字段；格式三查（prompt 固定格式 + README + 最近周） |
| DCE | `journal-cli.mjs qualify --entry --run`（机械资格：结构+脱敏扫描）→ `append --entry --run`（固定五件格式渲染 2.n + lastSyncedAt + 同题去重） |
| Close Skill | agent 读回追加结果，语义裁决 `approved\|escalated` + note |
| Close CLI | `journal-cli.mjs close --run --verdict --note`：校验裁决合法值 + run 链完整（begin+append 同 runId）+ 收口五查 → APPROVED/ESCALATED |
| 终态 | 实跑样本：W34 周记真实 close 全 PASS（run log 完整审计链） |

- 规范：`TriMetaverse/docs/workflow/operating-records/项目级 AI 共学周记/ade-journal-recording-spec.md`
- 执行体：`TriMetaverse/scripts/journal/journal-cli.mjs`（审计：`journal-run-log.jsonl`）
- 纪律：TriCompany 工程纪律 D-06
- owner：秘书处（小贾代管）
- 补齐项：cron 自动触发（依赖 TriMC resident 链路，见 automation-backlog.md）
- 评分记录（2026-08-20 首次）：**PASS 80/100 卡线**，必选项 6/6，试卷见 [fade-papers/FADE-003-paper.json](fade-papers/FADE-003-paper.json)；遗留：run 链完整审计补证（本机 run log 现 2 行，缺 begin/append）后复评
- 描述修正（2026-08-20 评分核实）："run log 完整审计链"表述与实际不符（本机 journal-run-log.jsonl 现 2 行：qualify ESCALATED + close CLOSED，缺 begin/append）——修正为"close 全 PASS 实测，完整 run 链待补证"

---

## FADE-004 候选岗位发布（员工上岗）

| 段 | 工件 |
| --- | --- |
| 事件触发 | 开业装配 selections / TriCade settings→agents 勾选 /（未来）CHO 增员提案 |
| 登记 | POST /staffing/onboard → requestId+runId，dataDir/staffing/requests.json（pending-cho）；去重 409 |
| Qualify/Plan Skill | 链态门（ready 后才可增员）+ JD 存在性 + role-catalog 单一真源映射 |
| DCE | 批准后 CompanyInitState.employees 原子写入 + init:staffing-* 事件 |
| Close Skill | CHO 语义裁决（面板代理 panel-cho 审计留痕；未来 CHO agent 会话） |
| Close CLI | POST /staffing/decide：CHO 门 403 → 名册写入 + 审计 json（CHO-staffing-<requestId>.json）→ roster 回读 |
| 终态 | E2E 8/8（2026-08-18 隔离环境：开业打钩/勾选/待审/重复409/CHO门403/批准/驳回回候选/审计落盘） |

- 规范：`TriMetaverse/docs/execution/candidate-staffing-fade.md`
- 执行体：TriLC src/company/staffing.ts + 3 端点（roster/onboard/decide）；呈现面：TriPilot settings→agents 勾选
- 组织依据：clone-dispatch-protocol.md（岗位=JD；上岗=进名册；分身 spawn=另一层 HC）
- owner：CHO（审批）+ 小贾（收口）
- 补齐项：CHO agent 会话自动审批（当前面板代理）；分身 spawn 前置校验「JD 已上岗」
- 评分记录（2026-08-20 首次）：**PASS 81/100 贴线**，必选项 6/6，试卷见 [fade-papers/FADE-004-paper.json](fade-papers/FADE-004-paper.json)；遗留：官方 CHO-staffing-*.json 审计回流后复评
- 范围（2026-08-19 整合定调）：扩容为 **ADE-B 员工域**——并入员工对象发布段（host object 生成 / binding profile / 委托 publish-agents / 治理回填），上岗链 + 发布链同一生命周期域；spec §六 案例表已并入本条目

## 候补（升格观察区）

- IPD 全流程（spec §6.2）：六组件齐但阶段输出未统一 ADE JSON 自检格式，gate 判断仍 agent 语义推断——补齐后可入册。

（员工对象发布条目已于 2026-08-19 整合定调迁入 FADE-004 员工域扩容。）
