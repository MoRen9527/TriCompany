# IPD Case 详解
---
在ipd_case_engine.py 里的 _ensure_case_defaults 有case字段的清洗，
这个清洗可以理解成两层作用：

第一层，它在“补结构”。也就是把一个可能来源不一、字段不齐的 case payload，补成 IPD 引擎能稳定消费的标准对象。

第二层，它在“定语义”。也就是把这些字段统一归到 IPD 流程里的几个固定位置：立项入口、阶段执行、审批签发、冻结控制、当前推进指针。这样后面的自动化、提交、签核、暂停、恢复，才能都围绕同一套字段工作。

先讲“IPD Case 里的这些字段分别是什么意思、在 IPD 里起什么作用”。

# 1. case 顶层字段
**整个 IPD case 的外壳**

在函数开头清洗的 caseId、title、status、currentStageKey，属于 case 顶层元信息。

它们在 IPD 里的作用是：
## 1.1 caseId
这条 IPD 事项的唯一标识。后续读写 case.json、事件流、阶段文档都靠它串起来。
## 1.2 title
这条事项的人类可读标题。主要用于 briefing、列表展示、审批界面和输出文档标题。
## 1.3 status   
`case_payload["status"]`
这条 case 当前处于什么总状态，比如等待 intake 审批、推进中、冻结中之类。它是整个流程引擎判断"现在还能不能继续跑"的总开关之一。

### 1.3.1 Case 级别状态 
`case_payload["status"]`

代表**整个 Case/IPD 流程**的宏观状态，反映当前 Case 在生命周期中的整体进展。

| 状态值 | 含义 |
|--------|------|
| `awaiting-intake-approvals` | 等待 intake（初始录入）审批 |
| `awaiting-stage-approvals` | 等待当前 stage 的审批 |
| `waiting-stage-output` | 等待当前 stage 的执行输出 |
| `paused-frozen` | Case 被冻结（暂停） |
| `paused-intake-clarification` | Intake 需要澄清信息 |
| `blocked` | 被阻塞（审批被拒绝等） |
| `completed` | Case 全部完成 |

---

### 1.3.2 Stage 级别状态 
`stage["status"]`

代表**单个 Stage（阶段）**的微观状态，一个 Case 包含多个 stages。

| 状态值 | 含义 |
|--------|------|
| `pending` | 等待开始（默认状态） |
| `in-progress` | 正在进行中 |
| `submitted` | 已提交，等待审批 |
| `completed` | 该 stage 已完成 |
| `rejected` | 该 stage 被审批拒绝 |
| `frozen` | 该 stage 被冻结 |

---

### 1.3.3 两者的关系

**Case 状态是由 Stage 状态推导出来的**，核心逻辑在 `_recalculate_status` 附近（约 [L2444-L2497](/TriCompany/runtime/cognition/ipd_case_engine.py#L2444-L2497)）：

```
Case 状态推导规则：
├─ intake 未批准 → awaiting-intake-approvals / paused-intake-clarification
├─ intake 已批准 → 看当前 stage 状态
│   ├─ stage = submitted → awaiting-stage-approvals
│   ├─ stage = in-progress → waiting-stage-output
│   ├─ stage = rejected → blocked
│   ├─ stage = frozen → paused-frozen
│   └─ stage = completed → 看是否还有后续 stage
│       ├─ 有后续 stage → waiting-stage-output（进入下一个 stage）
│       └─ 无后续 stage → completed
```

**简单说：**
- **Stage 状态** = 某个具体阶段的执行状态
- **Case 状态** = 基于当前 stage 状态计算出的整体流程状态

例如：当 stage 被提交审批时，`stage["status"] = "submitted"`，同时 Case 状态变为 `case_payload["status"] = "awaiting-stage-approvals"`，告诉外部"当前正在等待 stage 审批"。


## 1.4 currentStageKey
当前推进到哪个 stage。它决定自动化入口、审批入口、handoff 入口应该落到哪个阶段。

根据代码分析，这三个"入口"是 IPD Case 流程中不同环节的**执行切入点**，由 `_entry_checkpoint_for_case` 函数（[L3873-L3901](TriCompany/runtime/cognition/ipd_case_engine.py#L3873-L3901)）动态决定。它们的作用和区别如下：

---

### 三个入口的定义与区别

| 入口 | 英文标识 | 作用 | 触发时机 |
|------|----------|------|----------|
| **自动化入口** | `task-dispatch` | 自动派发任务给 AI Agent / Worker 执行 | Case 刚启动、进入第一个 stage 时 |
| **审批入口** | `ceo-demand` | 需要 CEO/总助人工审批或澄清 | intake 未批准、需要补充信息时 |
| **Handoff 入口** | stageKey（如 `discovery`, `designing` 等） | 阶段交接，从一个 stage 流转到下一个 stage | 当前 stage 完成，需要进入下一个 stage |

---

### 详细说明

#### 1. 自动化入口 (`task-dispatch`)

```python
# L3887 和 L3900
return "task-dispatch"
```

- **作用**：自动将任务分发给对应的 AI Agent 执行
- **触发条件**：
  - 当前是第一个 stage（如 `discovery`）且刚被激活、尚未提交产出
  - 或者所有 pending stage 中的第一个需要被激活
- **特点**：无需人工干预，系统自动推进

---

#### 2. 审批入口 (`ceo-demand`)

```python
# L3890-L3893
if status in {"awaiting-intake-approvals", "paused-intake-clarification"}:
    return "ceo-demand"
if intake_status != "approved":
    return "ceo-demand"
```

- **作用**：将流程挂起，等待 CEO/总助的人工审批或信息澄清
- **触发条件**：
  - Case 状态为 `awaiting-intake-approvals`（等待 intake 审批）
  - Case 状态为 `paused-intake-clarification`（需要澄清）
  - Intake 尚未被批准
- **特点**：人工决策点，阻断自动执行

---

#### 3. Handoff 入口 (`stage_key`，如 `discovery`, `designing`, `coding`...）

```python
# L3888
return stage_key
```

- **作用**：表示当前正在某个具体 stage 中执行，或从一个 stage 交接给下一个 stage
- **触发条件**：
  - 当前存在正在执行的 stage（`current_stage` 不为 None）
  - 且不满足 `task-dispatch` 的特殊条件
- **特点**：代表**阶段间的工作交接**，每个 stage 完成后会检查 `handoffChecklist`（交接清单）确保产出完整才能进入下一阶段

---

### 三者的流转关系

```
开始
  │
  ▼
┌─────────────────┐
│  intake 已批准？ │──否──► 审批入口 (ceo-demand)
└─────────────────┘
  │是
  ▼
┌─────────────────────────────┐
│ 是第一个 stage 且刚激活？      │──是──► 自动化入口 (task-dispatch)
└─────────────────────────────┘
  │否
  ▼
┌─────────────────────────────┐
│ 当前有正在执行的 stage？       │──是──► Handoff 入口 (stage_key)
└─────────────────────────────┘
  │否
  ▼
┌─────────────────────────────┐
│ 还有未完成的 pending stage？   │──是──► 自动化入口/下一 stage
└─────────────────────────────┘
  │否
  ▼
完成 (completed)
```

---

### 总结

| 维度 | 自动化入口 | 审批入口 | Handoff 入口 |
|------|-----------|----------|--------------|
| **驱动方** | AI/系统自动 | CEO/人工 | Stage 间自动流转 |
| **目的** | 自动派发任务 | 人工决策/澄清 | 阶段交接与产出检查 |
| **阻断性** | 非阻断 | 阻断（等待人工） | 非阻断（需 checklist 通过） |
| **典型场景** | Case 启动、进入新 stage | 需求不明确、需要审批 | 设计完成→开发、开发完成→测试 |
        


case顶层这组字段的本质是：定义“这是什么 case，现在走到哪了”。

# 2. intake 字段
**立项入口的业务上下文**

intake 是整条 IPD 的入口包，相当于“为什么要做这件事、想做什么、边界是什么、缺什么信息”。

这里需要被清洗的字段大致分几类。

## 2.1 需求背景与价值判断
objective
taskDescription
expectedDelivery
expectedOutcomes
opportunitySignals
businessModelFit
stageFit  
companyContext
constraints

根据代码分析，这 9 个字段都是 **Intake（需求录入）阶段**的核心字段，用于描述一个 IPD Case 的"为什么做、做什么、怎么做、做到什么程度"。它们的作用如下：

---

### 2.1.1 需求背景与价值判断字段说明

| 字段 | 代码位置 | 作用 |
|------|----------|------|
| **objective** | [L1549](TriCompany/runtime/cognition/ipd_case_engine.py#L1549) | **目标**：做这个 Case 要达成什么目的，一句话概括核心诉求 |
| **taskDescription** | [L1550](TriCompany/runtime/cognition/ipd_case_engine.py#L1550) | **任务描述**：具体要做什么工作，详细描述任务内容 |
| **expectedDelivery** | [L1567](TriCompany/runtime/cognition/ipd_case_engine.py#L1567) | **预期交付物**：最终要产出什么（文档、代码、产品等）|
| **expectedOutcomes** | [L1560](TriCompany/runtime/cognition/ipd_case_engine.py#L1560) | **预期成果**：交付后预期产生什么效果/价值 |
| **opportunitySignals** | [L1552](TriCompany/runtime/cognition/ipd_case_engine.py#L1552) | **机会信号**：市场/技术/业务上的机会点，说明为什么现在做 |
| **businessModelFit** | [L1553](TriCompany/runtime/cognition/ipd_case_engine.py#L1553) | **商业模式匹配度**：与公司商业模式的契合程度 |
| **stageFit** | [L1554](TriCompany/runtime/cognition/ipd_case_engine.py#L1554) | **阶段适配备注**：记录当前 Case 与既定推进方式的适配说明。当前实现里它只是 intake 下的字符串列表字段，不直接决定走哪套 stage 体系；真正决定流程的是 `caseCategory`。 |
| **companyContext** | [L1555](TriCompany/runtime/cognition/ipd_case_engine.py#L1555) | **公司上下文**：公司当前战略、资源、优先级等背景信息 |
| **constraints** | [L1551](TriCompany/runtime/cognition/ipd_case_engine.py#L1551) | **约束条件**：限制条件（预算、时间、技术栈等）|

#### `stageFit` 的当前真实含义

`stageFit` 在当前实现里表示：**对当前 Case 推进方式的补充说明**。

它的代码行为非常简单：

- 在 intake 时被写入 `intake.stageFit`
- 数据类型是**字符串列表**
- 当前引擎**不会**根据它的值来切换流程、跳过 stage 或决定执行顺序

也就是说，`stageFit` 目前更接近一个**备注型字段**，而不是流程控制字段。

---

#### 真正决定 stage 体系的是 `caseCategory`

当前代码中，Case 进入哪套 stage 模板，不是由 `stageFit` 决定，而是由 `caseCategory` 决定：

| `caseCategory` | 对应流程 | stage 体系 |
|------|------|------|
| `project-delivery` | 项目交付 | 标准 IPD stages |
| `process-improvement` | 流程改进 | agile-improvement stages |

也就是说：

- `project-delivery` 会进入标准 IPD 阶段链
- `process-improvement` 会进入 `backlog -> sprint-planning -> sprint-execution -> sprint-review -> retrospective -> validation-handoff`

`stageFit` 只能补充说明“为什么这样推进”“当前适配性如何”“边界是什么”，但**不是决定器**。

---

#### 两类 Case 中，`stageFit` 可以怎么写

##### 1. PLATFORM Case（`project-delivery`）

| 字段 | 值 | 含义 |
|------|-----|------|
| `caseCategory` | `project-delivery` | 走标准 IPD 流程 |
| `referenceTheme` | `PLATFORM` | 平台类产品交付 |
| `stageFit` | `[]` 或文字说明 | 用自然语言补充交付边界、切入点或阶段适配判断 |

这类 Case 里，`stageFit` 可以为空，也可以写成类似下面的说明：

- `当前事项适合走完整 IPD 交付链，暂不裁剪中间阶段。`
- `本轮重点先验证 discovery 到 designing 的串联，后续阶段按 gate 结果推进。`

这些是**说明文字**，不是引擎会识别的枚举值。

---

##### 2. WORKFLOW Case（`process-improvement`）

| 字段 | 值 | 含义 |
|------|-----|------|
| `caseCategory` | `process-improvement` | 走敏捷改进流程 |
| `referenceTheme` | `WORKFLOW` | 改进工作流/IPD 引擎 |
| `stageFit` | `[]` 或文字说明 | 用自然语言补充当前流程改进的推进边界与验证方式 |

这类 Case 里，`stageFit` 通常更像是流程说明，例如：

- `当前事项属于流程优化线，应先用 agile-improvement 跑 backlog -> validation-handoff，再另开真实 project-delivery case 验证。`

同样，这里也是**文字备注**，不是代码里定义好的控制信号。

---

#### 实际项目中的情况

当前样例里：

| Case ID | caseCategory | stageFit | 说明 |
|---------|-------------|----------|------|
| `IPD-20260610-PLATFORM-001` | `project-delivery` | `[]` | 当前未填写补充说明 |
| `IPD-20260611-PLATFORM-001` | `project-delivery` | `[]` | 当前未填写补充说明 |
| `IPD-20260611-WORKFLOW-001` | `process-improvement` | 非空文字说明 | 已明确写出应先走 agile-improvement，再另开真实 project-delivery case |
| `IPD-20260612-WORKFLOW-002` | `process-improvement` | `[]` | 当前未填写补充说明 |

所以，不能把 `stageFit` 简单理解为“某个固定阶段枚举”：

- 它**可能为空**
- 也**可能是自然语言说明**
- 但当前实现里**不会直接驱动流程**

---

#### 总结

> `caseCategory` 决定 Case 走哪套 stage 体系；`stageFit` 只是对该推进方式的补充说明。

`stageFit` 当前不是固定枚举，也不是流程选择器，而是 intake 中一个尚未被引擎消费的说明性列表字段。
        

---

### 2.1.2 分组理解

这 9 个字段可以分成三组：

#### 第一组：What — 做什么
- **objective** → 目标（Why）
- **taskDescription** → 任务内容（What）
- **expectedDelivery** → 交付物（What to deliver）

#### 第二组：Value — 为什么值得做
- **opportunitySignals** → 机会在哪里（Market/tech opportunity）
- **businessModelFit** → 是否符合商业模式（Business fit）
- **expectedOutcomes** → 预期收益（Expected ROI）

#### 第三组：Context — 在什么条件下做
- **companyContext** → 公司当前状况（Company situation）
- **stageFit** → 阶段是否合适（Stage timing）
- **constraints** → 限制条件（Limitations）

---

### 2.1.3 在流程中的使用

这些字段在 Case 生命周期中被多次使用：

1. **Intake 审批时** → 供审批者判断是否值得做
2. **生成 Stage 上下文时**（[L2568-L2582](TriCompany/runtime/cognition/ipd_case_engine.py#L2568-L2582)）→ 传递给各阶段执行者
3. **生成 CEO 简报时**（[L4917-L4968](TriCompany/runtime/cognition/ipd_case_engine.py#L4917-L4968)）→ 汇总展示 Case 全貌
4. **Discovery/Intelligence 阶段** → 作为分析输入（[L2881-L2920](TriCompany/runtime/cognition/ipd_case_engine.py#L2881-L2920)）

---

### 2.1.4 总结

> 这 9 个字段构成了 IPD Case 的**需求说明书**，回答了一个项目的核心五问：**为什么做、做什么、交付什么、有什么价值、在什么约束下做**。它们在 intake 阶段被录入，在后续所有阶段被引用，确保各方对需求理解一致。

它们在 IPD 里的作用是：帮助 intake 阶段和 discovery 阶段先判断这件事值不值得进入公司交付线、和当前商业路径是否匹配、预期交付是什么。

## 2.2 约束与资源边界
### 2.2.1 constraints
### 2.2.2 resourceEnvelope 
### 2.2.3 prerequisites
### 2.2.4 requiredSupport

它们的作用是：让后面的 discovery、intelligence、designing 不会脱离现实地乱跑。比如预算、人力、前置依赖、需要谁协同，这些都会直接影响后续是否 freeze、是否继续、是否缩 scope。

## 2.3 owner 初始设想
### 2.3.1 ownerProposal

它的作用是记录“提出方当前认为应该怎么做”。在 IPD 里这不是最终方案，但它是 discovery/intelligence 的初始输入之一，也能帮助后续判断是否发生了方案偏移。

## 2.4 预期结果
### 2.4.1 expectedOutcomes

它的作用是给后续阶段一个“验收方向”的粗锚点。后面 delivery、validation-handoff、review 时都会回看这些预期结果是不是被满足。

# 3. slotAnswers / clarificationSheet
**把模糊需求变成可推进需求**
这组字段非常关键。

1. slotAnswers：对 intake 关键槽位问题的回答。
2. clarificationRequired：当前是否要求补澄清。
3. clarificationSheet：基于 taskDescription 和 slotAnswers 生成的澄清单。

它们在 IPD 里的作用是：把 CEO 或需求提出方的自然语言需求，拆成可以审、可以补、可以推进的结构化信息。

简单说，IPD 不怕需求还不完整，怕的是“不知道缺哪块”。slotAnswers 和 clarificationSheet 就是在解决这个问题。后续 intake signoff、自动暂停、owner action package，都很依赖这组字段。

# 4. caseCategory / referenceTheme：给 case 定类型，决定后面怎么研究**
这两个字段不是普通文本，它们更像“路由字段”。

1. caseCategory：这条 case 属于什么类型，比如更偏产品交付、流程优化、研究类事项之类。
2. referenceTheme：这条 case 在 discovery/intelligence 阶段应该参考哪类对标主题。

它们在 IPD 里的作用是：
1. 决定标准 flow 模板怎么套。
2. 决定 discovery/intelligence 自动种子从哪一类资料开始构造。
3. 决定哪些角色更应该参与，哪些 deliverable 更重要。

所以这两个字段其实是在给后面的研究和执行路线“定导航”。

# 5. approvals / roleAssignmentMatrix：谁有权批，谁应该干**
intake 下有两组非常流程化的字段：

1. approvals
2. roleAssignmentMatrix

它们在 IPD 里的作用分别是：
1. approvals：记录当前 intake 需要谁批准、谁已批准、谁待批准。后面的 next pending approval、manual pause、signoff 都靠它。
2. roleAssignmentMatrix：定义这个阶段有哪些角色、角色职责和交付物。它是“组织分工视图”。

也就是说，这组字段不是描述需求内容，而是在描述“这件事要怎么在人和岗之间流动”。

# 6. release / package 相关字段：给 intake 和 stage 做签发与版本管理**
在 intake 和每个 stage 里，都有一组类似字段：

1. packageHash
2. releaseCounter
3. releaseVersion
4. releaseStatus
5. releaseIssuedAt
6. releaseIssuedByRole

它们在 IPD 里的作用是：把阶段产物从“临时内容”提升为“有版本、有签发状态的交付包”。

大致场景是：
1. 生成 briefing 或阶段文档后，要知道是不是正式版。
2. 多次提交、多次修订时，要能区分第几轮。
3. 签发后要能追踪是谁在什么时候签的。

这组字段的本质不是业务研究，而是“交付治理”。

# 7. stage 字段：每个 IPD 阶段自己的执行上下文**
函数里会遍历 case_payload["stages"]，给每个 stage 清洗一批字段。它们描述的是“这个阶段谁负责、谁审批、阶段输入是什么、属于哪一相位”。

比较关键的有：

1. businessOwner
2. actingOwner
3. moduleExecutor
4. gateOwner
5. ownerRole
6. requiredApprovers
7. approvals
8. phaseKey
9. participantRoles
10. inputRequirements
11. superDevReferenceStages

它们在 IPD 里的作用可以这样看：

1. owner 相关字段
定义业务负责人、实际推进人、模块执行方、gate 把关人。用于阶段责任划分、handoff、升级和 freeze 判断。

2. approver 相关字段
定义这个阶段谁必须签。用于 submit_stage_output 和 record_stage_signoff 这类操作。

3. phaseKey
把 stage 挂到更高一层 phase 里。便于汇总状态、流程视图、自动化分组。

4. participantRoles
定义除了 owner 之外还有哪些角色应参与。用于协作提示和输出包编排。

5. inputRequirements
定义这个阶段依赖什么输入。用于判断阶段是否 ready，也用于后续审查阶段缺口。

6. superDevReferenceStages
把本地 IPD 阶段和 super-dev 参考流程做映射。用于对齐参考链和执行证据。

这组字段本质上是在定义“阶段级工作合同”。

# 8. freezeControl：流程暂停/冻结机制**
顶层还有 freezeControl。

它在 IPD 里的作用是：当某个角色认为当前事项不能继续推进时，记录冻结状态、冻结人、冻结域、原因、对应阶段。后面 _case_is_frozen、_assert_case_not_frozen、pause summary 都会依赖它。

简单说，它是整个 IPD 流程的“刹车系统”。

# 9. currentWorkItemPath / entryCheckpoint：当前工作落点和恢复锚点**
最后还有两个偏运行态字段：

1. currentWorkItemPath
2. entryCheckpoint

它们的作用是：
1. currentWorkItemPath：告诉系统当前主要工作产物落在哪里，方便宿主或自动化继续接手。
2. entryCheckpoint：表示如果现在恢复推进，应该从哪个入口继续。

这两个字段更偏“流程引擎执行态”，不是业务含义本身，但对自动恢复、宿主接管、暂停后续跑很重要。

# 10 总结

一句话归纳这些字段在 IPD 里的分层：
可以把它们分成五层看：

1. case 身份层：caseId、title、status、currentStageKey
2. intake 业务层：objective、constraints、opportunitySignals、expectedDelivery 等
3. 澄清与分诊层：slotAnswers、clarificationSheet、caseCategory、referenceTheme
4. 阶段治理层：stage owner、approvals、phaseKey、inputRequirements
5. 运行控制层：freezeControl、release 字段、currentWorkItemPath、entryCheckpoint

所以 _ensure_case_defaults 不是随便清洗一堆字段，它其实是在把一个 case 校准成“既能表达业务意图，又能被流程引擎执行”的标准 IPD 对象。

如果你要，我下一步可以按你说的节奏，开始“逐组看清洗手法 + 后续使用场景”。我建议先从这三个块开始，最容易看懂：

1. intake 业务字段怎么清洗
2. clarification / slot 相关字段怎么清洗
3. stage owner / approvals 字段怎么清洗







        
