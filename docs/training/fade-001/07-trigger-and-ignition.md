<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-001/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-001 触发章——点火形态、runId 签发制与点火前四件

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-001/07-trigger-and-ignition.md
- syncMode: source-only
- lastSyncedAt: 卷面时点锚=git commit 时戳（零手打·D-47 增补款正形）

> **补编批（v2.2.0·2026-11-23·CEO 直令「把触发和 loop 也包含进教程」·BOD 转·DP-20261123-025·COS 补号 19:59）**：本篇=触发章新增（①触发形态全景 ②runId 四形与 COS 签发制 ③点火前四件 ④preflight/qualify 双门 ⑤三件前置 ⑥协议段号×实现段号错位如实注）。教程线零触链——纯文档面，不碰 payload/jobs.json/daemon/链面脚本。姊妹篇=[08 loop 章](08-loop-evolution.md)。
>
> **闭环更新批（v2.3.0·2026-11-23）**：DP-026 三如实注闭环（DP-027 落码 5ade74f·48/48+CAO 冻结+CHO 会签）——涉及 08 章 §2.2/§2.3/§4.4 改「已闭环」形；本篇 §六 DP-022 段号对表经四向核**未检出对表卷**，维持「在办」并加闭环核注（详见 §六）。
>
> **DP-022 对表补丁（v2.3.1·2026-11-23）**：CTO 对表卷 **e642f6051** 达面——§六 改「已对表（两轨映射表在卷）」+口诀正名（触发=隐形第 0 道·两轨 1..10 对齐·唯一功能差=段 7）；v2.3.0 核注转沿革留档。

读者：要参与/值守 FADE-001 点火的人——值席、COO/CTO 派工面、SDE 执行面，以及要接手点火链的工程师。
前置：已读 [01 小白版](01-beginner-guide.md) §三十阶段全景（十段链是什么）。
事实基线：2026-11-23 W48 进化环在役（loop 层已接装·点火脚本 `TriRMC/scripts/fade001-ignite.ts` 在盘）。

---

## 〇、培训判断：为什么单开「触发章」

01-06 讲的触发是**一条路**：周日 23:50，河源 TriRMC cron 到点起跑十阶段链（payload 形）。

2026-11-19→11-23 之间，FADE-001 长出了**第二条触发路**——**进化环点火**：不再等周日，人（COO/CTO 派工面）随时可以点火跑一轮，跑完联审出分、按任务书改造、再点火，循环直到达标。这条路带来一整套新概念：

- **runId 四形**（loop/ignite/official/resume）与 **COS 签发制**（没有签发的号，执行席拒绝执行）；
- **点火前四件**（checks 四布尔/清场/门态/试出卷）——缺一件就不许点；
- **双门**（preflight/qualify）从"周日自动跑"的语义，扩展到"每次点火都要过的门"；
- **三件前置**（ceo-ruling continue / charter mount / 号）——debug 态每轮点火前的硬门；
- **协议段号与实现段号错位**（DP-022 在办）——读协议说"段 1=触发"，读代码说"段 1=preflight"，新人在这里最容易懵。

本篇只讲"怎么点得着、点什么、点之前要齐什么"；点着之后**轮怎么转**（round_runner 状态机、FUSE、联审、charter 闭环）在 [08 loop 章](08-loop-evolution.md)。

## 一、触发面全景（先看大图）

### 1.1 两条触发路

| 路 | 谁是"点火人" | 载体 | 典型 runId 形 | 语义 |
| --- | --- | --- | --- | --- |
| **A. 周日正式拍（prod）** | cron（河源 TriRMC） | 十阶段形 payload（周日 23:50 硬锚） | `shift-W47-official-…`（正式拍） | 常规生产迁移，一年 52 次，零人工 |
| **B. 进化环点火（loop）** | COO/CTO 派工面→执行席（SDE） | `fade001-ignite.ts` 点火入口 → round_runner loop 宿主 | `shift-W48-loop-…` / `-ignite-` / `-resumeN-` | 为"把 FADE-001 自己进化到双>95"而多轮跑，随时点火 |

两条路**共用同一套十段链**（chain_runner 逐段调 TriCompany `runtime/cognition/` CLI），差别在"谁触发、跑几轮、轮间做什么"。A 路一轮一终态；B 路一次点火内可连跑多轮（受 FUSE=8 约束，见 08 章）。

### 1.2 触发源五类（协议层视角）

协议正身 `fade-protocol-spec.md` §一 列了触发源：**指令 / registry / codegraph / 文件修改扫描 / 探测**——这是"什么事件可以开启一次 FADE 生命周期"。落到 FADE-001 现役：

- 周日 cron = 定时源（最稳定）；
- 进化环点火 = 指令源（人下令）；
- 迁移器自身的事件/值守探测（齿条③晨检等）是**旁路监督**，不是点火源。

> 教学提醒：触发源（为什么跑）≠ 点火形态（以什么号跑）≠ 门（跑之前查什么）。三层分开记，后文逐层展开。

## 二、runId 四形与 COS 签发制

### 2.1 号形与四形并集

号形（COS 半正身 `cos-runid-gate-cos-half-20261123.md` §1.1）：

```
shift-<Wnn>-<type>-<ts>
```

- `<Wnn>`=**目标周**（如 W48）；
- `<type>`∈ **{loop, ignite, official, resume}** **四形并集**；
  - `loop`=进化迭代轮（实测最常用；历史锚 `shift-W47-loop-20261122T142315Z`）；
  - `official`=正式拍（周日生产迁移）；
  - `ignite`=点火形（补跑/首点）；
  - `resume`=补跑（可带序号，现役谱系已到 `resume10`；存量子号保留不回改）。
- `<ts>`=UTC `YYYYMMDDThhmmssZ`。

CTO 勘正的两点（`cto-runid-gate-form-20261123.md` §六）：

1. type 集是**四形并集**——初提时漏了 `loop`，而 loop 恰恰是最常用形（历史号不可废）；
2. **ts 语义变了**：历史号 ts=**起跑时点**；新制 ts=**签发时点**。**存量号不回改**；起跑时点改由 round_state / run_dir state 承载。签发表里固定列头「ts 语义」就是在防这个歧义。

### 2.2 签发四步（COS 值守面）

| 步 | 动作 | 要点 |
| --- | --- | --- |
| 1 报需求 | COO/CTO 报（轮类型+目标周+目的一行）→ COS | 不许执行席自己编号 |
| 2 去重核 | 查签发表：同 `Wnn+type` 近期已签未用=复核（防双跑） | **同形不重签** |
| 3 签发 | COS 回号（值守面 30min 内）+ 预分配轮内子序号段 `001-099` | 回号即生效 |
| 4 记账 | 入签发表 + 派工台账「runId 签发」列 | 台账正身=`cos-dispatch-ledger` 树 |

**签发表实锚**（截至 2026-11-23 19:56）：ignite 1 笔 / loop 1 笔 / resume 9 笔（resume～resume10，含 1 笔已签发候点火）——全表见 `cos-runid-gate-cos-half-20261123.md` §二。

### 2.3 两级粒度与门号判据

- **有轮的活**：轮级 runId 为根 + 子派单 `<runId>-DP-<NNN>`（NNN 在签发时预分配段内按序取）——**轮内任务不另取 DP**。
- **无轮的活**：`DP-YYYYMMDD-NNN`（现制照行）。
- **两侧皆门号**：有轮用 runId / 无轮用 DP——**任一具备即合规；无门号拒绝执行**（D-88「无号不认」的自然扩读；纪律册文字修订归 CAO，本卷提请中）。

为什么两级：一轮多席多派单（七席联审=7 派单），一号到底辨不清责任单元；两级让「回执归属+轮关联」兼得。

### 2.4 四不变量与落地面

| 不变量 | 落地形 |
| --- | --- |
| 唯一 | COS 签发（UTC 时戳+周号+轮类型）+ 签发前去重核 |
| 可追溯 | runId ↔ 签发表 ↔ 派单号 ↔ 回执双落 ↔ run_dir 产物 |
| 关联 | run_dir 命名用 runId；链段产物落 run_dir；trend 行挂 runId |
| 恢复锚 | runId → run_dir → round_state（恢复定位） |

**已落地/未落地如实注**：链层贯穿=已有（`chain_runner.ts` ChainParams.runId → 各段 `--run-id`）；轮层贯穿=DP-009（#16）施工毕（TriRMC commit 5d0c581，`RunnerState.run_id` 字段+round_state 持久化）——「一号贯穿」自 DP-009 起成立；`fade001-ignite.ts` L58 `runId: req('run-id')` 为**外部注入式**（缺即拒·零自铸），这是「COS 签发→点火传号」零代码改动可行的实证。

## 三、点火前四件（缺一件=不许点）

> 术语注：「点火前四件」是 W48 进化环实操中收敛出的检查簇（COO 路线图「三面齐才点火」+R10 批「点火前四件照例」），不是协议条文；教程按实操清单讲，条款原文见后列真源。

### 3.1 第一件：四布尔 checks 值席签（activation_gate）

`activation_gate.py`（TriCompany `runtime/cognition/`·版本 1.0.0）是**挡位边**判据件：值席在起跑前采集四个布尔，`--checks-json` 喂入，gate 判 `ready|blocked`。

| 键 | 含义 | 判读基准 |
| --- | --- | --- |
| `A1_d1_d5_done` | 改造线锚：D1-D5 划项完成 | 划项状态（调用面采集） |
| `A2_whitebox_zero_new_red` | 白盒面：案族全绿+全树**零新增红** | 判读基准=零新增红，**不是全绿**（既有预存红如实定谳·禁全绿冒充） |
| `A3_guard_anchors_ok` | 护栏面：四护栏常位验证锚齐 | 与 D7 共享读数·单向引用非环 |
| `A4_equivalence_and_zero_touch` | 语义面：两态等价性锚在卷+铁律域零触 | 等价性证据在卷 |

要点：

- **值席核后签非抄**（他席零代笔）——签值卷正身形：`{"A1…":true,…}` 四键+逐项判定基准（实锚 `cos-checks-json-签值卷-20261123.md`）。
- schema 白名单闭：A1-A4 + 轮面可选键（`first_round_complete`/`release_ref`/`round_reading`），**白名单外键=ValueError 拒**（防死锁自指：D6/D7 自身条目键进不来）。
- 缺键/值非布尔=契约面 fail-fast；运行面 never raises 保守 dict。
- gate=blocked → runLoop 直接 failed 出口（`rounds_run=0`·fail-closed 零静默起跑）。

### 3.2 第二件：清场确认

- 形：**dsh / py / ignite 三类进程零 + 瞬态身份白**（无残留孤儿进程冒名）。
- 来历：`resume3` 轮 1 红停=段 3 900s ETIMEDOUT，根因候选=**外部验证并发干扰**（铁证在案未清）→ 自此 `resume4` 起「清场确认」列为点火**前置硬条件**。
- 实操：点火令发出前由执行面自证清场读数，COO 双确认。

### 3.3 第三件：门态（ceo-ruling.json + job 面）

轮间门件 SOP 正身：`TriCompany/docs/workflow/round-gate-sop-20261123.md`（COO 批 3 门件施工·#10）。

- 文件位：`<run_dir>/ceo-ruling.json`（该轮 runs 目录内）。
- schema 四键（枚举严守）：

```json
{"decision":"continue|terminate","ruling_ref":"<裁决卷 ref>","signed_at":"<date 现查原值 UTC Z>","note":"<一行语境注>"}
```

- `continue`=ok True 本轮照跑（缺省形·常规轮毕一律 continue）；`terminate`=ok False job 停用 exit 5 后轮不跑（**仅停用裁决面用·禁误落**——SDE 源码实读锚）。
- 落件人=值席 COS（经 BOD 通道·sha256sum 留痕+读回原样双回执）；**轮毕即落**，不等下拍前（下拍前只复核）。
- job 面复核：`enabled=True` + `nextRunAtMs` 在位=门就绪；若 `enabled=False`=按 SDE/COO 指引恢复，值席先报读数不擅改。
- 负例实证：`shift-W48-ignite-20261122T175743Z` 缺 ceo-ruling.json → 拍 `exit 4`（ⓐ 缺件即拦）；W46 面曾误落 terminate → 覆盖重写 continue 更正（sha 留痕）。

### 3.4 第四件：试出卷验 ≥70%

- 为什么：点火前没有新卷可判，就用**段 3 单独试出卷**验证"出题面能不能被机器判"——避免白跑全链（一轮 77min 级成本）。
- 形：`plan_skill_spawn` 单独跑一次（独立 run_dir·产 `exam.json`）。
- 判据（CTO 裁 `cto-runid-gate-form-20261123.md` §七裁2）：**可判率 =（pass+fail）/objective 总数 ≥ 70%**（skipped ≤30%）且 **objective 条数 ≥3**；用 `score_cli` 的 `evaluate_exam_objective` 直接读数。
- 实锚：DP-010 试出卷 6/6=100%（≥70% 达标·commit 92cebe2）；resume9 轮 exam_objective 8/8 pass。
- 效力边界（如实注）：试出卷只验**出题可判性**（断言能被机判），**不验断言真实性效度**（同轮产物自证）；真实判分在点火轮段 6 自动执行。

### 3.5 三面齐才点火

COO 稳定化路线图（`coo-r10-chain-stability-95-roadmap-20261123.md`）：

1. **一次修复一次验证**：每个修复件（码/契约/prompt）落码后单独验证（试出卷/冒烟/单测），**绿才进下一件**——禁「多修叠发 resume」；
2. **三面齐**：码面（commit+推+产线 pull 验）+ 冒烟面（--help/空跑/单测）+ 前置面（号/清场/门态/预算）——**任一面缺=候**。

## 四、双门：preflight 与 qualify（各查什么）

### 4.1 preflight——「这一拍该不该跑」（触发侧闸）

`preflight.py`（版本 1.0.0）五断言：

| # | 断言 | 查什么 | 拦的后果 |
| --- | --- | --- | --- |
| 1 | 算周双闸（γ 主闸） | 触发日必须**周日**（明天=周一边界）+ 三值重算比对 | rc=2 本拍不执行 |
| 2 | hostname 断言 | `socket.gethostname()` 对配置常数（防 job 误落他机） | rc=2 |
| 3 | 无进行中 git 操作 | MERGE_HEAD/rebase 探针 + `git status --porcelain` 对**迁移面路径**（operating-records）非空即拦 | rc=2 |
| 4 | 8710 healthz | 载体 daemon 活性探针（ok!=true 即拦） | rc=2 |
| 5 | 分叉预检 | 复用 `weekly_plane_shift._preflight_bare_sync`（单点真源防两处分叉） | rc=3 双址 blocking 告警 |

**退出码语义**：0=全过交棒 / 2=断言族拦（本拍不执行）/ 3=分叉拦 / 4=保留（告警由 bash 链尾承担·防双重告警）。

**loop-window 豁免（进化环专用）**：`--loop-window` 旗标、`LOOP_WINDOW=1` env 或 `<TRICO_LOOP_MARKER_DIR>/loop-window.marker` 在 → **周日硬门豁免**，卷面记 `sunday_gate: "exempted(loop)"` + `run_dir_week_note`（loop-run 实际时点注记·归属周按此时点）。法源=CEO 23:55 令。所以进化环可以在任何一天点火，不违"周日才迁移"的语义——豁免是显式留痕的，不是偷偷绕。

### 4.2 qualify——「这个环境有没有资格跑」（执行侧闸）

`qualify.py` 五资格断言：

| # | 断言 | 查什么 | 为什么 |
| --- | --- | --- | --- |
| 1 | 执行身份 | `getpass.getuser()` 对期望值（默认 `fleet`；env `TRICO_QUALIFY_EXPECTED_USER`；`--skip-identity` 为 dev escape） | 非 fleet 跑=dubious ownership 前兆+notify 读不到→告警链全 render_only 静默死 |
| 2 | run dir 可写 | RUN_DIR probe 写+删 | 落卷面不可写=全链读数哑卷 |
| 3 | git 身份在位 | `git config user.name/user.email` 非空（值面零回显只判 nonempty） | 迁移 commit 身份 |
| 4 | 告警凭据在位 | notify config（`~/.trimetaverse/notify.json` smtp.host/pass）或 env 回退 nonempty | 告警链资格前验：凭据缺失=拦截时告警发不出=静默死 |
| 5 | 磁头余量 | 卷剩余 ≥ `MIN_FREE_MB`（默认 500·env `TRICO_QUALIFY_MIN_FREE_MB`） | 磁盘满=半路炸 |

退出码：0=五断言全过交棒 / 2=任一资格拦（qualify.json 落卷·trap 告警外发）。

### 4.3 三层判据族分野（别混）

`round_runner.ts` / `chain_runner.ts` 头注把三层分清：

| 层 | 判据件 | 判什么 | 频次 |
| --- | --- | --- | --- |
| **挡位边** | `activation_gate.py` | 值席手动形态→自动挡形态（一次性切换·A1-A4） | 一次性 |
| **轮转边** | `round_runner.ts`（EXIT≥95） | 每轮判是否升级 prod | 每轮 |
| **质量边** | Close Skill（retry<90） | 轮毕质量裁决 | 轮毕 |

三件**零消费对方产物、零分支交叠**（CTO `cto-d6d7-activation-ns9-survey` §一）：gate 不判 EXIT，EXIT 不判挡位。preflight/qualify 是**每拍门**，activation_gate 是**挡位激活门**——新人最容易把三者当一件事，记住"一次性/每拍/每轮"三个频次就分开了。

## 五、三件前置：ceo-ruling continue / mount / 号

这是 **debug 态每轮点火**要齐的三件（test 态直进不候裁决，见 08 章）：

| # | 前置 | 缺了会怎样 | 真源锚 |
| --- | --- | --- | --- |
| 1 | **ceo-ruling.json = continue** | 缺件=拍 exit 4（W48 ignite 负例）；terminate=ok False job 停用 exit 5 | `round-gate-sop-20261123.md` §一 |
| 2 | **charter mount**（任务书已挂载） | 未挂载/未批=`charter_approval` 非 APPROVED_* → 不拾取（auto_dispatch 默认不置·红线二） | `round_runner.ts` `tryCharterMount`/DP-014 守卫双修 |
| 3 | **号**（COS 签发 runId） | 无号=执行席拒绝执行（launcher `runId: req('run-id')` 必载 fail-closed） | `fade001-ignite.ts` L58+COS 签发表 |

**mount 的时序**（SDE 代取卷实证）：`runJointReviewHook → charter 生成 → mount → 下一轮起跑`——charter mtime 与轮 2 首段起跑差 5s，判"轮 2 消费本 charter·时序无错位"。挂载后 `pending_charter_ref` 置位、`charter_approval` 从 `CEO`（待批）→`APPROVED_CEO`（已批）。

> 三件的关系：**号=通行证；ceo-ruling=放行令；mount=弹药**。debug 态每轮都要齐；test 态（连续进化）只需要号+门态，不需逐轮候裁决（M7/M8）。

## 六、协议段号 × 实现段号对表（DP-022 已对表·两轨映射在卷）

> **闭环注（v2.3.1·2026-11-23）**：**已对表（两轨映射表在卷）**——CTO 卷 `cto-dp022-stage-number-parity-20261123.md`（commit **e642f6051**·sg 在链）。三要点：
> ①**两轨并列**：协议轨（教程 01 v2.0.0 十阶段：preflight..notify_done）+实现轨（chain_runner STAGES·5ade74f 实读 10 段）——**1-6/8-10 段两轨同名对齐**（段 3/8 的 spawn 形切换=形态切换·段号不变）。
> ②**唯一功能差=段 7**：协议 7=`score_rubric.py`（评分规则展示·report 透明度步）↔实现 7=`score_skill`（spawn 两席主观判分·score-skill.json）——**功能演进差（非编号错）**；正名=实现段 7 称「score_skill（段 7 演进面）」·协议 7 注「已并入评分面」（rubric 功能现内嵌 score_cli/spawn prompt 面·未单步落地）。
> ③**口诀正名**：**触发=隐形第 0 道（链前·非段 1）**⇒ 两轨 1..10 对齐；旧「段 1=触发」表述=**历史读法·引用须加注**。
> **沿革**：v2.3.0 曾记「四向核未检出对表卷·维持在办」（核证全文见树施工卷 `rdt-dp025-tutorial-v230-closure-20261123.md`）；v2.3.1 随 CTO 卷达面改「已对表」。零行为变更（对表非施工）。

这是本篇必须单列的一段——**新人读协议和读代码会对不上号**：

- **协议生命周期**（`fade-protocol-spec.md` §一）：任务说明书拟定与投送=**前置输入**；**十段计数自「事件触发/登记」起算**——即**协议段 1=事件触发/登记**，随后才是 Qualify→Plan→DCE→Verify→Score CLI→Score Skill→Close Skill→Close CLI→终态；
- **链实现**（`runtime/cognition/` 十件 CLI）：**段 1=preflight**（"该不该跑"）→ qualify → plan_scope → dce_steps → verify → score_cli → score_rubric → close_skill → close_cli → notify_done。

即：**协议的"触发/登记"段，在实现里被拆成了 payload 触发面+preflight（+qualify）双门**；协议段号与实现段号**整体错位**。

- **处置状态**：**DP-20261123-022 已对表**——CTO 卷 `cto-dp022-stage-number-parity-20261123.md`（e642f6051·两轨并列表+映射裁定+口诀正名），**零行为变更**（对表非施工；代码注释口径注候 FSD 顺手·非必须）。
- **教程口径（v2.3.1 正名）**：本教程族用**实现段号**（preflight…notify_done=段 1-10），与协议轨 **1-6/8-10 同名对齐**；**触发=隐形第 0 道（链前·非段 1）**；唯一差异=**段 7**（协议 rubric 展示↔实现 score_skill 演进面）。旧「段 1=触发」表述=历史读法·引用须加注。
- **记忆口诀（正名后）**：**"触发是第 0 道，段 1-10 两轨同名；只有段 7 是演进面"**——旧口诀「协议数触发，实现数 preflight」作历史读法留档。

## 七、最小体验与常见误区

### 7.1 最小体验（只读·安全）

在 TriCompany 仓根（沙箱/测试根，**不碰真平面**）：

```
# 1) 门件判据件自测（纯函数·零写面）
python -c "import json;print(json.dumps({'A1_d1_d5_done':True,'A2_whitebox_zero_new_red':True,'A3_guard_anchors_ok':True,'A4_equivalence_and_zero_touch':True}))" > /tmp/checks.json
python -m runtime.cognition.activation_gate --checks-json "$(cat /tmp/checks.json)"
```

期望：输出 `gate: ready`（或等价判读字段）；把任一键改 `false` → `blocked`。想试白名单拒绝：多塞一个 `D6_done` 键 → ValueError（防死锁自指）。

```
# 2) preflight 只读演练形（测试根·不带 --sync）
python -m runtime.cognition.preflight --from W47 --to W48 --start-date 2026-11-23
```

**验证标准**：能说出"四布尔各自判什么""缺一件会怎么拦""loop-window 豁免后卷面长什么样（`sunday_gate: exempted(loop)`）"——触发章毕业。

### 7.2 常见误区

| # | 误区 | 正解 |
| --- | --- | --- |
| 1 | 把 `resumeN` 当成新的轮类型 | 四形=loop/ignite/official/resume；`resumeN` 是 resume 形的存量子号（resume～resume10） |
| 2 | 把 runId 的 ts 当起跑时点 | 新制 ts=**签发时点**；起跑时点看 round_state/run_dir state；存量号不回改 |
| 3 | 以为执行席可以自己编号 | 无 COS 签发号=拒绝执行（D-88 扩读·两侧皆门号） |
| 4 | 以为进化环点火违"周日才迁移" | `--loop-window`/`LOOP_WINDOW=1`/marker → `sunday_gate: exempted(loop)` 显式豁免留痕 |
| 5 | 把 `activation_gate blocked` 当故障 | 前置未齐=设计内 fail-closed（rounds_run=0 出口），不是链坏 |
| 6 | 把三件（gate/ceo-ruling/号）混成一件 | 频次不同：gate=一次性挡位边；ceo-ruling=每轮门件；号=每次签发 |
| 7 | 读段号时把触发算成段 1 | **触发=隐形第 0 道（链前·非段 1）**；两轨 1..10 同名对齐；唯一功能差=段 7（协议 rubric 展示↔实现 score_skill 演进面）。旧「段 1=触发」=历史读法·引用须加注（DP-022 对表卷 e642f6051） |

## 使用依据

- runId 四形/签发制：`TriMetaverse/docs/workflow/operating-records/2026-W48/trees/fade001-evolve-20261123/cos-runid-gate-cos-half-20261123.md`（COS 半正身）+同目录 `cto-runid-gate-form-20261123.md`（技术形正身·§零可行性实证/§一四问/§二四不变量/§六两点勘正/§七试出卷/§八判读达成）
- 门件 SOP：`TriCompany/docs/workflow/round-gate-sop-20261123.md`（#10 ceo-ruling 条款+schema+负例锚三件）
- 四布尔 checks：`TriCompany/runtime/cognition/activation_gate.py` 头注（版本 1.0.0·A1-A4 白名单/防死锁自指/知情停点语义）+值席签值卷 `.../trees/bod-fade001-sprint-plan-20261120/cos-checks-json-签值卷-20261123.md`
- 双门：`TriCompany/runtime/cognition/preflight.py`（版本 1.0.0·五断言+退出码+loop-window 豁免）+`qualify.py`（五资格断言）
- 点火入口与轮层落地面：`TriRMC/scripts/fade001-ignite.ts`（L58 `runId: req('run-id')` 必载）+`TriRMC/src/fade001/round_runner.ts`（RunnerState.run_id / probeActivationGate / first_round_pending）
- 清场前置：`.../trees/cos-dispatch-ledger/dispatch-ledger-20261123.md`（resume3 红停记·dsh/py/ignite 三零+瞬态身份白）+`.../trees/fade001-evolve-20261123/coo-r10-chain-stability-95-roadmap-20261123.md`（一次修复一次验证·三面齐才点火）
- DP 谱系与段号错位：同 dispatch-ledger §一 DP-016/019/020/021/022/024/025 段
- 协议生命周期段表：`TriCompany/docs/engineering/fade-protocol-spec.md` §一（十段计数自事件触发/登记起算）
- 纪律：D-88（门号）、D-46（密值零回显）、D-47（时刻制）、D-02（cron state）
