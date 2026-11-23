<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-001/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-001 loop 章——进化环编排、轮末七席联审与任务书闭环

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-001/08-loop-evolution.md
- syncMode: source-only
- lastSyncedAt: 卷面时点锚=git commit 时戳（零手打·D-47 增补款正形）

> **补编批（v2.2.0·2026-11-23·CEO 直令「把触发和 loop 也包含进教程」·BOD 转·DP-20261123-025·COS 补号 19:59）**：本篇=loop 章新增（①loop 大图 ②round_runner 轮编排 ③chain_runner 段序驱动 ④轮末七席联审+31 维冻结表 ⑤improvements→生成器→charter→呈 CEO 批→施工→再点火闭环 ⑥M1-M9 全景 ⑦跨点火累计 ⑧W48 真实弧线）。教程线零触链——纯文档面。姊妹篇=[07 触发章](07-trigger-and-ignition.md)。

读者：要值守/评审/改造进化环的人——值席、COO/CTO/STE、七席联审参与者，以及要接手 loop 代码的工程师。
前置：已读 [07 触发章](07-trigger-and-ignition.md)（runId 四形/点火四件/三件前置）。
事实基线：2026-11-23 W48 进化环在役（round_runner/chain_runner/charter_generator 三件在盘·9 轮 resume 谱系实证·M1-M9 九条款完备）。

---

## 〇、培训判断：loop 与十段链是什么关系

十段链（01-06 讲的）回答：**"跑一次，跑对没有"**。
loop 回答：**"跑一次不够好，怎么自己变好"**。

所以 loop **不是第 11 段**，而是**包在十段链外面的轮循环**：

```
点火（runId+checks）
  └─ 轮 1：十段链全跑 → 轮末七席联审出分 → 未达标 → 生成任务书 → 候 CEO 批 → 施工改造
  └─ 轮 2：新代码再跑十段链 → 再联审 → …
  └─ … 直到 A>95 且 B>95（test→prod）或 FUSE 8 轮熔断（单次点火收敛）
```

`round_runner.ts` 头注原文定性：**"loop 本体=runner 内单程序内聚循环控制流（while＋状态机）——点火后循环体内自主迭代推进；前版「每轮一指令·队列接力」形=单轮开工指示器非 loop（勘正承录）"**。这句要背：**loop 是单进程 while，不是"人每轮再点一次"**。

本篇按"轮怎么转→每轮跑什么→轮末怎么评→评完怎么改→改完怎么再点"的顺序讲；M1-M9 九条款是这一整套的成文法，放第六节集中对表。

## 一、loop 层件族与运行位

| 件 | 位置 | 行数 | 职责 |
| --- | --- | --- | --- |
| 点火入口 | `TriRMC/scripts/fade001-ignite.ts` | — | 参数解析（`--run-id`/`--checks-json` 必载）→ 装配 chain+io → `runLoop` → 白名单投影打印 |
| 轮编排器 | `TriRMC/src/fade001/round_runner.ts` | 465 行 | loop 宿主：四态状态机/while 体/FUSE/首轮停点/charter 挂载/联审钩 |
| 十段链驱动器 | `TriRMC/src/fade001/chain_runner.ts` | 260 行 | 段序表硬串行·逐段调 TC `runtime/cognition/` CLI·产物前置断言·verdict 投影 |
| 任务书生成器 | `TriRMC/src/fade001/charter_generator.ts` | 188 行 | opinions.json → 五字段机械映射 → 任务书 JSON（pending_approval·零批准效力） |
| 联审 spawn | `TriCompany/runtime/cognition/loop_joint_review_spawn.py` | — | 七席 spawn·两对象×部门维度·opinions.json + joint-review.json |
| 维度冻结表 | `TriCompany/runtime/cognition/fade001-dimensions-v1.json` | v1.0.0 | 七席 31 维固定维度表（LLM 只打分不自创） |
| 挡位门 | `TriCompany/runtime/cognition/activation_gate.py` | — | 起跑前置 A1-A4（见 07 章 §3.1） |

部署位：产线=sg `/srv/fleet/TriRMC`（TC 检出 `/srv/fleet/TriCompany`·929 现位）；本机 clone 为施工线检出，运行态以产线读数为准。

> **「loop 层不是 fade 段」**：round_runner 头注明写 loop 尾段联审是「loop 层非 fade 段」——即协议十段之外的一层编排；改造 loop 本体=机制本体项，回呈 CEO（M4-v2 边界）。新人别把它塞进十段编号里。

## 二、轮编排器 round_runner.ts

### 2.1 主形：单进程 while（for(;;)）

`runLoop(io, ignite)` 骨架（照代码逐行对读）：

```
runLoop:
  flag = readFlag()            // 缺省 test；prod → 直接 throw（prod 不入 loop）
  st = readRunnerState()       // round_count/resume_stage/run_id/…
  st.run_id = params.run_id    // DP-009：runId 轮层贯穿
  gate = activationProbe(checks)  // gate≠ready → failed 出口（rounds_run=0）
  resumeStage = st.resume_stage ?? null
  for (;;):
    run = await chainRunner.run(params, resumeStage)   // 十段链（B 路核心）
    if !run.ok → failed 出口
    await runJointReviewHook(...)                      // 轮末七席联审（见 §四）
    if verdict==='loop_exit' → setFlag('prod') → prod 出口   // 唯一程序自动边
    if round_count>=FUSE_MAX_ROUNDS(8) → fuse_marker → fuse 出口
    if 首轮 && first_round_pending 未 released → first_round_pending 出口（停面候 CEO）
    if flag==='debug': 候裁决 continue/terminate/absent；continue→tryCharterMount
    // test 态：直进下轮（不候裁决）
    st.resume_stage = null      // 轮毕清写（防二次点火静默跳段）
    st.round_count += 1; writeRunnerState
    params = nextRoundParams(st, params)   // 自主迭代推进
```

四条读法要点：

1. **prod 不入 loop**：`readFlag()==='prod'` 直接 throw——周日正式拍走单轮直走形，不经过进化环。
2. **联审钩在 verdict 判级之前调用**，但钩子内部做了 DP-021 两阶段（先联审出分→再判级→达标跳过 charter），见 §四.5。
3. **每轮毕必清 `resume_stage`**——这是「铸件族窗 clear-write 修形」：防放行态下二次点火沿用陈旧 resume_stage 静默跳段（三形态实锤：continue 轮毕不清→同段重复→FUSE）。
4. **`round_count` 是 FUSE 计数域**；`rounds` 是本次点火内已跑轮数——两个不是一回事（跨点火累计看 round_count，单点火出口看 rounds）。

### 2.2 四态与六边（P4 状态机）

四态（`FlagState`）：**prod / test / debug / joint_review**。
- `joint_review` 是 **debug 的执行子态**（debug 轮产出 opinions.json 即进入联审产出面，融合后回 test）——不是第五态。
- 缺省态：`flag.json` 不存在 → `test`（直进形）。

六边（`nextFlagEdge`·纯函数）：

| 边 | 转换 | 触发条件（代码现役） | 自动/人环 |
| --- | --- | --- | --- |
| E1_prod_low | prod→test | 最近一轮 aggregate average ≤95 | 自动回退 |
| E2_test_stuck | test→debug | test 态 average ≤95 且 `roundsSinceFlag≥8` | 自动（7 席联审） |
| E3_debug_back | debug→test | opinions 已融合（人机环批准） | 人环 |
| E4_manual | →test | CEO/COS 手动 setFlag（本函数不算） | 人环 |
| E5_test_high | test→prod | test 态 average >95（既有 EXIT_GATE 边） | 自动 |
| E6_sunday | prod 周日迁移 | cron 面·非本函数域 | cron |

`flag.json` 卷面（D1 §二）：

```json
{"flag":"debug|test|prod|joint_review","authority_ref":"<CEO 令 ref·必载>","switched_at":"<ISO>"}
```

- **切换权=CEO 令**：`setFlag` 无 `authority_ref` 即抛错（fail-closed）；**唯一程序自动写面=EXIT≥95 边**（ref=`run:<run_dir>`）。
- 骨架期语义：`nextFlagEdge` 只判读不执行（runLoop 接线=log 面；flag 写面仍走 `setFlag` fail-closed）。

> **如实注·条款×代码并存差异**：M3-v2 条款（CEO 2026-11-23 03:33）要求**双对象分立判决**——debug→test 需 **A>90 且 B>90**；test→prod 需 **A>95 且 B>95**。而代码现役 `nextFlagEdge` 的 E1/E2/E5 判据取的是「最近一轮 aggregate average」（单值）。两者**并存未对齐**：判级/任务书面（`computeJointGrade`·§四.5）已按 A/B 双对象；flag 边仍按 aggregate average。本教程**如实并列，不裁决**——以 CTO 后续对齐卷为准（候办，非本批施工面）。

### 2.3 FUSE 与 M9（只有 test 态才熔断）

- `FUSE_MAX_ROUNDS = 8`（D1 §一 L21 定谳值；7→8 边界=F-2 钉）——`round_count>=8` → `fuse_marker=true` + 停候 CEO（fuse.marker+pending 冻结）。
- **M9（CEO 裁）**：**FUSE 仅 test 态生效**。
  - **test**：8 轮上限照役（M8 语义）；
  - **debug**：**不适用**——debug 每轮停在「出稿→候 CEO 批」审批步（M4-v2/M7-v2），**审批步=天然节流**，不会无限烧；
  - **prod**：周日拍不受影响（E6·cron 面照役）。
- 代码现状如实注：`runLoop` 的 FUSE 判断在循环体内对 `round_count` 统一检查（未按 flag 分支）；M9「仅 test」是条款面收窄语义，**代码分支是否已按态收窄=待 CTO 对表确认**（本批未实勘到按态分支，如实标注）。

### 2.4 首轮知情停点（first_round_pending）

- 语义：**首轮毕（close 段毕+verdict 面）→ 停面挂起，候 CEO 知情放行**——放行令=**令面非时面**：`release_ref`（authority_ref）在=released；无 ref=拒绝 fail-closed。
- **放行一次非逐轮放行**：`gateVerdict` 只在 `rounds===0` 时查，后续轮零复查。
- 代码落点：`if (rounds === 0 && gateVerdict?.first_round_pending)` → `released?` 否 → `first_round_pending` 出口（detail 带 `state`/`authority_ref 在/缺`/大白话一行）。
- 为什么有：首轮是"活体第一次全链"，完整性边界=close 段毕+verdict 面；知情停点=让 CEO 在第二轮烧钱之前看一眼真实读数。

### 2.5 resume 续跑边（段 7 续跑）

- `RESUME_STAGE_RETRY = 7`（resume 段号=score 段，D5 拟稿 schema 承）。
- 触发面：`retry_flag.json` pending-retry 轮 → 下一轮点火指令携带 `resumeStage=7`。
- 语义：**从段 N 起跑 + 段 1..N-1 产物真值前置断言全在**——缺=fail（fail-closed 零静默跳段）。
- 为什么是 7：段 6/7 是评分面，重试通常只重跑评分/收口，不重跑迁移本体（省钱省时）。

### 2.6 四护栏常位（CEO 意见⑥·改造后原样保留）

1. **8 轮 FUSE**（本件 round_count>=8 熔断）；
2. **GLM 轨单跑纪律面**：同窗并发 1（D1 L91 固化）——值席/编排面守，runner 零并发点火；
3. **token 值面禁进转报**（D-46）：报文/载荷构造全白名单投影，零原始卷 dump；
4. **D-47 时刻制**：报文落款=date 现查原值粘贴，调用面传时刻串非件内推算。

## 三、十段链驱动器 chain_runner.ts

### 3.1 段序表与硬串行

- `STAGES: StageDef[]`——十段段序表：每段声明 `name / script（TC runtime/cognition/ 相对路径）/ output（产物卷名）/ redirect（preflight/qualify 打 stdout 落卷）/ timeoutMs 覆写 / argv 白名单构造`。
- **硬串行禁跳段**（D1 §四）：**段 N+1 前置断言=段 N 落卷真值**——上一段产物不在，下一段不跑。
- `argv` 白名单构造（零瞎传）；`runDir` 内落产物（P5 二道闸载体）。
- 三层判据族分野同 round_runner：**gate/门判读零夹带**（runner 不复刻各段 CLI 内部判读）。

### 3.2 spawn 七席接装与超时预算

- 段 7=`score_skill_spawn.py` 现役正形（dsh headless CLI·7 席 spawn）——chain_runner 子进程调它=spawn 通道接装面，**零另铸替身**（D-27：spawn 形定谳=dsh CLI 现役先例）。
- `SPAWN_STAGE_TIMEOUT_MS = 7_200_000`（≈110min）：每席 subprocess timeout 缺省 900s × 7 席串行 + 开销余量。默认段超时 900s 会截杀 spawn 段——这是 2026-11-21 勘定后必修的面。
- 后续 DP-019 把段 3 超时从 900s → 300s（seat 工具面治理后段 3 应 2.5min 级）；段 7（score）仍用 spawn 总窗。

### 3.3 P3 灰度：段 3/8 spawn 默认形

- env `FADE_PLAN_SPAWN` / `FADE_CLOSE_SPAWN`：**缺省=spawn 形（现役默认正形）**；env 显式 `'0'` → 回 CLI 形（**回滚锚**）。
- 来历：P3 灰度（CTO 定谳 7c389cac3 §一·2026-11-21）先双形并存，2026-11-22 CEO 任务书 v7 flip（段 3/8 spawn 化=默认正形）。
- 教学要点：**改行为先找回滚锚**——loop 的所有新形都留了 env/开关回滚（P3 env、LOOP_JOINT_REVIEW=0、FADE_PLAN_EXAM_SPLIT=0 等），这是"敢改"的前提。

### 3.4 verdict 投影（轮转边的数值判读）

`chain_runner` 头注明写：

- `cos-score.json` 在（D4 §一 轮毕意见窗产物·真值源）→ `joint_review_avg_score`：
  - **≥95（含边界）→ verdict='loop_exit'**（EXIT2 sanctioned·**唯一程序自动边**）；
  - <95 → 'continue'。
- `eviction_decision`（evolve|hold 二值）**零消费**=层 2 门域（`cos_decision_gate`/preflight 轮间门消费）——**runner 零复刻 gate 判读**。
- `cos-score.json` 缺（首轮·意见窗未开）→ `manifest.json` run 终态投影：`ok→continue`（轮毕候意见窗）/ `failed|stale→ok=false+err`（fail-closed）。

### 3.5 与周日 payload 十阶段形的关系

| 维度 | 周日正式拍（prod） | 进化环（loop） |
| --- | --- | --- |
| 触发 | TriRMC cron 23:50 硬锚 | fade001-ignite.ts 手动点火 |
| 编排载体 | 十阶段形 payload（bash command 串） | chain_runner.ts（TS 段序驱动） |
| 轮数 | 1 轮 | while 多轮（FUSE=8 上限·仅 test） |
| 终态 | close_cli manifest（ok/failed/stale） | loop 出口（prod/fuse/failed/first_round_pending） |
| 共用 | **同一套十件 CLI**（runtime/cognition/） | **同一套十件 CLI** |

即：**payload 面零 PATCH**（分支 A 纪律）——进化环是新壳，不换芯。

## 四、轮末七席联审（loop 层）

### 4.1 召集形

`loop_joint_review_spawn.py`（runJointReviewHook 子进程调）：

- **七席**：cos/coo/cao/cpo/cto/cho/cfo——每席独立 spawn（dsh headless CLI）。
- **两对象 A/B**：每席对**两个对象**各出 ≥3 个部门维度 → 总计 `dimensions ≥6`/席。
- **职责红线（DP-019）**：**禁创建/修改/删除任何文件**——产物=回复 JSON（席自造产物→上下文爆涨→compaction 风暴→900s 截杀，resume3/4/5 三实证的根因链）。
- **improvements**：≥1 条·五字段齐（见 §五.1）；可为可执行改进或**如实写「本席无改进」条**（title=no-improvement·DP-017 追补）。
- 产物：
  - `run_dir/opinions.json`（schema 2.0.0·七席 opinions·improvements 五字段）；
  - `run_dir/joint-review.json`（schema_version / run_id / objects / dims_count / faces / dimension_table_version / seat_means / comparability）。
- 回滚锚：`LOOP_JOINT_REVIEW=0` 可关；fail-closed：联审败=state 不动+stderr 留痕；幂等：已有待批不重复（DP-014 守卫双修：approved 不挡新联审；pending 仅本 run 短路）。

### 4.2 31 维冻结表 v1（为什么冻结）

- 问题：LLM 每轮**自创维度名** → 跨轮分数不可比。Jaccard 实测 a=0.0%/b=1.5%（resume4 vs resume2）——**尺子每轮换，趋势无意义**。
- 根解①=**维度冻结**：固定维度表，LLM 只打分。
- 表件：`TriCompany/runtime/cognition/fade001-dimensions-v1.json`（version 1.0.0·TC@6f6361f 实锚）：

| 席 | 维数 | object_scope 分布 |
| --- | --- | --- |
| cos | 4 | both 4 |
| coo | 5 | A 3 / B 1 / both 1 |
| cao | 4 | both 4 |
| cpo | 4 | A 1 / B 1 / both 2 |
| cto | 5 | B 1 / both 4 |
| cho | 5 | both 5 |
| cfo | 4 | A 1 / B 1 / both 2 |
| **合计** | **31** | **A 5 / B 4 / both 22** |

- 规则：每席 3-5 维·维度设计依据=**各席部门职能**（非 LLM 随机产出）；联审 prompt 给「本席维度表（id+name+definition）」→ **只对给定维度打分 1-100·禁自创维度**（越表=fail-closed）；输出 schema 强校验 `dimension_id` 必须在表内。
- 版本化：`dimension_table_version` 入 joint-review.json；**同版本 comparability 恒 1.0**（工具自动证实）；**v1→v2 变更=历史分标版本·跨版本不混比**（趋势图注断点）。
- 已知现势：resume9 `dims_count` 27/26（同表打分未全覆盖）——CHO 联审提出「每席对 31 维全部 both 维必打（缺打=显式 skip+理由）」，入 R10 items（cho-op-3），round3 起验 `dims_count=31/31`。

### 4.3 comparability（可比性读数）

- 位置：`joint-review.json` 的 `comparability` 段。
- 实形（resume9）：`{"prev_run":"shift-W48-resume4-…","jaccard_a":0.0,"jaccard_b":0.0,"note":"dimension-name Jaccard vs previous round; analysis only, not in scoring"}`。
- 读法：**它不进分数**（analysis only）——0.0 不是"差"，是"两轮维度名完全不同"的信号（表切换期正常）。表冻结后同版本应恒 1.0；若同版本下掉 1.0=有维度名漂移异常，要查。

### 4.4 A/B 两对象的语义与错配风险（如实注）

- **判级口径（条款面 M3-v2）**：**两对象分立判决·不加总**——A/B 各自过门槛各判；任一不达标=停留原态。
- **对象语义存在两套说法**（这是**已知风险**，教程必注）：
  - 召集信口径（W48 本地七席联审）：**A=周迁移完成质量 / B=协议遵循**；
  - 标尺卷/冻结表时期口径：**A=实现度 / B=迁移质量**（与 resume9 一致）——**与召集信相反**。
  - 圈内处置：R10 任务书草稿 §一「口径统一注」=按对象名称判分+召集字母映射；CAO/CHO 双席示警「两个体系并存=潜在错配源，建议冻结窗统一」；CTO 面勘候。
- **新人记法**：**A/B 是两个"对象"，不是两个"分数口径"；读任何一轮的 A/B 分，先看该轮 objects 字段和 dimension_table_version，别跨版本/跨口径直接比。**
- 聚合：`mean-of-seat-means`（先各席均、再七席均）——`computeJointGrade` 单一源（DP-021）；优先 `seat_means`，缺则由 `faces` 现算。

### 4.5 DP-021 两阶段（达标轮不生成无用 charter）

修复前缺陷：`await runJointReviewHook` 在 `verdict==='loop_exit'` 判级**之前**跑 → 双达标轮仍生成无用 charter。

修法（CTO 规格·a08c0a5 已毕）：

```
阶段1：联审先行 → joint-review.json → computeJointGrade（A/B）
阶段2：bothPass(A/B>90) ?
   是 → 写 charter-skip.json（reason/gate/grade 留痕）→ 不生成 charter（skipped）
   否 → 照现生成器链 → opinions→charter→pending
```

- `JOINT_GRADE_THRESHOLD = 90`（debug 态 bothPass 门槛）。
- **charter-skip.json 不是失败**——是"达标轮无需改造"的正形留痕；resume10 是首个生效轮观察点（达标轮应见 skip 留痕）。
- 守卫不动：DP-014 幂等/跨 run 判重逻辑零改。

## 五、improvements → 生成器 → charter → 呈 CEO 批 → 施工 → 再点火

这是 M7-v2 的完整闭环，逐步拆：

### 5.1 improvements 六字段（意见条目形）

联审席在 opinions 里提 improvement，条目落任务书前必须字段齐：

| # | 字段 | 说明 |
| --- | --- | --- |
| 1 | `opinion_id` | 意见主键（如 R10-CTO-01·席前缀+序号） |
| 2 | `title` | 一行标题 |
| 3 | `target` | 改哪（run-dir 内路径或源码路径） |
| 4 | `change` | 怎么改 |
| 5 | `verify` | 怎么验（可执行判据） |
| 6 | `rollback` | 怎么回 |

- 联审 prompt 面叫「improvements 五字段」（title/target/change/verify/rollback）；进 charter 条目后加 `opinion_id`=**六字段**——两个叫法指同一件事的两面，教程并列注明防混。
- **no-improvement 显式条**（DP-017 追补 1da5242）：本席无改进也必须写一条（title=no-improvement·change=无），**不许静默缺席**——缺席与"无改进"在聚合面不可区分，是假读数家族入口。

### 5.2 生成器（charter_generator.ts·188 行）

- 输入：`opinions.json`（schema_version/run_id/round/opinions[]）。
- 强制面：`opinion_id`+`title`+`target/change/verify/rollback`——**任一条缺=整卷退回人工**（fail-closed，不生成、不静默降级）。
- 输出 `CharterDraft`：`schema_version 1.0.0 / charter_id r<round>-task-<date> / source{run_id,round,opinion_ids} / approver_pending CEO|COS / status pending_approval / items[]`。
- **红线二**：`auto_dispatch` 默认**不置**——只有 CEO 批面显式授予才写 true（脚本层兜死，防误扩大自动面）。
- **产物即 pending_approval 态：生成本身零批准效力。**

### 5.3 呈 CEO 批（M4-v2）

- **M4-v2（CEO 令 2026-11-23）：「下轮任务书 cos 发我审批，不再代批」**——原 M4「多轮 COS 代裁」条**作废**（留沿革）。
- 现形：**COS 只出稿不代批**（卷面+items 清单+批时点位待填·走 notify-mailbox 或直呈 BOD 转）；**批权归 CEO**；原五要件+M2 自证中**仅出稿义务保留**。
- 已代批历史件（c1b4f900e 等）留档不动=历史冻结。
- 边界照 D-86 必回呈六项。
- 实操注意：**M4-v2 前代批的痕迹（approver_pending=COS / APPROVED_COS）在旧件里合法存在**，新人别拿旧件当现制范例。

### 5.4 mount 与下一轮

- debug 态 `continue` 裁决后 → `tryCharterMount` → `pending_charter_ref` 置位、`charter_approval`=`APPROVED_CEO`（或历史 `APPROVED_COS`）→ 拾取面可见。
- 时序（SDE 代取卷实证）：`runJointReviewHook → charter 生成 → mount → 下一轮起跑`——charter 注入在下一轮起跑**之前**，轮 2 消费本 charter（非轮 3）。
- 幂等（DP-014）：同 run 内 pending 已存在=不重复生成；跨 run：approved 态不挡新联审，旧 run 残留 pending 不挡（`charter_run_id` 判重）。

### 5.5 M7-v2 闭环五步

| 步 | 动作 | 责任/形 |
| --- | --- | --- |
| ① | 本轮 A/B 出分 | 联审聚合（COS 汇总） |
| ② | 若未双过 90 → COS 出稿任务书 → **候 CEO 批** | M4-v2：COS 只出稿不代批·**不自动跨过审批步** |
| ③ | 按任务书施工改造 | 派工三步+D-88（DP 取号/runId 签发照役） |
| ④ | 施工毕+自测绿+**试出卷验≥70%** → **自动点火下一轮**（不需逐次请示） | CEO 常驻授权形 |
| ⑤ | 循环至**双>90（test）→双>95（prod）→2026-11-29 正式迁移** | M3-v2 双达标+M6 跨点火累计 |

**自动流转边界**：④自动点火不需请示=常驻授权；②审批步不跨（机制本体项仍回呈 CEO）；点火后读数随报 BOD（知情照役）。

## 六、M1-M9 九条款全景

正身=`w48-migration-joint-review-20261123/cos-loop-spec-gate-update-20261123.md`（文末自载「九条款完备」）：

| 条 | 名称 | 一句话 | 锚 |
| --- | --- | --- | --- |
| **M1** | 迁移轮出题 | 一轮的产出以"出题"为质量基线 | 卷首/轮面 |
| **M2** | 任务书条件 | 未达门槛 → 产生任务书（<95 产生制·**COS 代批已随 M4-v2 作废·出稿义务保留**） | r12 代批卷「M2 自证 73.49<95」 |
| **M3-v2** | 双达标 | debug→test **A>90 且 B>90**；test→prod **A>95 且 B>95**；两对象分立不加总 | 卷 §一 |
| **M4-v2** | 出稿呈 CEO 批 | COS 只出稿不代批（原 M4 代批撤回·留沿革） | 卷 §二 |
| **M5** | 轮循环 | 多轮循环直到 >95；每轮必验 exam.json 在位+两对象全维齐；轮间门件轮毕即落 | 卷 §三 |
| **M6** | 跨点火累计 | 单点火 FUSE 8；8 轮未达=**该次点火收敛**≠进化终止；可再点火续跑（新点火=新 FUSE 窗）；判级只认 A/B | 卷 §三之二 |
| **M7-v2** | 闭环自动流转 | 出分→未双过 90→COS 出稿→候 CEO 批→施工→**自测绿+试出卷≥70% 自动点火**→循环 | 卷 §三之三 |
| **M8** | test 态规则 | 双>90 进 test；连跑 8 轮；8 轮未达双>95 → 退回 debug；计数窗=进 test 清零；回退留痕=趋势线+未达因 | 卷 §三之四 |
| **M9** | FUSE 仅 test 生效 | debug 不适用（审批步=天然节流）；prod 周日拍不受影响 | 卷 §三之五 |

**条款×代码对照**（如 §2.2 所述）：M3-v2/M8 是条款面双对象门槛；flag 边代码现役按 aggregate average——差异如实并列，候 CTO 对齐卷。M4-v2 已由代码 `approver_pending` 默认 `'CEO'` 承接（`charter_generator.ts` 默认 approver=CEO）；M9 的按态分支待对表。

## 七、跨点火累计（M6）与收敛语义（M9）

三个词必须分清（这是新人最易混的）：

| 词 | 含义 | 谁触发 |
| --- | --- | --- |
| **轮（round）** | 一次十段链全跑 + 轮末联审 | loop 体内自动 |
| **点火（ignite）** | 一次 `runLoop` 调用（内含多轮，FUSE=8） | 人/派工面（COS 签号） |
| **进化（evolution）** | 跨点火的累计进程（M6） | 多轮多点火的集合 |

- **FUSE 到 ≠ 进化终止**：8 轮未达=该次点火收敛（保险丝），可再点火续跑；新点火=新一轮 FUSE 计数窗。
- **收敛≠失败**：fuse 出口是设计内出口（熔断停候 CEO），不是故障。
- **判级只认 A/B**：段 7 主观两席分（cos/coo）不混用判级（M6 口径）。
- **门槛维持 90/95**（CEO 裁「维持 90/95」·M3-v2 照役）。

## 八、真实弧线：W48 一日进化实录（教学素材）

这是 loop 第一次真跑的完整谱系（2026-11-23·全部实锚在 `cos-runid-gate-cos-half-20261123.md` §二签发表+`dispatch-ledger-20261123.md`）：

| 轮 | 现象 | 根因/处置 |
| --- | --- | --- |
| loop 首跑（shift-W48-loop-20261123T005158Z） | 轮 1 毕·轮 2 段 5 rc=2 | 契约缺口（DP-013 plan prompt 契约镜像修） |
| resume（033142Z） | 轮 2 钩短路由·联审缺分 | 不沿用原 runId 防污染轮态归因 |
| resume2（035946Z） | 轮 1 联审 7/7 恢复·A/B 43.25/47.56；轮 2 起进程内污染再临 | DP-014 守卫双修 |
| resume3（050813Z） | **轮 1 红停·段 3 900s ETIMEDOUT·rounds_run=0·FUSE 未耗** | 候选=外部并发干扰→**清场确认列硬条件** |
| resume4（053031Z） | 轮 1 毕·debug 裁决门 absent 挂起·A/B 51.88/50.39 | 设计内停点（CTO 代码实证） |
| resume5（073047Z） | 段 3 超时第三例·compaction13 | seat 自造产物→上下文爆涨→compaction 风暴（DP-019） |
| resume6（080638Z） | 段 3 红·max-tokens 16384 截断（真因定谳） | DP-020 拆分生成+精简 |
| resume7（082025Z） | plan 57.5s ✓·exam 挂死>240s→300s 帽杀 | DP-020 追补（exam 读面限定+子超时≤父超时） |
| resume8（084227Z） | 候 SDE 补报（中间态） | DP-020 追补 a+c 生效轮 |
| **resume9（085137Z）** | **全绿：段 3 4.5min/compaction3·A41.04/B50.25·dims31 首验** | **DP-020 终销实证轮** |
| resume10（115623Z） | 已签发候点火 | DP-024 R10 施工四件码面生效轮 |

**九个 resume 里 6 红**（COO 路线图原话）——这段历史的教学价值：

1. **一次修复一次验证**：禁多修叠发 resume（混因=归因失效）；
2. **三面齐才点火**：码面/冒烟面/前置面任缺=候；
3. **红停≠熔断**：resume3 rounds_run=0/FUSE 未耗=红停，不是跑满 8 轮的熔断；
4. **修复要治根不是绕过**：DP-019 治"席自造产物→compaction 风暴"根因（产物只由 stage 写/压缩上限/超时预算），而不是把超时调大；
5. **每一步留锚**：DP-016/019/020/021 全部有 commit/验收卷，事后可复算。

## 九、常见误区与自测

### 9.1 常见误区

| # | 误区 | 正解 |
| --- | --- | --- |
| 1 | 把 FUSE 8 当"进化只能 8 轮" | FUSE=**单次点火**保险丝；跨点火累计（M6）可续跑 |
| 2 | 把 fuse 出口当故障 | 设计内出口（熔断停候 CEO） |
| 3 | 把 charter-skip 当联审失败 | 达标轮无需改造的正形留痕（DP-021） |
| 4 | 以为 COS 还能代批任务书 | M4-v2 已撤：只出稿，批权归 CEO（旧件是历史冻结） |
| 5 | 拿不同轮 A/B 分直接比趋势 | 先看 `dimension_table_version`+`objects`；跨版本不混比（comparability 断点） |
| 6 | 把 comparability 0.0 当低分 | 它是维度名重合度（analysis only·不进分数）；同版本应 1.0 |
| 7 | 把 dims_count 27/26 当"表只有 27 维" | 表=31 维；dims_count=本轮实际打分覆盖数（缺打候 R10 cho-op-3 修） |
| 8 | 以为 test 态每轮也要候 CEO 批 | test 直进（M8 连跑 8 轮）；debug 才逐轮停审批步（M9 语义） |
| 9 | 把 round_count 当本次点火轮数 | round_count=FUSE 计数域（跨点火累计）；rounds=本次点火已跑轮数 |
| 10 | 手动 setFlag 不带 authority_ref | 必载（fail-closed）；唯一程序自动写面=EXIT≥95 边 |

### 9.2 自测

**读代码面**（本机 TriRMC 仓根）：

```
node --import tsx --test test/fade001/round_runner.test.ts test/fade001/chain_runner.test.ts
```

（套件实锚：round 47/47、chain 18/18 于 2026-11-23 各次修形验收；本批教程未重跑，接手以仓内 test 脚本为准。）

**口测三门**（各 30 秒说清即达标）：

1. **轮 vs 点火 vs 进化**三个词的区别（§七 表）；
2. **debug/test/prod 三态的进入条件与停点**（M3-v2/M4-v2/M8/M9）；
3. **A/B 出分到再点火的五步**（M7-v2 闭环表）。

**读卷练习**：打开 `joint-review-resume9-20261123T0939Z.json`，说出 `seat_means`/`comparability`/`dimension_table_version` 三字段各是什么、为什么 comparability 是 0.0 而本轮仍算全绿。

## 使用依据

- loop 代码面（2026-11-23 实读）：`TriRMC/src/fade001/round_runner.ts`（465 行·四态/六边/FUSE/首轮停点/resume/联审钩/DP-021 两阶段）+`chain_runner.ts`（260 行·STAGES/spawn 总窗/P3 灰度/verdict 投影）+`charter_generator.ts`（188 行·五字段+opinion_id/整卷退回/auto_dispatch 红线）+`scripts/fade001-ignite.ts`（入口·--run-id/--checks-json 必载）
- 联审与维度：`TriCompany/runtime/cognition/loop_joint_review_spawn.py`（7 席·dimensions≥6·improvements 五字段·禁文件写 DP-019）+`fade001-dimensions-v1.json`（31 维 v1.0.0）+`runtime/cognition/loop_autoreview.py`（per-seat 评分会话族参考）
- M 条款正身：`TriMetaverse/docs/workflow/operating-records/2026-W48/trees/w48-migration-joint-review-20261123/cos-loop-spec-gate-update-20261123.md`（M1-M9·文末九条款完备）
- 轮末联审召集/31 维/口径：同树 `cto-dimension-freeze-spec-20261123.md`（维度冻结四件）+`cto-m3-aggregation-and-round1-reading-20261123.md`（mean-of-seat-means）+`cao-review-20261123.md`（A/B 语义错配示警）+`.../trees/fade001-evolve-20261123/cos-batch-submission-R10-20261123.md` §一 口径统一注
- charter/mount 时序：`.../trees/fade001-evolve-20261123/sde-charter-delivery-20261123.md`（runJointReviewHook→charter→mount→下轮·5s 时序实证）
- DP 谱系：`.../trees/cos-dispatch-ledger/dispatch-ledger-20261123.md`（DP-009/010/013/014/016/017/019/020/021/024）
- W48 弧线：同 dispatch-ledger +`cos-runid-gate-cos-half-20261123.md` §二签发表 +`coo-r10-chain-stability-95-roadmap-20261123.md`
- 回归门件：`TriCompany/docs/workflow/round-gate-sop-20261123.md`（ceo-ruling 每轮落件·轮末 catch 断言）
- 纪律：D-46/D-47/D-86/D-88/D-15/D-24/D-27 v4
