# SP-202A CTO 最小技术任务单

版本：V0.1
日期：2026-06-16
状态：已完成 `SP-202A` 最小 guard 收口；后续 replay 正文追平问题转入 `13-discovery-replay-revision-follow-up-task-sheet.md`

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/agile-improvement/IPD-20260612-WORKFLOW-002/12-sp202a-cto-implementation-task-sheet.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 当前不发布；待 guard 真正收口后再决定
- lastSyncedAt: 2026-06-16

## 1. 文档定位

本文只解决一个问题：`SP-202A` 为什么曾经是 `partial-pass / replayReady=no`，以及 `ChiefTechnologyOfficer` 当时需要做哪些最小代码修改，才能把它推进到可开放 `CPO` 做 Discovery replay 的状态。

本文不是岗位脚本，也不替代 `09-cto-focused-self-test-001.md`。`SP-202A` 的最小 guard 目标已完成；如果当前问题是 replay 后正文未追平 baseline，请转到 [13-discovery-replay-revision-follow-up-task-sheet.md](13-discovery-replay-revision-follow-up-task-sheet.md)。

## 2. 当前事实

### 已成立部分

1. Discovery runtime 已能从 `competitorReference` 提取 targets。
2. Discovery runtime 已能把 targets 组装为 `sources`，并写入：
   - `reference-source-catalog.json`
   - `discovery-reference-functional-brief.md`
   - `discovery-competitor-landscape.md`
3. discovery CLI 的窄范围 unittest 已通过：
   `ChiefOfStaffIpdCaseValidationTest.test_cli_discovery_command_generates_and_submits_package`

### 尚未成立部分

1. 当前 validation 只证明关键文件存在，以及 `landscape` 中出现 `OpenRouter`，没有证明四个 seeded competitors 全覆盖。
2. 当前未见“缺失 seeded competitor 时阻断或标记 `revision-required`”的行为守门。
3. 现有测试面仍保留旧口径痕迹，例如 intelligence 相关测试仍有 `self.assertNotIn("Sub2API", source_names)`。

## 3. 目标收口定义

本轮 `SP-202A` 达到可 replay-ready，至少同时满足以下三条：

1. Discovery 自动化在 20260610 case 上，能把 `LiteLLM`、`sub2api`、`OpenRouter`、`OpenAI API Platform` 全部带入 `catalog / brief / landscape`。
2. 一旦这四项中任一项缺失，validation 能明确失败，而不是静默通过。
3. 对“可扩展更多竞品”的支持不影响前述四项的 carry-forward 覆盖。

## 4. CTO 代码任务

### 4.1 收紧 Discovery validation 断言

目标文件：

- [runtime/cognition/chief_of_staff_ipd_case_validation.py](runtime/cognition/chief_of_staff_ipd_case_validation.py)

最小动作：

1. 把当前 Discovery 自动化测试从“只断言 `OpenRouter` 出现”升级为“对四个 seeded competitors 全量断言”。
2. 断言面至少覆盖：
   - `reference-source-catalog.json`
   - `discovery-reference-functional-brief.md`
   - `discovery-competitor-landscape.md`
3. 若缺任一 seeded competitor，测试必须失败。

### 4.2 增加缺失时的守门行为验证

目标文件：

- [runtime/cognition/chief_of_staff_ipd_case_validation.py](runtime/cognition/chief_of_staff_ipd_case_validation.py)

最小动作：

1. 增加一条负向测试：构造缺少某个 seeded competitor 的 Discovery 结果。
2. 明确预期：提交失败、阻断，或输出被标记为 `revision-required`。
3. 该测试必须证明“不是只有文件存在就算通过”。

### 4.3 清理旧口径测试残留

目标文件：

- [runtime/cognition/chief_of_staff_ipd_case_validation.py](runtime/cognition/chief_of_staff_ipd_case_validation.py)

最小动作：

1. 复核仍带旧口径的断言，例如 `self.assertNotIn("Sub2API", source_names)`。
2. 明确该断言是否只属于旧 intelligence 场景，还是已经与当前平台 case 的新 contract 冲突。
3. 若冲突，必须改成与当前 `SP-202A` 一致的新口径。

### 4.4 必要时补 Discovery runtime 守门点

目标文件：

- [runtime/cognition/ipd_case_engine.py](runtime/cognition/ipd_case_engine.py)

最小动作：

1. 若现有实现只能“生成”而不能“守门”，则补一个最小守门点。
2. 守门点不要求大改架构，但至少要让 validation 能稳定识别“缺失 seeded competitor”并中止通过路径。
3. 不为这轮任务引入超出 `SP-202A` 的新流程语义。

## 5. CTO 自测顺序

代码修改后，`CTO` 应按以下顺序回到自测：

1. 先更新 [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md) 的 `implementationSummary` 与 `touchedFiles`。
2. 再运行 Discovery 相关 focused tests。
3. 若 focused tests 全部通过，再把 `passDecision` 从 `partial-pass` 改成新的真实状态。
4. 只有当四项 seeded competitors 的 full coverage 与缺失阻断都已成立时，才允许把 `replayReadyDecision` 改成 `yes`。

## 6. 最小验证集

本轮代码修改后，至少应重跑：

1. discovery CLI 正向自动化测试
2. seeded competitor full coverage 测试
3. seeded competitor 缺失时的负向阻断测试
4. 若改了 runtime 守门逻辑，对应 Python 诊断 / unittest

## 7. 完成定义

只有同时满足以下条件，才可视为 `SP-202A` 的 CTO 技术改动完成：

1. 四个 seeded competitors 在 Discovery 的 `catalog / brief / landscape` 上都有自动化验证。
2. 缺失任一 seeded competitor 时，自动化验证会失败或明确进入 `revision-required / blocked`。
3. `09-cto-focused-self-test-001.md` 已被 `CTO` 更新为新的真实结论。
4. `CEOChiefOfStaff` 可以据此重新评估是否允许 `CPO` 开始 replay。

## 8. Guardrails

1. 本任务单不授权总助代替 CTO 修改 runtime / validation 代码。
2. 本任务单不要求当前就开放 CPO replay。
3. 本任务单不把局部 test pass 写成 20260610 case 已满足发布前提。

## 9. Evidence Surface

- [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md)
- [11-discovery-replay-role-script.md](11-discovery-replay-role-script.md)
- [runtime/cognition/ipd_case_engine.py](runtime/cognition/ipd_case_engine.py)
- [runtime/cognition/chief_of_staff_ipd_case_validation.py](runtime/cognition/chief_of_staff_ipd_case_validation.py)
