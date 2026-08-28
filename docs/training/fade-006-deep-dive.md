# FADE-006 执行面自动拾取深度教程——全体系新标准首例压轴篇

> - sourceOfTruth：本教程为培训材料，不是事实裁决；一切事实以文中所引真源为准
> - 培训真源：`TriCompany/docs/training/`、`TriMetaverse/docs/training/`（本篇落点）
> - 实例真源：`D:/Code/ai/TriCompany/docs/engineering/fade-registry.md`（FADE-006 条目，v2.1）
> - 规范真源：`D:/Code/ai/TriCompany/docs/engineering/fade-protocol-spec.md`（v2.0.3）＋ `D:/Code/ai/TriMetaverse/docs/execution/fade-006-execution-autopick-spec.md`
> - 读者：技术研发新人（目标是能接手编排层代码、fade 工具族与树运维）
> - 成熟度：FADE 完整实例标准档（2026-08-28 LG-008 升格；首评 80 冻结＋增评 91 PASS 双轨在册）
> - 本篇定位：七篇培训压轴。FADE-006 是全体系**新标准首例**——第一个在 v2.0.0 协议立法**之后**出生并入册的实例，也是**段-实现映射表的首行填制者**。学会它，后面的 FADE-007 等实例都按它的骨架长。

---

## 〇、培训判断与学习路径

### 0.1 培训判断

读这篇教程之前，你需要三个先修心智模型，缺一个本篇读起来都会飘：

1. **协议与实例分层**：FADE 是协议本体（管每段的"不变量"），FADE-XXX 是实例（自己选"载体"）。这句话出自 `fade-protocol-spec.md` §一（分层总纲）。协议不关心你的 run 叫不叫 runId，只要求登记段满足四不变量。
2. **智能与确定性分离**：Agent 负责发现、规划、语义裁决（Skill）；CLI 负责执行、校验、终态写入（确定性）。FADE-006 的特殊性在于：它的 DCE 段执行体是 **CC 编排会话**（一个 agent 会话），所以协议给了它一条"降级合同"（§2.8 细则 4），这是全体系第一次大规模用这条合同。
3. **审计即第一公民**：本实例的每一个动作都要求"能指到 commit 或 hash"。retrospective §九的原话是：006 证明"逐段可指 hash"的实然形态。

### 0.2 学习路径（先读什么、后读什么、每步怎么验证）

| 序 | 读什么 | 路径 | 验证方式（做得到才算过） |
| --- | --- | --- | --- |
| 1 | 协议 §一 + §2.5/§2.6/§2.7/§2.8 | `TriCompany/docs/engineering/fade-protocol-spec.md` | 不看书面复述十段生命周期与登记段四不变量 |
| 2 | 实例规范全文 | `TriMetaverse/docs/execution/fade-006-execution-autopick-spec.md` | 默写 §二 六步流程表 |
| 3 | 管线设计 §二/§八/§九 | `TriMetaverse/docs/execution/2026-08-26/fade-pipeline-design.md` | 手画 §二 触发拓扑图，说出 hook 快/cron 慢两通道的分工 |
| 4 | 登记册 FADE-006 条目＋映射表 | `TriCompany/docs/engineering/fade-registry.md` :134-170 | 逐行对照本教程第四节，能指出每行锚在哪个文件 |
| 5 | 编排层源码 | `TriCompany/runtime/cognition/orchestrate_tick.py`（全 489 行） | 指出三重门、O_EXCL 锁、spawn 白名单、harvest-rc 各在哪几行 |
| 6 | 工具族四件 | `TriMetaverse/scripts/fade/`（`_fadehash.py`/`seal-materials.py`/`node-report-check.py`/`run-root.py`） | 每件说清退出码语义与守护的不变量 |
| 7 | 树实态 | `TriMetaverse/docs/workflow/operating-records/2026-W35/trees/trilc-lineage-merge/` | 解读 `run-root.json` 的 initialRoot/root/recompute_history 三者关系 |
| 8 | 评分三卷 | `TriCompany/docs/engineering/fade-papers/FADE-006-*.json` | 手工复算 80 与 91 两个总分 |

---

## 一、先讲大的结果：FADE-006 解决了什么、在全局里的位置

### 1.1 一句话

把"任何符合配方形状的任务包"（计划文档＋树注册）从"人写完计划还要人来推着做"升级为：**落盘即入队、双通道自动拾取、自治执行到收口、材料全程防篡改、故障分层取证自愈**（实例规范 §一原话）。

### 1.2 全局位置：为什么说它是"新标准首例"

`fade-instances-retrospective.md` §一 有一张架构期对照表，结论一行：**006 是唯一在完整目标架构（四模块全栈期）下出生的实例**。001 周平面迁移没有面概念，002 发布域没有编排层，003 共学周记靠手动触发，004 员工域是 HTTP 链。它们都是"前标准期实例"，按 CEO 裁定不追溯降格但要补课；而 006 出生时，m/r 面路由、枢纽镜像、卷封制、编排 spawn 已经全部就位。

更重要的一层：006 的运行期（2026-08-26/27）**早于** §2.7 节点收口报告（v1.3.0，08-27 立法）和 §2.8 段-实现绑定（v1.4.0，08-27 立法）。这两部法律就是从 006 的实战缺口里反向立法出来的——所以 006 首评只有 80 分卡线：立法后件按"评分仅采信运行期工件"如实低计。此后它又成为第一个走完"增评 91 → 升格标准档"全流程的样本。学 006，等于把整个 FADE 立法史走了一遍。

### 1.3 关键数字速览（全部可溯源，出处见第六节）

| 数字 | 值 | 一句话含义 |
| --- | --- | --- |
| 首评 / 增评 | PASS 80/100（冻结）→ PASS 91/100 | 双轨评分，不溯及既往 |
| P0 战役 | 八实例九项 P0 全修复 | 2026-08-26/27 首个完整运行 |
| 战役快照 root | `40ee6f8ce950ad…84af5`（完整值见 `p0-fix-and-trilc-merge-plan.md` :118） | 战役级 Merkle root 首演 |
| 单 run root | 初算 `c841f337…18b88` → 现行 `c4147085…11d5b` | run-root v2 schema 实态（见 7.3 节弧线） |
| 触发通道 | hook 秒级（trigger=hook）＋ cron :18/:48（trigger=cron） | AC-4 受控实验证明 cron 可独立拾取 |
| 节点报告 | TM-1/TM-2 两份，node-report-check FAIL 0/2 → PASS 2/2 | 校验器首战弧线，如实入卷 |

---

## 二、理论底座：十段协议与两部关键立法（先讲协议，再讲实例）

### 2.1 十段生命周期

`fade-protocol-spec.md` §一（:65-77）的生命周期图，翻译成培训语言：

```text
任务说明书拟定与投送（前置输入，不计入十段）
-> 事件触发 -> 登记（锚定运行标识） -> Qualify（机械准入门）
-> Plan Skill（实例化点：协议在此落入 FADE-006）
-> DCE（确定性执行段） -> Verify CLI（可选）
-> Score CLI（覆盖遗漏检测） -> Score Skill（语义评分）
-> Close Skill（语义裁决） -> Close CLI（终态写入）
-> APPROVED | FROZEN | ESCALATED | RETRY
```

三个最容易读错的地方：① 任务说明书是**前置输入**，十段计数从事件触发起算（:79 计数注解）；② Verify 是**可选段**，006 就没启用（见 4.6 节）；③ "DCE 只是确定性执行段，不等于 FADE"（:84）。

### 2.2 §2.7 节点收口报告：006 的实战缺口变成的法律

出处就写在法条里：spec :217 "出处：FADE-006 执行面自动拾取实例（P0 战役八实例）暴露的过程黑箱缺口"。它规定多节点树的**每个节点**完成时必须在树目录落 `reports/node-<NODE-ID>.md`，必备十字段（:202-215）——nodeId/agent、起止时刻（UTC Z）、基线 commit、触发来源、动作序列表、工件清单、门禁结果、异常与处置、断点交接、使用依据。两大职能：**断电恢复**（树状态给"到哪一步"，报告给"那一步内部发生了什么"）＋**审计**（杜绝过程黑箱）。

v1.4.1 联审又加了三颗牙（:219-223）：**状态翻转前置门**（置 done 前必须跑 `node-report-check`，exit≠0 不得翻转）＋**编排层收口复跑**（双门）；报告内嵌 ```json fenced 块承载**机读核心九键**（nodeId/agent/startedAt/finishedAt/baselineCommit/trigger/actions/artifacts/gateResults）；战役 Merkle root 快照范围**纳入 reports/** 目录。

### 2.3 §2.8 段合同与实现绑定：映射表的立法依据

一句话：**协议管不变量，实例管载体**（:227）。十段合同速写表（:236-249）里，登记段的四不变量是全协议最硬的一句——**唯一性 / 去重性 / 关联性 / 恢复锚**（:241）。

细则 1-10 全文在 :255-266，本篇用到其中六条：

- **细则 2**：实例入册附「段-实现映射表」，最小 schema 三字段：`段名 / 载体类型与形态 / 不变量满足证据引用`（CPO-F11：以最小交付替代"schema 化"宣称）。
- **细则 4（降级合同）**：agent 会话承载 DCE 时，DCE 不变量降级为"**先写后报 ＋ 原子即提交 ＋ §2.7 节点收口报告**即产物合同"，envelope 义务仅及于会话内调用的确定性 CLI——FADE-006 即此形态（:260）。
- **细则 6（判例收口）**：runId 单一字段非必须，等价聚合键必须；被评分卷宗引用的 run 必须可被单一显式标识引用；跨实例战役强制战役级关联键（Merkle root 惯例正式化，:262）。
- **细则 7（齿条）**：入册映射表须附**机器可复算检查或工件引用**式的证据（7a）；周检做"声明载体 vs 实际载体"漂移核对（7b）。
- **细则 8（006 复审触发）**：§2.7/§2.8 反向自 006，而 006 首评 80 卡线——补评若暴露**结构性缺陷**（非扣分修补），两节强制回联审复审。增评 91 的结论是"无结构性缺陷 → 复审触发解除"（增评 score 卷 notes :121）。
- **细则 10（立法完成度）**：接线＋实测才算立法完成；未接线的法条一律标注"纸面法"入清单；**不溯及既往**——已强制法不溯及生效前的 run，评分冻结不追改，实例合规由现行法下新增 run 评分背书（修正 2，:266）。

### 2.4 为什么这样设计

协议把"不变量"和"载体"拆开，是因为六实例同段异构（登记段就有显式 runId / manifest / registry 三元组 / jobs.json 四种载体）曾被质疑"谁不合规"。裁定是：都不违反，缺的是明文判据。于是映射表成为入册的标准件——006 是**第一行**按这个格式填的样本，第九节我们专门讲"怎么写"。

---

## 三、最小闭环 MVP：用 trilc-lineage-merge 走一遍完整 run

retrospective §九（:95）指定 trilc-lineage-merge 为正面样板："卷封制首试点，FADE-006 管线延续运行中工件最完整的一次单树生命周期"。先别管代码，看一次 run 的输入→处理→输出→验证闭环。以下时序全部取自树目录实态文件。

**F1 铸计划（08-27 凌晨）**：白班排期文档 `docs/execution/2026-08-27/p0-fix-and-trilc-merge-plan.md` 落盘，§一 列九项 P0，§二 列 TriLC 双线合并方案。它就是本次 run 的"任务说明书"（协议 ：79 的 FADE-006 实例形态=计划文档）。

**F2 拆树封卷（08-27 14:34Z）**：树 `trees/trilc-lineage-merge/tree-op.json` 注册，`seal-materials.py --attach` 预封两份 sourceMaterials——计划文档 raw hash `668d30a3…`（:35）＋实例规范 `3e412542…`（:44），recordedAt `2026-08-27T14:34:44Z`（:38）。这是**卷封制首个试点**（管线设计 §9.5 :155 明文指定）。

**触发与 Qualify（08-27 白班）**：这棵树 `domainRouting=local-executable`（:6）——服务端三重门**故意不拾取**它（notes :27："提交甄别必须在本机做"）。触发权威=CEO 开窗令，执行体=本地 TriMLC 会话。开工第一动作=验卷：`seal-materials --verify` 退出码 0 方可开卷。

**DCE（14:36Z-15:4xZ）**：TM-1（甄别重放，14:36Z-15:02Z）：三线盘点（local=gh=8ad6d5c｜sg=876d21e｜canonical=ba32bc7）→ 甄别 28 提交，排除 1 个旧 TC-s1 草案、保留 27 → backup 分支建立 → cherry-pick 27，唯一冲突在 180cfbf（QA stub 双 env，并集解）。TM-2（门禁＋单线化，15:02Z-15:40Z）：tsc 首跑 TS2300×6 → 修正案 `44e3843` → roster-gating 套件适配 `ff2f970` → 复门 **tsc 全清＋npm test 585 pass/1 fail**（唯一失败=HS-3 预置 tui 债，零新增）→ dev 单线化双远端推平。以上每一步的"时刻｜动作｜commit"都落在 `reports/node-TM-1.md` / `node-TM-2.md` 的动作序列表里。

**Score（08-28 凌晨）**：增评卷按 §2.6 重建：Score CLI 确定性覆盖检查＋Score Skill 两项重计语义评定（详见第八节）。

**Close（08-28 00:0x-00:2x＋08）**：收口时发现封卷后计划文档合法演进（追加 §四对账节，10462B→11696B）——**§9.3(a) 授权修订裁决真实触发**：豁免放行＋按当前版本重封留痕（tree-op notes :30，`resealed_after_adjudication: 2026-08-27T15:59:39Z`）。终态 done commit `c6f969de` 双远端（retrospective :109），heyuan 生产四仓切线决策入 merge-log。

**验证闭环**：你今天就能复验——读 `tree-op.json` 看到 status=done 与卷封字段；读两份 node 报告看到十字段＋机读九键；读 `reports/run-root.json` 看到完整性基线。输入（封卷 hash）、处理（27+2 提交链）、输出（done＋root）、验证（verify=0＋585/1）四环齐闭。

---

## 四、本篇核心：协议十段在 FADE-006 的逐段落地（映射表逐行解读）

登记册 v2.1（2026-08-28）为 FADE-006 填制了全体系**第一张**段-实现映射表（`fade-registry.md` :155-168）。先立三条**格式律**（表头自带一句："证据引用一律为锚非散文"）：

1. **证据必须是锚**——jq 命令、file:line、hash、退出码，不是形容词；
2. **空缺如实**——Verify 行直接写"可选段未启用（诚实空缺）"，不凑段；
3. **部分接线用三态声明**——"已接线 / 核验中（附解除条件）/ 未启用"，不许含糊。

下面逐行拆十段。每段给：载体类型 → 不变量怎么满足（证据锚）→ 为什么这样设计。

### 4.1 事件触发——双载体：归因锚＋触发机制

映射表原文：*"归因锚载体（前置输入）：任务说明书程序化投送；触发机制载体：post-receive hook 秒级派 tick＋trimc cron :18/:48 兜底"*。证据锚：计划文档封卷 hash（tree-op sourceMaterials 字段）＋ fade-hook.log tick 行（trigger 字段可归因）。

落地形态在 `orchestrate_tick.py`：`--trigger` 参数三选一 `cron|hook|manual`（:348-349），spawn 时写入 registry ticks 条目（:482）。**为什么双通道**：hook 快通道秒级但不冗余可靠（hook 被禁用/挂掉就盲），cron 慢通道兜底保证"最迟一个周期必拾取"；两者都靠三重门收敛，同一时刻只会 spawn 一次（管线设计 §四.1 :63）。**AC-4 受控实验**（管线设计 §七 :98）专门证明了这一点：临时禁用 hook → push 新树 → cron tick 以 trigger=cron 独立拾取 spawn → 会话收口 done（2026-08-27 04:18 北京时间 PASS）。归因就靠 registry 里 trigger 字段——出问题先问"这个 tick 是谁触发的"。

一处**漂移观察**（培训价值高于结论）：`orchestrate_tick.py` 头部 docstring 写 cron 错峰 `"13,43 * * * *"`（:21），而登记册/实例规范/试卷口径是 `:18/:48`（registry :138、spec §二 :23）。按细则 7b"声明载体 vs 实际载体漂移核对"的精神，以登记册为准，代码 docstring 滞后——这正是新人接手时要养成习惯去抓的缺口。

### 4.2 登记——registry (treeId, tick, pid) 三元组的四不变量

映射表把登记载体定为三层：`trees/<id>/tree-op.json`（face/domainRouting/sourceMaterials 卷封字段）＋ session-registry instances/ticks（**rc·pid·trigger 全留痕**）＋ fade-hook.log。四不变量逐个看锚：

- **唯一性**：instances 按 treeId 唯一。锚是一条可机器复算的 jq：`jq '[.[]|select(.treeId=="trilc-lineage-merge")]|length'` 计数=1（registry :160）。
- **去重性**：真机制=tick 指纹边沿＋活动锁＋1800s 冷却。锚：`tick-fingerprint.txt`＋registry 无重复 spawn 记录可机器复算。这里有个 **LG-008 归因修正**必须讲：旧表述曾把去重归因于"hook 幂等"，联审撤了这口——真正的防重入是代码里的三件套（见 5.2 节），归因要给真机制（retrospective :121）。
- **关联性**：ticks 按 treeId 聚合十段工件。锚：p0fix1 树的 ticks 链——每个 tick 条目带 tree/rc/pid/trigger，审计时按 treeId 一拉就是完整时间线。
- **恢复锚**：tree-op.json＋ticks 定位现场。锚：p0fix1 blocked 复工实证——blocked 后新 tick 读树状态只派 pending 节点（管线设计 §四.4 :66 "禁复用纪律"）。

对照协议判例（细则 6）：006 没有显式 runId 字符串，`registry (treeId,tick,pid) 三元组`是它的"运行标识"合法形态——等价聚合键成立即合规。

### 4.3 Qualify——双门并列，缺一即停

映射表原文：*"机械准入门=三重门（status=active＋server-executable＋pending 无时间门）＋卷封验卷 verify=0（双门并列：两门齐备方开工，缺一即停）"*。

第一道门是编排层的 `evaluate_backlog()`（orchestrate_tick.py :175-210），纯代码谓词、零模型裁量：门 1 状态门只收 `status=active`（:186）；门 2 域路由门只收 `domainRouting=server-executable`（:189，**缺省不授权——安全默认**）；门 2b 面路由门只取 m-face（:193，r-face 归 TriRMC）；门 3 可执行门排除"全部 pending 节点都带时间门语义"的树（:197-201，正则 `TIME_GATE_RE` :172）。这正是细则 9 的 profile 限定：runtime-owned/自动触发 profile 强制确定性拾取门，不允许模型自由裁量入队。

第二道门在执行会话内部：BRIEF_V2 铁律（:226）——树带 sourceMaterials 时"**开工第一动作**逐文件重算 sha256 对照登记值，任一不符→按红线 3 blocked＋差异报告，禁止带污染开卷"。证据锚：`seal-materials --verify` 退出码 0（trilc-lineage-merge §9.3(a) 重封后复验，registry :161）。

**为什么两道门并列**：三重门只判定"这棵树该不该被拾取"，管不到"材料在封卷后有没有被动过"；验卷管材料完整性。前者防错派，后者防污染，语义正交。

### 4.4 Plan——M 面定计划拆树＋三类冻结件

映射表：*"M 面 TriMLC+CEO 定计划拆树＋sourceMaterials 预封＋语义作业方案卷封字段；试卷冻结件自 spec v2.0.3 起生效（新 run 适用，既有 run 回溯卷按历史口径标注）"*。证据锚：`p0-fix-and-trilc-merge-plan.md` §二（甄别 27/1＋门禁基线）；tree-op sourceMaterials 双 hash（`668d30a3…`/`3e412542…`）。

Plan 段的协议不变量（spec :243）到 v2.0.3 定型为**三件 Plan 时点冻结件**：结构化计划＋两类卷封（原材料/语义作业方案）＋**试卷声明**。最后这件是 LG-008 联审新立的（spec v2.0.3 变更记录 :20）：试卷是 Score 段的评分合同，"评分不能引用一份执行期可被改动的基准"，所以试卷必须 Plan 时点冻结、DCE 期间不可变、评分对卷；且明文裁定**语义作业方案卷封不涵盖试卷**——防"自改考卷"。FADE-006 增评卷是回溯建卷，按"历史冻结口径如实标注，不溯及改卷"处理，成为这条立法的**命名先例**。

### 4.5 DCE——CC 编排会话＋agent-carried 降级合同

映射表：*"CC 编排会话 spawn（agent-carried 降级合同，细则 4：先写后报＋原子即提交＋§2.7 节点收口报告）；段内逐节点门禁=node-report-check＋tsc＋npm test（括注：属 DCE 段内门禁，非 Verify 段）"*。证据锚：27 重放提交（trilc-lineage-merge dev 线）＋node-TM-1.md/node-TM-2.md。

这是全篇最关键的一个设计裁定。envelope 结构化报告合同（§2.2）对 CLI 是义务，对 agent 会话做不到——会话不是确定性程序。协议的处理不是放水，而是**把不变量换算成会话能做到的三件事**（细则 4，spec :260）：先写后报（工件先落盘再报告，带路径＋行数）、原子即提交（每完成一个原子动作立即单独 commit，会话被回收只认已 commit 的进度）、节点收口报告。envelope 义务仅及于会话内调用的确定性 CLI。006 是这条合同的第一个大规模实证：P0 战役八树的"先写后报＋一动作一提交"提交链，就是首评卷 audit-record 项的证据（`FADE-006-paper.json` :54）。

逐节点门禁的**归属括注**值得学：tsc＋npm test＋node-report-check 都发生在 DCE 段内，不是 Verify 段——协议 §2.8 Verify 行明文"前置门禁属 Qualify 机械门与 DCE 开工验卷"（spec :245）。把段内门禁冒充 Verify 段凑十段齐，是细则 10 批判的"纸面段"。

### 4.6 Verify CLI——可选段未启用（诚实空缺）

映射表只写了八个字级别的实话：*"可选段未启用（诚实空缺——逐节点门禁已前置 DCE 段内，不凑段）*，证据锚栏一横杠。这不是丢分项，是**格式律的示范行**：协议允许 Verify 缺席（可选段），实例的义务是如实声明而不是表演十段齐。对照 FADE-003 降档教训（registry :107 引细则 10）："无场景的态=纸面态"。

### 4.7 Score CLI——增评卷确定性覆盖检查

映射表：*"增评卷确定性覆盖检查（增评卷（TM run，现行法））"*；证据锚：`FADE-006-paper-rereview-2026-08-28.json` coverage 部分。协议不变量（spec :246）："覆盖遗漏检测确定性可复算"。具体形态：逐检查项判 score＋omission（是否遗漏），不评质量——同目录的 `FADE-006-score-2026-08-27.coverage.json` 就是这个轨的实态：每项带 score/max/omission，`quality_score` 全部为 null（那是 Score Skill 的活）。

### 4.8 Score Skill——逐项语义分＋evidence_ref

映射表：*"两项重计语义评定（卷封 5/8→8/8＋节点报告 3/8→7/8，evidence_ref 逐项）"*；证据锚：`FADE-006-score-rereview-2026-08-28.json`。协议不变量：每项语义分必须带 evidence_ref（spec :247）。增评的实际动作：只重计两项低分项（其余项"沿用原战役证据＋必选 6/6 无回归确认"，增评卷 notes :7），每项 note 写清理由——例如 node-report 给 7/8 的 note 是"报告诞生早于 v1.4.1 机读格式，格式增补后合规——**1 分记格式代差成本**"（:90）。评分的两段合成口径见 §2.6：Score CLI 判"是否遗漏"，Score Skill 判"每项处理质量"，合并输出，位于 Close Skill 之前作为其客观证据。

### 4.9 Close Skill——§9.3 二选一裁决＋blocked 分层取证八股

映射表：*"收口裁决：§9.3 漂移二选一＋blocked 分层取证八股"*；证据锚：trilc-lineage-merge tree-op.json notes（豁免＋重封留痕，**非静默放过**）。

Close Skill 的两个语义裁决场景：

**场景一：材料漂移二选一**（管线设计 §9.3 :140-147）。发现封卷 hash 不符时只有两条合法路：**(a) 授权修订**——变更有可溯 commit 链且登记在案：影响工作语义→受影响节点新建跟踪树重做；不影响→记录豁免理由放行；**(b) 未授权漂移**——`git checkout <登记 commit> -- <path>` 恢复登记版＋差异事件留痕。两条都要求证据 hash 回写。"没有裁决记录的漂移＝收口无效，编排层有权拒收并重派"（§9.3 末句）。trilc-lineage-merge 是 (a) 分支的活教材：收口后发现计划文档追加了 §四对账节（commit 链 cd9c1614..092ad159 可溯、operative 步骤零改动）→ 豁免放行＋重封留痕（tree-op notes :30）。

**场景二：blocked 分层取证八股**。BRIEF_V2 红线 3（:238）"事实障碍如实标注 blocked 并停，不臆造完成"；实例规范 §四 的定层方法一句话："**取原始拒绝文本定层**"（审批前缀匹配层？执行通道缺失？权限层？上游层？），修复定向后自愈复工、不复用污染进度。P0 战役的六面墙（spec §四表）与 p0fix1 四轮 blocked、p0fix4 三重墙（W1 属主混杂/W2 外来 WIP 层/W3 bare 领先三笔，plan §一 附注 :50）都是这条八股的实战产出。

### 4.10 Close CLI——四件套＋三态声明的增补载体

映射表：*"顶层 done commit＋push 回流＋台账 rc 终值＋战役 Merkle root；增补载体=harvest-rc 程序化派生 rc——三态声明：matcher 载体=已接线（p0fix4 MATCH 实证＋部署 9215886）；例行化宽口径=核验中（解除条件=LG-005 首个真实战役实证）"*。证据锚：`c6f969de` 双远端；战役 root `40ee6f8c…`（八树快照口径，见 7.4 口径坑）；`reports/run-root.json`（run root=`c841f337…`，补算五要合规）。

四件套拆开：

1. **顶层 done commit＋push 回流**：BRIEF_V2 红线 4（:239）"收口必做：全部节点 done 后，把树文件顶层 status 置为 done，再提交（F1 修正）"；trilc-lineage-merge 的收口 commit `c6f969de` 双远端（registry :168；retrospective :109 另记 `355d24fe`）。
2. **台账 rc 终值**：tick 台账（session-registry）的 rc 从 "spawned" 到终值的闭环，载体见 5.5 节 harvest-rc。
3. **战役 Merkle root**：管线设计 §9.4（:149-151）——战役收口时把全部树的 `(treeId, status, ∏sourceMaterials.hashes, 收口commit)` 清单整体求 sha256。首演值 `40ee6f8ce950ad024e82b69309cede0b8b0cfee2cf9ab17ff26d1bafce184af5`（plan §4.2 :118），附诚实声明："本战役树群诞生于卷封制生效前，材料未预封——此 root 为收口后快照（防篡改基线，非过程完整性证明）"（:121）。
4. **为什么 Close CLI 不能自证**：§2.5 专句（spec :174）——"实例映射表声明的确定性载体（如 FADE-006 的 tick 台账回收器）视为该实例的 Close CLI 形态；**被裁决会话不得自证终值**（v1.4.1 CTO-F7）"。会话自己说"我成功了"只是声明性草案，终值必须由会话外的确定性程序定谳。

---

## 五、执行形态深拆：编排层代码走读（接手代码必读）

### 5.1 模块入口与单次 tick 职责

`D:/Code/ai/TriCompany/runtime/cognition/orchestrate_tick.py`，模块 docstring（:1-22）自述五步：三重门待办评估 → 待办集指纹 → 成本护栏 → spawn 编排会话 → 会话结束收割 usage 记台账。调用方两处：trimc cron（慢通道）与 sg-bare post-receive hook（快通道，`--trigger hook`）。

### 5.2 防重入三件套（去重不变量的真机制）

- **指纹边沿**：待办集指纹=可执行树 `(treeId, pendingNodes)` 集合的内容哈希（:208-209）。空提交/纯文档 push 不翻指纹；指纹未变→无新 tick。管线设计 §八.1（:104）补了运行语义：同指纹重入唯一路径=距上次 tick 收场 ≥1800s（战役续跑模式，代码 ：377-388），**无旁路**。
- **活动锁（O_EXCL）**：`os.open(LOCK_PATH, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o644)`（:406）——判定与写入之间的竞态窗口闭合（P1-2，管线设计 §七 :89），双通道并发只有一方创建成功。
- **PID 判活与陈旧锁四通道**（`_lock_stale_or_absent` :94-124）：锁龄>2×timeout（560s，:62）/ 锁内 pid 已死 / 台账反查该树 spawn pid 已死 / 无 pid 且锁龄>300s 短阈值判死。注释里写着历史教训："原版查无条目即判活，孤儿锁滞留最长 80 分钟"——**禁止默认拒斥**。

### 5.3 spawn 合同（DCE 段的发射器）

代码 ：421-486 的关键行：

- 模型显式钉死：`--model cfg["default_model"]`（:428，P1-4——防 HOME 配置漂移导致秒死）；
- 白名单全家桶：`--allowedTools` git 全家桶＋npm/npx tsc/node/python3＋文件检视工具族＋Task（:431-441）。来历写在注释里：p0fix1 blocked 复盘发现"此前仅 git 写三件＋mkdir/ls，npm/tsc 全被挡"（:429-430）——执行通道缺失墙的修复；
- **cwd 按树路由**：从 tree.repo 字段正则取路径，存在则直落该仓（:447-453）——配合 BRIEF 裸命令铁律，杜绝"`cd X && git …` 复合前缀被权限引擎整串拒"的形式性问题（D-11）；
- 异步发射：`subprocess.Popen` 不阻塞（:459-462）——修复同步等待被 trimc 600s timeout 杀死长任务、连续 52 次的事故；发射后锁内补记 pid（:474-478），ticks 条目落 `rc:"spawned"/pid/trigger`（:480-482）。

### 5.4 BRIEF_V2：写进代码的执行宪法

`BRIEF_V2` 模板（:213-246）是 spawn 时注入会话的任务简报，六节：任务（按节点派工 fresh 子实例、一次一个节点禁复用）、铁律（状态先行＋原子即提交；命令一律裸形式）、卷封制（开工验卷/收口对卷/§9.3 裁决）、节点收口报告（十字段＋机读九键＋翻转前置门）、红线四条、完成定义（"节点全 done＋顶层 status=done＋收口 commit 已 push＋session-registry 追加本 tick 台账"，:241-242）。**新人接手第一课：改 BRIEF_V2 就是改全管线的执行合同，任何一行变更都要过"下一个 tick 生效"的部署意识。**

### 5.5 _harvest_usage：Close CLI 载体（harvest-rc）

:290-342。原始职责是 P1-3（收割已结束会话的 usage 入账，修复预算双门读数恒零）；CTO-F7 立法后**兼职** Close CLI 载体（docstring :295-297 明写）。程序化派生 rc 的逻辑（:323-337）：扫 `orchestrator-session-*.log`，看到 `"type":"result"` 行即会话结束，解析 result JSON——`derived = 0 if subtype == "success" else 1`，然后按**数字前 14 位**匹配 registry 里 rc 仍为 `spawned/1/"1"` 的 tick 条目，回填 `rc=derived`＋`rc_source="harvest-close-cli"`。

为什么是"前 14 位"：匹配器首版用全格式子串匹配，但 tick 是 ISO 带冒号格式（`2026-08-27T10:42:05`）、日志文件名是紧凑格式（`20260827T104205Z`）——**永 miss**，被模拟证伪后改为数字前 14 位对齐。这是细则 10 的判例之一（spec :266"harvest-rc 匹配器（模拟证伪 → 前 14 位修正）"）。**映射表对它做了三态声明**：matcher 载体=已接线（p0fix4 MATCH 实证＋部署 9215886，registry :168）；例行化宽口径=核验中，解除条件=LG-005 首个真实战役实证（daily-progress :31："下个 M 面 spawn 后查 registry rc_source"）。**这就是"接线≠立法完成"的活样本**：代码在跑，但生产证据还在攒，映射表如实写"核验中"。

### 5.6 工具族四件（`TriMetaverse/scripts/fade/`）

| 工具 | 守护的不变量 | 关键机制（file:line） | 退出码 |
| --- | --- | --- | --- |
| `_fadehash.py` | 单一 canonical 双 hash | `dual_sha256`（:18-23）：raw=字节原样 sha256；lf=行尾归一后 sha256。seal 与 run-root 共享本模块，防"两套 hash 实现各自漂移"（docstring :4-7） | —（模块） |
| `seal-materials.py` | 材料完整性（卷封制） | attach **拒绝二次封卷**（:50-54 "封卷只许一次；重封需走 §9.3 裁决"）；verify 逐项重算，仅行尾差异判 SOFT-DRIFT 警告留痕（:87-92），内容差异判 DRIFT（:93-97） | 0=一致（含 SOFT）/1=未封卷/2=漂移/3=用法或缺料（§十 ：112） |
| `node-report-check.py` | §2.7 十字段合同 | ```json fenced 块须含核心九键（:26-27）＋散文三节"异常与处置/断点交接/使用依据"（:28）；支持 `--pending-from` 只查 done 节点（:67-69） | 0=全过/2=缺失或不全（翻转门必拦）/3=用法错误 |
| `run-root.py` | 单 run 收口完整性基线 | 输入集=树内全部文件＋`--plan` 显式工件，run-root 快照**自排除防自引用**（:51-60）；Merkle 口径=按 path 排序逐件 `"path\0raw\0lf"` 串接 sha256（:97-98）；**append-only**（:111-121 解析失败即拒绝不覆盖；:158-175 重算只追加 history） | 0/3 |

双 hash 的 SOFT-DRIFT 判据（`_fadehash.py` :10，联审 CTO-F6）：跨 Win/Unix 流转的行尾漂移**不按材料污染处理，仅警告留痕**——否则 Windows 工作机每个 CRLF 都会误触发 §9.3 污染裁决。

---

## 六、本周真实运行证据清单（一切数字的出处与可复验性）

| 事实 | 值 | 出处（file:line） | 本地可复验？ |
| --- | --- | --- | --- |
| 首评总分 | PASS 80/100，required_all_passed=true，scored_at `2026-08-27T19:5x+08` | `FADE-006-score-2026-08-27.json` :115-118 | 是（文件在手） |
| 增评总分 | PASS 91/100，scored_at `2026-08-28T01:1x:00+08` | `FADE-006-score-rereview-2026-08-28.json` :115-118 | 是 |
| 首评分项 | 必选 10/9/10/9/8/10＋卷封 5/8＋AC 8/8＋节点报告 3/8＋故障 8/8 | 同上 ：3-113 | 是 |
| 增评分项 | 必选全 10＋卷封 8/8＋节点报告 7/8＋AC 8/8＋故障 8/8 | `FADE-006-score-rereview-2026-08-28.json` | 是 |
| 战役快照 root | `40ee6f8ce950ad024e82b69309cede0b8b0cfee2cf9ab17ff26d1bafce184af5` | `p0-fix-and-trilc-merge-plan.md` :118 | 是（文本） |
| 封卷双 hash | `668d30a3…`（计划）/`3e412542…`（spec），recordedAt 2026-08-27T14:34:44Z | `tree-op.json` :35/:44/:38 | 是 |
| §9.3(a) 重封 | resealed_after_adjudication `2026-08-27T15:59:39Z` | `tree-op.json` :40/:49 | 是 |
| 合并门禁 | tsc exit 0；npm test 585 pass/1 fail（HS-3 预置） | `node-TM-2.md` :17/:70-79 | 是 |
| 终态提交 | dev=ff2f970 双远端单线化；修正案 44e3843 | `merge-log.md` :7；`node-TM-2.md` :15 | 是（文本） |
| 单 run root | initialRoot `c841f3375b27…18b88`；现行 root `c414708573bc…d5b` | `reports/run-root.json` :6/:14 | 是 |
| P0 修复锚 | agent-core `fabcbef`/`14499e5`/`95d8713`；TriModel 工件 `3ab659a`；heyuan 四仓 `ff2f970/30a671e/f09b633/6a6847e` | plan :105-108/:144-147 | 是（文本） |
| hook 日志 44 条 dev updated / instances=42 / ticks p0fix 系 10 条 | 首评卷 verify_method 记载 | `FADE-006-paper.json` :19/:27 | **否**——服务端 `/srv/fleet/shadow-plane/`，本地不可复读，采信卷宗 |
| harvest-rc matcher 部署 9215886 | registry :168 | 是（文本）；服务器侧部署实态不可本地复读 |
| run-root 覆盖写修复提交 9d97f563 | 任务卷宗口径 | **否**——本教程只读核查未在仓库文件中遇到该 hash，引用时以 `run-root.py` :19-21 "验收修复令 Bug-1"标记为准，如实标注 |

最后两行是本教程的**取证纪律示范**：所有 hash/数字要么给 file:line，要么明说"卷宗口径、本地不可复验"。严禁把后者写成前者。

---

## 七、故障弧线与教训：九项 P0＋覆盖写缺陷

### 7.1 P0 审计修复战役（首个完整运行，2026-08-26/27）

九项 P0 全清单在 `p0-fix-and-trilc-merge-plan.md` §一（:13-23）：

| # | 模块 | 缺陷（一句话） | 位置 |
| --- | --- | --- | --- |
| 1 | agent-core | 路径边界校验前缀混淆＋目录穿越双重绕过 | packages/agent-core/src（:19 起） |
| 2 | agent-core | acceptEdits 把 shell_exec 及一切非文件写入工具免确认放行 | decision-pipeline.ts:226-232 |
| 3 | agent-core | 规则内容匹配退化为序列化全文子串匹配 → allow 规则子串注入绕过 | decision-pipeline.ts:215 |
| 4 | agent-core | spawnAgent 丢弃全部权限配置，子代理恒 bypassPermissions 无 cwd 边界 | spawn.ts:31-39 |
| 5 | TriRMC | cron 载荷 runAs 无校验 → 反用为提权 | src/command-handler.ts:85 |
| 6 | TriRMC | /internal/* 鉴权 fail-open（token 未配置=零鉴权） | src/app.ts:121-122 |
| 7 | TriRMC | 权限规则子串匹配绕过（#3 的本地拷贝同源缺陷） | decision-pipeline.ts:100-108 |
| 8 | TriLC | 全 HTTP 面零认证＋三条命令执行通道＋可被 DNS rebinding 远程触达 | server/app.ts 等（精修版归并条目） |
| 9 | TriModel | stream() 中途 fallback 静默拼接两个模型输出流 | providers/client client.ts chat/stream 双实现区 |

修复按同源归并五批（:31-46）：A 权限引擎硬化（#1#3#7，先真源后拷贝）→ B 工具放行与子代理隔离（#2#4）→ C TriRMC 服务面（#5#6，fail-closed 反转）→ D TriLC HTTP 面（#8，X-Internal-Token＋Host/Origin 门，**注意本面是 fail-closed 变体，与 TriMC trimc-auth 的 fail-open 故意不同**，:45）→ E TriModel 流式 fallback（#9，已开流的 fallback 一律终止流并上报错，禁止拼接）。批次终态与锚点见 §4.1（:103-108）：p0fix1 `fabcbef`+`14499e5`+`95d8713`（46/46×2）、p0fix2 verify.md 15.6KB、p0fix3 常数时比较 token 门＋三门互锁、p0fix4 `3ab659a` 直落＋守卫测试 29/29×2。

### 7.2 六面墙：三天实战争得的故障定层表

实例规范 §四（:39-46）把故障处置压成一张速查表，每行都是"症状→定层方法→解法锚"：工具命令被拒→取原始拒绝文本看审批前缀匹配层→D-11 裸命令/cwd 直落；执行通道缺失→白名单对照被拒串→61dfaea 全家桶；push Permission denied→裸仓 objects 属主分布→D-10 chgrp＋sharedRepository＋bare-perm-heal cron（15 分钟自愈，管线设计 §八.4 :107）；push 后 tick 无反应→fade-hook.log 有无 dev-updated 行→D-08 unset GIT_DIR；tick 看不到新树→`_sync_worktree degraded` 字样→P1-1 自愈；多线归账互拒 fast-forward→range-diff 看同补丁异 SHA→merge-only 归账。**学法：不是背表，是背"取原始证据文本定层"这个动作——八股的第一步永远是把拒绝原文捞出来。**

### 7.3 覆盖写缺陷弧线（细则 10 第 4 判例——本域亲历，如实标注）

这是本教程最想让你带走的一弧，因为它发生在 LG-008 验收窗内、被实测当场抓出，全链证据都在本地文件里：

1. **立法**：LG-008 边界③清偿要求为 trilc-lineage-merge 补算单 run root，且补算须"五要合规"：recomputed_at＋触发原因＋输入差说明＋原根历史锚声明（append-only）＋basis manifest（retrospective :123）。
2. **初版缺陷**：首算版工具在 `initialProvenance.appendOnlyNote` 里**写着**"后续重算须另档新文件（append-only）"（run-root.json :12 至今保留这行历史原文），但当时的代码路径却是**整文件覆盖写**——注记口径与代码行为并存矛盾。培训黑话：**append-only 停留在注释口径，没有落为代码路径**。
3. **验收实测抓出**：编排层复算差异，Bug-1 定谳为覆盖写缺陷（run-root.json R1 条目 reason 自述："append-only 修复后首次重算（编排层复算差异 Bug-1 实测后）"，:19-20）。修复提交在任务卷宗口径记为 9d97f563（本地只读未复核到该 hash，见第六节末行标注）；修复痕迹在文件里可指认：`run-root.py` :19-21 docstring "**append-only（验收修复令 Bug-1）**：输出文件已存在时不得覆盖——原 producedAt/initialRoot/全部 recompute_history 保留，新计算只追加 recompute_history 条目并更新现行 root 字段"，以及 ：111-121 的读取门（既有快照解析失败即拒绝覆盖、exit 3）。
4. **复验探针被正确吸收**：修后连跑两次验证原根与历史全保留（R1/R2，prevRoot==newRoot==c841f337，:18-30）；第三次验收探针（R3"LG-008 acceptance third-run"，:31-37）因输入集变化（basis 6→4 件）产出新 root `c4147085…`——**探针没有抹掉历史，而是被追加为 recompute_history 第 3 条**，prevRoot/newRoot/inputDiff 齐全。append-only 立法至此"接线＋实测"双齐。
5. **判例定位（如实标注）**：本教程所读的 `fade-protocol-spec.md` v2.0.3 文本（:266）细则 10 尚记"判例×3"；覆盖写作为第 4 判例的入册状态以 TriCompany 仓库最新提交为准——但无论法条文本走到哪一版，**代码与快照里的证据链是完整的**，这就是"本域亲历"的含义。

**教训沉淀（原话引用）**："整文件覆盖写是 append-only 立法的头号违反形态——永不覆盖必须落为代码路径而非注释口径。" 展开：任何"只许追加"的语义（台账、history、审计日志）验收时必须做一个**故意重跑**的探针，验证旧值还在；写在注释里、写在变量名里、写在文档里的 append-only 都不算数，exit code 和留存的历史条目才算数。

### 7.4 两个口径坑（复算必读）

- **战役 root 九树口径**：首评卷 notes（`FADE-006-paper.json` :8）明示"CAMPAIGN-SNAPSHOT-ROOT 40ee6f8c… 为**九树口径**（含 trilc-lineage-merge）；八树口径必得异值——复算须钉口径"。注意登记册映射表写"八树快照"（:168）、retrospective 也写"八树"（:123）——那是"八棵**系统**树"的简写；收口真源 plan §4.2 原文是"八棵系统树＋一棵本地树"（:115）。复算对不上时，先查口径再查算法。
- **root 现行值≠initialRoot**：run-root.json 里 `root: c4147085…`（:14）≠`initialRoot: c841f337…`（:6），初学者容易误判"基线被改"。真相在 history：R3 探针输入集 6→4 件（少了两个 `--plan` 计划文档），root 是输入集的函数，输入变了 root 合法地变，而历史把两次计算都留着。**附一个维护者观察（推断，显式标注）**：清偿记录记载 anchors=c6f969de/355d24fe/战役根注记（retrospective :123），但现行文件 `anchors: []`（:65）——从代码看，recompute 分支（run-root.py :158-175）不回带既有 anchors、只取本次 CLI 参数，R3 探针未带 `--anchor` 即落空。这是工具现存的小缺口，接手者可列为待修项。

---

## 八、评分卷宗解读：双轨 80→91 怎么读

### 8.1 三件套与双门槛（§2.6 速记）

试卷（考什么：固定部分＋测试集＋治理对齐项）→ 答卷（运行标识、节点报告、结构化报告、评分输出、审计日志、终态样本）→ 评分（Score CLI 覆盖检查＋Score Skill 语义评定合并 JSON）。及格双门槛：**必选项全过**（确定性判定）∧ **总分达标**（实例声明阈值，006 为 80）。评分不达线 → RETRY 或 ESCALATED，不得写入终态。

### 8.2 首评卷（2026-08-27，回溯建卷，冻结留档）

回溯建卷的合法性口径写在卷首 notes（`FADE-006-paper.json` :7）："运行期(08-26/27)先于本卷存在，按 001-004 先例评分时点建卷，**评分仅采信运行期已产生的工件**。"分项实态（score-2026-08-27.json）：

| 项 | 权重 | 得分 | 扣分原因（卷内原话） |
| --- | --- | --- | --- |
| trigger-config | 10 | 10 | — |
| run-id-carrier | 10 | 9 | "旧时代 None 混入扣分"（paper verify_method :28） |
| skill-docs | 10 | 10 | — |
| cli-report | 10 | 9 | "运行期 stdout 空为可观测性扣分点"（:46） |
| audit-record | 10 | 8 | "十字段节点收口报告运行期未强制→本项扣分＋item9 专项"（:55） |
| terminal-sample | 10 | 10 | root 复算一致（九树口径坑入 notes） |
| sealing-integrity | 8 | 5 | "立法与工具三态实测齐；**运行期未预封**（retrospective 口径声明）→按发生时点低计"（:73） |
| acceptance-ac | 8 | 8 | AC-1a×44/AC-1b 实弹/AC-2/AC-3/AC-4 受控实验 PASS |
| node-report-27 | 8 | 3 | "运行期未强制（立法在后）→3/8：立法与部署实证齐，**运行实例零报告如实计低**"（:91） |
| fault-forensics-resume | 8 | 8 | 六墙四轮自愈＋p0fix4 沙箱 `3ab659a` 直落零重做 |

合计 80，卡线 PASS。登记册评语（:151）给这分的定性是："**'标准但不完美'的诚实读数**"——两个低分项不是实例做错了，而是立法晚于运行，按"仅采信运行期工件"如实低计，不作追溯豁免。同目录 `FADE-006-score-2026-08-27.coverage.json` 是 Score CLI 轨的独立卷（quality_score 全 null），证明"两源合并"不是说法而是两个真实文件。

### 8.3 增评卷（2026-08-28，LG-004 联审 C 口径双轨）

增评卷首行 notes 把边界钉死（`FADE-006-paper-rereview-2026-08-28.json` :7-10）：对象=**trilc-lineage-merge 双节点小 run 的现行法合规性增评，不是 P0 战役复验**；两项低分以新证据重评，其余沿用原战役证据＋必选 6/6 无回归确认（CTO 护栏 2）；试卷模板已升 v1.1.0（登记载体=运行标识口径，CTO 护栏 4，注意 item id 也从 run-id-carrier 改名 run-carrier）；**首评 80 冻结留档不改（CPO 修正 2 不溯及既往）**。

两项重计的证据链：卷封 5/8→**8/8**——"F2 封卷 verify=0＋开工验卷＋§9.3(a) 真实触发（收口后合法漂移豁免＋重封）——**两分支均实测**"（:74）；节点报告 3/8→**7/8**——"node-report-check 首跑 FAIL 0/2→机读核心增补→PASS 2/2（LG-003 首战）……弧线如实"，扣 1 分记"格式代差成本"（报告散文十段诞生早于 v1.4.1 机读格式，2026-08-28 增补 json 块后合规——你现在读 node-TM-1.md :15 看到的"机读核心（§2.7 v1.4.1 格式增补，2026-08-28；事实同上散文节）"就是这个增补的实物）。合计 **91，PASS**；score 卷 notes 收尾："细则 8 复审触发判定：**无结构性缺陷 → §2.7/§2.8 复审触发解除**"（:121）。

### 8.4 升格弧线：从 91 分到"完整实例标准档"

增评 PASS 只解决评分；升格还要清偿 retrospective §九 列出的**三处诚实边界**（:114-117），即 LG-008 联审的三件事：

1. **边界①（登记层弱化）**：local-executable 树不走 tick，映射表三字段应声明而未声明，为首行待填 → 清偿=登记册 v2.1 十段映射表首行填制＋补锚＋去重归因修正（撤"hook 幂等"误归因）＋Verify 行如实空缺＋harvest-rc 三态声明（retrospective :121）。
2. **边界②（试卷回溯）**：增评卷系收口后按 §2.6 重建，"Plan 时点声明试卷"的理想序未走全 → 清偿=spec v2.0.3 立法：试卷升格第三件 Plan 时点冻结件＋双 hash 冻结＋语义作业方案卷封明文不涵盖试卷＋**FADE-006 增评卷作为历史口径命名先例**（spec :20、retrospective :122）。
3. **边界③（单 run root 未算）**：战役级 root 是八（系统）树快照，本树独立 run root 未产出 → 清偿=run-root.py 工具首测即补算，run root=`c841f337…`，补算五要合规（retrospective :123）。

清偿程序本身也有留痕："组织者 CEOCS 评估初稿→三方联审（CPO/CTO 双席逐项裁决）→CEOCS 合成定案（含 CPO 单一 hash×CTO 分文件结构调和：独立脚本＋共享 _fadehash 模块）→编排层核验＋CEO 授权→落地"（:125）。调和案的实物就是 `_fadehash.py` docstring（:5-7）："CPO 产品侧坚持单一 hash 纪律 × CTO 结构裁定封卷与 root 语义相反须分文件——独立脚本＋共享 canonical 模块，两席关切各得其所。"

最终升格标注（registry :170）："三处诚实边界清偿齐备＋增评 91 PASS 在册——**FADE-006 升格完整实例标准档**……升格不溯及既往：既有 run 合规由现行法下新增 run 评分背书（spec 细则 10 修正 2 口径）。" 周进度把它记为 08-28 里程碑第 2 项（daily-progress :13："spec v2.0.3 @ecd922b、registry v2.1"）。

---

## 九、映射表首行填制范式：后来的实例怎么写

006 作为首行样本，把 §2.8 细则 2 的三字段 schema 用成了可复制的格式规约。逐条提炼：

1. **载体类型与形态列**：先给载体**类型**（registry/钩子/会话/CLI/快照），再给**形态**（哪棵树哪个文件哪个字段）。006 的"登记"行就是三层载体一次列全：tree 文件＋registry＋hook.log（registry :139）。
2. **事件触发段要分双载体**：归因锚（前置输入，任务说明书封卷 hash）与触发机制（hook/cron，trigger 字段可归因）分开写——触发段的不变量是"可重放、可归因"（spec :240），两类证据各管一半。
3. **不变量证据列一律是锚**：jq 计数命令、tick-fingerprint 文件名、hash、退出码、commit。判据：第三方能否**机器复算**（细则 7a）。写"运行良好"就是散文，退回。
4. **归因给真机制**：去重性写"指纹边沿＋活动锁＋1800s 冷却"，不写"hook 幂等"——LG-008 专门修正过这处误归因。证据锚必须指向真正干活的代码路径。
5. **可选段空缺如实**：Verify 行"—（空缺如实）"。把段内门禁挪名目凑段，违反细则 10 的"无场景的态=纸面态"。
6. **部分接线三态声明**："已接线（附实证锚）/核验中（附解除条件）/未启用"。harvest-rc 行的"解除条件=LG-005 首个真实战役实证"是解除条件的标准写法——有名字、有挂账、有核对动作。
7. **立法时点括注**：涉及立法后件的行带时点括注（如"试卷冻结件自 spec v2.0.3 起生效（新 run 适用，既有 run 回溯卷按历史口径标注）"）——把不溯及既往写进行内，省得周检再解释一遍。
8. **归属括注防冒领**：DCE 行括注"（属 DCE 段内门禁，非 Verify 段）"。每写一行问自己：这个工件归哪段？别让 Verify/Score/Close 替 DCE 领功。

**自检清单（FADE-007 起入册前过一遍）**：十行齐？每行有锚且机器可复算？空缺行如实？三态行有解除条件＋责任席位？立法后件带时点括注？与实际载体做过漂移核对（细则 7b）？

---

## 十、常见误区、遗留观察与接手任务

### 10.1 常见误区

- **误区一：把 DCE 会话当 CLI 要求 envelope**。会话走的是细则 4 降级合同，envelope 义务只在会话内调用的确定性 CLI 上。
- **误区二：把 registry 里会话自写的 rc 当终值**。台账自证合法（管线设计 §八.2 :105"这是特性不是数据损坏"），但调度只信锁内 PID，终值以 `rc_source="harvest-close-cli"` 的回填为准。
- **误区三：看到 verify 非 0 就当污染**。先看是 SOFT-DRIFT（行尾级，exit 0 留痕）还是 DRIFT（内容级，exit 2 须裁决）——seal-materials 的退出码语义表（§十 ：112）是唯一口径。
- **误区四：复算 root 对不上就说工具坏了**。先钉口径（九树 vs 八树；root 是输入集的函数，读 recompute_history 的 inputDiff）。
- **误区五：把首次 80 分读成"实例有结构性问题"**。80 是"立法晚于运行＋如实低计"的读数；结构性缺陷判定属细则 8 复审触发，增评已解除。

### 10.2 遗留观察（接手者候选任务清单）

| 项 | 现状 | 锚 |
| --- | --- | --- |
| LG-005：harvest-rc 例行化宽口径核验 | 挂账，"下个 M 面 spawn 后查 registry rc_source" | daily-progress :31；registry :168 |
| blocked 边沿告警 | v1.2 待办（会话 blocked 目前仅 registry 自证＋本地轮询可见） | 管线设计 §八.5 :108 |
| run root Close 时点纪律 | 新 run 起 root 应在 Close CLI 时点算（补算属历史清偿，非常态） | run-root.py :17 "root 计算时点钉死 Close CLI 点（新 run 纪律）" |
| run-root anchors 回带 | recompute 分支不保留既有 anchors（推断，见 7.4）；建议修复＋回归探针 | run-root.py :123-129/:158-175；run-root.json :65 |
| 代码 docstring 与登记册 cron 时刻漂移（13,43 vs :18/:48） | 以登记册为准，docstring 待同步 | orchestrate_tick.py :21；registry :138 |
| FADE-006 补齐项：节点报告与卷封预封"下实例起强制并复评" | 已立法（§2.7 双门＋v1.4.1），对 007 生效 | registry :150 |

### 10.3 一步验证（读完全篇后的自测）

在本仓只读环境下做三件事：① 打开 `reports/run-root.json`，向同伴讲清 initialRoot/root/history 三者为何不同；② 打开 `tree-op.json`，指出 §9.3(a) 裁决的原文与重封时间戳；③ 打开 `orchestrate_tick.py` :323-337，解释为什么 rc 回填要匹配"数字前 14 位"。三件都讲得清，你就具备接手 FADE-006 运维的入门资格了。

---

## 使用依据

- `D:/Code/ai/TriCompany/docs/engineering/fade-registry.md`（FADE-006 条目 :134-170：十段工件表、段-实现映射表、升格标注、评分双轨记录、补齐项三态）
- `D:/Code/ai/TriMetaverse/docs/execution/fade-006-execution-autopick-spec.md`（六步流程/护栏/六面墙/证据链）
- `D:/Code/ai/TriCompany/docs/engineering/fade-protocol-spec.md` v2.0.3（§2.5 终态门/§2.6 试卷冻结/§2.7 节点报告/§2.8 细则 1-10）
- `D:/Code/ai/TriCompany/docs/engineering/fade-papers/FADE-006-paper.json`、`FADE-006-score-2026-08-27.json`、`FADE-006-score-2026-08-27.coverage.json`、`FADE-006-paper-rereview-2026-08-28.json`、`FADE-006-score-rereview-2026-08-28.json`（评分双轨五卷实态）
- `D:/Code/ai/TriMetaverse/docs/execution/fade-instances-retrospective.md`（§一架构期对照/§三强制要件/§九十段实跑走查＋三处诚实边界及清偿记录）
- `D:/Code/ai/TriMetaverse/docs/execution/2026-08-26/fade-pipeline-design.md` v1.1（触发拓扑/AC 表/§八运行语义/§九卷封制/§十工具合同）
- `D:/Code/ai/TriMetaverse/docs/execution/2026-08-27/p0-fix-and-trilc-merge-plan.md`（九项 P0 清单/批次终态/战役 root §4.2/验收回执 §4.5）
- `D:/Code/ai/TriCompany/runtime/cognition/orchestrate_tick.py`（三重门 :175-210/BRIEF_V2 :213-246/锁与 spawn :393-486/_harvest_usage :290-342）
- `D:/Code/ai/TriMetaverse/scripts/fade/`（`_fadehash.py`/`seal-materials.py`/`node-report-check.py`/`run-root.py` 全文）
- 树实态：`D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W35/trees/trilc-lineage-merge/`（`tree-op.json`、`reports/node-TM-1.md`、`reports/node-TM-2.md`、`reports/merge-log.md`、`reports/run-root.json`）
- `D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W35/daily-progress.md`（2026-08-28 里程碑与 LG-005 挂账）

<<<<END>>>>
