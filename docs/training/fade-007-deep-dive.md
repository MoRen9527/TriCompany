# FADE-007 蓄水池（中枢上下文管理）深度教程

## 文档同步元信息

- sourceOfTruth: TriMetaverse/docs/execution/fade-007-context-reservoir-spec.md（本教程是其培训解读，不替代真源）
- syncMode: training-copy
- lastSyncedAt: 2026-08-29
- 状态: 培训教程（研发新人向）；所引 spec 现状=FADE 兼容档（2026-08-28 升格联审修后放行）
- 执笔: 小吴（RAndDTrainer）；hash/数字核验方式=Read/Glob 读在盘文件（无 git 运行通道），未核验项显式标注

## 零、培训判断与读者定位

- 读者：要接手 TriCompany 治理自动化代码与运维的研发新人。起点假设：会用 git 和 python，读过 `TriCompany/docs/engineering/fade-protocol-spec.md` 的 §一§二（没读过先补，本文 §二 给最小底座）。
- 接手目标分三层：①能复述蓄水池的问题模型与六源恢复配方（运维面）；②能读懂并运行 `hub-snapshot-diff.py` 与 `daily_progress_patrol.py`（代码面）；③能参与 E-3/E-4 演练与升完整硬门的推进（流程面）。
- 学习方法约定：本文按「大结果 → 协议底座 → 十段落地 → 最小闭环 → 流程与工件 → 代码导读 → 运行证据 → 故障教训 → 评分 → 协议对照 → 接手任务」组织；每一层都给出真源 file:line，读到拿不准的地方一律回真源，不凭本文记忆。

## 一、先讲大的结果：蓄水池解决什么问题

### 1.1 常驻中枢的三种死法

常驻中枢（小贾，xiaojia-hub，更名后职衔=董事长助理）持有完整工作上下文，但长会话会遇到三类故障（spec §一，`docs/execution/fade-007-context-reservoir-spec.md` L13-16）：

1. 爆上下文：任务降雨量持续大于上下文容量——装不下了。
2. 语义漂移：多次自动压缩叠加，重点被静默丢弃——还装着，但内容悄悄变质。
3. 不可控性：自动压缩无从审核，丢了什么没人知道——坏了也没人发现。

FADE-007 的目标效果一句话：**上下文压缩从「黑箱自动行为」变成「可审核、可恢复、可演练的受控流程」**。当前成熟度：恢复面向已实测（E-1/E-2 双演练 PASS），压缩/清空面向大部分纸面（见 §三档位表）。

### 1.2 CEO 蓄水池隐喻：降雨/蓄水/放水/水位

CEO 用蓄水池定过角色模型（spec §二 L18-24）。翻译成四要素：

| 隐喻要素 | 系统里是谁 | 干什么 | 真源锚 |
| --- | --- | --- | --- |
| 降雨 | 任务流（CEO 指令、联审、交付） | 持续向中枢注入上下文 | spec L13「任务降雨量」 |
| 蓄水池 | 编排层（现名董事会，CEO 直连会话） | 承接降雨、暂存原上下文（临时文档）、对比核验、放水 | spec L22 |
| 闹钟+记事本 | 也在董事会侧 | 监测运行时长/压缩次数，提醒 CEO 或触发清空；暂存过渡期摘要 | spec L23 |
| 河水水位 | 中枢上下文 | 实际工作记忆，水位判断依据 | spec L24 |

为什么这样设计：水位（上下文）在助理侧，但**放水审批权与核验权留在董事会侧**——被压缩方不能自己证明压缩没丢东西。这是整套协议的分权根基，后来被立法进 `TriMetaverse/CLAUDE.md` 分权制节（L33-39，其中 L38 明写「爆上下文风险→令助理产全量快照（`.fade/hub-snapshots/`）后受控压缩，董事会 diff 核验」）。注意术语史：spec 与 CLAUDE.md 早期文本写「编排层」，2026-08-28 16:3x 更名立法（CLAUDE.md 995bd161，台账镜像 ledger-mirror.md L16 在卷）改为「董事会/董事长助理」；**历史条目不改，现役口径用新名**——你读旧文档时要做这层翻译。

### 1.3 它在全局里的位置

- 上位：orchestrator-hub-split（编排/中枢分权制）——董事会与助理的分权是蓄水池的制度前提（spec L9）。
- 协议面：FADE-007 是 FADE 协议（`TriCompany/docs/engineering/fade-protocol-spec.md`，现行 v2.0.3）的一个实例，当前档位 FADE 兼容档，**不在** `fade-registry.md` 在册五实例（001/002/003/004/006）里——登记册 L11 明确定义「本册只登记完整档」。
- 与 FADE-001 的交叉：恢复配方第六源（周平面每日进度）由 FADE-001 维护项②承接（spec L71），其自动化生产者 `daily_progress_patrol.py` 是 FADE-001 域资产（LG-011），在本域扮演「最后恢复防线」。

### 1.4 当前档位的诚实读数

spec 头部 L8 状态行：**FADE 兼容档**（2026-08-28 升格联审修后放行——双席共识+主持人合成；原探索期）。为什么不是完整档也不是原样探索期：登记册口径「完整实例=十段齐+实跑过+评分通过」（registry L11）；FADE-007 的 Score 双段当时零实跑，跳档=自违反细则 10，所以按 FADE-003 降档先例升**兼容档**+补齐路线（升格材料包 `docs/execution/fade-007-upgrade-review.md` §一 L14-21 的裁决建议，联审采纳）。

## 二、理论底座：FADE 十段协议怎么读

### 2.1 协议管不变量，实例管载体

FADE 生命周期十段：事件触发 → 登记（运行标识）→ Qualify → Plan Skill → DCE → Verify(可选) → Score CLI → Score Skill → Close Skill → Close CLI → 终态（protocol-spec L95）。v1.4.0 立法分层模型（protocol-spec §2.8 L227-234）：协议层只约束每段职责不变量与产物合同；实例层选择具体载体，入册时声明「段-实现映射表」。这解释了为什么 FADE-007 的「登记」可以是「full-时间戳命名+四件套互引」而不是 runId 字符串——登记段四不变量（唯一/去重/关联/恢复锚，protocol-spec L241）满足即可。

### 2.2 三档与升格口径

三档（protocol-spec L97）：FADE 完整实例（十段齐、实跑过、评分通过）/ FADE 兼容档（核心段有、个别段待补）/ 纯确定性执行脚本。升格验收口径（L99）：逐段能指到**真实工件**，缺段即降档，必须带完整试卷与评分通过记录，不允许口头宣称。这套口径直接决定了 §三 里每一段的「诚实档位」写法。

## 三、协议十段在 FADE-007 的逐段落地形态

### 3.1 映射总表

真源两处：spec §6.4 十段表（L100-109）与材料包 §二 十一段映射表（L23-39，多一行「终态」）。下表合并两者，锚全部补到 file:line：

| 段 | 诚实档位 | 载体形态 | 不变量证据锚（file:line） |
| --- | --- | --- | --- |
| 事件触发 | 部分 | 董事会指令（压缩/清空/快照令）；水位启发式无机械载体 | full-1510Z 产出令与 E-2 重建令实跑（spec 运行日志 L123/L127）；指令存转录 jsonl 可归因（spec L27） |
| 登记 | **已实测** | full-`<ts>`.md 单调命名 + ledger-mirror + board-journal + daily-progress 四件套互引 | 双代快照 full-20260828T0330Z/full-20260828T1510Z 在盘（Glob `.fade/hub-snapshots/` 实测四文件）；E-2 凭五源定位现场全对（spec L127） |
| Qualify | 纸面 | 水位/变化判定散文启发式；恢复完整性判据在案 | spec L73 判据文本（「新中枢状态条能否复述台账现役清单与未完事项」） |
| Plan | 部分 | 八节快照模板+对比核验法声明；试卷未冻结 | 模板被 full-1510Z 实产消费（full-1510Z L7-60 八节齐）并被 E-2 重建体用作工作记忆组织；试卷=未冻结草稿（fade-007-assessment-paper.md L8） |
| DCE | 部分 | 流程 A 五步（spec L28-36）/流程 B 六步（L40-47）/恢复重建配方（L66-71） | 流程 A 仅蓄水步实跑；流程 B 零实跑；恢复重建全链已实测（E-1 49s L126 / E-2 L127） |
| Verify | 部分 | 董事会人工 diff（full vs post 逐项比对，拿不准升 CEO，spec L33-34） | E-2 验收=人工 diff 一例（L127）；hub-snapshot-diff exit code 门落地，首跑随 E-3（L105） |
| Score CLI | 纸面→载体已落地 | `scripts/fade/hub-snapshot-diff.py` 结构化 JSON 输出 | 工具在盘（本文 §6.1 逐段导读）；覆盖评分实跑待 E-3（spec L106） |
| Score Skill | 纸面 | 重点丢失语义判定方法未成文 | 无成文方法锚（材料包 L34）；E-2「全对+hash 级锚点」是验收叙述非成文评分 |
| Close Skill | 部分 | 核验裁决三态（通过/打回重压/升级 CEO，spec L34） | E-2 裁决 PASS+重建体转正令=人工先例一例（L127）；成文词表缺位 |
| Close CLI | 纸面 | 裁定=(c)+(a)：close manifest 由确定性小程序写出入仓+快照本体归档 `.fade/archived/`；(b) 白名单入仓否决 | spec L109；第 11 缺口（对比记录与 CEO 确认记录入 manifest，审计链不能断在窗内） |
| 终态 | 部分 | 压缩闭环/清空过渡完成/恢复闭环 | 恢复闭环实跑=E-2 重建体转正接续本尊（xiaojia-hub-r2，spec L127；daily-progress L40 恢复指针在卷） |

### 3.2 统计口径的一个真实细节

spec L111 写「已实测 1/部分 6/纸面 4」（合计 11），但 §6.4 表格只有 10 行。差的一行是「终态」——它登记在材料包 §二 映射表第 37 行（终态=部分），统计沿用材料包十一行口径。接手时别把这点当矛盾报上去：两份真源口径一致，只是 §6.4 表省略了终态行。这类「表行数与统计基数」的错位是读治理文档的常见坑，先找口径出处再下结论。

### 3.3 逐段展开：为什么这样落地

- **事件触发为什么先靠指令**：探索期不造机械水位探针，先让董事会人判「降雨量+水位接近阈值」（spec L29 启发式：会话轮数/任务体量/中枢自报负载）。机械载体列功能期方向（确定性只读探针，触发权留董事会，spec L100）——注意是只读探针，因为触发权不能下放给被压缩方自己。
- **登记为什么是四件套而不是 runId**：协议层判例（protocol-spec L262）runId 单一字段非必须、等价聚合键必须。本域的聚合键=full-`<ts>` 单调时间戳命名（UTC Z 机器轨，D-04 v4，这是 full-0330Z L20 决策 D2 的记录），四件套互引聚链提供关联性，E-2 实测提供了恢复锚证据。去重靠命名幂等（同名时间戳不重产）。
- **Qualify 为什么诚实标纸面**：判定逻辑（水位高低、变化有无）目前是散文启发式，没有机械门。纸面法不冒充已强制，这正是 spec §2.8 细则 10「接线+实测才算立法完成」在本域的自我适用（材料包 L10 诚实声明）。
- **Verify 为什么人工先行**：压缩的「重点丢失」是语义判断，探索期由董事会人工 diff 兜住；确定性工具（hub-snapshot-diff）只管结构门与条目集差素材，语义裁决留给 Score Skill（工具 docstring L13-14 明写「本工具无 LLM、不做可接受性裁决」）。
- **Close CLI 为什么选 (c)+(a)**：快照目录随 `.fade/` gitignore 不入仓库（spec L61），归档持久化若走白名单入仓就破了这条制度，故否决 (b)；改用 run-root 式清单 hash 载体（对齐 FADE-006 v2 schema 先例）+本机归档 `.fade/archived/`（spec L109）。同时立了第 11 缺口：对比记录与 CEO 确认记录必须进 manifest——审计链不能断在会话窗内。
- **组织者利益声明（在册义务）**：组织者=本域唯一执行体（董事长助理），自证风险结构性存在，所以 Score/Verify/Close 段证据双席抽验常设（spec L114；试卷 §三 L56-59）。

## 四、最小闭环：先用 E-2 把恢复全流程走通一遍

按教学协议，先看一条已实测的最小闭环——E-2 双崩演练（S3 场景），它把「快照→死→重建→复述→转正」整链跑通（spec 运行日志 L127；材料包 §五 第 1 条）：

1. 触发：中枢停止（模拟爆上下文死亡）+jsonl 不可读（模拟 S3 双崩）。
2. 重建：一个零背景重建体按六源配方依序读盘重建（配方见 §5.4）。
3. 核验：重建体状态条复述台账 4+6+M-001 全对（当时的现役/销账计数+元项读数），且带 hash 级锚点（995bd161、9d97f563 等可回指 commit）。
4. 双观测自纠：重建体自己发现并纠正两处文档漂移——spec 双 §九（protocol-spec 确实存在两个「## 九」标题：L505「实施要求」与 L532「立册与升格」，v2.0.0 迁移遗留，本教程已实读核实）与 ledger-mirror frontmatter 时刻滞后。
5. 转正：裁决 PASS，重建体转正为本尊（xiaojia-hub-r2）——这就是本实例「终态」段唯一的实跑样本。

为什么拿它当 MVP：它证明了六源配方的**消费端**成立——盘上工件齐、判据可执行、损失边界（末次状态条后的细粒度增量）被一任务一状态条纪律压到最小（spec L81）。压缩/清空面向（流程 A 放水四步、流程 B 全链）还没有同等待级的实跑，这是升完整的剩余路径。

## 五、两条流程与工件族

### 5.1 流程 A：受控压缩五步（spec L28-36）

```text
1. 触发：董事会判断降雨量+水位接近阈值
2. 蓄水：令中枢产出全量自述快照 full-<ts>.md（结构化八节）
3. 放水：令中枢基于快照重建精简工作记忆
4. 对比核验：董事会取 full 与压缩后重产的 post-<ts>.md 逐项比对——重点丢失即打回重压；拿不准→升级 CEO
5. 放水完成：核验通过后删除临时快照（或归档），压缩闭环
```

实跑现状：仅第 2 步（蓄水）有真实样本——full-20260828T1510Z（spec L104「流程 A 仅蓄水步实跑」）。放水/post/对比/闭环四步零实跑，是 E-3 演练要补的链。快照八节以实产结构为基座（2026-08-28 议题⑦模板对齐回写 §五，spec L53）：任务面/决策记录/挂账台账/关键 commit 与路径锚/授权边界/未完事项/教训/上下文风险自评。对照实产 `full-20260828T1510Z.md`：`## 一、任务面（增量）`到`## 八、上下文风险自评`（L7-60），与 `scripts/fade/hub-snapshot-diff.py` 的 DEFAULT_SECTIONS（L38-47）逐节同名——模板对齐这条硬门已落，工具的子串匹配设计（见 §6.1）就是为容错「一、」「（增量）」这类标题变体。

### 5.2 流程 B：清空过渡六步（spec L40-47）

```text
1. 触发：运行时长超限或压缩次数 ≥2（闹钟职责）
2. 蓄水：同流程 A 第 2 步
3. 核验：董事会比对
4. 过渡：核验后的摘要留存董事会上下文（记事本职责）——中枢清空为全 0
5. 问答期：中枢工作时有不懂可反问董事会（摘要在董事会侧）
6. 退役：中枢重新积累成熟后，董事会暂存摘要删除——清空过渡完成
```

全链零实跑（spec L104），E-4 演练补。设计要点：流程 B 与 A 的本质差别是**摘要的存放位置**——A 的摘要在盘上（快照文件），B 的摘要暂存在董事会会话内，中枢归零后靠问答期兜底，直到新记忆成熟再退役。

### 5.3 工件族（spec §五 L51-59 工件表）

| 工件 | 路径 | 职责与设计理由 |
| --- | --- | --- |
| 全量快照 | `.fade/hub-snapshots/full-<ts>.md` | 中枢自述八节；压缩/清空/基线三用途；双代实测同构（0330Z/1510Z） |
| 压缩后快照 | `.fade/hub-snapshots/post-<ts>.md` | 压缩后同结构重产，供 diff |
| 董事会记事本 | `.fade/hub-snapshots/board-journal.md` | **append-only** 增量日志（董事会职责件）：基线快照之后的中枢交付增量，双重故障时的挖矿恢复源（spec L55）。在盘实态：L1-3 题头+L5-26 增量段（LG-008 闭合/LG-009/治理更名/LG-001/LG-002/其他）+L28-33 内嵌四行恢复配方 |
| 台账镜像 | `.fade/hub-snapshots/ledger-mirror.md` | 挂账台账写时镜像（中枢维护，双层保障，spec L56）。真源在记忆目录 open-items-ledger.md（full-0330Z L7）；本文件 frontmatter 仍带记忆侧元数据（L2-9 `name: open-items-ledger`）——镜像属性的在盘证据 |
| run root | `<树>/reports/run-root.json` | 单树收口完整性基线（v2 schema，spec L57；属 FADE-006 域工具族） |
| 对比记录 | 董事会上下文（过渡期） | diff 结论与 CEO 确认记录；Close CLI manifest 立法后须入仓（第 11 缺口） |
| 结构化 diff | `scripts/fade/hub-snapshot-diff.py` | 一具两段（详见 §6.1） |

两个接手必知的实态细节：

- `.fade/` 随 gitignore 不入仓库（spec L61）——所以上面四件在盘工件只存在于本机，三端不可恢复性由第六源 daily-progress 补（它随 git 三端，spec L71「机器全灭时的最后恢复防线」）。
- board-journal L28-33 内嵌的恢复配方是四源旧版（17:2x 建档时写的），spec §五 L66-71 已扩为六源——**恢复时以 spec 为准**，这正是 E-2「双观测自纠」式文档漂移的又一实例，读工件先对真源版本。

### 5.4 五源恢复配方+第六源（spec L66-71）

双重故障（董事会 clear ∥ 中枢爆上下文不可恢复）时，新中枢按序重建：

1. `CLAUDE.md` 分权制节（自动加载：角色/白名单/判据口诀）——`TriMetaverse/CLAUDE.md` L33-39，五条：董事会边界/助理边界/无小任务豁免判据口诀/上下文管理/冲突时以仓库治理文档为准重建助理。为什么排第一：它零成本自动加载，先把「我是谁、听谁的」装回去。
2. board-journal + ledger-mirror（增量交付与台账现势）——E-2 实测命中为第二优先恢复源（材料包 §五 第 5 条）。
3. full-*.md 最近基线（工作记忆结构模板）——0330Z/1510Z 双代在盘。
4. fade-protocol-spec + fade-registry（协议与实例现状）——现行 v2.0.3/v2.1。
5. 董事会转录 jsonl 挖矿（`.claude/projects/` 下本会话文件）——中枢交付物全文留存于此，/clear 不删盘上文件；API 断连后 transcript 续跑零损失恢复（2026-08-28 17:2x，架构首证，spec L124）用的就是这一层。
6. 周平面每日进度（`docs/workflow/operating-records/<周>/daily-progress.md`）——仓库级粗粒度兜底，随 git 三端（本地/sg-bare/GitHub），机器全灭时的最后防线；FADE-001 扩维承接，commit 83753b74 补入（daily-progress L42 该提交主题行在卷）。

恢复完整性判据（spec L73）：**新中枢状态条能否复述台账现役清单与未完事项；有缺→董事会记事本补投**。这条判据后来成为试卷 T7（权重 20，全卷最高，paper L29）——恢复面是本域实测最充分的面，权重分配如实反映了这一点。

### 5.5 S1-S3 故障场景枚举（spec L75-83）

| 场景 | 董事会 | 中枢 | 恢复路径 | 实测状态 |
| --- | --- | --- | --- | --- |
| S1 董事会 clear | 对话窗清，jsonl 落盘仍在 | 存活 | 新董事会按 CLAUDE.md 分权制节自动指路→发「董事会恢复」→中枢状态条全量回报（零损失） | 设计在案，**未演练**（材料包 L92 明示不计入实证） |
| S2 董事会崩+jsonl 不可读 | 重建 | 存活 | agent 寻址为机器级→新董事会按名直连存活中枢→令其中枢自产全量快照落盘→从盘读取 | **E-1 演练 PASS** |
| S3 双崩 | 重建 | 重建 | 六源配方；损失边界=末次状态条后的细粒度增量 | **E-2 演练 PASS** |

E-1 细节（spec L126）：全新会话（零背景）经系统注入存活清单发现 xiaojia-hub→名字直连→回执 49s 全链闭环。两条收获如实记录：notify_when_idle 对 teammate 会话不支持；发现途径实测为注入清单（ListAgents 工具非必需）——「机制在册未实测」的假设被实测修正，这就是演练制度的价值。

E-2 细节见 §四。S2 寻址的机器级属性值得展开：subagent 会话是可按名字寻址的系统对象，不依赖人类操作者转发——这把「董事会崩了」从人工灾难降级为机械重启。

## 六、工具族代码导读

### 6.1 hub-snapshot-diff.py（`TriMetaverse/scripts/fade/hub-snapshot-diff.py`，376 行）

定位（docstring L2-16）：**一具两段**——Verify 段消费 exit code（确定性门），Score 段消费结构化 JSON（覆盖评分素材）；升完整时映射表两行绑同一载体，防 §7.4 双实现（spec L115）。确定性边界五条（docstring L7-14）：①节结构对齐（节名清单配置化，标题子串匹配）；②锚点提取校验（仅 ≥7 位 hex 记锚点，L51 `HEX_RE = re.compile(r"\b[0-9a-fA-F]{7,64}\b")`）；③条目集差（full 有 post 无，锚点级+行级）——**输出为 Score 素材非门禁错误**；④计数守恒；⑤「重点丢失」语义判定留 Score Skill，本工具无 LLM。

核心链路（按调用序）：

- `parse_sections`（L56-63）：按 `^## ` 标题切节。为什么只认二级标题：快照八节约定就是 `## 一、任务面` 层级，一级标题是文档名，三级是节内小节。
- `find_section`（L66-71）：子串匹配容错——`"任务面" in "一、任务面（增量）"` 命中。这是双代实测同构后仍需要的防御：标题后缀会带（增量）/（不变，增量提醒）这类状态注记（full-1510Z L7/L37 实证）。
- `extract_anchors`（L74-76）：≥7 位 hex token 归一化小写取集合。7 位下限=git 短 hash 惯例下限，64 上限=全 hash。
- `extract_lines`（L79-88）：bullet 行去符号压空白归一——同一条目换个破折号不构成丢失。
- `diff_snapshots`（L91-141）：逐节比对锚点集差与行集差；**计数守恒**（L129-138）：各节 missing 之和必须等于 items 总数，否则记 `conservation_violation`——这是 protocol-spec §2.2 四不变量（结构化/守恒/errors>0→rc=1/action 词表契约化，L118）的落地。action 词表硬编码断言在 L139-140（`section_missing/anchor_missing/line_missing/conservation_violation`）。
- rc 语义（L16+L372）：仅结构性违规（节缺失/守恒破坏）→rc=1；**条目集差只进 JSON 不动 rc**。为什么：压缩本身允许精简，39 条集差可能是合理演进，删节才是违规。这个区分是本工具最容易用错的地方。

验收记录（在卷，本教程未代跑）：真实两代 0330Z vs 1510Z → pass（errors 0，条目集差 39=9 锚+30 行，演进素材）；合成篡改对照 → rc=1（section_missing「教训」，守恒 7=7）（paper §二 L53、daily-progress L22，commit f902cd2b）。内置自测 15/15 pass（`--self-test`，四组 Case：A 完整承袭 pass/B 篡改件 fail 且 deadbeef 锚进 items/C 节清单缩域后结构通过/D 双侧缺节两侧报——L272-307；15 个断言数=4+8+2+1，与代码逐一可对）。

上手命令（引自 docstring L19-21，接手时先跑第三条）：

```bash
python scripts/fade/hub-snapshot-diff.py --full <path> --post <path>
python scripts/fade/hub-snapshot-diff.py --full a.md --post b.md --sections "任务面|决策记录"
python scripts/fade/hub-snapshot-diff.py --self-test
```

### 6.2 daily_progress_patrol.py（`TriCompany/runtime/cognition/daily_progress_patrol.py`，951 行）

定位（docstring L2-8）：FADE-001 维护项②「每日工作进度」巡检兜底（LG-011）——**第六源的生产者**。主=事件驱动（助理增量即写，元项 M-002 接线，ledger-mirror L26-28），辅=本脚本 TriMC cron 每 10 分钟（job d0f87756，runAs fleet，daily-progress L18）。它归 FADE-001 域，但 FADE-007 新人必须懂它：最坏丢失窗口从 23h 压到 10 分钟靠的就是它。

四种模式（docstring L31-33）：默认 dry-run（只读报 would-write）；`--sync` 写入+commit+push；`--self-test` 沙箱验证套件；`--score` 对指定日产 shadow 评分 envelope。

关键机制逐个讲：

- **拓扑门限**（`commits_since` L177-208）：机械门=自上次进度条目后新 commits>0。实现不是「时间戳严格大于」而是 `git log <touch_full>..HEAD` 拓扑口径——因为 20:20 tick 实测抓过同秒缺陷（rebase 连发使 marker 与进度提交同秒，门限误闭合），修复 3082d7d；Case I 同秒回归在卷（L784-802）。教训同款：边界条件必须用真实故障驱动出回归测试。
- **单写者原则**（docstring L21-24+L420-441）：巡检只补漏（append）不重写；与助理事件驱动写冲突用 `pull --rebase` 重试一次、再失败跳过本轮（下轮再补）。写前存 `pre_bytes`，写后 `verify_day_section` 回读自检（当日节存在且非空、追加块在卷、标题格式合规，L281-299），失败回滚。
- **自愈重推**（L372-379）：上轮 push 失败遗留的未推提交在下轮开头先重推——否则「文件已被自己触碰→门限闭合→永不重推」死锁。
- **三端持久纪律**（L453-464）：sg-bare 必达（失败不伪造终态，commit 留在舰队克隆等自愈）；GitHub best-effort 失败不阻塞（无凭据时 `GIT_TERMINAL_PROMPT=0` 快速失败，L103）。
- **数据边界的一个真实删除裁定**（docstring L14-19）：ledger-mirror 是机器本地不入仓的，服务器巡检读不到——所以门限仅用 git commits。ledger-mirror mtime 门限分支曾入 49287fc 设计，2026-08-28 升档联审裁定删除（「未实现未接线的纸面设计=审计负债」）。这是细则 10 精神落到代码设计史的实例：纸面设计留在 docstring 里当教训，不留在代码里当死分支。
- **--score 五约束**（L469-474 注释+实现 L603-668）：T3 事件及时性/T7 治理对齐留 Score Skill 禁自动化；T5 网络降级=「不可验」非 FAIL；scoreable run=自然日含事件驱动写与巡检补写各 ≥1（skip-only 不可评）；首评期 shadow 只观测不拦截（envelope 里 `gate_wired: False`，L661）；T8=载体运行时健康项非 run 产物项。确定性检查 T1/T2/T4/T5/T6/T8 权重 15/15/15/10/15/10（小计 80，L67），T3/T7 外置 10+10，阈值 90（L69）——注意这是 **FADE-001 的卷**，别和 FADE-007 的 85 混淆。T2 及时性阈值 T2_MAX_GAP=780s（tick 600+timeout 180，L64-66）。
- 自测计数演进（均为在卷记录，本教程未代跑）：上线 21/21（spec L128）→三迭代后 24/24（ledger L79）→--score 版 30/30（daily-progress L23）。

### 6.3 _fadehash.py（`TriMetaverse/scripts/fade/_fadehash.py`）

存在性经 Glob 核验（scripts/fade/ 六件之一）。职责：单一 canonical 的 dual_sha256 双 hash（raw+LF 双口径，行尾漂移按 SOFT-DRIFT 留痕不按污染裁决）——出自 LG-008 调和案 D8「CPO 单一 hash 纪律 × CTO 分文件结构调和」（full-1510Z L19；registry L170 配套工具族行）。在 FADE-007 的消费点：试卷冻结程序第 3 步「定稿卷以 `scripts/fade/_fadehash.py` 计算整卷双 hash raw+LF canonical」（paper L65）。为什么需要它：markdown 文件 CRLF/LF 漂移会让裸 hash 不可比，双 hash 让「内容相同但行尾不同」可被识别为软漂移而非篡改。

## 七、本周真实运行证据（2026-08-28，spec §七 L120-129 运行日志七行）

运行日志逐行（时刻+08）：

| 时刻 | 事件 | 本教程核验锚 |
| --- | --- | --- |
| 01:0x | 首次拉起 xiaojia-hub（就任核查+台账建册 LG-001..005 全过）；基线水位=低 | spec L122；full-0330Z L73「当前水位：低」 |
| 15:10 | 基线快照 full-1510Z；ledger-mirror 写时镜像生效 | spec L123；full-1510Z 在盘（L1-6） |
| 17:2x | 中枢 API 断连死亡→transcript 续跑零损失恢复（架构首证）；board-journal 建档 | spec L124；board-journal L3「记录基准=15:10Z 基线快照之后」 |
| 19:0x | 双重故障恢复配方入 spec；LG-008 验收实测抓出 run-root 覆盖写缺陷→修复 9d97f563+append-only 复验 PASS | spec L125；board-journal L10 同弧线 |
| 19:1x-19:3x | E-1 演练 PASS（49s 闭环） | spec L126 |
| 19:1x-19:3x | E-2 演练 PASS（双崩五源重建→4+6+M-001 全对→转正 xiaojia-hub-r2） | spec L127 |
| 20:0x | LG-011 巡检兜底上线（patrol v1.0 21/21 + cron d0f87756） | spec L128；daily-progress L18 |
| 21:4x | 兼容档升格（双席共识+主持人合成；统计 1/6/4；模板对齐回写；diff 工具落地；E-3 冻结卷备妥） | spec L129 |

commit 核验清单（全部经 Read 从在盘文件核验出处；无一凭记忆）：

| commit | 内容 | 在盘出处 |
| --- | --- | --- |
| 7290bf31 | 恢复配方入 spec | spec L112；daily-progress L39「fade-007 spec（@7290bf31 系）」 |
| 90bd8fc9 | S1-S3 场景枚举立法 | 材料包 §五 第 4 条（L89） |
| 83753b74 | 第六源补齐 | daily-progress L42 巡检补写行引用其提交主题全文 |
| 17a4af84 | daily-progress 建档 | spec L112；daily-progress L41（作为门限基线 commit 出现） |
| 9d97f563 | run-root 覆盖写修复（邻域 FADE-006） | spec L125；board-journal L10；ledger L89 |
| 07e44962 | 升格联审材料包 | spec L96；daily-progress L21 |
| 509ec99d | 兼容档立法包（§6.4+模板对齐+五条硬门+利益声明+Close CLI (c)+(a)） | daily-progress L22 |
| f902cd2b | hub-snapshot-diff.py 落地（自测 15/15+两代验收） | daily-progress L22；paper L23/L53 |
| 67cbdecb | E-3 冻结卷备妥（T1-T8 权重 100/双门槛 85/抽验义务/冻结程序） | daily-progress L22 |
| 995bd161 | 分权制更名立法 | ledger L16；board-journal L17；daily-progress L15 |
| 3082d7d | patrol 拓扑门限修复（邻域 FADE-001） | daily-progress L19；ledger L80 |
| 30e8dc02 | 任务简报标注为 E-1/E-2 运行日志落盘提交 | **诚实标注：本教程仅在盘文件通道（Read/Glob）未能找到该 hash 的在盘出处**；E-1/E-2 事实以 spec §七 L126/L127 为准，hash 请接手者用 `git log --oneline` 自行补验后再引用 |

数字核验声明：文中 49s、4+6+M-001、15/15、39=9+30、7=7、T1-T8 权重、85/90 阈值、780s、统计 1/6/4、各评分带（001 90/002 90→93/003 80→98/004 81→88/006 80→91）均逐一回到上表文件行；其中评分带出处=registry L62/L84-85/L108/L110/L131/L151-152。

## 八、故障弧线与教训

### 8.1 覆盖写缺陷弧线（邻域学费，如实标注不冒领）

弧线（ledger L88-91+board-journal L10+spec L125 三处在卷互证）：LG-008（FADE-006 升格）验收时，复验探针实测抓出 run-root.py **整文件覆盖写**缺陷——初版代码注释里写「appendOnlyNote：另档新文件」，代码路径却是覆盖写同一文件；配套还有首算 producedAt 缺失与 UTF-8 两缺陷。修复=9d97f563（append-only recompute_history 同文件追加+首算必填+显式声明）+自测 10/10，编排层独立复验 ALL PASS——复验探针被 append-only 正确吸收为 history 第 3 条，设计经外部探针实战检验。

归属诚实声明（材料包 §五 第 6 条，L91）：该判例属 LG-008/FADE-006 域学费，**不冒领**；但它反哺了本域 board-journal 的 append-only 设计（17:2x 建档行承接，间接学费）。细则 10 归属注记：spec L125 称其为「细则 10 第 4 判例」，而 protocol-spec L266 文本现记录「判例×3」（v2.0.2 定级时点）——交叉文档未同步，引用时以 FADE-007 spec 行为准并注明差异。

沉淀教训（ledger L91 原文口径）：整文件覆盖写是 append-only 立法的头号违反形态——**「永不覆盖」必须落为代码路径而非注释口径**。这句话适用于一切审计件：board-journal、ledger-mirror 的 append 纪律、patrol 的 T4 检查（patrol 身份提交删行即违规，代码 L546-554）都是它的展开。

### 8.2 本域弧线与自愈样本

- API 断连（17:2x）：中枢死亡但 transcript 续跑零损失——证明了第五源（jsonl 挖矿）的底噪价值，也直接催生了 board-journal 建档（单一 jsonl 依赖不够，要第二挖矿源）。
- E-2 双观测自纠：重建体主动发现 spec 双 §九（protocol-spec L505/L532 两个「## 九」，本教程实读核实仍在）与 mirror frontmatter 滞后——说明恢复判据不只是复述，还包括**对真源版本的批判性核对**；文档漂移靠消费者发现并留痕，比靠维护者自觉可靠。
- 巡检门限同秒缺陷（邻域）：时间戳比较被同秒连发击穿→拓扑门限修复 3082d7d+Case I 回归。第六源的健壮性由此而来。
- 模板漂移（缺口 10，材料包 L82）：spec §五八节清单与实产快照结构（含「上下文风险自评」节、合并「关键 commit 与路径锚」）一度措辞不一致——议题⑦联审裁决按实产八节对齐回写 §五（spec L129）。教训：模板应以实产为基座反向修法，而不是让实产迁就纸面。

### 8.3 教训清单（接手前背下来）

1. append-only 必须是代码路径，不是注释。
2. 评分基准不可自改考卷——试卷 Plan 时点冻结+语义作业方案卷封不涵盖试卷（protocol-spec §2.6 L193）。
3. 纸面设计未接线即审计负债（patrol mtime 分支删除先例）。
4. 边界条件（同秒/漂移/行尾）必须有真实故障驱动的回归。
5. 镜像不是真源：台账真源在记忆目录 open-items-ledger.md，ledger-mirror 是双层保障镜像，daily-progress 是粗粒度镜像——三层各有用途，恢复时按配方顺序取。
6. 机器本地工件（.fade/）与三端持久工件（daily-progress）必须分层设计，单一层不可靠。

## 九、评分卷宗解读：为什么 FADE-007 还没有评分卷

事实：`TriCompany/docs/engineering/fade-papers/` 下没有任何 FADE-007 卷宗（本教程 Glob 实测，该目录 35 个文件止于 FADE-006 与 001/003 扩维卷）。FADE-007 现有的「卷」是**未冻结草稿**：`TriMetaverse/docs/execution/fade-007-assessment-paper.md`（L8 状态行明写「未冻结草稿——冻结时点=E-3 的 Plan 时点」）。**升完整前置=先有评分卷**，这是硬门链条的第三环。

草稿已备好的要素（供提前解读）：

- T1-T8 检查项与权重：15/10/10/10/10/15/20/10=100（paper L21-32）。逐项：T1 八节结构（Score CLI 门）、T2 锚点 ≥7hex、T3 ledger 三计数双读数（现役/销账/元项；2026-08-28 样本 4/8/2，L52）、T4 board-journal append-only（git diff 仅增量）、T5 六源在位可读、T6 post 对 full 结构化对比（Score CLI 出素材+Skill 语义裁决）、T7 复述判据（权重 20 最高）、T8 分权制治理对齐（M-001 date 接线/白名单口诀/投递判据/单写者分权）。
- 双门槛：必选 T1-T8 全部通过+总分 ≥85（paper L41-42；85 为升格联审合成裁定定值，spec L113「双门槛 85 达标」）。不过线 → RETRY 或 ESCALATED，不得写终态（protocol-spec §2.6 L183）。
- 实时部分按 run 类型实例化（paper L44-48）：压缩 run 查 T6 逐条三态裁决（可精简/重点丢失/存疑升级）；恢复 run 查 T7 复述细目；清空 run 加编排层摘要留存项。
- 判定人独立性：T3/T7/T8 首 3 个功能期 run 双席抽验常设（paper L59）——对冲组织者自证风险。
- 冻结程序五步（paper L61-67）：E-3 真实压缩需求触发→按当日实况定稿（修订留痕）→_fadehash 双 hash→hash 入 E-3 run 登记段与 run root 引用集→DCE 期间不可变+评分对卷。

参照带读数（帮你校准 85 的松紧）：FADE-001 90、FADE-002 90→93、FADE-003 80（卡线降档教训）→升档首评 98、FADE-004 81→88、FADE-006 80（卡线冻结）→增评 91。85 不是宽松线——FADE-003/006 的首评都曾卡在 80。

升完整五条硬门时序（spec L113，链锁死）：模板对齐（已落）→ hub-snapshot-diff 落地（已落）→ 试卷冻结（E-3 Plan 时点，待）→ E-3 受控压缩真实事件（FADE-006 AC-4 口径：人为构造触发可、链路与产出全真实）→ E-4 清空过渡真实事件 → 双门槛 85 达标 → 升完整入登记册。补齐项挂两次周检齿条（spec L116）。

## 十、与 FADE 协议 v2.0.0（§2.7/§2.8）对照

### 10.1 §2.8 段合同对照（协议管不变量，实例管载体）

- **登记四不变量**（protocol-spec L241）：唯一性=full-`<ts>` 单调命名；去重性=命名幂等（无重复样本，机制口径——材料包 L28 如实标注）；关联性=四件套互引聚链（full-1510Z §三引台账真源、§四引 commit 锚）；恢复锚=E-2 凭五源定位现场全对。四条全部有载体或如实标注口径，这是「已实测」档位的含金量。
- **DCE 载体降级合同**（细则 4，protocol-spec L260）：agent 会话承载 DCE 时，不变量降级为「先写后报+原子即提交+节点收口报告」。本域 DCE 主体是助理会话（快照产出=先写后报），逐节点门禁不适用——FADE-007 是单会话交互域，无多节点树。
- **§2.7 节点收口报告的适用边界**：registry L17 补课范围裁定「节点收口报告仅适用多节点树实例——001/002/003 单段脚本/CLI 实例豁免」。FADE-007 同理豁免，它的对应物是**状态条**（一任务一状态条纪律，spec L81 损失边界的压控手段）——但注意状态条在会话窗内，不落 reports/，所以第 11 缺口才要求把对比记录与 CEO 确认记录写进 close manifest（spec L109）：审计链不能断在窗内。
- **载体显式度分级**（细则 5，L261）：单一显式标识优于分散组合。本域当前是分散组合（时间戳+四件套互引），材料包未把升 runId 列为补齐项——因为时间戳命名在本域承担了唯一标识职责且经 E-2 实测。若未来跨实例战役引用 FADE-007 的 run（细则 6：被引用 run 必须可被单一显式标识引用），需补显式 run 标识。

### 10.2 §2.5 终态门对照

- Close Skill 先出结构化裁决（三态：通过/打回重压/升级 CEO，spec L34），Close CLI 校验并持久化，失败进 CLOSE_REJECTED 不得静默完成（protocol-spec L170-172）。
- 「被裁决会话不得自证终值」（L174，CTO-F7）：本域的落实=Close CLI 裁定明确「组织者会话不自证终值」（spec L109）+close manifest 由**确定性小程序**写出入仓。组织者利益声明（spec L114）是该条款在「人即载体」实例上的延伸。
- 时序约束：本域升完整后必须 DCE→Verify→Score→Close Skill→Close CLI（FADE-001 条目 L66 对同构问题的同款立法可参照）。

### 10.3 §2.6 试卷三不变量对照

paper 冻结程序五步逐条对上 §2.6（L187-193）：Plan 时点冻结（第 1-2 步）/DCE 期间不可变（第 5 步前段）/收口对卷（第 5 步后段「实际使用卷 hash 必须等于冻结卷 hash」）+试卷 hash 入 run root 引用集（第 4 步）。E-3 冻结卷虽已备妥（67cbdecb），**冻结动作本身必须发生在 E-3 的 Plan 时点**——提前冻结会违反「按当日实况定稿」的程序要求（paper L64）。

## 十一、新人学习路径与接手任务

### 11.1 学习路径（先读什么、每步验证方式）

| 步 | 读/做 | 验证方式 |
| --- | --- | --- |
| 1 | `TriMetaverse/CLAUDE.md` L33-39 分权制节+本教程 §一 | 能向同事口述四角色隐喻与分权根基 |
| 2 | spec 全文（130 行，短）逐节读，对照本教程 §三§五 | 能逐段说出十段档位与「为什么」 |
| 3 | 材料包 §二§五+registry L11/L97 三档口径 | 能解释为什么是兼容档不是完整档 |
| 4 | `python scripts/fade/hub-snapshot-diff.py --self-test` | envelope status=pass、checks=15 |
| 5 | 读 `.fade/hub-snapshots/` 四件实态+spec L66-71 配方 | 能指出 board-journal 内嵌配方是旧版、以 spec 为准 |
| 6 | patrol docstring+`--self-test`（TriCompany 侧） | 记录 envelope；对照 §6.2 读懂拓扑门限与五约束 |
| 7 | paper 草稿+registry 参照带 | 能解读双门槛 85 与 T7 权重最高的理由 |
| 8 | protocol-spec §2.5/§2.6/§2.7/§2.8 回读 | 能完成本文 §十 的对照表默写 |

### 11.2 常见误区

- 把 daily-progress 当日总结——CEO 纠正过：第六源是**恢复兜底**不是日总结（daily-progress L43 巡检补写行引语在卷）。
- 把条目集差当违规——diff 工具 rc=0 但 39 条集差是合法演进（§6.1）。
- 把 board-journal 当可改写日志——append-only 是代码路径级纪律（§8.1）。
- 把 FADE-001 的 90 阈值和 FADE-007 的 85 混用。
- 把 ledger-mirror frontmatter 时刻当新鲜度判据——E-2 实测过滞后，读数看条目与计数。
- 凭记忆报 hash——本文 §七 的 30e8dc02 标注就是反例示范：核验不了就写「未核验」。

### 11.3 接手任务清单（当前开孔）

1. E-3 受控压缩真实事件：构造触发（AC-4 口径）→Plan 时点冻结试卷→跑流程 A 全链（放水/post/对比/闭环四步首跑）→Score 双段首评。
2. E-4 清空过渡真实事件：流程 B 六步全链首跑。
3. close manifest 确定性小程序首跑（载体=(c)+(a)，含第 11 缺口字段）。
4. run↔段证据索引：E-3 起现场建，缺口 4 不事后补（spec L116）。
5. 水位机械化（功能期）：确定性只读探针，触发权留董事会（spec L100）。
6. 补验 30e8dc02（§七诚实标注项）并回写培训材料。

## 十二、使用依据

- 真源：`D:/Code/ai/TriMetaverse/docs/execution/fade-007-context-reservoir-spec.md`（§一~§七+§6.4+运行日志）；`D:/Code/ai/TriMetaverse/docs/execution/fade-007-upgrade-review.md`；`D:/Code/ai/TriMetaverse/docs/execution/fade-007-assessment-paper.md`。
- 协议与登记：`D:/Code/ai/TriCompany/docs/engineering/fade-protocol-spec.md`（§2.5/§2.6/§2.7/§2.8，含 L505/L532 双 §九 实态）；`D:/Code/ai/TriCompany/docs/engineering/fade-registry.md`。
- 代码：`D:/Code/ai/TriMetaverse/scripts/fade/hub-snapshot-diff.py`（全文 376 行）；`D:/Code/ai/TriCompany/runtime/cognition/daily_progress_patrol.py`（全文 951 行）；`D:/Code/ai/TriMetaverse/scripts/fade/_fadehash.py`（存在性核验）。
- 工件实态：`D:/Code/ai/TriMetaverse/.fade/hub-snapshots/` 下 board-journal.md/ledger-mirror.md/full-20260828T0330Z.md/full-20260828T1510Z.md；`D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W35/daily-progress.md`；`D:/Code/ai/TriMetaverse/CLAUDE.md` L33-39；`D:/Code/ai/TriMetaverse/.claude/agents/ceo-chief-of-staff.md`。
- 核验方法声明：全部 hash/数字经 Read/Glob 从上述在盘文件核验；未设 git 运行通道，故「提交级」断言（某 hash=某提交）以文件内引用互证为准，唯一例外 30e8dc02 已显式标注未核验。
