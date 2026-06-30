# IPD-20260610 Discovery 非破坏性 Replay 验收清单

版本：V0.1
日期：2026-06-16
状态：CPO / CTO / CEOChiefOfStaff 直接执行用 checklist

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/agile-improvement/IPD-20260612-WORKFLOW-002/08-discovery-replay-validation-checklist.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待首轮 replay 验证完成后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-16

## 1. 文档定位

本文只解决一个问题：在 `SP-202A` 由 `ChiefTechnologyOfficer` 完成后，`IPD-20260610-PLATFORM-001` 应如何通过一轮非破坏性 `Discovery replay`，验证 seeded competitor carry-forward guard 已经达到要求。

本文不是流程代码实现说明，也不是新的 Discovery 真源。它只定义 replay 前置核查、角色边界、执行顺序、通过条件、阻断条件和最小验证动作。

## 2. 核心原则

### 2.1 允许扩展，不允许静默丢失

- `CEO` 在 clarification sheet 中填的 seeded competitors 不是 Discovery 唯一允许的竞品集合。
- 但每一个 seeded competitor 都必须在后续 `catalog / brief / landscape` 中被覆盖。
- 如果任何 seeded competitor 从 replay 结果中静默消失，则本轮 Discovery 必须标记为 `revision-required` 或被阻断。

### 2.2 先保留 baseline，再做 replay

- 不允许先清空当前 Discovery evidence 再开始验证。
- 当前 baseline 至少包括：
  - `reference-source-catalog.json`
  - `discovery-reference-functional-brief.md`
  - `discovery-competitor-landscape.md`
  - `discovery-common-capability-matrix.md`
  - `discovery-highlight-opportunity-memo.md`
- 如果工具链只支持单活产物，则必须先归档 baseline，再生成 replay 版本。

### 2.3 先 CTO 自测，再 CPO replay

- `ChiefTechnologyOfficer` 先完成 guard 实施和 focused self-test。
- `CEOChiefOfStaff` 只负责 replay-ready 核查和最终验收，不替 `CTO` 实现代码，也不替 `CPO` 给产品结论。
- `ChiefProductOfficer` 只在 replay-ready 之后重走 Discovery，不绕过 guard 直接手工修文档凑结果。

## 3. 前置核查

开始 replay 前，必须先确认：

1. `SP-202A` 已由 `ChiefTechnologyOfficer` 标记为实现完成。
2. `CTO` 已完成至少一轮 focused self-test，能证明 seeded competitor carry-forward guard 已接入 Discovery 自动化或 validation path。
3. 当前 20260610 baseline evidence 仍可读，或已具备明确归档副本。
4. 当前 intake briefing 与 case 中的 `competitorReference` 仍为：`LiteLLM、sub2api、OpenRouter、OpenAI API Platform`。
5. replay 继续沿用当前 intake，不在本轮临时改写 seeded competitors。
6. `CEOChiefOfStaff` 已确认 replay 目标是验证 carry-forward guard，而不是推进 Intelligence。

## 4. 角色边界

### 4.1 `ChiefTechnologyOfficer`

- 实现 seeded competitor carry-forward guard。
- 提供 focused self-test 结果。
- 如 replay 失败，负责判断是实现缺口还是校验条件缺口。

### 4.2 `ChiefProductOfficer`

- 基于当前 intake 重走 Discovery。
- 输出新的 Discovery package，不手工绕过 guard 修补 seeded competitor 覆盖。
- 对 replay 结果给出产品侧 `可继续 / revision-required` 判断。

### 4.3 `CEOChiefOfStaff`

- 检查 baseline 是否保留或已归档。
- 检查 replay 输出是否覆盖全部 seeded competitors。
- 记录通过 / 失败结论，并决定是否允许进入下一步，而不是代替 `CPO / CTO` 修改实现。

## 5. 固定执行顺序

1. `CTO` 完成 guard 实施。
2. `CTO` 运行 focused self-test，并保留结果摘要。
3. `CEOChiefOfStaff` 核查 baseline evidence 仍在，或已先归档。
4. `CEOChiefOfStaff` 核查当前 intake / case 的 seeded competitors 未被临时改写。
5. `CPO` 基于同一 intake 重走 Discovery，生成 replay 结果。
6. `CEOChiefOfStaff` 逐项检查 replay 结果中的 `catalog / brief / landscape` 是否覆盖全部 seeded competitors。
7. 如 seeded competitors 全覆盖，且允许扩展更多竞品，则记录 `pass`。
8. 如有任一 seeded competitor 缺失，则记录 `revision-required` 或阻断，并回流 `WORKFLOW-002`。

## 6. 逐项检查表

### 6.1 baseline 保留检查

执行前必须确认以下文件仍可读取，或已有 archive copy：

1. `TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/reference-source-catalog.json`
2. `TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-reference-functional-brief.md`
3. `TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-competitor-landscape.md`
4. `TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-common-capability-matrix.md`
5. `TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-highlight-opportunity-memo.md`

### 6.2 seeded competitor 覆盖检查

以下四个 seeded competitors 必须在 replay 结果中可定位：

1. `LiteLLM`
2. `sub2api`
3. `OpenRouter`
4. `OpenAI API Platform`

最小覆盖要求：

1. `reference-source-catalog.json` 中全部存在。
2. `discovery-reference-functional-brief.md` 中全部被引用或明确纳入问题拆解。
3. `discovery-competitor-landscape.md` 中全部有对应条目。

补充说明：

- `discovery-common-capability-matrix.md` 与 `discovery-highlight-opportunity-memo.md` 可以不要求对四个 seeded competitors 逐个逐文件点名，但不得与前三项结论矛盾。
- 如果 replay 新增其他竞品，只要 seeded competitors 未丢失，即不构成失败。

### 6.3 失败判定

出现以下任一情况，直接判定 replay 失败：

1. 任何 seeded competitor 未出现在 `catalog`。
2. 任何 seeded competitor 未出现在 `brief` 或没有被纳入问题拆解。
3. 任何 seeded competitor 未出现在 `landscape`。
4. replay 前 baseline 被直接删除，且没有 archive copy。
5. replay 结果是通过手工补文档绕过 guard，而不是通过 guard 机制产生。

## 7. 最小验证动作

replay 结束后，最少执行以下验证：

1. replay 后 Discovery 五件套的 Markdown / JSON 诊断。
2. 若 `CTO` guard 实现涉及 runtime / validation source，相关 Python 文件诊断。
3. 对比 seeded competitors 在 baseline 与 replay 结果中的覆盖差异。
4. 记录本轮 replay 的通过 / 失败摘要，并回写到 `WORKFLOW-002` 后续执行资产或 operating record。

补充记录面：

1. `CTO` 的 focused self-test 结果统一记录到 [09-cto-focused-self-test-record-template.md](09-cto-focused-self-test-record-template.md)。
2. Discovery replay 的最终结果统一记录到 [10-discovery-replay-result-record-template.md](10-discovery-replay-result-record-template.md)。
3. 首轮真实填写默认直接使用 [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md) 与 [10-discovery-replay-result-001.md](10-discovery-replay-result-001.md)，不再从模板临时复制结构。
4. 当天实际执行时，岗位最短操作顺序统一参考 [11-discovery-replay-role-script.md](11-discovery-replay-role-script.md)。

## 8. 完成定义

满足以下条件，视为“Discovery competitor carry-forward guard 首轮验证完成”：

1. baseline evidence 已保留或已归档。
2. `CTO` guard 实现和 focused self-test 已完成。
3. `CPO` 已完成一轮基于同一 intake 的 Discovery replay。
4. replay 结果对四个 seeded competitors 全部达到最小覆盖要求。
5. 结果已被 `CEOChiefOfStaff` 记录为 `pass` 或 `revision-required`，而不是口头结论。

## 9. Guardrails

1. 本清单不允许直接清空现有 Discovery evidence 再开始验证。
2. 本清单不允许以“新增了更多竞品”为理由掩盖 seeded competitors 丢失。
3. 本清单不允许 `CEOChiefOfStaff` 代替 `CTO` 改 guard 实现。
4. 本清单不把 replay 通过写成整个 20260610 case 已可直接进入生产级发布。

## 10. Evidence Surface

- [06-validation-handoff-plan.md](06-validation-handoff-plan.md)
- [06-validation-handoff-package.json](06-validation-handoff-package.json)
- [../../integrated-product-development-flow.md](../../integrated-product-development-flow.md)
- [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/intake-brief.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/intake-brief.json)
- [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/case.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/case.json)
- [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/reference-source-catalog.json](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/reference-source-catalog.json)
- [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-reference-functional-brief.md](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-reference-functional-brief.md)
- [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-competitor-landscape.md](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-competitor-landscape.md)
- [09-cto-focused-self-test-record-template.md](09-cto-focused-self-test-record-template.md)
- [10-discovery-replay-result-record-template.md](10-discovery-replay-result-record-template.md)
- [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md)
- [10-discovery-replay-result-001.md](10-discovery-replay-result-001.md)
- [11-discovery-replay-role-script.md](11-discovery-replay-role-script.md)
