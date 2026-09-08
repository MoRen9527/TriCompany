<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-006/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-006 产品版——六步配方、护栏与故障速查

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-006/02-product-guide.md
- syncMode: source-only
- lastSyncedAt: 2026-09-07

读者：要**发起/编排/协作**自动拾取任务的人——计划发起方（CEO/BOD/席位）、拆树封卷的编排
（COS）、执行会话、值班排障者。前置：已读 [小白版](01-beginner-guide.md)。

---

## 一、模块导读四要素

| 要素 | 内容 |
| --- | --- |
| **定位** | FADE-006"执行面自动拾取"：把符合配方形状的任务包（计划文档+树注册）变成落盘即入队、双通道拾取、自治执行、防篡改、自愈收口的流水线——公司 runtime-owned durable + 多节点树的标杆实例 |
| **成熟度** | **完整实例标准档**：首评 80/100（2026-08-27 回溯建卷，诚实低计）→ 增评 **91/100**（2026-08-28，卷封 5/8→8/8+节点报告 3/8→7/8，LG-004 双轨）；**段-实现映射表首行填制**（细则 2 标本）；配套工具族全接线（seal-materials/run-root/_fadehash/node-report-check）；立法成果反哺协议 §2.7/§2.8 |
| **真源路径** | 规格正身 `TriMetaverse/docs/execution/fade-006-execution-autopick-spec.md`；上位管线 `docs/execution/2026-08-26/fade-pipeline-design.md` v1.1；反向工程 `fade-instances-retrospective.md`；登记册 FADE-006 条；工具族 `TriMetaverse/scripts/fade/` |
| **常见误区** | ①树改了 active 就以为立刻被执行（要先推远端，hook 认 push）；②把 cron :18/:48 当主通道（hook 秒级是主，cron 是兜底）；③执行会话自行重试到好（规则=先分层取证定层，不盲试）；④把预算双门当摆设（15 亿 token/日+月度金额，超了就停）；⑤节点状态手工翻转（置 done 前必须过 node-report-check 校验器，编排层还会复跑——双门） |

## 二、六步配方（新战役照此复制）

| 步 | 角色 | 动作 | 硬性工件 |
| --- | --- | --- | --- |
| **F1 铸计划** | TriMLC+CEO | 计划文档落 docs/execution/，带元信息头与验收标准 | plan.md（版本化） |
| **F2 拆树封卷** | 小贾（编排） | 树注册周平面；`seal-materials.py --attach` 预封原材料；face/domainRouting 显式标注；试卷声明（v2.0.3 起 Plan 时点冻结） | tree-op.json+卷封字段 |
| **A 挂平面** | 小贾 | push sg-bare（枢纽）+GitHub（镜像）；**归账只 merge 不 cross-rebase** | hook 日志秒级行 |
| **D 自动拾取** | sg 编排层 | hook 秒级/cron :18,:48 兜底 → 三重门+面路由 → O_EXCL 锁+PID 判活+1800s 冷却 → spawn（cwd=树 repo 直落+裸命令铁律+BRIEF） | registry ticks（rc·pid·trigger 全留痕） |
| **E 自治执行** | CC 会话 | 节点 fresh 派工×一次一节点；**验卷→先写后报→原子提交→对卷收口**；blocked 必走分层取证 | 每节点 status 翻转 commit |
| **Z 收口回执** | 会话+小贾 | 树 done 快照 root 入战役档案；结果对账回填计划文档 §对账节；生产部署移交清单单列 | campaign Merkle root |

**拾取条件（D 步三重门）**：`status=active` + `server-executable` + `pending` 无时间门 + face 路由正确——四者即"会被本地（fade-watch）/服务器（hook+cron）自动拾取"的完整状态标识。

## 三、护栏五条（管线自带，配方直接继承）

| 护栏 | 白话 |
| --- | --- |
| **原子锁 O_EXCL + PID 存活判死** | 同一时刻只有一个会话碰同一棵树；进程死了锁自动释放，不留僵尸占位 |
| **1800s 冷却无旁路** | 同一批变更 30 分钟内只处理一次；想重入只有一条路——工作项真的变了 |
| **预算双门** | 15 亿 token/日台账 + 月度金额兜底——跑飞会被掐，账在台账 |
| **面路由** | m-face 缺省归 TriMMC；r-face 严格制显式标注——活不送错线 |
| **卷封制** | 材料漂移未裁决=不得通过（硬坎）；campaign Merkle root 收口存档，防事后篡改 |

## 四、故障处置速查（三天实战争得的六面墙）

| 症状 | 先做什么（定层） | 解法锚 |
| --- | --- | --- |
| 工具命令被拒 | 取**原始拒绝文本**：是审批前缀匹配层拒的？ | D-11 裸命令/cwd 直落（orchestrate_tick c0ad6b8） |
| 执行通道缺失（npm/tsc 全拒） | 被拒串对照 spawn 白名单 | --allowedTools 全家桶（61dfaea） |
| push Permission denied | 裸仓 objects 属主分布 | D-10 chgrp+sharedRepository+heal cron |
| push 后 tick 无反应 | **fade-hook.log 有无 dev-updated 行** | D-08 unset GIT_DIR；锁文件 666 共享 |
| tick 看不到新树 | 查 `_sync_worktree degraded` 字样 | P1-1 自愈已内建；降级即查脏树 |
| 多线归账互拒 fast-forward | range-diff 看是否同补丁异 SHA | merge-only 归账（禁跨 hub rebase） |

值班口诀：**先取证定层，再对表解法锚**——每面墙都有已被实战验证过的标准解，不要发明新解。

## 五、使用旅程

### 旅程 A：发起一场新战役（计划方视角）

1. 计划定稿（F1）：计划文档落 docs/execution/（本仓），验收标准写死在文档里。
2. 找编排（F2/A）：小贾拆树封卷挂平面——你要提供的是**稳定的目标与边界**，树怎么拆是编排的专业。
3. 之后就是观察：hook 日志秒级行 → registry ticks → 节点 commit——**进度全部可查询，不需要催**。
4. 收口后你会收到对账回填（Z）：计划文档 §对账节写明每项验收标准的实际结果。

### 旅程 B：执行会话视角（被 spawn 的一方）

开工三件事：**验卷**（材料 hash 对照封存，不符即停）→ 读 BRIEF（裸命令铁律：cwd 直落，
禁组合拳）→ 一次一节点。每节点收口：先写后报（工件落盘留 path+行数/hash）→ 门禁命令实跑
留退出码 → 置 done 前过 node-report-check → **blocked 不硬扛**：分层取证八股（原始拒绝文本
定层）+ 修复后自愈复工不复用旧进度。

### 旅程 C：值班排障视角

症状 → 查第四节六面墙表 → 定层 → 对锚解法。升级路径：定位不了的取证上报 COS/CTO，不静默。

## 六、价值主张

- **零催办**：批准即入队，进度全程可查（hook 行/ticks/节点 commit 三层留痕）。
- **防篡改**：卷封+Merkle root——三个月后仍可机械证明"照哪份材料、干成什么样"。
- **可复制**：六步配方+六面墙，新战役照配方走，无需重新发明流程。
- **喂协议**：本实例反向立法出 §2.7（节点收口报告）与 §2.8（映射表首行填制）——跑得好的实例长成协议。

## 七、诚实边界

- **已接线**：六步全链、五护栏、六面墙解法锚、工具族四件（seal/node-report-check/run-root/_fadehash）、Close CLI 载体 matcher（p0fix4 MATCH 实证；例行化宽口径核验中，解除条件=LG-005 首个真实战役实证）。
- **如实低计史**：首评 80 卷封 5/8+节点报告 3/8（立法晚于运行），增评已修——读卷先读 boundary。
- **增强项**：blocked 边沿告警（v1.2 待办）；自动化测试/部署场景仍是"推荐 FADE 模式"未收编。
- **演进注意**：编排机制在持续勘定演进（通道勘定/harvest-rc 立法等），现行以登记册与代码为准——旧教程（fade-006-deep-dive.md 427 行版）锚定 P0 战役时点，演进差异以本目录 ③④ 为准。

## 八、验证方式（学完自测）

1. 打开 W37 `trees/duty-night-patrol/tree-op.json`：说出它未被拾取的原因与放行条件。
2. 向同事复述六步配方不卡壳，并指出三重门在 D 步的位置。
3. 抽查一张六面墙表：给症状"push 后 tick 无反应"，说出第一查什么（fade-hook.log dev-updated 行）。
4. 对照 W35 九棵收口树任一棵的 tree-op.json 与节点状态，复述"验卷→先写后报→对卷收口"在哪个工件上留了痕。

## 使用依据

- 六步配方/护栏/故障表/证据链：`fade-006-execution-autopick-spec.md` 全文（2026-09-07 实读）
- 三重门/映射表/评分弧线：`fade-registry.md` FADE-006 条+`fade-papers/FADE-006-*` 五卷（2026-09-07 实勘清单）
- 活体样本：W37 trees 两棵（pending 态亲读）+W35 trees 九树（收口态清单）
- 首役叙事：P0 审计修复战役（八实例九项 P0 全修复，2026-08-26/27）
