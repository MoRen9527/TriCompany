# Discovery Replay Revision Follow-Up CTO 任务单

版本：V0.1
日期：2026-06-16
状态：等待 `ChiefTechnologyOfficer` 落实 replay 后修复

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/agile-improvement/IPD-20260612-WORKFLOW-002/13-discovery-replay-revision-follow-up-task-sheet.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 当前不发布；待 replay revision 收口后再决定
- lastSyncedAt: 2026-06-16

## 1. 文档定位

本文只解决一个问题：为什么 `SP-202A` 已经让 Discovery replay 通过 seeded competitor carry-forward guard，但首轮真实 replay 仍被判定为 `revision-required`，以及 `ChiefTechnologyOfficer` 现在需要做哪些最小修复，才能把 replay 从“名单没丢”推进到“正文不低于 baseline”。

本文不替代 [10-discovery-replay-result-001.md](10-discovery-replay-result-001.md)，也不回滚 [12-sp202a-cto-implementation-task-sheet.md](12-sp202a-cto-implementation-task-sheet.md) 的已完成结论。它只承接 replay 后暴露出的正文追平缺口。

## 2. 当前事实

### 已成立部分

1. `SP-202A` 已完成最小 guard 收口，Discovery replay 不会再让 seeded competitors 从 `catalog / brief / landscape` 静默消失。
2. 首轮非破坏性 replay 已真实执行，并已保留 baseline archive：
   - `TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001-replay-baseline-archive-20260616`
3. replay 结果中的四个 seeded competitors 仍然全部可定位：
   - `LiteLLM`
   - `sub2api`
   - `OpenRouter`
   - `OpenAI API Platform`

### 当前真实缺口

1. `LiteLLM` 与 `sub2api` 在 replay 中退化为 `manual-to-confirm`，未保留 baseline 中的官方来源、README 链接、能力重点和 intendedUse。
2. baseline 中用于锁定当前项目边界的 `TriAvatar` 与 `Tristaciss` 内部输入没有被 replay 保留。
3. 当前 replay 自动生成链证明了“名单全覆盖”，但没有证明“正文质量不低于 baseline”。

## 3. 根因假设

当前最可证伪的局部根因有两条：

1. Discovery 的 `_DISCOVERY_SOURCE_SEEDS` 没有把 `litellm` 与 `sub2api` 作为现役可直接命中的 seeded competitor 别名；当前相关定义主要存在于 intelligence seeds，因此 `_find_discovery_seed()` 在 replay 中回退成 `manual-litellm` 与 `manual-sub2api`。
2. Discovery 自动生成链当前主要从 `competitorReference` 重建外部对标输入，没有为 20260610 这类 project-delivery platform case 保留 baseline 中已验证过的 `TriAvatar / Tristaciss` 内部边界输入。

这两条假设都已经被首轮 replay 结果支持；下一步修复的目标不是扩大搜索，而是直接围绕这两个控制点补最小实现与回归验证。

## 4. CTO 代码任务

### 4.1 修正 Discovery seed 命中，让 `LiteLLM / sub2api` 不再退化为 manual

目标文件：

- [runtime/cognition/ipd_case_engine.py](runtime/cognition/ipd_case_engine.py)

最小动作：

1. 让 Discovery 对 `LiteLLM` 与 `sub2api` 的命中不再依赖人工补录。
2. 至少保证 replay 生成的 `reference-source-catalog.json` 中：
   - 不再出现 `manual-litellm`
   - 不再出现 `manual-sub2api`
3. replay 生成的 `catalog / brief / landscape` 中，`LiteLLM / sub2api` 必须恢复到不低于 baseline 的最小正文质量：
   - 有可用 `productUrl` / `sourceUrl`
   - 有非占位的 `intendedUse`
   - 有非占位的 `focusAreas` 或能力描述

### 4.2 为 20260610 平台 case 保住必要的内部边界输入

目标文件：

- [runtime/cognition/ipd_case_engine.py](runtime/cognition/ipd_case_engine.py)

最小动作：

1. 明确 `TriAvatar` 与 `Tristaciss` 这类项目边界输入在 Discovery 自动化中的保留策略。
2. 不要求把所有 baseline 自定义内容都硬编码回 runtime，但至少要为当前 20260610 platform case 建立稳定输入面，避免 replay 后静默丢失：
   - `TriAvatar` 作为现役前端入口
   - `Tristaciss` 作为后端 ingress / provider routing 主线
3. 如果不直接保留为 Discovery source entries，也必须给出同等稳定的自动输出位置，而不是让这些输入只存在于 archive baseline。

### 4.3 增加“正文不低于 baseline”的回归测试

目标文件：

- [runtime/cognition/chief_of_staff_ipd_case_validation.py](runtime/cognition/chief_of_staff_ipd_case_validation.py)

最小动作：

1. 补一条 replay-focused 正向测试，至少断言：
   - `LiteLLM` 与 `sub2api` 不再落成 `manual-to-confirm`
   - `catalog` 中二者具备真实来源链接
   - `brief / landscape` 中二者不再是“待补官方来源、待补功能边界”口径
2. 若采用当前 20260610 平台 case 作为 fixtures，还应断言 replay 输出仍能体现 `TriAvatar / Tristaciss` 的边界输入。
3. 不要求做全文 diff 一致，但必须证明 replay 正文质量没有退回到占位级输出。

### 4.4 用第二轮非破坏性 replay 重新验收

目标文件：

- [10-discovery-replay-result-001.md](10-discovery-replay-result-001.md)
- [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md)

最小动作：

1. 完成代码修复后，先更新 CTO 自测记录，新增本轮 touched files、focused tests 与真实结论。
2. 再基于同一 intake 做第二轮非破坏性 replay。
3. 新一轮 replay 目标不是再次证明“名单还在”，而是证明：
   - `LiteLLM / sub2api` 正文已不低于 baseline
   - `TriAvatar / Tristaciss` 边界输入已被自动输出保留

## 5. CTO 自测顺序

1. 先在 [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md) 追加本轮实现范围与 touched files。
2. 再运行 replay-focused tests，而不是只重跑 `SP-202A` 的 carry-forward tests。
3. 若 replay-focused tests 通过，再进入第二轮非破坏性 replay。
4. 只有当 replay 输出不再回退到 `manual-to-confirm / 待补` 口径时，才允许申请总助重新验收。

## 6. 最小验证集

本轮代码修改后，至少应重跑：

1. Discovery replay 正向测试：验证 `LiteLLM / sub2api` 恢复真实来源与能力描述
2. Discovery replay 边界输入测试：验证 `TriAvatar / Tristaciss` 不再静默丢失
3. 现有 `SP-202A` focused tests：确保 seeded competitor guard 未被修复动作破坏
4. 第二轮非破坏性 replay 的结果核查

## 7. 完成定义

只有同时满足以下条件，才可视为本轮 replay follow-up 修复完成：

1. replay 输出中 `LiteLLM / sub2api` 不再退化为 `manual-to-confirm`。
2. replay 输出对 `LiteLLM / sub2api` 的正文质量不低于当前 archived baseline 的最小信息面。
3. replay 输出能稳定体现 `TriAvatar / Tristaciss` 的项目边界输入，或有等效自动输出位承接它们。
4. 第二轮 replay 结果可由 `CEOChiefOfStaff` 从 `revision-required` 重新评估为新的真实状态。

## 8. Guardrails

1. 本任务单不要求回滚 `SP-202A` 已完成的 seeded competitor guard。
2. 本任务单不允许用手工补文档替代 Discovery 自动化修复。
3. 本任务单不把“正文追平 baseline”写成“20260610 case 已可进入 Intelligence”。

## 9. Evidence Surface

- [10-discovery-replay-result-001.md](10-discovery-replay-result-001.md)
- [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md)
- [12-sp202a-cto-implementation-task-sheet.md](12-sp202a-cto-implementation-task-sheet.md)
- [runtime/cognition/ipd_case_engine.py](runtime/cognition/ipd_case_engine.py)
- [runtime/cognition/chief_of_staff_ipd_case_validation.py](runtime/cognition/chief_of_staff_ipd_case_validation.py)
