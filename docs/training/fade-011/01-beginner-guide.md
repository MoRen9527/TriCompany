<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-011/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-011 小白版——公司里那位「文件一动就上班」的自动员工

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-011/01-beginner-guide.md
- syncMode: source-only
- lastSyncedAt: 2026-11-10

读者：完全零基础的新人。不需要懂 FADE 协议，不需要读过源码。
目标：20 分钟后，你能说出 FADE-011 每天自动做什么、它的「传感器」装在哪、去哪里看它干活的证据。

---

## 一、一句话说清这是什么

> 公司有一群「关键文件」（员工的岗位定义、技术规范、发布清单）。
> **FADE-011 雇了一位不用睡觉的守夜人：它盯着这些关键文件，谁动了一下，
> 它就自动开一张「检查工单」，把「谁动了什么、检查过没有、结果如何」记录在案。**

这位守夜人的「眼睛」叫 **event-watch（EW，事件守望）**——这个机制规定在协议书里
（`TriCompany/docs/engineering/fade-protocol-spec.md` §8.6），一句话原则：

> **检测即触发，触发与执行解耦。**

翻译成大白话：发现动静（检测）和干活检查（执行）是两步——先发现、记下来，再决定查多深。
就像门铃响（有人来了）和开门检查（看清楚是谁）分开做，门铃只管响。

---

## 二、它每天自动做什么（现役形态：每日自动轮）

FADE-011 现在是**全自动**的（CEO 2026-11-05 亲裁：保自动）。每天：

1. **守夜人巡逻**：每隔一小段时间（默认 30 秒）看一眼三个关键目录有没有新动静——
   - `source-agents/`（13 位员工的岗位定义文件）
   - `docs/engineering/`（技术规范真源）
   - `.github/manifests/`（发布清单）
2. **指纹对比**：它记着一本「上次的相册」（state.json 指纹状态文件）。这次看到的和相册一样
   → 什么都没发生（这不叫白跑，叫**幂等**，04 深度篇细讲）；不一样 → 有动静，开工。
3. **自动开工单**：在公司的档案室开一个新 run 树（`operating-records/<周>/trees/fade011-ew-runs/`
   下一个新文件夹），FADE 五节点链自动跑一遍：资格审查（qualify）→定计划（plan）→干活（DCE）→
   打分（score）→收尾归档（close）。
4. **留档**：每个节点留一份报告（node-qualify.md、node-plan.md……node-close.md），
   最后留一份总结（close-output.json）。谁都可以翻。

截至 2026-11-10，档案室里已经有 **64 张这样的工单**。

**一个重要纪律**：这套系统「保自动」，但**人不能随手手动去跑它**——手动运行是 CEO
专属通道（CEO 2026-11-05 裁令，在案 `TriMetaverse/docs/memory/fade011-manual-run-ceo-channel-only.md`）。
席位员工想触发它？不行，报告 CEO。就像锅炉的自动巡检机器人，值班员不能为了「试试」随手按手动按钮。

---

## 三、亲眼看一遍它的劳动成果（三分钟）

证据都在档案室（本机仓库就能看）：

```powershell
# 1. 看看 64 张工单长什么样（每张一个文件夹）
Get-ChildItem D:\Code\ai\TriMetaverse\docs\workflow\operating-records\2026-W45\trees\fade011-ew-runs\ | Select-Object -First 8

# 2. 打开最近一张工单，看五节点报告齐不齐
Get-ChildItem D:\Code\ai\TriMetaverse\docs\workflow\operating-records\2026-W45\trees\fade011-ew-runs\fade-w-fade011-ew-0090af2c1df3\ -Recurse -File | Select-Object FullName

# 3. 读一张工单的「计划书」开头
Get-Content D:\Code\ai\TriMetaverse\docs\workflow\operating-records\2026-W45\trees\fade011-ew-runs\fade-w-fade011-ew-0090af2c1df3\plan.md | Select-Object -First 8
```

你会看到：每张工单里有 `plan.md`（计划书）+ `reports/`（五节点报告）+ `artifacts/`（干活产物）。
计划书开头写着「程序化计划产物（FADE-011 S5.1 driver·plan skill 正身接线）」——
意思是这份计划不是人写的，是程序自动生成的。

---

## 四、它和 FADE-001/002 是什么关系？（家族合影）

| 实例 | 触发方式 | 一句话 |
|---|---|---|
| FADE-001 | 定时（每周日 23:00 cron 拍） | 每周自动翻工作台——闹钟叫醒型 |
| FADE-002 | 发布管线（源侧→发布面） | 源文件改了同步发布面——流水线型 |
| FADE-011 | **事件（文件一动就触发）** | 守夜人巡逻型——本案 |

三者共用同一本「员工手册」（FADE 协议 `fade-protocol-spec.md`）和同一套五节点作业流程。
EW 机制最早是为 FADE-002 补齐的触发探测能力，后来长成 FADE-011 这个独立实例——
**「检测」这门手艺是 002 带大的，「全自动开工」这门手艺是 011 练成的**。
每日审计（fade_instance_audit.py）里明确写着：其他实例向 fade011 看齐。

---

## 五、新人自测三问（能答出来就毕业）

1. FADE-011 的触发方式跟 FADE-001 有什么不同？
   （答：001=定时闹钟型每周日拍一次；011=事件型，文件一动/指纹一变就触发。）
2. 为什么它翻相册（state.json）发现没变化就不开工？
   （答：指纹未变=幂等去重，不重复触发；而且第一次巡逻只拍照建相册、不开工单，防止机器一开机就乱开单。）
3. 想手动跑一次 fade011 看看效果，应该找谁？
   （答：不找谁——手动运行是 CEO/人工通道，席位勿代办；正常让它自动跑就行。）

---

## 六、真源指针（教程不替代真源）

- 协议 §8.6：`TriCompany/docs/engineering/fade-protocol-spec.md`（检测即触发原则正身）
- run 树卷面：`TriMetaverse/docs/workflow/operating-records/2026-W45/trees/fade011-ew-runs/`
- CEO 保自动裁令：`TriMetaverse/docs/memory/fade011-manual-run-ceo-channel-only.md`
- 深入一步：读本目录 [02 产品版](02-product-guide.md) → [03 代码地图](03-code-map.md) → [04 深度研究](04-deep-research.md)
