# IPD-20260611-WORKFLOW-001 Sprint Plan

## Sprint Goal

- 把当前 WORKFLOW 流程优化 case 从“已可进入 backlog”推进到“agile-improvement 六阶段可以连续运行、可签发、可回退、可验证”的稳定状态。
- 保持流程优化线与真实项目交付线完全分离，不让这条 case 重新漂移成伪 Discovery / Intelligence 项目。

## Timebox And Resource Window

- 当前节奏：沿用 intake 约束，在 1 周窗口内完成 sprint-planning、sprint-execution 的首轮闭环验证。
- 资源窗口：以现有人力和少量工具成本完成，不新增正式宿主切换或额外平台建设任务。
- 参与角色：CEOChiefOfStaff 主持计划与收口，ChiefProductOfficer 负责边界与 review 口径，ChiefTechnologyOfficer 负责实现与验证切片。

## Ordered Task Breakdown

### 1. Freeze Workflow Contract

- 负责人：CEOChiefOfStaff
- 目标：把 agile-improvement 的阶段边界、审批顺序、回退入口和 live/source 对齐要求固定下来。
- 产出：明确的阶段输入输出、签发顺序、交接约束。

### 2. Prepare Execution Slice

- 负责人：ChiefTechnologyOfficer
- 协同：CEOChiefOfStaff
- 目标：把 sprint-execution 限定在 runtime、CLI、tests、workflow docs 和 live support-root 对齐这几个可验证改动面。
- 产出：执行清单、最小验证命令、预期 evidence 路径。

### 3. Lock Product Boundary And Review Gate

- 负责人：ChiefProductOfficer
- 协同：CEOChiefOfStaff
- 目标：把流程优化线的边界和 review 口径固定，防止把真实项目交付验证混进来。
- 产出：review 关注点、out-of-scope 守门条款、validation-handoff 口径。

### 4. Define Release Validation Path

- 负责人：CEOChiefOfStaff
- 协同：ChiefTechnologyOfficer
- 目标：明确本轮从 execution 到 review 的验证顺序，确保先跑聚焦验证，再扩大改动面。
- 产出：验证切片顺序、签核前最小证据要求、下一阶段进入条件。

## Sequence

1. 先冻结 workflow contract，再进入 execution 任务拆解。
2. 在 execution 开始前，先把验证切片和 evidence 路径写清楚。
3. 在 review 之前，由 CPO 明确流程优化线的边界与验收口径。
4. 只有当 execution evidence 满足最小验证要求时，才允许进入 sprint-review 签核。

## Validation Plan

- 验证切片一：runtime / CLI / tests / workflow docs 的改动顺序先固定，再开始实现。
- 验证切片二：每次 substantive 改动后先跑最小聚焦验证，不用 broad diff 代替可执行验证。
- 验证切片三：live support-root case 的阶段状态、签名链和 release metadata 必须和 source runtime 行为一致。
- 验证切片四：确认真实项目交付验证仍需独立 `project-delivery` case，不在本 sprint 内偷跑。

## Exit Criteria For Sprint Execution

- execution 目标、负责人与顺序已固定。
- 最小验证命令和 evidence 路径已固定。
- review 关注点与 validation-handoff 口径已固定。
- 当前 sprint 只承接流程优化线，不承接真实项目交付范围。
