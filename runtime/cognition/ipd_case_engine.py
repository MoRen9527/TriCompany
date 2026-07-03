from __future__ import annotations

import hashlib
import importlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_ipd_case_root, chief_of_staff_ipd_cases_root, source_root
from runtime.cognition.web3_signing import sign_web3_package_hash, verify_web3_signature


IPD_CASE_SCHEMA_VERSION = "1.0"
INTAKE_REQUIRED_APPROVERS = ("CEO", "CEOChiefOfStaff")
STAGE_FINAL_APPROVERS = ("CEO", "CEOChiefOfStaff")
_CASE_CATEGORY_PROCESS_IMPROVEMENT = "process-improvement"
_CASE_CATEGORY_PROJECT_DELIVERY = "project-delivery"
_PROCESS_IMPROVEMENT_REFERENCE_THEMES = {"WORKFLOW", "TRAINING", "VALIDATION"}

_ROLLBACK_CEO_DEMAND_ALIASES = {
    "ceo-demand",
    "ceo-demand-start",
    "ceo-request",
    "intake",
    "intake-start",
}
_ROLLBACK_TASK_DISPATCH_ALIASES = {
    "task-dispatch",
    "dispatch",
    "owner-dispatch",
    "discovery-dispatch",
}

_STAGE_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "stageKey": "discovery",
        "phaseKey": "DISCOVERY",
        "title": "Discovery / 总助分派后的产品研究",
        "businessOwner": "ChiefProductOfficer",
        "actingOwner": "ChiefProductOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefProductOfficer",
        "participantRoles": ("CEOChiefOfStaff", "CEO", "ChiefMarketingOfficer", "ChiefTechnologyOfficer"),
        "schemaHint": {
            "objectType": "IPD_DISCOVERY_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "总助拆解后的研发任务说明",
            "intake briefing",
            "上游业务背景与当前阶段边界",
        ),
        "outputRequirements": (
            "沉淀任务意图、目标边界、成功信号和 Discovery 真源草稿。",
            "把符合任务的产品、官方手册和官方说明下载到 TriMetaverse/reference/discovery/<case-id>/，形成 reference source catalog。",
            "自动生成并持续补齐 DiscoveryReferenceFunctionalBrief、DiscoveryCompetitorLandscape、DiscoveryCommonCapabilityMatrix、DiscoveryHighlightOpportunityMemo 等 markdown package 文档。",
            "在 markdown package 中完成竞品/手册搜索、功能共性抽取、亮点功能发掘和待验证问题整理，供 Intelligence 搜索开源代码。",
            "补齐最小 raw evidence pack、参考链接和后续需要验证的问题。",
        ),
        "standardFlow": {
            "referenceRoot": "TriMetaverse/reference/discovery/{caseId}",
            "catalogPath": "TriMetaverse/reference/discovery/{caseId}/reference-source-catalog.json",
            "summaryDocument": {
                "name": "DiscoveryReferenceFunctionalBrief",
                "path": "TriMetaverse/reference/discovery/{caseId}/discovery-reference-functional-brief.md",
                "purpose": "沉淀产品 / 官方手册研究后的典型功能、输入输出、边界、不做项和待验证问题，作为 Intelligence 搜索开源代码与 capability mapping 的直接输入。",
            },
            "packageDocuments": (
                {
                    "name": "DiscoveryCompetitorLandscape",
                    "path": "TriMetaverse/reference/discovery/{caseId}/discovery-competitor-landscape.md",
                    "purpose": "记录竞品、官方入口、手册来源、核心功能和差异点，作为 Discovery package 的主文档之一。",
                },
                {
                    "name": "DiscoveryCommonCapabilityMatrix",
                    "path": "TriMetaverse/reference/discovery/{caseId}/discovery-common-capability-matrix.md",
                    "purpose": "抽取竞品共性功能、输入输出和边界，避免 Intelligence 阶段直接从零开始搜代码。",
                },
                {
                    "name": "DiscoveryHighlightOpportunityMemo",
                    "path": "TriMetaverse/reference/discovery/{caseId}/discovery-highlight-opportunity-memo.md",
                    "purpose": "沉淀亮点功能、差异化机会和后续需要重点验证的创新点。",
                },
            ),
            "requiredActions": (
                "按总助拆解的研发任务，全网搜索符合情况的产品和其官方手册，并把原始材料落到 reference/discovery/<case-id>/。",
                "优先保留官网、官方 README、官方 docs、API 手册、产品功能页、定价页等一手资料。",
                "形成可机读的 reference-source-catalog.json，记录来源、官方性、下载位置和使用说明。",
                "自动生成并持续补齐 DiscoveryReferenceFunctionalBrief、DiscoveryCompetitorLandscape、DiscoveryCommonCapabilityMatrix、DiscoveryHighlightOpportunityMemo。",
                "在 markdown package 中完成竞品/手册搜索、功能共性抽取、亮点功能发掘和后续 Intelligence 问题清单。",
            ),
            "handoffToIntelligence": (
                "Intelligence 必须先消费 DiscoveryReferenceFunctionalBrief，再决定要搜索哪些开源项目和代码路径。",
                "如果 Discovery 只留下链接但没有整理成功能摘要、共性功能矩阵和亮点功能 memo，不允许直接跳到正式 PRD。",
            ),
        },
        "submissionTemplate": {
            "details": (
                "<task-boundary-and-success-signals>",
                "<downloaded-product-and-official-manual-catalog>",
                "<discovery-reference-functional-brief-summary>",
                "<common-capability-and-highlight-feature-summary>",
                "<open-questions-for-intelligence>",
            ),
            "evidence": (
                "TriMetaverse/reference/discovery/{caseId}/reference-source-catalog.json",
                "TriMetaverse/reference/discovery/{caseId}/discovery-reference-functional-brief.md",
                "TriMetaverse/reference/discovery/{caseId}/discovery-competitor-landscape.md",
                "TriMetaverse/reference/discovery/{caseId}/discovery-common-capability-matrix.md",
                "TriMetaverse/reference/discovery/{caseId}/discovery-highlight-opportunity-memo.md",
                "<additional-discovery-evidence-path>",
            ),
        },
        "handoffChecklist": (
            "先按总助拆解的研发任务，把产品与官方手册下载到 TriMetaverse/reference/discovery/<case-id>/。",
            "提交前必须完成 reference-source-catalog.json、discovery-reference-functional-brief.md，以及竞品/共性功能/亮点功能三份 markdown package。",
            "DiscoveryReferenceFunctionalBrief 与共性功能/亮点功能文档必须能直接支持 Intelligence 搜索开源代码，不能只留下原始链接。",
        ),
        "superDevReferenceStages": ("research", "baseline"),
    },
    {
        "stageKey": "intelligence",
        "phaseKey": "INTELLIGENCE",
        "title": "Intelligence / 结构化输入",
        "businessOwner": "ChiefProductOfficer",
        "actingOwner": "ChiefProductOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefProductOfficer",
        "participantRoles": (
            "CEOChiefOfStaff",
            "ChiefMarketingOfficer",
            "ChiefOperatingOfficer",
            "ChiefFinancialOfficer",
            "ChiefTechnologyOfficer",
        ),
        "schemaHint": {
            "objectType": "IPD_INTELLIGENCE_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "Discovery package",
            "DiscoveryReferenceFunctionalBrief",
            "市场证据与机会线索",
            "运营约束",
            "预算护栏",
        ),
        "outputRequirements": (
            "根据 DiscoveryReferenceFunctionalBrief，在 TriMetaverse/reference/intelligence/<case-id>/ 下载或登记相关开源代码，并形成 reference source catalog。",
            "由 ChiefTechnologyOfficer 根据上一阶段资料自动生成并持续补齐开源代码地图、CodeGraph 深读记录、架构选型与实现思路 markdown package。",
            "对 reference/intelligence 下的代码建立本地 CodeGraph，并基于结构化阅读形成 IntelligenceCapabilityExtractionMatrix。",
            "把 Discovery 原始材料整理为结构化 Intelligence 输入包。",
            "基于 capability extraction matrix 收口正式 PRD、项目计划、验收标准和进入设计阶段的前门。",
        ),
        "standardFlow": {
            "referenceRoot": "TriMetaverse/reference/intelligence/{caseId}",
            "catalogPath": "TriMetaverse/reference/intelligence/{caseId}/reference-source-catalog.json",
            "analysisDocument": {
                "name": "IntelligenceCapabilityExtractionMatrix",
                "path": "TriMetaverse/reference/intelligence/{caseId}/intelligence-capability-extraction-matrix.md",
                "purpose": "基于开源代码参考提取符合当前需求的功能，明确纳入 / 后置 / 排除项，并为正式 PRD 提供 capability mapping。",
            },
            "packageDocuments": (
                {
                    "name": "IntelligenceOpenSourceLandscape",
                    "path": "TriMetaverse/reference/intelligence/{caseId}/intelligence-opensource-landscape.md",
                    "purpose": "登记相关开源仓库、公开资料、参考价值和后续深读优先级。",
                },
                {
                    "name": "IntelligenceCodegraphAnalysis",
                    "path": "TriMetaverse/reference/intelligence/{caseId}/intelligence-codegraph-analysis.md",
                    "purpose": "记录 CodeGraph 深读重点、核心模块、调用链入口和与需求的对应关系。",
                },
                {
                    "name": "IntelligenceArchitectureOptionMemo",
                    "path": "TriMetaverse/reference/intelligence/{caseId}/intelligence-architecture-option-memo.md",
                    "purpose": "总结共性功能与亮点功能的架构选型、实现思路和首轮取舍建议。",
                },
            ),
            "requiredActions": (
                "根据 DiscoveryReferenceFunctionalBrief 搜索相关开源代码，并把代码快照或锚点记录落到 reference/intelligence/<case-id>/。",
                "对每个主要代码参考建立本地 CodeGraph；若宿主暂未挂载 CodeGraph，也必须先记录锚点、待建索引动作和结构化深读清单。",
                "自动生成并持续补齐 IntelligenceOpenSourceLandscape、IntelligenceCodegraphAnalysis、IntelligenceArchitectureOptionMemo。",
                "先做 capability extraction、架构选型和实现思路总结，再写正式 PRD；不允许跳过代码分析直接把上游项目包装成产品方案。",
            ),
            "prdRule": (
                "正式 PRD 必须基于 IntelligenceCapabilityExtractionMatrix 提取符合当前需求的功能，不得直接照搬上游代码结构、商业假设或合规假设。",
            ),
        },
        "submissionTemplate": {
            "details": (
                "<discovery-brief-derived-platform-scope>",
                "<opensource-reference-selection-and-codegraph-status>",
                "<intelligence-capability-extraction-matrix-summary>",
                "<architecture-options-and-implementation-ideas>",
                "<formal-prd-and-designing-entry>",
            ),
            "evidence": (
                "TriMetaverse/reference/intelligence/{caseId}/reference-source-catalog.json",
                "TriMetaverse/reference/intelligence/{caseId}/intelligence-capability-extraction-matrix.md",
                "TriMetaverse/reference/intelligence/{caseId}/intelligence-opensource-landscape.md",
                "TriMetaverse/reference/intelligence/{caseId}/intelligence-codegraph-analysis.md",
                "TriMetaverse/reference/intelligence/{caseId}/intelligence-architecture-option-memo.md",
                "<formal-prd-path>",
                "<project-plan-path>",
            ),
        },
        "handoffChecklist": (
            "先根据 DiscoveryReferenceFunctionalBrief 下载或登记开源代码到 TriMetaverse/reference/intelligence/<case-id>/。",
            "提交前必须完成 reference-source-catalog.json、CodeGraph 建索引动作、intelligence-capability-extraction-matrix.md，以及开源地图/CodeGraph 深读/架构选型三份 markdown package。",
            "正式 PRD 必须基于 capability extraction matrix，而不是直接照搬上游仓库。",
        ),
        "superDevReferenceStages": ("docs", "docs_confirm", "prd"),
    },
    {
        "stageKey": "designing",
        "phaseKey": "DESIGNING",
        "title": "Designing / 技术设计",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "IPD_DESIGN_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "PRD",
            "项目计划",
            "验收标准",
        ),
        "outputRequirements": (
            "产出技术路线、工程门禁、任务拆解和 branch / phase handoff。",
            "明确 TriDev phase engine 接入要求与版本包约束。",
        ),
        "standardFlow": {
            "packageRoot": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing",
            "packageDocuments": (
                {
                    "name": "DesignArchitectureDecisionRecord",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing-architecture-decision-record.md",
                    "purpose": "沉淀系统上下文、模块边界、接口契约和关键架构取舍，形成可签核的设计主文档。",
                },
                {
                    "name": "DesignTestBaseline",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing-test-baseline.md",
                    "purpose": "固化 verify-integration、QA 和回归所依赖的测试策略、测试金字塔和最小用例基线。",
                },
                {
                    "name": "DesignSecurityAndRedteamMemo",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing-security-and-redteam-memo.md",
                    "purpose": "提前写清 security-by-design、threat model、redteam 入口和高风险边界，不把安全留到后置补丁。",
                },
                {
                    "name": "DesignPhaseHandoffPlan",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing-phase-handoff-plan.md",
                    "purpose": "定义 coding / verify-integration / QA 的 branch、任务拆解、handoff 条件和放行顺序。",
                },
            ),
            "requiredActions": (
                "先把正式 PRD、项目计划、验收标准和 capability extraction matrix 收口成可执行设计输入。",
                "补齐系统上下文、模块边界、接口契约、数据契约、配置 / 迁移策略和最小 phased delivery 计划。",
                "在 Designing 阶段同时生成测试基线、安全设计和 handoff plan，避免 Verify-Integration / QA / Redteam 无前置 contract。",
                "给 Coding 阶段留下明确的 branch / phase handoff、任务拆解、工程门禁和回滚边界。",
            ),
            "handoffToCoding": (
                "Coding 必须消费 Designing 的 architecture decision、test baseline、security memo 和 phase handoff plan。",
                "如果 Designing 只形成泛泛技术方案，没有测试基线、安全前置和 handoff 条件，不允许直接进入 Coding。",
            ),
        },
        "submissionTemplate": {
            "details": (
                "<system-context-and-module-boundaries>",
                "<interface-data-config-and-migration-contracts>",
                "<test-baseline-and-regression-plan>",
                "<security-by-design-and-redteam-assumptions>",
                "<coding-phase-handoff-and-phased-delivery-plan>",
            ),
            "evidence": (
                "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing-architecture-decision-record.md",
                "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing-test-baseline.md",
                "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing-security-and-redteam-memo.md",
                "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/designing-phase-handoff-plan.md",
                "TriCompany/runtime/cognition/proving-ground/{caseId}/design-review-scorecard.json",
                "<additional-designing-evidence-path>",
            ),
        },
        "handoffChecklist": (
            "提交前必须至少补齐 architecture decision、test baseline、security memo 和 phase handoff plan 四类 designing 产物。",
            "Designing 必须把 Verify-Integration、QA 和 Redteam 的前置 contract 先写出来，不能把测试、安全和质量门全部后置。",
            "如未形成 design review scorecard、接口 / 数据契约或 phased delivery 计划，不允许直接进入 Coding。",
        ),
        "templateFields": {
            "designArtifacts": (
                "systemContext",
                "moduleBoundaries",
                "interfaceContracts",
                "dataContracts",
                "configAndMigrationPlan",
                "engineeringGuardrails",
                "branchAndPhaseHandoff",
                "mvpVsPhasedDeliveryPlan",
            ),
            "qualityAndSecurity": (
                "testStrategy",
                "regressionScope",
                "nonFunctionalConstraints",
                "securityByDesignAssumptions",
                "threatModelFocus",
                "redteamEntryConditions",
            ),
        },
        "scorecardSchema": {
            "schemaName": "DesignReviewScorecard",
            "version": "1.0",
            "scoreRange": "0-5",
            "dimensions": (
                {
                    "key": "architecture-clarity",
                    "label": "架构清晰度",
                    "weight": 0.2,
                    "question": "系统上下文、模块边界、接口关系和关键取舍是否足够清晰。",
                },
                {
                    "key": "contract-completeness",
                    "label": "契约完整度",
                    "weight": 0.2,
                    "question": "接口、数据、配置、迁移和 handoff 契约是否可直接支持 Coding。",
                },
                {
                    "key": "testability",
                    "label": "可测试性",
                    "weight": 0.2,
                    "question": "Verify-Integration / QA 所需测试基线、回归范围和执行顺序是否已明确。",
                },
                {
                    "key": "security-by-design",
                    "label": "安全前置设计",
                    "weight": 0.2,
                    "question": "threat model、redteam 入口和高风险假设是否在 Designing 阶段前置。",
                },
                {
                    "key": "delivery-phasing",
                    "label": "分阶段交付可执行性",
                    "weight": 0.2,
                    "question": "MVP、phased delivery、回滚和版本包边界是否可执行。",
                },
            ),
        },
        "superDevReferenceStages": ("architecture", "uiux", "spec"),
    },
    {
        "stageKey": "coding",
        "phaseKey": "CODING",
        "title": "Coding / 开发实现",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_CODING_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "技术方案",
            "开发任务",
            "工程门禁",
        ),
        "outputRequirements": (
            "提交开发产物、实现证据、失败 / 回滚记录和候选发布 bundle。",
            "明确可进入验证阶段的代码、artifact 和执行摘要。",
        ),
        "superDevReferenceStages": ("frontend", "backend"),
    },
    {
        "stageKey": "verify-integration",
        "phaseKey": "VERIFY-INTEGRATION",
        "title": "Verify-Integration / 集成验证",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_VERIFY_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "coding package",
            "测试计划",
        ),
        "outputRequirements": (
            "提交系统级验证结果、缺陷清单和集成测试证据。",
            "明确是否允许进入 redteam。",
        ),
        "superDevReferenceStages": ("quality",),
    },
    {
        "stageKey": "redteam",
        "phaseKey": "REDTEAM",
        "title": "Redteam / 对抗审查",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("CEOChiefOfStaff",),
        "schemaHint": {
            "objectType": "TRIDEV_REDTEAM_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "verify package",
            "攻击面与安全关注点",
        ),
        "outputRequirements": (
            "提交红队 / 安全对抗审查结果和高风险问题清单。",
            "明确是否允许进入 QA。",
        ),
        "superDevReferenceStages": ("quality",),
    },
    {
        "stageKey": "qa",
        "phaseKey": "QA",
        "title": "QA / 质量门禁",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_QA_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "verify package",
            "redteam package",
        ),
        "outputRequirements": (
            "提交统一质量评分、release readiness 结论和待修问题。",
            "形成 candidate delivery manifest / report，并明确是否允许部署。",
        ),
        "standardFlow": {
            "packageRoot": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/qa",
            "packageDocuments": (
                {
                    "name": "QaReleaseReadinessReview",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/qa-release-readiness-review.md",
                    "purpose": "沉淀 QA 阶段对 release readiness 的书面结论、通过项、阻塞项和残余风险。",
                },
                {
                    "name": "QaDefectAndRiskTriage",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/qa-defect-and-risk-triage.md",
                    "purpose": "记录缺陷分级、残余 bug、修复成本和不进入部署的阻塞项。",
                },
                {
                    "name": "QaCandidateDeliveryNarrative",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/qa-candidate-delivery-narrative.md",
                    "purpose": "解释 candidate delivery manifest / report 的形成依据、范围和注意事项。",
                },
            ),
            "requiredActions": (
                "汇总 verify-integration 与 redteam 的结果，形成统一质量判断，而不是把多个阶段结论原样拼接。",
                "按 scorecard 给出质量评分、release readiness、残余 bug、修复成本和部署放行结论。",
                "形成 candidate delivery manifest / report，为 Deployment 提供可执行的候选交付面。",
            ),
            "handoffToDeployment": (
                "Deployment 只能基于 QA 的 candidate delivery manifest / report 和 release readiness 结论继续推进。",
                "如果 QA 没有统一 scorecard、部署阻塞项和 candidate delivery 结论，不允许进入 Deployment。",
            ),
        },
        "submissionTemplate": {
            "details": (
                "<qa-scorecard-summary>",
                "<release-readiness-decision>",
                "<residual-bugs-and-fix-cost>",
                "<security-stability-concurrency-regression-summary>",
                "<candidate-delivery-manifest-and-report-summary>",
            ),
            "evidence": (
                "TriCompany/runtime/cognition/proving-ground/{caseId}/qa-scorecard.json",
                "TriCompany/runtime/cognition/proving-ground/{caseId}/candidate-delivery-manifest.json",
                "TriCompany/runtime/cognition/proving-ground/{caseId}/candidate-delivery-report.json",
                "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/qa-release-readiness-review.md",
                "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/qa-defect-and-risk-triage.md",
                "<additional-qa-evidence-path>",
            ),
        },
        "handoffChecklist": (
            "提交前必须形成 qa-scorecard.json、candidate-delivery-manifest.json 和 candidate-delivery-report.json。",
            "QA 评分至少覆盖设计缺陷、代码质量、架构合理性、测试覆盖率、回归情况、残余 bug 与修复成本、安全、并发性、稳定性和健壮性。",
            "如 release readiness 仍为 blocked 或 conditional，必须明确 Deployment 的阻塞条件与恢复动作。",
        ),
        "templateFields": {
            "qualityOutputs": (
                "qaScorecard",
                "releaseReadinessDecision",
                "defectAndRiskTriage",
                "candidateDeliveryManifest",
                "candidateDeliveryReport",
                "deploymentBlockers",
            ),
        },
        "scorecardSchema": {
            "schemaName": "QaScorecard",
            "version": "1.0",
            "scoreRange": "0-5",
            "dimensions": (
                {"key": "design-defects", "label": "设计缺陷", "weight": 0.1},
                {"key": "code-quality", "label": "代码质量", "weight": 0.1},
                {"key": "architecture-soundness", "label": "架构合理性", "weight": 0.1},
                {"key": "test-coverage", "label": "测试覆盖率", "weight": 0.1},
                {"key": "regression-status", "label": "回归情况", "weight": 0.1},
                {"key": "bug-backlog-cost", "label": "残余 bug 与修复成本", "weight": 0.1},
                {"key": "security-posture", "label": "安全评估", "weight": 0.1},
                {"key": "concurrency", "label": "并发性", "weight": 0.1},
                {"key": "stability", "label": "稳定性", "weight": 0.1},
                {"key": "robustness", "label": "健壮性", "weight": 0.1},
            ),
            "releaseDecisionEnum": ("blocked", "conditional", "ready"),
        },
        "superDevReferenceStages": ("quality", "preview_confirm"),
    },
    {
        "stageKey": "deployment",
        "phaseKey": "DEPLOYMENT",
        "title": "Deployment / 部署交付",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefOperatingOfficer", "ChiefFinancialOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_DEPLOYMENT_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "qa package",
            "release bundle",
            "deployment checklist",
        ),
        "outputRequirements": (
            "提交部署证据、发布说明、上线窗口和 rollout 计划。",
            "明确是否进入上线后 assurance 观察。",
        ),
        "superDevReferenceStages": ("delivery", "rehearsal"),
    },
    {
        "stageKey": "assurance",
        "phaseKey": "ASSURANCE",
        "title": "Assurance / 运行保障",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefOperatingOfficer", "ChiefFinancialOfficer", "CEOChiefOfStaff"),
        "schemaHint": {
            "objectType": "TRIDEV_ASSURANCE_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "deployment package",
            "运行观察指标",
            "恢复动作",
        ),
        "outputRequirements": (
            "提交运行保障结论、恢复验证、成本影响和 assurance evidence。",
            "明确是否达到可交付状态。",
        ),
        "standardFlow": {
            "packageRoot": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/assurance",
            "packageDocuments": (
                {
                    "name": "AssuranceRuntimeObservation",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/assurance-runtime-observation.md",
                    "purpose": "记录上线后观察窗口、关键指标、异常信号和运行面结论。",
                },
                {
                    "name": "AssuranceRecoveryValidationMemo",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/assurance-recovery-validation-memo.md",
                    "purpose": "沉淀回滚演练、恢复验证和失败时的处置动作。",
                },
                {
                    "name": "AssuranceCostAndRiskReview",
                    "path": "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/assurance-cost-and-risk-review.md",
                    "purpose": "复核告警、性能、成本、残余风险和继续观察条件。",
                },
            ),
            "requiredActions": (
                "围绕运行观察、告警、性能、恢复验证和成本复核形成 assurance 结论，不把上线后的稳定性判断省略掉。",
                "明确继续观察、立即交付、条件交付或回滚的判断口径。",
                "给 Delivery 留下最终交付结论依赖的运行保障证据。",
            ),
            "handoffToDelivery": (
                "Delivery 必须消费 Assurance 的 runtime observation、recovery validation 和 cost/risk 结论。",
                "如果 Assurance 没有恢复验证、观察窗口结论或残余风险追踪，不允许写成可正式交付。",
            ),
        },
        "submissionTemplate": {
            "details": (
                "<runtime-observation-window-and-signals>",
                "<recovery-validation-and-rollback-summary>",
                "<performance-alert-and-cost-review>",
                "<residual-risk-and-follow-up-actions>",
                "<delivery-readiness-decision>",
            ),
            "evidence": (
                "TriCompany/runtime/cognition/proving-ground/{caseId}/assurance-scorecard.json",
                "TriCompany/runtime/cognition/proving-ground/{caseId}/runtime-observation-report.json",
                "TriCompany/runtime/cognition/proving-ground/{caseId}/recovery-validation-report.json",
                "TriCompany/runtime/cognition/proving-ground/{caseId}/assurance-evidence.json",
                "TriCompany/docs/workflow/ipd-stage-packages/{caseId}/assurance-runtime-observation.md",
                "<additional-assurance-evidence-path>",
            ),
        },
        "handoffChecklist": (
            "提交前必须形成 assurance-scorecard.json、runtime-observation-report.json、recovery-validation-report.json 和 assurance-evidence.json。",
            "Assurance 必须写清观察窗口、恢复验证、告警 / 性能 / 成本复核和残余风险，不允许只写‘已上线’。",
            "如仍存在高风险残余项或恢复验证未通过，必须明确 Delivery 的冻结条件或条件交付边界。",
        ),
        "templateFields": {
            "assuranceOutputs": (
                "assuranceScorecard",
                "runtimeObservationReport",
                "recoveryValidationReport",
                "alertAndPerformanceReview",
                "costImpactReview",
                "residualRiskRegister",
                "deliveryReadinessDecision",
            ),
        },
        "scorecardSchema": {
            "schemaName": "AssuranceScorecard",
            "version": "1.0",
            "scoreRange": "0-5",
            "dimensions": (
                {"key": "availability", "label": "可用性", "weight": 0.2},
                {"key": "recovery", "label": "恢复验证", "weight": 0.2},
                {"key": "alerting-and-observability", "label": "告警与可观测性", "weight": 0.15},
                {"key": "performance", "label": "性能", "weight": 0.15},
                {"key": "cost-discipline", "label": "成本纪律", "weight": 0.15},
                {"key": "residual-risk", "label": "残余风险", "weight": 0.15},
            ),
            "deliveryDecisionEnum": ("blocked", "conditional", "ready"),
        },
        "superDevReferenceStages": ("delivery", "rehearsal"),
    },
    {
        "stageKey": "delivery",
        "phaseKey": "DELIVERY",
        "title": "Delivery / 最终交付",
        "businessOwner": "ChiefProductOfficer",
        "actingOwner": "ChiefProductOfficer",
        "moduleExecutor": "TriDev",
        "gateOwner": "ChiefProductOfficer",
        "participantRoles": (
            "CEOChiefOfStaff",
            "CEO",
            "ChiefOperatingOfficer",
            "ChiefFinancialOfficer",
            "ChiefProductOfficer",
            "ChiefTechnologyOfficer",
        ),
        "schemaHint": {
            "objectType": "TRIDEV_DELIVERY_PACKAGE",
            "schemaPath": "",
        },
        "inputRequirements": (
            "assurance package",
            "最终交付清单",
            "版本签发材料",
        ),
        "outputRequirements": (
            "形成最终交付结论、final delivery manifest / report、版本化 gate package 和后续行动。",
            "确认 closeout、继续迭代或新一轮 intake。",
        ),
        "superDevReferenceStages": ("delivery",),
    },
)

_PROCESS_IMPROVEMENT_STAGE_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "stageKey": "backlog",
        "phaseKey": "BACKLOG",
        "title": "Backlog / 流程增量整理",
        "businessOwner": "CEOChiefOfStaff",
        "actingOwner": "CEOChiefOfStaff",
        "moduleExecutor": "TriCompany",
        "gateOwner": "CEOChiefOfStaff",
        "participantRoles": ("CEO", "ChiefProductOfficer", "ChiefTechnologyOfficer"),
        "schemaHint": {"objectType": "AGILE_BACKLOG_PACKAGE", "schemaPath": ""},
        "inputRequirements": ("CEO 需求与当前流程痛点", "上一轮未关闭事项", "现有 IPD runtime / doc / test 现状"),
        "outputRequirements": (
            "形成本轮流程优化 backlog、优先级、边界和不做项。",
            "明确本轮只优化流程本身，不直接拿这条 case 充当真实项目交付。",
        ),
        "standardFlow": {
            "referenceRoot": "TriCompany/docs/workflow/agile-improvement/{caseId}",
            "summaryDocument": {
                "name": "AgileBacklogMemo",
                "path": "TriCompany/docs/workflow/agile-improvement/{caseId}/01-backlog-memo.md",
                "purpose": "沉淀流程增量、优先级、验收口径和本轮边界。",
            },
        },
        "submissionTemplate": {
            "details": ("<workflow-gaps-and-why-now>", "<prioritized-backlog-items>", "<out-of-scope-and-guardrails>"),
            "evidence": (
                "TriCompany/docs/workflow/agile-improvement/{caseId}/01-backlog-memo.md",
                "<additional-backlog-evidence-path>",
            ),
        },
        "handoffChecklist": (
            "明确本轮 backlog 只承接流程增量，不承接真实项目交付范围。",
            "把待改 runtime、CLI、tests、docs 边界写清楚。",
        ),
        "superDevReferenceStages": ("backlog",),
    },
    {
        "stageKey": "sprint-planning",
        "phaseKey": "SPRINT-PLANNING",
        "title": "Sprint-Planning / 迭代计划",
        "businessOwner": "CEOChiefOfStaff",
        "actingOwner": "CEOChiefOfStaff",
        "moduleExecutor": "TriCompany",
        "gateOwner": "CEOChiefOfStaff",
        "participantRoles": ("ChiefProductOfficer", "ChiefTechnologyOfficer"),
        "schemaHint": {"objectType": "AGILE_SPRINT_PLAN_PACKAGE", "schemaPath": ""},
        "inputRequirements": ("backlog memo", "本轮资源与时间窗口", "签发顺序与验证要求"),
        "outputRequirements": (
            "形成 sprint goal、任务拆解、负责人与先后顺序。",
            "明确本轮怎么验证流程增量已经落地。",
        ),
        "standardFlow": {
            "referenceRoot": "TriCompany/docs/workflow/agile-improvement/{caseId}",
            "summaryDocument": {
                "name": "SprintPlan",
                "path": "TriCompany/docs/workflow/agile-improvement/{caseId}/02-sprint-plan.md",
                "purpose": "沉淀本轮流程优化的任务拆解、owner 和验证顺序。",
            },
        },
        "submissionTemplate": {
            "details": ("<sprint-goal>", "<task-breakdown-and-order>", "<validation-plan>"),
            "evidence": (
                "TriCompany/docs/workflow/agile-improvement/{caseId}/02-sprint-plan.md",
                "<additional-sprint-planning-evidence-path>",
            ),
        },
        "handoffChecklist": (
            "把 runtime、CLI、tests、docs 的改动顺序写清楚。",
            "确认验证切片先于扩面修改。",
        ),
        "superDevReferenceStages": ("plan",),
    },
    {
        "stageKey": "sprint-execution",
        "phaseKey": "SPRINT-EXECUTION",
        "title": "Sprint-Execution / 实施与验证",
        "businessOwner": "ChiefTechnologyOfficer",
        "actingOwner": "ChiefTechnologyOfficer",
        "moduleExecutor": "TriCompany",
        "gateOwner": "ChiefTechnologyOfficer",
        "participantRoles": ("ChiefProductOfficer", "CEOChiefOfStaff"),
        "schemaHint": {"objectType": "AGILE_EXECUTION_PACKAGE", "schemaPath": ""},
        "inputRequirements": ("sprint plan", "待改代码与测试基线", "签发与验证规则"),
        "outputRequirements": (
            "提交本轮代码、CLI、测试和文档改动。",
            "附上最小可执行验证结果，而不是只交说明文档。",
        ),
        "standardFlow": {
            "referenceRoot": "TriCompany/docs/workflow/agile-improvement/{caseId}",
            "summaryDocument": {
                "name": "SprintExecutionLog",
                "path": "TriCompany/docs/workflow/agile-improvement/{caseId}/03-sprint-execution-log.md",
                "purpose": "记录本轮流程增量实现、验证和遗留问题。",
            },
        },
        "submissionTemplate": {
            "details": ("<implemented-flow-increments>", "<tests-and-validation-slice>", "<known-gaps>"),
            "evidence": (
                "TriCompany/docs/workflow/agile-improvement/{caseId}/03-sprint-execution-log.md",
                "<changed-source-or-test-path>",
            ),
        },
        "handoffChecklist": ("先列清楚已改 runtime/CLI/tests/docs，再列剩余缺口。", "至少附上一条可执行验证。"),
        "superDevReferenceStages": ("implementation",),
    },
    {
        "stageKey": "sprint-review",
        "phaseKey": "SPRINT-REVIEW",
        "title": "Sprint-Review / 阶段评审",
        "businessOwner": "ChiefProductOfficer",
        "actingOwner": "ChiefProductOfficer",
        "moduleExecutor": "TriCompany",
        "gateOwner": "ChiefProductOfficer",
        "participantRoles": ("ChiefTechnologyOfficer", "CEOChiefOfStaff"),
        "schemaHint": {"objectType": "AGILE_REVIEW_PACKAGE", "schemaPath": ""},
        "inputRequirements": ("execution package", "阶段验证结果", "未关闭风险"),
        "outputRequirements": (
            "确认本轮流程增量哪些已经成立、哪些仍待补齐。",
            "形成阶段性通过/冻结/返工结论。",
        ),
        "standardFlow": {
            "referenceRoot": "TriCompany/docs/workflow/agile-improvement/{caseId}",
            "summaryDocument": {
                "name": "SprintReviewMemo",
                "path": "TriCompany/docs/workflow/agile-improvement/{caseId}/04-sprint-review-memo.md",
                "purpose": "记录阶段性评审结论、通过项、冻结项和返工项。",
            },
        },
        "submissionTemplate": {
            "details": ("<validated-increments>", "<blocked-or-rework-items>", "<go-no-go-recommendation>"),
            "evidence": (
                "TriCompany/docs/workflow/agile-improvement/{caseId}/04-sprint-review-memo.md",
                "<review-supporting-evidence-path>",
            ),
        },
        "handoffChecklist": ("明确哪些增量已经足够稳定，可以进入复盘。", "没有通过的项必须明确返工条件。"),
        "superDevReferenceStages": ("review",),
    },
    {
        "stageKey": "retrospective",
        "phaseKey": "RETROSPECTIVE",
        "title": "Retrospective / 复盘固化",
        "businessOwner": "CEOChiefOfStaff",
        "actingOwner": "CEOChiefOfStaff",
        "moduleExecutor": "TriCompany",
        "gateOwner": "CEOChiefOfStaff",
        "participantRoles": ("ChiefProductOfficer", "ChiefTechnologyOfficer"),
        "schemaHint": {"objectType": "AGILE_RETROSPECTIVE_PACKAGE", "schemaPath": ""},
        "inputRequirements": ("sprint review memo", "执行中的问题与例外"),
        "outputRequirements": (
            "固化本轮确认有效的流程规则、命令和护栏。",
            "把未解决问题沉淀为下一轮 backlog。",
        ),
        "standardFlow": {
            "referenceRoot": "TriCompany/docs/workflow/agile-improvement/{caseId}",
            "summaryDocument": {
                "name": "RetrospectiveMemo",
                "path": "TriCompany/docs/workflow/agile-improvement/{caseId}/05-retrospective-memo.md",
                "purpose": "固化本轮有效规则、失败模式和下一轮待办。",
            },
        },
        "submissionTemplate": {
            "details": ("<what-worked>", "<what-did-not-work>", "<next-backlog-seeds>"),
            "evidence": (
                "TriCompany/docs/workflow/agile-improvement/{caseId}/05-retrospective-memo.md",
                "<retrospective-supporting-evidence-path>",
            ),
        },
        "handoffChecklist": (
            "把已确认有效的规则写成可复用口径。",
            "把仍待验证的项转成下一轮 backlog，不要混成已完成。",
        ),
        "superDevReferenceStages": ("retrospective",),
    },
    {
        "stageKey": "validation-handoff",
        "phaseKey": "VALIDATION-HANDOFF",
        "title": "Validation-Handoff / 另开真实 IPD case 验证",
        "businessOwner": "CEOChiefOfStaff",
        "actingOwner": "CEOChiefOfStaff",
        "moduleExecutor": "TriCompany",
        "gateOwner": "CEOChiefOfStaff",
        "participantRoles": ("CEO", "ChiefProductOfficer", "ChiefTechnologyOfficer"),
        "schemaHint": {"objectType": "AGILE_VALIDATION_HANDOFF_PACKAGE", "schemaPath": ""},
        "inputRequirements": ("retrospective memo", "已确认有效的流程规则", "候选真实项目方向"),
        "outputRequirements": (
            "形成阶段性优化完成结论和待验证 checklist。",
            "明确下一步应另开 project-delivery IPD case 做真实跑通验证。",
        ),
        "standardFlow": {
            "referenceRoot": "TriCompany/docs/workflow/agile-improvement/{caseId}",
            "summaryDocument": {
                "name": "ValidationHandoffPlan",
                "path": "TriCompany/docs/workflow/agile-improvement/{caseId}/06-validation-handoff-plan.md",
                "purpose": "记录阶段性固化后的验证清单、建议另开的真实 IPD case 和交接口径。",
            },
        },
        "submissionTemplate": {
            "details": ("<stabilized-rules>", "<recommended-validation-case>", "<handoff-checklist-for-real-ipd-case>"),
            "evidence": (
                "TriCompany/docs/workflow/agile-improvement/{caseId}/06-validation-handoff-plan.md",
                "<handoff-supporting-evidence-path>",
            ),
        },
        "handoffChecklist": (
            "明确这条 case 到这里为止只负责流程固化，不直接承担真实项目交付。",
            "下一步必须另开真实 project-delivery case 验证。",
        ),
        "superDevReferenceStages": ("validation",),
    },
)

_STAGE_TEMPLATE_LOOKUP: dict[str, dict[str, Any]] = {
    template["stageKey"]: template for template in (*_STAGE_TEMPLATES, *_PROCESS_IMPROVEMENT_STAGE_TEMPLATES)
}

_TRIDEV_RUN_MODE = "ipd-autopilot"
_AUTOPILOT_NOTE = "由 IPD autopilot 自动推进。"
_REAL_EXECUTION_STAGE_KEYS = (
    "coding",
    "verify-integration",
    "redteam",
    "qa",
    "deployment",
    "assurance",
    "delivery",
)
_AUTOPILOT_OWNER_ACTION_ROLES = (
    "CEOChiefOfStaff",
    "ChiefProductOfficer",
    "ChiefTechnologyOfficer",
)
_AUTOMATION_STAGE_SUMMARIES = {
    "discovery": "Discovery automation package 已提交",
    "intelligence": "Intelligence automation package 已提交",
}
_DISCOVERY_SOURCE_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "aliases": ("litellm",),
        "sourceId": "litellm-docs",
        "name": "LiteLLM",
        "category": "official-product",
        "official": True,
        "productUrl": "https://docs.litellm.ai/",
        "sourceUrl": "https://docs.litellm.ai/docs/",
        "captureStatus": "link-registered",
        "intendedUse": "研究统一 LLM gateway、OpenAI 兼容代理、provider 抽象与路由/回退能力，作为平台后端能力对标。",
        "focusAreas": ("OpenAI-compatible proxy", "provider abstraction", "routing and fallback", "gateway operations", "model access layer"),
        "commonCapabilities": (
            {"name": "统一代理 / provider 抽象", "inputOutput": "上游 provider 能力 -> 统一访问层", "reason": "适合为首版后端 gateway 与多 provider 适配提供主线参考。"},
            {"name": "OpenAI 兼容代理", "inputOutput": "兼容请求 -> 统一响应", "reason": "适合作为首版兼容层能力基线。"},
            {"name": "路由与回退", "inputOutput": "请求 -> provider fallback", "reason": "帮助平台建立最小可用的稳定性策略。"},
        ),
        "highlightFeatures": (
            {"name": "provider abstraction and fallback", "why": "适合为首版后端 gateway 的统一代理、路由和回退策略提供主线参考。", "risk": "若直接照搬实现，可能忽略我们自己的控制面、审计和模块边界。"},
        ),
        "differences": {"strength": "直接贴近后端统一 gateway 目标。", "limit": "不等于我们的完整产品控制面与业务边界。"},
        "intelligenceQuestions": (
            "LiteLLM 的 proxy / provider abstraction / fallback 能力中，哪些适合作为后端技术主线参考？",
        ),
    },
    {
        "aliases": ("sub2api", "sub 2 api"),
        "sourceId": "sub2api-reference",
        "name": "sub2api",
        "category": "upstream-open-source",
        "official": True,
        "productUrl": "https://github.com/Wei-Shaw/sub2api",
        "sourceUrl": "https://github.com/Wei-Shaw/sub2api/blob/main/README.md",
        "captureStatus": "link-registered",
        "intendedUse": "研究拼车共享、账号与额度分发、统一转接与后台治理能力，并为后续 reference -> vendor -> implementation 吸收链提供锚点。",
        "focusAreas": ("shared account routing", "quota distribution", "admin control surface", "gateway capability mapping", "reference absorption chain"),
        "commonCapabilities": (
            {"name": "共享账号 / 额度分发治理", "inputOutput": "共享资源策略 -> 请求分发 / 后台治理", "reason": "帮助明确哪些共享与分发能力进入首版、哪些因合规边界后置。"},
            {"name": "渠道 / provider 管理", "inputOutput": "后台配置 -> 请求路由", "reason": "后台必须能治理 provider、共享策略与模型。"},
            {"name": "管理后台 / 控制面", "inputOutput": "管理操作 -> 平台配置变更", "reason": "首版需要最小控制面，而不是只做裸转发。"},
        ),
        "highlightFeatures": (
            {"name": "shared-account governance and quota distribution", "why": "有助于定义共享/分发/后台治理能力是否进入首版，以及吸收链如何落位。", "risk": "合规、TOS 与商业边界风险必须单独评估，不能直接平移。"},
        ),
        "differences": {"strength": "对共享/分发/后台治理很有参考价值。", "limit": "必须单独审视合规、TOS 与吸收链边界。"},
        "intelligenceQuestions": (
            "sub2api 的共享账号、额度分发、后台治理与吸收链约束中，哪些进入首版 PRD，哪些必须显式后置或因合规边界排除？",
        ),
    },
    {
        "aliases": ("openai api platform", "openai", "openai platform"),
        "sourceId": "openai-api-platform-docs",
        "name": "OpenAI API Platform",
        "category": "official-product",
        "official": True,
        "productUrl": "https://platform.openai.com/",
        "sourceUrl": "https://platform.openai.com/docs/overview",
        "captureStatus": "link-registered",
        "intendedUse": "研究 first-party 模型 API 平台的文档结构、能力边界和开发者工作流。",
        "focusAreas": ("API surface", "model catalog", "authentication and keys", "usage and billing", "developer docs IA"),
        "commonCapabilities": (
            {"name": "统一模型 API 入口", "inputOutput": "统一请求入口 -> 模型响应", "reason": "降低上层接入成本。"},
            {"name": "模型目录与能力说明", "inputOutput": "模型元数据 -> 能力选择", "reason": "帮助产品和研发快速判断模型适配范围。"},
            {"name": "认证与密钥管理", "inputOutput": "密钥 / 权限 -> API 访问", "reason": "平台必须有明确的认证治理边界。"},
        ),
        "highlightFeatures": (
            {"name": "first-party docs IA", "why": "适合拿来做标准开发者体验基线。", "risk": "官方平台视角不覆盖多上游聚合控制面。"},
        ),
        "differences": {"strength": "官方文档和接口说明最完整。", "limit": "不直接回答自托管聚合与多渠道控制面问题。"},
        "intelligenceQuestions": (
            "OpenAI 风格接口的最小兼容面应该如何抽象？",
            "认证、模型目录和计量应拆成几个子域？",
        ),
    },
    {
        "aliases": ("openrouter",),
        "sourceId": "openrouter-docs",
        "name": "OpenRouter",
        "category": "official-product",
        "official": True,
        "productUrl": "https://openrouter.ai/",
        "sourceUrl": "https://openrouter.ai/docs/quickstart",
        "captureStatus": "link-registered",
        "intendedUse": "研究多上游模型聚合路由、统一接口、模型选择与价格透明层。",
        "focusAreas": ("provider aggregation", "OpenAI-compatible API", "routing and model selection", "pricing visibility", "developer onboarding"),
        "commonCapabilities": (
            {"name": "多 provider 聚合路由", "inputOutput": "请求 -> provider / model 选择", "reason": "统一平台需要支持多上游。"},
            {"name": "价格与可用性透明层", "inputOutput": "模型信息 -> 价格 / 能力展示", "reason": "帮助使用者做成本与模型选择。"},
            {"name": "OpenAI 兼容接口", "inputOutput": "兼容请求 -> 统一响应", "reason": "减少上层适配负担。"},
        ),
        "highlightFeatures": (
            {"name": "routing transparency", "why": "对统一模型平台的成本 / 路由可视化很有参考价值。", "risk": "更偏聚合转发层，不等于完整控制面。"},
        ),
        "differences": {"strength": "天然贴近多模型聚合平台目标。", "limit": "不直接代表自建后台治理能力。"},
        "intelligenceQuestions": (
            "路由策略应该按模型、价格、可用性还是租户策略组合？",
        ),
    },
    {
        "aliases": ("one api", "oneapi"),
        "sourceId": "one-api-upstream-readme",
        "name": "One API",
        "category": "upstream-open-source",
        "official": True,
        "productUrl": "https://github.com/songquanpeng/one-api",
        "sourceUrl": "https://github.com/songquanpeng/one-api/blob/master/README.md",
        "captureStatus": "link-registered",
        "intendedUse": "研究自托管统一模型网关、渠道管理和兼容层能力，作为自建控制面的对标输入。",
        "focusAreas": ("self-hosted gateway", "channel/provider management", "OpenAI-compatible API", "quota and key management", "admin console"),
        "commonCapabilities": (
            {"name": "自托管统一网关", "inputOutput": "多上游接入 -> 对外统一 API", "reason": "适合评估自建控制面路线。"},
            {"name": "渠道 / provider 管理", "inputOutput": "后台配置 -> 请求路由", "reason": "平台后台必须能治理渠道和模型。"},
            {"name": "后台控制台", "inputOutput": "管理员操作 -> 平台配置变更", "reason": "控制面是平台 MVP 的关键部分。"},
        ),
        "highlightFeatures": (
            {"name": "self-hosted admin console", "why": "适合为 Intelligence 阶段提供控制面实现对照。", "risk": "开源实现不等于正式产品边界。"},
        ),
        "differences": {"strength": "更接近自建统一网关与后台控制面。", "limit": "需要进一步验证其治理边界与部署复杂度。"},
        "intelligenceQuestions": (
            "渠道管理、配额和控制台需要怎样拆分模块？",
        ),
    },
    {
        "aliases": ("cursor",),
        "sourceId": "cursor-docs",
        "name": "Cursor",
        "category": "official-product",
        "official": True,
        "productUrl": "https://cursor.com/",
        "sourceUrl": "https://docs.cursor.com/",
        "captureStatus": "link-registered",
        "intendedUse": "研究 AI coding IDE、代码库上下文和 agent-like 编辑体验。",
        "focusAreas": ("codebase context", "editing workflow", "agent mode", "developer UX"),
        "commonCapabilities": (
            {"name": "代码库上下文检索", "inputOutput": "代码库 -> 建议 / 编辑", "reason": "适合作为研发执行类产品的基础能力。"},
            {"name": "任务驱动编辑工作流", "inputOutput": "任务描述 -> 代码改动建议", "reason": "有助于自动化研发场景。"},
        ),
        "highlightFeatures": (
            {"name": "IDE 内 agent flow", "why": "适合作为工作流产品的交互对标。", "risk": "不直接对应公司级流程编排。"},
        ),
        "differences": {"strength": "开发者交互体验成熟。", "limit": "更偏个人 IDE 入口，不是公司级执行中枢。"},
        "intelligenceQuestions": (
            "代码库上下文能力应该沉在宿主层还是流程层？",
        ),
    },
    {
        "aliases": ("devin",),
        "sourceId": "devin-docs",
        "name": "Devin",
        "category": "official-product",
        "official": True,
        "productUrl": "https://devin.ai/",
        "sourceUrl": "https://docs.devin.ai/",
        "captureStatus": "link-registered",
        "intendedUse": "研究任务型 AI 工程执行体的工作流分解与环境操作方式。",
        "focusAreas": ("task decomposition", "execution loop", "environment operations", "agent runtime"),
        "commonCapabilities": (
            {"name": "任务分解与执行 loop", "inputOutput": "任务 -> 子步骤 -> 结果", "reason": "适合作为公司级执行闭环参考。"},
            {"name": "环境操作能力", "inputOutput": "环境状态 -> 执行动作", "reason": "对自动执行器设计有参考价值。"},
        ),
        "highlightFeatures": (
            {"name": "long-running execution loop", "why": "对持续执行任务的节奏控制有参考价值。", "risk": "和当前 Copilot-host 交互模型不完全一致。"},
        ),
        "differences": {"strength": "任务执行闭环感更强。", "limit": "产品内部实现细节不透明。"},
        "intelligenceQuestions": (
            "长任务执行 loop 需要怎样的 checkpoint / resume 模型？",
        ),
    },
    {
        "aliases": ("linear",),
        "sourceId": "linear-docs",
        "name": "Linear",
        "category": "official-product",
        "official": True,
        "productUrl": "https://linear.app/",
        "sourceUrl": "https://linear.app/docs",
        "captureStatus": "link-registered",
        "intendedUse": "研究任务状态机、协同流转和 issue lifecycle 设计。",
        "focusAreas": ("issue lifecycle", "workflow state", "handoff", "collaboration UX"),
        "commonCapabilities": (
            {"name": "任务状态流转", "inputOutput": "状态变更 -> 协同执行", "reason": "适合对标流程编排产品。"},
            {"name": "handoff 与责任切换", "inputOutput": "负责人切换 -> 工作继续", "reason": "对 IPD 阶段切换有帮助。"},
        ),
        "highlightFeatures": (
            {"name": "清晰的 issue lifecycle", "why": "适合借鉴阶段状态与协同面。", "risk": "偏协作系统，不含代码执行能力。"},
        ),
        "differences": {"strength": "状态机与协同面清晰。", "limit": "不直接覆盖代码执行或 agent 环境。"},
        "intelligenceQuestions": (
            "阶段状态机与责任切换如何保持简洁且可审计？",
        ),
    },
    {
        "aliases": ("super-dev", "super dev"),
        "sourceId": "super-dev-upstream-readme",
        "name": "super-dev",
        "category": "upstream-open-source",
        "official": True,
        "productUrl": "https://github.com/shangyankeji/super-dev",
        "sourceUrl": "https://github.com/shangyankeji/super-dev",
        "captureStatus": "link-registered",
        "intendedUse": "研究商业级 AI 自动化开发流程的宿主恢复、知识注入、确认门与交付证据治理。",
        "focusAreas": ("resume and continue", "knowledge bootstrap", "spec-driven delivery", "review and quality gates", "delivery evidence"),
        "commonCapabilities": (
            {"name": "流程恢复与继续执行", "inputOutput": "run state -> continue / resume", "reason": "适合作为自动化开发项目的长任务恢复基线。"},
            {"name": "知识前置注入", "inputOutput": "knowledge bundle -> stage execution", "reason": "适合作为研发流程自动化的软件前置知识治理参考。"},
            {"name": "确认门与交付证据", "inputOutput": "review / quality gate -> release evidence", "reason": "有助于建立商业交付级质量可控和责任可追溯机制。"},
        ),
        "highlightFeatures": (
            {"name": "host-governed workflow", "why": "适合对标 AI 自动化开发软件在宿主恢复、知识注入和确认门上的实现形态。", "risk": "上游流程语义与 TriCompany 的公司级治理边界不能直接等同。"},
        ),
        "differences": {"strength": "在宿主恢复、知识 bootstrap 和交付证据治理方面参考价值高。", "limit": "不能直接替代 TriCompany 的公司级岗位分工与签发治理。"},
        "intelligenceQuestions": (
            "宿主恢复、knowledge bundle 与确认门应该如何映射到公司级 IPD 主线？",
            "哪些 workflow governance 能力适合直接吸收，哪些必须保留本地治理中间层？",
        ),
    },
)
_INTELLIGENCE_SOURCE_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "sourceId": "sub2api-local-reference",
        "name": "Sub2API",
        "aliases": ("platform", "openrouter", "one api", "openai api platform"),
        "themes": ("PLATFORM",),
        "category": "local-reference",
        "localPath": "TriMetaverse/reference/sub2api",
        "sourceUrl": "https://github.com/Wei-Shaw/sub2api",
        "anchorFiles": ("TriMetaverse/reference/sub2api/README.md",),
        "intendedUse": "研究 AI API gateway 的认证、计费、配额、负载均衡、并发控制和管理后台能力。",
        "focusAreas": ("multi-account management", "api key distribution", "usage metering and billing", "smart scheduling", "rate limiting", "admin dashboard"),
        "capabilityCandidates": (
            {"name": "上游账户 / 渠道管理", "signal": "README 强调多账户管理", "decision": "纳入评估", "nextQuestion": "provider / channel / model 抽象层怎样拆"},
            {"name": "API Key 分发", "signal": "README 明确支持平台 API key", "decision": "纳入评估", "nextQuestion": "平台 key 与 tenant 隔离怎么设计"},
            {"name": "计量与计费", "signal": "README 明确支持精细计量", "decision": "纳入评估", "nextQuestion": "首轮 MVP 是否只保留预算护栏与可见性"},
        ),
        "architectureOptions": (
            {"theme": "统一 API 兼容层", "approach": "先兼容 OpenAI 风格接口，再逐步扩展 provider adapter", "pros": "接入成本低", "risks": "兼容层边界容易膨胀", "recommendation": "首轮优先"},
            {"theme": "控制面后台", "approach": "分离渠道管理、模型目录、配额治理和用量可视化", "pros": "便于后续扩展", "risks": "过早拆分会抬高实现复杂度", "recommendation": "首轮做最小后台"},
        ),
    },
    {
        "sourceId": "one-api-upstream-repo",
        "name": "One API",
        "aliases": ("one api", "platform"),
        "themes": ("PLATFORM",),
        "category": "upstream-open-source",
        "sourceUrl": "https://github.com/songquanpeng/one-api",
        "anchorFiles": ("https://github.com/songquanpeng/one-api/blob/master/README.md",),
        "intendedUse": "补充自托管统一模型网关、渠道管理和兼容层的开源实现对标。",
        "focusAreas": ("self-hosted gateway", "channel/provider management", "OpenAI-compatible API", "admin console", "quota management"),
        "capabilityCandidates": (
            {"name": "自托管渠道控制面", "signal": "开源社区广泛用于统一模型网关", "decision": "纳入评估", "nextQuestion": "哪些能力适合 MVP，哪些应后置"},
        ),
        "architectureOptions": (
            {"theme": "渠道治理", "approach": "把渠道配置和流量策略沉在后台管理层", "pros": "治理清晰", "risks": "需要较强运维配置能力", "recommendation": "作为对照组"},
        ),
    },
    {
        "sourceId": "litellm-upstream-repo",
        "name": "LiteLLM",
        "aliases": ("openai api platform", "openrouter", "platform"),
        "themes": ("PLATFORM",),
        "category": "upstream-open-source",
        "sourceUrl": "https://github.com/BerriAI/litellm",
        "anchorFiles": ("https://github.com/BerriAI/litellm/blob/main/README.md",),
        "intendedUse": "补充统一模型适配层、provider adapter 和兼容 API 设计对照。",
        "focusAreas": ("provider adapters", "OpenAI-compatible API", "routing", "cost tracking"),
        "capabilityCandidates": (
            {"name": "provider adapter 抽象层", "signal": "广覆盖 provider 适配", "decision": "纳入评估", "nextQuestion": "我们需要多薄的 adapter 层"},
        ),
        "architectureOptions": (
            {"theme": "adapter layer", "approach": "保持 adapter 薄层，把预算护栏与控制面留在上层", "pros": "演进清晰", "risks": "需要额外控制面开发", "recommendation": "首轮参考"},
        ),
    },
    {
        "sourceId": "super-dev-vendor-reference",
        "name": "super-dev",
        "aliases": ("super-dev", "super dev"),
        "themes": ("WORKFLOW",),
        "category": "local-reference",
        "localPath": "TriDev/vendor/super-dev",
        "sourceUrl": "https://github.com/shangyankeji/super-dev",
        "anchorFiles": ("TriDev/vendor/super-dev/README.md", "TriDev/docs/workflow/super-dev-absorption-record.md"),
        "intendedUse": "补充商业级自动化开发流程治理、宿主恢复、知识注入与交付证据的实现对照，并结合 TriDev 吸收链做 Intelligence 研判。",
        "focusAreas": ("workflow governance", "resume and continue", "knowledge bootstrap", "review and quality gates", "delivery evidence"),
        "capabilityCandidates": (
            {"name": "宿主恢复与继续执行", "signal": "vendor 与吸收记录都强调 start / resume / continue 契约", "decision": "纳入评估", "nextQuestion": "哪些恢复语义应沉在宿主，哪些应保留在流程引擎层"},
            {"name": "knowledge bundle 前置注入", "signal": "吸收记录强调 knowledge bundle 与 host prompt context", "decision": "纳入评估", "nextQuestion": "知识注入与阶段 owner 自动执行之间如何做最小耦合"},
            {"name": "review gate 与交付证据", "signal": "上游和吸收记录都强调 review / quality / delivery evidence", "decision": "纳入评估", "nextQuestion": "哪些证据必须结构化落盘才能满足商业交付级可审计性"},
        ),
        "architectureOptions": (
            {"theme": "workflow governor", "approach": "把恢复、知识注入和确认门能力吸收到公司级 IPD 宿主层，而不直接替换阶段语义", "pros": "能保留岗位治理边界", "risks": "需要额外中间层适配", "recommendation": "首轮优先"},
            {"theme": "delivery evidence discipline", "approach": "把 proof-pack、review state 和 evidence binding 映射成本地阶段产物协议", "pros": "便于后续质量门和版本签发", "risks": "过早全量照搬会增加实现复杂度", "recommendation": "按最小闭环吸收"},
        ),
    },
    {
        "sourceId": "openhands-upstream-repo",
        "name": "OpenHands",
        "aliases": ("cursor", "devin", "workflow", "linear"),
        "themes": ("WORKFLOW",),
        "category": "upstream-open-source",
        "sourceUrl": "https://github.com/All-Hands-AI/OpenHands",
        "anchorFiles": ("https://github.com/All-Hands-AI/OpenHands/blob/main/README.md",),
        "intendedUse": "补充任务分解、agent runtime 和长流程执行的开源实现对照。",
        "focusAreas": ("task execution", "agent runtime", "environment operations"),
        "capabilityCandidates": (
            {"name": "任务执行 loop", "signal": "开源 agent runtime", "decision": "纳入评估", "nextQuestion": "我们需要多长的执行 loop"},
        ),
        "architectureOptions": (
            {"theme": "agent runtime", "approach": "流程层与执行层分离", "pros": "便于治理", "risks": "宿主与执行层接口复杂", "recommendation": "对照参考"},
        ),
    },
    {
        "sourceId": "continue-upstream-repo",
        "name": "Continue",
        "aliases": ("cursor", "workflow"),
        "themes": ("WORKFLOW",),
        "category": "upstream-open-source",
        "sourceUrl": "https://github.com/continuedev/continue",
        "anchorFiles": ("https://github.com/continuedev/continue/blob/main/README.md",),
        "intendedUse": "补充 IDE 入口、代码上下文与工作流对照。",
        "focusAreas": ("IDE integration", "context retrieval", "developer workflow"),
        "capabilityCandidates": (
            {"name": "IDE 入口与上下文检索", "signal": "IDE 插件和代码上下文能力成熟", "decision": "纳入评估", "nextQuestion": "哪些能力应落在宿主而不是流程层"},
        ),
        "architectureOptions": (
            {"theme": "宿主入口", "approach": "把上下文检索沉到宿主能力层", "pros": "用户体验直接", "risks": "宿主耦合较强", "recommendation": "按需参考"},
        ),
    },
)
_REAL_EXECUTION_RESERVED_FILENAMES = {
    "release.zip",
    "release.sha256",
    "delivery-manifest.json",
    "gate-ledger.json",
    "workflow-summary.md",
    "events.jsonl",
    "artifact-bindings.json",
    "reference-evidence.json",
    "validation-report.json",
    "run-metadata.json",
    "release-file-manifest.json",
    "release-verification-report.json",
}
_OWNER_ACTION_BLOCK_REASON = (
    "Autopilot 不再代表 ChiefProductOfficer 或 ChiefTechnologyOfficer 直接提交阶段输出；"
    "当前只生成 owner action package，并等待 acting owner 手动提交真实阶段产物。"
)
_NON_GENERATED_EVIDENCE_BLOCK_REASON = (
    "当前阶段至少需要一类非 workbench/knowledge/autopilot 生成物的真实提交证据，"
    "不能只依赖 docs/workbench/autopilot 包装产物自动放行。"
)
_REAL_EXECUTION_BLOCK_REASON = (
    "当前阶段需要真实工程执行证据（源码、测试、部署或运行产物），"
    "不能只依赖 workbench/docs/autopilot 生成物自动放行。"
)
_INTAKE_CLARIFICATION_SLOT_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "slotKey": "competitorReference",
        "label": "竞品 / 对标对象",
        "requiredFor": ("intake", "discovery"),
        "ownerRole": "CEO",
        "whyItMatters": "没有竞品或对标对象，CPO 在 Discovery 阶段就缺少明确的产品/官方手册研究起点。",
        "question": "这次需求至少想对标哪 1-3 个产品、平台、仓库或流程？如果没有直接竞品，也请明确‘按哪类现有方案对标’。",
        "suggestedOptions": (
            "已有 1-3 个明确竞品，请直接写名称或链接。",
            "没有直接竞品，但有同类流程/平台可对标。",
            "按内部流程问题处理，不对标外部竞品，但请说明原因。",
            "自定义。",
        ),
    },
    {
        "slotKey": "targetUserScenario",
        "label": "首轮目标用户与使用场景",
        "requiredFor": ("intake", "discovery"),
        "ownerRole": "CEO",
        "whyItMatters": "不明确谁在什么场景下使用，CMO 很难验证这是不是值得做的真实需求。",
        "question": "这次先服务哪类用户，在什么高频场景下用，当前最想解决什么问题？",
        "suggestedOptions": (
            "先服务内部岗位，提高研发/经营执行效率。",
            "先服务现有潜在客户，验证是否愿意试点或付费。",
            "先做 CEO / 总助 / 管理层内部控制面。",
            "自定义。",
        ),
    },
    {
        "slotKey": "deliveryWindow",
        "label": "期望工期 / 节奏",
        "requiredFor": ("intake", "designing"),
        "ownerRole": "CEO",
        "whyItMatters": "没有节奏约束，总助无法把任务拆成合理阶段，也无法约束 CPO / CTO 的交付窗口。",
        "question": "这次希望以什么节奏推进？是先 48 小时内出 briefing，还是一周内出 PRD，还是两周内跑最小验证？",
        "suggestedOptions": (
            "48 小时内完成 intake / Discovery 入口澄清。",
            "1 周内完成 Discovery + Intelligence + PRD。",
            "2 周内完成最小 MVP 验证。",
            "自定义。",
        ),
    },
    {
        "slotKey": "budgetGuardrail",
        "label": "预算护栏 / 成本窗口",
        "requiredFor": ("intake", "intelligence"),
        "ownerRole": "CEO",
        "whyItMatters": "不明确预算窗口，CFO 就无法形成后续预算护栏，CPO/CTO 也无法判断首轮范围。",
        "question": "这次允许投入到什么程度？只用现有人力，还是允许少量工具成本，还是允许明确试验预算？",
        "suggestedOptions": (
            "只用现有岗位和现有工具先验证。",
            "允许少量模型/API/工具试验成本。",
            "允许 1-3 人天级别的试验投入。",
            "自定义。",
        ),
    },
    {
        "slotKey": "successMetric",
        "label": "首轮成功信号",
        "requiredFor": ("intake", "delivery"),
        "ownerRole": "CEO",
        "whyItMatters": "没有成功信号，后续很容易把‘做完一些功能’误当成‘需求成立’。",
        "question": "这次第一轮做成，最希望看到什么结果？流程跑通、试点用户正反馈、可收费、还是节省了人力？",
        "suggestedOptions": (
            "先证明 IPD / 产品流程能跑通。",
            "先拿到一个可展示或可试点的 MVP。",
            "先验证有人愿意继续用或付费。",
            "自定义。",
        ),
    },
    {
        "slotKey": "mustHaveScope",
        "label": "必须交付的最小范围",
        "requiredFor": ("intake", "designing"),
        "ownerRole": "CEO",
        "whyItMatters": "没有最小范围，Discovery/Intelligence 很容易继续膨胀，最后 PRD 无法收口。",
        "question": "这次必须交付的最小结果是什么？是一份 PRD、一个最小工作流、一个 MVP 页面，还是完整平台闭环？",
        "suggestedOptions": (
            "先交付可签核 PRD 与项目计划。",
            "先交付单条最小工作流验证。",
            "先交付可演示 MVP。",
            "自定义。",
        ),
    },
    {
        "slotKey": "explicitOutOfScope",
        "label": "明确不做项",
        "requiredFor": ("intake", "discovery"),
        "ownerRole": "CEO",
        "whyItMatters": "没有不做项，团队容易把远期能力和当前验证目标混写。",
        "question": "这次明确不做什么？比如不上正式宿主、不做链上实现、不做大规模运营、不做完整商业化。",
        "suggestedOptions": (
            "不涉及正式宿主切换。",
            "不涉及链上/钱包/合约真实实现。",
            "不涉及大规模上线与运营。",
            "自定义。",
        ),
    },
)
_INTAKE_STAGE_ROLE_ASSIGNMENT_MATRIX: tuple[dict[str, Any], ...] = (
    {
        "role": "CEOChiefOfStaff",
        "stageKeys": ("intake", "backlog", "sprint-planning", "retrospective", "validation-handoff"),
        "taskType": "intake-orchestration",
        "status": "active",
        "canFreezeCase": True,
        "responsibility": "把 CEO 需求转成 intake briefing，补齐关键填槽信息，并在流程优化类 case 中维护 backlog、迭代计划、复盘和验证移交。",
        "deliverables": ("intake briefing", "clarification sheet", "dispatch plan", "backlog memo", "retrospective memo"),
    },
    {
        "role": "CEO",
        "stageKeys": ("intake",),
        "taskType": "clarification-and-signoff",
        "status": "active",
        "canFreezeCase": False,
        "responsibility": "补齐关键槽位并决定是否让事项进入公司级 IPD 主动交付线。",
        "deliverables": ("clarification answers", "intake signoff"),
    },
    {
        "role": "ChiefMarketingOfficer",
        "stageKeys": ("discovery",),
        "taskType": "demand-validation",
        "status": "placeholder",
        "canFreezeCase": True,
        "responsibility": "验证这是不是合理的真实需求，避免公司做出没有市场需求的产品。",
        "deliverables": ("需求真实性验证", "目标用户/场景复核"),
    },
    {
        "role": "ChiefProductOfficer",
        "stageKeys": ("discovery", "intelligence", "delivery", "backlog", "sprint-planning", "sprint-review", "validation-handoff"),
        "taskType": "product-research-and-prd",
        "status": "active",
        "canFreezeCase": True,
        "responsibility": "项目交付 case 中负责 Discovery/Intelligence/Delivery；流程优化 case 中负责 backlog 边界、review 收口和真实验证 handoff 口径。",
        "deliverables": (
            "DiscoveryReferenceFunctionalBrief",
            "DiscoveryCompetitorLandscape",
            "DiscoveryCommonCapabilityMatrix",
            "DiscoveryHighlightOpportunityMemo",
            "竞品/功能/官方手册研究",
            "正式 PRD",
            "项目计划",
            "review memo",
        ),
    },
    {
        "role": "ChiefTechnologyOfficer",
        "stageKeys": (
            "intelligence",
            "designing",
            "coding",
            "verify-integration",
            "redteam",
            "qa",
            "deployment",
            "assurance",
            "sprint-execution",
            "sprint-review",
            "validation-handoff",
        ),
        "taskType": "code-research-and-technical-design",
        "status": "active",
        "canFreezeCase": True,
        "responsibility": "项目交付 case 中负责代码研究、设计与开发；流程优化 case 中负责 sprint-execution 的实现、验证和技术缺口收口。",
        "deliverables": (
            "IntelligenceCapabilityExtractionMatrix",
            "IntelligenceOpenSourceLandscape",
            "IntelligenceCodegraphAnalysis",
            "IntelligenceArchitectureOptionMemo",
            "开源代码分析结论",
            "技术方案",
            "execution validation",
        ),
    },
    {
        "role": "ChiefOperatingOfficer",
        "stageKeys": ("intelligence", "deployment", "assurance", "delivery"),
        "taskType": "operations-constraints",
        "status": "placeholder",
        "canFreezeCase": True,
        "responsibility": "补试点路径、上线节奏和运营约束。",
        "deliverables": ("运营约束", "试点路径", "rollout 计划"),
    },
    {
        "role": "ChiefFinancialOfficer",
        "stageKeys": ("intelligence", "deployment", "assurance", "delivery"),
        "taskType": "budget-guardrail",
        "status": "placeholder",
        "canFreezeCase": True,
        "responsibility": "补预算护栏、成本窗口、止损条件和后续财务复核。",
        "deliverables": ("预算护栏", "成本约束", "止损条件"),
    },
)


def initialize_ipd_case(
    *,
    case_id: str,
    title: str,
    objective: str,
    task_description: str,
    created_by: str = "CEOChiefOfStaff",
    priority: str = "high",
    related_modules: Iterable[str] = (),
    constraints: Iterable[str] = (),
    opportunity_signals: Iterable[str] = (),
    business_model_fit: Iterable[str] = (),
    stage_fit: Iterable[str] = (),
    company_context: Iterable[str] = (),
    owner_proposal: Iterable[str] = (),
    resource_envelope: Iterable[str] = (),
    prerequisites: Iterable[str] = (),
    required_support: Iterable[str] = (),
    expected_outcomes: Iterable[str] = (),
    market_context: Iterable[str] = (),
    division_of_work: Iterable[str] = (),
    staffing_cost: Iterable[str] = (),
    other_cost: Iterable[str] = (),
    slot_answers: dict[str, str] | None = None,
    require_clarification_slots: bool = False,
    case_category: str = "",
    reference_theme: str = "",
    expected_delivery: str = "",
    required_approvers: Iterable[str] = INTAKE_REQUIRED_APPROVERS,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    now = _timestamp_now()
    normalized_case_id = _normalize_identifier(case_id)
    case_root = chief_of_staff_ipd_case_root(normalized_case_id, workspace_root)
    existing_case_payload: dict[str, Any] | None = None
    if case_root.exists():
        existing_case_payload = _load_case(normalized_case_id, workspace_root)
        if not _can_refine_intake(existing_case_payload):
            raise FileExistsError(f"IPD case already exists and cannot be reinitialized: {normalized_case_id}")
    else:
        case_root.mkdir(parents=True, exist_ok=True)
    existing_intake = existing_case_payload.get("intake", {}) if isinstance(existing_case_payload, dict) else {}
    approvals = _build_approvals(required_approvers, auto_approved_role=None, now=now)
    normalized_slot_answers = _normalize_slot_answers(slot_answers)
    clarification_sheet = _build_intake_clarification_sheet(
        task_description=task_description,
        slot_answers=normalized_slot_answers,
        required=require_clarification_slots,
    )
    resolved_case_category = _normalize_case_category(
        case_category or str(existing_intake.get("caseCategory") or ""),
        case_id=normalized_case_id,
    )
    resolved_reference_theme = _normalize_reference_theme(
        reference_theme or str(existing_intake.get("referenceTheme") or ""),
        case_id=normalized_case_id,
        case_category=resolved_case_category,
    )
    stage_templates = _initial_stage_templates(
        case_category=resolved_case_category,
        reference_theme=resolved_reference_theme,
    )
    case_payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "caseId": normalized_case_id,
        "title": title.strip(),
        "status": "awaiting-intake-approvals",
        "priority": priority.strip() or "high",
        "relatedModules": _string_list(related_modules),
        "createdAt": str((existing_case_payload or {}).get("createdAt") or now),
        "updatedAt": now,
        "currentStageKey": "",
        "currentWorkItemPath": "",
        "intake": {
            "objective": objective.strip(),
            "taskDescription": task_description.strip(),
            "constraints": _string_list(constraints),
            "opportunitySignals": _merge_string_lists(opportunity_signals, market_context),
            "businessModelFit": _string_list(business_model_fit),
            "stageFit": _string_list(stage_fit),
            "companyContext": _string_list(company_context),
            "ownerProposal": _merge_string_lists(owner_proposal, division_of_work),
            "resourceEnvelope": _merge_string_lists(resource_envelope, staffing_cost, other_cost),
            "prerequisites": _string_list(prerequisites),
            "requiredSupport": _string_list(required_support),
            "expectedOutcomes": _string_list(expected_outcomes),
            "slotAnswers": normalized_slot_answers,
            "clarificationRequired": require_clarification_slots,
            "clarificationSheet": clarification_sheet,
            "caseCategory": resolved_case_category,
            "referenceTheme": resolved_reference_theme,
            "roleAssignmentMatrix": _build_intake_role_assignment_matrix(),
            "expectedDelivery": expected_delivery.strip(),
            "briefPath": "",
            "packageHash": "",
            "releaseCounter": 0,
            "releaseVersion": "",
            "releaseStatus": "draft",
            "releaseIssuedAt": "",
            "releaseIssuedByRole": "",
            "createdBy": created_by.strip() or "CEOChiefOfStaff",
            "createdAt": str(((existing_case_payload or {}).get("intake", {}) or {}).get("createdAt") or now),
            "approvals": approvals,
            "status": _approval_rollup(approvals),
        },
        "stages": [
            {
                "stageKey": template["stageKey"],
                "title": template["title"],
                "businessOwner": template["businessOwner"],
                "actingOwner": template["actingOwner"],
                "moduleExecutor": template["moduleExecutor"],
                "gateOwner": template["gateOwner"],
                "ownerRole": template["actingOwner"],
                "phaseKey": template["phaseKey"],
                "participantRoles": list(template["participantRoles"]),
                "status": "pending",
                "requiredApprovers": _stage_required_approvers(template["actingOwner"]),
                "approvals": _build_approvals(_stage_required_approvers(template["actingOwner"]), auto_approved_role=None, now=""),
                "schemaHint": dict(template["schemaHint"]),
                "inputRequirements": list(template["inputRequirements"]),
                "superDevReferenceStages": list(template["superDevReferenceStages"]),
                "workItemPath": "",
                "outputPath": "",
                "packageHash": "",
                "releaseCounter": 0,
                "releaseVersion": "",
                "releaseStatus": "draft",
                "releaseIssuedAt": "",
                "releaseIssuedByRole": "",
                "activatedAt": "",
                "submittedAt": "",
                "completedAt": "",
                "blockedReason": "",
                "outputSummary": "",
                "lastUpdatedAt": now,
            }
            for template in stage_templates
        ],
    }
    intake_brief_path = _write_intake_brief(case_payload, workspace_root=workspace_root, written_at=now)
    case_payload["intake"]["briefPath"] = intake_brief_path.as_posix()
    _save_case(case_payload, workspace_root)
    _append_event(
        normalized_case_id,
        "intake-brief-refined" if existing_case_payload is not None else "case-initialized",
        {
            "createdBy": created_by,
            "intakeStatus": case_payload["intake"]["status"],
            "intakeBriefPath": intake_brief_path.as_posix(),
        },
        workspace_root=workspace_root,
    )
    return reconcile_ipd_case(normalized_case_id, workspace_root=workspace_root)


def reconcile_ipd_case(case_id: str, *, workspace_root: str | None = None) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    case_payload, summary = _reconcile_case_payload(case_payload, workspace_root=workspace_root)
    _save_case(case_payload, workspace_root)
    return summary


def reconcile_all_ipd_cases(*, workspace_root: str | None = None) -> dict[str, Any]:
    cases_root = chief_of_staff_ipd_cases_root(workspace_root)
    summaries: list[dict[str, Any]] = []
    if cases_root.exists():
        for case_root in sorted(path for path in cases_root.iterdir() if path.is_dir()):
            case_file = case_root / "case.json"
            if not case_file.exists():
                continue
            summaries.append(reconcile_ipd_case(case_root.name, workspace_root=workspace_root))
    return {
        "reconciledCaseCount": len(summaries),
        "advancedCaseCount": sum(1 for item in summaries if item["advanced"]),
        "completedCaseCount": sum(1 for item in summaries if item["status"] == "completed"),
        "cases": summaries,
    }


def record_intake_signoff(
    case_id: str,
    *,
    role: str,
    decision: str = "approved",
    note: str = "",
    signing_key: str = "",
    mnemonic: str = "",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    _assert_case_not_frozen(case_payload, action="intake signoff")
    now = _timestamp_now()
    package_hash = _package_hash(_build_intake_signature_payload(case_payload))
    case_payload["intake"]["packageHash"] = package_hash
    approval_record = _record_signed_approval(
        case_payload["intake"]["approvals"],
        role=role,
        decision=decision,
        note=note,
        now=now,
        package_hash=package_hash,
        signing_key=signing_key,
        mnemonic=mnemonic,
        default_seed=_default_wallet_seed(role),
    )
    case_payload["intake"]["status"] = _approval_rollup(case_payload["intake"]["approvals"])
    release_version = ""
    if role == "CEOChiefOfStaff" and decision.strip().lower() == "approved" and case_payload["intake"]["status"] == "approved":
        release_version = _issue_release(
            case_payload["intake"],
            case_id=case_payload["caseId"],
            subject_token="INTAKE",
            issued_by_role=role,
            now=now,
        )
    intake_brief_path = _write_intake_brief(case_payload, workspace_root=workspace_root, written_at=now)
    case_payload["intake"]["briefPath"] = intake_brief_path.as_posix()
    case_payload["updatedAt"] = now
    _append_event(
        case_payload["caseId"],
        "intake-signoff-recorded",
        {
            "role": role,
            "decision": decision,
            "note": note,
            "packageHash": package_hash,
            "signerAddress": approval_record.get("signerAddress", ""),
            "releaseVersion": release_version,
            "intakeBriefPath": intake_brief_path.as_posix(),
        },
        workspace_root=workspace_root,
    )
    _save_case(case_payload, workspace_root)
    return reconcile_ipd_case(case_payload["caseId"], workspace_root=workspace_root)


def submit_stage_output(
    case_id: str,
    *,
    stage_key: str,
    submitted_by: str,
    summary: str,
    details: Iterable[str] = (),
    evidence: Iterable[str] = (),
    object_path: str = "",
    signing_key: str = "",
    mnemonic: str = "",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    _assert_case_not_frozen(case_payload, action="stage submit")
    stage = _require_stage(case_payload, stage_key)
    if case_payload.get("currentStageKey") != stage_key:
        raise ValueError(f"current stage is {case_payload.get('currentStageKey') or 'none'}, not {stage_key}")
    if submitted_by != stage["actingOwner"]:
        raise ValueError(f"{submitted_by} cannot submit stage owned by {stage['actingOwner']}")
    _validate_stage_submission_evidence(stage, evidence=evidence, object_path=object_path)
    now = _timestamp_now()
    stage["requiredApprovers"] = _stage_required_approvers(stage["actingOwner"])
    stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
    stage["releaseVersion"] = ""
    stage["releaseStatus"] = "draft"
    stage["releaseIssuedAt"] = ""
    stage["releaseIssuedByRole"] = ""
    stage["packageHash"] = _package_hash(
        _build_stage_output_core_payload(
            case_payload,
            stage,
            summary=summary,
            details=details,
            evidence=evidence,
            object_path=object_path,
            written_at=now,
        )
    )
    owner_approval = _record_signed_approval(
        stage["approvals"],
        role=stage["actingOwner"],
        decision="approved",
        note="owner package signature recorded at submit",
        now=now,
        package_hash=stage["packageHash"],
        signing_key=signing_key,
        mnemonic=mnemonic,
        default_seed=_default_wallet_seed(stage["actingOwner"]),
    )
    output_path = _write_stage_output(
        case_payload,
        stage,
        summary=summary,
        details=details,
        evidence=evidence,
        object_path=object_path,
        workspace_root=workspace_root,
        written_at=now,
    )
    stage["status"] = "submitted"
    stage["outputPath"] = output_path.as_posix()
    stage["submittedAt"] = now
    stage["blockedReason"] = ""
    stage["outputSummary"] = summary.strip()
    stage["lastUpdatedAt"] = now
    case_payload["status"] = "awaiting-stage-approvals"
    case_payload["updatedAt"] = now
    _append_event(
        case_payload["caseId"],
        "stage-output-submitted",
        {
            "stageKey": stage_key,
            "submittedBy": submitted_by,
            "outputPath": output_path.as_posix(),
            "packageHash": stage["packageHash"],
            "signerAddress": owner_approval.get("signerAddress", ""),
        },
        workspace_root=workspace_root,
    )
    _save_case(case_payload, workspace_root)
    return _summary_for_case(case_payload, advanced=False)


def record_stage_signoff(
    case_id: str,
    *,
    stage_key: str,
    role: str,
    decision: str = "approved",
    note: str = "",
    signing_key: str = "",
    mnemonic: str = "",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    _assert_case_not_frozen(case_payload, action="stage signoff")
    stage = _require_stage(case_payload, stage_key)
    if stage["status"] != "submitted":
        raise ValueError(f"stage {stage_key} is not ready for signoff: {stage['status']}")
    now = _timestamp_now()
    package_hash = _resolve_stage_package_hash(stage, workspace_root=workspace_root)
    if not package_hash:
        raise ValueError(f"stage {stage_key} is missing package hash for signoff")
    approval_record = _record_signed_approval(
        stage["approvals"],
        role=role,
        decision=decision,
        note=note,
        now=now,
        package_hash=package_hash,
        signing_key=signing_key,
        mnemonic=mnemonic,
        default_seed=_default_wallet_seed(role),
    )
    release_version = ""
    if role == "CEOChiefOfStaff" and decision.strip().lower() == "approved" and _approval_rollup(stage["approvals"]) == "approved":
        release_version = _issue_release(
            stage,
            case_id=case_payload["caseId"],
            subject_token=stage_key.upper(),
            issued_by_role=role,
            now=now,
        )
    _sync_stage_output_metadata(stage, workspace_root=workspace_root)
    stage["lastUpdatedAt"] = now
    case_payload["updatedAt"] = now
    _append_event(
        case_payload["caseId"],
        "stage-signoff-recorded",
        {
            "stageKey": stage_key,
            "role": role,
            "decision": decision,
            "note": note,
            "packageHash": package_hash,
            "signerAddress": approval_record.get("signerAddress", ""),
            "releaseVersion": release_version,
        },
        workspace_root=workspace_root,
    )
    _save_case(case_payload, workspace_root)
    return reconcile_ipd_case(case_payload["caseId"], workspace_root=workspace_root)


def read_ipd_case(case_id: str, *, workspace_root: str | None = None) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    case_payload["entryCheckpoint"] = _entry_checkpoint_for_case(case_payload)
    return case_payload


def run_discovery_stage_automation(
    case_id: str,
    *,
    workspace_root: str | None = None,
    submit: bool = False,
) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    _assert_case_not_frozen(case_payload, action="discovery automation")
    stage = _ensure_stage_ready_for_automation(case_payload, "discovery", submit=submit)
    standard_flow = _stage_standard_flow(case_payload, stage)
    generated_at = _timestamp_now()
    sources = _build_discovery_sources(case_payload)
    catalog_ref = str(standard_flow.get("catalogPath") or "").strip()
    _write_stage_reference_catalog(
        catalog_ref,
        {
            "schemaVersion": IPD_CASE_SCHEMA_VERSION,
            "kind": "discovery-reference-source-catalog",
            "caseId": case_payload["caseId"],
            "stageKey": "discovery",
            "captureMode": "seeded-auto-generated",
            "generatedAt": generated_at,
            "notes": [
                "该 catalog 由 discovery 自动执行器根据当前 case 槽位和内置种子自动生成。",
                "请在人工复核后补充真实抓取、离线快照或额外官方来源。",
            ],
            "sources": sources,
        },
        workspace_root=workspace_root,
    )
    document_refs = _write_discovery_documents(
        case_payload,
        standard_flow=standard_flow,
        sources=sources,
        written_at=generated_at,
        workspace_root=workspace_root,
    )
    _validate_discovery_seeded_competitor_coverage(
        case_payload,
        catalog_ref=catalog_ref,
        summary_ref=str(standard_flow.get("summaryDocument", {}).get("path") or ""),
        landscape_ref=str(standard_flow.get("packageDocuments", [{}])[0].get("path") or ""),
        workspace_root=workspace_root,
    )
    generated_refs = [catalog_ref, *document_refs]
    details = [
        f"已自动登记 {len(sources)} 个 Discovery 对标来源。",
        "已自动刷新 Discovery 的竞品 landscape、共性功能矩阵、亮点功能 memo 与 functional brief。",
    ]
    return _finalize_stage_automation(
        case_payload,
        stage,
        generated_refs=generated_refs,
        details=details,
        object_path=str(standard_flow.get("summaryDocument", {}).get("path") or ""),
        submit=submit,
        workspace_root=workspace_root,
    )


def run_intelligence_stage_automation(
    case_id: str,
    *,
    workspace_root: str | None = None,
    submit: bool = False,
    enable_codegraph: bool = True,
) -> dict[str, Any]:
    case_payload = _load_case(case_id, workspace_root)
    _assert_case_not_frozen(case_payload, action="intelligence automation")
    stage = _ensure_stage_ready_for_automation(case_payload, "intelligence", submit=submit)
    standard_flow = _stage_standard_flow(case_payload, stage)
    generated_at = _timestamp_now()
    sources = _build_intelligence_sources(case_payload)
    codegraph_reports: list[dict[str, Any]] = []
    if enable_codegraph:
        for source in sources:
            if str(source.get("localPath") or "").strip():
                codegraph_reports.append(
                    _collect_codegraph_insights(case_payload, source, workspace_root=workspace_root)
                )
        _merge_codegraph_reports_into_sources(sources, codegraph_reports)
    catalog_ref = str(standard_flow.get("catalogPath") or "").strip()
    _write_stage_reference_catalog(
        catalog_ref,
        {
            "schemaVersion": IPD_CASE_SCHEMA_VERSION,
            "kind": "intelligence-reference-source-catalog",
            "caseId": case_payload["caseId"],
            "stageKey": "intelligence",
            "captureMode": "seeded-auto-generated",
            "generatedAt": generated_at,
            "notes": [
                "该 catalog 由 intelligence 自动执行器根据 Discovery 输入、内置开源种子和本地锚点自动生成。",
                "对存在 localPath 的锚点，执行器会尽量补齐 CodeGraph 状态；若宿主不可用，则降级登记为待执行。",
            ],
            "sources": sources,
        },
        workspace_root=workspace_root,
    )
    document_refs = _write_intelligence_documents(
        case_payload,
        standard_flow=standard_flow,
        sources=sources,
        codegraph_reports=codegraph_reports,
        written_at=generated_at,
        workspace_root=workspace_root,
    )
    generated_refs = [catalog_ref, *document_refs]
    details = [
        f"已自动登记 {len(sources)} 个 Intelligence 开源 / 公开资料来源。",
        "已自动刷新开源地图、CodeGraph 深读记录、能力提取矩阵和架构选型 memo。",
    ]
    return _finalize_stage_automation(
        case_payload,
        stage,
        generated_refs=generated_refs,
        details=details,
        object_path=str(standard_flow.get("analysisDocument", {}).get("path") or ""),
        submit=submit,
        workspace_root=workspace_root,
    )


def _ensure_stage_ready_for_automation(
    case_payload: dict[str, Any],
    stage_key: str,
    *,
    submit: bool,
) -> dict[str, Any]:
    stage = _require_stage(case_payload, stage_key)
    current_stage_key = str(case_payload.get("currentStageKey") or "").strip()
    if current_stage_key != stage_key:
        raise ValueError(f"current stage is {current_stage_key or 'none'}, not {stage_key}")
    if stage.get("status") not in {"in-progress", "submitted", "completed"}:
        raise ValueError(f"stage {stage_key} is not available for automation: {stage.get('status')}")
    return stage


def _finalize_stage_automation(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    generated_refs: list[str],
    details: list[str],
    object_path: str,
    submit: bool,
    workspace_root: str | None,
) -> dict[str, Any]:
    if submit:
        result = submit_stage_output(
            case_payload["caseId"],
            stage_key=stage["stageKey"],
            submitted_by=stage["actingOwner"],
            summary=_AUTOMATION_STAGE_SUMMARIES[stage["stageKey"]],
            details=details,
            evidence=generated_refs,
            object_path=object_path,
            workspace_root=workspace_root,
        )
        result["submitted"] = True
    else:
        result = _summary_for_case(case_payload, advanced=False, workspace_root=workspace_root)
        result["submitted"] = False
    result["automationStageKey"] = stage["stageKey"]
    result["generatedFiles"] = generated_refs
    return result


def freeze_ipd_case(
    case_id: str,
    *,
    role: str,
    reason: str,
    domain: str = "",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    normalized_role = str(role or "").strip()
    normalized_reason = str(reason or "").strip()
    if not normalized_role:
        raise ValueError("role is required")
    if not normalized_reason:
        raise ValueError("reason is required")

    case_payload = _load_case(case_id, workspace_root)
    if _case_is_frozen(case_payload):
        raise ValueError("case is already frozen")
    _assert_role_can_freeze_case(case_payload, normalized_role)

    now = _timestamp_now()
    current_stage = _current_stage(case_payload)
    stage_key = str(current_stage.get("stageKey") or "").strip() if current_stage else ""
    normalized_domain = str(domain or "").strip() or _infer_freeze_domain(normalized_role, stage_key)
    freeze_control = {
        "active": True,
        "status": "frozen",
        "frozenAt": now,
        "frozenByRole": normalized_role,
        "stageKey": stage_key,
        "domain": normalized_domain,
        "reason": normalized_reason,
        "previousCaseStatus": str(case_payload.get("status") or "").strip(),
        "previousStageStatus": str(current_stage.get("status") or "").strip() if current_stage else "",
        "previousBlockedReason": str(current_stage.get("blockedReason") or "").strip() if current_stage else "",
    }
    case_payload["freezeControl"] = freeze_control
    if current_stage is not None:
        current_stage["status"] = "frozen"
        current_stage["blockedReason"] = normalized_reason
        current_stage["lastUpdatedAt"] = now
    case_payload["status"] = "paused-frozen"
    case_payload["updatedAt"] = now

    intake_brief_path = _write_intake_brief(case_payload, workspace_root=workspace_root, written_at=now)
    case_payload["intake"]["briefPath"] = intake_brief_path.as_posix()
    _append_event(
        case_payload["caseId"],
        "case-frozen",
        {
            "role": normalized_role,
            "stageKey": stage_key,
            "domain": normalized_domain,
            "reason": normalized_reason,
        },
        workspace_root=workspace_root,
    )
    _save_case(case_payload, workspace_root)
    return _summary_for_case(case_payload, advanced=False, workspace_root=workspace_root)


def unfreeze_ipd_case(
    case_id: str,
    *,
    role: str,
    note: str = "",
    workspace_root: str | None = None,
) -> dict[str, Any]:
    normalized_role = str(role or "").strip()
    normalized_note = str(note or "").strip()
    if not normalized_role:
        raise ValueError("role is required")

    case_payload = _load_case(case_id, workspace_root)
    freeze_control = _normalize_freeze_control(case_payload.get("freezeControl"))
    if not freeze_control.get("active"):
        raise ValueError("case is not frozen")
    _assert_role_can_unfreeze_case(case_payload, normalized_role)

    now = _timestamp_now()
    current_stage = _current_stage(case_payload)
    frozen_stage_key = str(freeze_control.get("stageKey") or "").strip()
    if current_stage is not None and str(current_stage.get("stageKey") or "").strip() == frozen_stage_key:
        previous_stage_status = str(freeze_control.get("previousStageStatus") or "").strip() or "in-progress"
        current_stage["status"] = previous_stage_status
        current_stage["blockedReason"] = str(freeze_control.get("previousBlockedReason") or "").strip()
        current_stage["lastUpdatedAt"] = now

    freeze_control.update(
        {
            "active": False,
            "status": "resolved",
            "resolvedAt": now,
            "resolvedByRole": normalized_role,
            "resolutionNote": normalized_note,
        }
    )
    case_payload["freezeControl"] = freeze_control
    case_payload["status"] = str(freeze_control.get("previousCaseStatus") or case_payload.get("status") or "").strip()
    case_payload["updatedAt"] = now

    intake_brief_path = _write_intake_brief(case_payload, workspace_root=workspace_root, written_at=now)
    case_payload["intake"]["briefPath"] = intake_brief_path.as_posix()
    _append_event(
        case_payload["caseId"],
        "case-unfrozen",
        {
            "role": normalized_role,
            "stageKey": frozen_stage_key,
            "note": normalized_note,
        },
        workspace_root=workspace_root,
    )
    _save_case(case_payload, workspace_root)
    return reconcile_ipd_case(case_payload["caseId"], workspace_root=workspace_root)


def rollback_ipd_case(
    case_id: str,
    *,
    stage_key: str,
    reason: str,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    normalized_stage_key = str(stage_key or "").strip().lower()
    if not normalized_stage_key:
        raise ValueError("stage_key is required")
    if not str(reason or "").strip():
        raise ValueError("reason is required")

    case_payload = _load_case(case_id, workspace_root)
    previous_stage_key = str(case_payload.get("currentStageKey") or "").strip()
    now = _timestamp_now()
    rollback_target = _resolve_rollback_target(case_payload, normalized_stage_key)

    if rollback_target["kind"] == "ceo-demand":
        reset_stage_keys = _reset_all_stages(case_payload, now=now)
        _reset_case_to_ceo_demand(case_payload, now=now, workspace_root=workspace_root)
    else:
        reset_stage_keys = _reset_stages_from(case_payload, rollback_target["stageKey"], now=now)
        case_payload["currentStageKey"] = ""
        case_payload["currentWorkItemPath"] = ""

    _append_event(
        case_payload["caseId"],
        "case-rolled-back",
        {
            "fromStageKey": previous_stage_key,
            "targetStageKey": rollback_target["stageKey"],
            "targetNodeKey": rollback_target["nodeKey"],
            "targetNodeType": rollback_target["kind"],
            "reason": str(reason).strip(),
            "resetStageKeys": reset_stage_keys,
        },
        workspace_root=workspace_root,
    )
    if rollback_target["kind"] != "ceo-demand":
        _activate_stage(case_payload, rollback_target["stageKey"], workspace_root=workspace_root, activated_at=now)
    case_payload["updatedAt"] = now
    _save_case(case_payload, workspace_root)
    summary = reconcile_ipd_case(case_payload["caseId"], workspace_root=workspace_root)
    summary.update(
        {
            "rollbackTargetStageKey": rollback_target["stageKey"],
            "rollbackTargetNodeKey": rollback_target["nodeKey"],
            "rollbackTargetNodeType": rollback_target["kind"],
            "rollbackReason": str(reason).strip(),
            "resetStageKeys": reset_stage_keys,
            "previousStageKey": previous_stage_key,
        }
    )
    return summary


def run_case_autopilot(
    case_id: str,
    *,
    workspace_root: str | None = None,
    tridev_root: str | None = None,
    enable_tridev_bridge: bool = True,
    strict_release_bundle: bool = True,
    auto_approve_roles: Iterable[str] = INTAKE_REQUIRED_APPROVERS,
) -> dict[str, Any]:
    normalized_case_id = _normalize_identifier(case_id)
    auto_approve_roles_set = set(_string_list(auto_approve_roles))
    if not auto_approve_roles_set:
        raise ValueError("auto_approve_roles must include at least one role")
    activity: list[dict[str, Any]] = []
    tridev_root_path: Path | None = None
    tridev_workflow: ModuleType | None = None
    tridev_run_id = _default_tridev_run_id(normalized_case_id)
    if enable_tridev_bridge:
        tridev_root_path = _resolve_tridev_root(workspace_root=workspace_root, tridev_root=tridev_root)
        tridev_workflow = _load_tridev_workflow_module(tridev_root_path)
        tridev_run_id = _ensure_tridev_run(
            case_id=normalized_case_id,
            case_payload=_load_case(normalized_case_id, workspace_root),
            tridev_workflow=tridev_workflow,
            tridev_root=tridev_root_path,
        )

    reconcile_ipd_case(normalized_case_id, workspace_root=workspace_root)
    max_iterations = max(len(_load_case(normalized_case_id, workspace_root)["stages"]), 1) * 8 + 16
    for _ in range(max_iterations):
        case_payload = _load_case(normalized_case_id, workspace_root)
        status = str(case_payload.get("status") or "").strip()
        if status == "completed":
            _append_event(
                normalized_case_id,
                "autopilot-completed",
                {
                    "activityCount": len(activity),
                    "tridevRunId": tridev_run_id if enable_tridev_bridge else "",
                },
                workspace_root=workspace_root,
            )
            return {
                "caseId": normalized_case_id,
                "status": status,
                "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
                "stageCount": len(case_payload["stages"]),
                "tridevBridgeEnabled": enable_tridev_bridge,
                "tridevRunId": tridev_run_id if enable_tridev_bridge else "",
                "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
                "actions": activity,
            }
        if status == "blocked":
            current_stage = _current_stage(case_payload)
            raise RuntimeError(
                "autopilot stopped because case is blocked"
                + (f" at stage {current_stage['stageKey']}" if current_stage else "")
            )
        if status == "paused-frozen":
            return _autopilot_frozen_pause_summary(
                case_payload=case_payload,
                case_status=status,
                activity=activity,
                tridev_root_path=tridev_root_path,
                tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                workspace_root=workspace_root,
            )
        if status == "paused-intake-clarification":
            return _autopilot_intake_clarification_pause_summary(
                case_payload=case_payload,
                case_status=status,
                activity=activity,
                tridev_root_path=tridev_root_path,
                tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                workspace_root=workspace_root,
            )
        if status == "awaiting-intake-approvals":
            role = _next_pending_approval_role(case_payload["intake"]["approvals"])
            if not role:
                raise RuntimeError("awaiting-intake-approvals but no pending intake approver")
            if role not in auto_approve_roles_set:
                return _autopilot_manual_pause_summary(
                    case_payload=case_payload,
                    case_status=status,
                    pending_role=role,
                    pending_stage_key="",
                    activity=activity,
                    tridev_root_path=tridev_root_path,
                    tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                    workspace_root=workspace_root,
                )
            result = record_intake_signoff(
                normalized_case_id,
                role=role,
                decision="approved",
                note=_AUTOPILOT_NOTE,
                workspace_root=workspace_root,
            )
            activity.append({"type": "intake-signoff", "role": role, "status": result["status"]})
            continue
        if status == "waiting-stage-output":
            stage = _current_stage(case_payload)
            if stage is None:
                raise RuntimeError("waiting-stage-output but no current stage")
            if _stage_requires_owner_action(stage):
                owner_action_package = _write_stage_owner_action_package(
                    case_payload,
                    stage,
                    workspace_root=workspace_root,
                        tridev_root=tridev_root_path,
                        tridev_run_id=tridev_run_id,
                )
                activity.append(
                    {
                        "type": "owner-action-package",
                        "stageKey": stage["stageKey"],
                        "ownerRole": stage["actingOwner"],
                        "reference": owner_action_package["reference"],
                    }
                )
                return _autopilot_owner_action_pause_summary(
                    case_payload=case_payload,
                    case_status=status,
                    pending_role=stage["actingOwner"],
                    pending_stage_key=stage["stageKey"],
                    owner_action_package_ref=owner_action_package["reference"],
                    activity=activity,
                    tridev_root_path=tridev_root_path,
                    tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                    workspace_root=workspace_root,
                )
            if _stage_requires_real_execution(stage["stageKey"]):
                return _autopilot_real_execution_pause_summary(
                    case_payload=case_payload,
                    case_status=status,
                    pending_stage_key=stage["stageKey"],
                    activity=activity,
                    tridev_root_path=tridev_root_path,
                    tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                    workspace_root=workspace_root,
                )
            submission = _build_autopilot_stage_submission(
                case_payload,
                stage,
                workspace_root=workspace_root,
                enable_tridev_bridge=enable_tridev_bridge,
                tridev_workflow=tridev_workflow,
                tridev_root=tridev_root_path,
                tridev_run_id=tridev_run_id,
                strict_release_bundle=strict_release_bundle,
            )
            result = submit_stage_output(
                normalized_case_id,
                stage_key=stage["stageKey"],
                submitted_by=stage["actingOwner"],
                summary=submission["summary"],
                details=submission["details"],
                evidence=submission["evidence"],
                object_path=submission["objectPath"],
                workspace_root=workspace_root,
            )
            activity.append(
                {
                    "type": "stage-submit",
                    "stageKey": stage["stageKey"],
                    "ownerRole": stage["actingOwner"],
                    "status": result["status"],
                }
            )
            continue
        if status == "awaiting-stage-approvals":
            stage = _current_stage(case_payload)
            if stage is None:
                raise RuntimeError("awaiting-stage-approvals but no current stage")
            role = _next_pending_approval_role(stage["approvals"])
            if not role:
                raise RuntimeError(f"awaiting-stage-approvals but no pending approver: {stage['stageKey']}")
            if role not in auto_approve_roles_set:
                return _autopilot_manual_pause_summary(
                    case_payload=case_payload,
                    case_status=status,
                    pending_role=role,
                    pending_stage_key=stage["stageKey"],
                    activity=activity,
                    tridev_root_path=tridev_root_path,
                    tridev_run_id=tridev_run_id if enable_tridev_bridge else "",
                    workspace_root=workspace_root,
                )
            result = record_stage_signoff(
                normalized_case_id,
                stage_key=stage["stageKey"],
                role=role,
                decision="approved",
                note=_AUTOPILOT_NOTE,
                workspace_root=workspace_root,
            )
            activity.append(
                {
                    "type": "stage-signoff",
                    "stageKey": stage["stageKey"],
                    "role": role,
                    "status": result["status"],
                }
            )
            continue

        summary = reconcile_ipd_case(normalized_case_id, workspace_root=workspace_root)
        activity.append({"type": "reconcile", "status": summary["status"], "advanced": summary["advanced"]})

    raise RuntimeError("autopilot exceeded maximum iteration limit")


def _reconcile_case_payload(
    case_payload: dict[str, Any],
    *,
    workspace_root: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    now = _timestamp_now()
    advanced = False
    integrity_issue = _find_real_execution_integrity_issue(case_payload, workspace_root=workspace_root)
    if integrity_issue is not None:
        _apply_real_execution_integrity_issue(
            case_payload,
            issue_stage_key=integrity_issue["stageKey"],
            issue_reason=integrity_issue["reason"],
            workspace_root=workspace_root,
            now=now,
        )
        case_payload["updatedAt"] = now
        return case_payload, _summary_for_case(case_payload, advanced=False, workspace_root=workspace_root)
    freeze_control = _normalize_freeze_control(case_payload.get("freezeControl"))
    case_payload["freezeControl"] = freeze_control
    if freeze_control.get("active"):
        current_stage = _current_stage(case_payload)
        if current_stage is not None:
            current_stage["status"] = "frozen"
            if not str(current_stage.get("blockedReason") or "").strip():
                current_stage["blockedReason"] = str(freeze_control.get("reason") or "").strip()
            current_stage["lastUpdatedAt"] = now
        case_payload["status"] = "paused-frozen"
        case_payload["updatedAt"] = now
        return case_payload, _summary_for_case(case_payload, advanced=False, workspace_root=workspace_root)
    intake_status = _approval_rollup(case_payload["intake"]["approvals"])
    case_payload["intake"]["status"] = intake_status
    current_stage = _current_stage(case_payload)

    if current_stage is None:
        if intake_status == "rejected":
            case_payload["status"] = "blocked"
        elif intake_status != "approved":
            case_payload["status"] = "awaiting-intake-approvals"
        elif not _intake_clarification_ready(case_payload["intake"]):
            case_payload["status"] = "paused-intake-clarification"
        else:
            next_stage = _next_pending_stage(case_payload)
            if next_stage is None:
                case_payload["status"] = "completed"
            else:
                _activate_stage(case_payload, next_stage["stageKey"], workspace_root=workspace_root, activated_at=now)
                advanced = True
    else:
        if current_stage["status"] == "submitted":
            stage_approval_status = _approval_rollup(current_stage["approvals"])
            if stage_approval_status == "rejected":
                current_stage["status"] = "rejected"
                current_stage["blockedReason"] = "节点签核被拒绝，等待责任岗位重新提交。"
                case_payload["status"] = "blocked"
            elif stage_approval_status == "approved":
                current_stage["status"] = "completed"
                current_stage["completedAt"] = now
                current_stage["blockedReason"] = ""
                case_payload["currentStageKey"] = ""
                case_payload["currentWorkItemPath"] = ""
                next_stage = _next_pending_stage(case_payload)
                if next_stage is None:
                    case_payload["status"] = "completed"
                else:
                    _activate_stage(case_payload, next_stage["stageKey"], workspace_root=workspace_root, activated_at=now)
                    advanced = True
            else:
                case_payload["status"] = "awaiting-stage-approvals"
        elif current_stage["status"] == "rejected":
            case_payload["status"] = "blocked"
        elif current_stage["status"] == "frozen":
            case_payload["status"] = "paused-frozen"
        elif current_stage["status"] == "in-progress":
            case_payload["status"] = "waiting-stage-output"
        elif current_stage["status"] == "completed":
            case_payload["currentStageKey"] = ""
            case_payload["currentWorkItemPath"] = ""
            next_stage = _next_pending_stage(case_payload)
            if next_stage is None:
                case_payload["status"] = "completed"
            else:
                _activate_stage(case_payload, next_stage["stageKey"], workspace_root=workspace_root, activated_at=now)
                advanced = True

    case_payload["updatedAt"] = now
    return case_payload, _summary_for_case(case_payload, advanced=advanced, workspace_root=workspace_root)


def _activate_stage(
    case_payload: dict[str, Any],
    stage_key: str,
    *,
    workspace_root: str | None,
    activated_at: str,
) -> None:
    stage = _require_stage(case_payload, stage_key)
    stage["status"] = "in-progress"
    stage["activatedAt"] = activated_at
    stage["blockedReason"] = ""
    stage["requiredApprovers"] = _stage_required_approvers(stage["actingOwner"])
    stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
    stage["lastUpdatedAt"] = activated_at
    _seed_stage_supporting_artifacts(case_payload, stage, workspace_root=workspace_root, written_at=activated_at)
    work_item_path = _write_stage_work_item(case_payload, stage, workspace_root=workspace_root, written_at=activated_at)
    stage["workItemPath"] = work_item_path.as_posix()
    case_payload["currentStageKey"] = stage_key
    case_payload["currentWorkItemPath"] = work_item_path.as_posix()
    case_payload["status"] = "waiting-stage-output"
    _append_event(
        case_payload["caseId"],
        "stage-activated",
        {
            "stageKey": stage_key,
            "ownerRole": stage["actingOwner"],
            "workItemPath": work_item_path.as_posix(),
        },
        workspace_root=workspace_root,
    )


def _write_stage_work_item(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
    written_at: str,
) -> Path:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    work_items_root = case_root / "work-items"
    work_items_root.mkdir(parents=True, exist_ok=True)
    path = work_items_root / f"{_stage_index_for_case(case_payload, stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-stage-work-item",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "title": f"{case_payload['title']} / {stage['title']}",
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
        "status": stage["status"],
        "createdAt": written_at,
        "updatedAt": written_at,
        "priority": case_payload["priority"],
        "summary": _stage_summary(case_payload, stage),
        "intake": {
            "objective": case_payload["intake"]["objective"],
            "taskDescription": case_payload["intake"]["taskDescription"],
            "caseCategory": case_payload["intake"]["caseCategory"],
            "referenceTheme": case_payload["intake"]["referenceTheme"],
            "constraints": list(case_payload["intake"]["constraints"]),
            "opportunitySignals": list(case_payload["intake"]["opportunitySignals"]),
            "businessModelFit": list(case_payload["intake"]["businessModelFit"]),
            "stageFit": list(case_payload["intake"]["stageFit"]),
            "companyContext": list(case_payload["intake"]["companyContext"]),
            "ownerProposal": list(case_payload["intake"]["ownerProposal"]),
            "resourceEnvelope": list(case_payload["intake"]["resourceEnvelope"]),
            "prerequisites": list(case_payload["intake"]["prerequisites"]),
            "requiredSupport": list(case_payload["intake"]["requiredSupport"]),
            "expectedOutcomes": list(case_payload["intake"]["expectedOutcomes"]),
            "expectedDelivery": case_payload["intake"]["expectedDelivery"],
            "briefPath": case_payload["intake"]["briefPath"],
            "clarificationSheet": dict(case_payload["intake"]["clarificationSheet"]),
        },
        "roleAssignmentMatrix": _stage_role_assignment_matrix(stage["stageKey"]),
        "requiredApprovers": list(stage["requiredApprovers"]),
        "relatedModules": list(case_payload["relatedModules"]),
        "inputRefs": _input_refs(case_payload),
        "inputRequirements": list(stage.get("inputRequirements", [])),
        "outputRequirements": list(_stage_template(stage["stageKey"])["outputRequirements"]),
        "superDevReferenceStages": list(stage.get("superDevReferenceStages", [])),
        "schemaHint": dict(stage["schemaHint"]),
        "draftTemplate": _draft_template(case_payload, stage, written_at=written_at),
    }
    standard_flow = _stage_standard_flow(case_payload, stage)
    if standard_flow:
        payload["standardFlow"] = standard_flow
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_stage_output(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    summary: str,
    details: Iterable[str],
    evidence: Iterable[str],
    object_path: str,
    workspace_root: str | None,
    written_at: str,
) -> Path:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    outputs_root = case_root / "outputs"
    outputs_root.mkdir(parents=True, exist_ok=True)
    path = outputs_root / f"{_stage_index_for_case(case_payload, stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    payload = _build_stage_output_core_payload(
        case_payload,
        stage,
        summary=summary,
        details=details,
        evidence=evidence,
        object_path=object_path,
        written_at=written_at,
    )
    stage["packageHash"] = _package_hash(payload)
    payload["packageHash"] = stage["packageHash"]
    payload["signaturePolicy"] = _signature_policy_payload(stage["requiredApprovers"], subject_kind="stage-output")
    payload["signatureChain"] = _approval_signature_chain(stage["approvals"])
    payload["release"] = _release_metadata(stage)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _build_stage_output_core_payload(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    summary: str,
    details: Iterable[str],
    evidence: Iterable[str],
    object_path: str,
    written_at: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-stage-output",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
        "submittedAt": written_at,
        "summary": summary.strip(),
        "details": _string_list(details),
        "evidence": _string_list(evidence),
        "objectPath": object_path.strip(),
    }


def _sync_stage_output_metadata(stage: dict[str, Any], *, workspace_root: str | None) -> None:
    output_path_text = str(stage.get("outputPath") or "").strip()
    if not output_path_text:
        return
    output_path = _resolve_workspace_artifact_path(output_path_text, workspace_root)
    if not output_path.exists():
        return
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    payload["packageHash"] = str(stage.get("packageHash") or "").strip()
    payload["signaturePolicy"] = _signature_policy_payload(stage.get("requiredApprovers", ()), subject_kind="stage-output")
    payload["signatureChain"] = _approval_signature_chain(stage.get("approvals", []))
    payload["release"] = _release_metadata(stage)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_stage_package_hash(stage: dict[str, Any], *, workspace_root: str | None) -> str:
    package_hash = str(stage.get("packageHash") or "").strip()
    if package_hash:
        return package_hash
    output_path_text = str(stage.get("outputPath") or "").strip()
    if not output_path_text:
        return ""
    output_path = _resolve_workspace_artifact_path(output_path_text, workspace_root)
    if not output_path.exists():
        return ""
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return str(payload.get("packageHash") or "").strip()


def _draft_template(case_payload: dict[str, Any], stage: dict[str, Any], *, written_at: str) -> dict[str, Any]:
    stage_key = stage["stageKey"]
    payload = {
        "kind": "ipd-engine-native-draft",
        "objectType": stage["schemaHint"]["objectType"],
        "phaseKey": stage["phaseKey"],
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
        "summary": _stage_summary(case_payload, stage),
        "inputRequirements": list(stage.get("inputRequirements", [])),
        "requiredOutput": list(_stage_template(stage_key)["outputRequirements"]),
        "superDevReferenceStages": list(stage.get("superDevReferenceStages", [])),
        "workflowRefs": [
            {
                "relation": "phase-package-for",
                "phase": stage["phaseKey"],
                "runId": f"run-{case_payload['caseId']}",
                "branchId": _branch_id(case_payload["caseId"]),
            }
        ],
    }
    standard_flow = _stage_standard_flow(case_payload, stage)
    if standard_flow:
        payload["standardFlow"] = standard_flow
    template_fields = _stage_template(stage_key).get("templateFields")
    if template_fields:
        payload["templateFields"] = _materialize_stage_template(template_fields, case_id=case_payload["caseId"])
    scorecard_schema = _stage_template(stage_key).get("scorecardSchema")
    if scorecard_schema:
        payload["scorecardSchema"] = _materialize_stage_template(scorecard_schema, case_id=case_payload["caseId"])
    return payload


def _materialize_stage_template(value: Any, *, case_id: str) -> Any:
    if isinstance(value, str):
        return value.format(caseId=case_id)
    if isinstance(value, tuple):
        return [_materialize_stage_template(item, case_id=case_id) for item in value]
    if isinstance(value, list):
        return [_materialize_stage_template(item, case_id=case_id) for item in value]
    if isinstance(value, dict):
        return {key: _materialize_stage_template(item, case_id=case_id) for key, item in value.items()}
    return value


def _stage_standard_flow(case_payload: dict[str, Any], stage: dict[str, Any]) -> dict[str, Any]:
    standard_flow = _stage_template(stage["stageKey"]).get("standardFlow")
    if not standard_flow:
        return {}
    return _materialize_stage_template(standard_flow, case_id=case_payload["caseId"])


def _stage_submission_template(case_payload: dict[str, Any], stage: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "submittedBy": stage["actingOwner"],
        "summary": f"{stage['title']} 已提交",
        "details": ["<detail>"],
        "evidence": ["<evidence-path>"],
        "objectPath": "<primary-output-object-path>",
    }
    stage_submission_template = _stage_template(stage["stageKey"]).get("submissionTemplate") or {}
    if stage_submission_template:
        details = stage_submission_template.get("details")
        evidence = stage_submission_template.get("evidence")
        if details:
            payload["details"] = _materialize_stage_template(details, case_id=case_payload["caseId"])
        if evidence:
            payload["evidence"] = _materialize_stage_template(evidence, case_id=case_payload["caseId"])
    return payload


def _seed_stage_supporting_artifacts(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
    written_at: str,
) -> None:
    standard_flow = _stage_standard_flow(case_payload, stage)
    if not standard_flow:
        return
    catalog_path = str(standard_flow.get("catalogPath") or "").strip()
    if catalog_path:
        _seed_stage_reference_catalog(case_payload, stage, catalog_path=catalog_path, workspace_root=workspace_root, written_at=written_at)
    for document in _stage_markdown_documents(standard_flow):
        path = str(document.get("path") or "").strip()
        if not path:
            continue
        _seed_stage_markdown_document(
            case_payload,
            stage,
            document=document,
            workspace_root=workspace_root,
            written_at=written_at,
        )


def _stage_markdown_documents(standard_flow: dict[str, Any]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for key in ("summaryDocument", "analysisDocument"):
        document = standard_flow.get(key)
        if isinstance(document, dict) and str(document.get("path") or "").strip():
            documents.append(document)
    for document in standard_flow.get("packageDocuments", []):
        if isinstance(document, dict) and str(document.get("path") or "").strip():
            documents.append(document)
    return documents


def _seed_stage_reference_catalog(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    catalog_path: str,
    workspace_root: str | None,
    written_at: str,
) -> None:
    path = _resolve_workspace_artifact_path(catalog_path, workspace_root)
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": f"ipd-{stage['stageKey']}-reference-source-catalog",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "generatedAt": written_at,
        "sources": [],
        "notes": [
            f"本文件由 {stage['stageKey']} 阶段激活时自动生成。",
            "请在后续研究中持续补齐来源、官方性、锚点位置和用途说明。",
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _seed_stage_markdown_document(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    document: dict[str, Any],
    workspace_root: str | None,
    written_at: str,
) -> None:
    path = _resolve_workspace_artifact_path(str(document.get("path") or ""), workspace_root)
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _render_stage_markdown_document(case_payload, stage, document=document, written_at=written_at),
        encoding="utf-8",
    )


def _render_stage_markdown_document(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    document: dict[str, Any],
    written_at: str,
) -> str:
    stage_key = stage["stageKey"]
    document_name = str(document.get("name") or "").strip()
    if stage_key == "discovery":
        return _render_discovery_markdown_document(case_payload, document_name=document_name, written_at=written_at)
    if stage_key == "intelligence":
        return _render_intelligence_markdown_document(case_payload, document_name=document_name, written_at=written_at)
    title = document_name or stage["title"]
    return (
        f"# {title}\n\n"
        f"Case ID: {case_payload['caseId']}\n"
        f"Stage: {stage['stageKey']}\n"
        f"Generated At: {written_at}\n\n"
        "本文件由 runtime 在阶段激活时自动生成，请按当前阶段要求持续补齐。\n"
    )


def _render_discovery_markdown_document(case_payload: dict[str, Any], *, document_name: str, written_at: str) -> str:
    intake = case_payload["intake"]
    competitor_reference = _slot_answer(case_payload, "competitorReference", default="待补竞品名单")
    target_user_scenario = _slot_answer(case_payload, "targetUserScenario", default="待补目标用户与使用场景")
    success_metric = _slot_answer(case_payload, "successMetric", default="待补首轮成功信号")
    task_description = intake["taskDescription"]
    objective = intake["objective"]
    if document_name == "DiscoveryCompetitorLandscape":
        body = (
            "## 1. 对标对象\n\n"
            f"当前总助已明确的对标入口：{competitor_reference}\n\n"
            "## 2. 竞品与官方手册登记表\n\n"
            "| 对标对象 | 官方入口 | 手册 / README | 核心功能 | 差异点 | 当前判断 |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| 待补 | 待补 | 待补 | 待补 | 待补 | 待补 |\n\n"
            "## 3. 搜索要求\n\n"
            "1. 优先官网、官方 docs、官方 README、API 手册、功能页、定价页。\n"
            "2. 同一个竞品至少保留一个官方入口和一个可复核手册入口。\n"
            "3. 把对后续 Intelligence 有价值的关键词和模块名称写到备注里。\n"
        )
    elif document_name == "DiscoveryCommonCapabilityMatrix":
        body = (
            "## 1. 共性功能矩阵\n\n"
            "| 功能主题 | 竞品共性做法 | 输入 / 输出 | 适用当前项目的原因 | 待验证点 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 待补 | 待补 | 待补 | 待补 | 待补 |\n\n"
            "## 2. 使用要求\n\n"
            "1. 不只列功能名，要把输入、输出和边界写清。\n"
            "2. 至少区分必须保留的共性能力、可后置能力和当前不做项。\n"
            f"3. 当前成功信号：{success_metric}。\n"
        )
    elif document_name == "DiscoveryHighlightOpportunityMemo":
        body = (
            "## 1. 亮点功能候选\n\n"
            "| 亮点功能 | 来源竞品 / 手册 | 为什么值得跟进 | 当前风险 | 是否进入 Intelligence 深挖 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 待补 | 待补 | 待补 | 待补 | 待补 |\n\n"
            "## 2. 判断原则\n\n"
            "1. 亮点功能必须和当前任务目标直接相关，而不是单纯抄功能清单。\n"
            "2. 优先记录能改变体验、成本、控制面能力或后续商业化可能性的点。\n"
        )
    else:
        body = (
            "## 1. 当前任务边界\n\n"
            f"- Objective: {objective}\n"
            f"- Task: {task_description}\n"
            f"- Target User Scenario: {target_user_scenario}\n"
            f"- Competitor Reference: {competitor_reference}\n"
            f"- Success Metric: {success_metric}\n\n"
            "## 2. Discovery 自动工作要求\n\n"
            "1. 搜索竞品、官方手册、官方功能页和相关公开说明。\n"
            "2. 完成竞品 landscape、共性功能矩阵和亮点功能 memo。\n"
            "3. 给 Intelligence 留下明确的开源代码搜索问题与关键词。\n\n"
            "## 3. 当前待验证问题\n\n"
            "- 哪些功能是所有竞品都会做的共性能力？\n"
            "- 哪些亮点功能值得进入 Intelligence 深挖其实现路线？\n"
            "- 哪些看起来像功能，但实际应被明确列为 out-of-scope？\n"
        )
    return (
        f"# {document_name or 'DiscoveryPackageDocument'}\n\n"
        f"Case ID: {case_payload['caseId']}\n"
        "Stage: discovery\n"
        f"Generated At: {written_at}\n"
        "Owner: ChiefProductOfficer\n\n"
        f"总助指示：{task_description}\n\n"
        f"{body}"
    )


def _render_intelligence_markdown_document(case_payload: dict[str, Any], *, document_name: str, written_at: str) -> str:
    intake = case_payload["intake"]
    objective = intake["objective"]
    task_description = intake["taskDescription"]
    competitor_reference = _slot_answer(case_payload, "competitorReference", default="待补")
    if document_name == "IntelligenceOpenSourceLandscape":
        body = (
            "## 1. 开源代码与公开资料登记表\n\n"
            "| 项目 / 资料 | 仓库 / 文档入口 | 对应功能 | 参考价值 | 深读优先级 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 待补 | 待补 | 待补 | 待补 | 待补 |\n\n"
            "## 2. 研究要求\n\n"
            "1. 先消费上一阶段 DiscoveryReferenceFunctionalBrief 与亮点功能 memo。\n"
            "2. 同时登记开源仓库和公开技术资料，不把 Intelligence 收窄成只看代码。\n"
            "3. 对每个候选项目写清它对应的是共性功能还是亮点功能。\n"
        )
    elif document_name == "IntelligenceCodegraphAnalysis":
        body = (
            "## 1. CodeGraph 深读记录\n\n"
            "| 代码参考 | 模块 / 入口 | 关键调用链 | 对应需求 | 当前结论 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 待补 | 待补 | 待补 | 待补 | 待补 |\n\n"
            "## 2. 说明\n\n"
            "1. 如宿主已挂载 CodeGraph，优先记录 symbol、调用链和 impact 结论。\n"
            "2. 如当前 host 暂未挂载 CodeGraph，先记录待建索引动作和结构化阅读范围，后续补回真实图谱结论。\n"
        )
    elif document_name == "IntelligenceArchitectureOptionMemo":
        body = (
            "## 1. 架构选型候选\n\n"
            "| 功能主题 | 候选实现路线 | 参考来源 | 优点 | 风险 / 代价 | 首轮建议 |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| 待补 | 待补 | 待补 | 待补 | 待补 | 待补 |\n\n"
            "## 2. 实现思路\n\n"
            "1. 先分共性功能和亮点功能。\n"
            "2. 对亮点功能至少给出一条可执行的最小实现思路和一条后置路线。\n"
            "3. 不把上游仓库结构直接等同于我们的最终架构。\n"
        )
    else:
        body = (
            "## 1. Capability Extraction Matrix\n\n"
            "| 能力主题 | 参考项目 / 资料 | 当前实现信号 | 纳入 / 后置 / 排除 | 备注 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 待补 | 待补 | 待补 | 待补 | 待补 |\n\n"
            "## 2. Intelligence 自动工作要求\n\n"
            "1. 根据上一阶段资料搜索相关开源代码和公开技术资料。\n"
            "2. 对关键代码参考做 CodeGraph 深读，并沉淀结构化实现判断。\n"
            "3. 总结共性功能与亮点功能的架构选型和实现思路，供 CPO 收口 PRD。\n"
        )
    return (
        f"# {document_name or 'IntelligencePackageDocument'}\n\n"
        f"Case ID: {case_payload['caseId']}\n"
        "Stage: intelligence\n"
        f"Generated At: {written_at}\n"
        "Owner: ChiefProductOfficer / ChiefTechnologyOfficer\n\n"
        f"Objective: {objective}\n"
        f"Discovery Competitor Reference: {competitor_reference}\n"
        f"总助指示：{task_description}\n\n"
        f"{body}"
    )


def _slot_answer(case_payload: dict[str, Any], slot_key: str, *, default: str = "") -> str:
    value = str((case_payload.get("intake") or {}).get("slotAnswers", {}).get(slot_key) or "").strip()
    return value or default


def _resolve_workspace_artifact_path(path_text: str, workspace_root: str | None) -> Path:
    normalized = str(path_text or "").strip().replace("\\", "/")
    if not normalized:
        raise ValueError("artifact path is required")
    root = Path(workspace_root).resolve() if workspace_root is not None else Path(__file__).resolve().parents[2]
    if normalized.startswith("TriMetaverse/"):
        suffix = normalized.split("/", 1)[1]
        if root.name == "TriMetaverse":
            base = root
        elif (root / "TriMetaverse").exists():
            base = root / "TriMetaverse"
        elif (root.parent / "TriMetaverse").exists():
            base = root.parent / "TriMetaverse"
        else:
            base = root / "TriMetaverse"
        return base / suffix
    if normalized.startswith("TriCompany/"):
        suffix = normalized.split("/", 1)[1]
        return source_root(root) / suffix
    return root / Path(normalized)


def _write_stage_reference_catalog(catalog_ref: str, payload: dict[str, Any], *, workspace_root: str | None) -> None:
    path = _resolve_workspace_artifact_path(catalog_ref, workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_discovery_documents(
    case_payload: dict[str, Any],
    *,
    standard_flow: dict[str, Any],
    sources: list[dict[str, Any]],
    written_at: str,
    workspace_root: str | None,
) -> list[str]:
    capability_rows = _build_discovery_capability_rows(sources)
    highlight_rows = _build_discovery_highlight_rows(sources)
    intelligence_questions = _build_discovery_intelligence_questions(sources)
    document_texts = {
        str(standard_flow["summaryDocument"]["path"]): _render_discovery_functional_brief(
            case_payload,
            sources=sources,
            capability_rows=capability_rows,
            intelligence_questions=intelligence_questions,
            written_at=written_at,
        ),
        str(standard_flow["packageDocuments"][0]["path"]): _render_discovery_competitor_landscape(
            case_payload,
            sources=sources,
            written_at=written_at,
        ),
        str(standard_flow["packageDocuments"][1]["path"]): _render_discovery_common_capability_matrix(
            case_payload,
            capability_rows=capability_rows,
            written_at=written_at,
        ),
        str(standard_flow["packageDocuments"][2]["path"]): _render_discovery_highlight_opportunity_memo(
            case_payload,
            highlight_rows=highlight_rows,
            written_at=written_at,
        ),
    }
    for ref, text in document_texts.items():
        path = _resolve_workspace_artifact_path(ref, workspace_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return list(document_texts.keys())


def _write_intelligence_documents(
    case_payload: dict[str, Any],
    *,
    standard_flow: dict[str, Any],
    sources: list[dict[str, Any]],
    codegraph_reports: list[dict[str, Any]],
    written_at: str,
    workspace_root: str | None,
) -> list[str]:
    capability_rows = _build_intelligence_capability_rows(sources)
    architecture_rows = _build_intelligence_architecture_rows(sources)
    document_texts = {
        str(standard_flow["analysisDocument"]["path"]): _render_intelligence_capability_extraction_matrix(
            case_payload,
            capability_rows=capability_rows,
            written_at=written_at,
        ),
        str(standard_flow["packageDocuments"][0]["path"]): _render_intelligence_opensource_landscape(
            case_payload,
            sources=sources,
            written_at=written_at,
        ),
        str(standard_flow["packageDocuments"][1]["path"]): _render_intelligence_codegraph_analysis(
            case_payload,
            codegraph_reports=codegraph_reports,
            written_at=written_at,
        ),
        str(standard_flow["packageDocuments"][2]["path"]): _render_intelligence_architecture_option_memo(
            case_payload,
            architecture_rows=architecture_rows,
            written_at=written_at,
        ),
    }
    for ref, text in document_texts.items():
        path = _resolve_workspace_artifact_path(ref, workspace_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return list(document_texts.keys())


def _build_discovery_sources(case_payload: dict[str, Any]) -> list[dict[str, Any]]:
    targets = _extract_reference_targets(_slot_answer(case_payload, "competitorReference", default=""))
    sources: list[dict[str, Any]] = []
    for target in targets:
        seed = _find_discovery_seed(target)
        if seed is None:
            sources.append(
                {
                    "sourceId": "manual-" + _normalize_search_key(target).replace(" ", "-"),
                    "name": target,
                    "category": "manual-to-confirm",
                    "official": False,
                    "productUrl": "",
                    "sourceUrl": "",
                    "captureStatus": "needs-manual-confirmation",
                    "intendedUse": "该对标对象未命中内置发现种子，需要补官方入口与手册链接。",
                    "focusAreas": ["待补官方来源", "待补功能边界"],
                }
            )
            continue
        sources.append(
            {
                key: value
                for key, value in seed.items()
                if key not in {"aliases", "commonCapabilities", "highlightFeatures", "differences", "intelligenceQuestions"}
            }
        )
    sources.extend(_build_discovery_project_boundary_sources(case_payload))
    if not sources:
        sources.append(
            {
                "sourceId": "manual-discovery-target",
                "name": "待补 Discovery 对标对象",
                "category": "manual-to-confirm",
                "official": False,
                "productUrl": "",
                "sourceUrl": "",
                "captureStatus": "needs-manual-confirmation",
                "intendedUse": "当前 case 未提供明确 competitorReference，需要总助或 CPO 先补名单。",
                "focusAreas": ["待补对标对象", "待补官方手册"],
            }
        )
    return sources


def _build_discovery_project_boundary_sources(case_payload: dict[str, Any]) -> list[dict[str, Any]]:
    intake = case_payload.get("intake", {}) if isinstance(case_payload.get("intake"), dict) else {}
    if str(intake.get("caseCategory") or "").strip() != _CASE_CATEGORY_PROJECT_DELIVERY:
        return []
    if not str(intake.get("referenceTheme") or "").strip().upper().startswith("PLATFORM"):
        return []

    objective_text = _normalize_search_key(str(intake.get("objective") or ""))
    task_text = _normalize_search_key(str(intake.get("taskDescription") or ""))
    scope_text = _normalize_search_key(str((intake.get("slotAnswers") or {}).get("mustHaveScope") or ""))
    combined_text = " ".join(part for part in (objective_text, task_text, scope_text) if part)
    if "triavatar" not in combined_text and "tristaciss" not in combined_text:
        return []

    boundary_sources: list[dict[str, Any]] = []
    if "triavatar" in combined_text:
        boundary_sources.append(
            {
                "sourceId": "triavatar-readme",
                "name": "TriAvatar README",
                "category": "internal-module",
                "official": True,
                "productUrl": "TriAvatar/README.md",
                "sourceUrl": "TriAvatar/README.md",
                "captureStatus": "workspace-verified",
                "intendedUse": "确认当前现役 Web 前端入口落在 TriAvatar，且保留原有功能可用是首轮边界。",
                "focusAreas": ["web entry", "frontend scope", "existing pages and routes", "backend integration via VITE_API_URL"],
            }
        )
    if "tristaciss" in combined_text:
        boundary_sources.append(
            {
                "sourceId": "tristaciss-phase-c-design",
                "name": "Tristaciss Phase C ingress design",
                "category": "internal-module",
                "official": True,
                "productUrl": "TriStaciss/docs/tristaciss-openai-ingress-phase-c-design.md",
                "sourceUrl": "TriStaciss/docs/tristaciss-openai-ingress-phase-c-design.md",
                "captureStatus": "workspace-verified",
                "intendedUse": "确认 Tristaciss 当前后端 ingress 主线、legacy adapter 方向和模型 API 转接平台技术边界。",
                "focusAreas": ["OpenAI-compatible ingress", "legacy adapter strategy", "provider routing", "backend platform boundary"],
            }
        )
    return boundary_sources


def _validate_discovery_seeded_competitor_coverage(
    case_payload: dict[str, Any],
    *,
    catalog_ref: str,
    summary_ref: str,
    landscape_ref: str,
    workspace_root: str | None,
) -> None:
    required_targets = _extract_reference_targets(_slot_answer(case_payload, "competitorReference", default=""))
    if not required_targets:
        return

    catalog_path = _resolve_workspace_artifact_path(catalog_ref, workspace_root)
    summary_path = _resolve_workspace_artifact_path(summary_ref, workspace_root)
    landscape_path = _resolve_workspace_artifact_path(landscape_ref, workspace_root)

    catalog_payload = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
    source_names = {
        _normalize_search_key(str(entry.get("name") or ""))
        for entry in catalog_payload.get("sources", [])
        if isinstance(entry, dict)
    }
    normalized_summary = _normalize_search_key(summary_path.read_text(encoding="utf-8") if summary_path.exists() else "")
    normalized_landscape = _normalize_search_key(landscape_path.read_text(encoding="utf-8") if landscape_path.exists() else "")

    missing_in_catalog: list[str] = []
    missing_in_summary: list[str] = []
    missing_in_landscape: list[str] = []
    for target in required_targets:
        normalized_target = _normalize_search_key(target)
        if normalized_target not in source_names:
            missing_in_catalog.append(target)
        if normalized_target not in normalized_summary:
            missing_in_summary.append(target)
        if normalized_target not in normalized_landscape:
            missing_in_landscape.append(target)

    if not (missing_in_catalog or missing_in_summary or missing_in_landscape):
        return

    issues: list[str] = []
    if missing_in_catalog:
        issues.append("catalog missing: " + ", ".join(missing_in_catalog))
    if missing_in_summary:
        issues.append("brief missing: " + ", ".join(missing_in_summary))
    if missing_in_landscape:
        issues.append("landscape missing: " + ", ".join(missing_in_landscape))
    raise ValueError("discovery seeded competitor carry-forward validation failed: " + "; ".join(issues))


def _build_intelligence_sources(case_payload: dict[str, Any]) -> list[dict[str, Any]]:
    theme = _case_reference_theme(case_payload)
    discovery_targets = _extract_reference_targets(_slot_answer(case_payload, "competitorReference", default=""))
    normalized_discovery_targets = {_normalize_search_key(target) for target in discovery_targets}
    sources: list[dict[str, Any]] = []
    for seed in _INTELLIGENCE_SOURCE_SEEDS:
        aliases = {_normalize_search_key(alias) for alias in seed.get("aliases", ())}
        themes = {str(item).upper() for item in seed.get("themes", ())}
        if theme in themes or aliases.intersection(normalized_discovery_targets):
            sources.append(
                {
                    key: value
                    for key, value in seed.items()
                    if key not in {"aliases", "themes", "capabilityCandidates", "architectureOptions"}
                }
            )
    if not sources:
        sources.append(
            {
                "sourceId": "manual-intelligence-target",
                "name": "待补 Intelligence 代码参考",
                "category": "manual-to-confirm",
                "sourceUrl": "",
                "anchorFiles": [],
                "intendedUse": "当前 case 尚未命中内置开源代码种子，需要 CTO 补充代码参考。",
                "focusAreas": ["待补开源代码", "待补公开技术资料"],
                "captureStatus": "needs-manual-confirmation",
            }
        )
    return sources


def _extract_reference_targets(value: str) -> list[str]:
    raw_targets = re.split(r"[、，,;；/|]+", str(value or ""))
    targets: list[str] = []
    for item in raw_targets:
        text = str(item or "").strip()
        if text and text not in targets:
            targets.append(text)
    return targets


def _normalize_search_key(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[-_]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _find_discovery_seed(target: str) -> dict[str, Any] | None:
    normalized = _normalize_search_key(target)
    for seed in _DISCOVERY_SOURCE_SEEDS:
        aliases = {_normalize_search_key(alias) for alias in seed.get("aliases", ())}
        if normalized in aliases:
            return seed
    return None


def _case_short_name(case_id: str) -> str:
    parts = [part for part in str(case_id or "").split("-") if part]
    if len(parts) < 4:
        return "CASE"
    return "-".join(parts[2:-1]).upper()


def _normalize_case_category(value: str, *, case_id: str) -> str:
    normalized = str(value or "").strip().lower().replace("_", "-")
    aliases = {
        "process": _CASE_CATEGORY_PROCESS_IMPROVEMENT,
        "process-improvement": _CASE_CATEGORY_PROCESS_IMPROVEMENT,
        "workflow-improvement": _CASE_CATEGORY_PROCESS_IMPROVEMENT,
        "ipd-improvement": _CASE_CATEGORY_PROCESS_IMPROVEMENT,
        "project": _CASE_CATEGORY_PROJECT_DELIVERY,
        "project-delivery": _CASE_CATEGORY_PROJECT_DELIVERY,
        "delivery": _CASE_CATEGORY_PROJECT_DELIVERY,
    }
    if normalized in aliases:
        return aliases[normalized]
    if _case_short_name(case_id) in _PROCESS_IMPROVEMENT_REFERENCE_THEMES:
        return _CASE_CATEGORY_PROCESS_IMPROVEMENT
    return _CASE_CATEGORY_PROJECT_DELIVERY


def _normalize_reference_theme(value: str, *, case_id: str, case_category: str) -> str:
    normalized = str(value or "").strip().upper().replace("_", "-")
    normalized = re.sub(r"[^A-Z0-9-]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if normalized:
        return normalized
    short_name = _case_short_name(case_id)
    if short_name != "CASE":
        return short_name
    if case_category == _CASE_CATEGORY_PROCESS_IMPROVEMENT:
        return "WORKFLOW"
    return ""


def _case_reference_theme(case_payload: dict[str, Any]) -> str:
    intake = case_payload.get("intake") if isinstance(case_payload.get("intake"), dict) else {}
    case_id = str(case_payload.get("caseId") or "")
    case_category = _normalize_case_category(str(intake.get("caseCategory") or ""), case_id=case_id)
    return _normalize_reference_theme(
        str(intake.get("referenceTheme") or ""),
        case_id=case_id,
        case_category=case_category,
    )


def _seed_discovery_metadata(source_name: str) -> dict[str, Any]:
    seed = _find_discovery_seed(source_name)
    if seed is None:
        return {
            "commonCapabilities": (),
            "highlightFeatures": (),
            "differences": {},
            "intelligenceQuestions": (),
        }
    return {
        "commonCapabilities": seed.get("commonCapabilities", ()),
        "highlightFeatures": seed.get("highlightFeatures", ()),
        "differences": seed.get("differences", {}),
        "intelligenceQuestions": seed.get("intelligenceQuestions", ()),
    }


def _build_discovery_capability_rows(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for source in sources:
        metadata = _seed_discovery_metadata(str(source.get("name") or ""))
        for item in metadata["commonCapabilities"]:
            key = str(item.get("name") or "").strip()
            if not key:
                continue
            row = rows.setdefault(
                key,
                {
                    "name": key,
                    "inputOutput": str(item.get("inputOutput") or ""),
                    "reason": str(item.get("reason") or ""),
                    "sources": [],
                },
            )
            row["sources"].append(str(source.get("name") or ""))
    return list(rows.values())


def _build_discovery_highlight_rows(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in sources:
        metadata = _seed_discovery_metadata(str(source.get("name") or ""))
        for item in metadata["highlightFeatures"]:
            rows.append(
                {
                    "name": str(item.get("name") or "").strip(),
                    "source": str(source.get("name") or "").strip(),
                    "why": str(item.get("why") or "").strip(),
                    "risk": str(item.get("risk") or "").strip(),
                }
            )
    return rows


def _build_discovery_intelligence_questions(sources: list[dict[str, Any]]) -> list[str]:
    questions: list[str] = []
    for source in sources:
        metadata = _seed_discovery_metadata(str(source.get("name") or ""))
        for question in metadata["intelligenceQuestions"]:
            text = str(question or "").strip()
            if text and text not in questions:
                questions.append(text)
    if not questions:
        questions.append("需要进一步补齐 Intelligence 的代码参考来源和待验证问题。")
    return questions


def _find_intelligence_seed_rows(source_name: str, field_name: str) -> list[dict[str, Any]]:
    normalized = _normalize_search_key(source_name)
    rows: list[dict[str, Any]] = []
    for seed in _INTELLIGENCE_SOURCE_SEEDS:
        aliases = {_normalize_search_key(alias) for alias in seed.get("aliases", ())}
        if normalized == _normalize_search_key(str(seed.get("name") or "")) or normalized in aliases:
            rows.extend(seed.get(field_name, ()))
    return rows


def _build_intelligence_capability_rows(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in sources:
        for row in _find_intelligence_seed_rows(str(source.get("name") or ""), "capabilityCandidates"):
            rows.append({**row, "source": str(source.get("name") or "")})
    return rows


def _build_intelligence_architecture_rows(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in sources:
        for row in _find_intelligence_seed_rows(str(source.get("name") or ""), "architectureOptions"):
            rows.append({**row, "source": str(source.get("name") or "")})
    return rows


def _render_discovery_functional_brief(
    case_payload: dict[str, Any],
    *,
    sources: list[dict[str, Any]],
    capability_rows: list[dict[str, Any]],
    intelligence_questions: list[str],
    written_at: str,
) -> str:
    lines = [
        "# DiscoveryReferenceFunctionalBrief",
        "",
        f"Case ID: {case_payload['caseId']}",
        "Stage: Discovery",
        "Status: auto-generated draft",
        f"Generated At: {written_at}",
        "",
        "## 1. 当前任务边界",
        "",
        f"- Objective: {case_payload['intake']['objective']}",
        f"- Target User Scenario: {_slot_answer(case_payload, 'targetUserScenario', default='待补')}",
        f"- Must Have Scope: {_slot_answer(case_payload, 'mustHaveScope', default='待补')}",
        f"- Out Of Scope: {_slot_answer(case_payload, 'explicitOutOfScope', default='待补')}",
        "",
        "## 2. 当前对标对象",
        "",
        "| 对标对象 | 类型 | 当前观察重点 |",
        "| --- | --- | --- |",
    ]
    for source in sources:
        lines.append(
            f"| {source['name']} | {source.get('category') or '待补'} | {'、'.join(source.get('focusAreas', [])) or '待补'} |"
        )
    lines.extend(["", "## 3. 可以先提炼出的共性功能", ""])
    if capability_rows:
        for index, row in enumerate(capability_rows, start=1):
            lines.append(f"{index}. {row['name']}：{row.get('reason') or '待补原因'}")
    else:
        lines.append("1. 待补共性功能：当前未命中种子，请补来源。")
    lines.extend(["", "## 4. 对后续 Intelligence 的直接输入", ""])
    for index, question in enumerate(intelligence_questions, start=1):
        lines.append(f"{index}. {question}")
    lines.append("")
    return "\n".join(lines)


def _render_discovery_competitor_landscape(
    case_payload: dict[str, Any],
    *,
    sources: list[dict[str, Any]],
    written_at: str,
) -> str:
    lines = [
        "# DiscoveryCompetitorLandscape",
        "",
        f"Case ID: {case_payload['caseId']}",
        "Stage: Discovery",
        f"Generated At: {written_at}",
        "",
        "| 对标对象 | 官方入口 | 手册 / README | 核心功能焦点 | 当前差异判断 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for source in sources:
        metadata = _seed_discovery_metadata(str(source.get("name") or ""))
        difference = metadata.get("differences", {})
        lines.append(
            f"| {source['name']} | {source.get('productUrl') or '待补'} | {source.get('sourceUrl') or '待补'} | {'、'.join(source.get('focusAreas', [])) or '待补'} | {difference.get('strength', '待补')} / {difference.get('limit', '待补')} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_discovery_common_capability_matrix(
    case_payload: dict[str, Any],
    *,
    capability_rows: list[dict[str, Any]],
    written_at: str,
) -> str:
    lines = [
        "# DiscoveryCommonCapabilityMatrix",
        "",
        f"Case ID: {case_payload['caseId']}",
        "Stage: Discovery",
        f"Generated At: {written_at}",
        "",
        "| 功能主题 | 输入 / 输出 | 竞品共性来源 | 适用原因 |",
        "| --- | --- | --- | --- |",
    ]
    if capability_rows:
        for row in capability_rows:
            lines.append(
                f"| {row['name']} | {row.get('inputOutput') or '待补'} | {'、'.join(row.get('sources', [])) or '待补'} | {row.get('reason') or '待补'} |"
            )
    else:
        lines.append("| 待补共性功能 | 待补 | 待补 | 待补 |")
    lines.append("")
    return "\n".join(lines)


def _render_discovery_highlight_opportunity_memo(
    case_payload: dict[str, Any],
    *,
    highlight_rows: list[dict[str, Any]],
    written_at: str,
) -> str:
    lines = [
        "# DiscoveryHighlightOpportunityMemo",
        "",
        f"Case ID: {case_payload['caseId']}",
        "Stage: Discovery",
        f"Generated At: {written_at}",
        "",
        "| 亮点功能 | 来源 | 为什么值得跟进 | 当前风险 |",
        "| --- | --- | --- | --- |",
    ]
    if highlight_rows:
        for row in highlight_rows:
            lines.append(f"| {row['name']} | {row['source']} | {row['why']} | {row['risk']} |")
    else:
        lines.append("| 待补亮点功能 | 待补 | 待补 | 待补 |")
    lines.append("")
    return "\n".join(lines)


def _collect_codegraph_insights(
    case_payload: dict[str, Any],
    source: dict[str, Any],
    *,
    workspace_root: str | None,
) -> dict[str, Any]:
    local_path_text = str(source.get("localPath") or "").strip()
    result = {
        "sourceId": str(source.get("sourceId") or "").strip(),
        "name": str(source.get("name") or "").strip(),
        "localPath": local_path_text,
        "status": "pending",
        "statusOutput": "",
        "contextMarkdown": "",
    }
    if not local_path_text:
        result["status"] = "not-applicable"
        return result
    project_path = _resolve_workspace_artifact_path(local_path_text, workspace_root)
    if not project_path.exists():
        result["status"] = "missing-local-path"
        result["statusOutput"] = f"missing local path: {project_path.as_posix()}"
        return result
    status_run = _run_codegraph_command(["status", str(project_path)])
    if status_run["returncode"] != 0 or not (project_path / ".codegraph").exists():
        init_run = _run_codegraph_command(["init", "-i", str(project_path)])
        if init_run["returncode"] != 0:
            result["status"] = "init-failed"
            result["statusOutput"] = _trim_text(init_run["stderr"] or init_run["stdout"], 2000)
            return result
        status_run = _run_codegraph_command(["status", str(project_path)])
    result["status"] = "ready" if status_run["returncode"] == 0 else "status-failed"
    result["statusOutput"] = _trim_text(status_run["stdout"] or status_run["stderr"], 2000)
    context_run = _run_codegraph_command(
        [
            "context",
            "-p",
            str(project_path),
            _build_codegraph_task(case_payload, source_name=str(source.get("name") or "")),
        ]
    )
    if context_run["returncode"] == 0:
        result["contextMarkdown"] = _trim_text(context_run["stdout"], 6000)
    else:
        result["contextMarkdown"] = _trim_text(context_run["stderr"] or context_run["stdout"], 2000)
        if result["status"] == "ready":
            result["status"] = "context-failed"
    return result


def _merge_codegraph_reports_into_sources(sources: list[dict[str, Any]], reports: list[dict[str, Any]]) -> None:
    report_by_id = {report["sourceId"]: report for report in reports}
    for source in sources:
        report = report_by_id.get(str(source.get("sourceId") or ""))
        if not report:
            continue
        source["codegraph"] = {
            "status": report["status"],
            "statusOutput": report["statusOutput"],
        }


def _run_codegraph_command(arguments: list[str]) -> dict[str, Any]:
    command = _resolve_codegraph_command()
    if not command:
        return {
            "returncode": 127,
            "stdout": "",
            "stderr": "codegraph command not available",
        }
    try:
        completed = subprocess.run(
            [*command, *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            check=False,
        )
    except FileNotFoundError:
        return {
            "returncode": 127,
            "stdout": "",
            "stderr": "codegraph command not available",
        }
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _resolve_codegraph_command() -> list[str]:
    if sys.platform.startswith("win"):
        for candidate in ("codegraph.cmd", "codegraph.exe", "codegraph"):
            resolved = shutil.which(candidate)
            if resolved:
                return [resolved]
        powershell_script = shutil.which("codegraph.ps1")
        if powershell_script:
            return [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                powershell_script,
            ]
        return []
    resolved = shutil.which("codegraph")
    return [resolved] if resolved else []


def _build_codegraph_task(case_payload: dict[str, Any], *, source_name: str) -> str:
    return (
        f"Analyze {source_name} for case {case_payload['caseId']}. "
        f"Current objective: {case_payload['intake']['objective']} "
        f"Task description: {case_payload['intake']['taskDescription']}"
    )


def _trim_text(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _render_intelligence_capability_extraction_matrix(
    case_payload: dict[str, Any],
    *,
    capability_rows: list[dict[str, Any]],
    written_at: str,
) -> str:
    lines = [
        "# IntelligenceCapabilityExtractionMatrix",
        "",
        f"Case ID: {case_payload['caseId']}",
        "Stage: Intelligence",
        "Status: auto-generated draft",
        f"Generated At: {written_at}",
        "",
        "| 能力主题 | 参考来源 | 当前实现信号 | 纳入 / 后置 / 排除 | 后续问题 |",
        "| --- | --- | --- | --- | --- |",
    ]
    if capability_rows:
        for row in capability_rows:
            lines.append(
                f"| {row['name']} | {row.get('source') or '待补'} | {row.get('signal') or '待补'} | {row.get('decision') or '待补'} | {row.get('nextQuestion') or '待补'} |"
            )
    else:
        lines.append("| 待补能力主题 | 待补 | 待补 | 待补 | 待补 |")
    lines.append("")
    return "\n".join(lines)


def _render_intelligence_opensource_landscape(
    case_payload: dict[str, Any],
    *,
    sources: list[dict[str, Any]],
    written_at: str,
) -> str:
    lines = [
        "# IntelligenceOpenSourceLandscape",
        "",
        f"Case ID: {case_payload['caseId']}",
        "Stage: Intelligence",
        f"Generated At: {written_at}",
        "",
        "| 项目 / 资料 | 入口 | 类型 | 对应能力 | 当前用途 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for source in sources:
        entry = source.get("sourceUrl") or source.get("localPath") or "待补"
        lines.append(
            f"| {source['name']} | {entry} | {source.get('category') or '待补'} | {'、'.join(source.get('focusAreas', [])) or '待补'} | {source.get('intendedUse') or '待补'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_intelligence_codegraph_analysis(
    case_payload: dict[str, Any],
    *,
    codegraph_reports: list[dict[str, Any]],
    written_at: str,
) -> str:
    lines = [
        "# IntelligenceCodegraphAnalysis",
        "",
        f"Case ID: {case_payload['caseId']}",
        "Stage: Intelligence",
        f"Generated At: {written_at}",
        "",
        "## CodeGraph 状态",
        "",
    ]
    if not codegraph_reports:
        lines.append("当前没有可直接执行 CodeGraph 的本地代码锚点，或本轮选择了关闭 CodeGraph。")
        lines.append("")
        return "\n".join(lines)
    for report in codegraph_reports:
        lines.extend(
            [
                f"### {report['name']}",
                "",
                f"- Status: {report['status']}",
                f"- Local Path: {report['localPath'] or 'N/A'}",
                "",
                "#### Status Output",
                "",
                "```text",
                report.get("statusOutput") or "(empty)",
                "```",
                "",
                "#### Context",
                "",
                report.get("contextMarkdown") or "(no context captured)",
                "",
            ]
        )
    return "\n".join(lines)


def _render_intelligence_architecture_option_memo(
    case_payload: dict[str, Any],
    *,
    architecture_rows: list[dict[str, Any]],
    written_at: str,
) -> str:
    lines = [
        "# IntelligenceArchitectureOptionMemo",
        "",
        f"Case ID: {case_payload['caseId']}",
        "Stage: Intelligence",
        f"Generated At: {written_at}",
        "",
        "| 能力主题 | 参考来源 | 候选实现路线 | 优点 | 风险 / 代价 | 首轮建议 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if architecture_rows:
        for row in architecture_rows:
            lines.append(
                f"| {row['theme']} | {row.get('source') or '待补'} | {row.get('approach') or '待补'} | {row.get('pros') or '待补'} | {row.get('risks') or '待补'} | {row.get('recommendation') or '待补'} |"
            )
    else:
        lines.append("| 待补架构主题 | 待补 | 待补 | 待补 | 待补 | 待补 |")
    lines.append("")
    return "\n".join(lines)


def _stage_handoff_checklist(case_payload: dict[str, Any], stage: dict[str, Any]) -> list[str]:
    checklist = _stage_template(stage["stageKey"]).get("handoffChecklist") or []
    return _materialize_stage_template(list(checklist), case_id=case_payload["caseId"])


def _summary_for_case(
    case_payload: dict[str, Any],
    *,
    advanced: bool,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    current_stage = _current_stage(case_payload)
    return {
        "caseId": case_payload["caseId"],
        "title": case_payload["title"],
        "status": case_payload["status"],
        "entryCheckpoint": _entry_checkpoint_for_case(case_payload),
        "caseCategory": str(case_payload["intake"].get("caseCategory") or ""),
        "referenceTheme": str(case_payload["intake"].get("referenceTheme") or ""),
        "executionFlow": _execution_flow_for_case(case_payload),
        "intakeClarificationStatus": str(case_payload["intake"].get("clarificationSheet", {}).get("status") or ""),
        "missingIntakeSlotKeys": list(case_payload["intake"].get("clarificationSheet", {}).get("missingSlotKeys", [])),
        "clarificationSheet": dict(case_payload["intake"].get("clarificationSheet", {})),
        "freezeControl": dict(case_payload.get("freezeControl", {})),
        "currentStageKey": case_payload.get("currentStageKey") or "",
        "currentOwnerRole": current_stage["actingOwner"] if current_stage else "",
        "currentWorkItemPath": case_payload.get("currentWorkItemPath") or "",
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "advanced": advanced,
        "casePath": _case_file_path(case_payload["caseId"], workspace_root).as_posix(),
        "intakeBriefPath": str(case_payload["intake"].get("briefPath") or ""),
    }


def _entry_checkpoint_for_case(case_payload: dict[str, Any]) -> str:
    status = str(case_payload.get("status") or "").strip()
    intake = case_payload.get("intake") if isinstance(case_payload.get("intake"), dict) else {}
    intake_status = str(intake.get("status") or "").strip()
    current_stage = _current_stage(case_payload)

    if current_stage is not None:
        stage_key = str(current_stage.get("stageKey") or "").strip()
        if (
            stage_key == _first_stage_key(case_payload)
            and str(current_stage.get("status") or "").strip() == "in-progress"
            and not str(current_stage.get("submittedAt") or "").strip()
            and not str(current_stage.get("outputPath") or "").strip()
        ):
            return "task-dispatch"
        return stage_key

    if status in {"awaiting-intake-approvals", "paused-intake-clarification"}:
        return "ceo-demand"
    if intake_status != "approved":
        return "ceo-demand"
    if status == "completed":
        return "completed"

    next_stage = _next_pending_stage(case_payload)
    if next_stage is not None:
        next_stage_key = str(next_stage.get("stageKey") or "").strip()
        return "task-dispatch" if next_stage_key == _first_stage_key(case_payload) else next_stage_key
    return "ceo-demand"


def _resolve_rollback_target(case_payload: dict[str, Any], stage_key: str) -> dict[str, str]:
    if stage_key in _ROLLBACK_CEO_DEMAND_ALIASES:
        return {
            "kind": "ceo-demand",
            "nodeKey": "ceo-demand",
            "stageKey": "",
        }
    if stage_key in _ROLLBACK_TASK_DISPATCH_ALIASES:
        return {
            "kind": "task-dispatch",
            "nodeKey": "task-dispatch",
            "stageKey": _first_stage_key(case_payload),
        }
    _require_stage(case_payload, stage_key)
    return {
        "kind": "stage",
        "nodeKey": stage_key,
        "stageKey": stage_key,
    }


def _reset_all_stages(case_payload: dict[str, Any], *, now: str) -> list[str]:
    reset_stage_keys: list[str] = []
    for stage in case_payload["stages"]:
        _reset_stage_to_pending(stage, now=now)
        reset_stage_keys.append(str(stage.get("stageKey") or "").strip())
    return reset_stage_keys


def _reset_stages_from(case_payload: dict[str, Any], stage_key: str, *, now: str) -> list[str]:
    reset_stage_keys: list[str] = []
    reset_downstream = False
    for stage in case_payload["stages"]:
        current_stage_key = str(stage.get("stageKey") or "").strip()
        if current_stage_key == stage_key:
            reset_downstream = True
        if not reset_downstream:
            continue
        _reset_stage_to_pending(stage, now=now)
        reset_stage_keys.append(current_stage_key)
    return reset_stage_keys


def _reset_case_to_ceo_demand(
    case_payload: dict[str, Any],
    *,
    now: str,
    workspace_root: str | None,
) -> None:
    intake = case_payload["intake"]
    required_approvers = [
        str(item.get("role") or "").strip()
        for item in intake.get("approvals", [])
        if str(item.get("role") or "").strip()
    ] or list(INTAKE_REQUIRED_APPROVERS)
    intake["approvals"] = _build_approvals(required_approvers, auto_approved_role=None, now=now)
    intake["status"] = _approval_rollup(intake["approvals"])
    intake["packageHash"] = ""
    intake["releaseCounter"] = 0
    intake["releaseVersion"] = ""
    intake["releaseStatus"] = "draft"
    intake["releaseIssuedAt"] = ""
    intake["releaseIssuedByRole"] = ""
    intake["clarificationSheet"] = _build_intake_clarification_sheet(
        task_description=str(intake.get("taskDescription") or ""),
        slot_answers=_normalize_slot_answers(intake.get("slotAnswers")),
        required=bool(intake.get("clarificationRequired")),
    )
    case_payload["currentStageKey"] = ""
    case_payload["currentWorkItemPath"] = ""
    intake_brief_path = _write_intake_brief(case_payload, workspace_root=workspace_root, written_at=now)
    intake["briefPath"] = intake_brief_path.as_posix()


def _build_autopilot_stage_submission(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
    enable_tridev_bridge: bool,
    tridev_workflow: ModuleType | None,
    tridev_root: Path | None,
    tridev_run_id: str,
    strict_release_bundle: bool,
) -> dict[str, Any]:
    participant_record = _write_stage_participant_record(case_payload, stage, workspace_root=workspace_root)
    details = [
        f"{stage['actingOwner']} 已完成 {stage['title']} 自动提交。",
        f"岗位参与记录已写入 {participant_record['reference']}。",
    ]
    evidence = [participant_record["reference"]]
    tridev_report: dict[str, Any] | None = None
    if enable_tridev_bridge:
        if tridev_workflow is None or tridev_root is None:
            raise RuntimeError("TriDev bridge is enabled but TriDev workflow context is missing")
        tridev_report = _run_tridev_stage_automation(
            case_payload,
            stage,
            tridev_workflow=tridev_workflow,
            tridev_root=tridev_root,
            tridev_run_id=tridev_run_id,
            strict_release_bundle=strict_release_bundle,
        )
        details.append(f"TriDev 阶段 {stage['phaseKey']} 已完成 phase result 与 gate。")
        if tridev_report.get("bundleReference"):
            details.append(f"交付 bundle 已生成并校验：{tridev_report['bundleReference']}。")
        evidence.extend(tridev_report["evidenceRefs"])

    autopilot_package = _write_stage_autopilot_package(
        case_payload,
        stage,
        participant_record=participant_record,
        tridev_report=tridev_report,
        workspace_root=workspace_root,
    )
    evidence.append(autopilot_package["reference"])
    summary = f"{stage['title']} 已由 autopilot 自动提交并进入签核。"
    return {
        "summary": summary,
        "details": details,
        "evidence": evidence,
        "objectPath": autopilot_package["path"].as_posix(),
    }


def _run_tridev_stage_automation(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    tridev_workflow: ModuleType,
    tridev_root: Path,
    tridev_run_id: str,
    strict_release_bundle: bool,
) -> dict[str, Any]:
    phase_key = str(stage.get("phaseKey") or "").strip()
    if not phase_key:
        raise ValueError(f"missing phaseKey for stage {stage.get('stageKey')}")
    stage_artifact = _write_tridev_stage_artifact(case_payload, stage, tridev_root=tridev_root)
    stage_artifact_ref = _relative_to_root(tridev_root, stage_artifact)
    tridev_workflow.record_phase_result(
        tridev_root,
        run_id=tridev_run_id,
        stage=phase_key,
        status="completed",
        artifact_refs=[stage_artifact_ref],
        summary=f"{case_payload['caseId']} {stage['stageKey']} 自动推进完成。",
        branch_id=_branch_id(case_payload["caseId"]),
    )
    tridev_workflow.record_gate(
        tridev_root,
        run_id=tridev_run_id,
        stage=phase_key,
        status="approved",
        approved_by=stage["actingOwner"],
        comments=_AUTOPILOT_NOTE,
    )

    phase_result_file = _tridev_run_dir(tridev_root, tridev_run_id) / "phase-results" / f"{phase_key.lower().replace('-', '_')}.json"
    evidence_refs = [
        stage_artifact_ref,
        _relative_to_root(tridev_root, phase_result_file),
        _relative_to_root(tridev_root, _tridev_run_dir(tridev_root, tridev_run_id) / "gate-ledger.json"),
    ]
    bundle_reference = ""
    if phase_key == "DELIVERY":
        manifest_path = tridev_workflow.generate_delivery_manifest(
            tridev_root,
            run_id=tridev_run_id,
            strict=strict_release_bundle,
        )
        bundle_path = tridev_workflow.create_release_bundle(
            tridev_root,
            run_id=tridev_run_id,
            strict=strict_release_bundle,
        )
        verification = tridev_workflow.verify_release_bundle(tridev_root, run_id=tridev_run_id)
        if not verification["valid"]:
            raise RuntimeError("TriDev release bundle verification failed during autopilot")
        run_index_path = tridev_workflow.generate_run_index(tridev_root)
        evidence_refs.extend(
            [
                _relative_to_root(tridev_root, Path(manifest_path)),
                _relative_to_root(tridev_root, Path(bundle_path)),
                _relative_to_root(tridev_root, _tridev_run_dir(tridev_root, tridev_run_id) / "artifacts" / "release.sha256"),
                _relative_to_root(tridev_root, Path(run_index_path)),
            ]
        )
        bundle_reference = _relative_to_root(tridev_root, Path(bundle_path))
    return {
        "runId": tridev_run_id,
        "stage": phase_key,
        "evidenceRefs": evidence_refs,
        "bundleReference": bundle_reference,
    }


def _write_stage_participant_record(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
) -> dict[str, Any]:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    participants_root = case_root / "participant-records"
    participants_root.mkdir(parents=True, exist_ok=True)
    filename = f"{_stage_index_for_case(case_payload, stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    path = participants_root / filename
    records_roles: list[str] = []
    for role in [stage["actingOwner"], *list(stage.get("participantRoles", []))]:
        normalized_role = str(role).strip()
        if normalized_role and normalized_role not in records_roles:
            records_roles.append(normalized_role)
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-stage-participant-record",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
        "generatedAt": _timestamp_now(),
        "records": [
            {
                "role": role,
                "status": "completed",
                "summary": f"{role} 已在 {stage['stageKey']} 阶段完成 autopilot 协同条目。",
            }
            for role in records_roles
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "path": path,
        "reference": f"workbench/ipd/cases/{case_payload['caseId']}/participant-records/{filename}",
    }


def _write_stage_autopilot_package(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    participant_record: dict[str, Any],
    tridev_report: dict[str, Any] | None,
    workspace_root: str | None,
) -> dict[str, Any]:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    autopilot_root = case_root / "autopilot-packages"
    autopilot_root.mkdir(parents=True, exist_ok=True)
    filename = f"{_stage_index_for_case(case_payload, stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    path = autopilot_root / filename
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-autopilot-stage-package",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "generatedAt": _timestamp_now(),
        "participantRecordRef": participant_record["reference"],
        "tridev": tridev_report or {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "path": path,
        "reference": f"workbench/ipd/cases/{case_payload['caseId']}/autopilot-packages/{filename}",
    }


def _write_stage_owner_action_package(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
    tridev_root: Path | None,
    tridev_run_id: str,
) -> dict[str, Any]:
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    owner_action_root = case_root / "owner-action-packages"
    owner_action_root.mkdir(parents=True, exist_ok=True)
    filename = f"{_stage_index_for_case(case_payload, stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
    path = owner_action_root / filename
    generated_at = _timestamp_now()
    work_item_path = str(stage.get("workItemPath") or case_payload.get("currentWorkItemPath") or "").strip()
    work_item_ref = f"workbench/ipd/cases/{case_payload['caseId']}/work-items/{Path(work_item_path).name}" if work_item_path else ""
    intake_brief_path = str(case_payload["intake"].get("briefPath") or "").strip()
    intake_brief_ref = f"workbench/ipd/cases/{case_payload['caseId']}/intake-brief.json" if intake_brief_path else ""
    recommended_commands = [
        (
            "python -m runtime.cognition.chief_of_staff_ipd_case submit "
            f"--case-id {case_payload['caseId']} --stage-key {stage['stageKey']} "
            f"--submitted-by {stage['actingOwner']} --summary \"{stage['title']} 已提交\" "
            "--detail \"<detail>\" --evidence <evidence-path> --object-path <primary-output-object-path> "
            "--signing-key <web3-private-key>|--mnemonic \"<twelve-or-twenty-four-words>\""
        ),
        (
            "python -m runtime.cognition.chief_of_staff_ipd_case freeze "
            f"--case-id {case_payload['caseId']} --role <assigned-role> --reason \"<freeze-reason>\" --domain <domain>"
        ),
        (
            "python -m runtime.cognition.chief_of_staff_ipd_case unfreeze "
            f"--case-id {case_payload['caseId']} --role <freeze-role-or-CEOChiefOfStaff> --note \"<unfreeze-note>\""
        ),
        (
            "python -m runtime.cognition.chief_of_staff_ipd_case signoff "
            f"--case-id {case_payload['caseId']} --stage-key {stage['stageKey']} --role CEO "
            "--signing-key <web3-private-key>|--mnemonic \"<twelve-or-twenty-four-words>\""
        ),
        (
            "python -m runtime.cognition.chief_of_staff_ipd_case signoff "
            f"--case-id {case_payload['caseId']} --stage-key {stage['stageKey']} --role CEOChiefOfStaff "
            "--signing-key <web3-private-key>|--mnemonic \"<twelve-or-twenty-four-words>\""
        ),
    ]
    if stage["stageKey"] == "discovery":
        recommended_commands.insert(
            0,
            "python -m runtime.cognition.chief_of_staff_ipd_case discovery "
            f"--case-id {case_payload['caseId']} --submit",
        )
    elif stage["stageKey"] == "intelligence":
        recommended_commands.insert(
            0,
            "python -m runtime.cognition.chief_of_staff_ipd_case intelligence "
            f"--case-id {case_payload['caseId']} --submit",
        )
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-owner-action-package",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "gateOwner": stage["gateOwner"],
        "generatedAt": generated_at,
        "summary": _stage_summary(case_payload, stage),
        "reason": _OWNER_ACTION_BLOCK_REASON,
        "caseRef": f"workbench/ipd/cases/{case_payload['caseId']}/case.json",
        "workItemPath": work_item_path,
        "workItemRef": work_item_ref,
        "intakeBriefPath": intake_brief_path,
        "intakeBriefRef": intake_brief_ref,
        "inputRefs": _input_refs(case_payload),
        "roleAssignmentMatrix": _stage_role_assignment_matrix(stage["stageKey"]),
        "inputRequirements": list(stage.get("inputRequirements", [])),
        "outputRequirements": list(stage.get("outputRequirements", [])),
        "requiredApprovers": list(stage.get("requiredApprovers", [])),
        "schemaHint": dict(stage.get("schemaHint", {})),
        "draftTemplate": _draft_template(case_payload, stage, written_at=generated_at),
        "submissionTemplate": _stage_submission_template(case_payload, stage),
        "evidencePolicy": _REAL_EXECUTION_BLOCK_REASON if _stage_requires_real_execution(stage["stageKey"]) else _NON_GENERATED_EVIDENCE_BLOCK_REASON,
        "recommendedCommands": recommended_commands,
    }
    standard_flow = _stage_standard_flow(case_payload, stage)
    if standard_flow:
        payload["standardFlow"] = standard_flow
    handoff_checklist = _stage_handoff_checklist(case_payload, stage)
    if handoff_checklist:
        payload["handoffChecklist"] = handoff_checklist
    tridev_owner_adapter_bundle = _build_tridev_owner_adapter_bundle(
        stage,
        tridev_root=tridev_root,
        tridev_run_id=tridev_run_id,
    )
    if tridev_owner_adapter_bundle:
        payload["tridevOwnerAdapterBundle"] = tridev_owner_adapter_bundle
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "path": path,
        "reference": f"workbench/ipd/cases/{case_payload['caseId']}/owner-action-packages/{filename}",
    }


def _build_tridev_owner_adapter_bundle(
    stage: dict[str, Any],
    *,
    tridev_root: Path | None,
    tridev_run_id: str,
) -> dict[str, Any]:
    if tridev_root is None or not str(tridev_run_id or "").strip():
        return {}
    run_dir = _tridev_run_dir(tridev_root, tridev_run_id)
    role_adapters_file = run_dir / "role-adapters.json"
    workflow_state_file = run_dir / "workflow-state.json"
    bundle: dict[str, Any] = {
        "status": "missing-run-context",
        "runId": tridev_run_id,
        "targetStage": str(stage.get("phaseKey") or "").strip(),
        "ownerRole": str(stage.get("actingOwner") or "").strip(),
        "roleAdaptersPath": _relative_to_root(tridev_root, role_adapters_file) if role_adapters_file.exists() else "",
        "workflowStatePath": _relative_to_root(tridev_root, workflow_state_file) if workflow_state_file.exists() else "",
    }
    if not role_adapters_file.exists() or not workflow_state_file.exists():
        return bundle

    role_adapters_payload = json.loads(role_adapters_file.read_text(encoding="utf-8"))
    workflow_state = json.loads(workflow_state_file.read_text(encoding="utf-8"))
    target_stage = str(stage.get("phaseKey") or "").strip()
    stage_entry = next(
        (
            entry
            for entry in role_adapters_payload.get("stageAdapters", [])
            if str(entry.get("stage") or "").strip() == target_stage
        ),
        None,
    )
    if stage_entry is None and str(role_adapters_payload.get("stage") or "").strip() == target_stage:
        stage_entry = {
            "stage": role_adapters_payload.get("stage", ""),
            "adapters": list(role_adapters_payload.get("adapters", [])),
        }

    owner_role = str(stage.get("actingOwner") or "").strip()
    bundle.update(
        {
            "status": "ready" if stage_entry is not None else "missing-stage-adapters",
            "runCurrentStage": str(workflow_state.get("currentStage") or "").strip(),
            "runCurrentStageMatchesTargetStage": str(workflow_state.get("currentStage") or "").strip() == target_stage,
            "nextAction": str(role_adapters_payload.get("nextAction") or workflow_state.get("nextAction") or "").strip(),
            "executionMode": str(role_adapters_payload.get("executionMode") or workflow_state.get("executionMode") or "").strip(),
            "roleAdaptersPath": _relative_to_root(tridev_root, role_adapters_file),
            "workflowStatePath": _relative_to_root(tridev_root, workflow_state_file),
            "knowledgeBundlePath": str(workflow_state.get("knowledgeBundlePath") or "").replace("\\", "/"),
            "promptContextPath": str(workflow_state.get("promptContextPath") or "").replace("\\", "/"),
            "taskPlanPath": str(workflow_state.get("taskPlanPath") or "").replace("\\", "/"),
            "ownerAdapters": [],
            "supportingAdapters": [],
            "evidenceRefs": [],
        }
    )
    if stage_entry is None:
        return bundle

    stage_adapters = list(stage_entry.get("adapters", []))
    supporting_roles = {
        str(stage.get("moduleExecutor") or "").strip(),
        str(stage.get("gateOwner") or "").strip(),
        str(stage.get("businessOwner") or "").strip(),
    }
    supporting_roles.discard("")
    supporting_roles.discard(owner_role)
    bundle["ownerAdapters"] = [
        adapter
        for adapter in stage_adapters
        if str(adapter.get("role") or "").strip() == owner_role
    ]
    bundle["supportingAdapters"] = [
        adapter
        for adapter in stage_adapters
        if str(adapter.get("role") or "").strip() in supporting_roles
    ]
    evidence_refs: list[str] = []
    for ref in (
        _relative_to_root(tridev_root, workflow_state_file),
        _relative_to_root(tridev_root, role_adapters_file),
        str(workflow_state.get("knowledgeBundlePath") or "").strip(),
        str(workflow_state.get("promptContextPath") or "").strip(),
        str(workflow_state.get("taskPlanPath") or "").strip(),
    ):
        normalized_ref = str(ref or "").strip().replace("\\", "/")
        if normalized_ref and normalized_ref not in evidence_refs:
            evidence_refs.append(normalized_ref)
    bundle["evidenceRefs"] = evidence_refs
    return bundle


def _resolve_tridev_root(*, workspace_root: str | None, tridev_root: str | None) -> Path:
    if str(tridev_root or "").strip():
        path = Path(str(tridev_root)).resolve()
        if not path.exists():
            raise FileNotFoundError(f"TriDev root not found: {path}")
        return path
    candidates: list[Path] = []
    if str(workspace_root or "").strip():
        workspace = Path(str(workspace_root)).resolve()
        candidates.append(workspace.parent / "TriDev")
    source_repo_root = Path(__file__).resolve().parents[2]
    candidates.append(source_repo_root.parent / "TriDev")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("TriDev root not found; pass --tridev-root explicitly")


def _load_tridev_workflow_module(tridev_root: Path) -> ModuleType:
    tridev_src = tridev_root / "src"
    if not tridev_src.exists():
        raise FileNotFoundError(f"TriDev src not found: {tridev_src}")
    tridev_src_text = str(tridev_src)
    if tridev_src_text not in sys.path:
        sys.path.insert(0, tridev_src_text)
    return importlib.import_module("tridev.workflow")


def _ensure_tridev_run(
    *,
    case_id: str,
    case_payload: dict[str, Any],
    tridev_workflow: ModuleType,
    tridev_root: Path,
) -> str:
    run_id = _default_tridev_run_id(case_id)
    metadata_file = _tridev_run_dir(tridev_root, run_id) / "run-metadata.json"
    if metadata_file.exists():
        return run_id
    reference_evidence = tridev_workflow.ReferenceEvidence(
        upstream="TriCompany-IPD",
        referencePath=f"workbench/ipd/cases/{case_id}/intake-brief.json",
        vendorPath="TriDev/vendor/super-dev",
        license="internal-governed-use",
        commit=case_payload["updatedAt"],
        capabilityMapping=[stage["stageKey"] for stage in case_payload.get("stages", [])],
        exclusions=[],
    )
    tridev_workflow.create_run(
        tridev_root,
        task=case_payload["intake"]["taskDescription"],
        mode=_TRIDEV_RUN_MODE,
        branch_id=_branch_id(case_id),
        run_id=run_id,
        reference_evidence=reference_evidence,
    )
    return run_id


def _write_tridev_stage_artifact(case_payload: dict[str, Any], stage: dict[str, Any], *, tridev_root: Path) -> Path:
    artifact_root = tridev_root / "docs" / "ipd-autopilot" / case_payload["caseId"]
    artifact_root.mkdir(parents=True, exist_ok=True)
    path = artifact_root / f"{_stage_index_for_case(case_payload, stage['stageKey']) + 1:02d}-{stage['stageKey']}.md"
    lines = [
        f"# {case_payload['caseId']} - {stage['title']}",
        "",
        f"- phase: {stage['phaseKey']}",
        f"- businessOwner: {stage['businessOwner']}",
        f"- actingOwner: {stage['actingOwner']}",
        f"- moduleExecutor: {stage['moduleExecutor']}",
        f"- participants: {', '.join(stage.get('participantRoles', []))}",
        f"- generatedAt: {_timestamp_now()}",
        "",
        "## Intake Objective",
        case_payload["intake"]["objective"],
        "",
        "## Stage Summary",
        f"{stage['title']} 已由 IPD autopilot 自动推进并写入 TriDev phase result / gate。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _tridev_run_dir(tridev_root: Path, run_id: str) -> Path:
    return _tridev_surface_root(tridev_root) / "docs" / "runs" / run_id


def _default_tridev_run_id(case_id: str) -> str:
    return "ipd-" + case_id.replace("_", "-").replace(".", "-").lower()


def _tridev_surface_root(tridev_root: Path) -> Path:
    try:
        tridev_workflow = _load_tridev_workflow_module(tridev_root)
        support_root = Path(tridev_workflow.support_root_path(tridev_root)).resolve()
        if support_root.exists():
            return support_root
    except Exception:
        pass
    return tridev_root.resolve()


def _relative_to_root(root: Path, path: Path) -> str:
    resolved_path = path.resolve()
    candidates = [root.resolve()]
    support_root = _tridev_surface_root(root)
    if support_root not in candidates:
        candidates.append(support_root)
    for candidate in candidates:
        try:
            return resolved_path.relative_to(candidate).as_posix()
        except ValueError:
            continue
    return resolved_path.as_posix()


def _next_pending_approval_role(approvals: list[dict[str, str]]) -> str:
    for approval in approvals:
        if approval["status"] == "pending":
            return approval["role"]
    return ""


def _intake_clarification_ready(intake: dict[str, Any]) -> bool:
    clarification_sheet = intake.get("clarificationSheet", {}) if isinstance(intake, dict) else {}
    return str(clarification_sheet.get("status") or "").strip() in {"ready-for-dispatch", "not-enforced"}


def _case_is_frozen(case_payload: dict[str, Any]) -> bool:
    freeze_control = _normalize_freeze_control(case_payload.get("freezeControl"))
    return bool(freeze_control.get("active"))


def _assert_case_not_frozen(case_payload: dict[str, Any], *, action: str) -> None:
    freeze_control = _normalize_freeze_control(case_payload.get("freezeControl"))
    if not freeze_control.get("active"):
        return
    frozen_by = str(freeze_control.get("frozenByRole") or "").strip()
    raise ValueError(f"case is frozen by {frozen_by or 'unknown role'} and cannot perform {action}")


def _freeze_allowed_roles(case_payload: dict[str, Any]) -> list[str]:
    current_stage = _current_stage(case_payload)
    matrix = _build_intake_role_assignment_matrix()
    stage_key = str(current_stage.get("stageKey") or "").strip() if current_stage else "intake"
    allowed_roles = [
        item["role"]
        for item in matrix
        if bool(item.get("canFreezeCase")) and stage_key in set(item.get("stageKeys", []))
    ]
    unique_roles: list[str] = []
    for role in allowed_roles:
        normalized_role = str(role or "").strip()
        if normalized_role and normalized_role not in unique_roles:
            unique_roles.append(normalized_role)
    return unique_roles


def _assert_role_can_freeze_case(case_payload: dict[str, Any], role: str) -> None:
    normalized_role = str(role or "").strip()
    allowed_roles = _freeze_allowed_roles(case_payload)
    if normalized_role not in allowed_roles:
        current_stage = _current_stage(case_payload)
        stage_text = str(current_stage.get("stageKey") or "intake").strip() if current_stage else "intake"
        raise ValueError(f"{normalized_role} cannot freeze case during {stage_text}")
    current_stage = _current_stage(case_payload)
    if current_stage is None and normalized_role == "CEOChiefOfStaff" and not _intake_clarification_ready(case_payload.get("intake", {})):
        raise ValueError("CEOChiefOfStaff can freeze intake only after clarification sheet is ready")


def _assert_role_can_unfreeze_case(case_payload: dict[str, Any], role: str) -> None:
    normalized_role = str(role or "").strip()
    freeze_control = _normalize_freeze_control(case_payload.get("freezeControl"))
    frozen_by_role = str(freeze_control.get("frozenByRole") or "").strip()
    if normalized_role in {"CEOChiefOfStaff", frozen_by_role}:
        return
    raise ValueError(f"{normalized_role} cannot unfreeze case frozen by {frozen_by_role or 'unknown role'}")


def _infer_freeze_domain(role: str, stage_key: str) -> str:
    normalized_role = str(role or "").strip()
    role_domain_map = {
        "CEOChiefOfStaff": "feasibility",
        "ChiefMarketingOfficer": "market-demand",
        "ChiefProductOfficer": "product-scope",
        "ChiefTechnologyOfficer": "technical-feasibility",
        "ChiefOperatingOfficer": "operations",
        "ChiefFinancialOfficer": "finance",
    }
    return role_domain_map.get(normalized_role) or (str(stage_key or "").strip() or "professional-judgment")


def _autopilot_intake_clarification_pause_summary(
    *,
    case_payload: dict[str, Any],
    case_status: str,
    activity: list[dict[str, Any]],
    tridev_root_path: Path | None,
    tridev_run_id: str,
    workspace_root: str | None,
) -> dict[str, Any]:
    clarification_sheet = case_payload["intake"].get("clarificationSheet", {})
    _append_event(
        case_payload["caseId"],
        "autopilot-paused-intake-clarification",
        {
            "caseStatus": case_status,
            "missingSlotKeys": list(clarification_sheet.get("missingSlotKeys", [])),
        },
        workspace_root=workspace_root,
    )
    return {
        "caseId": case_payload["caseId"],
        "status": "paused-intake-clarification",
        "caseStatus": case_status,
        "entryCheckpoint": _entry_checkpoint_for_case(case_payload),
        "pendingRole": "CEO",
        "pendingStageKey": "",
        "missingSlotKeys": list(clarification_sheet.get("missingSlotKeys", [])),
        "followUpQuestions": list(clarification_sheet.get("followUpQuestions", [])),
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "tridevBridgeEnabled": bool(tridev_root_path or tridev_run_id),
        "tridevRunId": tridev_run_id,
        "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
        "actions": activity,
    }


def _autopilot_frozen_pause_summary(
    *,
    case_payload: dict[str, Any],
    case_status: str,
    activity: list[dict[str, Any]],
    tridev_root_path: Path | None,
    tridev_run_id: str,
    workspace_root: str | None,
) -> dict[str, Any]:
    freeze_control = _normalize_freeze_control(case_payload.get("freezeControl"))
    _append_event(
        case_payload["caseId"],
        "autopilot-paused-frozen",
        {
            "caseStatus": case_status,
            "frozenByRole": str(freeze_control.get("frozenByRole") or "").strip(),
            "stageKey": str(freeze_control.get("stageKey") or "").strip(),
            "reason": str(freeze_control.get("reason") or "").strip(),
        },
        workspace_root=workspace_root,
    )
    return {
        "caseId": case_payload["caseId"],
        "status": "paused-frozen",
        "caseStatus": case_status,
        "entryCheckpoint": _entry_checkpoint_for_case(case_payload),
        "pendingRole": str(freeze_control.get("frozenByRole") or "").strip(),
        "pendingStageKey": str(freeze_control.get("stageKey") or "").strip(),
        "freezeControl": freeze_control,
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "tridevBridgeEnabled": bool(tridev_root_path),
        "tridevRunId": tridev_run_id,
        "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
        "actions": activity,
    }


def _autopilot_manual_pause_summary(
    *,
    case_payload: dict[str, Any],
    case_status: str,
    pending_role: str,
    pending_stage_key: str,
    activity: list[dict[str, Any]],
    tridev_root_path: Path | None,
    tridev_run_id: str,
    workspace_root: str | None,
) -> dict[str, Any]:
    _append_event(
        case_payload["caseId"],
        "autopilot-paused-manual-approval",
        {
            "pendingRole": pending_role,
            "pendingStageKey": pending_stage_key,
            "caseStatus": case_status,
        },
        workspace_root=workspace_root,
    )
    return {
        "caseId": case_payload["caseId"],
        "status": "paused-manual-approval",
        "caseStatus": case_status,
        "entryCheckpoint": _entry_checkpoint_for_case(case_payload),
        "pendingRole": pending_role,
        "pendingStageKey": pending_stage_key,
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "tridevBridgeEnabled": bool(tridev_root_path or tridev_run_id),
        "tridevRunId": tridev_run_id,
        "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
        "actions": activity,
    }


def _autopilot_real_execution_pause_summary(
    *,
    case_payload: dict[str, Any],
    case_status: str,
    pending_stage_key: str,
    activity: list[dict[str, Any]],
    tridev_root_path: Path | None,
    tridev_run_id: str,
    workspace_root: str | None,
) -> dict[str, Any]:
    _append_event(
        case_payload["caseId"],
        "autopilot-paused-real-execution",
        {
            "pendingStageKey": pending_stage_key,
            "caseStatus": case_status,
            "reason": _REAL_EXECUTION_BLOCK_REASON,
        },
        workspace_root=workspace_root,
    )
    return {
        "caseId": case_payload["caseId"],
        "status": "paused-real-execution",
        "caseStatus": case_status,
        "entryCheckpoint": _entry_checkpoint_for_case(case_payload),
        "pendingStageKey": pending_stage_key,
        "reason": _REAL_EXECUTION_BLOCK_REASON,
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "tridevBridgeEnabled": bool(tridev_root_path or tridev_run_id),
        "tridevRunId": tridev_run_id,
        "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
        "actions": activity,
    }


def _autopilot_owner_action_pause_summary(
    *,
    case_payload: dict[str, Any],
    case_status: str,
    pending_role: str,
    pending_stage_key: str,
    owner_action_package_ref: str,
    activity: list[dict[str, Any]],
    tridev_root_path: Path | None,
    tridev_run_id: str,
    workspace_root: str | None,
) -> dict[str, Any]:
    _append_event(
        case_payload["caseId"],
        "autopilot-paused-owner-action",
        {
            "pendingRole": pending_role,
            "pendingStageKey": pending_stage_key,
            "caseStatus": case_status,
            "reason": _OWNER_ACTION_BLOCK_REASON,
            "ownerActionPackageRef": owner_action_package_ref,
        },
        workspace_root=workspace_root,
    )
    return {
        "caseId": case_payload["caseId"],
        "status": "paused-owner-action",
        "caseStatus": case_status,
        "entryCheckpoint": _entry_checkpoint_for_case(case_payload),
        "pendingRole": pending_role,
        "pendingStageKey": pending_stage_key,
        "reason": _OWNER_ACTION_BLOCK_REASON,
        "ownerActionPackageRef": owner_action_package_ref,
        "completedStageCount": sum(1 for stage in case_payload["stages"] if stage["status"] == "completed"),
        "stageCount": len(case_payload["stages"]),
        "tridevBridgeEnabled": bool(tridev_root_path or tridev_run_id),
        "tridevRunId": tridev_run_id,
        "tridevRoot": tridev_root_path.as_posix() if tridev_root_path else "",
        "actions": activity,
    }


def _case_file_path(case_id: str, workspace_root: str | None) -> Path:
    return chief_of_staff_ipd_case_root(case_id, workspace_root) / "case.json"


def _intake_brief_file_path(case_id: str, workspace_root: str | None) -> Path:
    return chief_of_staff_ipd_case_root(case_id, workspace_root) / "intake-brief.json"


def _events_file_path(case_id: str, workspace_root: str | None) -> Path:
    return chief_of_staff_ipd_case_root(case_id, workspace_root) / "events.jsonl"


def _load_case(case_id: str, workspace_root: str | None) -> dict[str, Any]:
    normalized_case_id = _normalize_identifier(case_id)
    case_path = _case_file_path(normalized_case_id, workspace_root)
    if not case_path.exists():
        raise FileNotFoundError(f"IPD case not found: {normalized_case_id}")
    payload = json.loads(case_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid case payload: {normalized_case_id}")
    _ensure_case_defaults(payload)
    return payload


def _save_case(case_payload: dict[str, Any], workspace_root: str | None) -> None:
    _ensure_case_defaults(case_payload)
    case_path = _case_file_path(case_payload["caseId"], workspace_root)
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(json.dumps(case_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_event(
    case_id: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    workspace_root: str | None,
) -> None:
    path = _events_file_path(case_id, workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "timestamp": _timestamp_now(),
        "eventType": event_type,
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(body, ensure_ascii=False) + "\n")


def _ensure_case_defaults(case_payload: dict[str, Any]) -> None:
    case_payload["caseId"] = str(case_payload.get("caseId", "") or "").strip()
    case_payload["title"] = str(case_payload.get("title", "") or "").strip()
    case_payload["status"] = str(case_payload.get("status", "awaiting-intake-approvals") or "").strip() or "awaiting-intake-approvals"
    case_payload["currentStageKey"] = str(case_payload.get("currentStageKey", "") or "").strip()
    intake = case_payload.setdefault("intake", {})
    intake["constraints"] = _string_list(intake.get("constraints", ()))
    intake["opportunitySignals"] = _merge_string_lists(intake.get("opportunitySignals", ()), intake.get("marketContext", ()))
    intake["businessModelFit"] = _string_list(intake.get("businessModelFit", ()))
    intake["stageFit"] = _string_list(intake.get("stageFit", ()))
    intake["companyContext"] = _string_list(intake.get("companyContext", ()))
    intake["ownerProposal"] = _merge_string_lists(intake.get("ownerProposal", ()), intake.get("roughDivisionOfWork", ()))
    intake["resourceEnvelope"] = _merge_string_lists(
        intake.get("resourceEnvelope", ()),
        intake.get("staffingCost", ()),
        intake.get("otherCosts", ()),
    )
    intake["prerequisites"] = _string_list(intake.get("prerequisites", ()))
    intake["requiredSupport"] = _string_list(intake.get("requiredSupport", ()))
    intake["expectedOutcomes"] = _string_list(intake.get("expectedOutcomes", ()))
    intake["slotAnswers"] = _normalize_slot_answers(intake.get("slotAnswers"))
    intake["clarificationRequired"] = bool(intake.get("clarificationRequired"))
    intake["caseCategory"] = _normalize_case_category(
        str(intake.get("caseCategory") or ""),
        case_id=case_payload["caseId"],
    )
    intake["referenceTheme"] = _normalize_reference_theme(
        str(intake.get("referenceTheme") or ""),
        case_id=case_payload["caseId"],
        case_category=intake["caseCategory"],
    )
    intake["packageHash"] = str(intake.get("packageHash") or "").strip()
    intake["releaseCounter"] = int(intake.get("releaseCounter") or 0)
    intake["releaseVersion"] = str(intake.get("releaseVersion") or "").strip()
    intake["releaseStatus"] = str(intake.get("releaseStatus") or "draft").strip() or "draft"
    intake["releaseIssuedAt"] = str(intake.get("releaseIssuedAt") or "").strip()
    intake["releaseIssuedByRole"] = str(intake.get("releaseIssuedByRole") or "").strip()
    text_fields = (
        "objective",
        "taskDescription",
        "expectedDelivery",
        "briefPath",
        "createdBy",
        "createdAt",
        "status",
    )
    for field in text_fields:
        intake[field] = str(intake.get(field, "") or "").strip()
    intake["clarificationSheet"] = _build_intake_clarification_sheet(
        task_description=intake["taskDescription"],
        slot_answers=intake["slotAnswers"],
        required=intake["clarificationRequired"],
    )
    intake["roleAssignmentMatrix"] = _build_intake_role_assignment_matrix()
    intake["approvals"] = _normalize_approvals(intake.get("approvals"), INTAKE_REQUIRED_APPROVERS)
    for stage in case_payload.get("stages", []):
        if not isinstance(stage, dict):
            continue
        template = _stage_template(stage.get("stageKey", ""))
        stage["businessOwner"] = str(stage.get("businessOwner") or template["businessOwner"]).strip()
        stage["actingOwner"] = str(stage.get("actingOwner") or template["actingOwner"]).strip()
        stage["moduleExecutor"] = str(stage.get("moduleExecutor") or template["moduleExecutor"]).strip()
        stage["gateOwner"] = str(stage.get("gateOwner") or template["gateOwner"]).strip()
        stage["ownerRole"] = str(stage.get("ownerRole") or stage["actingOwner"]).strip()
        stage["requiredApprovers"] = _stage_required_approvers(stage["actingOwner"])
        stage["approvals"] = _normalize_approvals(stage.get("approvals"), stage["requiredApprovers"])
        stage["packageHash"] = str(stage.get("packageHash") or "").strip()
        stage["releaseCounter"] = int(stage.get("releaseCounter") or 0)
        stage["releaseVersion"] = str(stage.get("releaseVersion") or "").strip()
        stage["releaseStatus"] = str(stage.get("releaseStatus") or "draft").strip() or "draft"
        stage["releaseIssuedAt"] = str(stage.get("releaseIssuedAt") or "").strip()
        stage["releaseIssuedByRole"] = str(stage.get("releaseIssuedByRole") or "").strip()
        stage["phaseKey"] = str(stage.get("phaseKey") or template["phaseKey"]).strip()
        stage["participantRoles"] = _string_list(stage.get("participantRoles", template["participantRoles"]))
        stage["inputRequirements"] = _string_list(stage.get("inputRequirements", template["inputRequirements"]))
        stage["superDevReferenceStages"] = _string_list(
            stage.get("superDevReferenceStages", template["superDevReferenceStages"])
        )
    case_payload["freezeControl"] = _normalize_freeze_control(case_payload.get("freezeControl"))
    case_payload["currentWorkItemPath"] = str(case_payload.get("currentWorkItemPath", "") or "").strip()
    case_payload["entryCheckpoint"] = _entry_checkpoint_for_case(case_payload)


def _write_intake_brief(
    case_payload: dict[str, Any],
    *,
    workspace_root: str | None,
    written_at: str,
) -> Path:
    path = _intake_brief_file_path(case_payload["caseId"], workspace_root)
    intake = case_payload["intake"]
    intake["packageHash"] = _package_hash(_build_intake_signature_payload(case_payload))
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-intake-brief",
        "caseId": case_payload["caseId"],
        "title": case_payload["title"],
        "priority": case_payload["priority"],
        "status": intake["status"],
        "createdAt": intake["createdAt"],
        "updatedAt": written_at,
        "createdBy": intake["createdBy"],
        "relatedModules": list(case_payload["relatedModules"]),
        "caseCategory": intake["caseCategory"],
        "referenceTheme": intake["referenceTheme"],
        "executionFlow": _execution_flow_for_case(case_payload),
        "stageLine": [stage["stageKey"] for stage in case_payload.get("stages", [])],
        "requiredApprovers": [approval["role"] for approval in intake["approvals"]],
        "approvals": list(intake["approvals"]),
        "packageHash": intake["packageHash"],
        "signaturePolicy": _signature_policy_payload(intake["approvals"], subject_kind="intake-brief"),
        "signatureChain": _approval_signature_chain(intake["approvals"]),
        "release": _release_metadata(intake),
        "objective": intake["objective"],
        "taskDescription": intake["taskDescription"],
        "constraints": list(intake["constraints"]),
        "freezeControl": dict(case_payload.get("freezeControl", {})),
        "expectedDelivery": intake["expectedDelivery"],
        "clarificationSheet": dict(intake["clarificationSheet"]),
        "roleAssignmentMatrix": list(intake["roleAssignmentMatrix"]),
        "briefing": {
            "opportunitySignals": list(intake["opportunitySignals"]),
            "businessModelFit": list(intake["businessModelFit"]),
            "stageFit": list(intake["stageFit"]),
            "companyContext": list(intake["companyContext"]),
            "ownerProposal": list(intake["ownerProposal"]),
            "resourceEnvelope": list(intake["resourceEnvelope"]),
            "prerequisites": list(intake["prerequisites"]),
            "requiredSupport": list(intake["requiredSupport"]),
            "expectedOutcomes": list(intake["expectedOutcomes"]),
            "slotAnswers": dict(intake["slotAnswers"]),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _build_intake_signature_payload(case_payload: dict[str, Any]) -> dict[str, Any]:
    intake = case_payload["intake"]
    return {
        "kind": "ipd-intake-brief",
        "caseId": case_payload["caseId"],
        "title": case_payload["title"],
        "priority": case_payload["priority"],
        "relatedModules": list(case_payload["relatedModules"]),
        "caseCategory": intake["caseCategory"],
        "referenceTheme": intake["referenceTheme"],
        "executionFlow": _execution_flow_for_case(case_payload),
        "stageLine": [stage["stageKey"] for stage in case_payload.get("stages", [])],
        "objective": intake["objective"],
        "taskDescription": intake["taskDescription"],
        "constraints": list(intake["constraints"]),
        "expectedDelivery": intake["expectedDelivery"],
        "clarificationSheet": dict(intake["clarificationSheet"]),
        "briefing": {
            "opportunitySignals": list(intake["opportunitySignals"]),
            "businessModelFit": list(intake["businessModelFit"]),
            "stageFit": list(intake["stageFit"]),
            "companyContext": list(intake["companyContext"]),
            "ownerProposal": list(intake["ownerProposal"]),
            "resourceEnvelope": list(intake["resourceEnvelope"]),
            "prerequisites": list(intake["prerequisites"]),
            "requiredSupport": list(intake["requiredSupport"]),
            "expectedOutcomes": list(intake["expectedOutcomes"]),
            "slotAnswers": dict(intake["slotAnswers"]),
        },
    }


def _build_intake_role_assignment_matrix() -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for item in _INTAKE_STAGE_ROLE_ASSIGNMENT_MATRIX:
        matrix.append(
            {
                "role": str(item.get("role") or "").strip(),
                "stageKeys": _string_list(item.get("stageKeys", ())),
                "taskType": str(item.get("taskType") or "").strip(),
                "status": str(item.get("status") or "").strip(),
                "canFreezeCase": bool(item.get("canFreezeCase")),
                "responsibility": str(item.get("responsibility") or "").strip(),
                "deliverables": _string_list(item.get("deliverables", ())),
            }
        )
    return matrix


def _stage_role_assignment_matrix(stage_key: str) -> list[dict[str, Any]]:
    normalized_stage_key = str(stage_key or "").strip()
    return [
        item
        for item in _build_intake_role_assignment_matrix()
        if normalized_stage_key in set(item.get("stageKeys", []))
    ]


def _build_intake_clarification_sheet(
    *,
    task_description: str,
    slot_answers: dict[str, str],
    required: bool,
) -> dict[str, Any]:
    slots: list[dict[str, Any]] = []
    missing_slot_keys: list[str] = []
    follow_up_questions: list[str] = []
    for template in _INTAKE_CLARIFICATION_SLOT_TEMPLATES:
        slot_key = str(template.get("slotKey") or "").strip()
        current_value = str(slot_answers.get(slot_key) or "").strip()
        if slot_key == "competitorReference" and not current_value and _task_mentions_competitor(task_description):
            current_value = "原始任务已提及竞品或对标，但总助仍需整理成可执行名单。"
        status = "provided" if current_value else ("needs-ceo-input" if required else "not-enforced")
        if required and not current_value:
            missing_slot_keys.append(slot_key)
            follow_up_questions.append(str(template.get("question") or "").strip())
        slots.append(
            {
                "slotKey": slot_key,
                "label": str(template.get("label") or "").strip(),
                "ownerRole": str(template.get("ownerRole") or "").strip(),
                "status": status,
                "requiredFor": _string_list(template.get("requiredFor", ())),
                "whyItMatters": str(template.get("whyItMatters") or "").strip(),
                "question": str(template.get("question") or "").strip(),
                "suggestedOptions": _string_list(template.get("suggestedOptions", ())),
                "currentValue": current_value,
                "allowCustom": True,
            }
        )
    overall_status = "ready-for-dispatch" if not missing_slot_keys else "needs-ceo-clarification"
    if not required:
        overall_status = "not-enforced"
    return {
        "required": required,
        "status": overall_status,
        "missingSlotKeys": missing_slot_keys,
        "followUpQuestions": follow_up_questions,
        "slots": slots,
    }


def _task_mentions_competitor(task_description: str) -> bool:
    lowered = str(task_description or "").strip().lower()
    if not lowered:
        return False
    return any(keyword in lowered for keyword in ("竞品", "对标", "competitor", "benchmark", "同类产品", "对照产品"))


def _current_stage(case_payload: dict[str, Any]) -> dict[str, Any] | None:
    current_stage_key = str(case_payload.get("currentStageKey") or "").strip()
    if not current_stage_key:
        return None
    return next(
        (stage for stage in case_payload["stages"] if stage["stageKey"] == current_stage_key),
        None,
    )


def _can_refine_intake(case_payload: dict[str, Any]) -> bool:
    if str(case_payload.get("currentStageKey") or "").strip():
        return False
    return all(str(stage.get("status") or "pending") == "pending" for stage in case_payload.get("stages", []))


def _next_pending_stage(case_payload: dict[str, Any]) -> dict[str, Any] | None:
    return next((stage for stage in case_payload["stages"] if stage["status"] == "pending"), None)


def _require_stage(case_payload: dict[str, Any], stage_key: str) -> dict[str, Any]:
    return next(
        stage for stage in case_payload["stages"] if stage["stageKey"] == stage_key
    )


def _stage_template(stage_key: str) -> dict[str, Any]:
    return _STAGE_TEMPLATE_LOOKUP[str(stage_key or "").strip()]


def _stage_index(stage_key: str) -> int:
    return next(index for index, template in enumerate(_STAGE_TEMPLATES) if template["stageKey"] == stage_key)


def _stage_index_for_case(case_payload: dict[str, Any], stage_key: str) -> int:
    normalized_stage_key = str(stage_key or "").strip()
    return next(
        index for index, stage in enumerate(case_payload.get("stages", [])) if str(stage.get("stageKey") or "").strip() == normalized_stage_key
    )


def _first_stage_key(case_payload: dict[str, Any]) -> str:
    for stage in case_payload.get("stages", []):
        stage_key = str(stage.get("stageKey") or "").strip()
        if stage_key:
            return stage_key
    return ""


def _execution_flow_for_case(case_payload: dict[str, Any]) -> str:
    first_stage_key = _first_stage_key(case_payload)
    if first_stage_key == "backlog":
        return "agile-improvement"
    intake = case_payload.get("intake") if isinstance(case_payload.get("intake"), dict) else {}
    if str(intake.get("caseCategory") or "").strip() == _CASE_CATEGORY_PROCESS_IMPROVEMENT:
        return "legacy-ipd-improvement"
    return "ipd-delivery"


def _initial_stage_templates(*, case_category: str, reference_theme: str) -> tuple[dict[str, Any], ...]:
    if str(case_category or "").strip() == _CASE_CATEGORY_PROCESS_IMPROVEMENT:
        return _PROCESS_IMPROVEMENT_STAGE_TEMPLATES
    return _STAGE_TEMPLATES


def _input_refs(case_payload: dict[str, Any]) -> list[str]:
    refs = []
    if str(case_payload["intake"].get("briefPath") or "").strip():
        refs.append("workbench/ipd/cases/" + case_payload["caseId"] + "/intake-brief.json")
    refs.append("workbench/ipd/cases/" + case_payload["caseId"] + "/case.json")
    refs.extend(
        stage["outputPath"]
        for stage in case_payload["stages"]
        if str(stage.get("outputPath") or "").strip()
    )
    return refs


def _stage_summary(case_payload: dict[str, Any], stage: dict[str, Any]) -> str:
    participants = "、".join(_string_list(stage.get("participantRoles", ())))
    participant_text = f"并协同 {participants}" if participants else ""
    return (
        f"{stage['actingOwner']} 需要基于 CEO / 总助已整理并获签核的 intake briefing，"
        f"围绕目标“{case_payload['intake']['objective']}”推进 {stage['title']}（{stage['phaseKey']}）{participant_text}，"
        f"并在提交后等待 CEO 签名与 CEOChiefOfStaff 最终验证签发。"
    )


def _stage_requires_owner_action(stage: dict[str, Any]) -> bool:
    return str(stage.get("actingOwner") or "").strip() in _AUTOPILOT_OWNER_ACTION_ROLES


def _stage_requires_real_execution(stage_key: str) -> bool:
    return str(stage_key or "").strip() in _REAL_EXECUTION_STAGE_KEYS


def _validate_stage_submission_evidence(
    stage: dict[str, Any],
    *,
    evidence: Iterable[str],
    object_path: str,
) -> None:
    refs = [*(_string_list(evidence)), str(object_path or "").strip()]
    if not _has_non_generated_stage_evidence(refs):
        raise ValueError(
            f"stage {stage['stageKey']} requires at least one non-generated evidence path outside workbench/knowledge/autopilot artifacts"
        )
    if not _stage_requires_real_execution(stage.get("stageKey", "")):
        return
    if _has_real_execution_evidence(refs):
        return
    raise ValueError(
        f"stage {stage['stageKey']} requires at least one real source/test/deploy evidence path outside docs/workbench generated artifacts"
    )


def _has_non_generated_stage_evidence(refs: Iterable[str]) -> bool:
    for ref in refs:
        normalized = str(ref or "").strip().replace("\\", "/")
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered.startswith(("knowledge/", "workbench/")):
            continue
        if any(segment in lowered for segment in ("/knowledge/", "/workbench/", "/participant-records/", "/autopilot-packages/", "/phase-results/")):
            continue
        return True
    return False


def _has_real_execution_evidence(refs: Iterable[str]) -> bool:
    for ref in refs:
        normalized = str(ref or "").strip().replace("\\", "/")
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered.startswith(("docs/", "knowledge/", "workbench/")):
            continue
        if any(segment in lowered for segment in ("/docs/", "/knowledge/", "/workbench/")):
            continue
        if any(segment in lowered for segment in ("/participant-records/", "/autopilot-packages/", "/phase-results/")):
            continue
        if lowered.endswith(".md"):
            continue
        filename = Path(lowered).name
        if filename in _REAL_EXECUTION_RESERVED_FILENAMES:
            continue
        return True
    return False


def _find_real_execution_integrity_issue(
    case_payload: dict[str, Any],
    *,
    workspace_root: str | None,
) -> dict[str, str] | None:
    for stage in case_payload.get("stages", []):
        stage_key = str(stage.get("stageKey") or "").strip()
        if str(stage.get("status") or "").strip() not in {"submitted", "completed"}:
            continue
        output_payload = _load_stage_output_payload(case_payload, stage, workspace_root=workspace_root)
        refs: list[str] = []
        if output_payload is not None:
            refs.extend(_string_list(output_payload.get("evidence", ())))
            refs.append(str(output_payload.get("objectPath") or "").strip())
        if not _has_non_generated_stage_evidence(refs):
            return {
                "stageKey": stage_key,
                "reason": _NON_GENERATED_EVIDENCE_BLOCK_REASON,
            }
        if not _stage_requires_real_execution(stage_key):
            continue
        if _has_real_execution_evidence(refs):
            continue
        return {
            "stageKey": stage_key,
            "reason": _REAL_EXECUTION_BLOCK_REASON,
        }
    return None


def _load_stage_output_payload(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
) -> dict[str, Any] | None:
    output_path_text = str(stage.get("outputPath") or "").strip()
    if not output_path_text:
        return None
    output_path = Path(output_path_text)
    if not output_path.is_absolute():
        output_path = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root) / output_path
    if not output_path.exists():
        return None
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _apply_real_execution_integrity_issue(
    case_payload: dict[str, Any],
    *,
    issue_stage_key: str,
    issue_reason: str,
    workspace_root: str | None,
    now: str,
) -> None:
    issue_stage = _require_stage(case_payload, issue_stage_key)
    should_emit_event = (
        str(case_payload.get("status") or "").strip() != "blocked"
        or str(issue_stage.get("blockedReason") or "").strip() != issue_reason
    )
    reset_downstream = False
    for stage in case_payload["stages"]:
        if stage["stageKey"] == issue_stage_key:
            reset_downstream = True
            stage["status"] = "rejected"
            stage["outputPath"] = ""
            stage["submittedAt"] = ""
            stage["completedAt"] = ""
            stage["blockedReason"] = issue_reason
            stage["outputSummary"] = ""
            stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
            stage["lastUpdatedAt"] = now
            continue
        if not reset_downstream:
            continue
        _reset_stage_to_pending(stage, now=now)
    case_payload["status"] = "blocked"
    case_payload["currentStageKey"] = issue_stage_key
    case_payload["currentWorkItemPath"] = str(issue_stage.get("workItemPath") or "").strip()
    if should_emit_event:
        event_name = "real-execution-evidence-missing" if issue_reason == _REAL_EXECUTION_BLOCK_REASON else "stage-evidence-generated-only"
        _append_event(
            case_payload["caseId"],
            event_name,
            {
                "stageKey": issue_stage_key,
                "reason": issue_reason,
            },
            workspace_root=workspace_root,
        )


def _reset_stage_to_pending(stage: dict[str, Any], *, now: str) -> None:
    stage["status"] = "pending"
    stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
    stage["workItemPath"] = ""
    stage["outputPath"] = ""
    stage["packageHash"] = ""
    stage["releaseCounter"] = 0
    stage["releaseVersion"] = ""
    stage["releaseStatus"] = "draft"
    stage["releaseIssuedAt"] = ""
    stage["releaseIssuedByRole"] = ""
    stage["activatedAt"] = ""
    stage["submittedAt"] = ""
    stage["completedAt"] = ""
    stage["blockedReason"] = ""
    stage["outputSummary"] = ""
    stage["lastUpdatedAt"] = now


def _build_approvals(
    roles: Iterable[str],
    *,
    auto_approved_role: str | None,
    now: str,
) -> list[dict[str, Any]]:
    approvals: list[dict[str, Any]] = []
    for index, role in enumerate(_string_list(roles)):
        auto_approved = auto_approved_role is not None and role == auto_approved_role and index == 0
        approvals.append(
            {
                "role": role,
                "status": "approved" if auto_approved else "pending",
                "note": "创建动作已视为当前角色签核" if auto_approved else "",
                "updatedAt": now if auto_approved else "",
                "packageHash": "",
                "signature": "",
                "signerAddress": "",
                "publicKey": "",
                "credentialType": "",
                "credentialHint": "",
                "verificationStatus": "not-signed" if not auto_approved else "not-required",
                "verifiedRoles": [],
                "verifiedAt": now if auto_approved else "",
            }
        )
    return approvals


def _merge_string_lists(*values: Iterable[str]) -> list[str]:
    merged: list[str] = []
    for value in values:
        merged.extend(_string_list(value))
    return merged


def _normalize_slot_answers(slot_answers: object) -> dict[str, str]:
    if not isinstance(slot_answers, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in slot_answers.items():
        slot_key = str(key or "").strip()
        slot_value = str(value or "").strip()
        if slot_key and slot_value:
            normalized[slot_key] = slot_value
    return normalized


def _normalize_freeze_control(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized = {
        "active": bool(value.get("active")),
        "status": str(value.get("status") or "").strip(),
        "frozenAt": str(value.get("frozenAt") or "").strip(),
        "frozenByRole": str(value.get("frozenByRole") or "").strip(),
        "stageKey": str(value.get("stageKey") or "").strip(),
        "domain": str(value.get("domain") or "").strip(),
        "reason": str(value.get("reason") or "").strip(),
        "previousCaseStatus": str(value.get("previousCaseStatus") or "").strip(),
        "previousStageStatus": str(value.get("previousStageStatus") or "").strip(),
        "previousBlockedReason": str(value.get("previousBlockedReason") or "").strip(),
        "resolvedAt": str(value.get("resolvedAt") or "").strip(),
        "resolvedByRole": str(value.get("resolvedByRole") or "").strip(),
        "resolutionNote": str(value.get("resolutionNote") or "").strip(),
    }
    if not normalized["active"] and not any(
        normalized[key]
        for key in (
            "status",
            "frozenAt",
            "frozenByRole",
            "stageKey",
            "domain",
            "reason",
            "previousCaseStatus",
            "previousStageStatus",
            "previousBlockedReason",
            "resolvedAt",
            "resolvedByRole",
            "resolutionNote",
        )
    ):
        return {}
    return normalized


def _approval_snapshot(roles: Iterable[str]) -> list[dict[str, Any]]:
    return [
        {
            "role": role,
            "status": "pending",
            "note": "",
            "packageHash": "",
            "signature": "",
            "signerAddress": "",
            "publicKey": "",
            "credentialType": "",
            "credentialHint": "",
            "verificationStatus": "not-signed",
            "verifiedRoles": [],
            "verifiedAt": "",
        }
        for role in _string_list(roles)
    ]


def _normalize_approvals(
    approvals: object,
    required_roles: Iterable[str],
) -> list[dict[str, Any]]:
    existing_by_role: dict[str, list[dict[str, Any]]] = {}
    if isinstance(approvals, list):
        for item in approvals:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            if role:
                existing_by_role.setdefault(role, []).append(item)
    normalized: list[dict[str, Any]] = []
    prior_approved = True
    for role in _string_list(required_roles):
        existing_items = existing_by_role.get(role, [])
        existing = existing_items.pop(0) if existing_items else {}
        status = str(existing.get("status") or "pending").strip() or "pending"
        if not prior_approved and status != "pending":
            status = "pending"
            note = ""
            updated_at = ""
            package_hash = ""
            signature = ""
            signer_address = ""
            public_key = ""
            credential_type = ""
            credential_hint = ""
            verification_status = "not-signed"
            verified_roles: list[str] = []
            verified_at = ""
        else:
            note = str(existing.get("note") or "").strip()
            updated_at = str(existing.get("updatedAt") or "").strip()
            package_hash = str(existing.get("packageHash") or "").strip()
            signature = str(existing.get("signature") or "").strip()
            signer_address = str(existing.get("signerAddress") or "").strip()
            public_key = str(existing.get("publicKey") or "").strip()
            credential_type = str(existing.get("credentialType") or "").strip()
            credential_hint = str(existing.get("credentialHint") or "").strip()
            verification_status = str(existing.get("verificationStatus") or "not-signed").strip() or "not-signed"
            verified_roles = _string_list(existing.get("verifiedRoles", ()))
            verified_at = str(existing.get("verifiedAt") or "").strip()
        normalized.append(
            {
                "role": role,
                "status": status,
                "note": note,
                "updatedAt": updated_at,
                "packageHash": package_hash,
                "signature": signature,
                "signerAddress": signer_address,
                "publicKey": public_key,
                "credentialType": credential_type,
                "credentialHint": credential_hint,
                "verificationStatus": verification_status,
                "verifiedRoles": verified_roles,
                "verifiedAt": verified_at,
            }
        )
        prior_approved = prior_approved and status == "approved"
    return normalized


def _approval_index_for_role(
    approvals: list[dict[str, Any]],
    *,
    role: str,
    prefer_pending: bool,
) -> int:
    matching_indexes = [
        index
        for index, approval in enumerate(approvals)
        if str(approval.get("role") or "").strip() == role
    ]
    if not matching_indexes:
        raise ValueError(f"approval role not found: {role}")
    if prefer_pending:
        for index in matching_indexes:
            if str(approvals[index].get("status") or "pending").strip() == "pending":
                return index
    return matching_indexes[0]


def _update_approval(
    approvals: list[dict[str, Any]],
    *,
    role: str,
    decision: str,
    note: str,
    now: str,
) -> None:
    normalized = decision.strip().lower()
    if normalized not in {"approved", "rejected"}:
        raise ValueError(f"unsupported decision: {decision}")
    target_index = _approval_index_for_role(approvals, role=role, prefer_pending=True)
    for predecessor in approvals[:target_index]:
        if predecessor["status"] != "approved":
            raise ValueError(f"{role} cannot sign before {predecessor['role']}")
    approval = approvals[target_index]
    approval["status"] = normalized
    approval["note"] = note.strip()
    approval["updatedAt"] = now


def _stage_required_approvers(owner_role: str) -> list[str]:
    return [owner_role, *STAGE_FINAL_APPROVERS]


def _default_wallet_seed(role: str) -> str:
    return f"role-wallet::{str(role or '').strip() or 'unknown-role'}"


def _canonical_package_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _package_hash(payload: Any) -> str:
    return "0x" + hashlib.sha3_256(_canonical_package_bytes(payload)).hexdigest()


def _release_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    status = str(payload.get("releaseStatus") or "draft").strip() or "draft"
    return {
        "status": status,
        "version": str(payload.get("releaseVersion") or "").strip(),
        "issuedAt": str(payload.get("releaseIssuedAt") or "").strip(),
        "issuedByRole": str(payload.get("releaseIssuedByRole") or "").strip(),
    }


def _approval_signature_chain(approvals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    for approval in approvals:
        chain.append(
            {
                "role": str(approval.get("role") or "").strip(),
                "status": str(approval.get("status") or "").strip(),
                "note": str(approval.get("note") or "").strip(),
                "updatedAt": str(approval.get("updatedAt") or "").strip(),
                "packageHash": str(approval.get("packageHash") or "").strip(),
                "signature": str(approval.get("signature") or "").strip(),
                "signerAddress": str(approval.get("signerAddress") or "").strip(),
                "publicKey": str(approval.get("publicKey") or "").strip(),
                "credentialType": str(approval.get("credentialType") or "").strip(),
                "credentialHint": str(approval.get("credentialHint") or "").strip(),
                "verificationStatus": str(approval.get("verificationStatus") or "").strip(),
                "verifiedRoles": _string_list(approval.get("verifiedRoles", ())),
                "verifiedAt": str(approval.get("verifiedAt") or "").strip(),
            }
        )
    return chain


def _signature_policy_payload(required_roles: Iterable[str], *, subject_kind: str) -> dict[str, Any]:
    roles: list[str] = []
    for item in required_roles:
        if isinstance(item, dict):
            role = str(item.get("role") or "").strip()
        else:
            role = str(item or "").strip()
        if role:
            roles.append(role)
    return {
        "subjectKind": subject_kind,
        "keyFormat": "web3-simulated",
        "credentialInputs": ["private-key", "mnemonic"],
        "curve": "secp256k1",
        "signatureAlgorithm": "ecdsa",
        "hashAlgorithm": "sha3_256-simulated",
        "approvalOrder": roles,
        "finalIssuerRole": "CEOChiefOfStaff",
    }


def _verify_predecessor_signatures(
    approvals: list[dict[str, Any]],
    *,
    role: str,
    package_hash: str,
) -> list[str]:
    target_index = _approval_index_for_role(approvals, role=role, prefer_pending=True)
    verified_roles: list[str] = []
    for approval in approvals[:target_index]:
        current_role = str(approval.get("role") or "").strip()
        if str(approval.get("status") or "").strip() != "approved":
            raise ValueError(f"{role} cannot sign before {current_role}")
        signature = str(approval.get("signature") or "").strip()
        public_key = str(approval.get("publicKey") or "").strip()
        approval_hash = str(approval.get("packageHash") or "").strip()
        if not signature or not public_key or not approval_hash:
            raise ValueError(f"{current_role} approval is missing web3 signature material")
        if approval_hash != package_hash:
            raise ValueError(f"{current_role} signed a different package hash")
        if not verify_web3_signature(package_hash, signature, public_key):
            raise ValueError(f"{current_role} signature verification failed")
        verified_roles.append(current_role)
    return verified_roles


def _record_signed_approval(
    approvals: list[dict[str, Any]],
    *,
    role: str,
    decision: str,
    note: str,
    now: str,
    package_hash: str,
    signing_key: str = "",
    mnemonic: str = "",
    default_seed: str,
) -> dict[str, Any]:
    normalized = decision.strip().lower()
    if normalized not in {"approved", "rejected"}:
        raise ValueError(f"unsupported decision: {decision}")
    verified_roles = _verify_predecessor_signatures(approvals, role=role, package_hash=package_hash)
    target_index = _approval_index_for_role(approvals, role=role, prefer_pending=True)
    envelope = sign_web3_package_hash(
        package_hash,
        signing_key=signing_key,
        mnemonic=mnemonic,
        default_seed=default_seed,
    )
    approval = approvals[target_index]
    approval["status"] = normalized
    approval["note"] = note.strip()
    approval["updatedAt"] = now
    approval["packageHash"] = envelope["packageHash"]
    approval["signature"] = envelope["signature"]
    approval["signerAddress"] = envelope["signerAddress"]
    approval["publicKey"] = envelope["publicKey"]
    approval["credentialType"] = envelope["credentialType"]
    approval["credentialHint"] = envelope["credentialHint"]
    approval["verificationStatus"] = "verified" if verified_roles else "not-required"
    approval["verifiedRoles"] = verified_roles
    approval["verifiedAt"] = now
    return approval


def _issue_release(payload: dict[str, Any], *, case_id: str, subject_token: str, issued_by_role: str, now: str) -> str:
    counter = int(payload.get("releaseCounter") or 0) + 1
    version = f"{case_id}-{subject_token}-V{counter:03d}"
    payload["releaseCounter"] = counter
    payload["releaseVersion"] = version
    payload["releaseStatus"] = "issued"
    payload["releaseIssuedAt"] = now
    payload["releaseIssuedByRole"] = issued_by_role
    return version


def _approval_rollup(approvals: list[dict[str, str]]) -> str:
    statuses = {str(item.get("status") or "pending") for item in approvals}
    if "rejected" in statuses:
        return "rejected"
    if statuses == {"approved"}:
        return "approved"
    return "pending"


def _normalize_identifier(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("case_id is required")
    normalized = []
    for character in text:
        if character.isalnum() or character in {"-", "_", "."}:
            normalized.append(character)
        else:
            normalized.append("-")
    identifier = "".join(normalized).strip("-")
    if not identifier:
        raise ValueError("case_id must contain at least one valid identifier character")
    return identifier


def _branch_id(case_id: str) -> str:
    return "ipd-" + case_id.replace(".", "-").replace("_", "-").lower()


def _string_list(values: Iterable[str]) -> list[str]:
    items: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            items.append(text)
    return items


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
