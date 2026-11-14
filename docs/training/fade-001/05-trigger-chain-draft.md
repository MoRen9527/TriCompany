# FADE-001 培训草稿（FADE 规范十阶段制·draft）

<!-- GOVERNANCE: 本稿真源在 TriCompany/docs/training/fade-001/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

> **本稿定形（CEO 2026-11-10 21:11 令原话）**：更新修正其下原有四个文档（01-04）的**临时依据和记录**——边研究边更新，本目录 01-04 四文档的修订以本稿为依据源；本稿自身随 CEO×BOD×RDT 三方拆解进度同步丰富。

- sourceOfTruth: TriCompany/docs/training/fade-001/05-trigger-chain-draft.md
- syncMode: draft（培训草稿——候 CEO×BOD×RDT 三方共读完善后转正身）
- lastSyncedAt: 2026-11-10T21:00:07+08:00（date 现查原值·写前现查）
- 令源: CEO 2026-11-10 20:38 直连令（经 BOD 20:39:42+08 转办）——「把 FADE-001 触发全链七层写成培训文档·标 draft·CEO 针对性提问用，后续三方一起完善成 fade-001 培训文档正身」
- 大纲重组令: CEO 2026-11-10 20:59 直连令（经 BOD 转办）——大纲升为 FADE 规范十阶段制，现七层全链内容整体落位第一段「触发执行」，其余九段候拆解逐段丰富
- **同步机制**：本稿大纲=FADE 规范十阶段·与 BOD×CEO 拆解进度同步丰富（CEO 2026-11-10 20:59 令·三方完善制）——BOD 每完成一段拆解（CEO OK 后）通知 RDT 丰富对应段
- 材料正身: `TriMetaverse/docs/execution/fade-001-improvement-20261110.md` §三「第一段补强·触发流程导读」（七层表+活体实锚+F4-F6）+§三第一段（F1-F3）——**本稿系其培训化展开，冲突一律回该真源**
- 读法承诺: 每层四件套=大白话干什么 → 代码在哪 → 想深挖怎么亲手查（可跑命令）→ CEO 可能想问的点
- 边界声明: 河源侧活体读数一律引 11-10 20:1x 河源直探实锚（材料正身 §三），本稿不另探；全文零 token 值面

---

## 十阶段总览（大纲现势·2026-11-14 重更新批）

> **重更新批注记（CEO 2026-11-14 16:19:08 直令「按现有整条链（FADE-001）状态，让 rdt 重新更新完善 fade-001 教程」·COS 16:20 派工转）**：段 2-10 已按**现役终态**填充（代码全实装+测试全绿·非骨架态）。历史演进面（γ/δ 分叉、v1 判读表、engine_absent 预期态等**已废止形态**）不入各段正文——需要时查「背景/勘革」指针节与树卷真源。
>
> **现役终态八锚速览**（写作基准·素材以树卷/git 在链卷为准）：
> ① 十阶段形 payload 在役（cmd_len=2750/md5=4e1c7df5·判据锚卷 e672f3f50）+vB 形备档（复原判定面专用 8237d12af）·托转一/二换锚序列=事件驱动（预告重排窗口语义版 a8fd88e81）；② score 引擎实弹态（v2 判读族 governs·生效锚=装配毕 12:25+CTO 验收毕·afb98d2b8）；③ 段 1 preflight/段 2 qualify 两段分立（score D 族读段 1/E 族读段 2·CTO 14:01:39 认证）；④ 发现 28 γ 施工终态定谳=δ 分叉消除·首拍 γ 过闸形态生效（cto-gamma-impl-acceptance-20261114）；⑤ SDE 预案分支 A 定谳=payload 零 PATCH·托转二可能全程零触发·**首拍 23:50 硬锚不动**（7dced229f）；⑥ STE 主审 CONDITIONAL_PASS+CTO 确认链闭环（179/176=口径差双真非笔误·57901674c）；⑦ 首拍预期态判读表 v2（engine_absent=缺件异常·9e310f5f0）；⑧ 双通知机理（ADE 面+FADE 段 10 并存≠重复投递）。

| 段 | 段名 | 现势 |
|---|---|---|
| 一 | 触发执行 | **已填充**（cron 七层全链+11-08 活体实锚+F1-F6 全档·**现役形态=十阶段形 payload·vB 七层叙事为历史基线见下方现势注记**） |
| 二 | Agent qualify | **已填充**（2026-11-14·preflight/qualify 两 CLI 实装现役形） |
| 三 | plan skill | **已填充**（2026-11-14·plan_scope 405 行三分类+双向断言） |
| 四 | DCE | **已填充**（2026-11-14·dce_steps 四步段序+dry-run/--execute 两层窗） |
| 五 | verify cli | **已填充**（2026-11-14·**γ 终态形**：旧周 trees/ 目录存在性判据·δ 分叉已消除） |
| 六 | score cli | **已填充**（2026-11-14·**引擎实弹态**：v2 判读族·run_state ok≠评分 pass） |
| 七 | score skill | **已填充**（2026-11-14·score_rubric 结构门+红灯 cap+F2 免评分母） |
| 八 | close skill | **已填充**（2026-11-14·漏报护栏+升级条目五字段） |
| 九 | close cli | **已填充**（2026-11-14·终态三态 ok/failed/stale） |
| 十 | 结论与动作 | **已填充**（2026-11-14·双向 notify+双通知机理） |

---

## 第一段 · 触发执行

> **现役形态注记（2026-11-14 重更新批·读本段前先看）**：下文七层链叙事基于 vB 形基线（写作时现役）；**现役=十阶段形 payload（2026-11-13 22:12 换锚在役·cmd_len=2750/md5=4e1c7df5·判据锚卷 e672f3f50）**——骨架段（trap/RUN_ID 头/段 1 preflight/manifest 主行/段 2 qualify）保留 vB 基座原形，段 3-10 八 CLI 编排（&& 链 fail-closed·段 6 二值容忍 rc∈{0,2}·RUN_DIR/RUN_ID 贯穿+arrival touch·notify_done 真形态）。L1-L5 通用闹钟引擎层语义不变；L6-L7 业务本体升为十阶段链（本稿段 2-10）。两形态并存现势：vB 形=复原判定面专用（托转一换回）；托转一/二=事件驱动（预告重排窗口语义版 a8fd88e81·预演窗今晚 00:00 后候 CEO 锁定·首拍 23:50 硬锚不动）。**两分禁互判**（STE 定谳）：禁以 vB 判据判十阶段形·禁以十阶段新形判复原态。
> 第一段 F1-F6 发现族的改造落点现势：F4 主解=preflight 上移（已实装为段 1 CLI）；F1/F6 合并=告警闸挂 job 级（TriRMC 告警闸模块已施工·本机检出顶 e408da5）；F2 arrival-missing 三分支已施工（fd866ca）。

### 先看大图：这条链到底干什么

一句话：**每周日晚上 23:50，有一台机器自动把公司的「周报柜」从上一周翻到新一周**——旧周目录归档、新周目录建好、没办完的事搬到新周、该提醒的提醒出去。全程无人值守，靠的就是这条七层链。

这个「周报柜」= `docs/workflow/operating-records/` 目录（每周一个文件夹，2026-W45 这样命名）。

七层分两段看更清楚：

- **L1-L5 = 通用闹钟引擎**（跟周报无关，任何定时任务都走这五层）：到点判定 → 执行循环 → 崩溃恢复 → 算出这次该用什么参数 → 拉起进程跑命令。
- **L6-L7 = 周迁移业务本体**：跑的那条命令先做 git 同步（L6 四段），再调 Python 迁移器完成六步搬家（L7）。

**为什么 CEO 要懂这条链**：11-08 那轮它 15 秒就死了，死完没有任何人任何闸知道，公司迁移悬空了 18 小时靠人巡检兜底——这条链的可靠性问题全部藏在层与层的缝隙里，读完七层就能精确指出每一处「谁在看住它」。

---

### L1 · 调度判定——「闹钟每秒看一次表」

**这段干什么**：机器上存着一张任务清单（JSON 文件），每条任务写着「什么时间跑什么命令」。周迁移这条任务的表 = cron 表达式 `50 23 * * 0`（每周日 23:50）+ 时区 Asia/Shanghai。调度判定就是不停地对比「现在」和「下次该跑的时间」，到点就算到期。

**代码在哪**：
- cron 表达式解析：`TriCompany/packages/agent-core/src/scheduler/cron-engine.ts`
- 任务清单存哪：`TriCompany/packages/agent-core/src/scheduler/job-store.ts` L32-39——store 路径 = `$TRIMC_CONFIG_DIR/cron/jobs.json`，没设环境变量就落当前目录 `./data/cron/jobs.json`（这个「没设就落当前目录」是 F5 事故的伏笔，见后文）。

**想深挖怎么亲手查**（PowerShell，本机直接跑）：

```powershell
# 看 store 路径解析逻辑（env 键 TRIMC_CONFIG_DIR + 兜底 ./data）
Get-Content D:\Code\ai\TriCompany\packages\agent-core\src\scheduler\job-store.ts | Select-Object -Skip 27 -First 15
```

**CEO 可能想问的点**：
- 为什么「每秒看一次表」而不是精确定时到 23:50:00 醒一次？（答案在 L2：引擎是通用循环，每秒一拍是简单可靠的代价）
- 任务清单就是个 JSON 文件，写坏了/删了怎么办？（现在没有备份闸——这是一处可以追问的缝隙）
- cron 表达式 `50 23 * * 0` 是谁写进去的、什么时候写的？（河源 TriRMC 的 jobs.json，job 编号 9c81c7ec，10-18 CEO 令改的时点形）

---

### L2 · 执行循环——「秒针走路的人」

**这段干什么**：一个永不停止的循环：找出最快到期的任务 → 算出还有多久 → 睡到那时候 → 起来执行 → 睡回继续找。睡眠间隔默认 1000 毫秒（`DEFAULT_TICK_MS = 1_000`），这就是 L1「每秒看一次表」的实现处。

**代码在哪**：`TriCompany/packages/agent-core/src/scheduler/job-executor.ts` L37（TICK 常量）+ L157-160（scheduleNext 循环体）。

**想深挖怎么亲手查**：

```powershell
# 看 TICK 常量与循环体
Get-Content D:\Code\ai\TriCompany\packages\agent-core\src\scheduler\job-executor.ts | Select-Object -Skip 34 -First 8
Get-Content D:\Code\ai\TriCompany\packages\agent-core\src\scheduler\job-executor.ts | Select-Object -Skip 154 -First 12
```

**CEO 可能想问的点**：
- 这个循环是活在一个什么进程里？（河源 TriRMC daemon——进程死了循环就没了，所以 L3 有崩溃恢复）
- 如果到点那一刻机器正好在忙别的，会延迟多少？（setTimeout 的精度问题——最多延迟一拍 1 秒，对周迁移够用）
- 「任务正在跑中」怎么表示？（job 记录里的 `runningAtMs` 时间戳——L3 的恢复逻辑就盯它）

---

### L3 · 服务适配——「值班的保安：处理上次没醒来的和病得不轻的」

**这段干什么**：两件守护事。
1. **stale-run 恢复**：daemon 启动时，发现某任务挂着 `runningAtMs ≠ null`（上次进程死时它「正在跑」）——把它复位，否则这个任务会永远卡在「运行中」再也不会被调度。
2. **degraded 聚合**：所有任务里取最大的连续失败次数（consecutiveFailures），达到阈值 3 就把整个服务标记为「降级」。**注意方向**：这是「连续失败 3 次才亮红灯」——11-08 轮只失败 1 次，红灯没亮（这是 F6 的关键机理）。

**代码在哪**：TriRMC 适配层 `TriRMC/src/cron/service.ts` L1-20（文件头注释就是这两件事的设计说明——**读代码先读文件头注释，这文件的注释是教科书级的**）。

**想深挖怎么亲手查**：

```powershell
Get-Content D:\Code\ai\TriRMC\src\cron\service.ts | Select-Object -First 20
```

**CEO 可能想问的点**：
- 怎么区分「进程崩了留下的假运行中」和「真在跑」？（区分不了就全复位——风险是把真在跑的标记搞乱，所以启动窗口要避开任务执行窗）
- 阈值 3 是不是太高了？周任务连续失败 3 次 = 连续三周翻周失败 = 悬空三周？（对高频任务 3 合理，对**周**任务等于纵容三周——11-08 轮实锤，这就是 F6 要改的）
- degraded 之后会发生什么？（标记+上层可见，但**不会自动补跑**——见 L7 之后的失败案例）

---

### L4 · 周算术——「把『每周日』翻译成具体日期」

**这段干什么**：任务命令里写着占位符 `{fromWeek}/{toWeek}/{startDate}`。触发时引擎算出三个真值：
- `toWeek` = **明天**所在的 ISO 周（周日 23:50 跑时「明天」=周一，所以 toWeek=新周，比如 2026-W46）
- `startDate` = 下个周一（新周第一天，2026-11-09）
- `fromWeek` = toWeek − 1（旧周，2026-W45）

**代码在哪**：`TriRMC/src/cron/command-handler.ts` L70-75（占位符替换）+ `TriRMC/src/cron/week-math.ts` L58-75（周算术本体——注意它还处理了跨年周：`fromWeek < 1` 时取去年的最后一周）。

**想深挖怎么亲手查**：

```powershell
Get-Content D:\Code\ai\TriRMC\src\cron\week-math.ts | Select-Object -Skip 54 -First 26
Get-Content D:\Code\ai\TriRMC\src\cron\command-handler.ts | Select-Object -Skip 69 -First 8
```

**CEO 可能想问的点**：
- 为什么用「明天」而不是「今天」算 toWeek？（因为触发点在周日深夜 23:50，23:50 之后到午夜前「今天」还是周日——用明天=周一所在周，语义才稳定。这是时点设计的精细处）
- ISO 周是什么？跟自然周有什么差别？（ISO 8601 标准：周一为一周第一天，含 1 月 4 日的那周是第 1 周——跨年时 ISO 周号会「倒回」，week-math 的 `isoWeekOfLastWeekOfYear` 就是处理这个）
- 时区在哪定的？（week-math 注释明说全部按服务器本地时区 Asia/Shanghai 算——如果服务器时区变了这里会全错，这是一处隐性依赖）

---

### L5 · 进程执行——「真正挽起袖子干活的人」

**这段干什么**：把替换好参数的命令交给操作系统：`/bin/bash -e -c <command>`。三个关键设定：
- **detached 进程组**：bash、python3、git 算一家人（同一个进程组），超时杀的时候全家一起死，不留孤儿。
- **超时 10 分钟**（`DEFAULT_JOB_TIMEOUT_MS`）。
- **每跑一次留一份独立日志**（per-run log），文件名带任务编号+时间戳——这是事后查案的第一现场。

**代码在哪**：`TriRMC/src/cron/command-handler.ts` L77-107。

**想深挖怎么亲手查**：

```powershell
Get-Content D:\Code\ai\TriRMC\src\cron\command-handler.ts | Select-Object -Skip 76 -First 32
```

**CEO 可能想问的点**：
- 为什么用 `-e`？（bash 的 -e = 命令一失败立即退出——11-08 轮 15 秒死就是它干的：第一步 git pull 失败，bash 直接退出，后面五步全没跑）
- 10 分钟超时对这任务够吗？（正常轮迁移器跑几十秒~几分钟；但超时只管「跑太久」，管不了「跑太快就死」——15 秒死不触发超时，触发的是 bash -e）
- per-run log 存在哪？（`/var/lib/trirmc/cron/logs/`——**注意**：跟 F5 的 store 分家了，见 F5）

---

### L6 · 迁移链四段——「干活的命令本身：先同步，再搬家，再交作业」

**这段干什么**：L5 起的 bash 跑的就是这条命令（河源 TriRMC jobs.json 里 job 9c81c7ec 的 payload.command），分四段：

| 段 | 干什么 | 出过什么事 |
|---|---|---|
| ① 前置同步 | `git pull --ff-only sg-bare dev`——把 sg 裸仓的最新内容快进拉下来 | **11-08 轮 15 秒死在这**（diverging 分叉，code 128） |
| ② 迁移器 | `python3 -m runtime.cognition.weekly_plane_shift --from … --to … --start-date … --sync` | 六步搬家本体（见 L7） |
| ③ 落 commit | `git add + commit`（署名 TriRMC-Scheduler——机器身份，人一眼认出这是自动提交） | 正常 |
| ④ 推回 sg 裸仓 | `git push sg-bare HEAD:dev`，失败则 `fetch+merge+push` 重试 | 正常（注意：**④有自愈重试，①没有**——F4） |

**代码在哪**：命令正身存河源 `/srv/fleet/TriRMC/data/cron/jobs.json` 的 payload.command（河源面读数见材料正身实锚，本稿不另探）。

**想深挖怎么亲手查**：本机可看等价物——dev 机 TriRMC 工作区若同构，`Get-Content D:\Code\ai\TriRMC\data\cron\jobs.json`（**注意**：这是 dev 机副本，河源现役正身以材料正身 §三实锚为准；F5 讲了这文件的实际落点与直觉不符）。

**CEO 可能想问的点**：
- `--ff-only` 是什么？为什么必须快进？（快进=本地没有自己的提交、只接受「直着往前拉」；一旦本地有分叉提交就拒绝——它选了「宁可死也不乱合」，11-08 轮正是这样死的）
- 为什么会 diverging？（sg-bare/dev 和河源工作树各有新提交=两条腿走路了——co-tenancy 竞速，8712 oprec-sync 同族机理，材料正身 F4 已判）
- ①段死了为什么不重试？④段都有重试为什么①没有？（**设计不对称，F4 全文**——④当年加了自愈，①裸奔，11-08 轮用 15 秒证明了代价）

---

### L7 · 迁移器六步——「搬家公司的标准作业流程」

**这段干什么**：`weekly_plane_shift.py` 的 main 函数（L216 起）按固定顺序跑六步，任何一步 fail 则整体 fail：

| 步 | 干什么 | 大白话 |
|---|---|---|
| 1 create | 建新周目录（幂等：目录已存在不算失败） | 「新柜子先摆好，摆过了就跳过」 |
| 2 migrate | 旧周目录内容迁入新周（内含 retire） | 「旧柜子的东西搬进新柜子，该退休的退休」 |
| 3 carry_over | unresolved（未办完事项）§1 平移到新周，周计数+1，4 周/8 周未办的自动升级标记 | 「没办完的事抄到新周的本子上，拖了 4 周 8 周的自动标红」 |
| 4 validate | 校验新周 index 的 active 面合格 | 「搬完点货，别搬丢」 |
| 5 agent_close/review_shift | 复核迁移结果+提取 8 周升级清单 | 「主管复查一遍+把拖最久的单子挑出来」 |
| 6 聚合+通知 | 全部结果写 `.shift-ade.json`（体检报告）；notify 发出（SMTP 邮件+TriLC 8711 POST） | 「写体检报告+给相关人员群发通知」 |

**代码在哪**：`TriCompany/runtime/cognition/weekly_plane_shift.py` L216-285（main 全序，328 行文件的核心段）。

**想深挖怎么亲手查**：

```powershell
Get-Content D:\Code\ai\TriCompany\runtime\cognition\weekly_plane_shift.py | Select-Object -Skip 215 -First 75
```

**CEO 可能想问的点**：
- 「幂等」是什么意思？为什么 create 要幂等？（同一件事跑两遍结果不变——重跑/补跑不会造成双份目录。11-09 的人工补跑全靠这个特性才安全）
- carry_over 的 4w/8w 升级是什么制度？（未办事项拖 4 周升级一次、拖 8 周再升级一次——自动把「拖久了的事」推到更醒目的位置。这是公司挂账制度的机械化执行）
- notify 发给谁、谁消费？（SMTP 邮件+TriLC 8711 POST——注意既有教训「信到箱≠信到人」：通知发了不等于有人处理，所以 W46 悬空还是靠 patrol 人工发现的）
- `--sync` 不加会怎样？（dry-run 彩排模式：全流程空跑不落盘——试新改动先彩排，这是迁移器的安全带）

---

### 活体实锚：11-08 轮的完整死亡时间线（失败案例是最好的教材）

以下读数全部引自 2026-11-10 20:1x 河源直探 jobs.json state（调度面 LastRun 真值，材料正身 §三在档）：

| 时点 | 发生了什么 | 七层对应 |
|---|---|---|
| 11-08 23:50+08 | job 9c81c7ec 准点触发（runCount=11 证明调度面活着） | L1-L4 全部正常 |
| 23:50 + 15 秒 | ①段 `git pull --ff-only` 死：code 128 diverging（sg-bare/dev `0cc423283..ac1e2380e` 分叉）·bash -e 即刻退出 | **L6 ①段死亡点** |
| 死后数秒 | consecutiveErrors=1——**小于阈值 3，degraded 不亮**；无告警外发；无自动补跑；nextRun 照排 11-15 | L3 的盲区+**F6 全文** |
| 11-08 23:50 → 11-09 17:24 | **迁移悬空整 18 小时**——没有任何闸发现，靠值席 patrol 人工兜底 | 全链无监测（F1 判据扩形的实证） |
| 11-09 17:24+08 | 人工应急补跑成功：W46 `.shift-ade.json`（pass·六步全绿）check_time=11-09 17:24——**这是 runbook §5 兜底路径的产物（迁移 commit 6860bf87b），不是 cron 轮产物** | L6 ②-④+L7 全六步（人工代跑） |
| 11-09 晚 | 首评分卷评的正是这个应急态（13.8%·T1 N/A 应急链承接） | 考卷面 |

**这条时间线的三层教训**：
1. **调度面活≠执行面活**——job 准点触发（runCount+1）不等于业务成功（15 秒就死了）。判活性必双面，这是家族纪律。
2. **失败检测靠人不靠闸**——错误发生了 18 小时，系统里没有一个环节主动喊人。F1（漏拍无监测）+F6（败跑无监测）合起来=触发段是全链第一张多米诺，且倒下时无声。
3. **兜底路径救了场但救不了制度**——runbook §5 人工补跑有效的前提是「有人恰好巡检到了」，把制度可靠性押在人的自觉上，就是 F 系全部改造候选要解决的问题。

---

### F1-F6 发现全档（候改造批的完整问题清单）

| # | 发现 | 一句话机理 | 候选改造方向 |
|---|---|---|---|
| F1 | 触发漏跑无监测 | job 漏拍/死亡没有任何闸会发现——第一张多米诺倒下无声 | 触发后 N 分钟无 per-run 成功日志即告警（挂候批件②P1） |
| F2 | 到岗窗无断言 | 考卷 T1 只判 cron 触发不判「agent 30 分钟到岗」——设计存在但无检查项 | T1 判据扩为「触发+到岗」双断言 |
| F3 | 免评分母规则缺 | T1 N/A 时权重 20 仍计入分母（145 的第三层口径疑点） | scoreable 规则补分母处理定义 |
| F4 | ①段 pull 无 fallback | ④段 push 有自愈重试而①段裸奔——diverging 无自愈路径，11-08 轮 15 秒死实证 | ①段补自愈（fetch+merge/重试退避）或改幂等 pull 形 |
| F5 | store 路径双形分裂 | agent-core 读 env 键 TRIMC_CONFIG_DIR，TriRMC 注入的是 TRIRMC_CONFIG_DIR——键错位致 store 落仓内 `./data/cron/jobs.json` 而 logs 落 `/var/lib/trirmc/cron/logs`，**store 与 logs 分家两目录** | env 键对齐或 store 路径显式配置化 |
| F6 | 失败轮无闸（并入 F1 判据） | consecutiveErrors=1<3 不 degraded——无告警无补跑 nextRun 照排，悬空 18 小时靠 patrol 兜底 | F1 判据扩形定谳：「漏拍**或败跑** N 分钟无 per-run 成功日志即告警」 |

**下轮现势风险注**（引自材料正身）：nextRun=11-15 23:50——若 sg-bare/dev 与河源工作树再现 diverging，①段将再挂（F4 未修前）。

---

## 第二段 · Agent qualify

> **现势（2026-11-14 重更新批）**：本段+段 1 preflight 已实装为独立 CLI（`runtime/cognition/preflight.py`/`qualify.py`·十阶段形 payload 基座段保留原形）——CTO 认证：score 考卷 D 族读段 1 preflight 产物、E 族读段 2 qualify 产物，**两段分立各管一断言族**（14:01:39 认证实锚）。

- **大白话干什么**：正式干活前先查"今天该不该跑、跑的环境有没有资格"。段 1 查业务面（今天是不是周日、参数齐不齐）；段 2 查载体面（git 仓库干不干净、daemon 活不活、有没有人在同时动文件）。
- **代码在哪**：`TriCompany/runtime/cognition/preflight.py`+`qualify.py`（含 `test_preflight.py`/`test_qualify.py`）；payload 编排位=十阶段形 command 串基座段（FSD 供形件卷 `cto-fsd-payload-supply-20261113.md` §三——preflight/qualify 两 CLI 分立·`|| RC` 形各自落 manifest 退出码）。
- **亲手查**：`cd TriCompany && python -m pytest runtime/cognition/test_preflight.py runtime/cognition/test_qualify.py -v`。
- **CEO 可能想问的点**：为什么拆两段不合一？——分立=断言族分立（D 族/E 族各读各的产物），一段挂了判读表能精确指认哪一族资格缺失；合一段则 preflight 失败与 qualify 失败混在一张卷里。

## 第三段 · plan skill

- **大白话干什么**：判"迁什么、不迁什么"。把上周目录里每棵树分成三类：**migrate**（在途的活，随人带走去新周）、**keep**（办完的记录，原地封存）、**carry_over**（没办完的事项行，抄进新周待办）。语义锚（CPO 定谳）：**"这是一周的记录，还是这一周的活——记录随周封存·活随人带走"**。
- **代码在哪**：`TriCompany/runtime/cognition/plan_scope.py`（405 行）。核心三件：三分类判据（classify_dir，degrade 链=tree-op status→authorization expiry→默认 keep——**"漏迁毒于误封存"**取保守在途）、双向枚举断言（bidirectional_check：migrate+keep 覆盖全集零遗漏零重叠+**清单外幽灵条目也拦**）、替身禁令（目录缺/坏=FAIL-EXPECTED 禁造空清单——空 keep 全集会让断言假绿）。
- **亲手查**：`python -m pytest runtime/cognition/test_plan_scope.py -v`；预演读数样本=G2 实弹 r2 pass migrate=2/keep=26/carry_over=2。
- **CEO 可能想问的点**：为什么默认 keep 而不是默认迁？——保守方向：误封存还能人工捞回（verify 对表+carry 面兜底），误迁移会把办完的事搅进新周。另注意 OP index 与实盘脱节是常态（W46 实锚 index activeTrees=0 vs 实盘 20+）——index 只是旁证不是基准。

## 第四段 · DCE

- **大白话干什么**：迁移本体确定性执行——按步骤表拉代码、跑迁移器、精确提交、走专用通道推走。**默认 dry-run 只渲染命令不执行（零生产触）**；`--execute` 是部署窗授权面保留位。
- **代码在哪**：`TriCompany/runtime/cognition/dce_steps.py`（242 行）。四步段序=pull（`--ff-only` 拒分叉）→migrate（真身=`python3 -m runtime.cognition.weekly_plane_shift`·**全名消歧：weekly_plane_shift.py=CLI 入口≠weekly_plane.py=库函数面**）→commit（**精确 pathspec `docs/workflow/operating-records` 禁 -A 全仓**+zero-diff 防线+识别式消息 `ops: weekly plane shift W<X>->W<Y> run=$RUN_ID`）→push（sg-bare 通道+断线 fetch/merge 重试，降级如实注）。rc_guard=True 步失败即拦停段（后续零执行）；push 步 rc_guard=False（断通道降级不拦·如实落卷）。
- **亲手查**：`python -m pytest runtime/cognition/test_dce_steps.py -v`（dry-run 渲染面+rc_guard 拦停案）。
- **CEO 可能想问的点**：dry-run 面验的是什么？——只验命令渲染，**不验参数真跑**。实锚教训：G3 骨架形曾给迁移器传 `--plan-file`，argparse 不认，`--execute` 必报错拦停——dry-run 没暴露（渲染面不查参数合法性），靠部署窗实走抓出后勘正。所以"预演全绿"≠"生产参数对"，两层窗是裁决 A 定谳的主线。

## 第五段 · verify cli

> **现势勘正（γ 终态定谳·2026-11-14 CTO 验收 PASS·δ 分叉消除）**：D 断言判据面已勘修——**旧周 trees/ 目录存在性**（原地封存语义·weekly_plane.py L282-293 白盒实锚）替代旧"to 周 OP index 两落点并集对表"（首拍空壳 index 必炸·迁移执行域与对表面解耦）。首拍/预演段 5 `--strict` **过闸形态生效**。

- **大白话干什么**：迁完验迁对。四道断言：A=拿到的迁移计划本身没被毒化（轻量复验）；B=周算术 γ 归位（新周号与起始日数学自洽·二道闸）；C=新周 index 结构面在（可得+可解析+键在）；D=对表（plan 里说要迁的条目 vs 实盘旧周 trees/ 目录存在性·逐项 landed/missing 读数，缺=exit 2 fail-closed）。
- **代码在哪**：`TriCompany/runtime/cognition/verify.py`（276 行）。`--strict` 预演形默认 off（迁移器未真跑时对表必炸）——留首拍/预演实走路径。
- **亲手查**：`python -m pytest runtime/cognition/test_verify.py -v`（含 γ 首拍不炸机理直证案=b350f9c 增补五案）。
- **CEO 可能想问的点**：为什么对表面不直接用 index？——历史演进面：迁移器只搬 index 层 doneTreesThisWeek（activeTrees 清空不搬家·文件树零触碰），旧判据在首拍实迁=0 时全 missing 必炸（发现 28）；γ 勘修后对表面=旧周 trees/ 目录存在性，与迁移执行域解耦——**历史 γ/δ 分叉叙事按定谳后终态理解，首拍即 γ 过闸形**。

## 第六段 · score cli

> **现势（v2 判读族全 governs·引擎实弹装配毕 2026-11-14 12:25 生效锚）**：score_engine 已实弹——**executed_ok=逐族评分读数（families 明细+score+verdict）是正常形；run_state ok ≠ 评分 pass（verdict 在 score.json 卷面独立判读）；engine_absent 装配毕不应出现·出现=缺件异常即报（J7 语义收窄为缺件态专用）**。探针正形=`python3 -m runtime.cognition.score_cli`（**TC 仓根 cwd**）——直跑 script 形会误报 engine_absent（sys.path 缺仓根）·值守窗照 -m 形。

- **大白话干什么**：跑完问"有没有分"。三态路径分立：executed_ok（引擎实跑成功→score.json 载读数）/executed_failed（引擎在但跑炸/返回不像话→非阻塞告警 COS 单址）/engine_absent（引擎缺件→J7 升级即报）。缺席≠跑败——升级路由看 engine_state 分立，防"部署缺件"被误判成"引擎坏了"。
- **代码在哪**：`TriCompany/runtime/cognition/score_cli.py`（117 行）+`score_engine.py`（实弹引擎·STE 主审 CONDITIONAL_PASS+CTO 确认链闭环）。
- **亲手查**：`python -m pytest runtime/cognition/test_score_cli.py runtime/cognition/test_score_engine.py -v`；门禁读数=TC cognition 全目录 184 passed（smoke 口径·CTO γ 验收独立重跑）。
- **CEO 可能想问的点**：引擎降级族判定是什么？——executed_ok 内部，缺件→族 fail/manual 入 reasons（哑卷≠引擎坏=设计行为·不外抛）；预演拍时段窗族红=读数保真非缺陷（预演时点非 23:50 窗使然·门不豁免——读卷如实）。

## 第七段 · score skill

- **大白话干什么**：考卷的结构承载与判分规则落地。**考卷侧零改动遵行**（八族内容不复制进代码——复制=卷面漂移风险）；红灯定性上限（族 C 红=79·族 G 红=59）**红灯不因其他族高分洗白**；F2 免评分母（零触发+标记正常=满分·不因无告警扣分）。
- **代码在哪**：`TriCompany/runtime/cognition/score_rubric.py`（192 行）。结构门=八列字段族+族号 A-H 机械键唯一+权重合计=100 断言；T1 三断言候选注记=落位≠改卷生效（CPO 裁③钉子）。
- **亲手查**：`python -m pytest runtime/cognition/test_score_rubric.py -v`。
- **CEO 可能想问的点**：C cap 79 现在触得发吗？——现权重数学下 C 红 total 天花板=76.9<79（"死保险丝"·N2 采认注记）——cap 语义=考卷权重改版后实活的护栏位，零改码保留正形。G cap 59 真权重有效。

## 第八段 · close skill

- **大白话干什么**：收口时自动复盘——扫五件段产物提取升级条目。**漏报护栏**：close.json 必载 `upgrade_list_state` 显式二值（extracted=提取实跑过·含空清单合法态/not_extracted=骨架未提取）——缺键=结构门拦。**"静默缺省=最毒漏报形"：收口面看着干净实则没跑。**
- **代码在哪**：`TriCompany/runtime/cognition/close_skill.py`（171 行）。升级条目五字段 spec：run_id/stage+trigger（枚举）/routing（候 COS|候 CEO·保守默认候 COS）/evidence（run id+段产物路径·禁零锚升级条目）/state（open|routed）。**防蠕变划线：清单=提取与承载不做裁决（裁=COS 域）——零自动降级零自动销项。**
- **亲手查**：`python -m pytest runtime/cognition/test_close_skill.py -v`。
- **CEO 可能想问的点**：close rc=0 是不是"没问题"？——不是。**结构门绿≠零升级**：升级清单非空是合法态（如实提取如实列），漏报（没跑提取/缺 state 键）才是毒。

## 第九段 · close cli

- **大白话干什么**：给每个 run 发"死亡证明"或"健康证明"——终态三态字段落 manifest。ok=六段产物全在且 verdict 全 pass；failed=全在但有 fail（**死有名字**——哪段死查各段卷）；stale=缺件或不可读（悬空 run）。
- **代码在哪**：`TriCompany/runtime/cognition/close_cli.py`（99 行）。判据顺序：**absent/unreadable 优先于 fail**——六段产物齐才得 ok/failed 真值；manifest=终点记录非闸（不拦链不告警——告警面在段 10）。
- **亲手查**：`python -m pytest runtime/cognition/test_close_cli.py -v`。
- **CEO 可能想问的点**：缺件 run 算 failed 吗？——不算，算 stale。failed 需要"全在+有 fail"；缺件连判 fail 的证据链都不齐，只能定性 stale（如实告知悬空）。

## 第十段 · 结论与动作

- **大白话干什么**：把结论送到人面前——成功/失败双向通知路由。ok→结论通知；failed→失败告警（**文案必带 run id**·可回溯到 run dir）；stale→悬空 run 报告；未知态→如实降级 unknown 面。
- **代码在哪**：`TriCompany/runtime/cognition/notify_done.py`（117 行）。best-effort 契约：复用 P1 notify 面永不抛+兜底 except——**notify 本身永不拦**（run 失败看 manifest.run_state 不看 notify）；`--dry-run-only`=render_only 零发送（演练面）。
- **双通知机理（现役定谳·发现 25/13）**：ADE 面 `_notify_shift`（`.shift-ade.json` 双址 blocking·迁移器产物）+FADE 段 10 `notify_done` 并存——**两通知到达≠重复投递事故**，两层面各自通知面，首拍并存=预期态。
- **亲手查**：`python -m pytest runtime/cognition/test_notify_done.py -v`。
- **CEO 可能想问的点**：通知失败会拦住链吗？——不会（best-effort）。另：演练时忘传 `--dry-run-only` 会真发信——演练命令必须带。

---

## 真源索引（本稿不替代真源，冲突回以下正身）

| 面 | 正身 |
|---|---|
| 材料正身（七层表/活体实锚/F4-F6/F1-F3） | `TriMetaverse/docs/execution/fade-001-improvement-20261110.md` §三 |
| L1-L2 引擎层 | `TriCompany/packages/agent-core/src/scheduler/`（cron-engine.ts / job-executor.ts / job-store.ts） |
| L3-L5 适配层 | `TriRMC/src/cron/`（service.ts / command-handler.ts / week-math.ts） |
| L7 迁移器 | `TriCompany/runtime/cognition/weekly_plane_shift.py`（main L216-285） |
| 十阶段段 1/2 CLI | `TriCompany/runtime/cognition/preflight.py` / `qualify.py`（现役·CTO 14:01:39 认证两段分立） |
| 十阶段段 3-10 CLI 族 | `TriCompany/runtime/cognition/plan_scope.py / dce_steps.py / verify.py / score_cli.py / score_rubric.py / close_skill.py / close_cli.py / notify_done.py` + `score_engine.py`（实弹引擎） |
| payload 供形正形 | `TriMetaverse/docs/workflow/operating-records/2026-W46/trees/fade001-tenstage-deploy-20261115/cto-fsd-payload-supply-20261113.md`（§三 编排对表注=十阶段形 command 串结构真源） |
| 现役判据锚（十阶段形五条族） | `.../trees/fade001-phase1-build-20261114/值守预期形-十阶段形判据锚-20261113.md`（e672f3f50 在役·vB 锚 8237d12af 备档） |
| 首拍预期态判读表 v2 | `.../trees/fade001-tenstage-deploy-20261115/cto-firstshot-expected-state-brief-20261114.md`（9e310f5f0·v2 全 governs） |
| γ 终态定谳 | `.../trees/fade001-tenstage-review-20261114/cto-gamma-impl-acceptance-20261114.md`（δ 分叉消除·首拍 γ 过闸形生效） |
| 预案分支 A 定谳 | `.../trees/fade001-tenstage-deploy-20261115/` 预案卷 §十一（7dced229f·payload 零 PATCH·托转二备用） |
| 应急兜底 runbook | `TriMMC/docs/ops/trimc-cron-plane-shift-runbook.md`（§5 兜底路径） |
| 协议正身 | `TriCompany/docs/engineering/fade-protocol-spec.md`（§8.1 十段链+恢复三款） |
| 考卷正身 | `TriCompany/docs/engineering/fade-papers/FADE-001-paper-*.json`（三卷形态分裂=⑥候批项） |

---

## draft 完善待办（三方共读时逐条过）

1. 每层「CEO 可能想问的点」候 CEO 试问一轮，问不到的补、答不清的重写。
2. 查证命令候选 CEO 实跑一轮验证可读性（PowerShell 形为默认，如需 git-bash 形可加注）。
3. F1-F6 改造候选若 CEO 批转，第一段加「改造后现势」对照段（改造前后同表对比——培训件跟代码走）。
4. 转正身条件（建议）：CEO×BOD 共读毕+三方确认口径 → 去 draft 头+转 `syncMode: write-time`+入 `docs/training/README.md` 索引（现索引只有 2026-09-05 旧四版教程族，本文为触发链专稿）。
5. **十段推进同步**（CEO 20:59 令定）：BOD 每完成一段拆解（CEO OK 后）通知 RDT 丰富对应段——第二段起逐段填充，文档跟拆解进度同步，防跑前跑后不一致。
6. **〔2026-11-14 重更新批注〕**：段 2-10 已按现役终态填充（CEO 16:19:08 直令·八锚基准见总览节）——待办 5 的「BOD 拆解逐段通知」形态由此批先行覆盖（代码+判读卷已成真源，拆解叙事可回填校正）；首拍读数落卷后候实弹锚增补（裁决 D 两段式·G2 先行批→首拍增补窗）。

—— RDT 小吴 · 培训草稿落卷 2026-11-10T20:42:20+08:00 / 大纲重组十阶段制 2026-11-10T21:00:07+08:00（两笔落款均 date 现查原值·卷面时戳锚=git commit 时戳）
—— 2026-11-14 重更新批（CEO 16:19:08 直令「按现有整条链状态重新更新完善」·COS 16:20 派工转）：段 2-十段现役终态填充+第一段现役形态注记+总览八锚+真源索引现役卷扩——RDT 小吴·写前现查 2026-11-14T08:24:13Z（+8=16:24·date 现查原值·D-47 正形）
