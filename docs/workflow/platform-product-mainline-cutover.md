# 完整模型 API 平台产品主链切换说明

版本：V0.2
日期：2026-06-29
状态：切换执行中

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/platform-product-mainline-cutover.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 当前不发布
- lastSyncedAt: 2026-06-29

## 1. 目的

本文用于把当前重心从“审批回填链继续扩张”切回“完整模型 API 平台产品主链推进”。

当前结论是：

1. [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 只保留最小 contract 收口用途，不再承担产品主链推进职责。
2. 产品主链直接切到 `IPD-20260610-PLATFORM-001` 这条 full-scope case。
3. 当前真实推进目标不是补更多审批稿，而是先产出完整 PRD、再切第一条可编码产品切片。
4. `IPD-20260611-PLATFORM-001` 已完成 `ceo-demand -> delivery` 全链路 proving-ground replay；其中已经验证通过的 `Discovery / Intelligence` 自动化能力不再重复研发，但其正式并入目标首先是公司级 IPD 基线；`IPD-20260610-PLATFORM-001` 是当前主链对该基线的首个 full-scope 消费与后续 Gate A / Gate B / Gate C 继续验证实例。

## 2. 当前依据

### 2.1 full-scope 产品 case 已存在

- archived case: [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/archived-cases/IPD-20260610-PLATFORM-001/case.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/archived-cases/IPD-20260610-PLATFORM-001/case.json)
- discovery work item: [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/archived-cases/IPD-20260610-PLATFORM-001/work-items/01-discovery.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/archived-cases/IPD-20260610-PLATFORM-001/work-items/01-discovery.json)

这条 case 已明确提出三个边界：

1. 不能再把最小 gateway slice 当完整平台 MVP。
2. 必须先形成完整 PRD，再进入 `Designing / Coding`。
3. 必须纳入前端最小 smoke，或明确写出前端不验收边界。

### 2.2 对应 run 也已存在

- active run brief: [../../../TriMetaverse/TriDev-copilot-host-assets/docs/runs/ipd-ipd-20260610-platform-001/SESSION_BRIEF.md](../../../TriMetaverse/TriDev-copilot-host-assets/docs/runs/ipd-ipd-20260610-platform-001/SESSION_BRIEF.md)

当前 run 仍停在：

- `currentStage: DISCOVERY`
- `nextOwner: ChiefProductOfficer`

这说明产品主链并不是不存在，而是已经有入口，但尚未真正被当前周经营动作接管。

### 2.3 discovery / intelligence 自动化优化已在验证桩落地

- discovery output: [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/01-discovery.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/01-discovery.json)
- intelligence output: [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/02-intelligence.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/02-intelligence.json)
- runtime contract source: [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py)
- validation source: [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py)

当前可以确认的已落地优化：

1. `Discovery` 已能自动登记 reference source catalog，并自动刷新 `functional brief / competitor landscape / common capability matrix / highlight opportunity memo`。
2. `Intelligence` 已能自动登记开源 / 公开资料 source catalog，并自动刷新 `capability extraction matrix / opensource landscape / codegraph analysis / architecture option memo`。
3. 上述两阶段已经在 `IPD-20260611-PLATFORM-001` 上完成提交、签发和 release version 发放，说明它们不再是待设计概念，而是已验证的可复用能力。
4. `IPD-20260611-PLATFORM-001` 本身已完成到 `delivery`，因此后续 Gate A / Gate B / Gate C 不再指向它继续补跑，而是指向 `IPD-20260610-PLATFORM-001` 的 full-scope 产品主线消费与必要 replay。

因此，当前正确顺序不是“先把优化写死进某个主链实例”，而是：

1. 先把已验证能力回写到公司级 IPD 基线，书面真源优先落到 [integrated-product-development-flow.md](integrated-product-development-flow.md)，执行真源同步落到 [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与相关 validation contract。
2. 再让 `20260610` 主线直接消费这套更新后的基线。
3. 对确有需要继续推进的特殊旧实例，再人工判断是否手动补齐差异。

`20260610` 主线当前不应重新发明 discovery / intelligence 自动化流程，而应直接继承这套已验证的 package 结构、签发规则和运行时 contract。

## 3. 审批链收口边界

以下审批面继续保留，但只做最小收口：

1. [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
2. [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
3. [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)

收口原则：

1. 只记录第一次真实 contract 判断，不继续膨胀为产品主线替身。
2. 不以审批回填全部完成，作为完整平台 PRD 启动前置条件。
3. 只要最小真实结论能写入，就允许产品主线继续向 `Discovery -> Intelligence -> PRD -> Designing` 推进。

## 4. 产品主链下一步

### 第一步：CPO 先补完整平台 PRD 输入

`ChiefProductOfficer` 先围绕 `IPD-20260610-PLATFORM-001` 输出：

1. 完整模型 API 平台 MVP 的目标用户、核心场景和不做项。
2. 前端 / 后端 / 模拟身份签名边界。
3. 验收矩阵：哪些属于首轮必须可用，哪些后置。
4. 直接复用 `20260611` 已验证的 `Discovery / Intelligence` package 结构，不再另起一套阶段模板。

最小结果要求：不能再只停在 proving-ground 语义，必须形成完整 PRD 入口。

`20260610` 在这一步的正确做法是：

1. 直接沿用 `20260611` 的 `DiscoveryReferenceFunctionalBrief / DiscoveryCompetitorLandscape / DiscoveryCommonCapabilityMatrix / DiscoveryHighlightOpportunityMemo`。
2. 直接沿用 `20260611` 的 `IntelligenceCapabilityExtractionMatrix / IntelligenceOpenSourceLandscape / IntelligenceCodegraphAnalysis / IntelligenceArchitectureOptionMemo`。
3. 只把内容从“验证桩平台壳”替换成“完整平台主线范围”，不再重写自动化 contract 本身。

### 第二步：CTO 把 PRD 收敛成第一条可编码产品切片

`ChiefTechnologyOfficer` 不直接铺满整个平台，而是先收敛出第一条可编码主链，至少明确：

1. 统一模型 API 入口如何定义。
2. provider 配置 / 路由 / 请求日志 / 失败回退中，首轮必须落地哪些。
3. 前端最小 smoke 如何覆盖这条主链。
4. 模拟身份 / 签名机制当前只保留到什么边界，不写成真实链上能力。

### 第三步：围绕这条切片做第一次真正的产品验证

第一轮验证要看的不是审批表，而是：

1. 有代码实现。
2. 有接口调用结果。
3. 有前端最小 smoke。
4. 有失败路径与回退说明。
5. 有交付边界结论：证明的是“当前平台 MVP 切片可用”，不是“生产级平台完成”。

## 5. 以后再做优化、验证、并入时的统一操作

后续如果还要继续优化流程能力，统一按下面三段执行，不再把流程优化和产品主线混写：

### 5.1 optimize

1. 先在 `WORKFLOW-*` 类 case 中定义本轮只优化哪一段能力，例如 `Discovery automation`、`Intelligence capability extraction`、`rollback semantics`。
2. 优化目标只写流程 / runtime / validation contract，不直接宣称产品能力已提升。
3. 每轮优化必须显式说明：要回灌到哪个 proving-ground case 验证。

### 5.2 validate

1. 固定先回灌到 `PLATFORM-001` 这类 proving-ground case 验证。
2. 验证通过的标准不是“感觉顺了”，而是必须有 stage output、evidence、signoff 和 release version。
3. 若验证失败，只回退到优化线修流程，不污染产品主线范围判断。

### 5.3 merge

1. 只有验证桩上已经形成可复用 stage output / runtime contract / validation contract，才允许发起并入。
2. 并入的第一目标永远是 TriCompany 内的公司级 IPD 基线，而不是某个单独实例。
3. 基线更新完成后，新创建实例自动继承；当前活跃主链实例再直接消费更新后的基线。
4. 对特殊旧实例、冻结后重开实例或历史回放实例，可按需要人工判断是否手动补齐差异，但这属于例外，不是默认路径。
5. 并入结果必须写回基线真源与当前主线说明，明确：
   - 哪项能力已并入 TriCompany 的公司级 IPD 基线
   - 哪些新实例会自动复用
   - 哪些旧实例需要手动补齐差异
   - 产品主线还剩哪些内容没有被验证桩覆盖

## 6. 本轮不再做

1. 不继续扩充审批稿字段，只保留最小真实回填。
2. 不把 `IPD-20260611-PLATFORM-001` 的 proving-ground replay 写成完整平台产品成熟。
3. 不把 TriChain / TriWeb4 的真实链上身份与签名能力写成现役实现。

## 7. 当前成功标准

满足以下条件，才算真正完成“切回产品主链”：

1. 当前周经营维护面已明确把主线切到 `IPD-20260610-PLATFORM-001`。
2. CPO 已开始输出完整平台 PRD 输入，而不是继续停在审批占位。
3. `20260611` 上已验证的 `Discovery / Intelligence` 自动化能力已经明确标记为可复用，并直接并入 `20260610` 主线。
4. CTO 已把第一条产品主链切片收敛到可编码范围。
5. 后续验证开始围绕产品代码与产品调用结果，而不是继续围绕审批稿本身。
