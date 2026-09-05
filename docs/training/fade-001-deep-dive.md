# FADE-001 周平面（迁移 + 每日进度维护）深度教程

> 性质声明：本篇是培训教程，不是事实裁决。教程中每一个 hash、行号、分数、时间都从仓库真源实读核验；当你发现本文与真源冲突，以真源为准，并把差异报回培训真源。
> 授课：小吴（RAndDTrainer）。事实基线：2026-08-28（W35 周平面）。
> **版本差注记（2026-09-05）**：本文拓扑叙事为 08-28 基线（TriMC/sg 承载、现役 `59 23 * * 0`）——已被四处现势超越：①迁移触发=**每周日 23:00 北京时间，河源 TriRMC job 9c81c7ec**（2026-08-30 提前+迁移，runbook 时点修正注记）②兜底 watcher=sg daily-progress-watcher **槽位 5,15,25,35,45,55**（2026-08-31 同秒竞态消除）③2026-09-05 晨检三案（分叉 union 归账/参照系误判/旗标体例）本文未载④patrol 现行 951 行。现行版四版教程见 [fade-001/](fade-001/README.md)，本文保留为历史档。

**本文引用文件与缩写对照**（均为绝对路径，正文用短名+行号）：

- `registry` = D:/Code/ai/TriCompany/docs/engineering/fade-registry.md
- `paper-①` = D:/Code/ai/TriCompany/docs/engineering/fade-papers/FADE-001-paper.json（迁移域原卷）
- `paper-②` = D:/Code/ai/TriCompany/docs/engineering/fade-papers/FADE-001-paper-maintenance.json（扩维冻结卷）
- `patrol` = D:/Code/ai/TriCompany/runtime/cognition/daily_progress_patrol.py
- `runbook` = D:/Code/ai/TriMC/docs/ops/trimc-cron-plane-shift-runbook.md
- `progress` = D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W35/daily-progress.md
- `review` = D:/Code/ai/TriMetaverse/docs/execution/fade-001-upgrade-review.md
- `disciplines` = D:/Code/ai/TriCompany/docs/workflow/engineering-disciplines.md
- `spec` = D:/Code/ai/TriCompany/docs/engineering/fade-protocol-spec.md

---

## 〇、培训判断与学习路径

**培训判断**：你是要接手 FADE-001 的研发新人。这个实例特殊在它刚刚完成了一次“扩维”——从一个每周跑一次的迁移脚本，长成了一个“每周迁移 + 每 10 分钟兜底巡检”的双项维护实例，并且评分体系（试卷、shadow 观测、gate 接线）正处于两阶段接线的中间态。接手它需要同时懂三件事：git 拓扑（门限口径）、TriMC cron 运维（节奏载体）、FADE 协议的评分立法（为什么 --score 现在只观测不拦截）。本文按“大结果 → 协议 → 双项十段 → 最小闭环 → 真实证据 → 故障弧线 → 评分卷宗 → 新立法对照 → 接手清单”推进。

**学习路径**（每步都有验证方式，验证不过不要往下走）：

| 步 | 读/做什么 | 验证方式 |
| --- | --- | --- |
| 1 | 读本文第一、二节，建立大图 | 能向同事口头复述“FADE-001 双项结构”与两域档位 |
| 2 | 读 registry 中 FADE-001 条目全文（registry:24-67） | 能指出①②两张十段表的位置 |
| 3 | 通读 patrol 全文（952 行） | 能说出拓扑门限、单写者、recovery push 三件事各在哪些函数 |
| 4 | 本机跑 `--self-test` 和 dry-run（第五节 MVP） | self-test 输出 `"status": "pass"`；dry-run 输出 envelope 且不写盘 |
| 5 | 读 paper-② 全卷 + run_score（patrol:603-668） | 能解读 65/80 部署日卷面（第八节） |
| 6 | 读 runbook §2/§5/§7 | 能背出部署七步里哪三步是权限修复 |
| 7 | 读 spec §2.5/§2.7/§2.8 | 能回答“为什么 push 即终态违反 §2.5” |

---

## 一、先讲大结果：FADE-001 是什么、现在处于什么档位

**一句话**：FADE-001 是 TriCompany 的“周工作平面维护”实例，2026-08-28 由 CEO 提案完成范围扩维——原来只做“周日晚上把上周 operating-records 平移进新周目录”这一件事（维护项①），现在扩为两件事，新增“每日工作进度维护”（维护项②）：在 `docs/workflow/operating-records/<ISO 周>/daily-progress.md` 里维护一个仓库级的粗粒度日进度文件，随 git 推三端（本地/sg-bare/GitHub），作为“机器全灭时的最后恢复防线”（registry:26；progress:4）。

**为什么要有②**：扩维前，最坏情况下一次工作进度的丢失窗口是 23 小时（旧日总结节奏）；②上线后是 10 分钟。重建验收场景写在 registry:60——“sg+本机+中枢三点全灭后，仅凭 GitHub 上的 daily-progress.md 可重建至最后 10 分钟”。

**当前档位（必须如实复述，这是新人最容易说错的点）**：

- 维护项①（迁移域）：完整档，首评 **PASS 90/100**（2026-08-20，必选 6/6），**冻结不重评**（registry:62；review:34）。
- 维护项②（维护域）：**扩评中**——十段已齐，Score CLI（patrol `--score`）已落地处于 shadow 首评期，Score Skill 纸面如实（registry:54,63）。
- 整体档位判定 = **两域双门槛各自 PASS 的合取**（paper-②:85-88，CPO 域级分卷采纳）；不以①完整宣称整体完整（registry:63）。

**节奏一句话**：② 的运行节奏是“事件驱动主 + 10 分钟兜底”——董事长助理在销账/交付/裁决后随手 append+push（主叙事，语义质量高）；TriMC cron 每 10 分钟跑一次确定性巡检脚本 patrol，发现进度文件落后就补写（registry:47）。两者遵守单写者原则，互不重写对方内容。

---

## 二、协议方法层：十段框架与本文要用的协议条款

FADE 协议的生命周期十段是：事件触发 → 登记（运行标识）→ Qualify → Plan Skill → DCE → Verify(可选) → Score CLI → Score Skill → Close Skill → Close CLI → 终态（spec:63-77 生命周期图；spec:95 完整实例定义）。三条对本文最要紧的协议条款：

1. **双门槛**（spec:183）：及格 = 必选项全部通过（Score CLI 确定性判定）且总分达标；不达线进 RETRY/ESCALATED，不得写入终态。
2. **§2.5 终态门**（spec:168-174）：Close Skill 先出语义裁决，Close CLI 校验后才写终态；“位于 Close Skill 之前的 CLI 只能称为 DCE、Verify CLI、Score CLI 或 evidence finalizer，不能提交不可逆终态”（spec:173）。
3. **§2.8 段-实现绑定**（spec:225-266）：立法原则一句话——“协议管不变量，实例管载体”（spec:227）。登记段的四不变量是唯一性/去重性/关联性/恢复锚（spec:241）；实例入册声明“段-实现映射表”，最小 schema 三字段（spec:258）。

两个 profile（spec §八）里，FADE-001 两个维护项都属 **runtime-owned durable**（spec:412-430）：cron/watcher 触发、runtime 持有生命周期。①的触发器是 cron，②的兜底腿也是 cron——这正是 §7.3 表格里“watcher、Git hook、cron、CI 触发 → 不足以由 standalone Skill 持有生命周期 → 应使用 runtime-owned profile”的标准案例。

---

## 三、维护项①（周平面迁移）：十段逐段落地形态

①的工件表在 registry:28-36，规范文件是 runbook（registry:38 指定）。逐段讲：

**1. 事件触发**：TriMC cron。注意一个**新人必踩的坑**：registry:30 写的是 `0 23 * * 0`（周日 23:00 Asia/Singapore），这是历史叙事口径；runbook:18 给出现役真值 `59 23 * * 0`、timezone `Asia/Shanghai`（周日 23:59 北京时间），runbook:165 明确解释了这个已知漂移——CLI 预设 `0 23` vs 现役 job 2026-08-16 手调成 `59 23`，且“历史文档按叙事冻结不改”。**运维时以 `trimc cron list` 输出为准，不要信文档里的表达式**。jobs.json 持久于 `/var/lib/trimc/cron/jobs.json`（runbook:25）。

**2. 登记**：jobId + per-run 日志 `/var/lib/trimc/cron/logs/<jobId>__<ISO>.log`，去重=调度引擎防重入（registry:31）。注意 runbook:71 的口径坑：引用 job 必须用 36 位完整 UUID（如周迁移 job `b00b0070-2f82-4e7d-a98c-de73e886834b`），截断形式查不到 job。这个载体形态被 spec:253 点名为合法登记载体示例：“jobs.json jobId + per-run 日志（周迁移）”。

**3. Qualify/Plan Skill**：五段链脚本内置，迁移段序固定：OP index → unresolved → trees → carry-over → 通知，“无需逐次语义规划”（registry:32）。注意“五段链”有两个视角：语义序（上面这个）和脚本五步 `create/migrate/carry_over/validate/agent_close`（paper-①:46）。Plan 是静态固化的——同②的模式，这是“维护类实例 Plan 段=静态计划固化”的共同形态。

**4. DCE**：`python3.8 五段链 --sync`，runAs fleet，写 operating-records，git commit（内联身份 TriMC Scheduler）+ push `/srv/git/TriMetaverse.git HEAD:dev`（registry:33；runbook:19-22）。两个硬约束：解释器必须是 **python3.8**（服务器系统 python3.6.8 不兼容新语法，runbook:27）；脚本幂等——“create already_exists 不失败、carry_over 目标存在即 skip，修正后直接重跑”（runbook:93）。

五步链逐步走读——一轮 `--sync` 在 `.shift-ade.json` 里落成 `steps[]` 五步，步名与字段合同出自 paper-①:46（每步必含 `status/result/changes/errors/check_time`）：

```text
create       建新周平面骨架（OP-YYYYMM-Wnn-001.json 周索引、unresolved-items.md 等，paper-①:64）；幂等：already_exists 不失败（runbook:93）
migrate      周平面平移：上周 OP index/unresolved/trees 语义段（registry:32）迁入新周，changes 记 created/retired/migrated 对照（paper-①:55）
carry_over   未结项挂账迁移 + escalation_8w 阈值上报（含 CARRY-* 明细，paper-①:73）；幂等：目标存在即 skip（runbook:93）
validate     链内校验步：五步结果在此汇成可断言结构——解析 .shift-ade.json 逐项断言的评分素材即源于此（paper-①:46）
agent_close  收口步：Close 判定落卷，终态样本=.shift-ade.json status=pass + 落盘文件 + commit 三方一致（paper-①:58-65）
```

五步各自的 `changes`（before/after 对照）与 `check_time` 时间戳就是 paper-① 的 audit-record 评分项（10 分，paper-①:50-55）——读一份 `.shift-ade.json` 先看这两个字段。

> 新人提示：先在测试根走 dry 链再碰真迁移——`python3.8 -m runtime.cognition.weekly_plane_shift --from W33 --to W34 --start-date 2026-08-17 --operating-root <测试根> [--sync]`（runbook:57-59）；真跑失败不回滚代码——脚本幂等，修正后直接重跑（runbook:93）。

**5. Verify**：①的登记表（写于前标准期）没有单列 Verify 行——链内 `validate` 步承担校验。这是“前标准期实例”的形态：registry:17 注记 FADE-001..004 属四模块架构成立前登记，按 CEO 裁定不追溯降格，但须对照新规补课。教学上要如实：不要替它脑补一个不存在的独立 Verify CLI。

**6/7. Score CLI / Score Skill**：①的评分是 2026-08-20 首评：对卷 paper-①（threshold 80，paper-①:5）得 **PASS 90/100、必选 6/6**（registry:62），遗留“服务器侧 jobs.json/per-run 日志回流后复评”。这次评分属回溯建卷口径——评分动作对真实 run 复算，而非每次 run 内嵌评分（后者是②正在走的新立法路径）。

**8. Close Skill**：迁移完成后邮件通知语义摘要——notify.json 0600 + QQ SMTP，2026-08 演练二期实证真实投递（registry:34；runbook:28，审计以 .shift-ade.json + git commit + per-run 日志为主、邮件为补充）。

**9. Close CLI**：`.shift-ade.json` 审计文件 + git commit 哈希为确定性收口载体（registry:35）。五步每步含 `status/result/changes/errors/check_time`，changes 含 before/after 对照（paper-①:46,53-55）。

**10. 终态**：实跑样本 W33→W34 迁移（2026-08-17 由服务域 TriMC 独立完成，registry:36），W34→W35 于 08-24 自然触发（review:36）。

**运维必背**（runbook §2 部署七步里的三个权限修复，每次 pull/push 后可能复发）：`.git` 属主修正 `chown -R fleet:fleet /srv/fleet/TriMetaverse/.git`（runbook:34-36，root pull 后常态复发）；裸仓 loose 目录 `g+w`（runbook:37-39）；fleet `safe.directory` 全局登记（runbook:40-41）。异常对照表在 runbook:88-97，演练回退“无痕四件套”（裸仓 ref/舰队克隆 HEAD/job 态/本地 HEAD）在 runbook:107-125。

---

## 四、维护项②（每日工作进度维护）：十段逐段落地形态

②的十段表在 registry:45-57，执行体是 patrol 全文（TriCompany runtime/cognition/daily_progress_patrol.py，952 行，纯确定性无 LLM）。先讲节奏设计，再逐段落地。

### 4.1 节奏：事件驱动主 + 10 分钟兜底 + 单写者三原则

设计注册分两步：十段设计 ea64927（runtime-owned durable profile，探索期手动/自动化期 cron 两阶段），节奏重设计 49287fc（CEO 纠正：“第六源是恢复兜底不是日总结”），两 commit 均见于 progress:43 的当日 registry 提交列表。

- **主=事件驱动**：助理销账/交付/裁决后随手 append+push——因为“哪件事值得记、怎么概括”是语义判断，写的人质量最高。
- **辅=定时巡检**：cron `*/10`，job `d0f87756-e941-4984-9919-1993028566bc`，Asia/Shanghai，runAs fleet（progress:18）——因为人会忘，确定性脚本不会；最坏丢失窗口 23h→10min（progress:18）。
- **单写者三原则**（patrol 文件头 docstring patrol:5-8, 21-24）：
  1. 助理主叙事：权威叙事在 ledger-mirror/董事会记本（机器本地不入仓），daily-progress 是粗粒度镜像（progress:3,29）；
  2. patrol 只 append 不重写：写入只开 append 句柄（patrol:420-428），T4 评分项直接机器检查“patrol 身份提交补丁零删除行”（patrol:546-554）；
  3. 冲突跳轮：与助理写冲突时 `pull --rebase` 重试一次，再失败**跳过本轮、下轮再补**，不算 cron 失败（patrol:119-130 attempts=2；patrol:362-370 返回 skip envelope）。

### 4.2 十段逐段

**1. 事件触发**：如上双通道。脚本入口三种模式：默认 dry-run / `--sync` 写入 / `--self-test`（patrol:31-33, 909-947）。

**2. 登记**：运行标识=日期锚 `## YYYY-MM-DD（周X）`；去重=同日标题已存在则 append 不新建（registry:48）。实现上 `day_section_index` 用**日期前缀匹配**而非全标题匹配——星期标签误标变体不会触发重复建节（patrol:95-98；自测 Case H patrol:775-778）。持久=git 三端。

**3. Qualify（机械门）**：当日确有运行变化，拓扑口径——“自上次进度条目后新 commits>0”（registry:49）。实现是 `commits_since(repo, base_full)`，核心一行 `git log ... "<base>..HEAD"`（patrol:177-208，拓扑表达式在 patrol:186）。无变化返回 skip，**不产空节**（patrol:394-395）——skip 是合法终态不是失败。曾设计的 ledger-mirror mtime 分支被 2026-08-28 升档联审裁定删除：“未实现未接线的纸面设计=审计负债；设计史留 patrol docstring”（registry:49；patrol:18-19）。为什么删？因为服务器巡检读不到 `.fade/`（gitignore，patrol:14-16），一个永远走不到的分支留在代码/文档里会误导审计者。

**4. Plan**：静态计划固化于脚本。增量块格式固定三件：补写行（时刻+基线短 hash+N 条 commit）→ commit 清单（默认上限 15 条）→ registry 行（版本+当日 registry 提交）（`build_increment` patrol:246-258；`build_day_section` patrol:261-278）。

**5. DCE**：`patrol_once` 一轮全流程（patrol:352-466）：pull --rebase → **recovery push 自愈** → 读门限 → 收集 registry 快照 → 组块 → 写入。四个关键设计：

- **recovery push（防死锁）**：上轮 push 失败遗留的未推提交，在下轮开头先重推。否则“文件已被自己触碰→门限闭合→永不重推”死锁（patrol:22-24 docstring；实现 patrol:372-379）。
- **写入即回滚保护**：写入前存 `pre_bytes`，verify 失败或 commit 失败就回滚到写前状态（patrol:430-451）。
- **push 分级**：sg-bare 必达——失败不伪造终态，envelope 记 fail，commit 留在舰队克隆等下轮自愈（patrol:453-458）；GitHub best-effort——服务器无凭据，`GIT_TERMINAL_PROMPT=0` 快速失败禁挂起（patrol:101-104；patrol:460-464）。
- **身份**：commit 内联 `TriMC Scheduler <trimc-scheduler@fleet.local>`（patrol:57-58）——这个身份是 Score CLI 区分“巡检写”与“事件写”的判据（patrol:612-613）。

**6. Verify**：写入后回读自检 `verify_day_section`：当日节存在且非空、本次追加块在卷、锚点格式合规（patrol:281-299）。失败即回滚+fail envelope（patrol:438-442）。

**7. Score CLI**：patrol `--score`，一具两段（Score 与 Verify 复用同一解析助手，防 §7.4 双实现——review:53）。五约束 + shadow/gate 两阶段，见第八节。

**8. Score Skill**：**待实现**（registry:54，纸面如实）。已圈定范围：T3（事件驱动及时性，commit/msg 时戳对照+双席抽验）与 T7（治理对齐：触发权董事会/执行 patrol/助理主叙事 + trimc jobCount 健康 + D-02 nextRun 保持）留 Skill，CLI 禁自动化（paper-②:34-41,64-70；约束 1 patrol:470）。

**9. Close Skill**：董事会/助理确认当日节完整（registry:55）。扩维裁定的立法方向：Close Skill 轻量独立化——事件驱动写内嵌语义判定 + 评分达标程序化判定三态（通过/RETRY/ESCALATED，引用评分证据）（registry:66）。

**10. Close CLI**：现行载体=“push 三端成功即终态（任何一端可达=每日进度不灭）”（registry:56）。**但联审已裁定这个时序违规 §2.5**：升完整后时序必须 DCE(push)→Verify→Score→Close Skill→Close CLI，现行“push 即终态”违反 §2.5；Close CLI 拆段=push 业务持久化【部分】降档如实（registry:66）。这是新人必须知道的“已知债务+已立法修复路径”，不是可以忽略的历史遗留。

**终态**：当日节在三端仓库可读——机器全灭时的日级重建锚（registry:57）。

### 4.3 拓扑门限详解（本实例最重要的一个技术点）

门限要回答的问题：“进度文件最后一次被触碰之后，仓库有没有新 commit？”第一版实现用“时间戳严格大于”（commit 时间 > 文件最后触碰时间）。20:20 巡检一轮 skip 实测抓出缺陷：**rebase 连发使 marker 提交与进度提交同秒**，同秒提交被“严格大于”漏计，门限误闭合（patrol:180-182 docstring 原话记录了这次实测缺陷）。修复=改拓扑口径 `git log <touch_full>..HEAD`（patrol:186）——git DAG 的可达性天生没有“同秒”问题，变基重写也不影响。修复同时留下回归用例：自测 Case I 用 `GIT_COMMITTER_DATE`/`GIT_AUTHOR_DATE` 固定同秒造两个提交，断言拓扑门限全部计入（patrol:784-802，I1/I2）。

**教训一句话**：顺序/计数类判定用 git 拓扑（DAG），不用墙上时钟——时间戳秒级粒度+变基重写都是它的判据盲区。这与 D-04 时刻纪律“禁止从上下文时间戳外推”（disciplines:37-41）是同一价值观在代码层的投影。

---

## 五、最小闭环 MVP：新人上手跑一遍（不碰生产）

patrol 默认路径指向服务器舰队克隆（`DEFAULT_TMV_REPO=/srv/fleet/TriMetaverse`，patrol:72-73），本机演练要么读代码，要么用参数覆盖到沙箱目录。**第一课只跑前两个命令**：

```bash
cd D:/Code/ai/TriCompany
python -m runtime.cognition.daily_progress_patrol --self-test   # 内置验证套件（沙箱 git 仓，不动真仓）
python -m runtime.cognition.daily_progress_patrol               # dry-run：只读，不 pull 不写不推
```

- `--self-test` 沙箱自建 bare+repo+tco 三仓（`_init_sandbox` patrol:674-689），跑 Case A（门限闭合→skip）/B（marker→written+当日节自动建）/C（自写后门限闭合，无自激循环）/D（二次增量 append 不重写）/E（verify 负例）/F（registry 解析）/G（dry-run 只读）/H（误标容错）/I（同秒回归）/S（score 沙箱含 T4 负例）——**30/30 过**（升 --score 后从 21 项扩到 30 项，progress:18,24）。输出 `"status": "pass"` 即通过；退出码 1=有 fail（patrol:35, 906）。
- dry-run 输出 envelope，`status=would-write` 时 `details.would_write_first_line` 给出将写入的首行预览（patrol:414-418）；`status=skip` 表示门限闭合。

服务器侧（只读观察起步）：`/var/lib/trimc/cron/logs/<jobId>__<ISO>.log` 是巡检 stdout envelope 的落盘处（patrol:26-28）——这是 FADE spec §九.4“sync-log 或等效审计日志”的等效载体。`--sync` 只应出现在服务器 fleet 环境下由 cron 拉起，**新人不要手动在服务器点火**（要验链路用 `npx tsx src/cli.ts cron run <全量UUID>` 幂等兜底，runbook:66-69）。

评分模式演练：

```bash
python -m runtime.cognition.daily_progress_patrol --score --date 2026-08-28
```

输出 shadow 评分 envelope（只观测，不写任何东西）。怎么读它，第八节讲。

---

## 六、本周真实运行证据（W35）：巡检三跳弧线 + 里程碑锚点

以下时间线全部来自 progress:18-19,41-46 与 registry:63-65 的实读核验（hash 均在两份以上文件交叉出现）。

**部署（08-28 傍晚）**：patrol v1.0 落 TriCompany（fbadf21/bfad13f，内置自测 21/21）+ trimc cron job `d0f87756-...` 注册，nextRun 落 20:10 +08（progress:18）。

**三跳弧线**（progress:19 原文记录）：

| 时刻 | 事件 | 证据锚 |
| --- | --- | --- |
| 20:10 | 首跳真实触发：门限开（触发 commit=83753b74，fade-007 恢复配方补第 6 源），补写落地 2014ef40；误标节容错识别生效 | progress:19,41-43（补写块原文：“自上次进度提交 17a4af84 后新增 1 条 commit：83753b74”） |
| 20:20 | 第二跳 skip——**skip 实测抓出门限同秒缺陷**（rebase 连发致 marker 与进度提交同秒被“时间戳严格大于”漏计） | progress:19；patrol:180-182 |
| 修复 | 拓扑门限 `git log <touch>..HEAD`，3082d7d 落地，含回归 Case I | patrol:186,784-802；review:20 |
| 20:30 | 第三跳精确补写：c9300421 补写 marker 8ad1ab4a（20:30:06 检出，**6 秒闭环**） | progress:19,44-46 |

注意 progress:19 结尾那句：“本销账行即事件驱动主第二次执行”——销账动作本身随手 append 进度文件，就是事件驱动主通道在跑。这就是“事件驱动主+兜底辅”在真实一天里的样子。

**GitHub 失败收敛实例**：20:10 巡检 GitHub push 失败（服务器无凭据，设计内），随后事件驱动写把三端补齐——“任何一端可达=每日进度不灭”口径的实测（review:26-27）。ls-remote 三端 tip 一致实证锚=ce3ad83f（review:19,23）。

**立法锚点（同日）**：十段设计注册 ea64927、节奏重设计 49287fc（progress:43）；备料包 b98ea91d（review 全文，progress:23）；升档裁定落地 TCO d0cb4d9+6d42612（扩维卷冻结+registry 立法包，progress:24；其内容与 registry:63-67 逐项对得上，可交叉验证）。

**跨日行为样本**：08-29 00:00 巡检在前一日晚间提交 caeec035（基线 c9770a36 之后）落入新一日节并自动建节（progress:47-52）——`week_relpath` 按 ISO 周推算路径（patrol:85-88），跨日/跨周都不需要人工干预。

---

## 七、故障弧线与教训（关联 D 系工程纪律）

**弧线 F1：W34→W35 迁移落旧基（①域，已立纪律）**。本地超前 101 commit 未推 → 迁移 commit 落在旧基 `ae3d32fe` → 回流被迫 merge + W34 index 冲突人工裁定 + W35 台账漏登 2 树（08-24 补全）（runbook:167）。产出的纪律：**迁移冻结窗口**——周日 23:00 北京时间前 operating-records 全部 commit 并推 sg-server，23:00 至周一回流完成期间冻结本地对 operating-records 的一切写入；姊妹条=周日全仓推送软习惯（runbook:167-168）。教训本质：迁移的 DCE 是确定性脚本，但它的输入基线不是确定性保证的——输入纪律必须由人来守。

**弧线 F2：20:20 同秒门限缺陷（②域，修复+回归）**。见 4.3 节。教训：时间戳当判据、拓扑当证据；缺陷被“skip 实测”抓出而非靠 review——**让系统跑起来观察它，比读代码更能暴露门限类缺陷**。

**弧线 F3：GitHub push 恒失败（②域，设计内边界）**。服务器巡检无 GitHub 凭据，push best-effort（patrol:460-464）。配套设计：T5 评分项“离线=不可验非 FAIL”（约束 2，patrol:471；paper-②:49-56）、GitHub 最终一致容差 ≤24h、收敛由事件驱动写兜底（paper-②:52-54；review:27）。教训：**失败要分“设计内降级”与“设计外故障”**，评分体系要给前者留“不可验”态，否则兜底通道会被误判为持续 FAIL。

**弧线 F4：recovery-push 死锁（②域，预防性设计）**。如果上轮 push 失败后不先重推，本轮巡检补写会把门限重新闭合，未推提交永远滞留（patrol:22-24）。教训：自愈逻辑要检查“自己上轮的遗留状态”，不是只看外部世界。

**弧线 F5：LG-012 restart 触发 TriModel dist 潜伏损坏（同日关联故障）**。TriMC cron CLI 补 X-Internal-Token 头当日闭环后，restart 触发 dist 丢失崩循环，21:08-21:11 如实入账后重建修复（progress:20）。复盘进 **D-03 v3**：dist 形态服务（gitignored 构建产物）restart 前置检查必须含 dist 完整性 + node_modules 符号链接目标存在性；对 gitignore 构建产物仓做 reset/re-checkout 后必须重建 dist——“旧进程内存存活会长期掩盖潜伏损坏”（disciplines:33）。

**弧线 F6：mtime 纸面设计的审计负债（②域，制度教训）**。ledger-mirror mtime 门限分支曾进 49287fc 设计，升档联审裁定删除——服务器根本读不到 `.fade/`，这个分支永远不会执行（patrol:14-19；registry:49）。这与 spec 细则 10“接线+实测才算立法完成，未接线的法条一律标注纸面法”（spec:266）同源：**设计史可以留 docstring，现行文档里不留给未实现分支任何“已设计”的暗示**。

---

## 八、评分卷宗解读

### 8.1 迁移域原卷（paper-①，已评结）

结构：10 检查项 × 权重 10 = 100，threshold **80**（paper-①:5），其中 6 项必选（trigger-config / run-id-carrier / skill-docs / cli-report / audit-record / terminal-sample，各 paper-①:13-65）。卷 notes 明确证据充分性口径：服务器侧 jobs.json/per-run 日志/邮件投递日志本机不可得，“以 runbook 文档级证据计分并如实扣分”（paper-①:8）。首评 **90/100、必选 6/6**（registry:62），扣掉的 10 分对应哪一项卷内可复算。遗留：服务器侧证据回流后复评——这项挂在 registry:67 齿条①，**09-17 四周警告线前必须动**。

### 8.2 维护域扩维卷（paper-②，冻结未达标结算）

先看冻结三要素（paper-②:6-11）：冻结点=**载体定版 commit 同盘**（裁定：patrol `--score` 落地=载体定版）；算法=`_fadehash.dual_sha256` canonical（raw+LF 双 hash，行尾漂移按 SOFT-DRIFT 留痕）；双 hash 值记在冻结 commit 消息与登记册条目，**不入卷内防自引用**——卷值 raw=lf=`82e34df7f16e4deda266b7c8106ded0c2eddec1e85e4729db70bb35194524153`（registry:64；progress:24），raw 与 LF 相等=卷纯 LF 无漂移。这正是 spec v2.0.3“试卷 Plan 时点冻结”立法（spec:187-193）的实例化：②为静态固化 Plan（无逐次 Plan Skill），所以冻结时点取 Score 载体落地 commit 同盘，首个维护域评分 run 收口对卷（review:79）。

**scoreable run 定义**（paper-②:12；约束 3 patrol:472）：自然日含事件驱动写与巡检补写**各≥1**；skip-only 轮不可评分。run_score 里的判据就是“当日 patrol 身份提交与事件身份提交都非空”（patrol:612-614），不满足时 envelope 给 `status=not-scoreable` 并带 reason（patrol:643-647）。举例：08-28 事件+巡检都有，scoreable；08-29 只有 00:00 一次巡检补写，在事件写发生前是 not-scoreable。

**T1-T8 权重表**（paper-②:17-78）：

| # | 检查项 | 权重 | 判定载体 | CLI 实现锚 |
| --- | --- | --- | --- | --- |
| T1 | 当日节结构齐备（存在+星期标签合规+节非空） | 15 | Score CLI | patrol:489-507 |
| T2 | 巡检兜底及时性：触发→下一次文件触碰 ≤780s | 15 | Score CLI | patrol:510-543 |
| T3 | 事件驱动及时性（销账/交付与状态条同 batch） | 10 | Score Skill（约束 1） | — |
| T4 | 单写者纪律：patrol 补丁零删除行（append-only） | 15 | Score CLI | patrol:546-554 |
| T5 | 三端持久（ls-remote 对账；GitHub 容差 ≤24h） | 10 | Score CLI | patrol:557-573 |
| T6 | 门限正确性（全文件日节零空节+提交消息格式合规） | 15 | Score CLI | patrol:576-593 |
| T7 | 治理对齐（分权制+jobCount+D-02 nextRun 保持） | 10 | Score Skill（约束 1） | — |
| T8 | 巡检脚本载体质量门（self-test 全过+无 LLM） | 10 | 自测输出+代码抽验 | patrol:596-600 |

双门槛：必选全过 + 总分 ≥90（定值=对齐①90 分档位带，paper-②:80-84）。**CLI 小计 80 + Skill 外部 20 = 100**（`SCORE_WEIGHTS` 小计 80 / `SCORE_SKILL_EXTERNAL={"T3":10,"T7":10}`，patrol:67-68）——这就是“扩评中”的数学含义：CLI 满分也只有 80，<90，**必须等 Score Skill 实跑才能上 90 线**。

**T2 的量化与基线**（本卷最容易误读的一项）：780s = tick 600 + timeout 180（`TICK_SECONDS=600`/`JOB_TIMEOUT_SECONDS=180`/`T2_MAX_GAP`，patrol:64-66；paper-②:29）——兜底义务的物理上限就是“一个调度周期+一次 job 超时预算”。基线规则=仅计**当日首次文件触碰之后**的触发，建档前无兜底义务（patrol:512-514；paper-②:31 boundary）；触发后尚未到下一 tick 或跨日的计 pending 不计违规（patrol:536）。

**部署日 65/80 的如实解读**（registry:65；progress:24）：08-28 shadow 校验得分 65/80。算术：80−15=T2 唯一违例，即 T1(15)+T4(15)+T5(10)+T6(15)+T8(10)=65 全过。唯一违例锚=**83753b74**：该 commit 落在 20:10 部署之前，当天 patrol 尚不存在，触发→补写间隔必然超 780s——这是**部署日 regime 边界**（系统上线当天，上线前的触发无兜底义务），处置=留 Score Skill 注记、不在 T2 重复扣分（paper-②:31）；随后 T2 首触基线规则在 shadow 观测期内落地为代码（patrol:512-514），让这类边界从“违例”变为“不计入”。**教学要点：65/80 不是“系统差 25 分”，而是“新卷首日观测 + 一条已被裁定为 regime 边界的违例”**——读评分卷宗必须先读 boundary 字段再读分数。

**shadow→gate 两阶段**（paper-②:13-16；约束 4 patrol:473）：首评期 `--score` 只观测不拦截（shadow envelope 留痕，envelope 里 `gate_wired: false` 写死，patrol:661）；试卷冻结+双门槛达标后，push 终态门接 score（不达标不 push、RETRY 留痕）——**接线时点=扩评达标日**。也就是说今天你跑 `--score`，它永远不会阻止你任何事；它“达标”的那一天，才会变成 push 前的硬门。

---

## 九、与 FADE 协议 v2.0.0 新立法（§2.7/§2.8）的对照

### 9.1 §2.7 节点收口报告：豁免，但有精神等价物

§2.7 立法动机来自 FADE-006 的过程黑箱缺口：多节点树里每个节点完成时必须在 `reports/node-<NODE-ID>.md` 落十字段收口报告，配 `node-report-check` 校验器与编排双门（spec:195-223）。**FADE-001 在补课范围裁定中被豁免**：节点收口报告仅适用多节点树实例——“001/002/003 单段脚本/CLI 实例豁免，004 HTTP 链多节点按段适用”（registry:17，联审 CPO-F16）。理由：①的一次 run 是一条五步链脚本，②的一次 run 是一轮 patrol——没有“节点”可拆。

但②有两个精神等价物，新人要能指认：

1. **每轮审计 envelope**：patrol stdout 结构化 JSON 由 trimc cron per-run 日志落盘，patrol docstring 自认这是“FADE §九.4 sync-log 或等效审计日志的等效载体”（patrol:26-28）；
2. **daily-progress 当日节本身**：按时间锚聚合“当日发生了什么（commit 清单+registry 变化）”，格式固定、可机器校验（T1/T6 就是在校验它）——功能上接近一份“日级收口报告”的叙事面，只是粒度是日而非节点。

### 9.2 §2.8 段-实现绑定：FADE-001 是“协议管不变量、实例管载体”的活教材

登记段四不变量（spec:241）在两个维护项上的载体对照：

| 不变量 | ①载体 | ②载体 |
| --- | --- | --- |
| 唯一性 | jobId（36 位 UUID） | 日期锚 `## YYYY-MM-DD`（同日单节） |
| 去重性 | 调度引擎防重入（runningAtMs 守卫，runbook:92,171） | `day_section_index` 同日已存在则 append 不新建（patrol:95-98） |
| 关联性 | per-run 日志按 jobId 聚合五步链 | 当日节聚合全部补写块+registry 快照（patrol:246-258） |
| 恢复锚 | `.shift-ade.json` + 迁移 commit | 三端可读的当日节（机器全灭日级重建锚，registry:57） |

①的载体形态被 spec:253 逐字点名为合法登记载体示例（“jobs.json jobId + per-run 日志（周迁移）”）。registry v1.2.1 注记已把本册十段工件表 schema 化为“段-实现映射表”（registry:19），最小 schema 三字段=段名/载体类型与形态/不变量满足证据引用（spec:258）；FADE-006 已完成映射表首行填制（registry:155-170），FADE-001 的正式映射表挂在其升完整路径上——现状①②两张表（registry:28-36,45-57）已是映射表的内容形态，升档时按三字段补齐证据引用即可。

**Close CLI 载体的诚实降档**是 §2.8 时代最值得学的表态范式：FADE-006 对 Close CLI 载体做了三态声明（“matcher 载体=已接线 / 例行化宽口径=核验中”，registry:168）；FADE-001② 同样把现行“push 即终态”如实降档为“push 业务持久化【部分】”，并立法升完整前置=收口登记载体（run-root 式清单 hash 或当日节收口行+registry 台账，v2 schema 复用零新工具）（registry:66）。**模式：不达标不隐瞒，声明三态+写明解除条件**。

**细则 10（spec:266）视角的②现状**：接线+实测才算立法完成。②的 Score CLI 已接线已实测（部署日 shadow 65/80 是真实 run 的观测）；Score Skill 纸面（registry:54）→ 属“纸面法”治理对象，登记册“纸面法清单”当前空清单开局（registry:172-178），②的纸面项在条目内以“扩评中”标注、周检核对。齿条两项盯紧：①迁移域服务器回流复评（09-17 警告线）②run↔段索引现场化——下个维护 run 起，不事后补（registry:67；review:69）。

---

## 十、接手任务清单

**读什么**（顺序）：registry FADE-001 条目 → patrol 全文 → paper-② → runbook §2/§5/§7 → spec §2.5/§2.7/§2.8 → review（理解扩维裁决从哪来）。

**跑什么**：第五节两条命令；`--score --date <昨日>` 看真实卷面。

**改哪里**：patrol 单文件即②的全部 DCE/Verify/Score CLI 载体；改完必须 `--self-test` 全过（T8 是评分项，patrol 改版后 T6/T8 复验不自动废卷，paper-②:76）。

**验证方式**：本地改动 → TriCompany 仓 commit → 服务器 `/srv/fleet/TriCompany` pull（代码修改一律本地发起：本地→裸仓→舰队克隆，runbook:169）；巡检 envelope 看 `/var/lib/trimc/cron/logs/`。

**常见误区表**（每条都有真实事故/裁定背书）：

| 误区 | 真相与锚 |
| --- | --- |
| 信 registry 里的 cron 表达式 `0 23 * * 0` | 现役 `59 23 * * 0` Asia/Shanghai，历史文档叙事冻结（runbook:18,165） |
| 用截断 UUID 查 job | 必须 36 位全量 UUID（runbook:71） |
| 手动改 cron state 时抹掉 nextRunAtMs | 引擎靠它排期，缺失=永不调度（D-02，disciplines:23-25；T7 评分项盯它） |
| 把 self-test 30/30 说成“Score 实跑通过” | 自测=载体构建质量门，Score=对真实 run 的评分，禁混同（review:10,51；paper-②:89） |
| 把 65/80 当“系统不及格” | CLI 小计上限 80；T2 违例系部署日 regime 边界已裁定注记（registry:65） |
| 在服务器手动 `--sync` 试运行 | 只用 cron 自然触发或 `cron run <全量UUID>` 幂等兜底（runbook:62-69） |
| 给 patrol 加 f-string/match 或假设 GitHub push 必达 | 服务器 python3.8 约束（runbook:27）；GitHub=best-effort，失败属设计内（patrol:460-464） |
| 报时直接减 UTC 与北京读数 | 换算一次、单一时区帧内比较（D-04 v3，disciplines:41）；envelope check_time 走 UTC Z、人读轨走 +08（D-04 v4，disciplines:43-46） |

---

## 使用依据

- D:/Code/ai/TriCompany/docs/engineering/fade-registry.md（FADE-001 条目 24-67 行：①十段表+②维护项②十段表+扩维块/Score 五约束/Close 立法/齿条；v1.2/v1.2.1/v2.0 注记）
- D:/Code/ai/TriCompany/docs/engineering/fade-papers/FADE-001-paper-maintenance.json（扩维冻结卷全文：freeze/scoreable/T1-T8/threshold/transfer_domain/honesty）
- D:/Code/ai/TriCompany/docs/engineering/fade-papers/FADE-001-paper.json（迁移域原卷：threshold 80、十检查项、notes）
- D:/Code/ai/TriCompany/runtime/cognition/daily_progress_patrol.py（全文 952 行：拓扑门限 177-208、单写者 119-130/362-370、recovery push 372-379、Verify 281-299、Score 五约束 469-474、T1-T8 489-600、run_score 603-668、自测含 Case I/S 784-883）
- D:/Code/ai/TriMC/docs/ops/trimc-cron-plane-shift-runbook.md（§1 架构/§2 部署/§3 装 job/§5 异常/§7 纪律：冻结窗口 167、时区口径 165、job UUID 71）
- D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W35/daily-progress.md（里程碑 1-16、三跳弧线 19 行、20:10/20:30 补写块 41-46、08-29 跨日节 47-52）
- D:/Code/ai/TriMetaverse/docs/execution/fade-001-upgrade-review.md（十段三态表/缺口 7 项/Score 载体方案/试卷草案/自检）
- D:/Code/ai/TriCompany/docs/workflow/engineering-disciplines.md（D-02/D-03 v3/D-04 v3-v4/D-10 等）
- D:/Code/ai/TriCompany/docs/engineering/fade-protocol-spec.md（§2.5 终态门 168-174、§2.6 试卷冻结 187-193、§2.7 节点收口报告 195-223、§2.8 段-实现绑定 225-266、§8.1 profile 412-430）
