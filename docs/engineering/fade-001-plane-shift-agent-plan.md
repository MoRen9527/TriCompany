# FADE-001 维护项①·周平面迁移——agent 承接计划（agent plan）

- sourceOfTruth: 本文件（工程域正身）
- syncMode: write-time
- lastSyncedAt: 卷面时点锚=git commit 时戳（零手打·D-47 增补款正形）
- 铸：m-duty-cos（registry owner 补课承办），2026-09-21；令源=CEO 定性「ADE-only 死工作」补课（BOD 转知）
- **升版（2026-11-08，CTO 圆桌令①「不能就马上优化」即刻施工项 O1）**：①段名双语对齐 plan_gate 四必答（REQUIRED_SECTIONS·协议层通用段名）②时点/机位勘正随 10-18 CEO 令改（23:00/TriMMC/sg → 23:50/TriRMC/河源·cron `50 23 * * 0` Asia/Shanghai·job 9c81c7ec weekly-plane-shift）③FADE 十段序承载节新增（N-D1/N-D3 STAGE_ORDER 对表）——升版依据=SDE 事实单（11-05 部署实例活体读数）+冻结考卷 1.1-frozen（bf8ba0e0 双 hash 对表验毕）+四骨架中性冒烟 28/28（3e0994b）
- 正身关联：runbook=`TriMC/docs/ops/trimc-cron-plane-shift-runbook.md`；登记册=`TriCompany/docs/engineering/fade-registry.md` FADE-001 条；考卷=`fade-papers/FADE-001-paper-plane-shift.json`（1.1-frozen）
- 目的：迁移线自「五段链脚本内置、无需逐次语义规划」补课为**可由 agent 席承接执行核验**的形态

## 触发与到岗（trigger-criteria）

- 触发：每周日 **23:50** Asia/Shanghai（cron `50 23 * * 0`，执行体=**R-HY TriRMC cron job `9c81c7ec` weekly-plane-shift**·10-18 CEO 令改形态·SDE 事实单 §一活体读数在卷）
- agent 承接窗：触发后 30 分钟内到岗核验（=**23:50-00:20+08 窗**；候链跑完，per-run 日志量级参照 SDE 事实单 11-01 拍 exit 0 实证）

## 前置断言（departure-window-precheck·D-24 机位断言先行）

1. hostname=**河源 R-HY**（R 面机·非 sg）；工作树=`/srv/fleet/TriMetaverse`（TMV）+协议层检出=`/srv/fleet/TriCompany`（**须含 N-D3 3e0994b 四骨架**——T-0 增项·`git log --oneline -1` 断言）
2. 工作树已 ff 至 bare 顶（payload 前置 ff 先例，2026-08-31 runbook 时点修正注记在卷）
3. 无进行中 git 操作（rebase/merge 空）
4. （T-0 值席勾）R-HY 8710 healthz ok+cron enabled+neg 401 门在岗（18710 隧道探针形：healthz ok/cron.enabled=true/degraded=false 11-08 08:0xZ 实证在卷）

## 迁移段序（segment-order·固定）

- **迁移器五步（老 SOP=FADE push 段实现体·cron 自动）**：OP index → unresolved → trees → carry-over → 通知
- **FADE 十段序（N-D1/N-D3 STAGE_ORDER 对表）**：`push → verify → score → close-skill → close-cli`——push=迁移器五步承载（cron 拍）；**verify→score→close-skill→close-cli 四段=agent 承接面**（本 plan 主体·骨架=runtime/fade_protocol/ 四件·3e0994b）；违序=段位降档（close_framework.sequence_violation 判序原语·首实弹验点）

## agent 执行步骤（dynamic-situation）

1. 读 per-run 日志 `/var/lib/trirmc/cron/logs/<jobId>__<ISO>.log`（**河源 TriRMC 路径**·trirmc 非 trimc）与新周审计件 `docs/workflow/operating-records/<新周>/.shift-ade.json`——`status=pass` 且 `from_week/to_week` 正确即 push 段成
2. **verify 段**：verify_runner 断言集（N-D3 件①）——新周索引三件（OP json/unresolved-items/daily-progress）存在且非空；旧周 carry-over 迁移到位；git 顶新增迁移 commit（身份=TriRMC Scheduler fleet 形）
3. **score 段**：冻结考卷 T1-T9 对照评分（score_engine·N-D3 件②主态；引擎缺席灰度=fallback patrol 旧形如实注·N-D5 §四两态内置）；**在办树点名随迁（T7）+台账随迁核验（T8）两必答落读数**（见归一补强两节）
4. **close-skill 段**：节点读数（时点/段序/审计件状态/评分三态）记入 daily-progress 当日节
5. **close-cli 段**：收口载体行（close_framework.close_carrier_row 形）+.shift-ade.json 升 run 收口四态词（N-D5 §七 charter 口径）
6. 异常路径（status≠pass/段缺失/四件缺任一）：**不触碰 daemon payload、不手调 jobs.json**——通报 m-duty-cos→BOD（附 log 绝对路径）

## 边界

- 不改 runbook 正身时点注记口径（2026-08-31 修正注记为现行值）
- jobs.json/payload 手调归 TriRMC 侧窗，agent 不越界
- 运行身份=fleet 单身份（heyuan 去 runAs 先例，2026-08-31）

## 归一补强两节（2026-09-21，m-cos registry owner 归一；双写归一 d719c55×acf8748）

- **在办树点名（迁移前必答，plan 核心新增·考卷 T7 对应）**：动手前盘点本周 `trees/` 全清单，**open 态树逐一点名**判定随迁/留置（随迁=树目录随周平移；留置=留原周+理由注记）——W38→W39 翻周事故的直接盲区即此（在办树未迁移）；plan 无此步=ADE-only 复发口。
- **台账随迁核验（迁移后必答·考卷 T8 对应）**：LG 系现役条目周指针随迁断言＋上周末态候批/候窗条目在新周平面可溯——考卷 T8 对应项。
