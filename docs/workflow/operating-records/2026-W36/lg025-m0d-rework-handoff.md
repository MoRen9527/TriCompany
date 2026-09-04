# LG-025 M0d commit② 返工·spawn 窗交接件（CTO 席组装，令文自足）

- sourceOfTruth: TriCompany/docs/workflow/operating-records/2026-W36/lg025-m0d-rework-handoff.md
- syncMode: static（交接快照）
- lastSyncedAt: 2026-09-03
- 用途：spawn 后备窗开工依据（FD 席窗预算耗尽，M-004 场景①同族改派）；令文三件由 CTO 席会话组装（返工令+续作令配方+FD 中止报要点全录）

## 一、任务规格（返工令 R1-R5，正身）

对象=TriCompany commit `ae349e8`（M0d commit②，COS 代跑复核抓三实缺陷后冻结勿扩散）。返工五修：

- **R1 值形态**：manifest sourceFiles 值改仓库前缀形态 `TriCompany/source-agents/<id>/<suffix>.agent.md`（§B 契约正身，与 liveEntries[].source 同形态；全域 78 键值面返工）。
- **R2 CSO/DE 合并投影**：colleagues/social 两键照 contract.paths 显式声明改指合并式 `colleagues-social.agent.md`（sourceFiles=contract.paths 的 manifest 投影，禁止自创文件名）。
- **R3 frontmatter 映射**：agent_frontmatter 改指实存在的 `agent-frontmatter.agent.md`。
- **R4 pre-flight 解析基座对齐仓根**：TriCompany 根（与 R1 值形态一致——内部自洽假绿根因消解）。
- **R5 存在性检查补**：sourceFiles 所指文件 resolve 不到即 error（D2/D3 类防再发）。

## 二、续作配方（FD 上窗已验证可行的路径，中止报留档）

- **R1-R3 投影规则**：逐席读 contract.yaml paths 六键原文投影+TriCompany/ 前缀+CSO/DE colleagues/social 同指 colleagues-social.agent.md（FD 已逻辑验证通过；工具 lg025_m0d_reproject.py 已删可依录重建）。
- **R4**：preflight 带 source_root 参数+前缀形态校验（FD 有全文设计）。
- **R5**：存在性 resolve。
- **fixture**：validation 文件 32 处值翻前缀形态（checkout 已还原需重翻）+`_write_agent_source` 种六件基座改法（FD 已验证可行）。
- **工作区起点**：manifest R1 前缀形态重投影版未提交在位（保留续用或重放皆可）。
- **上轮 14 fail 根因（关键提示）**：fixture 种件与 R5 存在性解析路径基座错位族——**R4/R5 与 fixture 翻必须同批同基座（TriCompany 仓根）落，勿分批试**。

## 三、永久断言三件套（第二方法固化，新窗必落）

1. 值形态前缀断言（`TriCompany/source-agents/` 前缀逐键）；
2. 契约投影对表断言（sourceFiles==contract.paths 投影逐键，含 CSO/DE 合并式）；
3. 存在性 error 断言（所指文件缺失→source_files_missing/error）。

## 四、完成判定与纪律

- unittest 全族绿（377 基线+新增）+dry-run rc=0 且真值面对表过（COS 复核法可复跑：值解析+contract 镜像对表）+三件套断言绿；
- commit② 重做独立 commit（冻结件 ae349e8 不扩散不覆盖）；
- 377 门+滚收件 66065c9 不动；manifest R1 版与重放二选一，终态以真值面对表过为准；
- 纪律：有阻即回；读数回 CTO 核验收（D-15）。
