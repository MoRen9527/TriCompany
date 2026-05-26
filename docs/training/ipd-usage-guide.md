# IPD 使用教程（面向 RAndDTrainer 与技术研发新人）

版本：V0.1

日期：2026-05-25

状态：当前 Copilot-host live 阶段可用的最小教程

## 1. 这份教程讲什么

这份教程讲的是：在当前 TriCompany 边界里，如何使用已经落下来的 IPD 最小运行面，把一条来自 CEO / CEOChiefOfStaff 的总目标，推进成可由各个岗位继续细化的工作链。

它不是讲 TriMC 正式宿主，也不是讲完整自动化公司。它只讲当前已经可用的最小闭环：

- CEO / 总助先创建一条 IPD case
- 由 CEO / 总助做 intake 书面签核
- 系统自动放行到当前阶段 owner
- owner 提交阶段产物
- CEO / 总助再做书面签核
- 签核通过后自动进入下一阶段

## 2. 这份教程适合谁

- RAndDTrainer 小吴
- 需要给研发新人讲解 IPD 最小闭环的人
- 需要接手 TriCompany workflow / runtime 的研发同学
- 需要理解“公司级 IPD 流程”和“TriDev 开发执行段”边界的人

## 3. 先记住三条边界

### 3.1 当前讲的是 TriCompany 公司级 IPD

这里讲的是 TriCompany 承载的公司侧主动交付 / 协同 / 核签层，不是说 TriCompany 自己另外再平行造一条脱离十阶段的第二套开发流程。

更准确地说：对开发型项目，当前 canonical 口径是 **TriDev 承接项目级 ten-phase engine，TriCompany 负责控制哪些员工在各阶段参与、提交什么资料、形成什么版本化 gate package，并由总助 / CEO 决定是否放行下一阶段**。

### 3.2 当前讲的是本地 Copilot-host 正式接管边界

这里的 CLI 和 case state machine，成立于当前 TriCompany source-side 与 `TriCompany-copilot-host-assets` support root 的边界里。

这不等于 TriMC 正式宿主切换完成。

### 3.3 当前是最小可运行闭环，不是完整生产化平台

现在已经有：

- IPD case 初始化
- intake 签核
- ten-phase case line
- 当前阶段 work item 生成
- 阶段产物提交
- 总助先签、CEO 终签
- 自动放行下一阶段

现在还没有：

- PRD 分叉并行
- 多分支 delivery 聚合
- 独立 phase package schema 族
- 完整岗位 adapter 自动写文档
- 正式宿主级调度器

## 4. IPD runtime 现在如何与十阶段对齐

先分清三件事：

1. `TriMetaverse/project.md` 里的十阶段主线仍是开发型项目的 canonical phase engine：`DISCOVERY -> INTELLIGENCE -> DESIGNING -> CODING -> VERIFY-INTEGRATION -> REDTEAM -> QA -> DEPLOYMENT -> ASSURANCE -> DELIVERY`。
2. `TriCompany IPD case` 不是第二套平行开发流程，而是把赛博公司的员工参与、资料组织、门禁和总助 / CEO 核签挂到这条主线上。
3. **当前 source-side runtime 已经开始按十阶段一比一运行**，不再是之前那种压缩节点链路。

但要提醒新人：现在的一比一 runtime，仍然只是当前阶段的 source-side case line。

它已经有：

- ten-phase stage line
- phase work item
- phase package draft
- 总助先签、CEO 终签
- 自动推进到下一 phase

它还没有：

- PRD 分叉并行
- 多分支 delivery 聚合
- 独立 phase package schema 族
- 完整岗位 adapter 自动写文档
- 正式宿主级调度器

当前一比一 ten-phase runtime 的主责如下：

| Phase | 当前 owner | 关键参与 | 主要输出 |
| --- | --- | --- | --- |
| `DISCOVERY` | `CEOChiefOfStaff` | `CEO`、`ChiefMarketingOfficer` | Discovery package |
| `INTELLIGENCE` | `ChiefProductOfficer` | `CEOChiefOfStaff`、`ChiefMarketingOfficer`、`ChiefOperatingOfficer`、`ChiefFinancialOfficer` | Intelligence package、PRD、项目计划 |
| `DESIGNING` | `ChiefTechnologyOfficer` | `ChiefProductOfficer`、`TriDev` | Design package、技术方案 |
| `CODING` | `TriDev` | `ChiefTechnologyOfficer`、`TriTest` | Coding package、开发产物 |
| `VERIFY-INTEGRATION` | `TriTest` | `TriDev`、`ChiefTechnologyOfficer` | Verify package |
| `REDTEAM` | `TriTest` | `ChiefTechnologyOfficer`、`TriDev` | Redteam package |
| `QA` | `TriTest` | `ChiefProductOfficer`、`ChiefTechnologyOfficer`、`TriDev` | QA package |
| `DEPLOYMENT` | `TriDeployment` | `TriDev`、`ChiefOperatingOfficer`、`ChiefFinancialOfficer` | Deployment package |
| `ASSURANCE` | `ChiefOperatingOfficer` | `ChiefFinancialOfficer`、`TriDeployment`、`TriTest` | Assurance package |
| `DELIVERY` | `CEOChiefOfStaff` | `CEO`、`ChiefOperatingOfficer`、`ChiefFinancialOfficer`、`ChiefProductOfficer`、`ChiefTechnologyOfficer` | Delivery package |

## 5. CLI 入口在哪里

在 `TriCompany` 根目录执行：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case --help
```

当前可用子命令：

- `task-intake`
- `init`
- `intake-approve`
- `submit`
- `signoff`
- `status`
- `step`

当前 ten-phase stage key 是：

1. `discovery`
2. `intelligence`
3. `designing`
4. `coding`
5. `verify-integration`
6. `redteam`
7. `qa`
8. `deployment`
9. `assurance`
10. `delivery`

## 6. 一条最小 IPD case 怎么启动

### 6.1 第一步：先用 `task-intake` 接住 CEO / 总助的粗任务

当上游只有一句总要求时，先不要逼 CEO 或总助一次写完全部字段，先把任务落成 case：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case task-intake `
  "做一个自动化开发软件，在公司级别从下发任务到总助评估分派各部门，部分负责人细化，按公司流程有序进行开发、验证、交付和长期运维"
```

这一步会先生成 case 和 intake briefing 草稿。

### 6.2 第二步：再用 `init` 把 intake briefing 精调成可签版本

`task-intake` 之后，总助再把同一条 case 精调成结构化 briefing：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case init `
  --case-id IPD-001 `
  --title "自动化开发执行闭环" `
  --objective "建立从 CEO 任务到交付收口的最小 IPD 引擎" `
  --task-description "CEO 和总助只提总要求，后续由各个 O 与 TriDev 细化推进。" `
  --opportunity-signal "AI coding 与 agent workflow 正在成为明显增量热点。" `
  --business-model-fit "符合当前小成本先跑通可收费闭环、先验证再扩大的路线。" `
  --stage-fit "符合当前 Copilot-host 正式接管阶段，先验证公司级 ten-phase runtime slice。" `
  --company-context "TriCompany 已有一比一 ten-phase IPD runtime，可先跑通单 case 单主线闭环。" `
  --owner-proposal "总助先做 intake briefing，随后按 DISCOVERY -> DELIVERY 的 phase owner 推进。" `
  --resource-envelope "预计 CTO / TriDev 首轮投入 2-3 人天，当前主要为时间与工具试验成本。" `
  --prerequisite "CEO 确认进入 IPD 主动交付线。" `
  --required-support "CMO / COO / CFO / CPO / CTO / TriDev / TriTest / TriDeployment 需按 phase 补齐判断与证据。" `
  --expected-outcome "形成一条可重复运行的一比一 ten-phase IPD 闭环。" `
  --related-module TriCompany `
  --related-module TriDev
```

### 6.3 第三步：做 intake 核签，总助先签、CEO 后签

如果 case 是总助自己创建的，总助那一签通常已经自动通过；但培训时仍要讲清楚 canonical 顺序：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case intake-approve `
  --case-id IPD-001 `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case intake-approve `
  --case-id IPD-001 `
  --role CEO
```

第二签通过后，case 会自动进入 `discovery`。

### 6.4 第四步：提交 `discovery` package

`discovery` 的 owner 是 `CEOChiefOfStaff`，这一阶段主要沉淀任务意图、目标边界和 raw evidence。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key discovery `
  --submitted-by CEOChiefOfStaff `
  --summary "Discovery package 已提交" `
  --detail "已沉淀任务意图、成功信号、边界约束和 raw evidence pack" `
  --evidence "docs/workflow/ipd-001-discovery.md"
```

### 6.5 第五步：签 `discovery`，放行到 `intelligence`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key discovery `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key discovery `
  --role CEO
```

### 6.6 第六步：提交 `intelligence` package

`intelligence` 的 owner 是 `ChiefProductOfficer`，但总助、CMO、COO、CFO 仍继续提供结构化输入。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key intelligence `
  --submitted-by ChiefProductOfficer `
  --summary "Intelligence package 已提交" `
  --detail "已把 Discovery、市场、运营和财务输入整理成结构化输入包与 PRD 草案" `
  --evidence "docs/product/ipd-001-intelligence.md"
```

### 6.7 第七步：签 `intelligence`，放行到 `designing`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key intelligence `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key intelligence `
  --role CEO
```

### 6.8 第八步：提交 `designing` package

`designing` 的 owner 是 `ChiefTechnologyOfficer`，这一阶段把产品定义收口成技术路线、工程门禁和任务拆解。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key designing `
  --submitted-by ChiefTechnologyOfficer `
  --summary "Design package 已提交" `
  --detail "已明确技术路线、工程门禁、任务拆解和 phase handoff" `
  --evidence "docs/engineering/ipd-001-designing.md"
```

### 6.9 第九步：签 `designing`，放行到 `coding`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key designing `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key designing `
  --role CEO
```

### 6.10 第十步：提交 `coding` package

`coding` 的 owner 是 `TriDev`，这里提交的是开发实现、执行证据和候选 release bundle。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key coding `
  --submitted-by TriDev `
  --summary "Coding package 已提交" `
  --detail "已提交开发产物、执行证据、失败记录和候选 release bundle" `
  --evidence "docs/execution/ipd-001-coding.md"
```

### 6.11 第十一步：签 `coding`，放行到 `verify-integration`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key coding `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key coding `
  --role CEO
```

### 6.12 第十二步：提交 `verify-integration` package

`verify-integration` 的 owner 是 `TriTest`，这里提交系统级验证结果、缺陷清单和集成测试证据。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key verify-integration `
  --submitted-by TriTest `
  --summary "Verify package 已提交" `
  --detail "已完成系统级验证、缺陷归档和集成测试收口" `
  --evidence "docs/execution/ipd-001-verify-integration.md"
```

### 6.13 第十三步：签 `verify-integration`，放行到 `redteam`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key verify-integration `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key verify-integration `
  --role CEO
```

### 6.14 第十四步：提交 `redteam` package

`redteam` 的 owner 仍是 `TriTest`，这里提交的是对抗审查、安全风险和高风险问题分级。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key redteam `
  --submitted-by TriTest `
  --summary "Redteam package 已提交" `
  --detail "已完成红队审查、安全复核和高风险问题归档" `
  --evidence "docs/execution/ipd-001-redteam.md"
```

### 6.15 第十五步：签 `redteam`，放行到 `qa`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key redteam `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key redteam `
  --role CEO
```

### 6.16 第十六步：提交 `qa` package

`qa` 的 owner 是 `TriTest`，这里提交统一质量评分、放行结论和待修问题。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key qa `
  --submitted-by TriTest `
  --summary "QA package 已提交" `
  --detail "已完成统一质量评分、问题分级和部署放行建议" `
  --evidence "docs/execution/ipd-001-qa.md"
```

### 6.17 第十七步：签 `qa`，放行到 `deployment`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key qa `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key qa `
  --role CEO
```

### 6.18 第十八步：提交 `deployment` package

`deployment` 的 owner 是 `TriDeployment`，这里提交部署证据、发布说明、上线窗口和 rollout 计划。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key deployment `
  --submitted-by TriDeployment `
  --summary "Deployment package 已提交" `
  --detail "已沉淀部署证据、发布说明、上线窗口和 rollout plan" `
  --evidence "docs/execution/ipd-001-deployment.md"
```

### 6.19 第十九步：签 `deployment`，放行到 `assurance`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key deployment `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key deployment `
  --role CEO
```

### 6.20 第二十步：提交 `assurance` package

`assurance` 的 owner 是 `ChiefOperatingOfficer`，这里沉淀运行观察、恢复验证和成本影响；CFO、TriDeployment、TriTest 也会参与。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key assurance `
  --submitted-by ChiefOperatingOfficer `
  --summary "Assurance package 已提交" `
  --detail "已沉淀运行观察、恢复验证、成本影响和 assurance evidence" `
  --evidence "docs/workflow/ipd-001-assurance.md"
```

### 6.21 第二十一步：签 `assurance`，放行到 `delivery`

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key assurance `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key assurance `
  --role CEO
```

### 6.22 第二十二步：提交 `delivery` package

`delivery` 的 owner 回到 `CEOChiefOfStaff`，这一步不是重复写总结，而是把整条 case 收成最终交付结论、版本化 gate package 和后续行动。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-001 `
  --stage-key delivery `
  --submitted-by CEOChiefOfStaff `
  --summary "Delivery package 已提交" `
  --detail "已形成最终交付结论、版本化 gate package、待办和下一轮动作" `
  --evidence "docs/workflow/ipd-001-delivery.md"
```

### 6.23 第二十三步：签 `delivery`，把 case 正式收口

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key delivery `
  --role CEOChiefOfStaff

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-001 `
  --stage-key delivery `
  --role CEO
```

第二签通过后，case 状态会进入 `completed`。

### 6.24 第二十四步：随时用 `status` 看当前位置

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case status `
  --case-id IPD-001
```

培训时至少要让新人看懂这几个字段：

- `status`
- `currentStageKey`
- `currentOwnerRole`
- `completedStageCount`
- `stageCount`

## 7. work item 和输出会写到哪里

当前默认写到总助 workbench 下：

- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/case.json`
- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/intake-brief.json`
- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/events.jsonl`
- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/work-items/*.json`
- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/outputs/*.json`

里面会逐步出现：

- `case.json`：当前 case 主状态
- `intake-brief.json`：当前供总助 / CEO 签核的入口 briefing
- `events.jsonl`：事件流水
- `work-items/*.json`：当前节点工作单
- `outputs/*.json`：owner 提交的节点产物

这是一套运行态对象，不是中央真源文档本身。

## 8. `step` 是干什么的

`step` 用来重算 case，让系统按当前状态判断是否需要推进。

单条 case：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case step --case-id IPD-001
```

全部 case：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case step
```

这已经接到 checkpoint 体系；`checkpointKind=ipd-case-step` 可以让现有 checkpoint / schedule 体系重算 IPD case。

## 9. RAndDTrainer 在培训时最需要强调什么

### 9.1 入口顺序是 `task-intake -> init -> intake-approve`

不要再把 `init` 讲成唯一入口，也不要把 `task-intake` 讲成临时兼容命令。

### 9.2 当前 runtime 已经按 ten-phase 一比一运行

不要再讲成“前半段压缩承接，后半段才进入十阶段”。

### 9.3 签核是 gate，不是装饰字段

每个 phase 都必须先 `CEOChiefOfStaff`，再 `CEO`；没签完就不会自动进入下一阶段。

### 9.4 TriCompany 和 TriDev 不是同一个 owner

TriCompany 负责公司员工参与、资料组织、书面门禁和核签；TriDev 负责开发执行段 phase engine。

### 9.5 `completed` 不是“自动化公司已经全部完成”

它只表示当前 case 在当前 scope 下完成了一轮公司级交付闭环。

## 10. 建议的授课顺序

1. 先讲 `task-intake -> init -> intake-approve`。
2. 再讲 `discovery -> intelligence -> designing`，说明为什么 TriDev 不是第一分钟就接手。
3. 再讲 `coding -> verify-integration -> redteam -> qa -> deployment`，说明 TriDev / TriTest / TriDeployment 如何进入主线。
4. 最后讲 `assurance -> delivery`，说明为什么交付后仍然需要公司侧运行保障和最终收口。
5. 收尾再讲 `status`、`step` 和 workbench 路径。

## 11. 常见误区

1. 把 `task-intake` 当成可跳过的临时命令。
2. 把 `TriDev` 讲成整个公司级 IPD 流程 owner。
3. 把 `completed` 讲成“完整自动化公司已经落地”。
4. 把当前 runtime 讲成“十阶段还没真正进入，只是压缩适配”。

## 12. 真源回链

- `TriCompany/docs/workflow/integrated-product-development-flow.md`
- `TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md`
- `TriCompany/docs/workflow/rd-trainer-role.md`
- `TriCompany/runtime/cognition/ipd_case_engine.py`
- `TriCompany/runtime/cognition/chief_of_staff_ipd_case.py`
- `TriMetaverse/docs/三元宇宙架构与模块说明.md`
