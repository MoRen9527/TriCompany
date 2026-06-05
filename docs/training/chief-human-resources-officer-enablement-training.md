# 赛博公司模块的新员工入职与启用流程

版本：V0.3
日期：2026-05-21
状态：内部技术培训草案；面向需要接手赛博公司模块员工启用链路的产品和研发新员工，以 ChiefHumanResourcesOfficer 作为贯穿案例；不构成 CHO live 发布声明

## 1. 这堂课应该怎么读

请先把自己代入一名刚加入产品或研发条线、需要接手 TriCompany 赛博公司模块的新员工。

这不是面向所有公司员工的通识课，也不是完整的产品和研发新员工全局 onboarding / enablement 技术培训。它是其中一个模块级专题：赛博公司模块里的员工对象，如何从源侧定义走到当前宿主启用判断。你不需要一开始就懂 agent、binding profile、support object 或 live binding。你只需要先理解一件事：在 TriCompany 里，启用一个产品或研发相关的新员工，不是一句“这个岗位上岗了”，也不是只创建一个文件，而是一条从公司需求到宿主运行的入职流水线。

这条流水线要回答几个朴素问题：

- 公司为什么需要这个新员工。
- 这个员工的职责、边界和协作关系写在哪里。
- 这个员工需要哪些源侧资料。
- 当前宿主要怎样读取这个员工。
- 哪些检查通过以后，才能说它已经准备好进入当前宿主。
- 什么情况下只能说“已定义”或“已发布 support object”，不能说“已 live”。

本文不会按某几个疑问逐条答复，而是带你沿着一名赛博公司新员工的启用旅程，从“提出岗位需求”一路看到“真正 live 上岗”。`ChiefHumanResourcesOfficer` 是本文的案例，因为 CHO 正好处在一个适合讲清 source、support、live 边界的阶段。

## 2. 赛博公司里的“入职与启用”到底是什么意思

这里说的入职与启用，不是现实世界里签劳动合同、发工资、办社保。

赛博公司里的入职与启用，是把一个稳定职责变成可运行、可迁移、可审计的员工资产。它包含三层意思：

1. 组织层确认：公司确实需要这个岗位或员工。
2. 资料层成型：这个员工的职责、人格、记忆边界、协作边界和宿主绑定资料都被写清楚。
3. 运行层接入：当前宿主真正可以读取、验证并在需要时启用这个员工。

所以，一个赛博公司员工不是单个 agent 文件。它更像一套入职档案、岗位手册、知识工作台、门禁记录和运行入口的组合。

## 3. 新员工启用旅程总览

一名新员工通常会经历下面这些阶段。

| 阶段 | 员工要理解什么 | 关键资料 | 门禁或完成标志 |
| --- | --- | --- | --- |
| 1. 提出岗位需求 | 公司为什么需要这个人 | 会议结论、operating record、岗位需求描述 | 职责足够稳定，不适合继续临时代管 |
| 2. 定义岗位职责 | 这个岗位做什么、不做什么 | `docs/workflow/<role>-role.md` | 职责、边界、协作对象和状态写清楚 |
| 3. 建源侧五件套 | 这个员工如何说话、思考、记忆和协作 | `.github/source-agents/<employee-id>/<employee-id>.*.md` | agent、soul、memory、colleagues、social 齐备，且源码侧不会被误识别为 live agent |
| 4. 检查认知边界 | 哪些内容能写进源侧，哪些只能运行时产生 | 五件套、认知层验证规则 | 没有把运行记忆、人物流水或 live 路径写进源侧 |
| 5. 准备知识工作区 | 岗位知识和员工实例记忆如何分开 | role / employee / org / audit workspace 规则 | role 知识、employee 私域、org shared 和 audit 边界清楚 |
| 6. 建绑定档案 | 当前宿主准备如何识别这个员工 | `.github/binding-profiles/<employee-id>.json` | hostStage、liveEntry、supportObjects、runtimeNamespaces 写清楚 |
| 7. 写对象生成声明 | 当前宿主对象要从哪些源侧资料生成 | `.github/manifests/tricompany-host-object-generation-manifest.json` | source refs、generator、validation command、support target 齐备 |
| 8. 发布 support object | 当前宿主是否已有可消费对象 | `TriCompany-copilot-host-assets/knowledge/**` 与 `host-object-manifest.json` | support root 里真实出现对象并登记 manifest |
| 9. 过验证门禁 | support、binding、source 和 owner 切换是否一致 | validation 输出、handoff record、operating record | 不再有 source/support/live 口径冲突 |
| 10. 判断 live binding | 是否真的把员工接入当前宿主运行 | live agent 入口、binding profile、治理回填 | 明确当前宿主已绑定该员工，且 owner 切换完成 |
| 11. 运行后沉淀 | 上岗后的工作连续性写到哪里 | `.tricompany-cognition/**` runtime state | 运行态记录开始出现，但不反写源侧人格文件 |

你可以把这张表当作“新员工入职路线图”。每次看到一个新岗位、新 agent 或新员工名，都先问它走到了哪一站，不要直接判断它已经上岗。

## 4. 新员工会遇到的三类资料

新员工资料很多，但初学者先分成三类就够了。

### 4.1 源侧定义资料

源侧定义资料回答：这个员工在公司制度里是谁。

常见资料包括：

- 岗位说明书：`TriCompany/docs/workflow/<role>-role.md`
- 源侧五件套：`TriCompany/.github/source-agents/<employee-id>/<employee-id>.(agent|soul|memory|colleagues|social).md`
- 认知层规则：memory、colleagues、social 的写入边界
- 绑定档案：`TriCompany/.github/binding-profiles/<employee-id>.json`
- 对象生成声明：`TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json`

源侧定义资料像员工档案和岗位手册。它可以证明“这个员工已经被定义”，但不能单独证明“当前宿主已经启用”。

### 4.2 当前宿主支撑资料

当前宿主支撑资料回答：当前 Copilot-host 是否已经有东西可以读。

常见资料包括：

- `TriMetaverse/TriCompany-copilot-host-assets/knowledge/roles/**`
- `TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/**`
- `TriMetaverse/TriCompany-copilot-host-assets/knowledge/org/shared/**`
- `TriMetaverse/TriCompany-copilot-host-assets/knowledge/audit/**`
- `TriMetaverse/TriCompany-copilot-host-assets/host-object-manifest.json`

support object 像给员工准备好的当前宿主工作台。工作台存在，说明宿主有可消费对象；但它仍然不等于员工已经 live 上岗。

### 4.3 live 与运行资料

live 与运行资料回答：当前宿主是否真的让这个员工工作，以及工作后的连续性写到哪里。

常见资料包括：

- `TriMetaverse/.github/agents/**` 当前 live 入口
- binding profile 中的 `liveEntry`
- operating record 或 handoff record
- `.tricompany-cognition/**` runtime state

live 入口是上岗入口。runtime state 是上岗后的工作记忆。源侧人格文件不应该被运行时记忆污染。

## 5. 新员工会经过的几道门禁

门禁不是为了让流程变复杂，而是为了防止赛博公司把“想法”“草案”“已发布对象”和“已上岗”混成一件事。

### 5.1 岗位必要性门禁

这道门禁确认：公司是否真的需要这个固定员工。

要看：

- 是否出现稳定、重复、可归属的职责。
- 是否已有岗位长期临时代管这项职责。
- 是否需要独立 owner 做制度、执行或审计。

没过这道门禁时，应该继续作为临时任务处理，不要创建固定员工。

### 5.2 源侧完整性门禁

这道门禁确认：员工的源侧定义是否足够完整。

要看：

- 岗位说明书是否存在。
- 五件套是否存在。
- 职责和不负责事项是否写清楚。
- 当前状态是否写成真实阶段。
- 是否避免把未完成事项写成已完成。

没过这道门禁时，只能说“岗位意向存在”或“草案中”。

### 5.3 认知层边界门禁

这道门禁确认：源侧人格和认知层契约没有被运行数据污染。

要看：

- `.memory.md` 是否只定义记忆契约，而不是写具体任务流水。
- `.colleagues.md` 是否只定义协作档案边界，而不是写实际人物流水。
- `.social.md` 是否只定义社交层边界，而不是写正式工作事实。
- 五件套是否没有硬编码当前 live 路径或 support employee 私域路径。

没过这道门禁时，员工定义就不适合迁移到未来宿主。

### 5.4 support 发布门禁

这道门禁确认：当前宿主是否已经真的拿到可消费对象。

要看：

- support root 里是否出现 role workspace。
- support root 里是否出现 employee workspace。
- `host-object-manifest.json` 是否登记该员工 object set。
- source manifest declaration 和实际 support manifest 是否一致。

没过这道门禁时，只能说“源侧已定义”或“生成声明已登记”，不能说 support object 已发布。

### 5.5 live 前验证门禁

这道门禁确认：如果要把员工接进当前宿主，source、support、owner 和记录是否一致。

要看：

- binding profile 的 `hostStage` 是否准确。
- `liveEntry` 是否仍是 `not-published`，还是已经进入可绑定状态。
- owner 切换是否有 handoff 记录。
- 是否需要替代式 shadow test。
- 不需要替代式 shadow 时，是否仍有 live readiness validation。

没过这道门禁时，不应宣布 live binding。

### 5.6 治理回填门禁

这道门禁确认：真正上岗后，公司的经营记录和资料层没有口径冲突。

要看：

- operating record 是否更新。
- registry 是否需要更新。
- training 或 workflow 文档是否需要说明状态变化。
- active owner 是否已经从代管者切给新员工。

没过这道门禁时，即使代码层看起来可用，组织层也还没有闭环。

## 6. 跟着一名新员工走完整流程

下面用一名新员工的视角走一遍。你可以把每一步理解成入职流程里的一个站点。

### 6.1 第一站：公司提出岗位需求

流程从“公司需要一个稳定职责 owner”开始。

例如 CHO 的需求来自交接治理：赛博公司开始需要岗位启用流程、职责交接流程、handoff checklist、completion tracking 和组织边界治理。这些工作不能长期由 CEOChiefOfStaff 临时代管，所以公司需要 CHO。

这一站的关键不是写文件，而是确认岗位必要性。

### 6.2 第二站：写岗位说明书

岗位说明书告诉相关协作者和读者：这个岗位为什么存在，负责什么，不负责什么，当前处于什么阶段。

通常位置是：

- `TriCompany/docs/workflow/<role>-role.md`

CHO 的岗位说明书是：

- `TriCompany/docs/workflow/chief-human-resources-officer-role.md`

对新员工来说，这是认识一个岗位的第一份正式资料。

### 6.3 第三站：建立源侧五件套

五件套告诉宿主和协作者：这个员工如何作为 agent 工作。

五件套放在：

- `TriCompany/.github/source-agents/`

包括：

| 文件 | 像真实公司里的什么 | 作用 |
| --- | --- | --- |
| `<employee-id>.agent.md` | 岗位执行说明 | 定义适用场景、职责、护栏和输出结构 |
| `<employee-id>.soul.md` | 员工气质档案 | 定义说话方式、工作气质和禁止退化 |
| `<employee-id>.memory.md` | 记忆制度 | 定义记忆层怎么用，不写具体运行记忆 |
| `<employee-id>.colleagues.md` | 协作制度 | 定义协作档案怎么用，不写具体人物流水 |
| `<employee-id>.social.md` | 轻社交制度 | 定义社交层边界，不写正式工作事实 |

CHO 的五件套是：

- `TriCompany/.github/source-agents/chief-human-resources-officer/chief-human-resources-officer.agent.md`
- `TriCompany/.github/source-agents/chief-human-resources-officer/chief-human-resources-officer.soul.md`
- `TriCompany/.github/source-agents/chief-human-resources-officer/chief-human-resources-officer.memory.md`
- `TriCompany/.github/source-agents/chief-human-resources-officer/chief-human-resources-officer.colleagues.md`
- `TriCompany/.github/source-agents/chief-human-resources-officer/chief-human-resources-officer.social.md`

五件套齐备，只能说明源侧员工定义具备基础形态，不能说明它已经 live。

### 6.4 第四站：划清 role workspace 和 employee workspace

赛博公司要把岗位知识和员工实例记忆分开。

role workspace 是岗位知识。它像岗位手册，下一任也能继承。

employee workspace 是员工实例记忆。它像当前员工自己的工作笔记，属于当前实例。

公司共享知识放在 org shared，来源和边界审计放在 audit。

相关规则来自：

- `TriCompany/docs/engineering/role-employee-knowledge-workspace.md`

当前宿主生成对象后，会形成类似结构：

```text
TriCompany-copilot-host-assets/knowledge/roles/<employee-id>/
TriCompany-copilot-host-assets/knowledge/employees/<employee-id>/
TriCompany-copilot-host-assets/knowledge/org/shared/
TriCompany-copilot-host-assets/knowledge/audit/
```

新员工要记住：role 是岗位知识，employee 是当前实例，不要混写。

### 6.5 第五站：登记 binding profile

binding profile 是员工级宿主绑定档案。

它告诉大家：当前宿主准备怎样识别这个员工，它当前是否 live，support object 应该在哪里，运行态 namespace 应该是什么。

通常位置是：

- `TriCompany/.github/binding-profiles/<employee-id>.json`

CHO 的 binding profile 是：

- `TriCompany/.github/binding-profiles/chief-human-resources-officer.json`

当前 CHO 的关键状态是：

- `hostStage`: `current-copilot-host-live`
- `liveEntry.status`: `current-copilot-host-live`

这说明 CHO 已经完成当前 Copilot-host live binding，并接管 handoff checklist、staffing governance 与 completion tracking。这个结论不等于 TriMC 正式宿主切换。

### 6.6 第六站：登记 host object generation declaration

host object generation declaration 是对象生成声明。

它告诉生成链：如果要为这个员工生成当前宿主可消费对象，要从哪些源侧资料读，执行哪个 generator，跑哪些 validation，生成到 support root 的哪些位置。

通常登记在：

- `TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json`

这份声明像“工位和系统账号的开通工单”。有工单，不代表工位已经开好；有生成声明，也不代表 support object 已经发布。

### 6.7 第七站：发布 support object

support object 发布，是把当前 Copilot-host 可以读取的对象真正生成出来。

对 CHO 这种单个员工，可以使用类似命令：

```powershell
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee chief-human-resources-officer
```

发布完成后，应该能在 support root 看到：

- `TriCompany-copilot-host-assets/knowledge/roles/chief-human-resources-officer/**`
- `TriCompany-copilot-host-assets/knowledge/employees/chief-human-resources-officer/**`
- `TriCompany-copilot-host-assets/host-object-manifest.json` 里登记 CHO object set

如果这些没有出现，就不能说 support object 已经发布。

### 6.8 第八站：通过 live 前验证

新员工进入 live 前要验证。

如果这个员工是在替换旧入口，通常需要 shadow test。shadow test 像试运行，确认新旧切换不会出问题。

如果这个员工是全新岗位，不一定需要替代式 shadow test。但只要要进入 live，就仍然需要 live 前 validation gate。

这一步重点确认：

- source 资料真实。
- support object 真实发布。
- binding profile 和 support manifest 对得上。
- owner 切换有 handoff 记录。
- 文档没有把未 live 状态写成 live。

### 6.9 第九站：做 live binding 判断

live binding 是最后的上岗判断。

它要确认：当前阶段是否真的需要把这个员工接入 live 宿主，如果要接入，用哪个 live 入口，active owner 是否切换，运行态记录写到哪里。

live binding 完成之前，只能说该员工处在某个准备阶段。

live binding 完成之后，才可以说该员工在当前宿主独立上岗。

### 6.10 第十站：运行后沉淀与治理回填

员工 live 后，运行中的工作连续性会沉淀到 runtime state，而不是写回源侧人格文件。

治理层还要视情况回填：

- operating record
- registry
- workflow 文档
- binding profile
- support manifest
- training 文档

这一步让公司知道：这个员工不只是技术上可用，也已经在组织记录里闭环。

## 7. CHO 作为案例现在走到哪里

CHO 是理解这条链路的好案例，因为它已经完成了源侧准备中的关键几步，但还没有真正上岗。

### 7.1 CHO 为什么被提出

赛博公司开始出现越来越多岗位启用和职责交接问题：

- CPO 接手 PRD 归属路由。
- CTO 接手技术方案和交付门禁。
- CEOChiefOfStaff 回到公司级任务分派、催办、升级和收口。
- 新岗位需要 handoff checklist。
- 交接完成度需要 tracking。

这些都是人力行政和交接治理问题，所以 CHO 被提出为治理设计 owner。

### 7.2 CHO 已经具备哪些资料

当前已经具备：

- CHO 岗位说明书。
- CHO 源侧五件套。
- CHO binding profile。
- CHO host object generation declaration。
- CHO handoff governance 文档。
- 首条正式 `RESPONSIBILITY_HANDOFF` operating record。

这说明 CHO 不是随口提出的岗位，而是已经有源侧定义和启用准备。

### 7.3 CHO 已通过哪些门禁

当前已完成：

- support root 真实发布 CHO role / employee object。
- support root 的 `host-object-manifest.json` 登记 CHO object set。
- live 前 validation gate。
- live binding 判断。
- active owner 从 CEOChiefOfStaff 切换到 CHO。

所以 CHO 当前可以写成 current Copilot-host live。准确说法是：CHO 处于 `current-copilot-host-live`，交接治理由 CHO 主责执行，CEOChiefOfStaff 保留公司级协调、催办、升级与收口职责。

## 8. 用几个现有员工帮助定位状态

不同员工可能处在不同阶段，不能用一个状态套所有人。

| 员工 | 当前更接近哪种状态 | 该怎么理解 |
| --- | --- | --- |
| CEOChiefOfStaff | 当前 live 总助入口 | 有 legacy support path，也有新 role / employee support payload，重点是兼容迁移 |
| ChiefProductOfficer | 已有当前 Copilot-host live entry，并补齐 TriCompany 源侧资产 | 是已有 live 入口加 source-side handoff 的模式 |
| ChiefTechnologyOfficer | 已有当前 Copilot-host live entry，并补齐 TriCompany 源侧资产 | 是已有 live 入口加 source-side handoff 的模式 |
| RAndDTrainer | 源侧岗位定义、role / employee support payload 与当前 Copilot-host live 入口已完成 | 说明 module-local live entry 可以与源侧五件套分层存在 |
| ChiefHumanResourcesOfficer | 源侧定义、binding profile、generation declaration、support object 与 live binding 已齐 | 说明 CHO 已从源侧准备进入当前 Copilot-host live |
| ChiefAdministrativeOfficer | 源侧定义、binding profile、generation declaration、support object 与 live binding 已齐 | 说明 CAO 已从源侧准备进入当前 Copilot-host live |

这张表的目的不是给每个人贴标签，而是训练你判断“它到底走到了哪一站”。

## 9. 新员工看状态时的用语规范

赛博公司里，状态用语要非常精确。

可以这样写：

- “源侧岗位定义已建立。”
- “源侧五件套已补齐。”
- “binding profile 已登记。”
- “host object generation declaration 已登记。”
- “support object 已实际发布。”
- “live 前 validation gate 已通过。”
- “live binding 已完成。”

不要这样写：

- “有 agent 文件，所以已经上岗。”
- “有 binding profile，所以已经发布 support object。”
- “有 generation declaration，所以当前宿主已经消费。”
- “有 support object，所以已经 live。”
- “CHO 是治理 owner，所以 CHO 已经执行治理。”

对 CHO 当前最准确的一句话是：CHO 已完成源侧定义、binding profile、host object generation declaration、support root 实际发布、live 前 validation 和 live binding，当前处于 `current-copilot-host-live`；但这不等于 TriMC 正式宿主切换。

## 10. 新员工启用检查清单

当公司下次要启用任何新员工时，可以按这份清单检查。

1. 这个岗位为什么现在需要？
2. 它接手的是哪个稳定职责？
3. 当前是否只是临时任务，还是已经需要固定员工？
4. 岗位说明书是否写清职责、边界、协作对象和当前状态？
5. 源侧五件套是否齐备？
6. memory、colleagues、social 是否只写契约，不写运行流水？
7. role workspace 和 employee workspace 的边界是否清楚？
8. binding profile 是否登记 hostStage、liveEntry、supportObjects 和 runtimeNamespaces？
9. host object generation declaration 是否写清 source refs、generator、validation command 和 support targets？
10. support root 是否真实出现 role / employee object？
11. support manifest 是否登记该员工 object set？
12. 是否需要替代式 shadow test？
13. 如果不需要替代式 shadow test，live 前 validation gate 是否仍然完成？
14. 是否真的决定 live binding？
15. active owner 是否完成切换？
16. operating record、registry 和培训文档是否需要回填？

如果这份清单没有走完，就要保守表达状态。赛博公司最怕的不是慢一点，而是把准备中、已发布、已上岗混成同一个词。

## 11. 最后记住这条主线

赛博公司入职启用新员工，本质是一条从组织需要到宿主运行的链路。

它的主线是：

1. 先确认公司真的需要这个岗位。
2. 再把岗位和员工源侧定义写清楚。
3. 再准备当前宿主可消费的 support object。
4. 再通过必要门禁。
5. 最后才做 live binding 和治理回填。

CHO 只是这条链路里的当前案例。它让我们看见：一个员工可以已经有完整源侧准备，但仍然没有进入当前宿主 live。只要记住这点，你就不会把“定义了一个员工”和“员工已经上岗”混在一起。
