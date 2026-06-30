# Module Routing Mode Post-Facto Backfill

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/agile-improvement/IPD-20260612-WORKFLOW-002/14-module-routing-mode-post-facto-backfill.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 当前不发布；先作为 WORKFLOW-002 后续增量留痕
- lastSyncedAt: 2026-06-29

## 1. Backfill 含义

`post-facto backfill` 指**事后回填**：代码或执行改动已经先发生，随后把这次改动补登记到对应 workflow case 的证据链里，避免真实代码状态与流程治理记录脱节。

本次 backfill 登记的是：`task-intake` 相关模块推断从单纯 deterministic 规则，扩展为 `deterministic | cpo | auto` 三模式，并允许在 orchestration 层通过 `CPO` 模块路由 hook 进行产品语义判断。

## 2. 变更边界

### 本次已经完成的代码增量

- 目标入口：[../../../../runtime/cognition/chief_of_staff_ipd_case.py](../../../../runtime/cognition/chief_of_staff_ipd_case.py)
- 验证入口：[../../../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../../../runtime/cognition/chief_of_staff_ipd_case_validation.py)

已落地能力：

1. `task-intake` 新增 `--module-routing-mode deterministic|cpo|auto`。
2. 默认模式为 `auto`。
3. `deterministic` 模式只走本地中央模块关键词规则。
4. `cpo` 模式强制调用 CPO module router hook。
5. `auto` 模式在 CPO hook 可用时优先调用 CPO；CPO 不可用或返回无效时回退 deterministic。
6. CPO 返回结果会经过 module catalog / alias 校验，不允许未知模块直接写入 case。
7. CPO 若返回 `needsBusinessStrategyEscalation=true`，流程应阻断并升级 `BusinessStrategy`，不得静默回退。

### 本次未改变的边界

1. 本次没有把 `_infer_related_modules()` 改成直接调用 subagent 的非纯函数。
2. 本次没有声明 CPO hook 已经在宿主侧真实部署。
3. 本次没有改变 IPD stage 模板、签核链或 `WORKFLOW-002` 的正式 stage 状态。
4. 本次不把“hook 接口可用”写成“CPO 已完成真实产品判断”。

## 3. 为什么要回填到 WORKFLOW-002

这次改动虽然是局部代码增强，但它改变了 IPD intake 阶段的模块路由语义：

- 相关模块不再只能由硬编码关键词推断。
- 产品语义判断可以交给 CPO 路由器完成。
- 代码层增加了 module catalog 校验和 BusinessStrategy escalation 保护。

因此它属于 `WORKFLOW-002` 的流程优化后续增量，而不是普通业务功能修补。若不回填，`WORKFLOW-002` 的流程证据会落后于 runtime / CLI 真实行为。

## 4. 本次 backfill 结论

| 项目 | 结论 |
| --- | --- |
| backfillId | `WF-002-MODULE-ROUTING-BACKFILL-001` |
| relatedCase | `IPD-20260612-WORKFLOW-002` |
| incrementType | `post-facto-runtime-and-cli-backfill` |
| runtimeSurface | `task-intake relatedModules inference` |
| decision | `recorded-as-follow-up-increment` |
| mergeReady | `yes-for-workflow-record` |
| requiresBusinessStrategyEscalation | `no` |

## 5. 验证记录

已执行的最小验证：

```powershell
Set-Location D:\OneDrive\Code\ai\TriCompany
python -m unittest runtime.cognition.chief_of_staff_ipd_case_validation.ChiefOfStaffIpdCaseValidationTest.test_infer_related_modules_uses_central_module_map_for_platform_tasks runtime.cognition.chief_of_staff_ipd_case_validation.ChiefOfStaffIpdCaseValidationTest.test_infer_related_modules_adds_pc_host_and_local_runtime_stack runtime.cognition.chief_of_staff_ipd_case_validation.ChiefOfStaffIpdCaseValidationTest.test_task_intake_default_auto_uses_cpo_module_router_when_available runtime.cognition.chief_of_staff_ipd_case_validation.ChiefOfStaffIpdCaseValidationTest.test_task_intake_deterministic_mode_skips_cpo_module_router runtime.cognition.chief_of_staff_ipd_case_validation.ChiefOfStaffIpdCaseValidationTest.test_cpo_module_routing_mode_requires_configured_router runtime.cognition.chief_of_staff_ipd_case_validation.ChiefOfStaffIpdCaseValidationTest.test_cli_task_intake_initializes_intake_briefing_from_freeform_task runtime.cognition.chief_of_staff_ipd_case_validation.ChiefOfStaffIpdCaseValidationTest.test_task_intake_auto_generates_date_slug_case_id
python -m compileall -q runtime\cognition\chief_of_staff_ipd_case.py runtime\cognition\chief_of_staff_ipd_case_validation.py
```

验证结论：

- `auto` 模式在 CPO hook 可用时会使用 CPO 返回的模块。
- `deterministic` 模式不会调用 CPO hook。
- `cpo` 模式在未配置 CPO hook 时会失败，不静默回退。
- 现有 `task-intake` 基础流程保持可用。

## 6. 后续动作

1. 若宿主侧要真实启用 CPO module router，需要补出 CPO hook 的宿主发布与调用说明。
2. 若 CPO 判断涉及新增长期模块、模块边界变化或当前商业路径取舍，必须升级 `BusinessStrategy`，不得由 CPO 直接写成既成事实。
3. 后续若继续增强 module routing，应优先进入 `WORKFLOW-002` 的下一轮 backlog seeds，而不是只改代码不回填。

## 7. Guardrails

1. 不得把本次 backfill 写成 `WORKFLOW-002` 全阶段已重新跑完。
2. 不得把 CPO hook 接口写成 CPO 真实岗位审批已完成。
3. 不得让未知模块绕过 catalog / alias 校验写入 IPD case。
4. 不得用 `auto` 的 deterministic fallback 掩盖需要 `BusinessStrategy` 裁决的边界问题。

## 8. Evidence Surface

- [../../../../runtime/cognition/chief_of_staff_ipd_case.py](../../../../runtime/cognition/chief_of_staff_ipd_case.py)
- [../../../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../../../runtime/cognition/chief_of_staff_ipd_case_validation.py)
- [06-validation-handoff-plan.md](06-validation-handoff-plan.md)
- [14-module-routing-mode-post-facto-backfill-package.json](14-module-routing-mode-post-facto-backfill-package.json)
