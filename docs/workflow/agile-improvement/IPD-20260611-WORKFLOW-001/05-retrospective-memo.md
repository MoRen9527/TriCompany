# IPD-20260611-WORKFLOW-001 Retrospective Memo

## What Worked

### 1. 流程优化线已经形成可连续推进的真实前门

- 当前 case 已从 CEO demand 驱动的 intake，连续推进到 backlog、sprint-planning、sprint-execution、sprint-review，并完成对应 release issuance。
- 这说明 agile-improvement 六阶段中的前四段已能在 live support-root 上被真实触发、提交、签核和切换。
- 对总助来说，CEO 提需求不再只是口头入口，而是可以被稳定转成 governed case 与阶段产物。

### 2. 签核链与 release issuance 的治理模型已经基本站稳

- intake 使用 CEO -> CEOChiefOfStaff 的双签顺序，stage output 使用 owner -> CEO -> CEOChiefOfStaff 的顺序，当前已在 live case 中持续成立。
- 重复角色审批链已经被 runtime 正确处理，允许 owner 与最终签发人在同一流程里出现同角色而不串位。
- 每个阶段都能把 package hash、signature chain、release version 和 events 一起落盘，具备后续审计基础。

### 3. 先做聚焦验证再推进阶段的工作方式是有效的

- 本轮没有用大范围 diff 代替验证，而是围绕 runtime、CLI、测试和 live artifacts 做最小可执行检查。
- sprint-execution 的聚焦 unittest 与 sprint-review 的 live output 验证，证明“先验证再签发”在当前宿主边界内可执行。
- 用 output JSON、events.jsonl 和新激活 work item 做回读，比只看终端滚动结果更稳定。

## What Did Not Work

### 1. 流程优化线和真实项目交付线仍然容易被混写

- 如果不在每个阶段反复强调边界，这条 case 很容易被误写成模型 API 中转平台已经开始真实交付验证。
- 当前事实只证明流程优化前门和签核链已经跑通，不证明真实 Discovery、Intelligence、PRD 或交付链已完成。

### 2. 宿主执行仍依赖显式人工签核与人工收口

- CEO 与总助的签核目前仍需要显式触发，不能写成全自动签发系统。
- 当前自动化更准确的表述是“自动生成产物与待签核状态”，而不是“自动完成全链路治理”。

### 3. 操作可观测性仍有噪声，必须继续依赖结构化回读

- 终端摘要有时只展示单步结果，不能单靠滚动输出判断整个推进是否已经完成。
- 如果不回读 output、case 和 events，就容易误判 stage 是否真正前进、release 是否真正签发。

## Next Backlog Seeds

### 1. 固化 validation-handoff 的正式交接口径

- 明确哪些流程规则已可视为当前阶段稳定基线。
- 明确 validation-handoff 必须输出的 checklist、候选真实项目方向和 project-delivery case 开案条件。

### 2. 继续降低签核与验证过程中的人工噪声

- 为关键命令补齐更稳定的结构化摘要读取方式，减少对终端滚动内容的依赖。
- 把常用的 live 验证切片固定成可重复复用的检查顺序。

### 3. 另开真实 project-delivery case 做独立验证

- 在流程优化线完成 validation-handoff 后，独立开启模型 API 中转平台的真实 project-delivery case。
- 新 case 必须承接真实 Discovery、Intelligence、PRD、实现与交付验证，不能借当前流程优化 case 直接宣告成立。

## Retrospective Guardrails

- 当前结论成立于本地 Copilot-host 正式接管阶段，不等于 TriMC 正式宿主已经接管。
- 当前结论成立于流程优化线，不等于真实商业交付线已经验证完成。
- validation-handoff 必须把“已证明有效”和“待真实项目验证”明确拆开，不能混写。

## Evidence Surface

- TriCompany/docs/workflow/agile-improvement/IPD-20260611-WORKFLOW-001/04-sprint-review-memo.md
- TriCompany/docs/workflow/agile-improvement/IPD-20260611-WORKFLOW-001/04-sprint-review-package.json
- TriCompany/runtime/cognition/ipd_case_engine.py
- TriCompany/runtime/cognition/chief_of_staff_ipd_case.py
- TriCompany/runtime/cognition/chief_of_staff_ipd_case_validation.py
