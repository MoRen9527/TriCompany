# IPD 第一次真实审批回填 Merge 候选矩阵

版本：V0.1
日期：2026-06-15
状态：第一次真实审批回填的候选预案

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-first-real-approval-merge-candidate-matrix.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待首次真实审批回填完成后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-15

## 1. 文档定位

本文不是审批稿，也不是主流程真源。

它只做一件事：把第一次真实审批回填中最可能遇到的 `APPROVE / FREEZE` 项，预先映射到 `merge hook -> 落点 -> 是否需要 runtime 双写 -> 首个验证动作`，供 `CEOChiefOfStaff` 在真实岗位结论写入后直接照表执行。

本文所有内容都以真实审批结果为前提。若 `CPO / CTO` 最终没有给出 `APPROVE + mergeReady = yes`，则本矩阵只保留为预案，不触发主流程真源或 runtime source 改写。

## 2. 使用方式

1. 先读取 [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)。
2. 再读取 `CPO / CTO` 两份审批稿中的真实 `最终决定` 与 `mergeReady`。
3. 只对真实 `APPROVE + mergeReady = yes` 的项目执行本文中的 merge 路径。
4. 在 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 中同步记录本轮真实状态，并按本文各表给出的段落提示回写；[ipd-first-real-approval-backfill-record-template.md](ipd-first-real-approval-backfill-record-template.md) 继续只保留为模板真源。
5. 对 `FREEZE / REVISE` 项，按本文列出的冻结回流落点执行，不回写主流程真源。

## 3. CPO 通过项候选矩阵

| 审批项 | merge hook | 审批稿来源 | 主流程落点 | runtime 双写 | 真实通过后的首个验证动作 | 回写到 backfill-001 哪一段 |
| --- | --- | --- | --- | --- | --- | --- |
| Discovery 五件套为最小通过条件 | `CPO-Discovery-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包` | 否 | 主流程 Markdown 诊断通过 | `4.2`；若已完成主流程回写，再补 `6.1` |
| 没有 `DiscoveryReferenceFunctionalBrief` 不得进 Intelligence | `CPO-Discovery-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包` | 否 | 主流程 Markdown 诊断通过 | `4.2`；若已完成主流程回写，再补 `6.1` |
| Intelligence 四件套为最小通过条件 | `CPO-Intelligence-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD` | 否 | 主流程 Markdown 诊断通过 | `4.2`；若已完成主流程回写，再补 `6.1` |
| PRD 范围只能来自 `IntelligenceCapabilityExtractionMatrix` 的纳入项 | `CPO-Intelligence-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD` | 否 | 主流程 Markdown 诊断通过 | `4.2`；若已完成主流程回写，再补 `6.1` |
| QA = 统一评分 + candidate delivery 对象 + readiness 判断 | `CPO-QA-Delivery-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线` 阶段表与 [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `6. 关键门禁` | 否 | 主流程 Markdown 诊断通过 | `4.2`；若已完成主流程回写，再补 `6.1` |
| Delivery 必须产出 final manifest / report | `CPO-QA-Delivery-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线` 阶段表与 `Delivery` 边界说明 | 否 | 主流程 Markdown 诊断通过 | `4.2`；若已完成主流程回写，再补 `6.1` |
| Delivery 不等于生产级上线完成 | `CPO-QA-Delivery-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `Delivery` 边界说明与 `7. 当前阶段边界` | 否 | 主流程 Markdown 诊断通过 | `4.2`；若已完成主流程回写，再补 `6.1` |

## 4. CPO 冻结项候选矩阵

| 审批项 | merge hook | 审批稿来源 | 冻结回流落点 | 后续承接 | 回写到 backfill-001 哪一段 |
| --- | --- | --- | --- | --- | --- |
| QA 具体分值阈值 | `CPO-QA-Delivery-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 的 `9. 供联审直接勾选的清单` | 下一轮 `WORKFLOW-002` backlog seeds | `4.2` 先记录真实结论；冻结回流完成后补 `6.3` |
| 一票否决维度列表 | `CPO-QA-Delivery-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 的 `9. 供联审直接勾选的清单` | 下一轮 `WORKFLOW-002` backlog seeds | `4.2` 先记录真实结论；冻结回流完成后补 `6.3` |
| candidate delivery 升 final delivery 的门槛 | `CPO-QA-Delivery-Contract` | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 的 `9. 供联审直接勾选的清单` | 下一轮 `WORKFLOW-002` backlog seeds | `4.2` 先记录真实结论；冻结回流完成后补 `6.3` |

## 5. CTO 通过项候选矩阵

| 审批项 | merge hook | 审批稿来源 | 主流程落点 | runtime / validation 双写 | 真实通过后的首个验证动作 | 回写到 backfill-001 哪一段 |
| --- | --- | --- | --- | --- | --- | --- |
| `DesignReviewScorecard / QaScorecard / AssuranceScorecard` 命名保留 | `CTO-Stage-Template-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线` 阶段表 | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | 相关 Python 文件诊断通过 | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| `templateFields / standardFlow / handoffChecklist` 进入稳定 stage contract | `CTO-Stage-Template-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线` 阶段表 | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | 相关 Python 文件诊断通过 | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| 真实 evidence 底线 | `CTO-Evidence-Policy-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `6. 关键门禁` 与后段阶段说明 | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | 相关 Python 文件诊断通过 | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| `Coding` 后不得 docs 假完成 | `CTO-Evidence-Policy-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `6. 关键门禁` 与 `7. 当前阶段边界` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | 相关 Python 文件诊断通过 | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| `packageHash / signatureChain / release` 四组对象 | `CTO-Signing-Release-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.0.2 Web3 签核与 autopilot` 与 `6. 关键门禁` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | 相关 Python 文件诊断通过 | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| `manual-ceo-signoff` 保留 | `CTO-Signing-Release-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.0.2 Web3 签核与 autopilot` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | 相关 Python 文件诊断通过 | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| simulated wallet 的签名原则 | `CTO-Signing-Release-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.0.2 Web3 签核与 autopilot` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | 相关 Python 文件诊断通过 | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| `Deployment / Assurance` 分层 | `CTO-Evidence-Policy-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线` 阶段表 | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | 相关 Python 文件诊断通过 | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |

## 6. CTO 冻结项候选矩阵

| 审批项 | merge hook | 审批稿来源 | 冻结回流落点 | 后续承接 | 回写到 backfill-001 哪一段 |
| --- | --- | --- | --- | --- | --- |
| default seed / mnemonic 细节 | `CTO-Signing-Release-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 的 `9. 供联审直接勾选的清单` | proving-ground 层继续冻结 + 下一轮 `WORKFLOW-002` backlog seeds | `5.2` 先记录真实结论；冻结回流完成后补 `6.3` |
| local-only deployment strategy 细节 | `CTO-Evidence-Policy-Contract` | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 的 `9. 供联审直接勾选的清单` | proving-ground 层继续冻结 + 下一轮 `WORKFLOW-002` backlog seeds | `5.2` 先记录真实结论；冻结回流完成后补 `6.3` |

## 7. 建议执行顺序

`CEOChiefOfStaff` 在第一次真实审批回填时，按以下顺序消费本矩阵：

1. 先处理 `CPO-Discovery-Contract` 与 `CPO-Intelligence-Contract` 的通过项。
2. 再处理 `CPO-QA-Delivery-Contract` 中真实通过、且不涉及阈值冻结的项目。
3. 然后处理 `CTO-Stage-Template-Contract`、`CTO-Evidence-Policy-Contract`、`CTO-Signing-Release-Contract` 的通过项。
4. 最后统一把全部 `FREEZE / REVISE` 项回写到长期清单、`WORKFLOW-002` backlog seeds 和 operating record。

这样做的目的，是先让主流程文档层完成产品 / 验收 contract 收口，再处理需要 runtime 双写的技术 contract，减少同轮 merge 的歧义。

## 8. Guardrails

1. 本矩阵不替代真实审批稿。
2. 本矩阵不允许把“当前建议 = APPROVE”自动视为真实通过。
3. 任何技术项只要需要 runtime 双写，就不能只改 [integrated-product-development-flow.md](integrated-product-development-flow.md)。
4. 本矩阵服务于赛博公司当前研发阶段与本地 Copilot-host 正式接管阶段，不自动外推为 `TriMC` 正式宿主 contract。

## 9. Evidence Surface

- [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)
- [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)
- [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
- [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
- [integrated-product-development-flow.md](integrated-product-development-flow.md)
- [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
- [agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md](agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md)
