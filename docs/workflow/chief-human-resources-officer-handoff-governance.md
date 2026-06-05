# ChiefHumanResourcesOfficer 交接治理规范

版本：V0.1
日期：2026-05-20
状态：当前 Copilot-host live 阶段交接治理真源；ChiefHumanResourcesOfficer 已独立启用并接管 handoff checklist、completion tracking 与员工生命周期变更验收

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/chief-human-resources-officer-handoff-governance.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 当前无同名 support 副本
- supportSyncRule: 仅在当前宿主需要直接消费 CHO 交接治理对象时再发布 support 副本
- lastSyncedAt: 2026-06-04

## 1. 文档定位

本文用于定义 TriCompany 当前阶段的跨岗位 handoff checklist、completion tracking 和交接验收口径。它同时约束员工入职、岗位职责变动、owner 迁移和源侧五件套增量更新进入当前 live 的验收口径。

它是 ChiefHumanResourcesOfficer 的源侧治理真源之一；当前 ChiefHumanResourcesOfficer 已在 Copilot-host live 阶段独立上岗并接管交接治理执行责任。

CEOChiefOfStaff 保留公司级协调、催办、升级与收口职责；交接治理 owner 不再由 CEOChiefOfStaff 长期代管。

## 1.1 机器对象资产

- 统一 schema：`TriMetaverse/docs/workflow/responsibility-handoff.schema.json`
- 示例对象：`TriMetaverse/docs/workflow/handoff-templates/responsibility-handoff.example.json`
- 自然语言 intake：`TriMetaverse/docs/workflow/responsibility-handoff-intake-template.md`
- envelope 的 `status` 继续沿用赛博公司统一状态；更细粒度的交接进度使用 `payload.completionTrackingStatus`

## 2. 适用场景

以下情况必须使用本规范：

1. 新固定员工岗位启用前，需要确认交接边界、前置条件和验收 owner。
2. 已有岗位之间发生 owner 迁移，例如产品、技术、秘书处或培训职责从临时 owner 转给固定 owner。
3. 某项持续性职责需要从单人代管切换到正式岗位承担。
4. 某项岗位启用会影响 workflow、registry、support payload、meeting discipline 或 host binding 边界。
5. 现有员工职责、协作关系、source kit 五件套、binding profile、support object、live discovery 或 host object manifest 需要随岗位变动做增量更新。

以下情况通常不单独启用本规范：

- 单次临时协作，不改变长期 owner。
- 纯会议动作项跟踪，但未形成岗位边界调整。
- 仅是文案修订，不涉及职责迁移、验收 owner 或完成度监督。
- 运行态 employee workspace 消费记录更新，且不改变源侧五件套、binding 或长期职责边界。

## 3. 当前治理边界

- ChiefHumanResourcesOfficer 是交接治理设计 owner 与执行验收 owner。
- CEOChiefOfStaff 负责公司级协调、催办、升级与收口，不再作为交接治理长期执行代管 owner。
- ChiefProductOfficer、ChiefTechnologyOfficer 和其他固定岗位只负责其专业结论，不自动承担交接治理闭环 owner。
- 若交接事项触及中央战略、模块边界变化或正式宿主切换，必须升级到 BusinessStrategy 或 CEO 裁决。
- 不把源侧岗位定义、support object、binding profile 或 central agent stub 写成已完成 live handoff。
- 当前调试阶段允许岗位职责和公司流程快速迭代；成熟期同类变更必须补充对应 owner 的验收或签字确认。

## 4. 标准 handoff checklist

每次岗位 / 职责交接至少检查以下项目：

1. 交接对象：明确交接的是岗位、职责、工作流 owner，还是单个执行面资产。
2. 前任 owner：明确当前代管或原 owner 是谁。
3. 新 owner：明确接手岗位或接手人是谁；若尚未独立上岗，必须写明代管 owner。
4. 生效边界：明确只在 source-side 生效、support 生效，还是 live 入口已生效。
5. 真源定位：列出需要回链的 workflow、registry、product、engineering 或 .github 源文件。
6. 支撑资产：列出是否涉及 binding profile、host object manifest、support payload、schedule、wiki 或 audit 对象。
7. 运行风险：说明交接过程中最可能出现的断点、owner 重叠或未完成项。
8. 验收条件：定义什么情况下可以视为 handoff 完成。
9. 升级条件：定义哪些风险、冲突或资料缺口需要升级给 CEO、BusinessStrategy 或对应负责人。
10. 发布链路：确认 source kit、support object、binding profile、live discovery、manifest 和治理回填是否需要同步更新。

缺少以上任一关键项时，默认状态应标记为 `待确认` 或 `blocked`，而不是直接标记完成。

## 5. Completion Tracking 状态机

当前统一使用以下状态：

- `drafted`：已提出交接事项，但 owner、范围或目标文件尚未收口。
- `ready-for-execution`：交接边界、前任 owner、新 owner、目标真源和验收条件已明确。
- `in-progress`：交接动作已开始执行，仍有未完成项。
- `blocked`：存在关键依赖缺口、边界冲突、未上岗岗位或缺少 CEO / 战略裁决。
- `ready-for-acceptance`：交接动作已执行完毕，等待验收 owner 确认。
- `accepted`：验收 owner 已确认闭环。
- `frozen`：事项被明确冻结，当前阶段不继续推进。

任何状态变化都应同步记录：

1. 当前 owner
2. 下一动作
3. 阻塞项或验收依据
4. 回填目标文档

## 6. 最小交接对象模板

每个交接事项最少应包含：

- handoffId
- subject
- previousOwner
- incomingOwner
- actingOwner
- scope
- sourceOfTruthFiles
- supportAssets
- status
- acceptanceCriteria
- nextAction
- blocker
- escalations
- notes

若后续新增岗位仅完成 source-side 准备但 live 未启用，`scope` 必须明确写成 `source-side-not-live` 或等价表述；当前 CHO 自身已是 `current-copilot-host-live`。

## 7. 当前阶段执行规则

1. CHO 当前已具备 source-side 岗位定义、治理文档、support object、binding profile 与 live discovery 入口。
2. 所有 handoff checklist 与 completion tracking 由 ChiefHumanResourcesOfficer 主责执行和验收。
3. CEOChiefOfStaff 可继续发起、协调、催办和升级交接事项，但不替代 CHO 做交接闭环 owner。
4. 若交接事项同时涉及 product 和 engineering，CPO / CTO 必须分别给出专业侧确认，但不替代 CHO 做交接闭环验收。

## 8. 验收口径

一个交接事项只有同时满足以下条件，才可标记为 `accepted`：

1. 交接边界和 owner 没有冲突。
2. 目标真源已按需要回填。
3. 必要的 support asset / source asset 已更新或明确不适用。
4. 下一阶段执行 owner 已确认接手。
5. 未完成风险已记录，且不影响当前阶段继续运行。
6. 若事项会进入当前 live，source kit、support object、binding profile、live discovery、host object manifest 与 governance 回填已完成或明确不适用。
7. 若已进入成熟期授权矩阵，相关 owner 已签字确认；当前调试期至少要有 CEO / 当前操作者的明确输入、CHO 验收口径和必要的专业 owner 确认。

若其中任一条件不成立，应继续保留在 `in-progress`、`blocked` 或 `ready-for-acceptance`。

## 9. 当前约束

- 不把本规范写成正式公司制度定稿。
- 不把当前 Copilot-host live 上岗写成 TriMC 正式宿主切换或完整授权矩阵完成。
- 不跳过验收条件或升级条件去追求表面完成。
- 不把跨模块战略边界争议在本文件内自行裁决。
- 不把“已更新源侧五件套”单独写成“已完成 live 变更”；live 变更必须同时核对 support object、binding profile、manifest、live discovery 和治理回填。
