<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-002/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-002 代码版——source_publish_check 研发实现地图

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-002/03-code-map.md
- syncMode: source-only
- lastSyncedAt: 2026-09-05

读者：要接手 `source_publish_check` 的工程师。
纪律声明：本文全部行号锚为 **2026-09-05 对 4688 行现行版实读**（`TriCompany/runtime/cognition/source_publish_check.py`，下称 CLI；校验套件下称 validation）。代码演进后行号会漂，**锚点语义优先于行号**——接手时先 `git log --oneline <file>` 看有无结构性变更，再按符号名重定位。
前置：已读 [小白版](01-beginner-guide.md) 与 [产品版](02-product-guide.md)。

---

## 一、培训判断与学习路径

学完本篇你应能：①不看文档说出任一参数属于哪个 scope、写开关是哪个；②逐字段读懂 envelope 并手验守恒不变量；③指出任一保护链条的代码位置与触发条件；④跑通校验套件并知道改动后必须跑哪一族。

| 步 | 做什么 | 验证 |
| --- | --- | --- |
| 1 | 读§二文件地图，建立 4688 行的心理分区 | 能说出六区的行号范围 |
| 2 | 读§三命令族，对照 `build_parser`（L3033） | 任指一参数能说出 scope 归属 |
| 3 | 读§四合同常量区（L256-336） | 手验一份 envelope 的守恒不变量 |
| 4 | 读§五§六执行流三主函数 | 能画出 project-docs 双分支流程图 |
| 5 | 跑§十一接手任务 1-3 | 套件全绿 + dry-run 输出可解读 |

## 二、文件地图（4688 行六区）

| 区 | 行段（约） | 内容 |
| --- | --- | --- |
| 常量区·同步域 | L38-103 | 扫描范围/排除规则/保护清单/五件套后缀 |
| 常量区·宿主渲染 | L105-253 | HostRenderSpec/三宿主注册表/session-body 键/M-001 注入常量 |
| 常量区·协议合同 | L256-336 | envelope 协议/词表/run-id/终态/评分阈值 |
| 数据类与工具函数 | L344-1035 | SyncItem/AgentPublishItem/ProjectDocSyncItem 三报告族 + run-id/路径/片段加载工具 |
| 执行流 | L1037-2760 | 渲染→发布→三业务 scope→容器→close→score |
| argparse 与 main | L3033-3924 | 参数族→scope 互斥→五路分发→退出码聚合 |

## 三、命令族全表（build_parser，L3033-3286）

**基座**：`--source-root`（默认 `.`，TriCompany 仓根）/ `--support-root`（默认 `../TriMetaverse`）/ `--format json`（唯一取值）/ `--scope`（stderr 打印检测范围报告，审计用）。

| 组 | 参数 | 语义锚 |
| --- | --- | --- |
| 目录同步域 | `--check` / `--sync` | sync 必须配 check（L3894-3899 反向校验） |
| 项目真源域 | `--project-docs` / `--project-docs-execute` / `--project-docs-manifest` / `--workspace-root` / `--project-doc-ids` / `--project-doc-candidate ID=PATH` | candidate 可重复 append（L3138-3144）；格式错 L3770-3784 拒 |
| 员工发布域 | `--publish-agents` / `--agent-execute` / `--host {copilot,claude,claude-session}` / `--employees` | host 取值=注册表键（L3092）；employees 只滤 role-agent |
| 运行标识 | `--run-id` | 显式优先于时间戳派生；合法性 `ADE_RUN_ID_PATTERN`（L316）；`--watch` 下被拒（L3632-3638） |
| 生命周期 | `--close` / `--verdict` / `--evidence-ref` / `--source-revision` / `--ade-data-dir` | close 与业务 scope/score 互斥（L3639-3650） |
| 评分 | `--score` / `--score-paper` / `--score-report` / `--score-quality-scores` / `--score-threshold` | 输出评分合同非 envelope |
| 触发面 | `--event-watch` / `--watch` / `--interval` / `--watch-dirs` / `--no-git` / `--auto-sync` / `--sync-threshold` / `--audit-dir` / `--state-file` | 与一切业务/lifecycle 互斥（L3620-3631） |

互斥矩阵是手写的（L3615-3650）：五组 if 每组 stderr 报错+rc=1。**没有** argparse `add_mutually_exclusive_group`——改动互斥规则时五处都要看，这是第一个接手陷阱。

## 四、合同常量区（L256-336）——先读这里再读执行流

- `ADE_PROTOCOL="ade-report"`（L267）：**代码级冻结合同**。ADE 概念已退役但字段值不改——存量消费方都按它解析（spec §2.2 明文保留历史命名）。
- `ADE_SCOPES`（L269）：三业务域。`close`/`event-watch` 复用 envelope 形状但**不进**此表（L306-309、L322 注释）。
- `ADE_ACTIONS`（L275-291）+ `ADE_ACTIONS_PER_SCOPE`（L293-310）：action 词表契约化，每 action 带一行语义注释（dry-run 意图/派生一致/触发面专属三值都在这）。
- `ADE_RUN_ID_PATTERN`（L316）：run_id 同时是 close 审计文件名，必须文件系统安全。
- `ADE_CLOSE_VERDICTS`（L319）/`ADE_CLOSE_STATE_*`（L327-328）：CLOSED 唯一终态写；一切校验失败=CLOSE_REJECTED 且非零 rc，**永不静默**。
- `ADE_SCORE_DEFAULT_THRESHOLD=80.0`（L336）：阈值回退链=显式参数→试卷声明→80。

**守恒不变量**（协议 §2.2）：`summary.total == len(items)` 且 `total == changed + skipped + errors`。validation 的 `EnvelopeContractTests`（L1510 起）强制。手验方法见§十一任务 2。

## 五、三业务 scope 执行流

### 5.1 run_project_doc_sync（L1735-2034）——manifest 驱动双分支

流程：resolve manifest→逐 entry→`_resolve_project_doc_path`（L1641-1661：拒绝对路径/盘符相对/`..` 越界）→`_is_protected_target` 命中即 `error:protected_target`（L1855-1861）→按 `sync_mode` 分支：

- **published-copy**（L1890-1931）：源/目标 SHA-256 相等→`in_sync`；不等→dry-run 记 `planned_update/planned_create`（after_hash=源 hash），execute 才 `shutil.copy2` 字节复制→`updated/created`。
- **published-summary**（L1933-2031）：先验目标头部四字段元信息门 `_summary_metadata_errors`（L1690-1710：sourceOfTruth 须等于 manifest source、syncMode 须为 published-summary、sourceRevision 须 `sha256:<当前源hash>`、lastSyncedAt 非空）→门过即 `in_sync`（reason=source_revision_match）；门不过则**必须**有候选（`requires_candidate`，L1947-1956）——候选经同样的元信息门+存在性校验后才允许复制（L1958-2031）。**CLI 从不生成摘要内容**，这是 docstring 原文级承诺（L1745-1747）。
- 状态聚合 `_finalize_project_doc_report`（L1713-1732）：errors>0→fail；needs_plan>0→partial；否则 pass。

### 5.2 run_agent_publish（L1351-1559）——四步流水

1. **整轮否决**（L1396-1437）：`_derive_allowed_agent_targets`→`_derive_host_target` 派生**最终写目标**→任一命中 `_is_agent_publish_target_protected` 即整 run 拒绝（`protected_target_rejected`），派生失败同罪。"被污染的 manifest 一次都不许写"——不是逐条跳过。
2. **条目过滤**（L1439-1455）：`--employees` 滤 role-agent；claude-session 面再滤——无 `sessionBody` 键的条目**零行为**（不产 item 不计数，L1440-1446）；随后 M-001 公共段 run 级单次抽取（L1447-1453，失败 stderr 警告不阻塞）。
3. **逐条目**：M0d 预检 `_source_files_preflight`（L1323-1348，sourceFiles 六键齐备+`TriCompany/source-agents/` 前缀+存在性）→源解析→宿主目标派生→**写根解析**（L1503-1514，见§七）→`_publish_single_agent`。
4. **结果聚合**（L1540-1557）：report target 统一改写为宿主派生后的最终写目标（消费方读真实写面）。

`_publish_single_agent`（L1095-1240 附近）：渲染面算 render(源+模板) 的 hash 与目标比对（同=`derived_identical`，异=`derived_drift`），复制面直接比文件 hash（同=`skipped_identical`）——同一份 live 文件在两种面下走不同 action 词表。写入走 `write_bytes`（渲染面）或 `copy2`（复制面），前后 hash 进 item。

### 5.3 run_check / _execute_sync（L3289 起）

四路 diff（doc 哈希/源码 git diff+哈希回退/manifest JSON 语义 diff/CodeGraph 结构），策略表在 main 的 `--scope` 报告里可见（L3874-3881）。`--sync` 执行后**复跑一次 check** 取 after 态（L3841-3848），before/after 双快照进 change_summary——"先写后报"的字段化。

## 六、claude-session 渲染线（2026-09 新增，旧教程未载）

- **宿主注册**：`HOST_RENDER_REGISTRY["claude-session"]`（L214-225）——`target_root=".claude/hub/"`、后缀 `.session.md`、无 frontmatter（L219）、无工具映射、保护前缀=`.claude/hub/`、尾附 `CLAUDE_SESSION_DERIVED_MARKER`（L160-162）。
- **片段加载**：`_resolve_session_body_path`（L671）/`_load_session_body_payload`（L690-713）——未声明/文件缺/读失败三类显式错误码，**不静默**（测试 L3484/L3504 钉死）。
- **组合公式** `_compose_session_payload`（L770-788）：

  ```text
  渲染正文 = 合成件 body 全量直入 − stripSections 剥离（零剥离起步，L720-736）
           + M-001 全席公共段（可选，正交插入）
           + "## 会话面补充（session-body）" 分隔段 + 席专属片段尾追（L717）
  ```

- **M-001 公共段通道**（L242-253 常量 + `_extract_m001_public_section` L739-767）：**运行时读取**纪律册正身（`M001_SOURCE_REL` L247），按段头正则（L249）抽段，节头统一换"真源投影"头（L251），尾注常量缀段尾（L253）。**正身段缺位=跳过注入+stderr 警告，不阻塞渲染**（L754-756）——这是"幻影真源案"后立法的两步解耦（见[深度研究版](04-deep-research.md)案 2）。你若是在岗员工席，本会话 system prompt 里的"状态条机械合同"段就是这条通道的产物。
- **调用点**：`_publish_single_agent` L1133-1156——片段错误→显式 error item 不落盘；组合后交 `_render_agent_payload` 走无 frontmatter 路径。

## 七、保护链三层（含写根修复现行版）

1. **静态翻转门** `_is_agent_publish_target_protected`（L831-885）：逃逸形态（绝对/根相对/`..`）恒保护→五件套后缀恒保护→binding-profiles 恒保护→**只有宿主 `protected_prefix` 是授权落区，其余一切路径全保护**（L877-885 翻转逻辑注释：防 `.github/agents-backup` 这类兄弟变体目录）。
2. **写根解析** `_resolve_agent_target_path`（L791-828）：**b 案 manifest 前缀感知**——target 带 `TriMetaverse/` 前缀→live 根=调用方传入的 `live_root`（`source_root.parent / "TriMetaverse"`，L1510-1514）；无前缀→support_root。resolve 后 `relative_to` 复核防越界。此函数是写根 bug（3200b89）的修复落点，docstring 带裁示锚（L796-800）。
3. **project-docs 侧同族门** `_resolve_project_doc_path`（L1641-1661）+ `protected_target` 检查（L1855-1861）。

为什么这三层都要存在：第 1 层拦"清单写了禁区"，第 2 层拦"合法清单被解析到仓外"，第 3 层是另一 scope 的同构防线——纵深防御，单层失守不破功。

## 八、生命周期：Close CLI 与 Score CLI

- **run_close**（L2412-2500）：四输入校验（`_validate_close_inputs` L2326，evidence 须可解析为存在文件或 http(s)/file URL，L2310）→失败返回 CLOSE_REJECTED envelope；**同一 run 二次 close 被 `run_already_closed` 拒**（L2453-2464）——状态转换单次性；成功写 `<data_dir>/<run_id>.close-ade.json` 五字段审计记录（L2468-2478）。
- **score**（`_iter_report_envelopes` L2507 归一 bare/container 两形态→`_find_item_evidence` L2524 在 envelope 里找试卷 evidence_ref→`score_assessment` L2614 合并覆盖分与语义分→双门槛判定）。Score CLI 输出**评分合同**（item/score/max/evidence_ref/omission+total+required_all_passed+verdict），不是 envelope——协议 §2.2 的明文例外。

## 九、event-watch 触发面

参数见§三触发面组；main 分发 L3652-3660。核心语义：指纹=文件 SHA-256 ∪ Git HEAD/refs（裸仓看 refs——push 不改 HEAD 符号引用，注释在 `EventWatchGitState` 附近）；首扫建基线不触发（防 daemon 启动即误报）；同指纹=单条 `deduped` 且**不写事件日志**（防噪音）；顶层 status 只表达触发面健康度，业务结果下沉 `scope_specific`（否则巡检把"等候选"常态天天报成故障）。`--auto-sync` 是唯一显式写入口，且 project-docs 永不自动写（测试 `test_project_docs_never_executes_with_auto_sync` 钉死）。

## 十、退出码契约（CI 可感知的拒绝路径）

| 位置 | 语义 |
| --- | --- |
| L3658 | event-watch：批次 fail→1 |
| L3675 | close：非 CLOSED→1（含 CLOSE_REJECTED） |
| L3713 | score：verdict≠PASS→1 |
| L3797-3798 | project-docs：status=fail→1 |
| L3815-3816 | publish-agents：errors>0→1（含整轮否决） |
| L3891-3892 | sync execute 有 error→1 |
| L3924 | 业务 scope 聚合返回 |

组合运行（如 `--check --publish-agents`）输出容器 `{...,reports:[envelope...]}`（`_serialize_combined_container` L2243）：聚合规则=任一域 errors>0→fail＞任一 partial→partial＞pass；summary 四字段直和（各自守恒⇒直和守恒）；容器 `run_id` 仅显式传入时出现。

## 十一、接手任务清单（第一周）

1. 跑校验套件（TriCompany 根）：`python -m unittest runtime.cognition.source_publish_check_validation`——当前基线 **180 项全绿（2026-09-05 实测 46.8s）**。改动本 CLI 后必须复跑；改了哪个 scope 就重点看哪一族（§十二）。
2. 手验守恒：取任意一份 envelope，核对 `total == len(items)` 且 `total == changed + skipped + errors`。
3. 跑 `--project-docs`（dry-run）与 `--publish-agents --host claude-session`（dry-run），对照§五/§六读输出。**不要 execute**——真实写入走发布窗（联审）。
4. 读码顺序（按锚不通读）：L256-336（合同）→ L1735-2034（project-docs）→ L1351-1559（publish-agents）→ L791-885（保护链）→ L739-788（M-001+组合公式）→ L2412-2500（close）→ L3033-3286（argparse）。
5. 找到写根负路径测试三件（`test_target_path_live_root_prefix_resolves_to_live_root` L675 / `..._no_prefix_stays_support_root` L705 / `..._deep_nested_layout_live_root_correct` L720），读懂它们防的是什么——这是 3200b89 的回归护栏，动路径逻辑前先看。

## 十二、校验套件地图（18 类 180 项）

文件 `source_publish_check_validation.py`（4198 行）。类→域→行号（2026-09-05 实勘）：

| 类 | 域 | 起 L | 亮点测试 |
| --- | --- | --- | --- |
| ComparisonLogicTests | sync 域单元 | 256 | 全同零漂移/binding 排除/五件套排除/gap |
| CLIIntegrationTests | CLI 集成 | 420 | envelope 十键断言=合同钉子 |
| AgentPublishLogicTests | 发布逻辑 | 521 | **写根负路径三件 L630-753**；整轮否决 |
| AgentPublishBaseCLITests | 发布 CLI | 1079 | execute 参数错配拒 |
| ProjectDocumentSyncTests | PD 单元 | 1175 | copy dry-run→execute / 元信息门 / 逃逸拒 |
| ProjectDocumentSyncCLITests | PD CLI | 1417 | execute 需显式模式 |
| EnvelopeContractTests | 合同 | 1510 | 词表契约化/守恒/盘符相对拒 |
| RunIdExplicitTests | 运行标识 | 1744 | 显式覆盖/非法拒/容器传播 |
| CombinedContainerAggregationTests | 容器聚合 | 1880 | errors 优先聚合/直和守恒 |
| AdeEnvelopeHelperTests | 解析助手 | 1976 | 畸形容器防御 |
| CloseCliTests | close | 2051 | 双 close 拒/CLOSE_REJECTED 全型 |
| ScoreCliTests | score | 2218 | omission 零分规则/质量分越界拒 |
| AgentPublishRenderTests | 渲染 | 2558 | CRLF→LF 归一仅渲染面/工具剔除审计/翻转逻辑变体目录 |
| AgentPublishHostCLITests | 宿主 CLI | 3113 | 污染变体目标零写入 |
| ClaudeSessionRenderTests | **会话面** | 3269 | 无 frontmatter/片段缺失显式 error/未声明零行为/落区翻转 |
| AgentPublishSessionHostCLITests | 会话面 CLI | 3659 | execute 写入无 frontmatter |
| EventWatchTests | 触发面 | 3795 | 首扫基线/mtime 触碰不误报/PD 永不自动写/裸仓 refs |
| EventWatchCLITests | 触发面 CLI | 4142 | 互斥/auto-sync 显式 |

历史注：CLI 文件头"13/13 green（2026-07-24）"是 B4 时点基线（ComparisonLogic+CLIIntegration 两类 13 项）；套件此后随 scope 扩容至 180 项，13 项仍是合同底线回归面。

## 十三、使用依据

- 全部行号：`TriCompany/runtime/cognition/source_publish_check.py`（4688 行）与 `source_publish_check_validation.py`（4198 行），2026-09-05 实读
- 套件读数：`python -m unittest runtime.cognition.source_publish_check_validation` → `Ran 180 tests in 46.783s / OK`（2026-09-05T03:5xZ 实跑）
- dry-run 样本：2026-09-05T03:56Z `--project-docs` 实跑 envelope（见[小白版](01-beginner-guide.md)§六）
- 协议条文：`fade-protocol-spec.md` §2.2/§2.4/§2.5/§2.6/§8.6；登记册 FADE-002 条
- 写根修复裁示与事故弧线：TriCompany commit 3200b89（docstring/调用点注释原文 L796-800/L1503-1509）
