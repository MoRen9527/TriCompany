# TriCompany 工程纪律集（三端通用）

> sourceOfTruth: TriCompany/docs/workflow/engineering-disciplines.md
> syncMode: source-only
> lastSyncedAt: 2026-08-17
> 性质：跨域工程纪律（编排层/TriLC/TriMC 员工通用）——从编排层会话记忆升级为公司资产。员工知识工作区同步路径：合同/培训文档引用本文件。

## 为什么有这个文件

纪律最初在编排层（本地研发仓 claude code）会话记忆中沉淀，但 TriLC/TriMC 侧员工不可见——**跨域通用纪律必须落在 TriCompany 真源**，三端员工经各自知识通道读取。

## 纪律条目

### D-01 subagent 落盘纪律（2026-08-17，三次事故提炼）

长任务 agent context 耗尽时，**口头"已落盘"不可信**（总结文本先于写盘生成，断点常落在两者之间）。

- agent 侧：**先写文件、后写总结**——总结必须带文件路径 + 行数/大小证据
- 收稿侧：**三查**（文件存在 / 内容规模 / 与报告口径一致）后才采信
- 长任务（50+ 项/多文件）分段落盘（每 ~20 条），断点可续
- 兜底：发现未落盘直接接续生成（机械转化类最快），不返工原 agent

### D-02 cron job state 卫生（2026-08-17，weekly 三夜未触发根因）

手动改 cron job state 时**禁抹 `nextRunAtMs`**——引擎靠它排期，缺失=永不调度。只 patch 目标字段；改 cron 表达式后重算 nextRunAtMs；诊断口诀：cron 型 job 不触发先查该字段。

### D-03 daemon 重启纪律（2026-08-16）

重启 TriLC daemon 走 `trilc stop` → `.cmd` 拉起两步（pidfile 权威路径），禁裸杀进程（pidfile 与监听进程错位→新旧进程身份混乱→"补丁没生效"假象）。

### D-04 时刻引用纪律（2026-08-17，编排层报时错 8 小时根因）

上下文混存本地时刻与 UTC ISO 时间戳（teammate 消息/日志 `Z` 后缀）——**报时刻前必现查系统时钟**，禁止从上下文时间戳外推；引用 ISO 时间戳必须认 `Z` 并按本地时区换算（中国 +8）。

### D-05 git index 共享卫生（2026-08-14，三次 index 污染提炼）

多 agent 共享仓：统一 `git add <明确路径>` + `git commit`，禁 `git commit -- <path>`；commit 前三查（status/cached diff/log）。

## 维护规则

- 新纪律事故复盘后追加（格式：D-XX + 日期 + 根因一句 + 行为规则）
- 源侧为本文件；三端员工运行时经知识通道引用——不各自复制（防多真源）
