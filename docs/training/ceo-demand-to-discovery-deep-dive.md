# ################################### 
# 文档提示词：你是小吴吧，你现在带着我从ipd的ceo-demand开始，一小段一小段的，先业务逻辑后代码逻辑（细到连语法都讲如有必要），我们花几天时间，把ipd初始化到discovery的五件套生成，把他捋清楚，你找个文档来保存这个过程。一小段一小段细细讲，我说明确说明白了，我们再进入下一个一小段。
# ###################################

# CEO Demand → Discovery 逐段深讲（小吴教学日志）

版本：V0.1
日期：2026-07-04
状态：教学中（进行中）

## 教学约定

1. 每一次课只讲**一小段**：一个函数调用、一个分支、一个文件。
2. 先讲业务逻辑（这一段在流程中做什么、为什么在这），再讲代码逻辑（怎么写的、每一行在干什么），必要时讲到 Python 语法。
3. 你说"明白了"，我们才进入下一小段。
4. 本文档是教学过程的记录，随着教学推进不断追加。

---

## 第一段：task-intake 这个命令是什么

### 业务逻辑

你敲下这条命令：

```
python -m runtime.cognition.chief_of_staff_ipd_case task-intake \
  --case-id IPD-20260610-PLATFORM-001 \
  "做一个统一模型 API 平台"
```

`task-intake` 是子命令（subcommand），`"做一个统一模型 API 平台"` 是子命令的**位置参数**（positional argument）。注意：这里没有写 `--task` 或 `task` 关键字，因为它是位置参数——直接放在选项后面就行。

`task-intake` 是 IPD 世界里的"前台窗口"——你只需要给一段自然语言描述，它帮你把 ID、标题、目标、关联模块、七槽位全部处理好，调 `initialize_ipd_case()` 创建 case。跟 `init` 子命令的区别是：`init` 是"精细模式"，每个字段都要你自己填；`task-intake` 是"智能模式"，能从你的大白话里自动推断。

### argparse 位置参数 vs 可选参数（语法小课）

看第 143 行的注册代码：

```python
task_intake_parser.add_argument("task", nargs="+")
```

`"task"` 前面**没有** `--`，所以 argparse 把它当位置参数处理。用户不需要写 `--task` 或 `task`，直接把文本放在命令行末尾即可。

对比第 145 行：

```python
task_intake_parser.add_argument("--case-id", ...)
```

`"--case-id"` 前面有 `--`，这是可选参数（optional argument），用户必须写 `--case-id IPD-...`。

`nargs="+"` 的意思是"至少一个，可以多个"——所以你写 `"做平台"` 是一个词，写 `"做一个 统一模型 API 平台"` 会被 argparse 拆成多个词然后拼起来。

### 代码逻辑逐行讲

```python
# 第 351 行
if args.command == "task-intake":
```

`args.command` 是 argparse 自动解析出来的。你在命令行写 `task-intake`，这里就进这个分支。

```python
# 第 352 行
task_description = _normalize_task_text(args.task)
```

`args.task` 是你命令行里 `"做一个统一模型 API 平台"` 这段文字。`nargs="+"`（第 143 行）表示可以写多个词，argparse 会把它们拼成一个列表。`_normalize_task_text` 把它拼成干净的字符串。

```python
# 第 353-354 行 — case_id 的自动生成
case_id=args.case_id or _generate_case_id(task_description, workspace_root=args.workspace_root),
```

这是 Python 的 `or` 短路求值：如果你传了 `--case-id`，就用你的；如果没传，`_generate_case_id()` 会从任务描述里提取关键词（比如 "平台" → `PLATFORM`），加上日期和序号自动生成一个 `IPD-20260704-PLATFORM-001` 这样的 ID。

```python
# 第 355 行 — 标题自动推导
title=args.title or _derive_title(task_description),
```

同样的 `or` 逻辑：没传 `--title` 就从任务描述里推断一个。

```python
# 第 356 行 — 目标自动推导
objective=args.objective or _derive_objective(task_description),
```

同上。

```python
# 第 362-363 行 — 关联模块的自动路由
related_modules=args.related_module
    or _resolve_related_modules(task_description, mode=args.module_routing_mode),
```

这里的 `or` 有三层逻辑（对应 `--module-routing-mode`）：
- `deterministic`：直接拿内置的 `_MODULE_ROUTING_HINTS` 做关键词匹配，比如描述里有"模型 API"就匹配到 TriStaciss
- `cpo`：调用外部 CPO 路由器
- `auto`（默认）：先试 CPO，失败就回退到 deterministic

```python
# 第 393-394 行
slot_answers=_parse_slot_answers(args.slot_answer),
require_clarification_slots=True,
```

如果你通过 `--slot-answer competitorReference=Cursor` 手动填了槽位，这里解析成字典。`require_clarification_slots=True` 意味着七槽位不全的情况下状态会标记为 `paused-intake-clarification`。

```python
# 第 399 行
print(json.dumps(result, ensure_ascii=False, indent=2))
```

最终调用 `initialize_ipd_case()` 返回的结果是一个大字典，打印成格式化的 JSON 给你看。

> **总结这一小段的要点**：`task-intake` 就是一个智能接单窗口。你说大白话，它补全 ID、标题、目标、模块，然后调 `initialize_ipd_case()`。你不需要记住所有参数——只记住 `--case-id` 和任务描述就够了。

---

## 第二段：`initialize_ipd_case()` 函数签名与前 4 行

### 业务逻辑

`initialize_ipd_case()` 是整个 IPD 的"出生证明签发处"。不管你是走 `task-intake`（智能模式）还是 `init`（精细模式），最终都落到这个函数。它做三件顶层的事：

1. 确定 case 在文件系统里的位置（目录路径）
2. 判断是新建还是重新细化（refine）已有的 intake
3. 组装一个巨大的 `case_payload` 字典写进 `case.json`

我们这一小段只看前 4 行代码——时间戳、ID 标准化、目录路径、空变量初始化。

### 代码逐行

```python
# 第 1501-1502 行 — 函数签名里的 *
def initialize_ipd_case(
    *,
```

`*` 是 Python 的 **keyword-only 参数分隔符**。它后面的所有参数都**必须**用关键字传递，不能用位置。比如你只能写 `initialize_ipd_case(case_id="...", title="...")`，不能写 `initialize_ipd_case("...", "...")`。

**为什么这样设计？** 这个函数有 30 个参数，如果允许位置传参，调用方很容易搞错顺序。强制关键字传参是一种防御性设计——宁可多打几个字，也不要因为参数顺序错了 debug 半天。

```python
# 第 1531 行 — 返回值类型
) -> dict[str, Any]:
```

`dict[str, Any]` 是 Python 的类型标注：键是字符串，值可以是任何类型。这个函数返回一个巨大的嵌套字典——就是我们之前说的 `case_payload`。

```python
# 第 1532 行
now = _timestamp_now()
```

给这次创建操作打一个统一时间戳。后续所有用到"创建时间"的地方都用这个变量，保证一致性。`_timestamp_now()` 返回 ISO 8601 格式字符串，比如 `"2026-07-05T17:10:00+08:00"`。

```python
# 第 1533 行
normalized_case_id = _normalize_identifier(case_id)
```

把你传进来的 `case_id`（可能是 `IPD-20260610-PLATFORM-001` 或用户手打的 `ipd-20260610-platform-001`）统一成标准格式：大写前缀 + 日期 + 主题 + 序号。`_normalize_identifier` 负责大小写统一、多余空格清除、非法字符替换。

```python
# 第 1534 行
case_root = chief_of_staff_ipd_case_root(normalized_case_id, workspace_root)
```

这行算出 case 在文件系统里的目录路径。`chief_of_staff_ipd_case_root` 来自 `chief_of_staff_wiki_paths` 模块，返回值是 `pathlib.Path` 对象。最终路径类似：

```
workbench/ipd/cases/ipd-20260610-platform-001/
```

```python
# 第 1535 行 — 类型标注 + 初始值
existing_case_payload: dict[str, Any] | None = None
```

`dict[str, Any] | None` 是 Python 3.10+ 的联合类型语法，等价于旧写法 `Optional[dict[str, Any]]`。意思是"这个变量要么是一个字典，要么是 `None`"。先初始化成 `None`——假设这个 case 还不存在；等检查完文件系统再决定要不要读取已有数据。

> **总结这一小段**：函数开头 4 行做了三件事——拿时间戳、规范化 ID、确定目录路径。`*` 强制关键字传参是防御性设计（30 个参数不能搞混顺序）。`case_root` 是后续所有读写操作的根目录。

---

## 第三段：新建还是重开？`case_root.exists()` 分支

### 业务逻辑

当你执行 `task-intake` 时，可能有两种情况：

1. **这个 case 是全新的**——目录不存在 → 创建目录，走新建流程
2. **这个 case 已经存在**——目录已存在 → 加载旧数据，走"精细化重填"流程

第二种情况对应实际场景：小贾第一次可能只建了粗略的 case，后来 CPO 补充了更多信息，需要回到 intake 阶段重新编辑。但这里有一道硬门禁：**如果 case 已经推进到了 intake 之后（比如已经进入 discovery），就不允许回头改 intake 了**。

### 代码逐行

```python
# 第 1535 行
existing_case_payload: dict[str, Any] | None = None
```

先初始化为 `None`——默认假设 case 不存在。

```python
# 第 1536 行
if case_root.exists():
```

`case_root` 是上一段算出来的 `pathlib.Path` 对象。`.exists()` 检查这个目录在文件系统里是否已存在。返回 `True` 或 `False`。

```python
# 第 1537 行 — 目录存在：加载旧数据
existing_case_payload = _load_case(normalized_case_id, workspace_root)
```

`_load_case()` 读取目录下的 `case.json` 文件，解析成 Python 字典。**case 的唯一真源就是 `case.json`**，所有状态都存在这个 JSON 文件里。

```python
# 第 1538-1539 行 — 硬门禁
if not _can_refine_intake(existing_case_payload):
    raise FileExistsError(
        f"IPD case already exists and cannot be reinitialized: {normalized_case_id}"
    )
```

`_can_refine_intake()` 判断这个 case 是否还允许回头编辑 intake。如果 case 已经推进到了 discovery 及之后，它返回 `False`，函数直接抛 `FileExistsError`（Python 内置异常）终止。

**门禁背后的业务规则**：intake 一旦签核通过（CEO + CEOChiefOfStaff 双签），case 进入正式流水线，不能再回头改需求。这保护的是"签核之后不乱改需求"这条治理规则。

```python
# 第 1540-1541 行 — 目录不存在：新建目录
else:
    case_root.mkdir(parents=True, exist_ok=True)
```

`mkdir(parents=True, exist_ok=True)` 是 `pathlib.Path` 的方法：
- `parents=True`：如果父目录（比如 `workbench/ipd/cases/`）也不存在，一并创建
- `exist_ok=True`：防御性编程，即使目录存在也不报错（防止竞态条件）

```python
# 第 1542 行
existing_intake = existing_case_payload.get("intake", {}) if isinstance(existing_case_payload, dict) else {}
```

为后续做准备：如果是重开已有 case，从旧数据里提取 `intake` 字段（嵌套字典）；如果是新建，给空字典 `{}`。`isinstance(existing_case_payload, dict)` 做类型安全检查——确保读出来的确实是字典。

> **总结**：`if case_root.exists()` 做的事就是"新建目录 vs 加载旧数据"。核心门禁在 `_can_refine_intake()`——case 一旦推进到 discovery 之后，回头改 intake 的路就堵死了。

---

## 第四段：审批骨架与七槽位澄清表

### 业务逻辑

`initialize_ipd_case()` 的第 1543-1549 行在做两件 intake 的核心工作：

1. **搭建审批骨架**（`_build_approvals`）——给 CEO 和 CEOChiefOfStaff 各建一条审批记录
2. **生成七槽位澄清表**（`_build_intake_clarification_sheet`）——CEO 必须回答的 7 个关键问题

这两件事合在一起，决定了 intake 的初始状态：**"等待 CEO 填槽 + CEO + 总助双签"**。

### 第 1543 行：`_build_approvals()`

```python
approvals = _build_approvals(required_approvers, auto_approved_role=None, now=now)
```

`required_approvers` 默认值是 `INTAKE_REQUIRED_APPROVERS`，即 `("CEO", "CEOChiefOfStaff")`（第 46 行定义）。

`_build_approvals()` 给每个审批角色生成一条结构化审批记录：

```json
[
  {"role": "CEO",              "decision": "pending", "signedAt": "", ...},
  {"role": "CEOChiefOfStaff",  "decision": "pending", "signedAt": "", ...}
]
```

`auto_approved_role=None` 意味着**没有任何角色可以自动通过**——intake 阶段必须两个人手动签。这是最严的门禁。

### 第 1544 行：`_normalize_slot_answers()`

```python
normalized_slot_answers = _normalize_slot_answers(slot_answers)
```

把用户通过 `--slot-answer competitorReference=Cursor` 传进来的键值对，做 key 标准化（大小写、空格清理），返回干净的 `{slotKey: value}` 字典。

### 第 1545-1549 行：`_build_intake_clarification_sheet()`

```python
clarification_sheet = _build_intake_clarification_sheet(
    task_description=task_description,
    slot_answers=normalized_slot_answers,
    required=require_clarification_slots,
)
```

这是七槽位的**生成引擎**。它遍历 `_INTAKE_CLARIFICATION_SLOT_TEMPLATES`（第 1305 行），七个槽位：

| # | slotKey | 问题 | 为什么重要 |
|---|---------|------|------------|
| 1 | `competitorReference` | 对标哪 1-3 个产品/平台？ | 没对标，CPO 没研究起点 |
| 2 | `targetUserScenario` | 先服务谁、什么场景？ | 没用户/场景，CMO 无法验证需求 |
| 3 | `deliveryWindow` | 什么节奏推进？ | 没节奏约束，无法拆阶段 |
| 4 | `budgetGuardrail` | 预算窗口/成本上限？ | 没预算，CFO 无法形成护栏 |
| 5 | `successMetric` | 首轮成功的信号？ | 没信号，容易把"做完了"当"做对了" |
| 6 | `mustHaveScope` | 必须交付的最小范围？ | 没最小范围，PRD 会膨胀 |
| 7 | `explicitOutOfScope` | 明确不做哪些？ | 没不做项，远期能力污染当前目标 |

核心遍历逻辑（第 5035-5058 行）：

```python
for template in _INTAKE_CLARIFICATION_SLOT_TEMPLATES:
    slot_key = template["slotKey"]
    current_value = slot_answers.get(slot_key, "")   # 从用户填的答案里取
    status = "provided" if current_value else "needs-ceo-input"
    if required and not current_value:
        missing_slot_keys.append(slot_key)            # 记入缺失列表
        follow_up_questions.append(template["question"])
```

最后：

```python
overall_status = "ready-for-dispatch" if not missing_slot_keys else "needs-ceo-clarification"
```

- **七槽全满** → `"ready-for-dispatch"`，可以进入审批签核
- **有槽位空缺** → `"needs-ceo-clarification"`，case 挂起在 `paused-intake-clarification`，等 CEO 回来填

> **总结**：这三行代码搭建了 intake 的两大支柱——双人审批链 + 七槽位澄清表。槽位不全 = 流程暂停，CEO 必须回来补。这也是为什么 §3 教程里说"槽位不全 → paused-intake-clarification"。

---

## 第五段：分类、主题与阶段模板选择——IPD 的铁路道岔

### 业务逻辑

这三行（1550-1562）是 IPD 最重要的**分叉点**——决定了这个 case 走"十阶段项目交付流水线"还是"agile sprint 流程优化线"。

```
case_id: IPD-20260610-PLATFORM-001  →  "project-delivery"   →  十阶段模板
case_id: IPD-20260612-WORKFLOW-002  →  "process-improvement" →  5 阶段 agile 模板
```

推理依据是 case_id 里的短名（PLATFORM / WORKFLOW / TRAINING / VALIDATION），不需要手动传 `--case-category`。

### 第 1550-1553 行：`_normalize_case_category()`

```python
resolved_case_category = _normalize_case_category(
    case_category or str(existing_intake.get("caseCategory") or ""),
    case_id=normalized_case_id,
)
```

优先级链（Python `or` 短路求值）：

1. 用户显式传了 `--case-category project-delivery` → 直接用
2. 重开已有 case → 从旧 `existing_intake["caseCategory"]` 取
3. 都没有 → 从 `case_id` 推断

推断规则：`_PROCESS_IMPROVEMENT_REFERENCE_THEMES = {"WORKFLOW", "TRAINING", "VALIDATION"}`（第 50 行）。case_id 中包含这些短名 → `"process-improvement"`；否则 → `"project-delivery"`。

### 第 1554-1558 行：`_normalize_reference_theme()`

```python
resolved_reference_theme = _normalize_reference_theme(
    reference_theme or str(existing_intake.get("referenceTheme") or ""),
    case_id=normalized_case_id,
    case_category=resolved_case_category,
)
```

同样的 `or` 优先级链。`reference_theme` 是从 case_id 中提取的短名（如 `PLATFORM`、`WORKFLOW`）。它后续用于 Discovery/Intelligence 阶段的 **source seed 过滤**——只选匹配 theme 的竞品和开源代码种子。

### 第 1559-1562 行：`_initial_stage_templates()`

这个函数只有 3 行（第 5136-5139 行）：

```python
def _initial_stage_templates(*, case_category: str, reference_theme: str):
    if str(case_category or "").strip() == _CASE_CATEGORY_PROCESS_IMPROVEMENT:
        return _PROCESS_IMPROVEMENT_STAGE_TEMPLATES   # 5 阶段 agile sprint
    return _STAGE_TEMPLATES                            # 10 阶段交付流水线
```

`reference_theme` 当前未使用（参数预留）。真正的分叉只看 `case_category`。

### 两种模板对比

| | `_STAGE_TEMPLATES` | `_PROCESS_IMPROVEMENT_STAGE_TEMPLATES` |
|---|---|---|
| 用途 | 项目交付 | 流程优化 |
| 阶段数 | 10 | 5（+ validation-handoff） |
| 第一阶段 | discovery | backlog |
| 核心 owner | CPO / CTO | CEOChiefOfStaff / CTO / CPO |
| 产出 | 产品代码 | 更好的流程规则 |

> **总结**：这三行就是 IPD 的"铁路道岔"——case_id 里的短名决定了整条 case 走哪条轨道。`_initial_stage_templates` 是最终裁决者，只有 3 行代码，但决定了后续所有阶段的生成逻辑。

---

## 第六段：组装 `case_payload`——顶层字段与 intake 子对象

### 业务逻辑

前面五段都是在**做准备工作**——时间戳、ID、目录、审批骨架、七槽位、分类。现在 `case_payload` 字典开始把这些全部**组装成一个 JSON 文档**。这一小段看顶层字段和 `intake` 子对象（第 1563-1605 行）。

`intake` 子对象是 case 的"出生档案"——记录了 CEO 最初提了什么、七槽位填了什么、谁审批了、release 版本是什么。它**不会随着 case 推进到 discovery 而改变**（`_can_refine_intake` 门禁堵死了回头路）。

### 第 1563-1573 行：顶层 case 字段

```python
case_payload = {
    "schemaVersion": IPD_CASE_SCHEMA_VERSION,   # "1.0" — 数据格式版本
    "caseId": normalized_case_id,               # 标准化后的 ID
    "title": title.strip(),                     # 标题（去首尾空格）
    "status": "awaiting-intake-approvals",      # 初始状态：等签核
    "priority": priority.strip() or "high",     # 优先级，默认 high
    "relatedModules": _string_list(related_modules),  # ["TriStaciss", "TriAvatar"]
    "createdAt": str((existing_case_payload or {}).get("createdAt") or now),  # 保留原始创建时间
    "updatedAt": now,                           # 本次更新时间
    "currentStageKey": "",                      # 初始为空，签核后才赋值
    "currentWorkItemPath": "",                  # 同上
```

值得注意的两点：

- `"createdAt"` 用了 Python 的 `or` 链式短路求值：`(None or {}).get("createdAt")` → 新建时返回 `None` → 取 `now`。重开时保留原始时间。
- `_string_list()` 确保任何传入的可迭代对象都转成干净的字符串列表。比如 `"hello"` → `["hello"]`。

### 第 1574-1605 行：intake 子对象（按分组讲）

**① 经营上下文（第 1575-1586 行）**

```python
"objective": objective.strip(),           # 目标
"taskDescription": task_description,      # 原始任务描述
"constraints": [...],                     # 约束条件
"opportunitySignals": _merge_string_lists(opportunity_signals, market_context),
"businessModelFit": [...],               # 商业模式匹配
"stageFit": [...],                       # 当前阶段匹配
"companyContext": [...],                 # 公司背景
"ownerProposal": _merge_string_lists(owner_proposal, division_of_work),
"resourceEnvelope": _merge_string_lists(resource_envelope, staffing_cost, other_cost),
"prerequisites": [...],                  # 前置条件
"requiredSupport": [...],               # 需要支持的岗位
"expectedOutcomes": [...],              # 期望产出
```

`_merge_string_lists()` 做历史兼容合并——旧代码可能用 `marketContext` / `divisionOfWork` / `staffingCost` 等旧字段名，合并后统一存进新字段。

**② 澄清与分类（第 1587-1592 行）**

```python
"slotAnswers": normalized_slot_answers,        # 七槽位答案
"clarificationRequired": True,                 # 强制要求
"clarificationSheet": clarification_sheet,     # 完整的七槽位结构
"caseCategory": "project-delivery",            # 分类
"referenceTheme": "PLATFORM",                  # 主题
"roleAssignmentMatrix": _build_intake_role_assignment_matrix(),
```

`_build_intake_role_assignment_matrix()`（第 5000 行）把岗位分配矩阵转成字典列表——方便后续查"CMO 能在 discovery 冻结 case 吗"。

**③ Release 元数据（第 1594-1600 行）**——DST-04 contract 在此初始化：

```python
"briefPath": "",            # intake-brief.json 路径，后面 _write_intake_brief 补
"packageHash": "",          # 空，签核时才计算哈希
"releaseCounter": 0,        # 发布计数
"releaseVersion": "",       # 发布版本号
"releaseStatus": "draft",   # draft → released
"releaseIssuedAt": "",      # 发布时间
"releaseIssuedByRole": "",  # 签发人
```

**④ 审批（第 1601-1604 行）**

```python
"createdBy": "CEOChiefOfStaff",
"createdAt": str(...),       # 保留原始 intake 创建时间
"approvals": approvals,      # CEO + CEOChiefOfStaff 双人 pending
"status": _approval_rollup(approvals),  # → "pending"
```

`_approval_rollup()` 聚合所有审批记录：全部 approved → `"approved"`，有待签 → `"pending"`。

> **总结**：`intake` 子对象分四组——经营上下文、七槽位+分类、release 元数据、审批链。它是 case 的"出生档案"，签核后不可改。

---

## 第七段：`stages` 数组的列表推导式生成

### 业务逻辑

`stage_templates` 是第五段里 `_initial_stage_templates()` 返回的——project-delivery 十条、process-improvement 五条。每条模板是一个字典，定义了阶段的"设计蓝图"：谁管、谁做、什么阶段、需要什么输入。

列表推导式把每条模板**实例化**成一个 stage record——相当于拿蓝图造出了具体的阶段对象，给每个阶段注入审批人、初始化为 pending 状态、并预留后续运行时会填写的字段。

### 代码结构（第 1606-1639 行）

```python
"stages": [
    {
        # 第一类：模板直接复制（8 个）
        "stageKey": template["stageKey"],           # "intake"
        "title": template["title"],                 # "初始化与受理"
        "businessOwner": template["businessOwner"], # "CEO"
        "actingOwner": template["actingOwner"],     # "CEOChiefOfStaff"
        "moduleExecutor": template["moduleExecutor"], # "CEOChiefOfStaff"
        "gateOwner": template["gateOwner"],         # "CEOChiefOfStaff"
        "ownerRole": template["actingOwner"],       # 历史兼容字段
        "phaseKey": template["phaseKey"],           # "intake"
        "participantRoles": list(template["participantRoles"]),

        # 第二类：动态生成（2 个）
        "requiredApprovers": _stage_required_approvers(template["actingOwner"]),
        "approvals": _build_approvals(..., auto_approved_role=None, now=""),

        # 第三类：初始化为空/草稿（12 个）
        "status": "pending",
        "workItemPath": "", "outputPath": "",
        "packageHash": "", "releaseCounter": 0, "releaseVersion": "",
        "releaseStatus": "draft", "releaseIssuedAt": "", "releaseIssuedByRole": "",
        "activatedAt": "", "submittedAt": "", "completedAt": "",
        "blockedReason": "", "outputSummary": "",
        "lastUpdatedAt": now,
    }
    for template in stage_templates
],
```

### 三类字段详解

**第一类：模板直接复制。** 8 个字段从 `_STAGE_TEMPLATES` 或 `_PROCESS_IMPROVEMENT_STAGE_TEMPLATES` 原样搬过来。第 1614 行 `"ownerRole": template["actingOwner"]` 和第 1611 行重复——历史兼容，旧代码查 `ownerRole`，新代码查 `actingOwner`。

**第二类：动态生成。** `_stage_required_approvers("CEOChiefOfStaff")` 返回 `["CEOChiefOfStaff"]`——每个阶段只需要它的 actingOwner 审批。`auto_approved_role=None` 意味着即使总助审自己的阶段，也必须显式签 `approved`。

**第三类：未来运行时填充。** 全是空字符串或 0。DST-04 release 四件套（packageHash / releaseCounter / releaseVersion / releaseStatus）和阶段生命周期时间戳（activatedAt → submittedAt → completedAt）都在后续运行时逐步填写。`lastUpdatedAt` 初始化为 `now`——和别的空字段不同，至少有一个"被碰过"的时间戳。

### 语法重点：为什么到处是 `list()` 和 `dict()`？

```python
"participantRoles": list(template["participantRoles"]),        # ← list()
"schemaHint":        dict(template["schemaHint"]),              # ← dict()
"inputRequirements": list(template["inputRequirements"]),       # ← list()
"superDevReferenceStages": list(template["superDevReferenceStages"]),  # ← list()
```

Python 字典赋值是**引用传递**。如果不做 `list()` 浅拷贝，stage record 里的 `participantRoles` 和模板里的 `participantRoles` 就是**同一个列表对象**。后续 `list.append("CMO")` 会污染模板，下一个 case 初始化时会带上不该有的角色。`list()` 和 `dict()` 创建新对象，切断引用链。

> **总结**：列表推导式把一个 10 条（或 5 条）模板数组，转成同等数量的 stage record 数组。每个 stage record 混合了三类来源——模板静态数据 + 动态审批生成 + 空字段占位。

---

## 第八段：`initialize_ipd_case()` 收尾——写入磁盘 + 事件记录 + 对账

### 业务逻辑

`case_payload` 组装完还在内存里。收尾四步把它落地为三个磁盘文件，然后做一次"写后对账"确保数据一致。

```
ipd-cases/IPD-20260706-PLATFORM-001/
├── case.json          # 完整 case（_save_case）
├── intake-brief.json  # 签核用精简版（_write_intake_brief）
└── events.jsonl       # 事件日志（_append_event，追加模式）
```

### 第一步：`_write_intake_brief()`（第 1641 行）

独立函数（4913-4965 行）提取 ~30 个字段生成 `intake-brief.json`。存在理由是：`case.json` 会随着推进越来越臃肿，但**签核只需要 intake 数据**。brief 是签核快照。

```python
# 第 4921 行：写文件前先算哈希
intake["packageHash"] = _package_hash(_build_intake_signature_payload(case_payload))
```

DST-04 防篡改——签核后 brief 被改过，哈希就对不上了。

文件分三层：**元数据**（`kind: "ipd-intake-brief"`、`executionFlow`、`stageLine`）、**审批**（`signaturePolicy`、`signatureChain`、`packageHash`）、**内容**（`briefing` 组 9 个子字段）。

### 第二步：回填 briefPath（第 1642 行）

```python
case_payload["intake"]["briefPath"] = intake_brief_path.as_posix()
```

`as_posix()` 把 Windows 反斜杠转正斜杠，跨平台兼容。

### 第三步：`_save_case()`（第 1643 行）

只有 5 行（4805-4809），但**每次写前都调 `_ensure_case_defaults`**：

```python
def _save_case(case_payload, workspace_root):
    _ensure_case_defaults(case_payload)     # ← 先归一化！
    case_path = _case_file_path(...)
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(json.dumps(case_payload, ensure_ascii=False, indent=2) + "\n", ...)
```

`_ensure_case_defaults`（4830-4880 行）做两件事：
1. **类型强制**：`str()` 文本、`int()` 计数、`bool()` 布尔——防 `None` 污染
2. **历史字段合并**：`marketContext` → `opportunitySignals`、`roughDivisionOfWork` → `ownerProposal`、`staffingCost` + `otherCosts` → `resourceEnvelope`。字段改名后确保落盘结构一致。

### 第四步：`_append_event()`（第 1644-1653 行）

```python
_append_event(case_id,
    "intake-brief-refined" if existing_case_payload is not None else "case-initialized",
    {"createdBy": ..., "intakeStatus": ..., "intakeBriefPath": ...})
```

实现（4812-4827）：

```python
def _append_event(case_id, event_type, payload, *, workspace_root):
    path = _events_file_path(case_id, workspace_root)    # → events.jsonl
    body = {"timestamp": _timestamp_now(), "eventType": event_type, "payload": payload}
    with path.open("a", encoding="utf-8") as handle:    # ← "a" = append
        handle.write(json.dumps(body, ensure_ascii=False) + "\n")
```

- **`.jsonl` 格式**：每行一个 JSON 对象，不是 JSON 数组。追加写入不用重写整个文件。
- **`"a"` 模式**：文件不存在自动创建，存在则末尾追加。
- **事件类型分叉**：新建 → `"case-initialized"`，重开 → `"intake-brief-refined"`。

### 第五步：`return reconcile_ipd_case()`（第 1654 行）

```python
def reconcile_ipd_case(case_id, *, workspace_root):
    case_payload = _load_case(case_id, workspace_root)          # 重新读盘
    case_payload, summary = _reconcile_case_payload(case_payload, workspace_root)
    _save_case(case_payload, workspace_root)                    # 写回
    return summary
```

**写后对账**——写完立即读回、做一致性修复（补默认字段）、再写回。返回值含 `advanced`、`status`，供 CLI 输出。

> **总结**：收尾四步把内存落地为三个磁盘文件。`events.jsonl` 用 append，`case.json` 和 `intake-brief.json` 全量覆写。`_ensure_case_defaults` 每次 `_save_case` 前做类型强制和历史字段合并。最后 `reconcile_ipd_case` 做写后对账。`initialize_ipd_case()` 到此全函数走完。

---

## 第九段：`intake-approve`——从 CLI 命令到签核生效

### 业务逻辑

`initialize_ipd_case()` 走完后，case 状态是 `"awaiting-intake-approvals"`。CEO 和总助需要分别在 `intake-brief.json` 上签 `approved`。两人都签完，intake 才算正式通过。

### CLI 层（第 212-218 行 + 第 402-413 行）

```bash
python chief_of_staff_ipd_case.py intake-approve \
    --case-id IPD-20260706-PLATFORM-001 \
    --role CEO \
    --decision approved
```

dispatch 只做一件事——把 argparse 参数透传给 `record_intake_signoff()`：

```python
if args.command == "intake-approve":
    result = record_intake_signoff(
        args.case_id, role=args.role, decision=args.decision,
        note=args.note, signing_key=args.signing_key,
        mnemonic=args.mnemonic, workspace_root=args.workspace_root,
    )
```

### 核心函数：`record_intake_signoff()`（第 1681-1735 行）

9 个步骤，按顺序走：

**步骤 1：加载 + 冻结检查**
```python
case_payload = _load_case(case_id, workspace_root)
_assert_case_not_frozen(case_payload, action="intake signoff")
```
冻结的 case 不能签核——`freeze` 命令的保护。

**步骤 2：重新计算 packageHash**
```python
package_hash = _package_hash(_build_intake_signature_payload(case_payload))
case_payload["intake"]["packageHash"] = package_hash
```
每次签核前重算哈希——两次签核之间数据可能被改过。哈希写进审批记录，作为"我签的是这个版本"的证据。

**步骤 3：原地修改审批记录**
```python
approval_record = _record_signed_approval(
    case_payload["intake"]["approvals"],   # ← 传引用，原地改！
    role=role, decision=decision, note=note,
    now=now, package_hash=package_hash,
    signing_key=signing_key, mnemonic=mnemonic,
    default_seed=_default_wallet_seed(role),
)
```
找到 `role` 匹配的记录，填上 `decision`、`signedAt`、`packageHash`、`signerAddress`。同一个人签两次不会创建重复记录（原地覆盖）。

**步骤 4：汇总状态**
```python
case_payload["intake"]["status"] = _approval_rollup(case_payload["intake"]["approvals"])
```
三态：
- 有任一 `rejected` → `"rejected"`
- 全部 `approved` → `"approved"`
- 其他 → `"pending"`

**步骤 5：总助签核时触发 DST-04 release（第 1709-1716 行）**
```python
if role == "CEOChiefOfStaff" and decision.strip().lower() == "approved" \
   and case_payload["intake"]["status"] == "approved":
    release_version = _issue_release(
        case_payload["intake"], case_id=..., subject_token="INTAKE",
        issued_by_role=role, now=now,
    )
```
只在**总助签核 + 两人都 approved**时触发。为什么是总助？因为总助是 intake 的 actingOwner——owner 负责"发布"，审批人只负责"批准"。CEO 签完 → `approved`，总助签完 → `released`。

**步骤 6-9：写入磁盘**（和第八段一模一样的收尾模式）
```python
intake_brief_path = _write_intake_brief(...)       # 重写 brief（含新签名）
case_payload["intake"]["briefPath"] = ...
_append_event(..., "intake-signoff-recorded", ...) # 事件日志
_save_case(case_payload, workspace_root)            # 写 case.json
return reconcile_ipd_case(...)                      # 写后对账
```

> **总结**：签核是幂等的——同角色签两次原地覆盖。CEO 和总助谁先签都行，release 只在总助签核且两人都 approved 时触发。签核后的 intake 三态：`"pending"` / `"approved"` / `"rejected"`。

---

## 第十段：`_reconcile_case_payload`——IPD 中央状态机

### 业务逻辑

`_reconcile_case_payload` 是 IPD 的**中央状态机**。每次 case 被碰过（签核、提交、冻结……），`reconcile_ipd_case` 都会调它来判断"现在该干什么"。整个 case 生命周期靠它推进。返回值 `summary["advanced"]` 标记"这次是否让 case 往前推进了一步"。

### 三大分支

```python
def _reconcile_case_payload(case_payload, *, workspace_root):
    # 分支 A：执行完整性异常 → 自动修复，直接返回
    # 分支 B：冻结 → 标记当前阶段 frozen，返回
    # 分支 C：正常状态机（下面是重点）
```

### 分支 C：正常状态机（第 2473-2526 行）

```python
intake_status = _approval_rollup(case_payload["intake"]["approvals"])
current_stage = _current_stage(case_payload)

if current_stage is None:
    # C1：还没激活任何阶段
else:
    # C2：已有活跃阶段
```

**`_current_stage`（5077-5084 行）**：读 `currentStageKey`，在 stages 数组里找匹配的阶段。初始化为空字符串 → 返回 `None`。

### C1：无活跃阶段（第 2477-2490 行）

intake 签核后第一次对账走这里：

| intake 状态 | 七槽位 | 结果 |
|---|---|---|
| rejected | — | `"blocked"` |
| pending | — | `"awaiting-intake-approvals"` |
| approved | 有空缺 | `"paused-intake-clarification"` |
| approved | ready | **激活第一个阶段！** |

```python
elif not _intake_clarification_ready(case_payload["intake"]):
    case_payload["status"] = "paused-intake-clarification"
else:
    next_stage = _next_pending_stage(case_payload)  # 第一个 pending 阶段
    _activate_stage(case_payload, next_stage["stageKey"], ...)
    advanced = True
```

- `_intake_clarification_ready`（4522-4524）：`clarificationSheet.status` 是不是 `"ready-for-dispatch"` 或 `"not-enforced"`
- `_next_pending_stage`（5093-5094）：`next(stage for stage in stages if stage["status"] == "pending")` ——按顺序取第一个 pending 阶段

### `_activate_stage()`（第 2532-2561 行）

```python
def _activate_stage(case_payload, stage_key, *, workspace_root, activated_at):
    stage["status"] = "in-progress"            # pending → in-progress
    stage["activatedAt"] = activated_at
    stage["approvals"] = _build_approvals(...)  # 重建审批链
    _seed_stage_supporting_artifacts(...)       # 播种种子文件
    work_item_path = _write_stage_work_item(...)
    case_payload["currentStageKey"] = stage_key
    case_payload["status"] = "waiting-stage-output"
```

### C2：已有活跃阶段（第 2491-2526 行，概览）

| 当前阶段状态 | 动作 |
|---|---|
| `"submitted"` | 查审批 → approved 则完成当前、激活下一个 |
| `"rejected"` | case → `"blocked"` |
| `"frozen"` | case → `"paused-frozen"` |
| `"in-progress"` | case → `"waiting-stage-output"` |
| `"completed"` | 激活下一个 pending 阶段 |

### 重点：两层 intake

容易搞混——intake 有两个层面：
- **Case 级**：`record_intake_signoff()` 操作 `case_payload["intake"]["approvals"]`——CEO+总助对**整个 case 立项**签核
- **Stage 级**：stages 数组里 `stageKey == "intake"` 的阶段——总助作为 actingOwner **执行** intake 工作

流程：case 级签核通过 → 状态机激活 stage 级 intake → stage 级 intake 提交/通过 → 状态机激活 discovery。

> **总结**：`_reconcile_case_payload` 三层分支（异常→冻结→正常）。正常分支根据"有没有活跃阶段"分两条路：没活跃就看 intake 签核决定是否激活第一阶段；有活跃就根据阶段状态决定推进/阻塞/等待。

---

## 第十一段：`_activate_stage()`——阶段激活的八个动作

### 业务逻辑

上一段我们看到，状态机在 intake 签核通过且七槽位就绪后，会调用 `_activate_stage(case_payload, next_stage["stageKey"], ...)` 来激活第一个阶段。

`_activate_stage()` 是 IPD 引擎里**阶段切换的微观执行者**。它的职责不是"判断该不该激活"（那是状态机的活），而是"一旦决定激活，把所有东西准备好"。你可以理解为：状态机是调度中心，`_activate_stage()` 是现场施工队——到了现场就按清单干活，不讨论该不该来。

它做了 8 件事，按顺序排列：
1. 把阶段状态从 `"pending"` 翻成 `"in-progress"`
2. 清除阻塞原因
3. 重建审批链（阶段级审批，全手动，无人可自动通过）
4. **播种种子文件**（`_seed_stage_supporting_artifacts`）——这是 Discovery 五件套的源头！
5. **生成工作项 JSON**（`_write_stage_work_item`）——这是阶段执行者的"任务单"
6. 更新 case 的 `currentStageKey` 和 `currentWorkItemPath`
7. 把 case 状态翻成 `"waiting-stage-output"`
8. 记一条 `"stage-activated"` 事件日志

### 代码逻辑（第 2532-2561 行）

```python
def _activate_stage(
    case_payload: dict[str, Any],
    stage_key: str,
    *,
    workspace_root: str | None,
    activated_at: str,
) -> None:
```

**语法点**：`-> None` 表示这个函数不返回任何有意义的值（只做副作用——改 case_payload、写文件）。

#### 第一步：定位阶段对象

```python
    stage = _require_stage(case_payload, stage_key)
```

`_require_stage` 在 stages 数组里按 `stageKey` 查找。找到了就返回那个 stage 字典的**引用**（不是副本），所以接下来对 `stage` 的修改会直接反映到 `case_payload["stages"]` 里。找不到就抛异常——"必须存在"的语义。

#### 第二步：翻状态 + 清阻塞

```python
    stage["status"] = "in-progress"
    stage["activatedAt"] = activated_at
    stage["blockedReason"] = ""
```

三行一起看：pending → in-progress，记录激活时间戳，把可能残留的阻塞原因清空。

#### 第三步：重建审批链

```python
    stage["requiredApprovers"] = _stage_required_approvers(stage["actingOwner"])
    stage["approvals"] = _build_approvals(stage["requiredApprovers"], auto_approved_role=None, now="")
    stage["lastUpdatedAt"] = activated_at
```

`_stage_required_approvers` 根据 `actingOwner` 决定谁需要审批这个阶段。注意 `auto_approved_role=None`——阶段级审批**没有人能自动通过**，这和前面第四段讲的 case 级 intake 审批逻辑一致。

#### 第四步（★核心）：播种种子文件

```python
    _seed_stage_supporting_artifacts(case_payload, stage, workspace_root=workspace_root, written_at=activated_at)
```

这一行是 Discovery 五件套的源头。我们马上展开。

#### 第五步（★核心）：生成工作项

```python
    work_item_path = _write_stage_work_item(case_payload, stage, workspace_root=workspace_root, written_at=activated_at)
    stage["workItemPath"] = work_item_path.as_posix()
```

生成 `work-items/XX-{stageKey}.json`，并把路径写回 stage。下一段会展开。

#### 第六、七步：更新 case 级指针

```python
    case_payload["currentStageKey"] = stage_key
    case_payload["currentWorkItemPath"] = work_item_path.as_posix()
    case_payload["status"] = "waiting-stage-output"
```

把 case 的"当前焦点"指向刚激活的阶段，状态翻成"等待阶段产出"。

#### 第八步：记日志

```python
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
```

### 语法小课：Python 字典引用 vs 副本

```python
stage = _require_stage(case_payload, stage_key)  # stage 是引用
stage["status"] = "in-progress"  # 直接改了 case_payload 里的原始字典
```

Python 里，字典、列表等可变对象在赋值时传递的是**引用**而非副本。所以 `stage["status"] = "in-progress"` 等价于 `case_payload["stages"][0]["status"] = "in-progress"`。这就是为什么 `_activate_stage` 不需要 `return case_payload`。

> **总结**：`_activate_stage()` 的核心价值在于两步——**播种种子文件**和**生成工作项**。前者创建阶段初始目录结构和空模板，给后续 agent 一个可操作的起点；后者把 intake 上下文打包成任务单，告诉阶段执行者"你是谁、你该干什么、你的约束是什么"。这两步合在一起，就是 IPD 从"规划"到"执行"的交接仪式。

---

## 第十二段：`_seed_stage_supporting_artifacts()`——种子文件从哪里来

### 业务逻辑

每个阶段激活时，IPD 都会在该 case 目录下自动创建一组**种子文件**。这不是"把活干了"，而是"把工作台搭好"——就像给你一张空白的实验记录表，告诉你"在这里填结果"。

种子文件分两类：
1. **reference-source-catalog.json**：来源目录（空的，等你填）
2. **Markdown 文档**：从阶段模板的 `standardFlow` 里读出来，可能是 `summaryDocument`、`analysisDocument`、`packageDocuments` 等

这些文件都**只创建不覆盖**——如果文件已经存在（比如之前激活过又重开），就跳过。所以"种子"这个比喻很准确：只在空地播种，不铲已有的苗。

### 代码逻辑（第 2796-2831 行）

```python
def _seed_stage_supporting_artifacts(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
    written_at: str,
) -> None:
```

#### 第一步：读阶段模板的 standardFlow

```python
    standard_flow = _stage_standard_flow(case_payload, stage)
    if not standard_flow:
        return
```

`_stage_standard_flow`（第 2770-2774 行）做了两件事：
1. 从阶段模板（`_stage_template(stage["stageKey"])`）取 `standardFlow` 字段
2. 用 `_materialize_stage_template()` 把模板里的占位符（如 `{caseId}`）替换成实际值

如果这个阶段模板根本没有 `standardFlow`，就直接返回——不是所有阶段都需要种子文件。

#### 第二步：播种 reference-source-catalog.json

```python
    catalog_path = str(standard_flow.get("catalogPath") or "").strip()
    if catalog_path:
        _seed_stage_reference_catalog(case_payload, stage, catalog_path=catalog_path, workspace_root=workspace_root, written_at=written_at)
```

如果 `standardFlow.catalogPath` 有值，就调用 `_seed_stage_reference_catalog` 创建。注意这个路径经过了 `_materialize_stage_template` 的替换，所以 `{caseId}` 已经变成了实际值（如 `IPD-20260610-PLATFORM-001`）。

#### 第三步：播种 Markdown 文档

```python
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
```

`_stage_markdown_documents`（第 2822-2831 行）从 `standardFlow` 里捞出所有需要创建的 Markdown 文档：

```python
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
```

**语法点**：`for key in ("summaryDocument", "analysisDocument")` 用元组做循环——先取 `summaryDocument`，再取 `analysisDocument`。每个取出来如果是 dict 且有非空 path，就加入列表。然后 `packageDocuments` 是一个数组，用 `list.extend()` 风格逐个追加。

所以一个阶段的种子文档 = `summaryDocument`（可选）+ `analysisDocument`（可选）+ `packageDocuments`（0 到 N 个）。

### `_seed_stage_reference_catalog`（第 2834-2858 行）

```python
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
        return                          # ★ 已存在就跳过
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": f"ipd-{stage['stageKey']}-reference-source-catalog",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "generatedAt": written_at,
        "sources": [],                  # ★ 空数组，等你填
        "notes": [
            f"本文件由 {stage['stageKey']} 阶段激活时自动生成。",
            "请在后续研究中持续补齐来源、官方性、锚点位置和用途说明。",
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

**关键细节**：
- `if path.exists(): return`——防御性语义："只在空地播种"
- `sources: []`——空的！这个文件是**模板**，需要 agent 在阶段执行过程中手动填充
- `kind` 是动态生成的：`f"ipd-{stage['stageKey']}-reference-source-catalog"`。对于 discovery 阶段，就是 `"ipd-discovery-reference-source-catalog"`

### 语法小课：`path.parent.mkdir(parents=True, exist_ok=True)`

```python
path.parent.mkdir(parents=True, exist_ok=True)
```

- `path.parent`：取文件路径的父目录。比如 `Path("a/b/c.json").parent` → `Path("a/b")`
- `mkdir(parents=True)`：等价于 `mkdir -p`，自动创建所有中间目录
- `exist_ok=True`：如果目录已存在不报错

合起来就是"确保目录存在，没有就建，有就跳过"。

> **总结**：`_seed_stage_supporting_artifacts` 是阶段激活时的"基建队"——从阶段模板里读 `standardFlow`，按清单创建 `reference-source-catalog.json` 和各 Markdown 种子文档。所有文件都"只建不覆盖"，空地播种、不伤已有产出。这就是为什么你看到的 `reference-source-catalog.json` 里 `sources` 总是空的——它是个**待填模板**，不是已完成的报告。

---

## 第十三段：`_write_stage_work_item()`——阶段执行者的任务单

### 业务逻辑

种子文件建好了，但阶段执行者（比如 discovery 阶段的 CPO+CTO）还需要知道"我要做什么、我有哪些上下文、我的产出要求是什么"。

`_write_stage_work_item()` 就是干这个的——它把 case 层面的全部上下文（intake 信息、角色分配、输入引用、输出要求）打包成一个独立的 JSON 文件，放到 `work-items/` 目录下。你可以把它理解为**阶段的任务派发单**：执行者打开这个文件，就知道自己是谁、目标是什么、有什么约束、要产出什么。

这个文件有两个重要特征：
1. **独立自包含**——它把 intake 的核心字段都复制了一份进去，不需要执行者再回去翻 `case.json`
2. **内含 draft template**——它预嵌了一个 `draftTemplate` 对象，告诉执行者"按这个骨架填内容"。这就是 discovery 阶段里那些 `discovery-summary.md` 等文档的**初始空模板**的来源

### 代码逻辑（第 2564-2626 行）

```python
def _write_stage_work_item(
    case_payload: dict[str, Any],
    stage: dict[str, Any],
    *,
    workspace_root: str | None,
    written_at: str,
) -> Path:
```

返回值是 `Path`——创建的文件路径，要写回 `stage["workItemPath"]`。

#### 第一步：确定文件路径

```python
    case_root = chief_of_staff_ipd_case_root(case_payload["caseId"], workspace_root)
    work_items_root = case_root / "work-items"
    work_items_root.mkdir(parents=True, exist_ok=True)
    path = work_items_root / f"{_stage_index_for_case(case_payload, stage['stageKey']) + 1:02d}-{stage['stageKey']}.json"
```

**关键**：文件名格式是 `{序号}-{stageKey}.json`。序号是阶段在 `stages` 数组里的索引 + 1（因为索引从 0 开始）。

`_stage_index_for_case`（第 5111-5115 行）：
```python
def _stage_index_for_case(case_payload, stage_key):
    return next(
        index for index, stage in enumerate(case_payload.get("stages", []))
        if str(stage.get("stageKey") or "").strip() == normalized_stage_key
    )
```

**语法点**：`next(generator)` 从生成器表达式里取第一个匹配项。如果找不到会抛 `StopIteration`——这是故意的，说明数据不一致。

所以对于 discovery 阶段（十阶段模板里的第 2 个，索引为 1），文件名是 `02-discovery.json`。

#### 第二步：组装 payload（第 2575-2624 行）

```python
    payload = {
        "schemaVersion": IPD_CASE_SCHEMA_VERSION,
        "kind": "ipd-stage-work-item",
        "caseId": case_payload["caseId"],
        "stageKey": stage["stageKey"],
        "phaseKey": stage["phaseKey"],
        "title": f"{case_payload['title']} / {stage['title']}",
        ...
```

`title` 是 case 标题和 stage 标题的拼接。例如：`"做一个统一模型 API 平台 / 市场调研与技术发现"`。

```python
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        "moduleExecutor": stage["moduleExecutor"],
        "gateOwner": stage["gateOwner"],
        "ownerRole": stage["actingOwner"],
        "participantRoles": list(stage.get("participantRoles", [])),
```

四角色（businessOwner / actingOwner / moduleExecutor / gateOwner）原样从阶段模板复制。`ownerRole` 等于 `actingOwner`——这是给执行者的身份标签。

```python
        "status": stage["status"],          # "in-progress"
        "createdAt": written_at,
        "updatedAt": written_at,
        "priority": case_payload["priority"],
        "summary": _stage_summary(case_payload, stage),
```

`_stage_summary` 生成一段中文摘要，例如：
> "CPO 需要基于 CEO / 总助已整理并获签核的 intake briefing，围绕目标"做一个统一模型 API 平台"推进 市场调研与技术发现（discovery），并协同 CTO，并在提交后等待 CEO 签名与 CEOChiefOfStaff 最终验证签发。"

#### 第三步：复制 intake 上下文（第 2593-2611 行）

```python
        "intake": {
            "objective": case_payload["intake"]["objective"],
            "taskDescription": case_payload["intake"]["taskDescription"],
            "caseCategory": case_payload["intake"]["caseCategory"],
            "referenceTheme": case_payload["intake"]["referenceTheme"],
            "constraints": list(case_payload["intake"]["constraints"]),
            "opportunitySignals": list(case_payload["intake"]["opportunitySignals"]),
            ...
            "clarificationSheet": dict(case_payload["intake"]["clarificationSheet"]),
        },
```

这里**不是引用**，是**复制**。`list(...)` 和 `dict(...)` 做了浅拷贝，所以修改 work-item 里的 intake 不会污染 `case.json` 里的原始数据。12 个字段 + clarificationSheet 完整打包。

#### 第四步：角色矩阵 + 输入输出（第 2612-2619 行）

```python
        "roleAssignmentMatrix": _stage_role_assignment_matrix(stage["stageKey"]),
        "requiredApprovers": list(stage["requiredApprovers"]),
        "relatedModules": list(case_payload["relatedModules"]),
        "inputRefs": _input_refs(case_payload),
        "inputRequirements": list(stage.get("inputRequirements", [])),
        "outputRequirements": list(_stage_template(stage["stageKey"])["outputRequirements"]),
        "superDevReferenceStages": list(stage.get("superDevReferenceStages", [])),
        "schemaHint": dict(stage["schemaHint"]),
```

- `roleAssignmentMatrix`：从阶段模板取该阶段的角色分配矩阵
- `inputRefs`：收集前序阶段的产出路径（brieffile + case.json + 已完成阶段的 outputPath）
- `outputRequirements`：从阶段模板读取该阶段的输出要求列表（如 `["技术选型报告", "市场 analysis", "可行性评估"]`）
- `schemaHint`：该阶段的对象类型提示（如 discovery 阶段是 `"discovery-package"`）

#### 第五步（★核心）：内嵌 draft template

```python
        "draftTemplate": _draft_template(case_payload, stage, written_at=written_at),
```

`_draft_template`（第 2721-2755 行）生成了一个嵌入的模板骨架：

```python
def _draft_template(case_payload, stage, *, written_at):
    payload = {
        "kind": "ipd-engine-native-draft",
        "objectType": stage["schemaHint"]["objectType"],
        "phaseKey": stage["phaseKey"],
        "businessOwner": stage["businessOwner"],
        "actingOwner": stage["actingOwner"],
        ...
        "summary": _stage_summary(case_payload, stage),
        "inputRequirements": list(stage.get("inputRequirements", [])),
        "requiredOutput": list(_stage_template(stage_key)["outputRequirements"]),
        "superDevReferenceStages": list(stage.get("superDevReferenceStages", [])),
        "workflowRefs": [{...}],
    }
    # 如果阶段模板有 standardFlow，嵌入
    standard_flow = _stage_standard_flow(case_payload, stage)
    if standard_flow:
        payload["standardFlow"] = standard_flow
    # 如果阶段模板有 templateFields，嵌入（已替换 {caseId}）
    template_fields = _stage_template(stage_key).get("templateFields")
    if template_fields:
        payload["templateFields"] = _materialize_stage_template(template_fields, case_id=case_payload["caseId"])
    # 如果阶段模板有 scorecardSchema，嵌入
    scorecard_schema = _stage_template(stage_key).get("scorecardSchema")
    if scorecard_schema:
        payload["scorecardSchema"] = _materialize_stage_template(scorecard_schema, case_id=case_payload["caseId"])
    return payload
```

这个 `draftTemplate` 就是后续自动化（如 `run_discovery_stage_automation`）用来生成实际阶段产出文档的**源代码级模板**。`standardFlow` 里定义了要创建哪些文件（`summaryDocument`、`analysisDocument`、`packageDocuments` 等），`templateFields` 定义了每个文件里要填哪些字段。

#### 第六步：写入磁盘

```python
    standard_flow = _stage_standard_flow(case_payload, stage)
    if standard_flow:
        payload["standardFlow"] = standard_flow
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
```

注意 `standardFlow` 既嵌在 `draftTemplate` 里，又放在 payload 顶层——顶层是给自动化快速读取的，`draftTemplate` 里是给模板引擎用的。两者指向同一个对象（`_stage_standard_flow` 的返回值），但因为 `json.dumps` 序列化时会展开，所以写入文件后是两份独立数据。

### 语法小课：`f"{n:02d}"` 格式化

```python
f"{_stage_index_for_case(...) + 1:02d}-{stage['stageKey']}.json"
```

- `:02d`：十进制整数，至少 2 位，不足补零
- 索引 1 → `"02"`，索引 9 → `"10"`
- 这是为了文件名自然排序（`01-`、`02-`... 而不是 `1-`、`10-`、`2-`）

> **总结**：`_write_stage_work_item` 生成了一个**自包含的阶段任务派发单**。它把 intake 上下文、角色矩阵、输入引用、输出要求和 draft 模板全部打包进一个 JSON 文件。阶段执行者打开 `work-items/02-discovery.json` 就知道全部上下文。这个文件里最关键的字段是 `draftTemplate`——它包含了 `standardFlow`（要创建哪些文件）和 `templateFields`（每个文件填什么），是后续自动化的源代码。

---

## 第十四段：`_activate_stage` 返回之后——状态机的回程与阶段推进

### 业务逻辑

第十三段讲完了 `_activate_stage` 做了什么。现在要回答一个关键问题：**`_activate_stage` 返回后，case 怎么继续往前走？**

先厘清一个容易混淆的点：`_activate_stage` **不会自动执行阶段工作**。它只是把工作台搭好（种子文件 + 任务单），然后把 case 状态设为 `"waiting-stage-output"`。**真正的阶段执行**（比如 discovery 的市场调研）是后续由人（或自动化脚本）显式调用的。

所以从 ceo-demand 到 discovery 五件套，中间经过的是：

```
intake 签核通过
  → reconcile_ipd_case()
    → 状态机看到 current_stage is None + intake approved + 七槽位 ready
    → _activate_stage("ceo-demand")  ← 激活第一个阶段
    → case status = "waiting-stage-output"
    
ceo-demand 阶段完成（CEO 提交/签核）
  → reconcile_ipd_case()
    → 状态机看到 ceo-demand status = "completed"
    → _activate_stage("discovery")  ← 激活第二个阶段
    → case status = "waiting-stage-output"
    
discovery 阶段已激活
  → run_discovery_stage_automation()  ← 显式调用自动化
    → 生成五件套
```

每一次推进都靠 `reconcile_ipd_case` 驱动——它是 IPD 的心跳。

### 代码逻辑：`_activate_stage` 返回后的收尾

`_activate_stage` 在第 2489 行被调用后，状态机继续执行：

```python
                _activate_stage(case_payload, next_stage["stageKey"], workspace_root=workspace_root, activated_at=now)
                advanced = True          # ← 标记"推进了一步"
    # ... 所有分支结束后 ...
    case_payload["updatedAt"] = now      # 第 2528 行
    return case_payload, _summary_for_case(case_payload, advanced=advanced, workspace_root=workspace_root)
```

只有两行收尾：
1. 刷新 `updatedAt`
2. 返回 `(case_payload, summary)` 元组

然后回到 `reconcile_ipd_case`（第 1657-1661 行）：

```python
def reconcile_ipd_case(case_id, *, workspace_root=None):
    case_payload = _load_case(case_id, workspace_root)          # 读 case.json
    case_payload, summary = _reconcile_case_payload(case_payload, workspace_root=workspace_root)  # 状态机
    _save_case(case_payload, workspace_root)                     # 写回 case.json
    return summary                                               # 返回摘要给调用者
```

**三步走**：读 → 对账（可能激活阶段、可能推进状态）→ 写回。`summary` 里的 `advanced` 字段告诉调用者"这次有没有推动进度"。

### 阶段推进的完整序列

以 project-delivery 十阶段为例，从 ceo-demand 到 discovery 激活：

| 步骤 | 谁调用 | 发生什么 | case status |
|---|---|---|---|
| 1 | `task-intake` | 创建 case，stages 全 pending | `awaiting-intake-approvals` |
| 2 | `reconcile_ipd_case` | 第一次对账：intake 未签核，不动 | `awaiting-intake-approvals` |
| 3 | `intake-approve` (CEO) | CEO 签核 intake | `awaiting-intake-approvals` |
| 4 | `intake-approve` (总助) | 总助签核 → intake approved | `awaiting-intake-approvals` |
| 5 | `reconcile_ipd_case` | 第二次对账：intake approved + 七槽位 ready → **激活 ceo-demand** | `waiting-stage-output` |
| 6 | CEO 提交 ceo-demand | stage status → submitted | — |
| 7 | `reconcile_ipd_case` | 第三次对账：ceo-demand submitted → approved → completed → **激活 discovery** | `waiting-stage-output` |
| 8 | `run_discovery_stage_automation` | 显式调自动化 | （自动化内部处理） |

**关键洞察**：步骤 1-5 我们已经讲完了（第一到十三段）。步骤 6-7 是阶段提交/审批流程，步骤 8 才是 discovery 自动化的入口。

### 为什么自动化不是自动触发的？

你可能会问：状态机在第 5 步激活了 ceo-demand，为什么不顺便把自动化跑了？

因为 IPD 的阶段分两类：
- **需人工判断的阶段**（ceo-demand、intake 执行等）：激活后等人操作
- **可自动化的阶段**（discovery、intelligence 等）：激活后由自动化脚本填充

但即使是可自动化的阶段，`_activate_stage` 也只做"基建"不做"施工"。这是刻意的设计——**激活和执行的解耦**让流程更灵活：可以先激活看看上下文，再决定是否自动执行；也可以手动补充种子文件后再跑自动化。

> **总结**：`_activate_stage` 返回后，状态机只做 `updatedAt` 刷新和返回 summary。`reconcile_ipd_case` 负责"读 → 对账 → 写回"三步。每一次对账都是一次心跳——检查有没有签核变化、阶段有没有提交、该不该激活下一个阶段。Discovery 的自动化不是状态机触发的，而是由 `run_discovery_stage_automation()` 显式调用——它是 IPD 的外挂执行器，不是状态机的一部分。

---

## 第十五段：`run_discovery_stage_automation()`——Discovery 自动化的全部秘密

### 业务逻辑

这是我们整个教学旅程的"大结局"——从 CEO 一句话"做一个统一模型 API 平台"，经过初始化、签核、阶段激活，终于来到 **Discovery 五件套的自动生成**。

`run_discovery_stage_automation()` 是整个 Discovery 自动化的入口函数。它的职责是：

1. **装载 case，校验状态**——当前阶段必须是 discovery，且状态就绪
2. **组装对标来源列表**——从 CEO 在 intake 阶段填的 `competitorReference` 槽位出发，匹配内置种子库，补齐项目边界来源
3. **写入 reference-source-catalog.json**——把来源列表持久化
4. **生成 Discovery 五件套**——五个 Markdown 文档，一次性写完
5. **校验覆盖完整性**——CEO 指定的对标对象必须全部出现在文档中
6. **收尾**——根据是否 `submit`，选择提交 stage 还是仅返回摘要

流程极简但每个子步骤都富含深意。我们一步步来。

---

### 代码逻辑（第 1889-1946 行）

#### 主函数入口

```python
def run_discovery_stage_automation(
    case_id: str,
    *,
    workspace_root: str | None = None,
    submit: bool = False,
) -> dict[str, Any]:
```

**语法小课：`*` 作为分隔符**

```python
def func(a, *, b, c):
```

`*` 之后的所有参数都是**关键字参数**（keyword-only），调用时**必须写名字**：

```python
func("x", b=1, c=2)  # ✅ 正确
func("x", 1, 2)      # ❌ 报错！b 和 c 必须用关键字传
```

这是 Python 3 的特性，用来强制调用者写清楚每个参数的语义。这里 `workspace_root` 和 `submit` 都用了这个模式。

---

#### 第一步：装载与防御

```python
    case_payload = _load_case(case_id, workspace_root)               # line 1895
    _assert_case_not_frozen(case_payload, action="discovery automation")  # line 1896
    stage = _ensure_stage_ready_for_automation(case_payload, "discovery", submit=submit)  # line 1897
```

三行代码，三层防御：

1. `_load_case`——读 `case.json`。我们在第一段讲过，路径是 `<workspace>/ipd-cases/<caseId>/case.json`
2. `_assert_case_not_frozen`——如果 case 被 freeze 了，立即抛异常。Frozen case 是"只读保护区"，不允许任何自动化写入
3. `_ensure_stage_ready_for_automation`——双重校验：当前阶段必须是 discovery，且状态必须是 `in-progress`/`submitted`/`completed` 之一

---

### `_ensure_stage_ready_for_automation()`——自动化前的安检门（第 2012-2024 行）

```python
def _ensure_stage_ready_for_automation(
    case_payload: dict[str, Any],
    stage_key: str,
    *,
    submit: bool,
) -> dict[str, Any]:
    stage = _require_stage(case_payload, stage_key)      # 在 stages 数组里找 discovery
    current_stage_key = str(case_payload.get("currentStageKey") or "").strip()
    if current_stage_key != stage_key:                    # 当前焦点不是 discovery？
        raise ValueError(
            f"current stage is {current_stage_key or 'none'}, not {stage_key}"
        )
    if stage.get("status") not in {"in-progress", "submitted", "completed"}:
        raise ValueError(
            f"stage {stage_key} is not available for automation: {stage.get('status')}"
        )
    return stage
```

**业务含义**：自动化只能在"当前活跃阶段是 discovery 且状态就绪"时运行。如果 discovery 还是 `pending`（还没被状态机激活），或者当前焦段在别的阶段，直接报错。

**注意**：`_require_stage` 我们在第十一段讲过，它从 `case_payload["stages"]` 数组里按 `stageKey` 查找。找不到也报错。

---

#### 第二步：读取阶段模板

```python
    standard_flow = _stage_standard_flow(case_payload, stage)   # line 1898
```

这我们在第十二段详细讲过——从阶段模板的 `standardFlow` 字段取出文档路径清单（`summaryDocument`、`packageDocuments` 等），并用 `_materialize_stage_template` 把 `{caseId}` 替换成实际值。对于 discovery 阶段，`standard_flow` 大致是：

```json
{
  "summaryDocument": {
    "path": "ipd-cases/{caseId}/discovery/discovery-summary.md",
    "title": "..."
  },
  "packageDocuments": [
    { "path": "ipd-cases/{caseId}/discovery/competitor-landscape.md", ... },
    { "path": "ipd-cases/{caseId}/discovery/common-capability-matrix.md", ... },
    { "path": "ipd-cases/{caseId}/discovery/highlight-opportunity-memo.md", ... }
  ],
  "catalogPath": "ipd-cases/{caseId}/discovery/reference-source-catalog.json"
}
```

咦，不是说"五件套"吗？怎么只列出了四个文档？别急——实际上有五份产出：
1. **discovery-summary.md**（functional brief）
2. **competitor-landscape.md**（竞品地图）
3. **common-capability-matrix.md**（共性功能矩阵）
4. **highlight-opportunity-memo.md**（亮点机会备忘录）
5. **reference-source-catalog.json**（来源目录）

其中 `reference-source-catalog.json` 在第三步单独写入，其余四个 Markdown 在第四步一起写入。所以实际上是 **1 个 JSON + 4 个 MD = 五件套**。

---

#### 第三步：组装对标来源列表

```python
    generated_at = _timestamp_now()                            # line 1899
    sources = _build_discovery_sources(case_payload)           # line 1900
```

`sources` 是一个 `list[dict]`，每个元素代表一个对标来源。它的组装逻辑在 `_build_discovery_sources()` 中（第 3147-3189 行），这是我们接下来重点。

---

### `_build_discovery_sources()`——对标来源的"雷达扫描"（第 3147-3189 行）

```python
def _build_discovery_sources(case_payload: dict[str, Any]) -> list[dict[str, Any]]:
    targets = _extract_reference_targets(
        _slot_answer(case_payload, "competitorReference", default="")
    )
    sources: list[dict[str, Any]] = []
```

#### 第一步：拆解 competitorReference

`_slot_answer` 从七槽位里取 `competitorReference` 字段的值。我们在第四段讲过七槽位——CEO 在 intake 时填的竞品参考，可能包含逗号、分号、顿号分隔的多个名称（如 `"LiteLLM, OpenAI, One API"`）。

`_extract_reference_targets()`（第 3320-3327 行）把它拆成列表：

```python
def _extract_reference_targets(value: str) -> list[str]:
    raw_targets = re.split(r"[、，,;；/|]+", str(value or ""))  # 按分隔符拆
    targets: list[str] = []
    for item in raw_targets:
        text = str(item or "").strip()
        if text and text not in targets:          # 去重
            targets.append(text)
    return targets
```

**语法小课：`re.split()`**

```python
import re
re.split(r"[、，,;；/|]+", "LiteLLM, OpenAI、One API")
# → ['LiteLLM', ' OpenAI', 'One API']
```

`[...]+` 表示匹配方括号内任意字符的一次或多次。所以无论用户用逗号、顿号还是分号分隔，都能正确拆分。

---

#### 第二步：匹配内置种子库

```python
    for target in targets:
        seed = _find_discovery_seed(target)
        if seed is None:
            sources.append({ ... "manual-to-confirm" ... })
            continue
        sources.append({ key: value for key, value in seed.items()
                         if key not in {"aliases", ...} })
```

`_find_discovery_seed()`（第 3337-3343 行）：

```python
def _find_discovery_seed(target: str) -> dict[str, Any] | None:
    normalized = _normalize_search_key(target)
    for seed in _DISCOVERY_SOURCE_SEEDS:
        aliases = {_normalize_search_key(alias) for alias in seed.get("aliases", ())}
        if normalized in aliases:
            return seed
    return None
```

`_normalize_search_key()`（第 3330-3334 行）把文本全部转成小写、把连字符和底线替换成空格、压缩多余空格：

```python
def _normalize_search_key(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[-_]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
```

**为什么这么做？** 用户写的 `"LiteLLM"`、`"litellm"`、`"LITE-LLM"` 都指向同一个种子。通过归一化实现模糊匹配。

内置种子库 `_DISCOVERY_SOURCE_SEEDS`（第 950 行开始）目前包含 LiteLLM 等预置竞品，每个种子有：
- `aliases`：归一化后的别名集合（用于匹配）
- `sourceId`、`name`、`productUrl`、`sourceUrl` 等：来源元数据
- `commonCapabilities`：预填的共性功能（矩阵的初始行）
- `highlightFeatures`：预填的亮点功能（memo 的初始素材）
- `differences`：差异点分析

**未命中种子怎么办？** 生成一个 `manual-to-confirm` 占位：

```python
{
    "sourceId": "manual-" + ...,
    "name": target,
    "category": "manual-to-confirm",
    "official": False,
    "captureStatus": "needs-manual-confirmation",
    "intendedUse": "该对标对象未命中内置发现种子，需要补官方入口与手册链接。",
    ...
}
```

这**不是错误**——它是给 CPO/CTO 的标记："这个竞品我没查过，你来补"。

---

#### 第三步：追加项目边界来源

```python
    sources.extend(_build_discovery_project_boundary_sources(case_payload))
```

`_build_discovery_project_boundary_sources()`（第 3192-3235 行）：

```python
def _build_discovery_project_boundary_sources(case_payload):
    intake = case_payload.get("intake", {}) if isinstance(...) else {}
    if str(intake.get("caseCategory") or "").strip() != _CASE_CATEGORY_PROJECT_DELIVERY:
        return []                          # 不是项目交付类 case，不追
    if not str(intake.get("referenceTheme") or "").strip().upper().startswith("PLATFORM"):
        return []                          # 参考主题不是 PLATFORM 开头，不追
```

只有**项目交付**且参考主题以 **PLATFORM** 开头的 case 才触发。然后扫描 intake 的 `objective`、`taskDescription`、`mustHaveScope` 三个字段：

```python
    combined_text = " ".join(part for part in (objective_text, task_text, scope_text) if part)
    if "triavatar" not in combined_text and "tristaciss" not in combined_text:
        return []
```

如果在这些字段里找到了 `triavatar` 或 `tristaciss` 关键词，就自动追加内部模块来源——比如此时追加 `TriAvatar README` 和 `TriStaciss Phase C design` 作为 Discovery 的边界参考。

**业务含义**：CEO 说"做一个统一模型 API 平台"，平台 referenceTheme 是 PLATFORM，且 intake 里提到 TriAvatar（前端入口）和 TriStaciss（后端 ingress），自动执行器就帮你把这两个模块标记为"当前产品边界来源"，提醒 CPO/CTO 在 Discovery 阶段要确认这两块的功能不丢。

---

#### 第四步：兜底

```python
    if not sources:
        sources.append({
            "sourceId": "manual-discovery-target",
            "name": "待补 Discovery 对标对象",
            "captureStatus": "needs-manual-confirmation",
            ...
        })
    return sources
```

如果 CEO 没填竞品、又不是项目交付类，就生成一个占位，提醒"需要手动补"。

---

### `_write_stage_reference_catalog()`——写入来源目录（第 3059-3062 行）

```python
def _write_stage_reference_catalog(
    catalog_ref: str, payload: dict[str, Any], *, workspace_root: str | None
) -> None:
    path = _resolve_workspace_artifact_path(catalog_ref, workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

回到主函数第 1901-1918 行：

```python
    catalog_ref = str(standard_flow.get("catalogPath") or "").strip()
    _write_stage_reference_catalog(
        catalog_ref,
        {
            "schemaVersion": IPD_CASE_SCHEMA_VERSION,
            "kind": "discovery-reference-source-catalog",
            "caseId": case_payload["caseId"],
            "stageKey": "discovery",
            "captureMode": "seeded-auto-generated",    # ← 标记"自动生成"
            "generatedAt": generated_at,
            "notes": [
                "该 catalog 由 discovery 自动执行器根据当前 case 槽位和内置种子自动生成。",
                "请在人工复核后补充真实抓取、离线快照或额外官方来源。",
            ],
            "sources": sources,                        # ← 核心：来源列表
        },
        workspace_root=workspace_root,
    )
```

**关键字段 `captureMode: "seeded-auto-generated"`**——它告诉后续的读者（CPO/CTO/agent）："这个 catalog 是机器根据种子库自动拼的，不是人工逐条核实过的。请复核。"

---

### `_write_discovery_documents()`——Discovery 四份 MD 的生成（第 3065-3104 行）

这是最核心的产出步骤：

```python
def _write_discovery_documents(
    case_payload: dict[str, Any],
    *,
    standard_flow: dict[str, Any],
    sources: list[dict[str, Any]],
    written_at: str,
    workspace_root: str | None,
) -> list[str]:
```

#### 第一步：预处理数据

```python
    capability_rows = _build_discovery_capability_rows(sources)
    highlight_rows = _build_discovery_highlight_rows(sources)
    intelligence_questions = _build_discovery_intelligence_questions(sources)
```

三个辅助函数从 sources 里提取结构化数据：
- `capability_rows`：从每个 source 的 `commonCapabilities` 字段汇总，用于**共性功能矩阵**
- `highlight_rows`：从每个 source 的 `highlightFeatures` 字段汇总，用于**亮点机会备忘录**
- `intelligence_questions`：预生成 intelligence 阶段的探索问题，用于 **functional brief**

#### 第二步：组装四份文档

```python
    document_texts = {
        str(standard_flow["summaryDocument"]["path"]):
            _render_discovery_functional_brief(
                case_payload, sources=sources,
                capability_rows=capability_rows,
                intelligence_questions=intelligence_questions,
                written_at=written_at,
            ),
        str(standard_flow["packageDocuments"][0]["path"]):
            _render_discovery_competitor_landscape(
                case_payload, sources=sources, written_at=written_at,
            ),
        str(standard_flow["packageDocuments"][1]["path"]):
            _render_discovery_common_capability_matrix(
                case_payload, capability_rows=capability_rows, written_at=written_at,
            ),
        str(standard_flow["packageDocuments"][2]["path"]):
            _render_discovery_highlight_opportunity_memo(
                case_payload, highlight_rows=highlight_rows, written_at=written_at,
            ),
    }
```

**文档对应关系**：

| 序号 | 文档路径 | 中文名 | 内容 |
|---|---|---|---|
| 1 | `discovery-summary.md` | 功能概要（Functional Brief） | 目标、竞品清单、共性功能摘要、待探索问题 |
| 2 | `competitor-landscape.md` | 竞品地图 | 每个竞品的定位、优势、差异 |
| 3 | `common-capability-matrix.md` | 共性功能矩阵 | 表格：功能 × 竞品 的覆盖矩阵 |
| 4 | `highlight-opportunity-memo.md` | 亮点机会备忘录 | 各竞品的亮点功能、为什么值得关注、风险 |

#### 第三步：写入磁盘

```python
    for ref, text in document_texts.items():
        path = _resolve_workspace_artifact_path(ref, workspace_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return list(document_texts.keys())
```

四个文档一次性写入，返回路径列表。

**关键细节**：`_write_discovery_documents` 的 `document_texts` 字典的 key 是路径、value 是内容。因为每个文档用独立的 `_render_*()` 函数渲染，所以它们的内容互不依赖——这意味着**四个文档可以并行生成**（当前实现是顺序的，但架构上支持并行）。

---

### `_validate_discovery_seeded_competitor_coverage()`——覆盖完整性校验（第 3238-3285 行）

回到主函数第 1926-1932 行：

```python
    _validate_discovery_seeded_competitor_coverage(
        case_payload,
        catalog_ref=catalog_ref,
        summary_ref=str(standard_flow.get("summaryDocument", {}).get("path") or ""),
        landscape_ref=str(standard_flow.get("packageDocuments", [{}])[0].get("path") or ""),
        workspace_root=workspace_root,
    )
```

这个校验函数做三件事：

1. **从 catalog 里读 source names**：打开刚写入的 `reference-source-catalog.json`，提取所有 `sources[].name`
2. **从 summary 和 landscape 里搜索关键词**：把两个 MD 文件全文归一化后查找
3. **交叉比对**：CEO 填的每个 `competitorReference` 必须同时出现在 catalog、summary 和 landscape 中

```python
    normalized_target = _normalize_search_key(target)
    if normalized_target not in source_names:
        missing_in_catalog.append(target)
    if normalized_target not in normalized_summary:
        missing_in_summary.append(target)
    if normalized_target not in normalized_landscape:
        missing_in_landscape.append(target)
```

**如果有缺失**，抛异常并精确报告"catalog missing: LiteLLM; brief missing: OpenAI"。

**业务含义**：CEO 指定的竞品，一个都不能漏。如果某个竞品在种子库里不存在，`_build_discovery_sources` 会生成 `manual-to-confirm` 占位（catalog 层面不缺失），但 render 函数可能在生成 MD 时漏掉它。这个校验就是"最后的保险丝"——确保 CEO 说过的每个竞品都出现在交付物中。

**如果没有缺失**，`return` 什么都不做（沉默的成功）。

---

### `_finalize_stage_automation()`——收尾（第 2027-2054 行）

回到主函数最后一步：

```python
    generated_refs = [catalog_ref, *document_refs]    # 全部产出文件的路径列表
    details = [
        f"已自动登记 {len(sources)} 个 Discovery 对标来源。",
        "已自动刷新 Discovery 的竞品 landscape、共性功能矩阵、亮点功能 memo 与 functional brief。",
    ]
    return _finalize_stage_automation(
        case_payload, stage,
        generated_refs=generated_refs,
        details=details,
        object_path=str(standard_flow.get("summaryDocument", {}).get("path") or ""),
        submit=submit,
        workspace_root=workspace_root,
    )
```

**语法小课：`*` 解包运算符**

```python
[catalog_ref, *document_refs]
```

`*document_refs` 把列表"展开"为独立元素。假设 `document_refs = ["a.md", "b.md", "c.md", "d.md"]`，结果就是：

```python
["catalog.json", "a.md", "b.md", "c.md", "d.md"]
```

等价于 `[catalog_ref] + document_refs`。

`_finalize_stage_automation()` 内部：

```python
def _finalize_stage_automation(case_payload, stage, *, generated_refs, details,
                                object_path, submit, workspace_root):
    if submit:
        result = submit_stage_output(           # 正式提交 stage
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
```

**分支逻辑**：
- `submit=True`：调用 `submit_stage_output()`（第 1738 行开始），它会把 stage 状态翻成 `submitted`，生成 package hash、记录 owner 签名，case status 变成 `awaiting-stage-approvals`。**这是"正式提交"路径**。
- `submit=False`（默认）：只返回当前 case 摘要，不改变任何状态。**这是"试跑/预览"路径**。

返回体格式：
```json
{
  "submitted": true/false,
  "automationStageKey": "discovery",
  "generatedFiles": [
    "ipd-cases/.../reference-source-catalog.json",
    "ipd-cases/.../discovery-summary.md",
    "ipd-cases/.../competitor-landscape.md",
    "ipd-cases/.../common-capability-matrix.md",
    "ipd-cases/.../highlight-opportunity-memo.md"
  ],
  ... // case summary fields
}
```

---

### Discovery 五件套全景回顾

| # | 文件 | 类型 | 内容 | 核心渲染函数 |
|---|---|---|---|---|
| 1 | `reference-source-catalog.json` | JSON | 对标来源清单（种子命中 + 项目边界 + 人工待补） | `_write_stage_reference_catalog()` |
| 2 | `discovery-summary.md` | MD | 功能概要：目标、竞品清单、共性功能摘要、待探索问题 | `_render_discovery_functional_brief()` |
| 3 | `competitor-landscape.md` | MD | 竞品地图：逐一对比定位、优势、差异 | `_render_discovery_competitor_landscape()` |
| 4 | `common-capability-matrix.md` | MD | 共性功能矩阵：功能 × 竞品表格 | `_render_discovery_common_capability_matrix()` |
| 5 | `highlight-opportunity-memo.md` | MD | 亮点机会备忘录：各竞品亮点、风险、机会 | `_render_discovery_highlight_opportunity_memo()` |

---

### 完整调用链路

```
run_discovery_stage_automation()
  ├── _load_case()                          # 读 case.json
  ├── _assert_case_not_frozen()             # 防冻结
  ├── _ensure_stage_ready_for_automation()  # 安检：当前阶段=discovery 且状态就绪
  │     └── _require_stage()                # 在 stages 数组找 discovery
  ├── _stage_standard_flow()                # 读阶段模板 → 文档路径清单
  │     └── _materialize_stage_template()   # 替换占位符 {caseId}
  ├── _build_discovery_sources()            # 组装对标来源列表
  │     ├── _extract_reference_targets()    # 拆解 competitorReference 槽位
  │     ├── _normalize_search_key()         # 归一化文本
  │     ├── _find_discovery_seed()          # 匹配内置种子库
  │     └── _build_discovery_project_boundary_sources()  # 追加项目边界来源
  ├── _write_stage_reference_catalog()      # 写入 reference-source-catalog.json
  ├── _write_discovery_documents()          # 生成 4 份 MD 文档
  │     ├── _build_discovery_capability_rows()
  │     ├── _build_discovery_highlight_rows()
  │     ├── _build_discovery_intelligence_questions()
  │     ├── _render_discovery_functional_brief()
  │     ├── _render_discovery_competitor_landscape()
  │     ├── _render_discovery_common_capability_matrix()
  │     └── _render_discovery_highlight_opportunity_memo()
  ├── _validate_discovery_seeded_competitor_coverage()  # 覆盖完整性校验
  └── _finalize_stage_automation()          # 收尾：submit 或 仅摘要
        └── submit_stage_output() [if submit]
```

---

### 设计哲学

`run_discovery_stage_automation` 的设计体现了四个原则：

1. **种子驱动**——不是从零写，而是从预置种子库（`_DISCOVERY_SOURCE_SEEDS`）出发，用 CEO 的输入做筛选和补充。种子库里存的是"已知的最佳实践"。
2. **不做最终决策**——自动生成的文档标记为 `seeded-auto-generated`，所有 `manual-to-confirm` 占位提醒人工复核。机器负责"拼装"，人负责"判断"。
3. **覆盖可验证**——`_validate_discovery_seeded_competitor_coverage` 确保 CEO 说的每个竞品都在交付物中，漏了就报错。这是工程交付的闭环。
4. **试跑/提交分离**——`submit=False` 可以先预览，`submit=True` 才正式写入。这在 CLI 里体现为 `--submit` flag。

> **总结**：`run_discovery_stage_automation()` 完成的是从 CEO 需求 → Discovery 五件套的"最后一公里"。它不创造新知识，而是用内置种子库 + CEO 的竞品列表 + 项目边界识别，自动组装出一套结构化的 Discovery 文档。这个自动化的价值在于**标准化**——每个 case 的 Discovery 都以一致的格式产出，CPO/CTO 拿到的是结构化的"待复核素材"而非"从零填写的空白文档"。Discovery 之后就是 Intelligence（代码深读）阶段，留待后续教学。

---

> **教学旅程里程碑**：从第一段到第十五段，我们完整走通了 IPD 的 **CEO Demand → Discovery 五件套** 全链路。你已经理解了 `task-intake` → `initialize_ipd_case` → `intake-approve` → `_activate_stage` → `run_discovery_stage_automation` 的完整代码逻辑。剩下的 Intelligence、Solution、Plan 等阶段，都是这个骨架的延伸和复用。恭喜！

