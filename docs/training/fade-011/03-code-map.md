<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-011/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-011 代码地图——触发链七步与亲手查证

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-011/03-code-map.md
- syncMode: source-only
- lastSyncedAt: 2026-11-10（代码锚全部当次实勘）

读者：要接手 fade011/EW 相关代码的研发新人。目标：30 分钟后，你能对着本地图独立读懂触发链每一步、亲手跑查证命令、知道改哪个文件前先看哪个真源。

---

## 一、文件地图（三个代码正身+两个数据面）

| 角色 | 文件 | 规模/位置锚 |
|---|---|---|
| **EW 实现正身** | `TriCompany/runtime/cognition/source_publish_check.py` | L3546 起 EW 参数系 / L3956 触发面隔离 / **L4286 起 EW 段（触发链注释+常量=最佳读物）** |
| 每日审计 | `TriCompany/runtime/cognition/fade_instance_audit.py` | 全实例执行审计（fade011 系为主） |
| 协议正身 | `TriCompany/docs/engineering/fade-protocol-spec.md` | §8.6 触发探测 / §2.4 安全门 |
| 指纹状态 | `<source-root>/.ade/event-watch/state.json` | 跨批次持久指纹（文件 hash+Git head/refs） |
| 审计卷宗 | `<source-root>/.ade/event-watch/` | events.jsonl 变更日志 + reports/<run_id>.json envelope |

**读代码第一站**：`source_publish_check.py` L4286-4311 的触发链注释块——作者把整条链的
设计意图写成了 24 行注释，比任何教程都权威。本地图第三节就是它的展开。

---

## 二、触发链七步（逐步代码锚+查证命令）

> 第 0 步常识：`--event-watch` 是**独立触发面**——禁止与业务 scope/`--close`/`--score`/`--watch`
> 组合使用（L3956-3965 双入口硬校验，fail-closed）。

```powershell
# 第 0 步查证：看触发面隔离校验
Get-Content D:\Code\ai\TriCompany\runtime\cognition\source_publish_check.py | Select-Object -Skip 3955 -First 12
```

**第 1 步·监听**：默认盯三个目录（`EVENT_WATCH_DEFAULT_DIRS`，L4313）——`source-agents/`、
`docs/engineering/`、`.github/manifests/`；可用 `--watch-dirs` 覆盖。

**第 2 步·指纹**：每次扫描算指纹 = 文件 hash 表 ∪ Git HEAD/refs；与 state.json 里上次指纹对比。

**第 3 步·批次化去重**：同一次变更的文件事件与 Git 事件**并集合并**（同一变更不双触发）；
指纹未变 → action=deduped 不触发；首扫只建基线（state_known）不触发。

**第 4 步·scope 派生**：按变更路径派生检查范围——`source-agents/` 变更→发布一致性检查；
manifest 变更→publish-agents+project-docs；`docs/engineering/` 等→check。

**第 5 步·默认 dry-run**：检查以 envelope 报告输出，**零写入**。

**第 6 步·sync 建议门**：单批次变更文件数 ≥5（`EVENT_WATCH_DEFAULT_THRESHOLD`）或触碰关键文件
（两份 manifest / `.agent.md` 后缀，L4319-4325）→ 建议 sync；`--auto-sync` 显式传入才真写
（project-docs 永不自动写——硬编码）。

**第 7 步·审计落盘**：events.jsonl（变更日志）+ reports/<run_id>.json（envelope）+ state.json（指纹）。

```powershell
# 第 1-7 步一站式查证：读触发链注释+全部常量（最佳读物·24 行注释+常量定义）
Get-Content D:\Code\ai\TriCompany\runtime\cognition\source_publish_check.py | Select-Object -Skip 4285 -First 60

# 参数系查证（--event-watch/--watch/--interval/--watch-dirs/--auto-sync 门/--threshold）
Get-Content D:\Code\ai\TriCompany\runtime\cognition\source_publish_check.py | Select-Object -Skip 3545 -First 65
```

---

## 三、run 树形貌（数据面实锚·2026-11-10 实勘 64 例）

每张自动工单落 `TriMetaverse/docs/workflow/operating-records/<周>/trees/fade011-ew-runs/`：

```
fade-w-fade011-ew-<hash12>/        ← run 树（hash12=运行实例标识）
├── plan.md                        ← 程序化计划（FADE-011 S5.1 driver·plan skill 正身接线）
├── reports/
│   ├── node-qualify.md            ← 五节点报告（链成率审计的计数单位）
│   ├── node-plan.md
│   ├── node-dce.md
│   ├── node-score.md
│   ├── node-close.md
│   └── close-output.json          ← 终态审计输出
└── artifacts/
    └── dce-output.md              ← DCE 段产物
```

```powershell
# 查证：任意取一例核对结构
Get-ChildItem D:\Code\ai\TriMetaverse\docs\workflow\operating-records\2026-W45\trees\fade011-ew-runs\fade-w-fade011-ew-0090af2c1df3\ -Recurse -File | Select-Object -ExpandProperty Name
```

**注意 `{week}` 字面目录**：`fade011-ew-runs/` 下另有一本 `README-POINTER.md` 记载两张落进
字面 `{week}` 路径的 run 树（2026-11-04 排障插曲·dist 未重建旧代码触发）——CTO 裁原地保留，
**接手者勿清理**，先读 POINTER。

---

## 四、改造热力图（哪里最可能动）

| 面 | 位置 | 改动前必读 |
|---|---|---|
| 加监听目录/改阈值 | `EVENT_WATCH_DEFAULT_DIRS/_THRESHOLD/_INTERVAL`（L4313-4345） | spec §8.6+§2.4 安全门 |
| 加关键文件/后缀 | `EVENT_WATCH_CRITICAL_RELS/_SUFFIXES` | 触发建议面=敏感面，宁窄勿宽 |
| 触发逻辑本体 | EW 段函数群（L4286 起） | 先读 24 行触发链注释·改后跑 validation |
| 每日审计读数 | `fade_instance_audit.py` | 审计口径变更=CFO/CHO 消费面变化，先对消费面 |
| 生命周期法条 | spec L449 批认注（CTO 11-04 具法条效力） | 幂等八段续跑/EXECUTING 唯一改写段/RETRY 无出边 |

---

## 五、接手自测四问

1. EW 和 `--watch` 循环是什么关系？（`--event-watch`=单次扫描，定时巡检链的交接点；`--watch`=前台循环带 `--interval`。两者都禁与业务 scope 组合。）
2. 为什么首扫只建基线？（防 daemon 每次启动都触发一轮无意义检查——幂等设计，state.json 是相册。）
3. 关键文件清单里为什么是两份 manifest+.agent.md？（manifest=发布映射真源，.agent.md=员工 live entry 源——这些变了必须建议同步，属「变更即建议 sync」的硬清单。）
4. 删一张历史 run 树要什么流程？（不是 rm——先读 POINTER+事故卷：DB/盘双记账，禁单侧删除，处置归 CTO 裁。）

---

## 六、真源指针（教程不替代真源）

- 代码正身：`TriCompany/runtime/cognition/source_publish_check.py`（EW 段 L4286 起）
- 协议：`TriCompany/docs/engineering/fade-protocol-spec.md` §8.6/§2.4
- 设计纵深与工程史：[04-deep-research.md](04-deep-research.md)
