<!-- GOVERNANCE: 本目录教程真源在 TriCompany/docs/training/fade-011/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-011 event-watch 自动触发实例——四版教程（由浅入深）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-011/README.md
- syncMode: source-only
- lastSyncedAt: 2026-11-10（写前 date 现查 2026-11-10T21:1x+08）
- 形制：对齐 [fade-001/](../fade-001/README.md) / [fade-002/](../fade-002/README.md) 目录四版制

## 这套教程讲什么

FADE-011（event-watch 自动触发实例）是 TriCompany 十一个 FADE 实例里最「自动化」的一个：
**它不需要人喊开工——文件一动它就动**。

一句话：公司在 `source-agents/`、`docs/engineering/`、`.github/manifests/` 这些关键目录装了
「动静传感器」（event-watch 触发探测，spec §8.6）。文件一变、git 一提交，指纹就变；
指纹一变，FADE-011 自动开一个 run，在 operating-records 树上跑完五节点链
（qualify→plan→DCE→score→close），把「这次谁动了什么、检查结果如何」自动记录成档。
现役形态=**每日自动轮**（TriMLC 8713 daily-sweep 通道·CEO 2026-11-05 裁保自动；
手动运行=CEO/人工通道，席位勿代办——`TriMetaverse/docs/memory/fade011-manual-run-ceo-channel-only.md`）。

三个数字建立第一印象（2026-11-10 实勘）：

- **64 个 run 树**已落 `operating-records/2026-W45/trees/fade011-ew-runs/`（fade-w-fade011-ew-<hash12> 命名）
- **5 个节点报告**每 run 必留（node-qualify/plan/dce/score/close + close-output.json + dce-output.md）
- **30 秒**默认轮询间隔、**5 文件**变更阈值、首扫只建基线不触发（幂等三件套，见 04 深度篇）

四版由浅入深，按起点选入口：

| 版 | 文件 | 读者与目标 | 预计耗时 |
|---|---|---|---|
| ① 小白版 | [01-beginner-guide.md](01-beginner-guide.md) | 零基础：说清 EW 是什么、每天自动做什么、去哪看证据 | 20 分钟 |
| ② 产品版 | [02-product-guide.md](02-product-guide.md) | 产品/管理视角：能力边界、现役形态、运维面与裁决口径 | 15 分钟 |
| ③ 代码地图 | [03-code-map.md](03-code-map.md) | 要接手代码：文件地图+触发链七步+每步代码锚+亲手查证 | 30 分钟 |
| ④ 深度研究 | [04-deep-research.md](04-deep-research.md) | 深读实现：幂等/去重/安全门设计+工程史+风险与改造面 | 45 分钟 |

另有第五件 [improvement-draft](fade-011-improvement-draft.md)：FADE 规范十阶段骨架
（临时依据+记录形制·对位 fade-001 的 05 稿）——候 CEO×BOD 拆解推进至 fade-011 时逐段丰富，
**当前只有骨架占位不预写**。

## 与姊妹实例的关系

- **FADE-001**（[../fade-001/](../fade-001/)）= 平面维护实例：定时触发（每周日 cron 拍），
  人不碰它也会准时动。
- **FADE-002**（[../fade-002/](../fade-002/)）= 发布域管线：源侧→发布面同步，EW 机制正是
  FADE-002 补齐项落地后长出的触发面（source_publish_check.py 的 `--event-watch` 系）。
- **FADE-011** = 触发面实例本体：把「检测即触发」做成全自动 run 工厂，其他实例向它看齐
  （fade_instance_audit.py 每日审计读数：「其他实例向 fade011 看齐+fade011 自身完善」）。

## 真源指针（教程不替代真源）

- 协议正身：`TriCompany/docs/engineering/fade-protocol-spec.md`（§8.6 触发探测/§2.4 安全门/§8.1 durable profile）
- EW 实现正身：`TriCompany/runtime/cognition/source_publish_check.py`（L3546 参数系/L3956 独立触发面/L4286 触发链注释与常量）
- 每日审计：`TriCompany/runtime/cognition/fade_instance_audit.py`
- Phase 2 排期单：`TriMetaverse/docs/execution/fade-011-automation-phase2-plan-20261103.md`（S1-S5 工序/验收门/回滚姿态）
- run 树现役卷面：`TriMetaverse/docs/workflow/operating-records/2026-W45/trees/fade011-ew-runs/`
- 排障插曲指针：同目录 `README-POINTER.md`（{week} 字面目录·CTO 裁候裁保留）
- 事故卷：`operating-records/2026-W45/trees/fade011-ew-runs/事故卷-值席违规单侧删除两run树-20261023.md`
- CEO 裁令：`TriMetaverse/docs/memory/fade011-manual-run-ceo-channel-only.md`（保自动+手动=CEO 通道）

遇到冲突回真源，不回教程。
