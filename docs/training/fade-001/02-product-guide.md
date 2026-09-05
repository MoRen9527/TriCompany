<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-001/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-001 产品版——双域工作流与使用旅程

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-001/02-product-guide.md
- syncMode: source-only
- lastSyncedAt: 2026-09-05

读者：要**与 FADE-001 共处**的人——写工作日志的员工、运维值班、要做周计划的协作者，
以及评审"这套维护体系值不值得依赖"的人。不需要读代码。
前置：已读 [小白版](01-beginner-guide.md)（或已懂 周平面/单写者/兜底巡检 三概念）。
事实基线：2026-09-05 现势（时点=周日 23:00 河源 TriRMC；兜底=sg watcher 槽位 5,15,…,55）。

---

## 一、模块导读四要素

| 要素 | 内容 |
| --- | --- |
| **定位** | FADE-001"周工作平面维护"实例（登记册在册），双域结构——迁移域①（周日自动翻页）+维护域②（每日进度双通道维护），公司级"最低恢复防线" |
| **成熟度** | ①迁移域：**完整档，首评 PASS 90/100**（2026-08-20），冻结不重评；遗留=服务器侧证据回流复评（齿条①，**09-17 四周警告线**）。②维护域：**扩评中**——十段齐、Score CLI（patrol `--score`）shadow 观测期（部署日 65/80 属 regime 边界非不及格）、Score Skill 纸面如实；整体档位=两域双门槛各自 PASS 的合取，不以①完整宣称整体完整 |
| **真源路径** | 登记册 `TriCompany/docs/engineering/fade-registry.md` FADE-001 条；patrol `TriCompany/runtime/cognition/daily_progress_patrol.py`（951 行）；迁移链 `runtime/cognition/weekly_plane_shift`；runbook `TriMMC/docs/ops/trimc-cron-plane-shift-runbook.md`；进度文件 `TriMetaverse/docs/workflow/operating-records/<周>/daily-progress.md` |
| **常见误区** | ①信文档里的旧 cron 表达式（时点以 runbook 修正注记+服务器 API 现值为准：周日 23:00 heyuan 9c81c7ec）；②把 skip 当故障（门限闭合=正常）；③把 65/80 当不及格（CLI 小计上限 80+regime 边界裁定）；④迁移窗口内写 operating-records（冻结窗口纪律）；⑤用截断 UUID 查 cron job（须 36 位全量） |

## 二、功能面全景（双域）

### 2.1 迁移域①：周日 23:00 翻页（runtime-owned durable）

| 项 | 现势 |
| --- | --- |
| 触发 | 河源 TriRMC cron job **9c81c7ec**，`0 23 * * 0` Asia/Shanghai（每周日 23:00 北京时间；2026-08-30 自 23:59 提前，留补救窗） |
| 执行 | 五步确定性链 `weekly_plane_shift --sync`（python3.8，服务 User=fleet 单身份，job 不带 runAs）：create（建新周骨架，幂等）→ migrate（上周平移）→ carry_over（未结项搬迁+8 周升级上报）→ validate（链内校验）→ agent_close（收口落卷） |
| 审计 | `.shift-ade.json` 五步清单（每步 status/result/changes/errors/check_time）+ git commit + per-run 日志 |
| 兜底 | `cron run <36 位全量 UUID>` 幂等补跑；失败不回滚代码——脚本幂等，修正后直接重跑 |
| 健康断言 | **齿条③**：每周一晨检 GET 核验 job `lastRunStatus=ok`（TriCompany 34753ae；W35→W36 首跑 ok/9342ms=基准样本；非 ok 即迁移失败暴露口） |

### 2.2 维护域②：每日进度双通道（runtime-owned durable）

| 通道 | 谁 | 干什么 |
| --- | --- | --- |
| 事件驱动主 | 董事长助理 | 销账/交付/裁决后**随手** append 当日节+push 三端——语义质量最高（哪件事值得记、怎么概括） |
| 定时巡检兜底 | sg daily-progress-watcher（patrol 脚本） | 槽位 5,15,25,35,45,55 分（每 10 分钟，同秒竞态消除）；门限开（日志落后）才补写 commit 清单块；**只追加不重写** |

巡检的安全设计（产品面看得见的四条）：

1. **拓扑门限**：判断"落后"用 git 拓扑（`git log <上次触碰>..HEAD`），不用时钟比较——同秒提交、变基重写都不会误判。
2. **recovery push 自愈**：上轮推送失败遗留的未推提交，下轮开头先重推——防"自己写过→门限闭合→永不重推"死锁。
3. **写入回滚保护**：写入前存底，回读校验失败即回滚到写前状态。
4. **推送分级**：sg-bare 必达（失败如实报 fail 等下轮自愈）；GitHub 尽力而为（无凭据快速失败，由事件驱动写收敛）。

### 2.3 评分体系（维护域，shadow 期）

`--score` 对真实日评分：T1-T8 八项，CLI 确定性六项（小计 80）+ Score Skill 语义两项（T3 事件及时性/T7 治理对齐，20 分）=100；双门槛=必选全过∧总分≥90。**shadow 阶段只观测不拦截**；达标日才接线为 push 终态硬门。scoreable 判据=当日事件驱动写与巡检补写**各≥1**。

## 三、使用旅程

### 旅程 A：作为普通员工，一周里你需要做什么

- **平时**：什么都不用做。日志由助理和巡检双通道维护；你的 commit 只要正常提交，巡检会看见。
- **周日 23:00 前**：把 `docs/workflow/operating-records/` 的改动 commit 并推送（编排层职责；顺手全仓推送是软习惯）。23:00 至周一回流完成，**不要写 operating-records**（冻结窗口）。
- **周一早上**：看两样东西——新周目录已建好（迁移 commit 落地）、晨检读数 job 9c81c7ec `lastRunStatus=ok`。任何一样异常，按[深度研究版](04-deep-research.md)的暴露口路径上报。

### 旅程 B：作为助理（事件驱动主）

销账/交付/裁决后，随手向 `daily-progress.md` 当日节 append 主叙事行 + registry 变化行，
与状态条同批 push 三端。约束：只更新自己的主叙事与全节组织权，不碰巡检块；同日已有节
则续写不新建。这就是"权威叙事在人、粗粒度镜像在仓"的分工——机器本地不入仓的
台账/记事本才是权威细节，daily-progress 是恢复锚。

### 旅程 C：作为运维值班（异常时看什么）

1. **巡检日志**：`/var/lib/trimc/cron/logs/<jobId>__<ISO>.log`（sg 侧）——每轮 stdout JSON 小票（written/skip/fail + 补写首行预览 + push 三态）。
2. **迁移审计**：周日跑完后看 `.shift-ade.json` 五步全 pass + 周一晨检断言。
3. **失败分级**：巡检 `fail`（sg-bare 推送失败）→ 看是否下轮自愈（recovery push）；GitHub 落后 → 设计内容差（≤24h 收敛口径）；job 连续 error → 报 CTO 域，勿手动改 job state（**禁抹 nextRunAtMs**，缺它永不调度——D-02）。
4. **手动补跑**：只用幂等兜底 `cron run <全量 UUID>`，**禁止服务器手动 `--sync` 点火**。

### 旅程 D：灾后重建演练（这套系统的存在意义）

最坏场景：本地+sg+中枢全灭。恢复路径=从 GitHub 取最近的 `daily-progress.md`，按当日节的
commit 清单与挂账行重建工作现场——丢失窗口≤10 分钟（巡检节奏上限）。这是登记册写死的
验收场景，不是宣传语；每周的巡检补写都在为这个场景演练。

## 四、价值主张

- **不靠记性**：翻页、补日志都是确定性程序——"人忘"不再是单点。
- **不靠单一机器**：三端持久+推送分级，任何一端可达日志就不灭。
- **丢得起、找得回**：最坏丢失窗口 23h→10min；重建材料（commit 清单+挂账+锚点）就是日志本身。
- **诚实可评**：维护域每一轮有小票、每一天可评分（shadow 卷面公开）、每项短板有立法修复路径——依赖它之前可以查它的成绩单。

## 五、诚实边界（用前必读）

- **已实现**：双域十段、patrol 五约束、Score CLI shadow、迁移幂等链、齿条③晨检断言、拓扑门限+回归用例。
- **人工态/纸面**：维护域 Score Skill 待实现（T3/T7 留语义评分）；"push 即终态"现行时序违反协议 §2.5——已立法修复路径（升完整后 DCE(push)→Verify→Score→Close Skill→Close CLI），当前如实降档。
- **挂账**：迁移域服务器证据回流复评（齿条①，09-17 警告线）；巡检独立达 GitHub（增强项，董事会裁定不入册维持现状）。
- **历史口径注意**：登记册/旧文档里的 `59 23`、TriMC(sg) 承载等表述为历史叙事冻结——现行以 runbook 时点修正注记（周日 23:00 heyuan TriRMC 9c81c7ec）与服务器 API 现值为准。

## 六、验证方式（学完自测）

1. 跑 `--self-test`：30 用例全 ok、退出码 0。
2. 打开本周 `daily-progress.md`：指出助理主叙事与巡检兜底两种笔迹，并解释它们为何互不覆盖。
3. 口测：向同事复述"周日 23:00 会发生什么 + 冻结窗口为什么存在 + 机器全灭后怎么重建"三件事不卡壳。
4. 进阶：跑 `--score --date <昨日>` 读 shadow 卷面，能说出 scoreable 判据与"65/80≠不及格"的原因。

## 使用依据

- 双域十段与档位/评分/齿条：`fade-registry.md` FADE-001 条（扩维块、paper-① 90/100、扩维卷 65/80、齿条①③）
- 时点/槽位现势：runbook 头部时点修正注记（b8ed553 同批，2026-08-31）+ W36 daily-progress.md 08-31 节（槽位移 5,15,…,55）
- 齿条③：TriCompany 34753ae（周一晨检 lastRunStatus 断言，W35→W36 基准 ok/9342ms）
- patrol 行为（门限/recovery/单写者/推送分级）：`daily_progress_patrol.py` 头注与 L64-68/L177/L352/L377（2026-09-05 现行版实读）+ `--self-test` 30/30 实测
- 冻结窗口与反面案例：runbook §7（W34→W35 落旧基 ae3d32fe 实录）
