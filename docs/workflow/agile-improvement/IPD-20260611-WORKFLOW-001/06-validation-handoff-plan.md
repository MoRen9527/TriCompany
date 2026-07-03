# IPD-20260611-WORKFLOW-001 Validation Handoff Plan

## Stabilized Rules

### 1. CEO demand 已经是当前流程优化线的真实入口

- 当前流程优化 case 已证明 CEO demand 可以被稳定转成 governed intake，而不是停留在口头指令层。
- 总助可基于 intake briefing、clarification sheet、work item 与 output artifacts，把事项连续推进到 backlog、planning、execution、review、retrospective。
- 这条规则已经在 live support-root 上被完整跑通，可作为后续真实 case 的固定前门。

### 2. 签核链、package hash 与 release issuance 已形成稳定治理基线

- intake 使用 CEO -> CEOChiefOfStaff 的双签顺序；stage output 使用 owner -> CEO -> CEOChiefOfStaff 的顺序。
- package hash、signature chain、release version 和 events.jsonl 已能在每个已完成阶段稳定落盘。
- 重复角色审批链不再会把 owner 与最终签发人的位置串乱，当前 runtime 行为已可复用到后续真实 case。

### 3. 当前阶段应坚持“先做聚焦验证，再做阶段签发”

- 不再用大范围 diff 或口头确认替代行为验证。
- 对关键阶段，至少要回读 live output、case 状态、events 与新 work item，确认真正落盘后再放行下一阶段。
- 这条规则应继承到后续真实 project-delivery case，避免把文档推进误当成真实验证。

## Recommended Validation Case

### 1. 建议另开独立 project-delivery case

- 建议方向：模型 API 中转平台。
- 建议 caseCategory：project-delivery。
- 建议 referenceTheme：PLATFORM。
- 建议目标：在真实业务边界内跑通 Discovery、Intelligence、PRD、实现与验证，检验当前已固化的流程前门能否支撑真正的项目交付。

### 2. 建议由新 case 独立承接的真实验证范围

- Discovery：竞品、功能、官方文档和用户场景研究。
- Intelligence：代码、开源方案、架构路径与成本约束研究。
- Designing / Coding / Verify：围绕模型 API 中转平台本体做真实方案、实现与验证。
- 以上内容不得回填到当前 WORKFLOW 流程优化 case 中伪装为已验证结论。

## Handoff Checklist For Real IPD Case

### 1. 开案前必须继承的流程规则

- 继续使用 CEO demand 作为需求起点。
- 继续要求总助做 intake 补槽、任务分发和阶段收口。
- 继续使用 web3-simulated 签名链和 release issuance 作为阶段签发基线。

### 2. 开案时必须重新填写的真实项目输入

- 模型 API 中转平台的真实目标用户、场景、预算护栏与成功信号。
- 真实项目的竞品基线、技术边界、首轮最小交付范围与明确 out-of-scope。
- 真实项目所需的产品、技术、测试与部署证据路径。

### 3. 明确禁止继承的错误外推

- 不得把当前流程优化 case 的通过，直接写成模型 API 中转平台已经验证完成。
- 不得把当前本地 Copilot-host 接管阶段，写成 TriMC 正式宿主已经切换完成。
- 不得把当前流程优化线的 review/retrospective 结论，当成真实项目 PRD 或技术方案结论。

## Completion Conclusion

- 当前 agile-improvement case 已完成“公司级 IPD 流程优化前门固化”的阶段性目标。
- 到 validation-handoff 为止，这条 case 的职责是形成稳定前门、签核链和阶段治理口径，不直接承担真实项目交付。
- 下一步应另开真实 project-delivery case，用模型 API 中转平台作为独立验证对象，检验这套流程能否支撑真实商业交付。

## Evidence Surface

- TriCompany/docs/workflow/agile-improvement/IPD-20260611-WORKFLOW-001/05-retrospective-memo.md
- TriCompany/docs/workflow/agile-improvement/IPD-20260611-WORKFLOW-001/05-retrospective-package.json
- TriCompany/runtime/cognition/ipd_case_engine.py
- TriCompany/runtime/cognition/chief_of_staff_ipd_case.py
- TriCompany/runtime/cognition/chief_of_staff_ipd_case_validation.py
