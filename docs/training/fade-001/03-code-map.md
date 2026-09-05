<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-001/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-001 代码版——patrol 与迁移链研发实现地图

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-001/03-code-map.md
- syncMode: source-only
- lastSyncedAt: 2026-09-05

读者：要接手 FADE-001 双执行体的工程师。
纪律声明：本文锚点为 **2026-09-05 对现行版实读**——patrol=`TriCompany/runtime/cognition/daily_progress_patrol.py`（**951 行**，下称 patrol）+迁移链=`runtime/cognition/weekly_plane_shift.py`（**328 行**，下称 shift）。行号漂移防护同 FADE-002 代码版：**锚点语义优先于行号**，接手先 `git log --oneline <file>` 再按符号重定位。
跨服务器实勘边界（诚实声明）：①迁移 cron 与②兜底 watcher 的**运行态配置在服务器侧**（河源 TriRMC cron job 9c81c7ec / sg watcher job），本机不可直读——本文代码面锚为本地仓实勘，运行态现值以服务器 API GET（齿条③晨检口径）与 runbook 现势注记为准，**不以本机 clone 冒充部署态**。

前置：已读 [产品版](02-product-guide.md)。

---

## 一、培训判断与学习路径

学完本篇你应能：①画出 patrol 一轮 patrol_once 的完整流程（门限→组块→写入→verify→push）；②说清拓扑门限为什么不用时钟比较；③独立跑沙箱自测并读懂任一用例的断言意图；④知道迁移五步链每步的幂等语义与审计落点；⑤说清本机实勘与服务器运行态的边界。

| 步 | 做什么 | 验证 |
| --- | --- | --- |
| 1 | 读§二双执行体地图 | 能说出两个文件各管哪个域 |
| 2 | 读§三 patrol 四大机制 | 能指出门限与 recovery push 的函数行 |
| 3 | 跑§七自测任务 1 | 30 用例全 ok，能解读 Case I 的回归意图 |
| 4 | 读§五迁移链 | 能背出五步与各自幂等语义 |
| 5 | 读§六 TriRMC 面 | 能说出本机 clone 与 heyuan 部署态的差异处理 |

## 二、双执行体地图

### patrol（951 行）——维护域②唯一执行体（DCE+Verify+Score CLI 三载合一）

| 区 | 行段 | 内容 |
| --- | --- | --- |
| 常量 | L55-74 | GIT_REMOTE/GIT_BRANCH、评分合同（SCORE_PROTOCOL="daily-progress-score" L62）、节奏（TICK_SECONDS=600/JOB_TIMEOUT=180/T2_MAX_GAP=780 L64-66）、权重（SCORE_WEIGHTS 小计 80 L67/SCORE_SKILL_EXTERNAL T3+T7=20 L68/SCORE_THRESHOLD=90 L69）、服务器默认路径（/srv/fleet/… L72-73） |
| 周路径与节定位 | L80-100 | week_relpath（ISO 周推算 L85）、day_heading（`## YYYY-MM-DD（周X）` L91）、**day_section_index（日期前缀匹配——星期标签误标不触发重复建节 L95-99）** |
| git 工具族 | L101-176 | git_env（GIT_TERMINAL_PROMPT=0 快速失败 L101）、run_git、**git_pull_rebase（attempts=2 冲突退让 L119）**、file_last_touch（L133）、recent_commits（L148）、**commits_since（拓扑门限 `git log <base>..HEAD` L177）** |
| 组块 | L211-335 | registry_snapshot/registry_line、build_increment（L246：补写行+commit 清单默认上限 15+registry 行三件）、build_day_section（L261）、**verify_day_section（L281 写入后回读）**、git_commit_file/git_push/unpushed_count |
| 主流程 | L336-476 | make_envelope（L336）、**patrol_once（L352 一轮全流程，rollback L430）** |
| 评分 | L477-672 | day_window/commits_in_window、check_score_t1(L489)/t2(L510)/t4(L546)/t5(L557)/t6(L582)/t8(L596)、**run_score（L603）** |
| 沙箱自测 | L674-951 | _init_sandbox（L674 自建 bare+repo+tco 三仓）、用例族 L707-883、self_test（L901）、main（L909） |

### shift（328 行）——迁移域①五步链（DCE+链内 validate+agent_close）

| 步 | 函数锚 | 幂等语义 |
| --- | --- | --- |
| 1 create | main L229-236（create_weekly_plane） | already_exists **不算失败**（L229 注记） |
| 2 migrate | L238-240（migrate_weekly_plane，内含 retire） | 重跑=重复迁移目标已存在即 skip |
| 3 carry_over | L244-246（shift_carry_over L58，含 8 周升级 bump_row） | 目标存在即 skip |
| 4 validate | L250-253（validate_index） | 链内校验步，逐项断言素材源 |
| 5 agent_close | L259（review_shift L128 产 review 输入） | 收口落卷；push_trilc_notification L199 通知 |

审计载体：`steps[]` 五步清单（每步 status/result/changes/errors/check_time）落 `.shift-ade.json`——迁移域评分卷（paper-① audit-record 项）的对卷物。

## 三、patrol 四大机制（维护域的命根子）

**1. 拓扑门限（commits_since L177）**
判据问题："文件最后触碰之后有没有新 commit？"实现=`git log <touch_full>..HEAD -- <rel>`——git DAG 可达性，**天然无同秒问题、变基重写不影响**。历史：首版用"时间戳严格大于"，20:20 skip 实测抓出同秒漏计（rebase 连发使 marker 与进度提交同秒），3082d7d 改拓扑口径并留回归用例（自测 Case I 用 GIT_COMMITTER_DATE/GIT_AUTHOR_DATE 固定同秒造提交，断言全计入）。**教训一句话：顺序/计数判定用 DAG，不用墙上时钟。**

**2. 单写者冲突口径（git_pull_rebase L119 + patrol_once）**
巡检与助理写撞车：`pull --rebase origin dev` 重试一次（attempts=2），再失败**跳过本轮**（返回 skip envelope，不算 cron 失败，下轮再补）。append-only 是硬约束：写入只追加补写块；评分 T4（check_score_t4 L546）机器断言"patrol 身份提交补丁零删除行"。巡检身份=commit 内联 `TriMC Scheduler <trimc-scheduler@fleet.local>`——Score 用它区分"巡检写"与"事件写"。

**3. recovery push（patrol_once L377 一带）**
上轮 push 失败遗留的未推提交，本轮开头先重推——否则"文件已被自己触碰→门限闭合→永不重推"死锁（头注 L21-24 原话）。配套 unpushed_count（L326）做自检。

**4. 写入回滚保护（rollback L430）**
写入前存 pre_bytes；verify_day_section 回读失败（当日节不在/本次追加块缺失/锚点格式不合）或 commit 失败 → 回滚到写前状态 + fail envelope。**先写后报的字段化**：任何 fail 都有小票，没有"写了但没说"。

推送分级：sg-bare 必达（失败不伪造终态，commit 留舰队克隆等下轮自愈）；GitHub best-effort（git_env 的 GIT_TERMINAL_PROMPT=0 快速失败禁挂起）。

## 四、评分实现（shadow 期载体）

- **scoreable 判据**（run_score L603 一带）：当日 patrol 身份提交与事件身份提交**都非空**；不满足→`not-scoreable`+reason（skip-only 轮不可评分）。
- **六项 CLI 确定性检查**：T1 当日节结构（L489）/T2 兜底及时性（L510，≤780s=tick 600+timeout 180；基线规则=仅计当日首次文件触碰后的触发，部署日 regime 边界不重复扣）/T4 单写者（L546）/T5 三端持久（L557，ls-remote 对账，GitHub 容差≤24h，离线=不可验非 FAIL）/T6 门限正确性（L582，零空节+提交消息格式）/T8 载体质量（L596，self-test 全过+无 LLM）。
- **两项留 Skill**：T3 事件及时性/T7 治理对齐（SCORE_SKILL_EXTERNAL L68）——CLI 小计 80 < 阈值 90（L69），**数学上保证 shadow 期不可能偷偷达标**。
- gate_wired=false 写死：`--score` 只观测不拦截；接线时点=扩评达标日（push 终态门前置 score）。

## 五、迁移链运维要点

- **解释器硬约束**：服务器 python3.8（系统 3.6.8 不兼容新语法）——写代码禁 f-string/match（patrol 同约束）。
- **测试根先行**：`python3.8 -m runtime.cognition.weekly_plane_shift --from W33 --to W34 --start-date <日期> --operating-root <测试根>`（不带 --sync=只读演练）；真跑失败不回滚代码——五步全幂等，修正后直接重跑。
- **身份与推送**：commit 内联 TriMC Scheduler；push `/srv/git/TriMetaverse.git HEAD:dev`。
- **前置纪律**：迁移冻结窗口（runbook §7）——输入基线的确定性靠人守，DCE 本身不保证输入。

## 六、TriRMC cron 面（跨河源实勘边界示范）

本机 `/d/Code/ai/TriRMC/` clone 可实勘的**代码面**：

- `src/cli.ts:51`：cron 预设 `weekly-plane-shift`（`npx tsx src/cli.ts cron add --plane-shift` 路线）；
- `deploy/trirmc-mc.service`：systemd 单元——**服务级 User=fleet 单身份**，这就是"job 不带 runAs"的架构根因（runAs=fleet 会 runuser 必炸，08-30 三跳观察实录在 W36 daily-progress）；
- `scripts/rmc_tick.py` 等：R 面治理注入件（LG-016 件 3 线，非本实例核心）。

**不可实勘的运行态**（如实标注，勿脑补）：河源侧现役 job 9c81c7ec 的 cron 表达式/timeout/payload 现值——查法=服务器 API `GET /internal/v1/cron/jobs`（齿条③晨检断言 34753ae 的核验路径）；sg watcher job 槽位现值同理。本机 clone 与 heyuan 部署态可能存在版本差（切指/部署滞后），**结论引用一律以 API 读数为准**。
runbook 命令族（TriMMC 仓）：`cron add/update/list/run`；坑两条——job 必须用 **36 位全量 UUID**；`cron update` 缺 `--timezone` 旗标且 `--cron` 整体替换 schedule 会丢 tz 字段（runbook §7 跟进项）。

## 七、接手任务清单（第一周）

1. 跑自测：`python -m runtime.cognition.daily_progress_patrol --self-test`——基线 **30 用例全 ok（2026-09-05 实测 EXIT=0）**。改 patrol 必跑（T8 是评分项）。
2. 跑 dry-run：默认模式输出小票——读懂 skip / would-write（含 would_write_first_line 预览）两态。
3. 读码顺序：头注 L1-40（设计锚/数据边界/单写者口径一次讲清）→ L177-208（拓扑门限）→ L352-476（patrol_once）→ L246-300（组块+verify）→ L603-672（run_score）→ L674-695（沙箱）。
4. 找到同秒回归用例（Case I，L784 一带）与 T4 负例（S6），读懂它们防什么——改门限或写入逻辑前先看。
5. 服务器侧只读起步：看 `/var/lib/trimc/cron/logs/` 巡检小票；**新人不手动 `--sync` 点火**，补跑用 `cron run <全量 UUID>`。

**常见误区速查**（每条有事故/裁定背书，详见两件历史档教程误区表）：信文档旧 cron 表达式（以 API 现值为准）／用截断 UUID 查 job／手动改 cron state 抹 nextRunAtMs（D-02，永不调度）／把 self-test 30/30 说成"Score 实跑通过"／把 65/80 当不及格／给 patrol 加 python3.10+ 语法／假设 GitHub push 必达。

## 使用依据

- patrol/shift 全函数行号：两文件 2026-09-05 实读（951/328 行）
- 自测读数：`--self-test` 30 用例全 ok、EXIT=0（2026-09-05T04:2xZ 实跑）
- 运行态现值口径：runbook 时点修正注记（周日 23:00 heyuan 9c81c7ec）+ TriCompany 34753ae（齿条③ API GET 断言）+ W36 daily-progress.md 08-31 节（去 runAs 三跳观察/槽位移）
- 评分卷宗：fade-papers/FADE-001-paper.json（90/100）+ FADE-001-paper-maintenance.json（T1-T8/65/80/shadow→gate）
- 历史档函数级拆解：fade-001-maintenance-deep-dive.md 第二部分（sg 纵深篇；行号为 08-28 版，接手以本文现行锚为准）
