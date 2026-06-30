# IPD 第一次真实审批回填 Through-Pass Checklist

版本：V0.1
日期：2026-06-15
状态：短版 operator checklist

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-first-real-approval-through-pass-checklist.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待首次真实审批回填完成后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-15

## 1. 文档定位

本文不是完整 runbook，也不是逐项矩阵。

它只保留第一次真实审批回填中最可能首批通过、且适合 `CEOChiefOfStaff` 直接照单执行的 through-pass 项，目标是把真实审批后的第一轮回写压缩成一页可操作清单。

本文默认前提不变：只有在 `CPO / CTO` 审批稿中被真实标记为 `APPROVE`，且签发区 `mergeReady = yes` 的项目，才允许执行本文动作。

## 2. 使用前提

开始执行本清单前，必须先确认：

1. [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md) 已核查完成。
2. [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md) 已确认 landing zone。
3. [ipd-first-real-approval-backfill-record-template.md](ipd-first-real-approval-backfill-record-template.md) 继续只作为模板真源保留，不作为本轮真实填写面。
4. [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 已创建并作为本轮唯一真实填写面。
5. `CPO / CTO` 审批稿中的真实结论已经写入，不再是 `pending`。

## 3. 首批 through-pass 候选项

### 3.1 `CPO` 首批高概率通过项

以下项目默认最适合进入第一次 through-pass：

1. `Discovery 五件套为最小通过条件`
2. `没有 DiscoveryReferenceFunctionalBrief 不得进 Intelligence`
3. `Intelligence 四件套为最小通过条件`
4. `PRD 范围只能来自 IntelligenceCapabilityExtractionMatrix 的纳入项`
5. `QA = 统一评分 + candidate delivery 对象 + readiness 判断`
6. `Delivery 必须产出 final manifest / report`
7. `Delivery 不等于生产级上线完成`

这些项目的共同特征是：

1. 当前审批稿已给出明确 `APPROVE` 建议。
2. 主流程真源已有明确 merge hook 和 landing zone。
3. 不要求在同轮先解决阈值冻结、seed 冻结或 proving-ground only 细节。

### 3.2 `CTO` 首批高概率通过项

以下项目默认最适合进入第一次 through-pass：

1. `templateFields / standardFlow / handoffChecklist` 进入稳定 stage contract
2. `真实 evidence 底线`
3. `Coding 后不得 docs 假完成`
4. `packageHash / signatureChain / release` 四组对象
5. `manual-ceo-signoff` 保留
6. `simulated wallet 的签名原则`
7. `Deployment / Assurance` 分层

这些项目的共同特征是：

1. 当前审批稿已给出明确 `APPROVE` 建议。
2. 它们代表稳定 contract 原则，而不是样例阈值或凭据细节。
3. 即使需要 runtime / validation 双写，目标面也已经在矩阵中明确。

## 4. 固定执行顺序

第一次 through-pass 固定按以下顺序执行：

1. 先处理 `CPO-Discovery-Contract`。
2. 再处理 `CPO-Intelligence-Contract`。
3. 再处理 `CPO-QA-Delivery-Contract` 中不涉及阈值冻结的通过项。
4. 然后处理 `CTO-Stage-Template-Contract`。
5. 再处理 `CTO-Evidence-Policy-Contract`。
6. 最后处理 `CTO-Signing-Release-Contract` 中不涉及 seed / mnemonic 冻结的通过项。

这样做的目的是先收口产品 / 验收主流程，再收口需要 runtime 双写的技术原则，避免首轮真实回填时同时摊开过多冻结分支。

## 5. 一页式执行单

| 顺序 | 项目 | merge hook | 目标落点 | 双写要求 | 完成后立即记录到哪里 | 回写到 backfill-001 哪一段 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Discovery 五件套为最小通过条件 | `CPO-Discovery-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包` | 否 | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `4.2`；若已完成主流程回写，再补 `6.1` |
| 2 | 没有 `DiscoveryReferenceFunctionalBrief` 不得进 Intelligence | `CPO-Discovery-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包` | 否 | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `4.2`；若已完成主流程回写，再补 `6.1` |
| 3 | Intelligence 四件套为最小通过条件 | `CPO-Intelligence-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD` | 否 | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `4.2`；若已完成主流程回写，再补 `6.1` |
| 4 | PRD 范围只能来自 `IntelligenceCapabilityExtractionMatrix` 的纳入项 | `CPO-Intelligence-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD` | 否 | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `4.2`；若已完成主流程回写，再补 `6.1` |
| 5 | QA = 统一评分 + candidate delivery 对象 + readiness 判断 | `CPO-QA-Delivery-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线` 与 `6. 关键门禁` | 否 | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `4.2`；若已完成主流程回写，再补 `6.1` |
| 6 | Delivery 必须产出 final manifest / report | `CPO-QA-Delivery-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `Delivery` 阶段说明 | 否 | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `4.2`；若已完成主流程回写，再补 `6.1` |
| 7 | Delivery 不等于生产级上线完成 | `CPO-QA-Delivery-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `Delivery` 边界说明与 `7. 当前阶段边界` | 否 | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `4.2`；若已完成主流程回写，再补 `6.1` |
| 8 | `templateFields / standardFlow / handoffChecklist` 进入稳定 stage contract | `CTO-Stage-Template-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| 9 | 真实 evidence 底线 | `CTO-Evidence-Policy-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `6. 关键门禁` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| 10 | `Coding` 后不得 docs 假完成 | `CTO-Evidence-Policy-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `6. 关键门禁` 与 `7. 当前阶段边界` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| 11 | `packageHash / signatureChain / release` 四组对象 | `CTO-Signing-Release-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.0.2 Web3 签核与 autopilot` 与 `6. 关键门禁` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| 12 | `manual-ceo-signoff` 保留 | `CTO-Signing-Release-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.0.2 Web3 签核与 autopilot` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| 13 | simulated wallet 的签名原则 | `CTO-Signing-Release-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.0.2 Web3 签核与 autopilot` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |
| 14 | `Deployment / Assurance` 分层 | `CTO-Evidence-Policy-Contract` | [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线` | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 与 [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) | `5.2`；若已完成主流程回写，再补 `6.1`；若已双写 runtime/validation，再补 `6.2` |

## 6. 不进入首批 through-pass 的项目

以下项目默认不进入第一次 through-pass，而是继续走冻结回流：

1. `QA 具体分值阈值`
2. `一票否决维度列表`
3. `candidate delivery 升 final delivery 的门槛`
4. `default seed / mnemonic 细节`
5. `local-only deployment strategy 细节`

原因固定为两类：

1. 它们需要额外阈值、边界或样例外推判断。
2. 它们高度依赖 proving-ground 当前实现细节，不适合首轮直接升级为长期 contract。

## 7. 最小验证动作

through-pass 完成后，最少执行以下验证：

1. 主流程真源 Markdown 诊断。
2. 若涉及技术项，runtime Python 诊断。
3. 若涉及技术项，validation Python 诊断。
4. 记录模板更新后的 Markdown 诊断。
5. operating record Markdown / JSON 诊断。

补充说明：through-pass 的真实记录默认写入 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)；[ipd-first-real-approval-backfill-record-template.md](ipd-first-real-approval-backfill-record-template.md) 继续只保留为模板真源。

## 8. Guardrails

1. 本清单只服务第一次真实审批后的首批 through-pass，不覆盖全部审批项。
2. 本清单不允许绕过真实审批稿直接回写主流程或 runtime。
3. 本清单不允许把冻结项偷偷并入首批 through-pass。
4. 本清单不把当前本地 Copilot-host 正式接管阶段写成 `TriMC` 正式宿主收口。

## 9. Evidence Surface

- [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)
- [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
- [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)
- [ipd-first-real-approval-backfill-record-template.md](ipd-first-real-approval-backfill-record-template.md)
- [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
- [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
