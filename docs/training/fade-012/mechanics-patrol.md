<!-- GOVERNANCE: 本件为 FADE-012 草稿卷聚合稿，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-012 机制面聚合——patrol 巡检兜底/双笔迹/评分 shadow

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-012/mechanics-patrol.md
- syncMode: source-only
- lastSyncedAt: 卷面时点锚=git commit 时戳（零手打·D-47 增补款正形）

> **草稿态注记（2026-11-14·CEO 19:48:54 fade-001 重写令随批）**：本件=从 fade-001/ 01/02/03 三篇拆出的 FADE-012 机制内容**聚合稿**（素材保全优先·非重写）——各节标注拆出源。事实基线=2026-09-05 现势（patrol 951 行/30 用例基线）；接手时以现行版实读为准（锚点语义优先于行号）。

---

## 一、小白入门段（拆自 fade-001/01 §一/§二坏结局二/§三词 2/3/§四比喻）

**一句话**：公司的工作进展原来记在 AI 员工的"脑子里"（会话上下文）。会话会压缩、机器会重启、进程会崩——一旦出事，"我们这几天干了什么"就没了。FADE-012 把一份**粗粒度的工作日志**（daily-progress.md）随 git 推到三个地方（本地 / sg 服务器裸仓 / GitHub）。哪怕三点全灭，只要 GitHub 还在，就能把工作重建到最后 10 分钟以内——这是写进登记册的验收承诺。

**词 1：单写者（single writer）**
日志有两种笔迹：**助理主叙事**（AI 秘书长做完大事随手记，质量最高）和**巡检兜底补写**（确定性脚本，只在发现"落后了"时补一笔 commit 清单）。规矩：兜底**只追加、绝不改写**别人的内容；两人撞车时，兜底方退让（重试一次，再不行跳过这轮，下轮再补）。一台机器补一笔账，永远不会覆盖人的记录——这就是单写者原则。

**词 2：兜底巡检（patrol）**
每 10 分钟跑一次的确定性脚本（叫 patrol），它只回答一个问题："日志文件的最后一次更新之后，仓库里有没有新 commit？"有 → 说明有人干活了但日志没跟上 → 补写；没有 → 什么都不做（这叫 skip，是正常休息，不是故障）。

**比喻**：`daily-progress.md` = 墙上的**值班日志本**；助理主叙事 = 值班经理随手记的大事记；patrol 巡检 = 每 10 分钟来一次的**实习生**：只准往本子上贴"过去 10 分钟的打卡流水"（commit 清单），不准动经理写的字；贴之前先看一眼"上次贴完之后有没有新动静"，没动静就安静走开。**三端持久** = 日志本一式三份（本地/sg/GitHub），烧了哪份都补得回来。

## 二、双通道与安全设计（拆自 fade-001/02 §2.2）

| 通道 | 谁 | 干什么 |
| --- | --- | --- |
| 事件驱动主 | 董事长助理 | 销账/交付/裁决后**随手** append 当日节+push 三端——语义质量最高（哪件事值得记、怎么概括） |
| 定时巡检兜底 | sg daily-progress-watcher（patrol 脚本） | 槽位 5,15,25,35,45,55 分（每 10 分钟，同秒竞态消除）；门限开（日志落后）才补写 commit 清单块；**只追加不重写** |

巡检的安全设计（产品面看得见的四条）：

1. **拓扑门限**：判断"落后"用 git 拓扑（`git log <上次触碰>..HEAD`），不用时钟比较——同秒提交、变基重写都不会误判。
2. **recovery push 自愈**：上轮推送失败遗留的未推提交，下轮开头先重推——防"自己写过→门限闭合→永不重推"死锁。
3. **写入回滚保护**：写入前存底，回读校验失败即回滚到写前状态。
4. **推送分级**：sg-bare 必达（失败如实报 fail 等下轮自愈）；GitHub 尽力而为（无凭据快速失败，由事件驱动写收敛）。

## 三、活体证据：现在就去看两种笔迹（拆自 fade-001/01 §五）

打开本周进度文件 `TriMetaverse/docs/workflow/operating-records/<当前周>/daily-progress.md`：

1. 文件头部有一行声明：维护方=事件驱动主（董事长助理）+巡检兜底（daily-progress-watcher）。
2. 正文里你能看到两种段落：**「助理主叙事」**（人话总结）和**「巡检兜底补写」（daily-progress-watcher 自动）**（commit 流水清单）。
3. 用 `git log --oneline -- docs/workflow/operating-records/` 翻几页，会看到两种提交署名：助理的提交和 `docs(plane): 巡检兜底补写 ……（daily-progress-watcher 自动；FADE-001 维护项②/LG-011）`——**同一份文件、两种笔迹、互不覆盖**，就是单写者原则本尊（署名中"FADE-001 维护项②"为拆分前历史叙事）。

时间线彩蛋：巡检补写的调度槽位有错峰设计——sg 巡检兜底现行挂 **5,15,25,35,45,55 分**槽位（2026-08-31 CEO 定，消除与整点任务的同秒竞争）。你在本地 `git log` 里看到的巡检 commit 时点可能仍有 :00/:30 等戳——不同巡检实例与历史节奏都混在流水里，以你实跑所见为准。

## 四、评分体系 shadow 期（拆自 fade-001/02 §2.3）

`--score` 对真实日评分：T1-T8 八项，CLI 确定性六项（小计 80）+ Score Skill 语义两项（T3 事件及时性/T7 治理对齐，20 分）=100；双门槛=必选全过∧总分≥90。**shadow 阶段只观测不拦截**；达标日才接线为 push 终态硬门。scoreable 判据=当日事件驱动写与巡检补写**各≥1**。

## 五、patrol 代码地图（拆自 fade-001/03 §二 patrol 半壁·2026-09-05 实读基线）

`TriCompany/runtime/cognition/daily_progress_patrol.py`（**951 行**）——每日进度维护唯一执行体（DCE+Verify+Score CLI 三载合一）：

| 区 | 行段 | 内容 |
| --- | --- | --- |
| 常量 | L55-74 | GIT_REMOTE/GIT_BRANCH、评分合同（SCORE_PROTOCOL="daily-progress-score" L62）、节奏（TICK_SECONDS=600/JOB_TIMEOUT=180/T2_MAX_GAP=780 L64-66）、权重（SCORE_WEIGHTS 小计 80 L67/SCORE_SKILL_EXTERNAL T3+T7=20 L68/SCORE_THRESHOLD=90 L69）、服务器默认路径（/srv/fleet/… L72-73） |
| 周路径与节定位 | L80-100 | week_relpath（ISO 周推算 L85）、day_heading（`## YYYY-MM-DD（周X）` L91）、**day_section_index（日期前缀匹配——星期标签误标不触发重复建节 L95-99）** |
| git 工具族 | L101-176 | git_env（GIT_TERMINAL_PROMPT=0 快速失败 L101）、run_git、**git_pull_rebase（attempts=2 冲突退让 L119）**、file_last_touch（L133）、recent_commits（L148）、**commits_since（拓扑门限 `git log <base>..HEAD` L177）** |
| 组块 | L211-335 | registry_snapshot/registry_line、build_increment（L246：补写行+commit 清单默认上限 15+registry 行三件）、build_day_section（L261）、**verify_day_section（L281 写入后回读）**、git_commit_file/git_push/unpushed_count |
| 主流程 | L336-476 | make_envelope（L336）、**patrol_once（L352 一轮全流程，rollback L430）** |
| 评分 | L477-672 | day_window/commits_in_window、check_score_t1(L489)/t2(L510)/t4(L546)/t5(L557)/t6(L582)/t8(L596)、**run_score（L603）** |
| 沙箱自测 | L674-951 | _init_sandbox（L674 自建 bare+repo+tco 三仓）、用例族 L707-883、self_test（L901）、main（L909） |

## 六、四大机制（拆自 fade-001/03 §三——FADE-012 维护面的命根子）

**1. 拓扑门限（commits_since L177）**
判据问题："文件最后触碰之后有没有新 commit？"实现=`git log <touch_full>..HEAD -- <rel>`——git DAG 可达性，**天然无同秒问题、变基重写不影响**。历史：首版用"时间戳严格大于"，20:20 skip 实测抓出同秒漏计（rebase 连发使 marker 与进度提交同秒），3082d7d 改拓扑口径并留回归用例（自测 Case I 用 GIT_COMMITTER_DATE/GIT_AUTHOR_DATE 固定同秒造提交，断言全计入）。**教训一句话：顺序/计数判定用 DAG，不用墙上时钟。**

**2. 单写者冲突口径（git_pull_rebase L119 + patrol_once）**
巡检与助理写撞车：`pull --rebase origin dev` 重试一次（attempts=2），再失败**跳过本轮**（返回 skip envelope，不算 cron 失败，下轮再补）。append-only 是硬约束：写入只追加补写块；评分 T4（check_score_t4 L546）机器断言"patrol 身份提交补丁零删除行"。巡检身份=commit 内联 `TriMC Scheduler <trimc-scheduler@fleet.local>`——Score 用它区分"巡检写"与"事件写"。

**3. recovery push（patrol_once L377 一带）**
上轮 push 失败遗留的未推提交，本轮开头先重推——否则"文件已被自己触碰→门限闭合→永不重推"死锁（头注 L21-24 原话）。配套 unpushed_count（L326）做自检。

**4. 写入回滚保护（rollback L430）**
写入前存 pre_bytes；verify_day_section 回读失败（当日节不在/本次追加块缺失/锚点格式不合）或 commit 失败 → 回滚到写前状态 + fail envelope。**先写后报的字段化**：任何 fail 都有小票，没有"写了但没说"。

推送分级：sg-bare 必达（失败不伪造终态，commit 留舰队克隆等下轮自愈）；GitHub best-effort（git_env 的 GIT_TERMINAL_PROMPT=0 快速失败禁挂起）。

## 七、评分实现（拆自 fade-001/03 §四·shadow 期载体）

- **scoreable 判据**（run_score L603 一带）：当日 patrol 身份提交与事件身份提交**都非空**；不满足→`not-scoreable`+reason（skip-only 轮不可评分）。
- **六项 CLI 确定性检查**：T1 当日节结构（L489）/T2 兜底及时性（L510，≤780s=tick 600+timeout 180；基线规则=仅计当日首次文件触碰后的触发，部署日 regime 边界不重复扣）/T4 单写者（L546）/T5 三端持久（L557，ls-remote 对账，GitHub 容差≤24h，离线=不可验非 FAIL）/T6 门限正确性（L582，零空节+提交消息格式）/T8 载体质量（L596，self-test 全过+无 LLM）。
- **两项留 Skill**：T3 事件及时性/T7 治理对齐（SCORE_SKILL_EXTERNAL L68）——CLI 小计 80 < 阈值 90（L69），**数学上保证 shadow 期不可能偷偷达标**。
- gate_wired=false 写死：`--score` 只观测不拦截；接线时点=扩评达标日（push 终态门前置 score）。

## 八、接手起步（拆自 fade-001/03 §七 012 面各条）

1. 跑自测：`python -m runtime.cognition.daily_progress_patrol --self-test`（TriCompany 仓根）——基线 **30 用例全 ok（2026-09-05 实测 EXIT=0）**。改 patrol 必跑（T8 是评分项）。
2. 跑 dry-run：默认模式输出小票——读懂 skip / would-write（含 would_write_first_line 预览）两态。
3. 读码顺序：头注 L1-40（设计锚/数据边界/单写者口径一次讲清）→ L177-208（拓扑门限）→ L352-476（patrol_once）→ L246-300（组块+verify）→ L603-672（run_score）→ L674-695（沙箱）。
4. 找到同秒回归用例（Case I，L784 一带）与 T4 负例（S6），读懂它们防什么——改门限或写入逻辑前先看。
5. 服务器侧只读起步：看 `/var/lib/trimc/cron/logs/` 巡检小票。

**常见误区速查（012 面）**：把 self-test 30/30 说成"Score 实跑通过"／把 65/80 当不及格（CLI 小计上限 80+regime 边界裁定）／给 patrol 加 python3.10+ 语法（服务器 python3.8 硬约束）／假设 GitHub push 必达（尽力而为端）／把 skip 当故障（门限闭合=正常）。

## 两个新人疑问（拆自 fade-001/01 §七 Q1/Q2）

**Q1：助理反正每次都随手记了，为什么还要巡检兜底？**
因为"人会忘、会忙、会话会断"。事件驱动主保证**记的质感**，巡检兜底保证**记的下限**——最坏 10 分钟内必有一笔。两者配合才是设计，拆开任何一半都会退化回旧的 23 小时丢失窗口。

**Q2：巡检推 GitHub 失败了，要慌吗？**
不慌，这是**设计内降级**：服务器巡检没有 GitHub 凭据，推 GitHub 是"尽力而为"（失败不阻塞、不伪造成功）；sg-bare 才是必达端。三端里任何一端可达，日志就不灭——失守的那端由下一次事件驱动写收敛补齐。

## 使用依据

- 拆出源：fade-001/ 01-beginner-guide.md §一/§二/§三/§四/§五/§六/§七 Q1Q2；02-product-guide.md §2.2/§2.3；03-code-map.md §二 patrol 半壁/§三/§四/§七 012 面条目（2026-11-14 CEO 重写令拆出·素材保全聚合）
- patrol 实读基线：`daily_progress_patrol.py` 951 行（2026-09-05）+ `--self-test` 30/30 实测（2026-09-05T04:2xZ）
- 拓扑门限与槽位：TriCompany 3082d7d（拓扑口径）+ W36 daily-progress.md 08-31 节（槽位错峰）
- registry：`fade-registry.md` FADE-012 条（v2.2.0·0c54864·候 CEO 追认）
