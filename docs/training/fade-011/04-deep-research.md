<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-011/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-011 深度研究——幂等、安全门、解耦设计与工程史

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-011/04-deep-research.md
- syncMode: source-only
- lastSyncedAt: 2026-11-10（代码锚当次实勘）

读者：要维护或改造 EW 的工程师与架构研究者。目标：读懂三个核心设计决策的「为什么」、
两起在案事故的根因归属、改造时哪些面是敏感面——以及哪些结论要等数据、不要预判。

---

## 一、三个核心设计决策（对照触发链注释块 L4286-4311）

### 决策 1：定时轮询指纹（30s），不是实时文件系统 watcher

- spec §8.6 只定原则（检测即触发·触发与执行解耦），实现选型是轮询：`--interval` 默认
  30.0 秒（常量 L4345 `EVENT_WATCH_DEFAULT_INTERVAL`）。
- 为什么选轮询（培训解读，以注释块原文为准）：与守护进程生命周期解耦（重启不丢机制）、
  跨平台行为一致、且能覆盖 **Git 提交层事件**——文件系统 watcher 天然抓不到「一次 commit
  改了十个文件」这种语义单元。代价=最长 30 秒触发延迟，对内部文件同步场景完全够用。
- 查证：

```powershell
Get-Content D:\Code\ai\TriCompany\runtime\cognition\source_publish_check.py | Select-Object -Skip 4285 -First 60
```

### 决策 2：指纹 = 文件 hash 表 ∪ Git HEAD/refs

- 注释块原文表述：指纹取两个来源的并集。
- 为什么两者都要（培训解读）：文件 hash 抓**工作区未提交改动**，Git 状态抓**提交/回滚层
  事件**——单看任一来源都有盲区，并集互为兜底。指纹持久化在
  `<source-root>/.ade/event-watch/state.json`，跨批次、跨重启可比。

### 决策 3：触发面与执行面彻底解耦

- 触发面的全部产出=「开一张 run 工单」（落 operating-records 树）；执行面=五节点链，
  独立演化。
- 架构价值的实证：Phase 2「十段全自动通」改造全部发生在执行面，触发面零改动——
  改执行逻辑不动触发逻辑，两边各自演进互不牵连。

---

## 二、幂等三件套（不重复触发、不乱触发的三层防线）

| 防线 | 机制 | 防的是什么 |
|---|---|---|
| ① 指纹未变 → deduped | state.json 存上次指纹；本次对比相同=无事件，不开工 | 同一批变更被反复扫描时重复开工 |
| ② 首扫只建基线（state_known） | state 无记录时只写入指纹、不触发 | daemon 每次启动都全量触发一轮无意义检查 |
| ③ 批次化去重 | 同一变更产生的文件事件与 Git 事件并集合并，只开一张单 | 「一次提交改 N 文件」被算成 N+1 次事件 |

**失效模式两则（都是实证，不是推演）**：

1. {week} 字面目录事故（2026-11-04）的本质=「执行面代码旧于触发面期望」——排障窗旧代码
   实例触发，路径模板 `{week}` 未被展开。幂等三件套本身没坏，坏的是**发布链**（dist 未重建）。
2. 值席单侧删除事故（2026-10-23 事故卷）的本质=「幂等设计只覆盖触发面，不覆盖档案面」——
   档案的一致性靠 DB checkpoint 与盘面**双记账对账**，任何单侧动手即破坏。
   两起都不姓「触发逻辑」——这是接手者最容易误诊的方向。

---

## 三、安全门三层（写入通道的层层收窄）

1. **dry-run 默认**：检查结果只落 envelope 报告，零写入（spec §2.4 安全门）。
2. **`--auto-sync` 显式开启**：命令行显式传入才允许 sync 类写入——不存在隐式写通道。
3. **project-docs 类别级禁自动写**：代码常量硬编码，连 `--auto-sync` 也不豁免。

第四道辅助闸：**关键文件清单**（两份 manifest + `.agent.md` 后缀，L4319-4325）——
触碰即「建议 sync」。设计取向是宁窄勿宽：触发建议面是敏感面，误报一次 sync 建议
的代价高于漏报一次（sync 本身还有人审）。

```powershell
# 查证：协议两节原文（§2.4 安全门 / §8.6 触发探测）
Select-String -Path D:\Code\ai\TriCompany\docs\engineering\fade-protocol-spec.md -Pattern '^## .*2\.4|^## .*8\.6'
# 查证：常量与关键文件清单定义
Get-Content D:\Code\ai\TriCompany\runtime\cognition\source_publish_check.py | Select-Object -Skip 4300 -First 46
```

---

## 四、工程史三段（它怎么长成现在这样）

1. **002 补齐项期**：EW 机制最早是给 FADE-002（发布域管线）补的触发探测能力——
   `source_publish_check.py` 的 `--event-watch` 参数系（L3546 起）。
2. **独立实例化期**：机制升格为 FADE-011 独立实例；生命周期法条在协议 L449 批认注
   （CTO 2026-11-04 签发·具法条效力）：幂等八段续跑 / EXECUTING 唯一改写段 / RETRY 无出边。
3. **Phase 2 全自动化期**：十段全自动通落地（S1-S5 顺序工序制·排窗已废·完成即报）；
   彩排 S1 评分 14.5/15 在卷（audit 脚本注释引）；开跑后基线数据收集窗中。
   排期单真源：`TriMetaverse/docs/execution/fade-011-automation-phase2-plan-20261103.md`。

现势读数（2026-11-10 实勘）：64 张 run 树在卷，每日审计
（`fade_instance_audit.py`）读数口径=触发量/链成率/verdict 分布，其他实例向 fade011 看齐。

---

## 五、两起事故的工程复盘（教训提炼）

| | 事故一：{week} 字面目录 | 事故二：值席单侧删除 |
|---|---|---|
| 时点 | 2026-11-04（排障窗） | 2026-10-23 |
| 根因 | dist 未重建→旧代码触发，模板未展开 | 绕过双记账纪律，单侧删盘面文件 |
| 裁决 | CTO 裁原地保留（一致性优先） | 事故卷归档+纪律重申 |
| 教训（一句） | 改代码必须连带重建运行时副本（D-03 dist 纪律同族） | 双记账档案禁单侧动手，「删个文件夹」=破坏性操作 |
| 留痕 | 同目录 `README-POINTER.md` | `事故卷-值席违规单侧删除两run树-20261023.md` |

**共同点**：两起都不是触发逻辑的 bug，都是**系统边界外的操作**砸了系统——
守夜人没失职，失职的是绕过门禁的手。接手者在排障时先把这条记牢：先查操作面，
再怀疑机制面。

---

## 六、风险与改造面（培训视角观察·非裁决）

- **改造热区**：回指 [03 代码地图 §四](03-code-map.md)热力图——常量/关键文件清单/触发逻辑
  本体/审计口径/生命周期法条五处，各附改动前必读。
- **候数据不候预判**：开跑后基线数据收集窗中，两轮后升实质结论（CHO 评估注在案）——
  本教程如实记录这个状态，不提前下「运行良好/有问题」的结论。
- **席位纪律提醒**（培训面复述，裁决面在真源）：手动运行=CEO/人工通道；run 树与排障
  产物处置=CTO 裁；审计与报告零 token 值面（D-46 同样约束本实例产物）。

---

## 七、真源指针（教程不替代真源）

- 触发链注释块+常量：`TriCompany/runtime/cognition/source_publish_check.py` L4286-4345
- 协议：`TriCompany/docs/engineering/fade-protocol-spec.md` §8.6 / §2.4 / L449 批认注
- Phase 2 排期单：`TriMetaverse/docs/execution/fade-011-automation-phase2-plan-20261103.md`
- 事故卷与 POINTER：`TriMetaverse/docs/workflow/operating-records/2026-W45/trees/fade011-ew-runs/`
- CEO 裁令：`TriMetaverse/docs/memory/fade011-manual-run-ceo-channel-only.md`
