# FADE 成熟实例登记册

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/fade-registry.md
- syncMode: source-only
- lastSyncedAt: 2026-08-28（v2.1：FADE-006 升格标注+映射表首行填制；v2.0：上位规范迁移+FADE-006 条目；六实例反向工程注记）

版本：v2.1（2026-08-28：FADE-006 升格完整实例标准档标注＋段-实现映射表首行填制，LG-008 三方联审；2026-08-18 立册，CEO 定名 FADE 并指定首批三实例收编）

定义：见 [fade-protocol-spec.md §一](fade-protocol-spec.md)——完整生命周期十段全部落地且实跑过、评分通过的 **FADE 完整实例**。本册只登记完整档；FADE 兼容档/纯确定性执行脚本档见 spec §六案例表，升格后移入本册。

登记/升降格规则：新实例入册需附逐段工件证据；缺段实例先列"补齐项"，两次周检未补即降回 spec §六。

v1.1.0 注记（2026-08-18）：spec 新增 §2.6 收尾对标（试卷—答卷—评分），入册/升格须附试卷与评分通过记录；既有四实例的试卷与评分已列入各自补齐项，限期补齐。

v1.2 注记（2026-08-27，六实例反向工程）：FADE-001..004 登记于四模块架构成立前，**属前标准期实例**——按 CEO 裁定不追溯降格，但须对照新规补课（spec §2.7/§2.8）；反向提炼全文见 `TriMetaverse/docs/execution/fade-instances-retrospective.md`。FADE-006 为首个四模块全栈期标准实例。**补课范围裁定（联审 CPO-F16）**：节点收口报告仅适用多节点树实例——001/002/003 单段脚本/CLI 实例豁免，004 HTTP 链多节点按段适用；确定性拾取门按 spec §2.8 细则 9 的 profile 限定分别适用。

v1.2.1 注记（2026-08-27，spec §2.8 同步）：本册十段工件表自本版起 schema 化为「**段-实现映射表**」——协议只约束每段不变量（spec §2.8），实例条目声明载体实现。判例：runId 字段非必须，登记段四不变量（唯一/去重/关联/恢复锚）必须；显式标识优于分散组合（定位成本）。
v2.0 同步注记（2026-08-28）：上位规范重构迁移 ade-pattern-spec.md → **fade-protocol-spec.md v2.0.0**（ADE 概念退役，FADE 升为协议本体，FADE-XXX 为实现；"ADE-A/B 域"历史代号→发布域/员工域）；本册各条目内 runId/jobs.json/requestId 等为实例实现绑定（合法），协议层术语见 spec「运行标识」。

---

## FADE-001 周工作平面维护（weekly plane maintenance）——v2.0.2 扩维：迁移→维护

> **范围扩维（2026-08-28，CEO 提案）**：本实例从"周平面迁移"扩为"**周平面维护**"——迁移是维护的一个项；新增**每日工作进度维护**（仓库级粗粒度恢复兜底，`operating-records/<周>/daily-progress.md`，随 git 三端，机器全灭时的最后恢复防线）。扩维细节见每日进度文件头部声明。

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
- 维护项（扩维后）：
  - ①**周平面迁移**（周日 23:00，原主体，十段齐已评分）
  - ②**每日工作进度维护**（2026-08-28 新增，十段设计如下——runtime-owned durable profile）：

| 段 | 实现 | 节点 |
| --- | --- | --- |
| 事件触发 | **主=事件驱动**（董事长助理任务完成增量即写——销账/交付/裁决后随手 append+push）；**辅=定时巡检兜底**（TriMC cron 每 10 分钟确定性脚本，检 daily-progress 落后即补写；单写者原则：巡检只补漏不重写，防双写冲突） | TriMC daemon（sg 守候进程）+ 助理 |
| 登记 | 运行标识=日期锚（daily-progress.md `## YYYY-MM-DD` 标题）；去重=同日标题已存在则 append 不新建；持久=git 三端 | 仓库即 runtime |
| Qualify | 机械门：当日确有运行变化（自上次进度条目后新 commits>0 或 ledger-mirror mtime 变化）；无变化=skip 不产空节 | 确定性脚本 |
| Plan | 静态计划已固化（三节结构：已完成/现役挂账/恢复指针），无逐次规划——同迁移项模式 | 固化于脚本 |
| DCE | 确定性收集（ledger-mirror+当日 commits→粗粒度三节）→追加写入→commit+push 三端 | 脚本（自动化期）/助理手填（探索期） |
| Verify | 写入后回读：当日节存在且非空、锚点格式合规 | 脚本自检 |
| Score CLI | （功能期）确定性查当日节三节齐/锚点 12 位/挂账与 ledger-mirror 一致性 | 待实现 |
| Score Skill | （功能期）语义查粗粒度是否失真（漏战役/挂账过期） | 待实现 |
| Close Skill | 董事会/助理确认当日节完整 | 人/会话 |
| Close CLI | push 三端成功即终态（任何一端可达=每日进度不灭） | git |
| 终态 | 当日节在三端仓库可读——机器全灭时的日级重建锚 | — |

  两阶段路径：**探索期（现在）**=助理事件驱动随手写（任务完成增量即 append）+巡检兜底待接；**自动化期**=TriMC cron 10 分钟巡检脚本上线（确定性收集 git log/registry→落后即补写），Score CLI 缺口随脚本一并补齐。最坏丢失窗口：23h（旧日总结节奏）→**10 分钟**（本设计）。
  重建价值锚：每日进度兜底的验收场景=「sg+本机+中枢三点全灭后，仅凭 GitHub 上的 daily-progress.md 可重建至最后 10 分钟」。
- 补齐项：无（十段齐）；每日进度维护自动化（cron 日更）列增强项
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
- 补齐项：文件/Git 事件自动触发（automation-backlog，CTO 2026-08-21 裁决）；~~runId 字段显式化~~ ✅ 已于 2026-08-21 复评核销（7→10）
- 评分记录（2026-08-20 首次）：**PASS 90/100**，必选项 6/6，试卷见 [fade-papers/FADE-002-paper.json](fade-papers/FADE-002-paper.json)；遗留：runId 显式化与事件自动触发增强后复评
- 复评（2026-08-21，FADE-LEFTOVER-20260821-001 项 3① 随真实发布窗）：**PASS 93/100**——run-id-carrier 7→10（`--run-id` 显式化在本发布窗实跑 5 次核销：b1-copilot/-claude 两宿主 execute + recheck×2 + converged，envelope run_id 均显式值）；报告/质量/评分见 fade-papers/FADE-002-{report,quality,score}-rereview-2026-08-21.json；遗留仅剩事件自动触发增强（挂 automation-backlog，CTO 裁决 2026-08-21）
- 范围（2026-08-19 整合定调）：扩容为 **ADE-A 发布域**——覆盖 源侧→发布侧同步、项目真源文档同步、Agent live entry 发布三候选域；CLI `source_publish_check` 三 scope（--check / --project-docs / --publish-agents），`--host` 参数扩展宿主侧发布；spec §六 案例表已并入本条目

## FADE-003 共学周记记录（journal recording）〔**FADE 兼容档**——v2.0.2 逐段对照降档标注，CEO 2026-08-28 判定追认〕

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
- 档位判定依据（v2.0.2 逐段对照，CEO 判定"非标准 FADE 流程"成立）：**Score CLI/Score Skill 双段缺失**（质量评价缺位=W34 首写违规 D-06 的制度根源）、Verify 缺失、触发手动化（Agent-owned profile 最弱形态）、终态两态分辨率不足、Qualify 自判无独立裁判——对照分析见 retrospective §三 与本条目
- 补齐项（升完整实例路线）：① `journal-cli score --run`（Score CLI：对照周记 spec 检查表确定性查覆盖——五件结构/元信息头/去重/同题/run 链）② Score Skill 语义评定 2.n 内容质量（四维度+evidence_ref）③ RETRY 路径（评分不达线→append 修订重跑，同步解决词表两态）④ cron 自动触发（resident 链路，automation-backlog）⑤ 裁决词表升四态+大小写统一（v2.0.2 联审 R-C4 合并跟踪，期限下次周检）
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

## FADE-006 执行面自动拾取（execution-plane autopilot：计划任务说明书→周平面自动拾取）

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
- 评分记录（2026-08-27 首评·回溯建卷·**冻结留档**）：**PASS 80/100 卡线**，必选项 6/6——卷封完整性 5/8 与节点收口报告 3/8 如实低计（均立法于运行期后），"标准但不完美"的诚实读数；卷宗 [fade-papers/FADE-006-paper.json](fade-papers/FADE-006-paper.json) / [score](fade-papers/FADE-006-score-2026-08-27.json)（coverage/quality 同目录）；root 口径敏感坑（九树口径）已记卷 notes
- 增评（2026-08-28，LG-004 联审 C 口径双轨·对象 trilc-lineage-merge run）：**PASS 91/100**——卷封完整性 8/8（§9.3(a) 真实触发+verify=0 双分支闭环）+ 节点收口报告 7/8（node-report-check 首跑 FAIL→机读核心增补→PASS 2/2 弧线如实）；其余项沿用原战役证据+必选 6/6 无回归；补齐项**关闭**、细则 8 复审触发**解除**；卷宗 [fade-papers/FADE-006-paper-rereview-2026-08-28.json](fade-papers/FADE-006-paper-rereview-2026-08-28.json) / [score](fade-papers/FADE-006-score-rereview-2026-08-28.json)
- 备注：编号跳 005 沿用 08-21 勘误口径（005 已并入 FADE-004 员工域）

**段-实现映射表（§2.8 细则 2 首行填制，2026-08-28 LG-008 升格标注；格式律：证据引用一律为锚非散文）**

| 段名 | 载体类型与形态 | 不变量满足证据引用（锚） |
| --- | --- | --- |
| 事件触发 | 归因锚载体（前置输入）：任务说明书程序化投送；触发机制载体：post-receive hook 秒级派 tick＋trimc cron :18/:48 兜底 | 计划文档封卷 hash（tree-op.json sourceMaterials 字段）；fade-hook.log tick 行（trigger 字段可归因） |
| 登记 | registry (treeId,tick,pid) 三元组＋tree-op.json（face/domainRouting/sourceMaterials）＋session-registry instances/ticks | 唯一性=instances 按 treeId 唯一（锚：`jq '[.[]|select(.treeId=="trilc-lineage-merge")]|length'` 计数=1）；去重性=tick 指纹边沿＋活动锁＋1800s 冷却（锚：tick-fingerprint.txt＋registry 无重复 spawn 记录可机器复算）；关联性=ticks 按 treeId 聚合十段工件（锚：p0fix1 树 ticks 链）；恢复锚=tree-op.json＋ticks 定位现场（锚：p0fix1 blocked 复工实证） |
| Qualify | 机械准入门=三重门（status=active＋server-executable＋pending 无时间门）＋卷封验卷 verify=0（双门并列：两门齐备方开工，缺一即停） | 编排会话三重门判定留痕（fade-hook.log/编排台账）；seal-materials --verify 退出码 0（trilc-lineage-merge tree-op.json，§9.3(a) 重封后复验） |
| Plan | M 面 TriMLC+CEO 定计划拆树＋sourceMaterials 预封＋语义作业方案卷封字段；试卷冻结件自 spec v2.0.3 起生效（新 run 适用，既有 run 回溯卷按历史口径标注） | p0-fix-and-trilc-merge-plan.md §二（甄别 27/1＋门禁基线）；tree-op.json sourceMaterials 双 hash（668d30a3…/3e412542…） |
| DCE | CC 编排会话 spawn（agent-carried 降级合同，细则 4：先写后报＋原子即提交＋§2.7 节点收口报告）；段内逐节点门禁=node-report-check＋tsc＋npm test（括注：属 DCE 段内门禁，非 Verify 段） | 27 重放提交（trilc-lineage-merge dev 线）；node-TM-1.md/node-TM-2.md |
| Verify CLI | **可选段未启用**（诚实空缺——逐节点门禁已前置 DCE 段内，不凑段） | —（空缺如实） |
| Score CLI | 增评卷确定性覆盖检查（增评卷（TM run，现行法）） | fade-papers/FADE-006-paper-rereview-2026-08-28.json coverage 部分 |
| Score Skill | 两项重计语义评定（卷封 5/8→8/8＋节点报告 3/8→7/8，evidence_ref 逐项） | fade-papers/FADE-006-score-rereview-2026-08-28.json |
| Close Skill | 收口裁决：§9.3 漂移二选一＋blocked 分层取证八股 | trilc-lineage-merge tree-op.json notes（豁免＋重封留痕，非静默放过） |
| Close CLI | 顶层 done commit＋push 回流＋台账 rc 终值＋战役 Merkle root；增补载体=harvest-rc 程序化派生 rc——**三态声明：matcher 载体=已接线**（p0fix4 MATCH 实证＋部署 9215886）；**例行化宽口径=核验中**（解除条件=LG-005 首个真实战役实证） | c6f969de 双远端；战役 root 40ee6f8c…（八树快照）；reports/run-root.json（run root=c841f337…，补算五要合规） |

**升格标注（2026-08-28，LG-008 三方联审定案＋编排层核验＋CEO 授权落地）**：三处诚实边界清偿齐备（①映射表首行填制＋补锚＋去重归因修正 ②试卷 Plan 时点冻结立法 spec v2.0.3 ③单 run root 补算 c841f337… 五要合规）＋增评 91 PASS 在册——**FADE-006 升格完整实例标准档**。配套工具族：TriMetaverse scripts/fade/_fadehash.py（单一 canonical 双 hash，CPO 单一 hash 纪律×CTO 分文件结构调和案）＋run-root.py（首测即补算）＋seal-materials.py 改造（回归 5/5 行为等价）。升格不溯及既往：既有 run 合规由现行法下新增 run 评分背书（spec 细则 10 修正 2 口径）。

## 纸面法清单（spec §2.8 细则 10 修正 1 落点·周检核对）

> 每条必载：解除条件+责任席位+入账日期；两次周检未接线即冻结退回提案区。

| 入账日期 | 纸面法条目 | 解除条件 | 责任席位 |
| --- | --- | --- | --- |
| 2026-08-28 | （空清单开局——细则 10 判例×3 均已接线实测） | — | CEOCS |

## 候补（升格观察区）

- IPD 全流程（spec §6.3）：六组件齐但阶段输出未统一 ADE JSON 自检格式，gate 判断仍 agent 语义推断——补齐后可入册。

（员工对象发布条目已于 2026-08-19 整合定调迁入 FADE-004 员工域扩容。）
