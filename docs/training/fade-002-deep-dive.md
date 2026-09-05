# FADE-002 发布域深度教程——source_publish_check 与 envelope 合同的正主实例

> 读者：技术研发新人（目标是能接手 `source_publish_check` 的代码与发布域运维）。
> 培训真源顺序：本文只是导读；事实以文中标注的真源文件为准，冲突时回真源，不回教程。
> **版本差注记（2026-09-05）**：本文行号锚基于当时 4344 行版 CLI（现行 4688 行），且不含
> claude-session 渲染面、M-001 全席公共段注入通道与 2026-09-04/05 发布实战三案——现行版
> 深度内容见 [fade-002/04-deep-research.md](fade-002/04-deep-research.md)（四版教程系列），
> 本文保留为 2026-08-29 时点历史档。

## 一、培训判断

你要接的是 TriCompany 里最成熟的一条"确定性发布管线"：FADE-002 发布域。它是 FADE 协议 v2.0.0 里 envelope 报告合同（§2.2）的**声明载体正主**——协议文档里那段 envelope JSON，描述的就是这个 CLI 的真实输出形状。学完本篇，你应该能：

1. 说出发布域三个 scope（`--check` / `--project-docs` / `--publish-agents`）各自管什么、安全门在哪一行代码；
2. 逐字段读懂一份 envelope v1.0 报告，并用守恒不变量验它；
3. 看懂 08-20 首评 90 分到 08-21 复评 93 分两份卷宗的差异，理解 runId 判例为什么值 3 分；
4. 独立跑一次 dry-run、跑校验套件、并知道改了源侧之后该走哪条命令发布。

## 二、学习路径

| 步 | 读什么 | 验证方式 |
| --- | --- | --- |
| 1 | 本篇§三大图 | 能向别人复述"发布域管哪三件事" |
| 2 | `TriCompany/docs/workflow/project-source-document-sync-ade.md`（发布域规范） | 能说出 manifest 合同四要素 |
| 3 | 本篇§四十段表 + `TriCompany/docs/engineering/fade-registry.md` L69-86 | 能把十段逐段指到真实工件 |
| 4 | `TriCompany/runtime/cognition/source_publish_check.py`（4344 行，按下文锚点分段读） | 能找到 ADE_ACTIONS、保护链、渲染管线 |
| 5 | `TriCompany/docs/engineering/fade-protocol-spec.md` §2.2/§2.7/§2.8/§6.1/§6.2 | 能说清 envelope 哪些是协议不变量、哪些是发布域参考实现 |
| 6 | `TriCompany/docs/engineering/fade-papers/FADE-002-*.json` 六份卷宗 | 能对照出 90→93 只动了哪一项 |
| 7 | 本篇§十二接手任务 | 亲手跑 dry-run + 校验套件全绿 |

## 三、先讲大图：发布域管什么

TriCompany 是"源侧真源、发布侧消费"的双仓结构：员工的岗位定义、binding profile、协议文档都在 `TriCompany/`（源侧），而 `.claude/agents/`、`.github/agents/`、项目根文档等运行消费面在 `TriMetaverse/`（发布侧）。源侧改了，发布侧必须跟平——但**不能让 Agent 手工复制文件**（不可审计、易漂移），于是有了这条管线：

```text
源侧发布事件 → manifest/白名单登记 → 小贾规划 + 小乔/小狄联审（语义）
→ source_publish_check（DCE，确定性执行，envelope 报告）
→ Score CLI/Skill 评分 → Close Skill 裁决 → Close CLI 终态审计
```

一个 CLI、三个业务 scope、两个生命周期 scope（close / event-watch），全部序列化成同一份 envelope 合同——这就是"Score/Close 用一个解析器消费所有域"的设计根基（`source_publish_check.py` L199-209 的注释原文讲的正是这件事）。

三个 scope 的分工：

- **`--check`（+`--sync`）**：兼容目录扫描域。扫 `SYNC_SOURCE_DIRS`（L38-42：`source-agents/registries/`、`docs/`、`.github/`），用四路 diff 引擎（hash/git/codegraph/JSON 语义，L2413-2581）找漂移，`--sync` 显式传入才复制（`_execute_sync` L2633-2670）。
- **`--project-docs`（+`--project-docs-execute`）**：manifest 驱动的项目真源文档同步。默认 dry-run，`published-copy` 字节复制、`published-summary` 必须等小贾给候选文档（CLI 永不自行总结）。
- **`--publish-agents`（+`--agent-execute` +`--host`）**：员工/registry 定义的 live entry 发布，多宿主渲染模型（copilot 字节复制面 / claude 渲染面）。

## 四、协议十段在 FADE-002 的逐段落地形态

协议十段定义见 spec §一生命周期图（`fade-protocol-spec.md` L63-77）；002 的段表登记在 `fade-registry.md` L72-79。逐段落地与取证：

**1. 事件触发**——源侧发布事件，CEO/员工发起发布指令（registry L73）。确定性触发面是 `--event-watch` / `--watch`（L2879-2895）：文件指纹 + Git HEAD/refs 轮询，单次扫描或 30 秒循环（`EVENT_WATCH_DEFAULT_INTERVAL` L3625）。文件/Git 事件的**全自动写入增强**挂 automation-backlog（CTO 2026-08-21 裁决，registry L83）。

**2. 登记（运行标识）**——两套载体并存：域级是 manifest 驱动（`.github/manifests/project-source-doc-sync-manifest.json` + live-agent publish manifest，registry L74）；run 级是 envelope `run_id`，显式 `--run-id` 优先、否则时间戳派生 `ade-{scope}-{ts}`（`_make_run_id` L420-432、`_resolve_run_id` L435-444、合法性 `ADE_RUN_ID_PATTERN` L259）。对照 §2.8 登记段四不变量（spec L241）：唯一性由 run_id 单 token 保证；去重性在 event-watch 里由 `state.json` 指纹实现（同指纹 → `deduped` 不触发，L4127-4158）；关联性=同一 run_id 串起 envelope/评分/close 审计；恢复锚=审计文件 `<source-root>/.ade/<run_id>.close-ade.json`（L273-275）。

**3+4. Qualify / Plan Skill**——语义段，人工承载：小贾规划候选，小乔核产品语义，小狄核 revision 与安全门（registry L75）；manifest 顶层 `planOwner`/`closeOwner`/各 entry `reviewers` 就是这段的登记形态（manifest L5-L7、L33-L38）。机械侧的"资格门"在 CLI 内部：manifest 缺失/非法直接产 error item（L1416-1441），`enabled:false` 记 `skipped_disabled`（L1486-1490）。

**5. DCE**——`source_publish_check` 三 scope 本体（registry L76）。默认 dry-run、显式参数才写入：`--sync`、`--agent-execute`、`--project-docs-execute` 三个写开关分别绑死各自的 scope（L3380-3397 校验"execute 参数必须配 scope"）。

**6. Verify**——002 没有独立 Verify 段载体，它的后置校验职能由两件东西承担：校验套件 `source_publish_check_validation.py`（B4 集成收口 13/13 green，文件头 L6 注记）和 envelope 自身的哈希/守恒证据。registry 段表把校验套件记在 Close CLI 行（L78），这是实例层的载体声明，不违反协议（Verify 本就是可选段，spec L245）。

**7. Score CLI**——同 CLI 的 `--score` 模式（L2843-2878，`score_assessment` L2272-2375）：确定性覆盖检查（试卷 item 在 envelope 里找 evidence，找不到 = omission = 0 分）+ 合并 Score Skill 质量分 + 双门槛判定。注意 spec §2.2 L118 的例外句：Score CLI 输出的**不是 envelope，是 §2.6 评分合同**。你后面看到的 `FADE-002-score-*.json` 两卷的字段结构（items 的 `id/label/weight/score/max/evidence_ref/required/omission/quality_score` + `total{score,max,threshold}` + `required_all_passed` + `verdict` + `scored_at`）与 `score_assessment` 返回合同（L2333-2375）逐字段对应。

**8. Score Skill**——联审语义评分，落成 `FADE-002-quality-rereview-2026-08-21.json`（每项一个 0-10 分的 map），经 `--score-quality-scores` 并入评分合同（L2250-2269 支持两种输入形状）。

**9. Close Skill**——联审语义裁决（approve/freeze 记录于 manifest 状态，registry L77），裁决词表四态 `APPROVED|FROZEN|ESCALATED|RETRY`（`ADE_CLOSE_VERDICTS` L262）。

**10. Close CLI**——`--close` 模式（`run_close` L2070-2158）：校验 verdict/run_id/evidence-ref/source-revision 四输入（L1984-2014），失败产 `CLOSE_REJECTED` envelope 不静默；成功写 `<data_dir>/<run_id>.close-ade.json`，同一 run 二次 close 被 `run_already_closed` 拒绝（L2112-2122）——状态转换单次性。

**终态样本**——registry L79 记录了多轮 source→support 发布同步与 project-docs 两 profile 裁决；本文§八给出 08-21 复评窗与 08-28 真源归位两次可核验实跑。

一个要提前打预防针的差异：manifest 的 `adeLifecycle` 仍写着 `closeCli: "pending"`（manifest L18），而 CLI 的 `--close` 早已落地（spec §6.1 L334 也已划销）。这就是 spec §2.8 细则 7(b) 要求周检做"声明载体 vs 实际载体漂移核对"（L263）的活教材——接手时先核对这类声明差，别照单全收。

## 五、三 scope 全解与 --host 宿主参数

### 5.1 --check / --sync（兼容目录扫描域）

纳入范围硬编码在 `SYNC_SOURCE_DIRS`（L38-42），排除规则 `EXCLUDE_GLOBS` 把员工五件套（soul/memory/colleagues/social）和 binding-profiles 永远挡在外面（L47-53）。为什么 manifest 单独用 JSON 语义 diff（`_manifest_semantic_diff` L2584-2612）而不是字节 hash？因为 live-agent manifest 两侧允许注释性差异，按 key 级比较才不会因格式抖动误报。执行写入时保护目标硬检查 `_is_protected_target`（L2617-2630）：live entry、binding profiles、五件套后缀命中即 skip 不写。

### 5.2 --project-docs（manifest 驱动域）

manifest 默认 `.github/manifests/project-source-doc-sync-manifest.json`（L2778-2782），当前 4 个 entry：2 个 `published-summary`（tricompany-central-summary、dynamic-task-tree-protocol-summary）+ 2 个 `published-copy`（08-28 新增的 CLAUDE.md/AGENTS.md 真源归位，见§八）。

- **published-copy**（L1548-1589）：同 hash → `in_sync`；不同 → dry-run 记 `planned_create/planned_update`，execute 才 `shutil.copy2` 字节复制。
- **published-summary**（L1591-1689）：目标头部元信息门 `_summary_metadata_errors`（L1348-1368）强制校验四个字段——`sourceOfTruth` 必须等于 manifest source 路径、`syncMode` 必须是 `published-summary`、`sourceRevision` 必须是 `sha256:<当前源 hash>`、`lastSyncedAt` 非空。revision 过期且无候选 → `requires_candidate`（reason=`planner_candidate_required_for_published_summary`），**CLI 不写、也不生成摘要**——语义摘要是小贾的 Plan 产物，经联审后以 `--project-doc-candidate ID=PATH` 传入，CLI 只做元信息/哈希/路径校验然后复制候选。
- 路径安全：`_resolve_project_doc_path`（L1299-1319）拒绝绝对路径、Windows 盘相对路径（`C:foo`，L460-468）、`..` 越界（resolve 后 `relative_to` 校验）；`_is_protected_target` 把 live entry/binding/五件套即使被误写进 manifest 也拒掉（L1513-1519）。这就是规范里"白名单 ∩ 保护域 = ∅"的 project-docs 侧实现。

### 5.3 --publish-agents（live entry 发布域）与 --host

读 live-agent publish manifest（`MANIFEST_REL_PATH` L65-67），只发布两种状态的 entry：`source-published-live-entry` 和 `current-copilot-host-live`（L82-85）。`--host` 参数取值直接来自 `HOST_RENDER_REGISTRY` 的键（L2748-2757），默认 `copilot`（L190）。运行前先做整轮否决：任何白名单目标（经宿主派生后的**最终写目标**）落在禁区 → 全 run 拒绝、逐条产 `protected_target_rejected` error（L1097-1138）。`--employees` 可按源侧目录 slug 过滤 role-agent（L546-586）。

### 5.4 event-watch 触发面详解（文件/Git 事件自动触发的确定性载体）

这是 FADE-002 补齐项落地的第三块拼图（前两块：`--run-id`、`--close`）。代码本体在
`source_publish_check.py` L3582-4343，头注 L3582-3604 用 20 行把触发链、去重与幂等
语义一次讲清。双模式入口（argparse L2879-2940）：

- **`--event-watch` 单次扫描**：执行一个扫描批次就退出，JSON envelope 打到 stdout——
  这是给 TriLC daemon cron 定期唤起用的（spec §8.6 定时巡检链交接点，L2884-2887 帮助原文）。
- **`--watch` 前台循环**：每 `--interval` 秒（默认 30.0，L3625）跑一次同一扫描，逐批次
  输出（`_event_watch_loop` L4305-4339）。两种模式都与业务 scope/lifecycle 互斥
  （main L3274-3293）；`--watch` 下 `--run-id` 被拒——批次 id 自动派生，不许外部指定。

**指纹构成 = 文件 hash ∪ Git 指纹**。文件侧 `_event_scan_fingerprints`（L3698-3724）
扫监听目录（默认 `source-agents/`、`docs/engineering/`、`.github/manifests/`，
L3610-3614；可 `--watch-dirs` 覆盖）做逐文件 SHA-256，排除规则复用 `_is_excluded`
（五件套/binding-profiles 永不进触发面，L3718）。Git 侧 `EventWatchGitState`（L3652-3670）
分三形态：worktree 看 HEAD sha；**裸仓看 refs 指纹**——push 只改 `refs/heads/*` 文件内容，
HEAD 是 `ref: ...` 符号引用不随 push 变（L3751-3770 注释原文），所以裸仓 push 事件判据是
refs 指纹差（`_event_is_bare_repo` L3727-3731、refs 指纹 L3751-3770）。

**幂等三件套**：① 首次扫描（无 `state.json`）只建基线不触发，`kind=none`——防 daemon
每次启动触发一轮无意义检查（L4087-4090、L4112-4113）；② `state.json` 持久化文件 hash 表
+ Git 指纹（`_event_save_state` L3949-3972），指纹未变 → 单条 `deduped` item 直接返回，
且**不写事件日志防噪音**（L4126 注释、L4127-4158）；③ 文件事件 ∪ Git 事件并集合并成单一批次，
同一次变更不双触发（L4110-4111）。`--no-git` 时旧 Git 指纹不构成变更（L4100-4102）。

**批次流水**：变更集 → scope 派生（`_event_derive_scopes` L3822-3844：两个 manifest 是
关键文件同时派 publish-agents+project-docs，`source-agents/` 派 publish-agents，
`docs/`、`.github/` 派 check，兜底 check）→ 建议 sync 判据=变更数 ≥ `--sync-threshold`
（默认 5，L3623）**或**含关键文件（两份 manifest / `.agent.md` 后缀，L3616-3621、
L3858-3862）→ 实际写入必须 `--auto-sync` 显式传入（L2915-2923、L4163）。

**审计落盘三件**（默认 `<source-root>/.ade/event-watch/`，L3626-3630）：`events.jsonl`
批次日志（`_event_append_log` L3975-3983）、`reports/<run_id>.json` 批次 envelope
（L3986-4000）、`state.json` 指纹基线。envelope 的 `scope_specific` 里带 `report` 与
`event_log` 回指路径（L4252-4259）。

**顶层 status 只表达触发面健康度**——这是最容易被新人误读的一点。`_event_serialize_envelope`
的 docstring（L4027-4031）明说：event-watch 的 status 是"批次是否健康执行"的信号，
业务检查结果（partial/requires_candidate 等）留在 `scope_specific.event.scope_reports`
供消费方解析；action 词表也是专属三值 `EVENT_WATCH_ACTIONS = {triggered, deduped, error}`
（L3636-3640），复用 envelope 合同但不进三业务域词表（`EVENT_WATCH_SCOPE` L3634）。
为什么这样设计：定时巡检每 30 秒跑一次，published-summary 的 `requires_candidate` 是
**常态**不是故障——若把业务 partial 冒泡到顶层 status，巡检会天天误报，cron 消费方
（只看 status 决定告警）就废了。业务归业务、健康归健康，一层信号只回答一个问题。

**与 FADE-006 post-receive hook 的分工边界**：hook 是 push 模型——git 服务端收到 push
秒级派 tick（fade-registry.md L138），服务执行面编排；event-watch 是 pull 模型——30 秒
轮询、只负责"检测→dry-run 检查→建议"，发布域自己的触发的面。spec §6.1（L334）划销口径
要读准：**检测面已落地，挂 automation-backlog 的是"自动写入"增强**——且就算开
`--auto-sync`，project-docs 也永不自动写（`execute=False` 硬编码，L3884-3885、L3920、
L4167-4168 双保险），因为 published-summary 必须等 planner 候选 + 联审，这条保守门
event-watch 不能越。

## 六、envelope v1.0 逐字段——合同正主讲解

spec §2.2 L120 原话："**发布域参考实现（FADE-002 声明载体）**……envelope v1.0（实现于 `source_publish_check` 三 scope）"。也就是说：协议 v2.0.0 把 envelope 从"普适强制"降格为"发布域参考实现"，而这份参考实现的真身就是本 CLI。逐字段过（常量区 L210-279）：

| 字段 | 合同 | 实现锚点 |
| --- | --- | --- |
| `protocol` | 恒为 `"ade-report"` | `ADE_PROTOCOL` L210。**代码级冻结合同**，保留历史命名（ADE 概念已退役，语义即 FADE 报告合同）——改名会破坏所有存量消费方，所以 spec 明文保留 |
| `version` | `"1.0"` | `ADE_VERSION` L211 |
| `scope` | `sync\|project-docs\|publish-agents` | `ADE_SCOPES` L212；`close`/`event-watch` 是 lifecycle/触发面 scope，**不进三业务域**（L249-252 注释、L265、L3634） |
| `run_id` | 显式 `--run-id` 优先，否则时间戳派生 | `_resolve_run_id` L435-444；合法性 `^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$` L259（它同时是 close 审计文件名，必须文件系统安全） |
| `mode` | `dry-run\|execute` | 各 serialize 函数按 `dry_run` 翻译（如 L1250、L1714） |
| `check_time` | ISO8601 | 机器轨 UTC（spec §2.3 L159；人读呈现走 D-04 v4 双轨制） |
| `status` | `pass\|fail\|partial` | project-docs 的三态判定在 `_finalize_project_doc_report` L1371-1390：errors>0→fail、needs_plan>0→partial、否则 pass；publish-agents 只有 pass/fail（L1252） |
| `summary` | **守恒不变量**：`total == len(items)` 且 `total == changed + skipped + errors` | spec L140"validation 强制"。两个精妙换算：publish-agents 把 `derived_*` 计入 skipped 而非 changed（派生一致不是写入，L1233-1243 注释）；project-docs 的 skipped 直接用 `total - changed - errors` 兜底（L1720-1722） |
| `items[]` | **七字段合同基座**：`action/source/target/before_hash/after_hash/scope_key/error` | spec L141"域扩展字段可选，消费者状态裁决只可依赖七字段"。发布域扩展：publish-agents 加 `kind/manifest_status/dropped_tools`（L1259-1274），project-docs 加 `entry_id/sync_mode/candidate/reason`（L1725-1739） |
| `scope_specific` | 域私有字段 | plan_owner/close_owner/counts/tool_drops 等都住这里，不污染共享合同 |

**action 词表契约化**（spec L143，validation 强制"action ∈ 词表 ∧ 域白名单"）：

```python
ADE_ACTIONS: frozenset[str] = frozenset({
    "created", "updated", "planned_create", "planned_update",
    "in_sync", "skipped_identical", "skipped_dry_run", "skipped_disabled",
    "skipped_protected", "requires_candidate", "gap", "closed",
    "derived_identical", "derived_drift", "error",
})                                                    # L218-234

ADE_ACTIONS_PER_SCOPE = {
    "sync":           {"updated", "planned_update", "in_sync",
                       "skipped_protected", "gap", "error"},
    "project-docs":   {"created", "updated", "planned_create", "planned_update",
                       "in_sync", "skipped_disabled", "requires_candidate", "error"},
    "publish-agents": {"created", "updated", "skipped_identical", "skipped_dry_run",
                       "derived_identical", "derived_drift", "error"},
    "close":          {"closed", "error"},            # L236-253
}
```

`close` 复用 envelope 形状但只允许 `closed|error`（`_serialize_close_envelope` L2017-2067，summary 恒为 total=1 的单 item）；`event-watch` 是触发面审计 scope，专属词表 `EVENT_WATCH_ACTIONS = {triggered, deduped, error}`（L3636-3640），批次业务结果住 `scope_specific.event.scope_reports`，顶层 status 只表达**触发面健康度**（L4027-4031 注释原文）。scope 枚举怎么扩？spec L146（CTO-F11）：以词表常量为准，不靠文档枚举。

**组合运行容器与顶层聚合**（`_serialize_combined_container` L1901-1953）：`--check --publish-agents` 这类组合跑会把多个 envelope 收进 `{protocol, version, run_id?, check_time, status, summary, reports:[...]}`。聚合规则三条（L1922-1929）：任一域 errors>0 → 容器 fail（errors 优先）；否则任一 partial → partial；否则 pass。summary 四字段直和——因为每个 envelope 各自守恒，直和后守恒自动保持。容器 `run_id` 只在显式传入时出现（"no synthetic container id"）。退出码：任何 scope errors>0 → rc=1（L3452-3453、L3468-3471、L3545-3547），CI 可感知拒绝路径。

## 七、多宿主渲染模型（spec §6.2 的代码落点）

§6.2（spec L336-343）一句话：**源单份 + 每宿主一条注册 → 未来新宿主 = 注册表加一个条目，发布流程零改动**。落点：

- **HOST_RENDER_REGISTRY**（L152-187）：每宿主一个 `HostRenderSpec`（L122-134）。copilot 是**字节保真复制面**：`target_root=".github/agents/"`、后缀 `.agent.md`、`tool_name_map={}`（源 frontmatter 原样透传，零回归）；claude 是**渲染面**：`target_root=".claude/agents/"`、后缀 `.md`、工具名小写→PascalCase 映射表（L170-183）、`protected_prefix=".claude/agents/"`、默认附加段 `CLAUDE_DERIVED_MARKER`（L139-141，就是你在本仓库 `.claude/agents/*.md` 尾部看到的那句"禁人工编辑"）。
- **渲染规则**（`_render_agent_payload` L818-869）：非 copilot 宿主一律渲染（`_is_render_entry` L704-717）；渲染面先做 CRLF→LF 归一（L848-850，CTO 2026-08-20 方案 A——归一放在 copy 透传分支**之后**，复制面字节保留不受影响）；frontmatter 按 `frontmatter_fields` 顺序重排，tools 逐个查映射：未映射 → **剔除并记 `dropped_tools`**（审计可见非静默）；映射值不在 `CLAUDE_HOST_TOOL_ALLOWLIST`（L146-149，11 个：Read/Glob/Grep/Edit/Write/Bash/WebFetch/WebSearch/NotebookEdit/Task/CodeSearch）→ **error 不落盘**。剔除清单按目标聚合进 `scope_specific.tool_drops`（L1290-1294）。
- **派生一致校验**：渲染面不比"目标==源文件"，而比"目标==render(源+模板)"——同即 `derived_identical`，漂移即 `derived_drift`（`_publish_single_agent` L897-944）。这是"live entry 是派生加载壳、不是第二真源"（D-07 纪律）的机械化表达。
- **保护链三层**：① 整轮白名单∩禁区否决（L1097-1138）；② `_is_agent_publish_target_protected`（L639-693）的**翻转逻辑**——只有宿主 `protected_prefix` 是授权落区，其余一切路径（含 `.github/agents-backup` 这类兄弟变体目录）都是禁区，静态层还先拦绝对路径/根相对/`..` 逃逸形态（L665-671）；③ `_resolve_agent_target_path`（L606-636）resolve 后 `relative_to` 复核，静态层漏网的在这里第二层兜底。

## 八、本周真实运行证据（全部取自仓库文件）

**复评窗（2026-08-21，W34）**——卷宗 `FADE-002-report-rereview-2026-08-21.json` 收录 4 份 envelope：

1. `project-docs` dry-run，`run_id=ade-project-docs-20260820T042509798090`（**时间戳派生 id——首评 7 分态的物证**），status=partial：`tricompany-central-summary` in_sync（`before_hash=8a3ebd5a…c33b`，reason=`source_revision_match`）+ `dynamic-task-tree-protocol-summary` requires_candidate（reason=`planner_candidate_required_for_published_summary`）。
2. `publish-agents` copilot execute，`run_id=fade-leftover-20260821-b1-copilot-converged`（12:28:20Z），18 items：13 条 `derived_identical`（role-agent）+ 5 条 `skipped_identical`（registry-or-governance-agent），`tool_drops={}`。
3. `publish-agents` claude execute，`run_id=fade-leftover-20260821-b1-claude-recheck`（12:26:25Z），18 条全 `derived_identical`；`tool_drops` 有 5 条——chief-product-officer / chief-technology-officer / deployment-engineer / full-stack-developer / test-engineer 各剔除 `["execute"]`。**同一份 manifest、两个宿主、两套 action 词表**：copilot 面 5 个 registry 条目走复制面所以是 `skipped_identical`，claude 面全走渲染面所以是 `derived_identical`——这组对照是理解"复制面 vs 渲染面"最快的样本。同一个人（rd-trainer）两宿主 hash 不同（copilot `ed9eabd1…4ddf`，claude `f8804373…ff87`），因为渲染面多了工具映射和派生标记。
4. evidence-index 证据索引壳（手工归档容器，非 CLI 业务 scope），5 条 in_sync 把 manifest/规范/联审文档/CLI/校验套件五件证据串成索引。

`enhancement_notes` 原文记录核销细节：`--run-id` 在本发布窗**实跑 5 次**（b1-copilot/-claude 两宿主 execute + recheck×2 + converged），envelope run_id 全为显式值；真实写入证据=源侧 commit `820c39d` → TriMetaverse `613256f8`（3 条 live entry 更新），收敛复核 changed=0/18、errors=0。

**本周样本（2026-08-28，W35）——发布域真源归位实跑**。`TriMetaverse/docs/workflow/operating-records/2026-W35/daily-progress.md` L14 记录："发布域扩容：TriMetaverse CLAUDE.md/AGENTS.md 真源归位 TriCompany（published-copy 双条目，跨端一致）"；L39 恢复指针给出 commit 锚：fade-registry v2.1（**TriCompany @2a6af9d**）。manifest 现存两个新 entry（manifest L54-81）：

- `trimetaverse-claude-md-copy`：`TriCompany/docs/project-sources/trimetaverse-claude-md.md` → `TriMetaverse/CLAUDE.md`，注记"字节保真发布；禁直接改项目侧副本"；
- `trimetaverse-agents-md-copy`：→ `TriMetaverse/AGENTS.md`，注记"多宿主渲染化列增强项挂账"。

这就是你在本仓库根看到的那份 CLAUDE.md 的合法修改路径：**改 `TriCompany/docs/project-sources/` 下的真源，走 `--project-docs` 发布**，直接改项目侧副本会被下次发布覆盖且无审计。

**评分数字**（卷宗原文）：首评 `FADE-002-score-2026-08-20.json`，`scored_at=2026-08-20T04:29:25.023875+00:00`，总分 **90.0/100**、threshold 80、verdict PASS、必选项 6/6；复评 `FADE-002-score-rereview-2026-08-21.json`，`scored_at=2026-08-21T12:29:09.498244+00:00`，总分 **93.0**，其余同。

## 九、评分卷宗解读：90 → 93 两卷对照

试卷 `FADE-002-paper.json` 固定：10 项 × 各 10 分，前 6 项 required（trigger-config / run-id-carrier / skill-docs / cli-report / audit-record / terminal-sample），后 4 项可选（dry-run-default / metadata-gate / path-safety / review-gate），及格线双门槛（必选全过 ∧ 总分 ≥80）。两卷逐项只有一处差异：

| item | 首评 | 复评 | 差异原因 |
| --- | --- | --- | --- |
| run-id-carrier | **7** | **10** | 唯一变动项：`--run-id` 显式化实跑核销 |
| 其余 9 项 | 9/9/10/9/8/10/10/9/9 | 同左 | 无回归 |
| 总分 | 90 | 93 | +3 全部来自这一项 |

首评卷 notes 里写着扣分理由（原文）："runId 字段显式化（现为 manifest 状态隐式承载）——不影响 FADE 档判定但扣质量分"。为什么这一项值 3 分？因为 spec §2.8 细则 5（L261）立法："**单一显式标识 > 分散组合**——多段复杂实例推荐显式运行标识"；细则 6（L262）加判例："被评分卷宗/周检报告/跨实例战役引用的 run 必须可被单一显式标识引用"。首评时的 run_id 是时间戳派生（你可以在首评卷证据 envelope 里看到 `ade-project-docs-20260820T042509798090` 这种 id），卷宗引用它只能靠时间戳反查；复评后 run_id 是人写的业务语义 id（`fade-leftover-20260821-b1-claude-recheck`），从 id 就能读出"哪个遗留项、哪天、哪个宿主、第几次复核"。**定位成本的差异就是这 3 分**。

另一个读卷要点：`terminal-sample` 两卷都是 8 分且复评**没有**回修——因为 manifest `adeLifecycle` 仍是 `dce-implemented-lifecycle-pending`、`currentProfile=agent-owned-interactive-manual`（manifest L10-11），Plan/Close Skill 仍是人工态。复评只核销了被真实实跑证实的项，没有为"好 看"抬分——这正是"评分是证据的函数，不是愿望的函数"。

## 十、故障弧线与教训（D 系纪律关联）

**弧线一：runId 隐式承载 → 显式化核销（7→10）。** 根因是历史演进：CLI 先于协议生命周期立法存在，run 身份靠 manifest 状态 + 时间戳拼合。教训与修复路径都进了协议：§2.8 细则 5/6 从这个案例反向立法。复盘方法论值得学：核销不是"改完代码就销账"，而是**等一个真实发布窗**（FADE-LEFTOVER-20260821-001 项 3①），用 5 次实跑的 envelope 作为销账证据——纸面修复不算修复，实测才算（与 spec §2.8 细则 10"接线+实测才算立法完成"同源）。

**弧线二：字节保真复制面的行尾漂移。** 复评卷 enhancement_notes 第 4 条如实记录：byte-preserve 复制面行尾随源侧 worktree 的 autocrlf stash/checkout 翻转漂移了一次，recheck 发现 1 条 churn，内容归一后收敛；管线归一化改进列观察清单。这里有个真实的设计张力：渲染面已经做了 CRLF→LF 归一（L848-850），复制面为了"字节保真"承诺**不能**归一——于是 Windows 全局 autocrlf 的任何翻转都会在复制面表现为一次假漂移。接手后若要改这块，先想清楚：归一化复制面会破坏"published-copy 字节级确定性"的规范承诺（sync-ade 规范 §5.1），正确解法大概率在 git 配置侧或对比侧，而不是复制侧。

**弧线三：声明与实现的漂移。** manifest `adeLifecycle.closeCli=pending` vs CLI `--close` 已落地（§四末尾）。这不是事故，但放任不管就会变成事故——某天有人按 manifest 判断"Close CLI 还没有"而绕过终态门。处理方式就是 spec §2.8 细则 7(b) 的周检漂移核对。

**D 系纪律关联**（`TriCompany/docs/workflow/engineering-disciplines.md`）：

- **D-07 live entry 派生壳纪律**（L52-54）：禁人工直接编辑 `.github/agents/*.agent.md`，改动一律走源侧 + `--publish-agents` 发布；hash 不一致时下次 publish 覆盖 + 审计留痕。整条多宿主渲染管线就是这条纪律的执行机器。
- **D-04 v4 双轨时刻制**（L43-46）：envelope `check_time`、评分卷 `scored_at` 是机器轨，一律 ISO8601 UTC 不改；面向人的发布报告对齐北京时间可括注 UTC。你在卷里看到的 `2026-08-21T12:29:09Z` 与叙述里的"20:29 北京"是同一时刻的两轨。
- **D-01 先写后报**（L14-21）：审计可信度的底线。envelope 的 `before_hash/after_hash` 就是"先写后报"的字段化——先有文件与哈希，后有报告；复评卷里 changed=0 的收敛复核能用 recheck envelope 自证，依赖的正是这套哈希面。

## 十一、与 FADE 协议 v2.0.0 的对照——为什么说 002 是 envelope 正主

**§2.2（结构化报告合同，spec L116-153）**：v2.0.0 把合同拆成两层——上面是**四条普适不变量**（结构化/可守恒校验/errors>0 非零退出码/action 词表契约化，L118），任何 FADE 实例必须满足；下面才是 envelope v1.0 参考实现，括号里点名"FADE-002 声明载体"（L120）。其他域不必复用 envelope，经段-实现映射表声明各自报告合同即可。所以读 002 代码时的分层感应该是：L218-253 的词表常量、各 serialize 函数的守恒换算，是**协议不变量的实现**；而 copilot/claude 的宿主派生、published-summary 的候选语义，是**发布域私有物**。002 还有两处被写进 §2.2 的加固（v1.2.0）：

- **内容归属校验入合同**（spec L147）：角色定义载体不得含模板通用纪律句，白名单 `FORBIDDEN_TEMPLATE_DISCIPLINE_MARKERS` 在 `runtime/cognition/employee_source_kit.py` L55-68 承载（10 句 agent/soul 模板骨架句），`check_content_attribution`（同文件 L175-197）逐句扫描 agent-body 组件与合成文件，命中即 issue。入册条件是"该句在现役角色定义中零出现"——白名单防误伤，纪律句归工程纪律文档，角色定义只含角色职责。
- **跨管线派生校验入合同**（spec L148）：组件（agent-body/soul/contract）→ 合成（`<id>.agent.md`）**单向**传导逐段校验（`check_component_synthetic_sync`，employee_source_kit.py L304 起；组件每个 `## ` 段落必须逐字出现在合成文件，合成独有段不算漂移、反向不检）。registry 类单文件区经 `SYNTHETIC_PATH_OVERRIDES` 映射覆盖（L218-220，现仅 business-strategy 一条，出处 FADE-LEFTOVER-20260821-001 项 1b CTO 裁决：组件目录再放一份合成 = 第二真源）。

**§2.7（节点收口报告）**：002 **豁免**。registry v1.2 注记（L17）裁定：节点收口报告仅适用多节点树实例，001/002/003 是单段脚本/CLI 实例。但别把豁免当无关——单次 envelope 的 items + scope_specific 本身就承担了同等的审计职能（逐条目动作/哈希/原因），只是不需要跨节点断点交接。

**§2.8（段合同与实现绑定）**：这是读 002 最重要的一节。"协议管不变量，实例管载体"（L227）——002 的登记段声明了"`--run-id` 显式标识（发布域，2026-08-21 复评核销）"作为合法载体示例（L253）；validation 边界细则 3（L259）：envelope/评分合同这类产物合同层封闭可校验、validation 强制，载体层开放枚举只做周检漂移核对。002 的 7→10 复评弧线被协议直接引用为细则 5 的实证（L261 括号原文"FADE-002 复评 7→10 实证"）——**实例喂协议、协议反过来保护实例**，这个循环是 FADE 体系能持续长硬的原因。

**§6.1（发布域条目，L325-334）**：注意"尚待补齐"一行的划销记录——文件/Git 事件触发、runId、Close CLI 三个名字上有删除线（已落地：event-watch 单次扫描+循环、`--run-id`、`--close`），只有"自动触发增强"保留为独立工程项。读规范时先看版本行：spec 现行 v2.0.3（L3），而 `project-source-document-sync-ade.md` 还是 V1.1/2026-08-07——它 §7 里的 report 形状是 envelope 落位（spec v1.1.7，2026-08-20）**之前**的旧合同，现行以 spec §2.2 和代码为准。接手任何模块前先核对这类版本差，是本系列培训的第一课。

## 十二、接手任务（第一周清单）

1. 跑全量 dry-run（在 `TriCompany/` 根，命令出自 sync-ade 规范 §6.1）：

   ```powershell
   python -m runtime.cognition.source_publish_check `
     --source-root . `
     --workspace-root .. `
     --project-docs
   ```

   预期：输出 envelope，`status` 为 pass 或 partial（published-summary 条目 revision 过期时 partial 属正常），退出码 0。
2. 跑校验套件：`python -m unittest runtime.cognition.source_publish_check_validation -v`，预期全绿（B4 基线 13/13）。
3. 读代码顺序（按锚点，别通读 4344 行）：L199-279（合同常量区）→ L1393-1692（project-docs 执行）→ L1052-1217（publish-agents 执行+保护否决）→ L639-741（保护链+宿主派生）→ L818-869（渲染）→ L1901-1953（容器聚合）→ L2070-2158（close）→ L4050-4261（event-watch）。
4. 手工验一份 envelope 守恒：取 `FADE-002-report-rereview-2026-08-21.json` 第三个 envelope，核对 `total(18) == changed(0) + skipped(18) + errors(0)`，再数 items 条数=18。
5. 改一处源侧文档（如 `TriCompany/docs/project-sources/trimetaverse-claude-md.md` 的真源），dry-run 观察它变 `planned_update`；**不要 execute**，revert——第一次上手感到此为止，真实写入走联审。

## 十三、校验套件 B4 十三项清单

"13/13 green（2026-07-24）"这个数字在 CLI 文件头（`source_publish_check.py` L6）和
复评卷 evidence-index 第 5 条 reason 里都出现过。它指 B4 集成收口时的测试基线，实体在
`D:/Code/ai/TriCompany/runtime/cognition/source_publish_check_validation.py`：
`ComparisonLogicTests`（L218 起，9 项）+ `CLIIntegrationTests`（L382 起，4 项）= 13。
逐项清单（名称 + 验证什么 + 锚行号，全部实核）：

| # | 级别 | 测试方法 | 验证什么 | 锚行 |
| --- | --- | --- | --- | --- |
| 1 | 单元 | `test_all_in_sync_reports_clean` | TC6：两树全同 → 报告 total=1/in_sync=1 零漂移 | L230-243 |
| 2 | 单元 | `test_out_of_sync_detected_when_content_differs` | TC5：同路径不同内容 → out_of_sync 命中 | L247-255 |
| 3 | 单元 | `test_out_of_sync_multiple_files` | 多文件混合（2 漂 + 1 同）计数正确 | L257-271 |
| 4 | 单元 | `test_binding_profiles_excluded` | TC7：binding-profiles 永不进 sync 范围 | L275-287 |
| 5 | 单元 | `test_employee_five_piece_kit_excluded` | TC7：五件套五后缀全部排除 | L289-305 |
| 6 | 单元 | `test_employee_private_cognition_excluded` | TC7：`.tricompany-cognition/employee/` 排除 | L307-315 |
| 7 | 单元 | `test_gaps_reported_for_source_only_files` | 源单侧文件 → gap（漏发布可见） | L319-326 |
| 8 | 单元 | `test_result_matches_cli_json_contract` | 报告七键齐 + summary 四值为 int | L330-357 |
| 9 | 单元 | `test_source_agents_registries_in_scope` | registries 目录**在**范围内（反向排除确认） | L361-375 |
| 10 | 集成 | `test_help_executable` | TC1：`--help` 退出码 0 有 usage | L406-410 |
| 11 | 集成 | `test_no_args_outputs_valid_json` | TC2：零参数默认跑，stdout 是 envelope 且 `protocol="ade-report"`/`scope="sync"` | L414-433（断言在 L430-431） |
| 12 | 集成 | `test_check_outputs_valid_json` | TC3：`--check` 输出含 envelope 全部十键（protocol/version/scope/run_id/mode/check_time/status/summary/items/scope_specific） | L437-462（断言 L450-462） |
| 13 | 集成 | `test_format_json_outputs_parseable_json` | TC4：`--format json` 可解析 | L466-477 |

读法提示：第 11、12 项是**envelope 合同的钉子**——十键名与 `protocol="ade-report"` 值
被断言写死，谁改了 serialize 形状或合同常量，这两项立刻红。集成类挂在
`skipUnless(_HAS_CLI_MODULE, ...)`（L381）上，模块缺失自动 skip 而不是假绿。
注意"13/13"是 B4 时点基线：文件此后按 scope 扩容追加了 `AgentPublishUnitTests`
（TC-AP1..14 起，L483 起，覆盖白名单过滤/路径逃逸拒绝/dry-run 无写入/execute 真写/
白名单∩禁区整轮否决 TC-AP14 L798-819）与 PD 两族（`ProjectDocumentSyncTests` /
`ProjectDocumentSyncCLITests`，入口见 sync-ade 规范 §9 L190-193）——今天跑套件，
跑到的远不止 13 项，但 13 项是发布域三 scope 报告合同的底线回归面。

**纪律提示：改 `source_publish_check.py` 必跑此套件。** 这个 CLI 的 stdout 是机器合同
（envelope/评分合同），不是给人看的日志——TC2/TC3 断言的就是合同本身。这与 spec §2.8
细则 10"接线 + 实测才算立法完成"同一条道理：改完不跑校验 = 只做了纸面修复。落盘命令：

```powershell
python -m unittest runtime.cognition.source_publish_check_validation -v
```

顺手把 PD 两族细分入口也跑一遍（sync-ade 规范 §9）：

```powershell
python -m unittest runtime.cognition.source_publish_check_validation.ProjectDocumentSyncTests -v
python -m unittest runtime.cognition.source_publish_check_validation.ProjectDocumentSyncCLITests -v
```

## 十四、使用依据

- 段表/评分/复评记录：`D:/Code/ai/TriCompany/docs/engineering/fade-registry.md`（L69-86 FADE-002 条目）
- 协议条文：`D:/Code/ai/TriCompany/docs/engineering/fade-protocol-spec.md`（§2.2 L116-153 / §2.7 L195-223 / §2.8 L225-266 / §6.1 L325-334 / §6.2 L336-343）
- 执行体（全部行号为该文件实际行号）：`D:/Code/ai/TriCompany/runtime/cognition/source_publish_check.py`；`D:/Code/ai/TriCompany/runtime/cognition/employee_source_kit.py`（L55-68 / L175-197 / L218-220）
- 卷宗：`D:/Code/ai/TriCompany/docs/engineering/fade-papers/` 下 FADE-002-paper.json、FADE-002-score-2026-08-20.json、FADE-002-report-rereview-2026-08-21.json、FADE-002-quality-rereview-2026-08-21.json、FADE-002-score-rereview-2026-08-21.json
- 规范与 manifest：`D:/Code/ai/TriCompany/docs/workflow/project-source-document-sync-ade.md`；`D:/Code/ai/TriCompany/.github/manifests/project-source-doc-sync-manifest.json`
- 本周样本：`D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W35/daily-progress.md`（L14/L39，commit 2a6af9d）
- 纪律：`D:/Code/ai/TriCompany/docs/workflow/engineering-disciplines.md`（D-01/D-04/D-07）
