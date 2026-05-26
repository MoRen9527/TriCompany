# 集成产品开发流程（IPD 流程）

版本：V0.2
日期：2026-05-27
状态：当前 Copilot-host live 阶段流程设计（补充 Discovery 新模块单项发布与 TriDev init 对接）

## 1. 文档定位

本文定义 TriCompany 当前阶段的集成产品开发流程（IPD 流程）。

当前项目真源改按更清晰的两层关系理解：

1. `TriCompany` 负责公司侧流程、员工参与、资料组织、门禁完善与书面核签。
2. `TriDev` 负责开发型项目的项目级十阶段 phase engine。
3. `IPD` 不是与项目十阶段并行的第二套开发流程，而是赛博公司围绕这条十阶段主线的参与 / 协同 / 放行机制。

当前设计只代表虚拟公司研发阶段和本地 Copilot-host 正式接管阶段，不代表 TriMC 正式宿主、生产级自动运营看板或完整授权矩阵已经完成。

## 2. 流程总名与两条线

当前总名采用：

- `TriCompany IPD 双线闭环`

两条工作线分别为：

- `IPD 市场雷达线`：由 CMO 主责，持续发现公司内外部需求、市场信号、竞品变化、热点、用户痛点和风险机会；该线只形成机会候选，不直接启动开发。
- `IPD 主动交付线`：由 CEO / CEOChiefOfStaff 正式下发需求或任务后启动；公司员工按 CMO、COO、CFO、CPO、CTO、开发执行、验收、运营、财务、总助收口的顺序参与，而流程主线默认挂接到 `TriDev` 的项目级十阶段。

两条线的衔接规则：

`IPD 市场雷达线 -> CEO / CEOChiefOfStaff 决策 -> 正式需求 / 任务 -> IPD 主动交付线`

## 3. IPD 市场雷达线

市场雷达线是被动机会发现机制，不等于正式立项。

| 阶段 | 主责 | 参与 | 输入 | 输出 |
| --- | --- | --- | --- | --- |
| 1. 日常市场扫描 | CMO | CEOChiefOfStaff、CPO、COO、CFO | 竞品、行业新闻、热点、用户反馈、公司内部需求、销售或运营线索 | 市场雷达日报 / 周报 |
| 2. 机会归类 | CMO | CPO、COO、CFO | 市场雷达材料 | 用户痛点、产品机会、运营机会、财务风险、待验证假设 |
| 3. 初筛建议 | CMO | CEOChiefOfStaff | 高价值机会候选 | 机会建议、证据摘要、建议是否进入决策 |
| 4. 决策分流 | CEO / CEOChiefOfStaff | CMO、CPO、COO、CFO、CTO | 机会建议 | 丢弃、继续观察、补充调研、进入正式任务 |
| 5. 主动线触发 | CEO / CEOChiefOfStaff | CMO、CPO、COO、CFO、CTO | 正式任务决定 | IPD 主动交付线启动 |

市场雷达线的最小证据要求：

- 来源、时间、样本范围和可信度。
- 事实、判断、假设和待验证问题分开写。
- 不能把未经验证的搜索材料包装成市场结论。
- 不能绕过 CEO / CEOChiefOfStaff 决策直接要求 TriDev 开发。

## 4. IPD 主动交付线

主动交付线用于把正式需求或任务推进到产品交付、运营和财务收口。

对开发型产品，当前 canonical 口径已进一步落到 source-side runtime：`TriDev` 直接承接项目级十阶段主线，`TriCompany IPD case` 负责把员工参与、资料与核签要求一比一挂到这条主线上。

当前 source-side runtime 已开始按 discovery 到 delivery 的 ten-phase stage line 生成 work item、phase package draft、书面签核和自动推进；当前仍未完成的是 PRD 分叉并行、多分支 delivery 聚合、独立 phase package schema 族和完整岗位 adapter。

| 阶段 | 主责 | 参与 | 关键职责 | 输出 |
| --- | --- | --- | --- | --- |
| 1. Discovery | CEOChiefOfStaff | CEO、CMO | 沉淀任务意图、目标边界、Discovery 真源草稿和 raw evidence pack；如涉及新正式模块，同步生成模块标配单项发布草案 | Discovery package、NewModuleBaselineRelease（如涉及新模块） |
| 2. Intelligence | CPO | CEOChiefOfStaff、CMO、COO、CFO | 把市场、运营、财务输入结构化并收口成 PRD / 项目计划 / 验收标准 | Intelligence package、PRD、项目计划 |
| 3. Designing | CTO | CPO、TriDev | 产出技术路线、工程门禁、任务拆解和 phase handoff | Design package、技术方案 |
| 4. Coding | TriDev | CTO、TriTest | 执行开发实现并沉淀代码、artifact、失败 / 回滚记录和候选 release bundle | Coding package、开发产物 |
| 5. Verify-Integration | TriTest | TriDev、CTO | 执行系统级验证、集成测试和缺陷收口 | Verify package |
| 6. Redteam | TriTest | CTO、TriDev | 执行对抗审查、安全问题分级和整改要求 | Redteam package |
| 7. QA | TriTest | CPO、CTO、TriDev | 给出统一质量评分和是否允许部署的结论 | QA package |
| 8. Deployment | TriDeployment | TriDev、COO、CFO | 形成部署证据、发布说明、上线窗口和 rollout plan | Deployment package |
| 9. Assurance | COO | CFO、TriDeployment、TriTest | 沉淀运行观察、恢复验证、成本影响和 assurance evidence | Assurance package |
| 10. Delivery | CEOChiefOfStaff | CEO、COO、CFO、CPO、CTO | 形成最终交付结论、版本化 gate package 和后续动作 | Delivery package |

### 4.1 Discovery 标准动作：新模块单项发布

- 当 `Discovery` 判断该事项需要新增正式模块（而非落到既有模块）时，必须同步形成 `NewModuleBaselineRelease`，并作为阶段内标准产物进入门禁。
- `NewModuleBaselineRelease` 最小内容：
  1. 模块归属路由与边界结论（既有模块 / 新正式模块）。
  2. 模块标配骨架：独立 git 仓、`README.md`、`docs/` 六件套、根级 `.gitignore`、本地 CodeGraph 初始化计划。
  3. `vendor-extraction-profile`：source、version anchor、subpath 映射、patch 策略、回滚点与审计说明。
  4. owner 与签核链：CPO（归属）、CTO（技术与抽取）、CAO（治理）、总助与 CEO（放行）。
- 发布状态机固定为 `candidate -> approved -> init`：
  - `candidate`：Discovery 草案阶段，可迭代，不得写成已落地模块。
  - `approved`：完成跨岗位签核，允许进入初始化执行。
  - `init`：由 `TriDev init` 消费已签核发布包并落下模块骨架。
- `TriDev init` 属于流程层执行动作，不替代 CPO 的归属判断、CTO 的长期技术路线设计和后续 `INTELLIGENCE / DESIGNING` 的正式收口。

## 5. TriDev 接入规则

这里不要把 TriDev 理解成表里某一个瞬时“开发执行”动作。

更准确地说，在当前 canonical 口径里：

1. `TriDev` 是开发型项目十阶段的流程层 / phase engine。
2. `TriCompany IPD case` 是公司侧任务、资料、门禁、核签和跨岗位协同层。
3. 赛博公司的员工在 `TriDev` 十阶段各节点参与提交资料、完善门禁、形成可签发版本号的 gate package，再由总助 / CEO 决定是否放行下一阶段。
4. 当前 source-side runtime 已按 ten-stage 提供 discovery 到 delivery 的一比一 stage line，但 PRD 分叉并行、多分支 delivery 聚合、独立 package schema 族和完整岗位 adapter 仍待继续补齐。

在当前 source-side runtime 里，TriDev 在新模块场景下可从 `Discovery` 的 `init` 动作提前进入（消费 `NewModuleBaselineRelease` 执行模块骨架初始化），并在 designing / coding 阶段持续承接 phase engine；更早的公司侧分诊与更晚的经营复盘，仍由 TriCompany 组织员工参与和书面放行。

1. CEO / CEOChiefOfStaff 已确认该事项进入 IPD 主动交付线。
2. CMO 已提供最小市场证据或 CEO 明确允许跳过补证。
3. COO 已给出上线节奏、试点路径或运营约束。
4. CFO 已给出预算护栏、成本约束或停止条件。
5. CPO 已给出 PRD、MVP 范围、验收标准和项目计划。
6. CTO 已给出技术路线、开发任务拆解和工程门禁。
7. 若涉及新正式模块：`NewModuleBaselineRelease` 已达到 `approved`，且 `TriDev init` 已完成首轮骨架初始化。

TriDev 接入后负责：

- 维护开发型项目的十阶段流程层、phase state、分叉与版本包签发。
- 建立开发 run。
- 沉淀设计、编码、验证、发布和 assurance 所需的 gate / evidence / artifact / 版本包。
- 绑定 PRD、技术方案、市场证据、运营计划和预算护栏为输入证据。
- 执行阶段 gate、artifact 记录、digest 校验、failure / rollback / resume 和 release bundle。
- 将可验收产物交回 CTO / CPO。
- 将交付证据提供给 COO 做运营接管，提供给 CFO 做决算复盘。

TriDev 不负责：

- 决定是否立项。
- 替 CMO 做市场判断。
- 替 CPO 写产品范围和验收标准。
- 替 COO 负责运营复盘。
- 替 CFO 负责预算和决算。
- 替 CTO 决定长期技术路线。

## 6. 关键门禁

| 门禁 | 决策 owner | 通过条件 |
| --- | --- | --- |
| 机会进入决策 | CEO / CEOChiefOfStaff | 市场雷达线提供足够机会信息，或 CEO 直接提出战略需求 |
| 正式进入主动交付线 | CEO / CEOChiefOfStaff | 明确任务、目标、优先级、约束、owner，以及已由总助预梳理的 intake briefing（包含商业模式 / 阶段适配判断）；默认总助先签、CEO 终签 |
| PRD 就绪 | CPO | Discovery 真源草稿、市场证据、运营约束、预算护栏和产品范围可对齐 |
| 技术实施就绪 | CTO | 技术路线、工程门禁、开发任务和依赖边界清楚 |
| TriDev 接入 | CTO / CPO | PRD、验收标准、技术任务和输入证据齐备；若涉及新正式模块，还需 `NewModuleBaselineRelease=approved` 且 `TriDev init` 已完成 |
| 产品验收 | CPO | 交付产物满足 PRD 与验收标准 |
| 运营接管 | COO | rollout、观察指标、恢复动作和复盘机制明确 |
| 财务决算 | CFO | 实际成本、预算偏差、收益假设和停止条件可复核 |
| 总助收口 | CEOChiefOfStaff | 证据、状态、阻塞、复盘和下一步动作可回填 |

## 7. 当前阶段边界

- 当前 IPD 流程是 docs-first 的公司级流程设计，优先服务当前 Copilot-host live 阶段。
- 当前 CMO / CPO / COO / CFO / CTO 已进入 Copilot-host live 阶段，但不代表完整授权矩阵、自动数据管道、自动运营看板或自动财务系统已完成。
- 当前 TriDev 已具备 Copilot-host 本地开发执行 engine 可靠性切片，但不代表 ten-stage phase engine 已在 source-side 全量拆开、也不代表完整岗位 adapter、自动任务调度、生产级交付平台或 TriMC 正式宿主已经完成。
- 当前已新增 source-side 一比一 ten-phase runtime slice：CEO / 总助可先创建一条 IPD case；其中总助需先把机会信号、对当前商业模式的适配、对当前阶段的适配、公司现状、owner 建议、资源 envelope、前置条件、所需支持和预期成果整理成 intake briefing，再按“总助先签、CEO 终签”的顺序完成书面签核。签核通过后，runtime 会按 `DISCOVERY -> INTELLIGENCE -> DESIGNING -> CODING -> VERIFY-INTEGRATION -> REDTEAM -> QA -> DEPLOYMENT -> ASSURANCE -> DELIVERY` 的顺序生成阶段 work item，并把 participant roles、input requirements、phase package draft 与总助 / CEO 顺序签核挂到各 phase。当前仍不等于 PRD 分叉并行、多分支 delivery 聚合或完整岗位 adapter 已完成。
- 涉及正式宿主边界、长期模块边界或商业模式裁决时，应升级 BusinessStrategy。

## 8. 市场雷达候选采集工具

`CloakHQ/CloakBrowser` 可作为 CMO 市场雷达线的候选浏览器自动化采集工具，用于公开网页、竞品页面、公开评论区、公开榜单、行业新闻和热点页面的市场证据采集验证。

当前只登记为候选工具，不直接写成已生产接入能力，也不直接进入 reference / vendor 吸收链。若后续决定吸收其代码或二进制能力，必须按项目级开源吸收链执行：`TriMetaverse/reference -> 目标模块/vendor -> 真实实现`。

候选事实：

- 上游仓库：`https://github.com/CloakHQ/CloakBrowser`
- 当前定位：Stealth Chromium / Playwright 替代工具，服务 browser automation 与 web scraping 场景。
- 源码许可：仓库 wrapper 源码标注为 MIT License。
- 二进制许可：CloakBrowser Chromium binary 使用单独 Binary License；允许组织内部运行，但限制再分发、转售、重新打包和面向第三方的 SaaS / OEM 嵌入。
- 当前风险：该工具强调反 bot detection、anti-detect、captcha / Cloudflare 场景，必须按合法公开数据采集、站点条款、robots / rate limit、隐私和授权边界使用。

准入门禁：

1. CMO 只可把它用于公开市场信息、竞品公开页面、新闻、公开评论和公开趋势材料的采集验证。
2. 禁止用于未授权登录、绕过认证、账户批量注册、凭证尝试、金融 / 医疗 / 政府等敏感系统访问或任何未授权数据采集。
3. CTO 需先评估安装、运行隔离、二进制来源校验、版本固定、日志、速率限制和失败回滚。
4. CFO 需评估代理、服务器、存储、调用和维护成本。
5. CAO / CompanyGovernanceRegistry 需确认内部使用和许可证边界，不得把二进制打包进对外产品或服务。
6. 只有在 CMO、CTO、CFO 和 CAO 共同确认后，才能进入最小试点。

## 9. Sources

- `TriCompany/docs/product/PROJECT.md`
- `TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md`
- `TriCompany/docs/registry/product-state.md`
- `TriMetaverse/docs/三元宇宙架构与模块说明.md`
- `TriDev/docs/registry/product-state.md`
- `https://github.com/CloakHQ/CloakBrowser`
