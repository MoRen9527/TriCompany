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

## 十阶段总览（大纲现势）

| 段 | 段名 | 现势 |
|---|---|---|
| 一 | 触发执行 | **已填充**（cron 七层全链+11-08 活体实锚+F1-F6 全档） |
| 二 | Agent qualify | 骨架（候拆解） |
| 三 | plan skill | 骨架（候拆解） |
| 四 | DCE | 骨架（候拆解） |
| 五 | verify cli | 骨架（候拆解） |
| 六 | score cli | 骨架（候拆解） |
| 七 | score skill | 骨架（候拆解） |
| 八 | close skill | 骨架（候拆解） |
| 九 | close cli | 骨架（候拆解） |
| 十 | 结论与动作 | 骨架（候拆解） |

---

## 第一段 · 触发执行

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

（候 BOD×CEO 拆解推进至本段时填充）

## 第三段 · plan skill

（候 BOD×CEO 拆解推进至本段时填充）

## 第四段 · DCE

（候 BOD×CEO 拆解推进至本段时填充）

## 第五段 · verify cli

（候 BOD×CEO 拆解推进至本段时填充）

## 第六段 · score cli

（候 BOD×CEO 拆解推进至本段时填充）

## 第七段 · score skill

（候 BOD×CEO 拆解推进至本段时填充）

## 第八段 · close skill

（候 BOD×CEO 拆解推进至本段时填充）

## 第九段 · close cli

（候 BOD×CEO 拆解推进至本段时填充）

## 第十段 · 结论与动作

（候 BOD×CEO 拆解推进至本段时填充）

---

## 真源索引（本稿不替代真源，冲突回以下正身）

| 面 | 正身 |
|---|---|
| 材料正身（七层表/活体实锚/F4-F6/F1-F3） | `TriMetaverse/docs/execution/fade-001-improvement-20261110.md` §三 |
| L1-L2 引擎层 | `TriCompany/packages/agent-core/src/scheduler/`（cron-engine.ts / job-executor.ts / job-store.ts） |
| L3-L5 适配层 | `TriRMC/src/cron/`（service.ts / command-handler.ts / week-math.ts） |
| L7 迁移器 | `TriCompany/runtime/cognition/weekly_plane_shift.py`（main L216-285） |
| 应急兜底 runbook | `TriMMC/docs/ops/trimc-cron-plane-shift-runbook.md`（§5 兜底路径） |
| 协议正身 | `TriCompany/docs/engineering/fade-protocol-spec.md` |
| 考卷正身 | `TriCompany/docs/engineering/fade-papers/FADE-001-paper-*.json`（三卷形态分裂=⑥候批项） |

---

## draft 完善待办（三方共读时逐条过）

1. 每层「CEO 可能想问的点」候 CEO 试问一轮，问不到的补、答不清的重写。
2. 查证命令候选 CEO 实跑一轮验证可读性（PowerShell 形为默认，如需 git-bash 形可加注）。
3. F1-F6 改造候选若 CEO 批转，第一段加「改造后现势」对照段（改造前后同表对比——培训件跟代码走）。
4. 转正身条件（建议）：CEO×BOD 共读毕+三方确认口径 → 去 draft 头+转 `syncMode: write-time`+入 `docs/training/README.md` 索引（现索引只有 2026-09-05 旧四版教程族，本文为触发链专稿）。
5. **十段推进同步**（CEO 20:59 令定）：BOD 每完成一段拆解（CEO OK 后）通知 RDT 丰富对应段——第二段起逐段填充，文档跟拆解进度同步，防跑前跑后不一致。

—— RDT 小吴 · 培训草稿落卷 2026-11-10T20:42:20+08:00 / 大纲重组十阶段制 2026-11-10T21:00:07+08:00（两笔落款均 date 现查原值·卷面时戳锚=git commit 时戳）
