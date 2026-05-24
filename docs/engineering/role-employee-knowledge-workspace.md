# Role And Employee Knowledge Workspace

版本：V0.1
日期：2026-04-29
状态：源侧规则初版，已补统一员工对象生成、老员工兼容规则与 CPO / CTO live entry 绑定规则

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/role-employee-knowledge-workspace.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: on-demand-published-copy
- supportPublishedCopy: 待确认
- supportSyncRule: 仅在当前宿主显式依赖 role / employee workspace 规则时再发布 support 副本
- lastSyncedAt: 2026-04-29

## 1. 文档定位

本文用于沉淀虚拟公司员工知识空间的源侧规则。

它回答三个问题：

1. role knowledge workspace 和 employee knowledge workspace 有什么区别。
2. 具体员工实例如何读取和写入这些空间。
3. 这些机制如何发布到当前宿主支撑包而不把 support object set 写成真源。

## 2. 核心规则

- role knowledge workspace 归岗位，不归某个具体员工。
- employee knowledge workspace 归具体员工实例，不归抽象岗位。
- org shared workspace 归公司，用于沉淀跨岗位共享结论。
- audit workspace 归审计，用于记录来源、写入动作和回迁边界。
- 新增固定员工时，必须先在 TriCompany 源侧定义岗位 / 员工、agent 资产、四层记忆资产、职责、协作关系、流程 owner 和 knowledge workspace 规则，再发布到当前宿主生成对象载荷。
- 已存在的老员工进入新机制时，必须走兼容迁移：新增 `knowledge/roles/<employee-id>` 与 `knowledge/employees/<employee-id>`，保留原有 legacy support object path，并在 manifest 中声明映射；不得移动、删除或重命名当前 live 入口和运行态文件。
- `.tricompany-cognition/**` 是 runtime-state，只由 cognition provider 在实际写入时创建；host object generation 不预创建、不跟踪、不把它当作 source truth。

## 3. role knowledge workspace

role knowledge workspace 用于保存岗位级稳定知识。

适合放入：

- 岗位职责和边界
- 标准流程和判断框架
- 必读文档索引
- 与其他岗位的协作协议
- 岗位级 LLM wiki 页面
- 可复用 prompt / task / schedule 规则
- 继任时应保留的岗位知识

示例：

```text
knowledge/roles/chief-product-officer/
  inbox/
  wiki/
  audit/
  workbench/
```

这表示 ChiefProductOfficer 岗位应该如何工作，而不是某一位 CPO 当前记得什么。

## 4. employee knowledge workspace

employee knowledge workspace 用于保存具体员工实例的工作连续性。

适合放入：

- 当前员工的阶段性记忆
- 个人工作偏好和沟通风格
- 当前任务上下文
- 已读材料的个人整理
- 与 CEO 和其他员工的协作记录
- 临时判断、草稿和待复核结论
- 私域记忆，以及需要审计后才能进入共享层的内容

示例：

```text
knowledge/employees/cpo/
  inbox/
  wiki/
  audit/
  workbench/
```

这表示某个 CPO 员工实例的当前工作记忆，不等于 CPO 岗位本身。

## 5. 实例读取顺序

当具体员工执行任务时，默认按以下顺序组织 recall：

1. employee 私域记忆：当前员工自己的连续性和上下文。
2. role 岗位知识：岗位职责、流程和判断框架。
3. org shared 公司共享知识：会议结论、经营事实和跨角色共识。
4. audit 审计空间：来源、写入动作和回迁边界。

示例：CPO 评估一个 MVP 时，先读取自己的 employee/cpo 近期上下文，再读取 role/ChiefProductOfficer 的评估标准，再读取 org/shared 的战略和产品路线，最后把输出写入 employee/cpo；稳定结论经审批后再进入 role、org/shared 或正式 docs。

## 6. 发布边界

TriCompany 源侧维护的是员工定义、岗位规则、机制实现、教程和流程。

`.github/source-agents/<employee-id>/<employee-id>.memory.md`、`.colleagues.md`、`.social.md` 在源侧只允许作为认知层契约文件使用：它们定义该层的用途、当前原则、写入边界和运行资产落点，不承载具体人物档案、事项记录、命名记录、阶段任务记忆或 workflow 写回摘录。

新招聘固定员工时，应先通过 `runtime/cognition/employee_source_kit.py` 生成或校验 `TriCompany/.github/source-agents/<employee-id>/` 下的源侧五件套，再进入 host object payload 发布。该 scaffold / validator 只负责源侧 `.agent.md`、`.soul.md`、`.memory.md`、`.colleagues.md`、`.social.md` 的 canonical 模板和边界门禁，不自动登记 support manifest，也不启用 live 入口。

源侧五件套应表达岗位 / 员工真源、认知层边界、稳定职责与长期行为规则，但不固化当前 live 入口、当前宿主 support 路径、当前宿主阶段状态等 host binding 事实。这类绑定信息应进入 `TriCompany/.github/binding-profiles/<employee-id>.json`；`TriCompany/.github/manifests/tricompany-host-object-generation-manifest.json` 只继续承担生成规则与 binding 索引层。

当前 validator 还会显式拒绝把 `TriMetaverse/.github/agents/**` live 入口句式、`TriCompany-copilot-host-assets/knowledge/employees/**` support 路径以及 `.tricompany-cognition/employee/**` 这类具体 runtime employee 路径写回源侧五件套。

当前 workspace discovery 纪律是：`TriCompany/.github/agents/` 不再作为源侧五件套目录使用；只有 `TriMetaverse/.github/agents/` 是当前 Copilot-host live agent discovery 面。

TriCompany-copilot-host-assets 侧承接的是当前宿主实际消费或生成的对象载荷，例如：

- inbox 原始资料
- wiki 页面
- audit 记录
- workbench 快照
- schedule JSON

因此员工实例的消费记录默认落在当前宿主的 employee workspace 或 runtime cognition state 中；具体 support 路径由员工级 binding profile 承接，而不是写回源侧五件套。若其中某条内容经复核后升级为稳定项目事实，再按 owner 回写到 product / engineering / workflow / registry / operating records 等正式真源。

当前推荐发布入口是 `python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee <id|all>`；它把 support payload 生成和员工级 binding profile 导出收成同一条显式发布链。底层 `employee_host_object_generation` 与 `employee_host_binding_profile_generation` 仍保留，用于拆分验证或局部排查。

换宿主时，迁移的是完整虚拟公司源侧定义、岗位规则和流程，再按新宿主生成对象载荷；不应在新宿主重新招聘员工或重建流程。

## 7. 运行态边界

`TRICOMPANY_COGNITION_HOME` 或默认 `.tricompany-cognition/` 下的 markdown 文件，是员工实际运行后的私域 / 共享 / 审计落盘状态。

它与 `knowledge/roles/**`、`knowledge/employees/**`、`knowledge/org/shared/**`、`knowledge/audit/**` 的 support object payload 不是同一层：

- `knowledge/**` 表示当前宿主可消费的对象载荷，可由 host object generator 生成并由 manifest 跟踪。
- `.tricompany-cognition/employee/<actor>.md` 表示某个 actor 已经发生过 cognition 写入；没有文件只代表该 actor 尚未运行或尚未写入，不等于缺少员工定义。
- `.tricompany-cognition/org/shared.md` 与 `.tricompany-cognition/org/audit.md` 是全公司共享运行态命名空间，不按员工拆分，也不需要为 RAndDTrainer 单独创建 org 文件。

因此 RAndDTrainer、CPO、CTO、CHO 或 CAO 当前不出现在 `.tricompany-cognition/employee/` 仍是预期状态：它们已经有 source 定义、support payload 和当前 Copilot-host live binding，但运行态文件只在实际 cognition 写入后出现，不由 host object generation 预创建。CEOChiefOfStaff 出现在该目录，是因为总助是当前 live 员工且已经写过 cognition。

## 8. 老员工兼容迁移规则

CEOChiefOfStaff / 总助早于 role / employee workspace 机制出现，当前同时存在三类资产：

1. live 入口：`TriMetaverse/.github/agents/ceo-chief-of-staff.agent.md`，当前仍生效；历史 live 侧 `.soul/.memory/.colleagues/.social` 兼容文件已回收到 `TriCompany/.github/source-agents/ceo-chief-of-staff/` 源侧五件套，不再作为 live 入口旁路文件保留。
2. legacy support object set：`TriCompany-copilot-host-assets/knowledge/chief-of-staff/**`，继续作为当前总助 LLM wiki / workbench 兼容路径保留。
3. 新 role / employee support payload：`TriCompany-copilot-host-assets/knowledge/roles/ceo-chief-of-staff/**` 与 `knowledge/employees/ceo-chief-of-staff/**`，用于把总助纳入统一雇佣员工模型。

平滑升级顺序固定为：先补新 role / employee payload，再在 manifest 中登记 legacy path，再等后续 live 入口和 LLM wiki 任务显式切换；本轮不做破坏性迁移。

## 9. 当前状态

- 总助相关 LLM wiki 已有 chief-of-staff 专用实现和支撑包对象集。
- role / employee knowledge workspace 规则已在本文建立源侧口径。
- `TriCompany/runtime/cognition/knowledge_workspace.py` 已提供最小源侧路径抽象，可生成 role、employee、org shared、audit 四类 knowledge workspace，并固定 employee -> role -> org shared -> audit 的 recall 顺序。
- `python -m unittest runtime.cognition.role_employee_workspace_validation` 可验证路径、目录生成和 recall 顺序。
- `python -m unittest runtime.cognition.employee_source_kit_validation` 可验证新员工源侧五件套 scaffold 和源码 / 消费资产边界门禁。
- 统一员工 host object generation 已由 `runtime/cognition/host_object_generation.py`、`runtime/cognition/employee_host_object_generation.py` 与 `runtime/cognition/rd_trainer_host_object_generation.py` 提供，当前可生成 RAndDTrainer、CEOChiefOfStaff、ChiefProductOfficer、ChiefTechnologyOfficer 与 ChiefHumanResourcesOfficer 的 role / employee / org shared / audit support object payload 和 `host-object-manifest.json`。
- CEOChiefOfStaff 已补入新 role / employee support object set，同时保留 `knowledge/chief-of-staff/**` legacy 兼容路径；live `.github` 入口未被替换。
- ChiefProductOfficer 与 ChiefTechnologyOfficer 已绑定现有 live `.github` 入口并补齐 TriCompany 源侧五件套；这属于当前 Copilot-host live 上岗，不代表 TriMC 正式宿主切换。
- 跨岗位 LLM wiki refresh 任务、跨员工 schedule 模板、RAndDTrainer live 宿主启用和跨宿主 manifest 仍待后续实现。
