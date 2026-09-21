# FADE-001 维护项①·周平面迁移——agent 承接计划（agent plan）

- 铸：m-duty-cos（registry owner 补课承办），2026-09-21；令源=CEO 定性「ADE-only 死工作」补课（BOD 转知）
- 正身关联：runbook=`TriMC/docs/ops/trimc-cron-plane-shift-runbook.md`；登记册=`TriCompany/docs/engineering/fade-registry.md` FADE-001 条；考卷=`fade-papers/FADE-001-paper-plane-shift.json`
- 目的：迁移线自「五段链脚本内置、无需逐次语义规划」补课为**可由 agent 席承接执行核验**的形态

## 触发与到岗

- 触发：每周日 23:00 Asia/Shanghai（cron `0 23 * * 0`，TriMMC daemon jobs.json 持久）
- agent 承接窗：触发后 30 分钟内到岗核验（候链跑完，per-run 日志 9342ms 量级）

## 前置断言（D-24 机位断言先行）

1. hostname=sg 服务域；工作树=`/srv/fleet/TriMetaverse`
2. 工作树已 ff 至 bare 顶（payload 前置 ff 先例，2026-08-31 runbook 时点修正注记在卷）
3. 无进行中 git 操作（rebase/merge 空）

## 五段链段序（固定）

OP index → unresolved → trees → carry-over → 通知

## agent 执行步骤

1. 读 per-run 日志 `/var/lib/trimc/cron/logs/<jobId>__<ISO>.log` 与新周审计件 `docs/workflow/operating-records/<新周>/.shift-ade.json`——`status=pass` 且 `from_week/to_week` 正确即链成
2. 四件核验：新周索引三件（OP json/unresolved-items/daily-progress）存在且非空；旧周 carry-over 迁移到位；git 顶新增迁移 commit（身份=TriMC Scheduler）
3. 节点读数（时点/段序/审计件状态）记入 daily-progress 当日节
4. 异常路径（status≠pass/段缺失/四件缺任一）：**不触碰 daemon payload、不手调 jobs.json**——通报 m-duty-cos→BOD（附 log 绝对路径）

## 边界

- 不改 runbook 正身时点注记口径（2026-08-31 修正注记为现行值）
- jobs.json/payload 手调归 TriMMC 侧窗，agent 不越界
- 运行身份=fleet 单身份（heyuan 去 runAs 先例，2026-08-31）

## 归一补强两节（2026-09-21，m-cos registry owner 归一；双写归一 d719c55×acf8748）

- **在办树点名（迁移前必答，plan 核心新增）**：动手前盘点本周 `trees/` 全清单，**open 态树逐一点名**判定随迁/留置（随迁=树目录随周平移；留置=留原周+理由注记）——W38→W39 翻周事故的直接盲区即此（在办树未迁移）；plan 无此步=ADE-only 复发口。
- **台账随迁核验（迁移后必答）**：LG 系现役条目周指针随迁断言＋上周末态候批/候窗条目在新周平面可溯——考卷 T8 对应项。
