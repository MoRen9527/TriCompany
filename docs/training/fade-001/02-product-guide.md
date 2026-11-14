<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-001/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-001 产品版——十阶段迁移链工作流与使用旅程

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-001/02-product-guide.md
- syncMode: source-only
- lastSyncedAt: 卷面时点锚=git commit 时戳（零手打·D-47 增补款正形）

> **重写批注记（v2.0.0·2026-11-14·CEO 19:48:54 fade-001 重写令）**：①本篇全部重写为十阶段链工作流产品版（内容基准=[05 稿](05-trigger-chain-draft.md) 十阶段总览下沉）；②原 §2.2/§2.3/旅程 B/旅程 D 等每日进度内容（FADE-012）**已拆出**至 [../fade-012/](../fade-012/README.md) 草稿卷——本篇纯迁移域零混装。修正留痕：v1.x（09-05 基线·双域叙事）→ v1.9（11-12 拆分注记）→ v2.0.0（11-14 重写令）。

读者：要**与 FADE-001 共处**的人——要做周计划的协作者、运维值班，以及评审"这套迁移体系值不值得依赖"的人。不需要读代码。
前置：已读 [小白版](01-beginner-guide.md)（或已懂 周平面/十段链/两层窗 概念）。
事实基线：2026-11-14 现役终态（十阶段形 payload 在役·首拍=周日 23:50 硬锚·score 引擎实弹态·γ 过闸形态生效）。

---

## 一、模块导读四要素

| 要素 | 内容 |
| --- | --- |
| **定位** | FADE-001"周平面迁移"实例（登记册在册），公司级"最低恢复防线"的迁移腿——周日自动翻页；现役执行形态=**十阶段链**（触发+段 1-10·每段一问一卷面 fail-closed） |
| **成熟度** | 迁移域完整档（首评 PASS 90/100·2026-08-20·冻结不重评）；十阶段链=**预演形验证毕·生产形真值候周日 23:50 首拍**（两层窗分开判读）；遗留挂账=齿条①服务器证据回流复评 |
| **真源路径** | 登记册 `TriCompany/docs/engineering/fade-registry.md` FADE-001 条；十阶段执行体=`TriCompany/runtime/cognition/` 十件 CLI（preflight/qualify/plan_scope/dce_steps/verify/score_cli+score_engine/score_rubric/close_skill/close_cli/notify_done）；迁移器本体=`runtime/cognition/weekly_plane_shift`；runbook=`TriMMC/docs/ops/trimc-cron-plane-shift-runbook.md`；判据锚卷/判读表 v2/γ 验收卷（现役卷锚见 [README 真源指针](README.md)） |
| **常见误区** | ①把预演窗跑绿当生产真值（两层窗·预演形≠生产形）；②把 run_state ok 当评分 pass（两态分立）；③把 engine_absent 当"正常没分"（装配毕不应出现·=缺件异常即报）；④把段 6 退出码 2 当链路故障（二值容忍 rc∈{0,2}·2=如实落卷的非 pass 态·链路语义内）；⑤迁移窗口内写 operating-records（冻结窗口纪律）；⑥用截断 UUID 查 cron job（须 36 位全量） |

## 二、功能面全景

### 2.1 触发面（第 0 道）

| 项 | 现势 |
| --- | --- |
| 触发 | 河源 TriRMC cron job·**首拍=周日 23:50 硬锚**（十阶段形 payload 在役态） |
| payload 两形态 | **十阶段形在役**（2026-11-13 22:12 换锚·cmd_len=2750/md5=4e1c7df5·判据锚五条族：cmd_len/md5/jobCount/enabled/schedule）+ **vB 形备档**（cmd_len=1741/md5=4f990e911·复原判定面专用）——两分禁互判 |
| 托转序列 | 事件驱动（候 CEO 锁定·锚 a8fd88e81）；SDE 预案分支 A=payload 零 PATCH·托转二可能全程零触发（锚 7dced229f） |

### 2.2 十阶段链全景（每段一问·fail-closed && 链）

| 段 | 问题 | 执行体（runtime/cognition/） | 段产物 | 退出码语义 |
|---|---|---|---|---|
| 1 | 该不该跑 | preflight.py | preflight.json | 0 过/2 拦 |
| 2 | 有资格吗 | qualify.py（五断言） | qualify.json | 0 过/2 拦 |
| 3 | 迁什么 | plan_scope.py（405 行·migrate/keep/carry_over 三分类+双向断言+幽灵检测） | plan.json | 0 过/2 拦 |
| 4 | 跑 | dce_steps.py（242 行·pull→migrate→commit→push 四步段序·dry-run 默认/--execute 授权窗·精确 pathspec 禁 -A） | dce.json | 0 过/2 拦 |
| 5 | 迁对没 | verify.py（276 行·四断言 A 毒化拦/B γ 归位=旧周 trees/ 目录存在性/C 新周 index 结构/D 对表） | verify.json | 0 过/2 拦 |
| 6 | 有没有分 | score_cli.py（117 行·三态 executed_ok/executed_failed/engine_absent）+score_engine.py（实弹引擎） | score.json | **二值容忍 rc∈{0,2}**——2=如实落卷的非 pass 态，链路继续 |
| 7 | 怎么评 | score_rubric.py（192 行·八列结构门+红灯 cap C79/G59+F2 免评分母） | report（不落 run_dir） | 0 过/2 拦 |
| 8 | 复盘收口 | close_skill.py（171 行·漏报护栏 upgrade_list_state+升级条目五字段 run_id/stage+trigger/routing/evidence/state） | close.json | 0 过/2 拦 |
| 9 | 有终点吗 | close_cli.py（99 行·三态 ok/failed/stale·absent 优先·manifest 终点记录非闸） | manifest.json | 0 过/2 拦 |
| 10 | 到达人了吗 | notify_done.py（117 行·双向路由·best-effort 永不拦·--dry-run-only） | — | — |

横切保障与读卷要点见[小白版 §三](01-beginner-guide.md)（退出码同族/run_id 全链主键/如实落卷三条）。

### 2.3 迁移器本体（段 4 的内核）

五步幂等链 `weekly_plane_shift`（十阶段段 4 DCE 的内部执行核）：

| 步 | 干什么 | 幂等语义 |
| --- | --- | --- |
| 1 create | 建新周骨架 | already_exists 不算失败 |
| 2 migrate | 上周平移 | 目标已存在即 skip |
| 3 carry_over | 未结项搬迁+8 周升级上报 | 目标存在即 skip |
| 4 validate | 链内校验 | 逐项断言素材源 |
| 5 agent_close | 收口落卷 | 重跑补卷 |

审计载体：`steps[]` 五步清单（每步 status/result/changes/errors/check_time）落 `.shift-ade.json` + git commit + per-run 日志。

## 三、使用旅程

### 旅程 A：作为普通员工，一周里你需要做什么

- **平时**：什么都不用做。你的 commit 只要正常提交，迁移链自然看得见。
- **周日首拍前**：把 `docs/workflow/operating-records/` 的改动 commit 并推送（编排层职责；顺手全仓推送是软习惯）。首拍到周一回流完成，**不要写 operating-records**（冻结窗口）。
- **周一早上**：看新周目录已建好（迁移 commit 落地）+ 首拍卷面终态。异常按[深度研究版](04-deep-research.md)的暴露口路径上报。

### 旅程 B：作为协作者，怎么查一次运行的链路

1. 找到本次运行的 **run_id**（首拍窗值守简报或 daemon 日志给出）。
2. 用它串起 **RUN_DIR 下七件段产物**：preflight.json→qualify.json→plan.json→dce.json→verify.json→score.json→close.json，最后看 **manifest.json** 终态章（ok/failed/stale）。
3. 断在哪一段，卷面 `errors` 字段给原因——链路语义=死在第一道出问题的工序，后面不会有半成品。

### 旅程 C：作为运维值班（首拍窗/异常时看什么）

1. **判读对表面**：按《首拍预期态判读表 v2》（`cto-firstshot-expected-state-brief-20261114.md`·七行判读）逐段对预期态——`run_state ok≠评分 pass`；`engine_absent`=缺件异常即报。
2. **迁移审计**：首拍跑完后看 `.shift-ade.json` 五步全 pass + manifest 终态。
3. **失败分级**：段 5 verify 拦（rc=2）→ 按卷面断言项定归属（A 毒化拦/B 归位/C 结构/D 对表）；job 连续 error → 报 CTO 域，**勿手动改 job state**（禁抹 nextRunAtMs——D-02）。
4. **手动补跑**：只用幂等兜底 `cron run <36 位全量 UUID>`，**禁止服务器手动 `--sync` 点火**。

### 旅程 D：作为评审者，"值不值得依赖"看什么

- **fail-closed 结构**：段 3-10 八件 CLI && 链——错误不跨段传染。
- **卷面诚实性**：替身禁令（缺/坏=FAIL-EXPECTED 禁空清单替身）+如实落卷（降级/缺件/未知态显式落卷）。
- **评分可复核**：段 7 规则摊开（八列结构门+红灯 cap），评分不是黑盒。
- **验收链**：γ 终态定谳卷（`cto-gamma-impl-acceptance-20261114.md`）+ STE 主审 CONDITIONAL_PASS+CTO 确认链——读这两卷再下结论。

## 四、价值主张

- **不靠记性**：翻页是确定性程序——"人忘"不再是单点。
- **不靠"跑完就行"**：十段链把"跑/对/分/收/达"分立成独立可验工序，深夜无人值守也有全程留痕。
- **错了知道死在哪段**：退出码同族+run_id 贯穿+段产物卷面，故障定位不靠猜。
- **诚实可评**：预演/生产两层窗分开报，缺件降级如实落卷——依赖它之前可以查它的卷面与验收链。

## 五、诚实边界（用前必读）

- **已实现**：十件 CLI 全实装+测试全绿（184 passed smoke 口径·2026-11-14 实勘）；γ 终态定谳（verify D 断言=旧周 trees/ 目录存在性·δ 分叉消除）；score 引擎实弹装配毕+CTO 验收毕；payload 十阶段形换锚在役；段 1/2 两段分立（D 族读段 1/E 族读段 2·CTO 认证）。
- **候拍/候锁**：生产形真值=周日 23:50 首拍（现役硬锚·**尚未发生**——预演窗结论只覆盖预演形）；托转序列事件驱动候 CEO 锁定。
- **挂账**：迁移域服务器证据回流复评（齿条①）。
- **历史口径注意**：五步链时代"周日 23:00"、TriMC(sg) 承载等表述为历史叙事冻结——现役以十阶段链判据锚卷与判读表 v2 为准。
- （每日进度兜底/patrol/Score shadow 属 FADE-012——已拆出，见 [../fade-012/](../fade-012/README.md)。）

## 六、验证方式（学完自测）

1. 跑全链自测：`python -m pytest runtime/cognition/ -q`（TriCompany 仓根·184 passed 基线）。
2. 对《首拍预期态判读表 v2》能说出任两段的预期态与异常态判读（至少含"run_state ok≠评分 pass"一条）。
3. 口测：向同事复述"周日首拍会发生什么（十段）+ 冻结窗口为什么存在 + 首拍异常怎么分级上报"三件事不卡壳。
4. 能指出 score 引擎探针正形：TC 仓根 cwd `python3 -m runtime.cognition.score_cli`——直跑 script 形会因 sys.path 缺仓根误报 engine_absent。

## 使用依据

- 十阶段链现役终态八锚+段 2-10 正文：[05-trigger-chain-draft.md](05-trigger-chain-draft.md)
- 十件 CLI 行数/职责/段产物：`runtime/cognition/` 2026-11-14 实读+[03-code-map.md](03-code-map.md) §二
- payload 供形正形（编排对表注①-⑥）：`cto-fsd-payload-supply-20261113.md`（W46 树 fade001-tenstage-deploy-20261115）
- 判据锚五条族：`值守预期形-十阶段形判据锚-20261113.md`（W46 树 fade001-phase1-build-20261114）
- 首拍判读表 v2：`cto-firstshot-expected-state-brief-20261114.md`；γ 定谳与验收链：`cto-gamma-impl-acceptance-20261114.md`（W46 树 fade001-tenstage-review-20261114）
- SDE 预案分支 A：锚 7dced229f；托转事件驱动：锚 a8fd88e81
- 全链自测：184 passed（smoke 口径）/181（discover 口径）口径差双真（57901674c）
- 冻结窗口与反面案例：runbook §7（W34→W35 落旧基 ae3d32fe 实录）
