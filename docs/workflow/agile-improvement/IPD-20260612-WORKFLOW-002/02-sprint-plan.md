# IPD-20260612-WORKFLOW-002 Sprint Plan

## Sprint Goal

- 把本轮全阶段 IPD 优化从“已签核的 backlog”推进到“Gate A replay contract、自测矩阵、回退矩阵和 proving-ground 回放顺序已固定”的可执行状态。
- 明确 `IPD-20260611-PLATFORM-001` 已完成全链路 proving-ground replay，后续作为证据基线；Gate A / Gate B / Gate C 的继续验证与产品主线消费对齐 `IPD-20260610-PLATFORM-001`，不让本轮又退回只谈 `Discovery / Intelligence`。

## Timebox And Resource Window

- 当前节奏：沿用 intake 约束，以本轮 sprint 先固化 Gate A 所需的 planning contract，并为后续 Gate B / Gate C 衔接留出口。
- 资源窗口：仅使用现有人力与少量工具试验成本，不引入正式宿主切换、生产部署或平台新建设任务。
- 参与角色：CEOChiefOfStaff 主持计划与收口；ChiefProductOfficer 负责 capability gate 与验收边界；ChiefTechnologyOfficer 负责自测矩阵、runtime/CLI 验证切片、Discovery competitor carry-forward 严谨性补丁与 replay 前检查。

## Ordered Task Breakdown

### 1. Freeze Gate A Replay Contract

- 负责人：CEOChiefOfStaff
- 协同：ChiefProductOfficer
- 目标：把 `ceo-demand -> task-dispatch -> discovery -> intelligence -> package/signoff` 的 replay 顺序、进入条件和暂停条件固定下来。
- 产出：Gate A 顺序合同、进入 proving-ground replay 的前置条件。

### 2. Define Source-Side Self-Test Matrix

- 负责人：ChiefTechnologyOfficer
- 协同：CEOChiefOfStaff
- 目标：把每轮改动在 replay 前必须经过的 source-side 验证收成固定矩阵。
- 产出：runtime / CLI / focused regression / stage-output 对齐检查矩阵。

### 3. Harden Discovery Competitor Carry-Forward Rule

- 负责人：ChiefTechnologyOfficer
- 协同：CEOChiefOfStaff、ChiefProductOfficer
- 目标：把 Discovery 自动化改成“CEO 填槽竞品不是唯一上限，但每个 seeded competitor 都必须被后续引用覆盖，除非显式 waiver”。
- 产出：Discovery catalog / brief / landscape 的覆盖校验规则、阻断或 revision-required 条件，以及 CTO 负责的流程代码修改入口。

### 4. Lock Rollback Matrix And Replay Gate

- 负责人：CEOChiefOfStaff
- 协同：ChiefTechnologyOfficer
- 目标：明确何时回 `ceo-demand`、何时回 `task-dispatch`、何时回 `discovery`，以及什么情况下允许局部重跑更后阶段。
- 产出：主回退锚点规则、live replay 失败后的分流标准。

### 5. Write Gate B And Gate C Capability Map

- 负责人：ChiefProductOfficer
- 协同：ChiefTechnologyOfficer、CEOChiefOfStaff
- 目标：把 `designing -> coding -> verify-integration` 与 `redteam -> qa -> deployment -> assurance -> delivery` 的逐段放行条件写成下一轮可接单的 map。
- 产出：Gate B / Gate C 能力门框架、后续阶段验收关注点。

### 6. Define Release Validation Path

- 负责人：CEOChiefOfStaff
- 协同：ChiefTechnologyOfficer、ChiefProductOfficer
- 目标：固定“流程优化 sprint -> source-side 自测 -> IPD-20260610-PLATFORM-001 live replay / 产品主线消费 -> 继续/冻结/回退”的验证顺序。
- 产出：本轮 exit criteria、下一阶段 execution 的验证路径和 evidence 约束。

## Sequence

1. 先冻结 Gate A replay contract，再定义 source-side 自测矩阵。
2. 在 execution 开始前，必须先把 Discovery competitor carry-forward 规则写成 CTO 负责实现的严谨性补丁。
3. 然后写清 rollback matrix 与 proving-ground replay gate。
4. 在 review 之前，必须先补出 Gate B / Gate C 的 capability map，防止本轮语言再次退化成 D/I-only。
5. 只有当 source-side self-test、competitor carry-forward guard 和 replay gate 都满足时，才允许下一阶段进入 sprint-execution。

## Validation Plan

- 验证切片一：source-side 自测矩阵先固定，至少覆盖 runtime、CLI、focused regression 和 stage-output 签名链行为。
- 验证切片一补充：Discovery 若扩展更多竞品可以通过，但 CEO 填槽的 seeded competitors 不能从 catalog / brief / landscape 里静默消失。
- 验证切片二：`IPD-20260610-PLATFORM-001` 必须保留当前 Discovery baseline / replay surface，直到本轮 execution 明确进入受控 replay。
- 验证切片三：任何 replay 失败都必须先套用 rollback matrix，再回流到 workflow sprint，不允许直接口头跳过。
- 验证切片四：Gate B / Gate C 的 map 必须在 planning 阶段就留下明确入口，避免“当前只先做 D/I”被误写成总目标。

## Exit Criteria For Sprint Execution

- Gate A replay contract 已固定。
- source-side 自测矩阵已固定。
- Discovery competitor carry-forward guard 已固定，且流程代码修改责任明确归 CTO。
- rollback matrix 与 replay gate 已固定。
- Gate B / Gate C capability map 已形成第一版。
- execution 阶段可以直接按计划推进，而不需要重新解释为什么要做 proving-ground replay。
