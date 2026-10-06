# TriCompany 秘书处机制草案

版本：V0.1
日期：2026-04-16
状态：**正式生效**（CEO 批准 2026-09-14 00:33 批文②，BOD 15:5x 重发校验；补批三要素见批准记录节）——原「研发草案」态自此解除，可生产级援引

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/cyber-company-secretariat.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-10-06（§9.1 值席位载体修订——LG-065 N1·CEO 17:21 批令·COS 起草+CAO 会签 17:34+CAO 落正身；前账 2026-09-30=§9 值守班次节增（CEO 23:09 批令一体方案/23:55 三批②批）+§10 铸单主流程一行指针增（CEO 02:56 批）+§1 研发草案残句勘正（09-14 转正漏改残句清理）+supportPublishedCopy 行删（BOD R2 裁 B 案 03:33，旧 published-summary 副本 orphan 归档 TMV docs/workflow/archive/，commit 0f532c2a，本件自归 source-only 无 published-copy 义务））

## 批准记录（补批转正，2026-09-14）

- **审批人**：CEO 磨人
- **审批时点**：2026-09-14 00:33+0800（四件批文②；BOD 2026-09-14 15:5x 重发校验）
- **元信息头**：本文件 sourceOfTruth/syncMode/publishTier/lastSyncedAt 齐备；supportPublishedCopy 追平规则维持（support 侧 `tricompany-secretariat.md` 候同轮/下一轮追平）
- 补批依据：LG-034-INST 修订二来源白名单对表所列「补批清单第 1 条」（2026-09-11），呈报候批→本次 CEO 批文转正。

## 1. 文档定位

本文用于约束 TriCompany 当前阶段的会议组织、会议开始 / 结束口径、动作项回填与跟进方式。

本制度已正式生效（2026-09-14 00:33 CEO 批准转正，原「研发草案」态自此解除——见文档头与批准记录节；§1 残句勘正 2026-09-30，BOD 定性认「09-14 转正漏改残句」）。秘书处和行政管理的正式归属应对齐 CAO 与 `CompanyGovernanceRegistry`；人力资源、岗位启用和交接治理归 CHO 侧，不再与 CAO 混写。

## 2. 当前阶段责任

- CAO 已在当前 Copilot-host live 阶段启用，秘书处日常机制、会议制度、纪要归档和行政治理资料归属由 CAO 主责
- 会议开始、会议结束、纪要收口、动作项跟踪仍由总助进行公司级协调和催办；制度 owner 与归档规则由 CAO 维护
- **COS 职责定谳（CEO 2026-09-16 令）**：董事长助理=承上启下的会议记录与整理中枢——对董事会：零散讨论→整理任务书→呈批→董事会令；对 COO：监督执行+做 COO 上下文主干备份；sg m-duty-cos 与本机 m-cos 互备交叉验证。岗位定位本体入册归 CHO（CHO 域），本节只登记会议机制面定位。
- 涉及岗位 / 职责交接的 checklist 与 completion tracking，按 `TriCompany/docs/workflow/chief-human-resources-officer-handoff-governance.md` 执行，并归 CHO 侧治理；CHO 已在当前 Copilot-host live 阶段启用

## 3. 会议开始口径

开始会议时至少要收口：

- 会议名称
- 会议目的
- 参会角色
- 当前背景
- 核心议题
- 预期产物

信息不足时，只补问关键缺口，不做机械式连环提问。

## 4. 会议结束口径

结束会议时至少要收口：

- 已确认结论
- 冻结项
- 升级项
- 动作项
- 责任人
- 截止时间
- 会后需要回填的文档或 registry
- 活跃模块是否存在需要收口的 `Git Health` / dirty worktree / 本地提交事项
- 若涉及 operating record，必须区分“当前周维护面”与“单条事项状态”；默认沿用 `CompanyGovernanceRegistry` 中定义的 `active` / `frozen` / `stale-review` / `closed`

## 5. 会后回填要求

当前阶段优先回填到：

- docs/execution 下对应阶段文档
- 需要变化的 docs/product 或 docs/engineering 文档
- 需要变化的 docs/registry/product-state.md 或 code-state.md
- 需要变化的 `CompanyGovernanceRegistry` 术语、秘书处规则或 operating record 术语对齐说明
- 总助认知资产中确有必要长期保留的部分

如果活跃模块的本地脏改动跨过一个会议周期仍未收口，应同步进入 operating record 的 `blockedItems` 或 `nextActions`，并标明：

- 模块名
- 当前 owner
- dirty worktree 原因
- 是否已有可提交切片
- 预期本地提交或冻结时间
- 若事项进入 operating record，单条事项状态默认只写 `active` / `frozen` / `stale-review` / `closed`；模块状态默认写“现役模块 / 占位模块 / 待初始化模块 / 待迁移模块 / 待归档兼容仓”，不得混成一套
- 若事项进入 operating record 的未决事项清单，至少写出：**事项 ID / 事项名称 / 事项简介 / 事项状态 / 当前进度**；推荐继续补齐来源、当前动作、下一步、恢复条件或截止时间、Owner

## 5.1 待办复查入口

- 当 CEO、总助或秘书处要求对当前未决事项做一次正式复查时，默认使用：
  - `/待办复查`
  - `/review-backlog`（ASCII 兼容入口）
- 该动作默认复查**当前周维护面**，而不是随意抽查历史周；若用户指定其他 `OPERATING_PLAN`，以用户指定为准。
- “超过 3 天未续推”默认触发**复查**，不是自动冻结；复查后才判断维持 `active`、改为 `stale-review`、改为 `frozen`，或直接 `closed`。
- 若复查结论改变了当前周维护面的事项状态、当前进度、下一步或 owner，默认同步更新最新 active `OPERATING_PLAN` 的 Markdown 与 JSON，除非用户明确要求“只分析，不回填”。

## 6. 文档语言规则

- 公司级、模块级、registry、workflow、产品、技术、执行、培训和经营记录文档默认中文优先。
- 专有名词、模块名、命令、代码符号、schema 字段、API 字段、许可证、上游引用、宿主格式字段和对外英文材料可保留英文。
- `reference/` 与 `vendor/` 中的上游文件默认保留原貌；进入自有文档、registry 或 workflow 后，应转换为中文优先口径。
- 若存在特殊原因需要英文为主，应在文档中说明面向对象或宿主格式原因。

## 7. 当前边界

- 不把会中讨论直接写成已确认结论
- 不跳过冻结项、升级项和 owner
- 不把研发草案误写成正式公司制度定稿
- 不把当前 Copilot-host live 上岗写成 TriMC 正式宿主切换或完整授权矩阵完成

## 8. Agent 合同与宿主迁移（落点索引）

- agent 合同机制的永久落点：`TriMetaverse/docs/registry/company-governance-state.md` → `Agent Contract-Based Migration Approach`
- 所有核心 Role Agent 的 contract 文件统一存放于：`TriCompany/docs/registry/<AgentID>.contract.yaml`
- 路径治理规则（固定前置核查 item 0 + 交接路径治理）已写入 CEOChiefOfStaff / ChiefProductOfficer / ChiefTechnologyOfficer 三份核心 contract
- 涉及岗位交接、宿主迁移或 agent 能力审计时，以 contract 为准进行能力重建，不依赖 `.agent.md` 或 `.prompt.md` 这类宿主特定格式

## 9. 值守班次（2026-09-29 增；CEO 23:09 批令一体方案·23:55 三批②批）

> 正身依据：值守班次节×静默探测一体方案（operating-records 2026-W40 trees/duty-silence-probe-01/cao-consolidated-probe-shift-design.md，BOD 23:24 一体批全批）。本节=班次翼（制度面）成文；探测翼（机器面）归 CTO/FSD 工程线，探测制度条候选号位候批统裁不入本节。

### 9.1 值守角色

1. **值席位**：常设行政班次岗位，由 **sg 独立值席会话**承担（通信正名 m-duty-cos，sg tmux 常驻 7×24 独立会话；与本地域 COS 会话进程/上下文/生命周期全隔离；闲置零消耗、唤醒才计费；单席值不设多席同值）〔2026-10-06 修订：值席位载体由「COS 面兼任」改「sg 独立会话」——LG-065 值席 b+c 组合案 N1·CEO 17:21 批令；黄金段全责条款（§9.2）不变〕；
2. **兜席位**：值席缺位或无响应时的升级承接=BOD（董事会直连会话，全天在位性由宿主面保证）；
3. **值席三责**：告警响应（承接静默探测告警，语义级链路终端）；催办断面（值守窗内对在办单超 D-34/D-27 时限档的在途任务主动催办）；应急通道（应急令第一承接面——停工不停应急先例常态化）；
4. **值席三不**：不代工（只催办不代 owner 办活）；不裁内容面（技术与产品判断归 owner 席）；不动正身（制度与真源改动走批程不走值席通道）。

### 9.2 班段（滚动循环两段制）

| 班段（北京，滚动循环） | 时长 | 值守配置 |
| --- | --- | --- |
| 黄金段 18:00→次日 14:00 | 20h | 值席全责段（告警响应+催办巡检）；sg 侧 0:00-9:00 子段夜航形态照现役值席批次惯例 |
| 禁窗段 14:00-18:00 | 4h | 值席减配**不空窗**（只保留告警响应，催办巡检免——探测 job 照跑不随班段停） |

- 时间底座=纪律册 D-23 v2 排程哲学款（GLM 轨滚动循环「18:00→次日 14:00」逐日接续），班段与排窗同源；
- 与 7×24 的关系：服务域（sg daemon 面）7×24 自动运转归机器面（watchdog/TriMLC-Watchdog），值守针对**半自动本地域 13 席会话面**。

### 9.3 告警消费衔接（对接语义级静默探测）

1. **消费时窗**：idle 升级告警 7×24 进值席位信箱（nudge 事件）——两段都消费，禁窗段消费动作=只转发不停；
2. **值席响应动作链**：收 idle 升级告警→①核对该席在办单（在办账读）→②语义确认（waiting 挂账/深夜候晨/冷却期内=吸收入账不催）→③无豁免理由即转发催办信直达承办席（三选一动作要求：继续办给 ETA／报 waiting 给挂账理由／升级给阻塞点）→④承办席无复超 D-34/D-27 时限档→升级 BOD；
3. **离值兜底（二跳）**：值席位自身静默=探测第二跳对象直告 BOD——值守断链的最后一网；
4. **留痕闭环**：信箱入站 nudge+转发达成 status 双点，值席处置摘要随周索引留痕；
5. **探测判据与阈值正身**：语义级探测方案合卷 §二/§三（三源 OR 豁免／900s 检查节奏／15min 提醒级／30min idle 升级／通道案 a notify 信箱面+值守转发 pipe）——本节只定义消费面，探测实施与制度条号位候批统裁。

### 9.4 排班载体与试运行

- 值班表按周排，COS 汇总写入 operating-records 周索引件（周平面随迁，零新工具）；值席变更=台账状态字段更新，不另立排班工具；
- 首周=试排观察期，班段密度参数候两周读数校准，首版不定死；
- 边界：值守缺位定性归 CHO 个人面线，本节零个人面内容；探测与催办全程观察非处罚（被催即 active=期望行为）；BOD 提醒 CEO 段仍 human。

批准记录：CEO 2026-09-29 23:09 批令（值守班次节设计方案令，一体设计一体批）+23:24 批令回执（两卷一体批全批+滚动循环口径修正采纳）+23:55 三批②批（合卷方案批·值守班次节入册归 CAO 线）；CAO 主笔（班次节设计卷 §二~四 折算）；CTO 合卷抽验认承（2026-09-29 23:46 技术要件零失真，二跳实施位=探测 job 对象配置面随工程实施批）；CPO §八「值守班次节衔接归 CAO 成卷域」闭合=本节 9.3；**2026-10-06 §9.1 值席位载体修订**（LG-065 值席 b+c 组合案 N1·任务书 07683648·CEO 17:21 批令·BOD 立书）：COS 起草（sec9-amendment-draft-n1.md）→**CAO 会签 2026-10-06T17:34:07+0800（内容面+归属面双认**：§9.1 现行文逐字核对吻合+最小 diff 防夹带五项清点实核零夹带+全件触点清点 L119 系唯一载体条款零内部矛盾+L33 互备表述兼容；事实锚=sg fleet tmux m-duty-cos 10-03 22:45 起在役（COS 值席窗活体现探进程 3136462，CAO 面不越机面未独立复探——载体在役性由值席窗与 N3 兜底链实测双线后续覆盖））→CAO 落正身（一物一册一 owner 唯一通道，稿流程「COS 代笔」环节由 owner 自替）；m-cos 零改动 diff 断言随 N1 收口（任务书验收锚③）。

## 10. 铸单主流程（指针）

- 铸单主流程制度正身：`TriCompany/docs/workflow/cast-order-mainflow.md`（2026-09-30 02:56 CEO 批）——六环节「CEO 内容→BOD 完善→COS 整理→回 CEO 批成正式任务→COS 发 COO 派工并监督催办→审批反向催 BOD」全链折算既有正身；本文件不复制条文（防双写），与本制度 §9 值守班次的咬合关系见正身 §5.3。
