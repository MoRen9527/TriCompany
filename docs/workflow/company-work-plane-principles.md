# 公司工作平面治理原则

版本：V1.0
日期：2026-08-12
状态：公司级治理文档（CEO 定调，CAO 归属待登记）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/company-work-plane-principles.md
- syncMode: source-only
- lastSyncedAt: 2026-08-12

## 1. 定位

本文是 TriCompany 公司工作平面的治理总纲，定义员工工作从接收到执行的三层结构及其层级关系。三条原则由 CEO 定调，是公司治理的一级条目。

## 2. 三层工作结构

```
周工作平面（依据）
  └→ 任务拆解（动态任务树）
        └→ 执行（ADE 原则）
```

| 层 | 定位 | 承载 | 治理文档 |
| --- | --- | --- | --- |
| 工作依据 | 员工工作的总纲——本周期做什么、优先级、owner | 周工作平面（Weekly Work Plane） | `runtime/cognition/weekly_plane.py`（运行时平面生成）；周平面 shift SOP 待文档化 |
| 任务承载 | 每个任务可以拆为动态任务树——节点链、交接、存档 | tree-op.json 节点链 | `docs/workflow/dynamic-task-tree-protocol.md` V0.6 |
| 执行原则 | 所有流程化、可重复的工作必须遵循 ADE | Agent plans → Deterministic CLI executes → Agent closes | `docs/engineering/ade-pattern-spec.md` v1.4 |

## 3. 原则一：工作依据——以周工作平面为总依据

员工每周期的工作以**周工作平面**（Weekly Work Plane）为总依据。周工作平面由公司编排层（CEOChiefOfStaff）生成和维护，定义：

- 本周期的经营事项、项目动作和跨项目交付目标
- 各项的优先级、owner 和预期交付物
- 与上一周期的 carry-over 和下一周期的衔接

周工作平面是**唯一的一级工作编排入口**。任何员工在任意时刻应以当前周工作平面为工作参考，不依赖临时、口头或会话内的非结构化指令。

关联：
- 周平面移位（weekly plane shift）：在周与周之间迁移在途工作项，确保无断层
- 周平面生成 runtime：`TriCompany/runtime/cognition/weekly_plane.py`

## 4. 原则二：任务承载——以动态任务树拆解任务

周工作平面中的每项任务可以**拆为动态任务树**（Dynamic Task Tree），以 tree-op.json 节点链承载：

- 根节点（CEOChiefOfStaff）建树、规划节点链和交接顺序
- 每个节点代表一个明确的执行角色和交付动作
- 节点间通过 routedInput（前节点 checkpoint 引用）和 brief（工作简报）显式交接
- Git commit 作为交接信号——节点完成 commit 触发下游开工
- 节点故障通过 checkpoint + brief 存档实现幂等续跑

多树并行时，根节点统一资源调度，树间无共享可变状态。

关联：`docs/workflow/dynamic-task-tree-protocol.md` V0.6

## 5. 原则三：流程化工作遵循 ADE

所有流程化、可重复的工作——构建、测试、发布、巡检、文档同步、审核——必须遵循 **ADE 原则**：

```text
Agent plans → Deterministic CLI executes → Agent closes
```

ADE 原则保证多次执行的可靠性：

- **幂等**：同一输入重复执行产生相同结果（Agent 不做非确定性操作，CLI 输出结构化自检报告）
- **可审计**：每次执行有 runId、状态变迁记录、产物的 commit SHA
- **可恢复**：中断后通过 ADE runtime 的 checkpoint 机制续跑，不需从头开始

ADE 不等于 DCE。DCE 只是 ADE 中的确定性执行阶段；Close Skill + Close CLI 形成语义裁决和终态写入，是 ADE 完整性的保证。

满足以下任意两项的工作即适用 ADE：涉及文件系统写操作、需要事后审计、可被自动化重复执行、涉及跨模块/跨仓库同步、操作失败需可回滚或可追溯、需跨会话恢复。

关联：`docs/engineering/ade-pattern-spec.md` v1.4

## 6. 层级关系与边界

三层之间的边界清晰：

| 边界 | 说明 |
| --- | --- |
| 周平面 ↔ 任务树 | 周平面列出"做什么"，任务树定义"怎么做"——周平面不规定执行细节，任务树不替代周平面做优先级决策 |
| 任务树 ↔ ADE | 任务树定义"谁做、交付什么"，ADE 定义"如何可靠执行"——Trees 不创建 ADE 内部 checkpoint，ADE 不创建组织节点 |
| 周平面 ↔ ADE | 周平面列出"哪些工作要走 ADE 流程"——不规定 ADE 内部参数 |

## 7. 治理

- 本文是 CEO 定调的一级治理条目。owner：CEOChiefOfStaff
- 文档归属由 CAO（Chief Administrative Officer）维护，真源路由由 CompanyGovernanceRegistry 收录
- 三条原则是周工作平面、动态任务树协议和 ADE 规范的总纲——三者各自独立演进，本文维护原则层一致性
- 变更需 CEO 审批

## 8. 关联文档

| 文档 | 关系 |
| --- | --- |
| `docs/workflow/dynamic-task-tree-protocol.md` V0.6 | 原则二的执行载体 |
| `docs/engineering/ade-pattern-spec.md` v1.4 | 原则三的执行载体 |
| `runtime/cognition/weekly_plane.py` | 原则一的运行时生成 |
| `runtime/cognition/weekly_plane_shift.py` | 周平面移位 runtime |
| `docs/workflow/published-copy-refresh-sop.md` | 发布流程（如本文需同步到项目侧） |
