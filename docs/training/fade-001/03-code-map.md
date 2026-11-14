<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-001/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-001 代码版——十阶段迁移链研发实现地图

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-001/03-code-map.md
- syncMode: source-only
- lastSyncedAt: 卷面时点锚=git commit 时戳（零手打·D-47 增补款正形）

> **重写批注记（v2.0.0·2026-11-14·CEO 19:48:54 fade-001 重写令）**：①本篇重组为**十阶段链单执行体族地图**（原 §五·乙 升为正文主体）；②原 §二 patrol 半壁/§三 四大机制/§四 评分实现等每日进度内容（FADE-012）**已拆出**至 [../fade-012/mechanics-patrol.md](../fade-012/mechanics-patrol.md)——本篇纯迁移域零混装。修正留痕：v1.x（09-05 基线·双执行体合讲）→ v1.9（11-12 拆分注记+11-14 现势更新注记）→ v2.0.0（11-14 重写令·patrol 全部拆出+十阶段地图为主体）。

读者：要接手 FADE-001 十阶段链的工程师。
纪律声明：本文锚点为 **2026-11-14 对现行版实读**——十件 CLI 全在 `TriCompany/runtime/cognition/`；迁移器本体=`runtime/cognition/weekly_plane_shift.py`（328 行·09-05 实读基线）。行号漂移防护：**锚点语义优先于行号**，接手先 `git log --oneline <file>` 再按符号重定位。

跨服务器实勘边界（诚实声明）：迁移 cron 的**运行态配置在服务器侧**（河源 TriRMC cron job 的 cron 表达式/timeout/payload 现值），本机不可直读——本文代码面锚为本地仓实勘，运行态现值以服务器 API GET（`GET /internal/v1/cron/jobs`·齿条③晨检口径）与判据锚卷为准，**不以本机 clone 冒充部署态**。

前置：已读 [产品版](02-product-guide.md)。

---

## 一、培训判断与学习路径

学完本篇你应能：①画出十阶段链一段 failing 时全链的行为（&& 链 fail-closed·死在第一道）；②说清每件 CLI 的段产物与退出码语义；③知道段 6 二值容忍与三态分立的设计；④独立跑通全链自测并读懂任一用例的断言意图；⑤说清本机实勘与河源运行态的边界。

| 步 | 做什么 | 验证 |
| --- | --- | --- |
| 1 | 读 §二 十阶段执行体地图 | 能背出十段问题链+各段产物文件名 |
| 2 | 读 §二 横切八条 | 能说出退出码同族与 run_id 贯穿语义 |
| 3 | 跑 §六 自测任务 1 | 184 passed（smoke 口径），能说出与 181 discover 口径的差 |
| 4 | 读 §三 迁移器本体 | 能背出五步与各自幂等语义 |
| 5 | 读 §四 TriRMC 面 | 能说出本机 clone 与 heyuan 部署态的差异处理 |

## 二、十阶段链执行体地图（2026-11-14 现役终态）

十阶段形 payload（河源 jobs.json command 串·cmd_len=2750/md5=4e1c7df5·2026-11-13 22:12 换锚在役）编排结构（正形真源=`cto-fsd-payload-supply-20261113.md` §三 编排对表注）：

**段 1/2（payload 基座段·vB 原形保留）+段 3-10（八 CLI && 链 fail-closed）**：

| 段 | CLI（runtime/cognition/） | 行数 | 职责一句话 | 段产物 |
|---|---|---|---|---|
| 1 | preflight.py | — | 该不该跑（is_sunday 周门+tokens 参数齐·D 族读它） | preflight.json |
| 2 | qualify.py | — | 载体资格（五断言·E 族读它） | qualify.json |
| 3 | plan_scope.py | 405 | 迁什么（migrate/keep/carry_over 三分类+双向断言+幽灵检测） | plan.json |
| 4 | dce_steps.py | 242 | 跑（四步段序·dry-run 默认/--execute 授权窗·精确 pathspec 禁 -A） | dce.json |
| 5 | verify.py | 276 | 迁对没（四断言·D=旧周 trees/ 目录存在性·γ 终态形·δ 分叉消除） | verify.json |
| 6 | score_cli.py+score_engine.py | 117+— | 有没有分（三态分立 executed_ok/executed_failed/engine_absent·**引擎实弹态**） | score.json |
| 7 | score_rubric.py | 192 | 怎么评（结构门+红灯 cap C79/G59+F2 免评分母+T1 落位≠生效） | report（不落 run_dir） |
| 8 | close_skill.py | 171 | 复盘收口（漏报护栏 upgrade_list_state+升级条目五字段 run_id/stage+trigger/routing/evidence/state） | close.json |
| 9 | close_cli.py | 99 | run 终点（三态 ok/failed/stale·absent 优先·manifest 终点记录非闸） | manifest.json |
| 10 | notify_done.py | 117 | 结论到达（双向路由·best-effort 永不拦·--dry-run-only·双通知机理与 ADE 面 _notify_shift 并存≠重复投递） | — |

payload 细节锚（供形正形卷 §三 编排对表注）：vB 基座段 L1-14 逐字保留·段 6 二值容忍 rc∈{0,2}·RUN_DIR arrival touch·notify_done 真形态。

**全族横切设计模式八条（读任何段前先记）**：退出码同族（0 交棒/2 拦）·哑卷防线（落卷败 print+return 2）·替身禁令（缺/坏=FAIL-EXPECTED 禁空清单替身）·结构门写前自校验·mtime 序取最新（妆容劫持防）·stdout reconfigure GBK 兜底·run_id 全链主键（七件段产物同串贯穿）·如实落卷（降级/缺件/未知态显式落卷不静默）。

**两层窗主线**（裁决 A）：预演形（链路形态全真·零生产触）≠生产形真值（周日 23:50 首拍·vB 判据族至 payload 换形）。首拍预期态判读表 v2=值守对表面（`cto-firstshot-expected-state-brief-20261114.md`·engine_absent=缺件异常即报·run_state ok≠评分 pass）。

**探针正形**（防误报·装配毕勘定笔）：score_cli 探针=TC 仓根 cwd `python3 -m runtime.cognition.score_cli`——直跑 script 形误报 engine_absent（sys.path 缺仓根）。

**全链自测**（TriCompany 仓根·2026-11-14 实勘）：`python -m pytest runtime/cognition/ -q`——cognition 全目录 184 passed（smoke 口径·CTO γ 验收独立重跑读数；discover 口径 181=不含 smoke_test 3 案——**口径差双真非笔误**·57901674c）。

段 1/2 分立读数口径（CTO 14:01:39 认证）：score D 族读段 1（preflight）/E 族读段 2（qualify）——两段各答各问，禁互判。

## 三、迁移器本体：weekly_plane_shift（段 4 DCE 的内部执行核）

> **两层注记（现役形）**：本节五步链=**迁移器本体**（域①内部·幂等可重跑）；其外包着十阶段编排壳（§二）。引用命令时带全名消歧：`weekly_plane_shift.py`=CLI 入口（main+γ 闸）≠`weekly_plane.py`=库函数面（migrate_weekly_plane 实装）。

328 行（2026-09-05 实读基线），五步表：

| 步 | 函数锚 | 幂等语义 |
| --- | --- | --- |
| 1 create | main L229-236（create_weekly_plane） | already_exists **不算失败**（L229 注记） |
| 2 migrate | L238-240（migrate_weekly_plane，内含 retire） | 重跑=重复迁移目标已存在即 skip |
| 3 carry_over | L244-246（shift_carry_over L58，含 8 周升级 bump_row） | 目标存在即 skip |
| 4 validate | L250-253（validate_index） | 链内校验步，逐项断言素材源 |
| 5 agent_close | L259（review_shift L128 产 review 输入） | 收口落卷；push_trilc_notification L199 通知 |

审计载体：`steps[]` 五步清单（每步 status/result/changes/errors/check_time）落 `.shift-ade.json`——迁移域评分卷（paper-① audit-record 项）的对卷物。

## 四、TriRMC cron 面（跨河源实勘边界示范）

本机 `/d/Code/ai/TriRMC/` clone 可实勘的**代码面**：

- `src/cli.ts:51`：cron 预设 `weekly-plane-shift`（`npx tsx src/cli.ts cron add --plane-shift` 路线）；
- `deploy/trirmc-mc.service`：systemd 单元——**服务级 User=fleet 单身份**，这就是"job 不带 runAs"的架构根因（runAs=fleet 会 runuser 必炸，08-30 三跳观察实录在 W36 daily-progress）；
- **告警闸模块**（2026-11-13/14 施工·本机检出顶 e408da5）：F1/F6 合并判据=job 级独立 timer 读 job-store 判定（漏拍/败跑双判据+dedup 熔断）+F2 arrival-missing 三分支（fd866ca）+probeArrivalFace mtime 序（e408da5 勘修·字典序被模板字面量 run dir 劫持实锚）——部署候窗·本机 clone 为施工线检出非现役部署态；
- `scripts/rmc_tick.py` 等：R 面治理注入件（LG-016 件 3 线，非本实例核心）。

**不可实勘的运行态**（如实标注，勿脑补）：河源侧现役 job 的 cron 表达式/timeout/payload 现值——查法=服务器 API `GET /internal/v1/cron/jobs`（齿条③晨检断言 34753ae 的核验路径）；本机 clone 与 heyuan 部署态可能存在版本差（切指/部署滞后），**结论引用一律以 API 读数与判据锚卷为准**。

runbook 命令族（TriMMC 仓）：`cron add/update/list/run`；坑两条——job 必须用 **36 位全量 UUID**；`cron update` 缺 `--timezone` 旗标且 `--cron` 整体替换 schedule 会丢 tz 字段（runbook §7 跟进项）。

## 五、迁移链运维要点

- **解释器硬约束**：服务器 python3.8（系统 3.6.8 不兼容新语法）——迁移链代码禁 f-string/match。
- **测试根先行**：`python3.8 -m runtime.cognition.weekly_plane_shift --from W33 --to W34 --start-date <日期> --operating-root <测试根>`（不带 --sync=只读演练）；真跑失败不回滚代码——五步全幂等，修正后直接重跑。
- **身份与推送**：commit 内联 TriMC Scheduler；push `/srv/git/TriMetaverse.git HEAD:dev`。
- **前置纪律**：迁移冻结窗口（runbook §7）——输入基线的确定性靠人守，DCE 本身不保证输入。

## 六、接手任务清单（第一周）

0. **先读 §二 执行体地图+[05 稿段 2-10](05-trigger-chain-draft.md)**（现役终态叙事），跑全链自测：`python -m pytest runtime/cognition/ -q`（184 passed 基线·smoke 口径）——改十阶段任何段模块必跑。
1. 单件入手顺序建议：plan_scope（§段 3·三分类最独立）→ dce_steps（§段 4·与五步本体对接处）→ verify（§段 5·四断言）→ score 三件（§段 6/7）→ close 两件（§段 8/9）→ notify_done（§段 10）；每件先读其测试再读实现。
2. 找到替身禁令与哑卷防线在任一件 CLI 的实现位置，读懂它们防什么——改任何段前先看。
3. 服务器侧只读起步：`GET /internal/v1/cron/jobs` 看现役 job 现值（36 位全量 UUID）；**新人不手动 `--sync` 点火**，补跑用 `cron run <全量 UUID>`。
4. **（生产触点面禁触清单）**payload 换形/--execute wiring/判据族换锚/daemon 面——新人禁触，候部署树授权窗；读首拍预期态判读表 v2 建立判读面（知悉即达标）。

**常见误区速查**（每条有事故/裁定背书）：信文档旧 cron 表达式（以 API 现值为准）／用截断 UUID 查 job／手动改 cron state 抹 nextRunAtMs（D-02，永不调度）／把预演绿当首拍绿（两层窗）／把 run_state ok 说成"评分 pass"／把 engine_absent 当正常态（=缺件异常即报）／探针直跑 script 形（sys.path 陷阱·用 -m 形）。

## 使用依据

- **十阶段执行体地图（§二·2026-11-14 现役终态）**：runtime/cognition 十件 CLI 行数实读+payload 供形正形卷（`cto-fsd-payload-supply-20261113.md` §三）+首拍预期态判读表 v2（`cto-firstshot-expected-state-brief-20261114.md`）+γ 验收卷（`cto-gamma-impl-acceptance-20261114.md`）+判据锚卷（`值守预期形-十阶段形判据锚-20261113.md`）+全链自测实勘 184 passed（2026-11-14）
- 迁移器本体五步表：`weekly_plane_shift.py` 328 行（2026-09-05 实读基线·接手以现行版实读为准）
- 运行态现值口径：服务器 API `GET /internal/v1/cron/jobs`（齿条③·TriCompany 34753ae）+判据锚卷五条族
- 评分卷宗：`fade-papers/FADE-001-paper.json`（90/100·FADE-001 迁移域冻结链零改动）
- 纪律：`TriCompany/docs/workflow/engineering-disciplines.md`（D-02 cron state）
