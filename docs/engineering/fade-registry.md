# FADE 成熟实例登记册

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/fade-registry.md
- syncMode: source-only
- lastSyncedAt: 2026-08-28（v2.0 同步：上位规范迁移+FADE-006 条目；六实例反向工程注记）

版本：v2.0（2026-08-28；2026-08-18 立册，CEO 定名 FADE 并指定首批三实例收编）

定义：见 [fade-protocol-spec.md §一](fade-protocol-spec.md)——完整生命周期十段全部落地且实跑过、评分通过的 **FADE 完整实例**。本册只登记完整档；FADE 兼容档/纯确定性执行脚本档见 spec §六案例表，升格后移入本册。

登记/升降格规则：新实例入册需附逐段工件证据；缺段实例先列"补齐项"，两次周检未补即降回 spec §六。

v1.1.0 注记（2026-08-18）：spec 新增 §2.6 收尾对标（试卷—答卷—评分），入册/升格须附试卷与评分通过记录；既有四实例的试卷与评分已列入各自补齐项，限期补齐。

v1.2 注记（2026-08-27，六实例反向工程）：FADE-001..004 登记于四模块架构成立前，**属前标准期实例**——按 CEO 裁定不追溯降格，但须对照新规补课（spec §2.7/§2.8）；反向提炼全文见 `TriMetaverse/docs/execution/fade-instances-retrospective.md`。FADE-006 为首个四模块全栈期标准实例。**补课范围裁定（联审 CPO-F16）**：节点收口报告仅适用多节点树实例——001/002/003 单段脚本/CLI 实例豁免，004 HTTP 链多节点按段适用；确定性拾取门按 spec §2.8 细则 9 的 profile 限定分别适用。

v2.0 同步注记（2026-08-28）：上位规范重构迁移 ade-pattern-spec.md → **fade-protocol-spec.md v2.0.0**（ADE 概念退役，FADE 升为协议本体，FADE-XXX 为实现；"ADE-A/B 域"历史代号→发布域/员工域）；本册各条目内 runId/jobs.json/requestId 等为实例实现绑定（合法），协议层术语见 spec「运行标识」。
v1.2.1 注记（2026-08-27，spec §2.8 同步）：本册十段工件表自本版起 schema 化为「**段-实现映射表**」——协议只约束每段不变量（spec §2.8），实例条目声明载体实现。判例：runId 字段非必须，登记段四不变量（唯一/去重/关联/恢复锚）必须；显式标识优于分散组合（定位成本）。

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
- 复评（2026-08-21，FADE-LEFTOVER-20260821-001 项 3① 随真实发布窗）：**PASS 93/100**——run-id-carrier 7→10（`--run-id` 显式化在本发布窗实跑 5 次核销：b1-copilot/-claude 两宿主 execute + recheck×2 + converged，envelope run_id 均显式值）；报告/质量/评分见 fade-papers/FADE-002-{report,quality,score}-rereview-2026-08-21.json；遗留仅剩事件自动触发增强（挂 automation-backlog，CTO 裁决 2026-08-21）
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
- 评分记录（2026-08-20）：首次 **PASS 81/100** → 官方审计证据就位后复评 **PASS 88/100**（audit-record 6→9、terminal-sample 9→10 等 4 项升级，无降项），试卷见 [fade-papers/FADE-004-paper.json](fade-papers/FADE-004-paper.json)，复评证据见 fade-papers/FADE-004-evidence/
- 范围（2026-08-19 整合定调）：扩容为 **ADE-B 员工域**——并入员工对象发布段（host object 生成 / binding profile / 委托 publish-agents / 治理回填），上岗链 + 发布链同一生命周期域；spec §六 案例表已并入本条目

## FADE-006 计划任务 execution→周平面自动拾取（execution-plane autopilot）

| 段 | 工件 |
| --- | --- |
| 事件触发 | 本地 M 面定计划拆树后 `git push sg-bare`；post-receive hook 秒级派 tick（trigger=hook）+ trimc cron `:18/:48` 慢通道兜底（trigger=cron） |
| 登记 | 树文件 `trees/<id>/tree-op.json`（face/domainRouting/sourceMaterials 卷封字段）+ session-registry instances/ticks（rc·pid·trigger 全留痕）+ fade-hook.log |
| Qualify/Plan Skill | 编排层三重门确定性评估（status=active + server-executable + pending 无时间门 + face 路由）；M 面 TriMLC+CEO 定计划拆树，材料预封卷 |
| DCE | CC 编排会话（spawn cwd 按树 repo 直落+白名单全家桶+BRIEF 裸命令铁律）按节点 fresh 派工：先写后报、原子即提交、卷封验卷/对卷 |
| Close Skill | 会话收口裁决：漂移走 §9.3 二选一裁决；blocked 分层取证八股（原始拒绝文本定层），修复后自愈复工不复用旧进度 |
| Close CLI | 树顶层 status=done commit + push 回流 + 台账 rc 终值 + 战役快照 Merkle root（首演 40ee6f8c…） |
| 终态 | 实跑样本：2026-08-26/27 P0 审计修复战役——八实例九项 P0 全修复（agent-core 4/TriRMC 2/TriLC 三通道/TriModel 流式 fallback），含 AC-1..4 四验收实证与 AC-4 受控实验 PASS |

- 规范：`TriMetaverse/docs/execution/fade-006-execution-autopick-spec.md` + 管线设计 `fade-pipeline-design.md` v1.1（§八运行语义/§九卷封制）
- 树：W35 平面 p0fix1..4 / rmc-audit-cmp-001 / trimodel-audit-001 / fade-rehearsal-001 / fadeslow-verify-001
- 基建锚：sg-server（bare post-receive hook / trimc cron / orchestrate_tick c0ad6b8 系）；模型档 glm-5.3-flash
- owner：小贾（计划/卷封/镜像归账）+ TriMMC 编排会话（执行）+ 本地监控会话（fade-watch.ps1 承载，监督 owner=小贾）
- 补齐项：blocked 边沿告警（v1.2 待办）；节点收口报告与卷封预封为立法后件，**下实例起强制并复评**（本实例 3/8 与 5/8 如实低计在卷）；**联审复审触发**（CPO-F6）：补评若暴露结构性缺陷，§2.7/§2.8 回联审复审；**Close CLI 载体接线**（CTO-F7）：tick 台账回收器程序化派生 rc 已立法为映射表声明载体，工程窗接线核验
- 评分记录（2026-08-27 首评·回溯建卷）：**PASS 80/100 卡线**，必选项 6/6——卷封完整性 5/8 与节点收口报告 3/8 如实低计（均立法于运行期后），"标准但不完美"的诚实读数；卷宗 [fade-papers/FADE-006-paper.json](fade-papers/FADE-006-paper.json) / [score](fade-papers/FADE-006-score-2026-08-27.json)（coverage/quality 同目录）；root 口径敏感坑（九树口径）已记卷 notes
- 备注：编号跳 005 沿用 08-21 勘误口径（005 已并入 FADE-004 员工域）

## 候补（升格观察区）

- IPD 全流程（spec §6.3）：六组件齐但阶段输出未统一 ADE JSON 自检格式，gate 判断仍 agent 语义推断——补齐后可入册。

（员工对象发布条目已于 2026-08-19 整合定调迁入 FADE-004 员工域扩容。）
