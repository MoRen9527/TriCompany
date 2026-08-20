# TriCompany Code State

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/registry/code-state.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/registry/code-state.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-06-04

## Repository Map

- TriMetaverse/.github/agents/: 当前生效的本地正式接管 registry agent 与总助研发套件
- TriMetaverse/.github/instructions/: 当前生效的总助维护规则
- TriMetaverse/.github/manifests/: 记录从 shadow-test 收口到本地正式接管的宿主资产清单
- TriMetaverse/.github/prompts/: 当前生效的会议开始 / 结束入口
- TriMetaverse/.github/: 当前生效的 Copilot 本地正式接管宿主资产层
- support root: 当前生效本地正式接管资产统一回看的支撑根目录，负责提供 docs、runtime 与 vendor 参考副本；当前固定为 TriCompany-copilot-host-assets
- historical support root name: `TriCompany-shadow-host` 仅保留为 phase-1 已验证证据链对应的历史路径名
- source-agents/: registry agent 草案与员工源侧五件套；不作为 VS Code agent discovery 入口
- .github/instructions/: 总助维护规则
- .github/manifests/: 回迁 TriMetaverse/.github 的 shadow-test 清单
- .github/prompts/: 会议开始 / 结束入口
- .github/: 当前阶段 Copilot 试运行宿主资产层
- docs/product/: 产品真源
- docs/engineering/: 技术真源
- docs/workflow/: 编排与秘书处草案
- docs/workflow/: 集成产品开发流程（IPD 流程）、秘书处草案与跨岗位 owner 边界
- docs/execution/: 当前启动阶段执行文档
- docs/training/: 岗位、模块、代码和流程培训材料
- vendor/reference/: Hermes 冻结参考副本
- runtime/cognition/: 元认知 contracts、kernel、providers，以及 chief-of-staff workflow / schedule source 回迁入口

## Current Code Health

- 当前属于 docs-first + .github 宿主资产并行状态
- 当前已完成 runtime/cognition 的 smoke、contract、integration、backend、模拟 external-adapter、HTTP external-backend、Supermemory schema、Supermemory SDK seam 与 Supermemory live smoke 九层验证基线
- 当前已把 chief-of-staff approval report、task_resolver、cron_runner / resident_runner、knowledge workbench、schedule staging CLI、workflow bridge 与对应 source validation 回写到 `TriCompany/runtime/cognition/`
- 当前已把 chief-of-staff resident runner CLI、operating review closeout CLI，以及 registry / operating review closeout source validation 回写到 `TriCompany/runtime/cognition/`
- 当前已把 chief-of-staff wiki batch refresh CLI 回写到 `TriCompany/runtime/cognition/`，当前可见 top-level `chief_of_staff_*.py` 入口已与 support bundle 对齐
- 当前已把 workflow hook 的 command 识别、stdin 解析与 `sync-memory` 调度纯逻辑提炼到 `TriCompany/runtime/cognition/chief_of_staff_workflow_sync_hook.py`；TriMetaverse live hook 脚本仅保留 thin wrapper
- 当前生效的本地正式接管 agent / prompt / manifest 位于 TriMetaverse/.github，TriCompany-copilot-host-assets 负责支撑文档、runtime 与 vendor 参考副本
- 当前已完成同一 support root 下的连续会议链路补证，可统一写成“本地 Copilot-host 已完成 shadow-test，现进入正式接管；该结论不等于正式宿主切换。”
- 当前已完成中央命名吸收；未来若进入 `TriMC` 新宿主，应另建平行宿主资产包，而不是复用当前 Copilot-host 的物理命名
- 当前 CPO / CTO 已采用既有 `TriMetaverse/.github` live entry 上岗，并已补齐 `TriCompany/source-agents/chief-product-officer/**`、`TriCompany/source-agents/chief-technology-officer/**`、host object generation、CLI 与 support `knowledge/{roles,employees}/chief-{product,technology}-officer/**` 对象载荷；这不代表 TriMC 正式宿主切换
- 当前 CodeRegistry 由 CTO 小狄管理，负责代码事实、CodeGraph 摘要、技术风险、实现边界、仓库健康与工程门禁；CEOChiefOfStaff 只负责技术事项的公司级路由、协调、催办、升级与中央收口
- 当前集成产品开发流程（IPD 流程）由 TriCompany source 侧维护；TriDev 只作为产品开发执行段 phase engine / local engine 被调用，不承接 COO / CFO 持续运营监控或公司级总编排
- 当前已把 `runtime/cognition/ipd_case_engine.py` 改写为一比一 ten-phase case line：阶段模板、work item、phase package draft、participant roles 与总助 / CEO 顺序签核已按 `DISCOVERY -> DELIVERY` 对齐
- 当前已新增 `run_case_autopilot` 与 `chief_of_staff_ipd_case autopilot`：可自动推进 intake 签核、十阶段提交/签核、岗位参与记录，并在 TriDev 可用时同步写入 phase result / gate / delivery bundle 校验证据；支持 `manual-ceo-signoff` 在 CEO 签核点切人工暂停
- 当前已具备 source 侧回归入口：`python -m unittest runtime.cognition.chief_of_staff_bridge_validation`、`python -m unittest runtime.cognition.chief_of_staff_workflow_validation`、`python -m unittest runtime.cognition.chief_of_staff_schedule_staging_validation`
- 当前已具备 closeout 相关 source 侧回归入口：`python -m unittest runtime.cognition.chief_of_staff_registry_closeout_validation`、`python -m unittest runtime.cognition.chief_of_staff_operating_review_closeout_validation`
- 当前已具备 source 侧 CLI / staging 入口：`python -m runtime.cognition.chief_of_staff_schedule_staging --help`
- 当前已具备 source 侧 resident / closeout CLI 入口：`python -m runtime.cognition.chief_of_staff_resident_runner --help`、`python -m runtime.cognition.chief_of_staff_operating_review_closeout --help`
- 当前已具备 source 侧 wiki batch refresh CLI 入口：`python -m runtime.cognition.chief_of_staff_wiki_batch_refresh --help`
- 当前“代码健康”主要体现为结构边界、文档一致性和当前阶段宿主资产口径的清晰度
- 当前已具备一个未执行的 Supermemory live smoke 入口，用于承接真实账号验证前的最后一层门禁
- 当前已明确公司级技术纪律：架构表中的模块一旦被写成正式模块面，默认由 CTO 与对应 CodeRegistry 补齐独立 git 仓、`README.md`、`docs/` 六件套、`.gitignore` 与本地 CodeGraph 初始化、忽略规则和索引摘要维护；占位模块也先补齐骨架，再保持“待初始化”标记；`TriDev` 已作为当前首个执行对象落地该基线
- 当前已明确既有正式模块流程：`Discovery` 阶段先产出 `ModuleTargetingReport`，并由 `TriDev` 执行 `ModuleReadinessInit`（标配审计与缺口 init），通过后再进入后续业务开发
- 当前已明确新正式模块流程：`Discovery` 阶段先产出 `NewModuleBaselineRelease`（含 `vendor-extraction-profile`），签核到 `approved` 后由 `TriDev init` 消费发布包执行 `init`；模块 owner 继续对提交质量与长期演进负责
- 当前已完成宿主对象生成编排层设计：`docs/engineering/host-object-generation-design.md`（COPY/SYMLINK/GENERATE 三条路径、5-Gate Pipeline、版本策略）
- 当前已完成 Phase A 代码注册：TestEngineer + FullStackDeveloper HostObjectSetDefinition 写入 `runtime/cognition/host_object_generation.py`，DECLARED_HOST_OBJECT_SETS 9→11，EMPLOYEE_GENERATORS 补齐 CMO/COO/CFO 缺口 7→13
- **TriStaciss Credit Ledger 已落地（2026-07-14，CTO 小狄）**：`credit_ledger.py`（SQLite 账本）+ `credit_api.py`（balance/usage 查询端点）已集成到 `/v1/messages` 与 `/v1/chat/completions` 非流式路径。G3 门禁"Credit 消耗可追踪 → 可查证"非流式侧已达成；流式路径标记为 deferred
- **CTO-008 大框架 4/4 全部完成（2026-07-16，CTO 小狄）**；CTO-008-M 代码实现也已落地（2026-07-17）：CTO-008-C（TriMC/TriLC 共享核心抽象，含经营工作流状态机）+ CTO-008-M（TriMC↔TriLC 通信协议，M.1-M.6 28 tests 全部通过）+ CTO-008-P（PC 端打包方案）+ CTO-008-S（TriMC K8s HA 运维方案）全部设计+代码交付。K8s manifests 已同步更新（3 replicas + podAntiAffinity + HPA + PDB minAvailable=2 + Service sessionAffinity）。关联：TriMC/docs/engineering/cto-008-*.md 四份设计文档、TriMC/k8s/trimc/ manifests、CTO-007 smoke test pipeline
- **COS-005 Openclaw 吸收链规划已完成（2026-07-17，CTO 小狄）**：守护进程与定时任务吸收规划 APPROVED。输出 TriMC/docs/engineering/cos-005-openclaw-absorption-plan.md，四阶段 12h 分步吸收（P0 调度核心 4h → P1 执行可靠性+P1 进程监督 6h → P2 单机服务 2h）。吸收目标：CronService 定时任务调度 + ProcessSupervisor 受管子进程 + Backoff 退避重试。待 小全/小柯 接手实现阶段
- **cpo-trimodel-deployment Phase 1 完成（2026-07-22，小全/小狄）**：三仓库配置平面改造交付 — TriModel（API server 4 端点 + DeepSeek-Anthropic provider + v0.2.0）、TriLC（key-cache + mirror pusher + session store v2 + contract resolver）、TriPilot（TriLCClient HTTP+SSE）。Phase 2 backlog 8 项 CONDITIONAL_PASS 已登记（TriModel/docs/execution/cpo-trimodel-deployment/phase-2-backlog.md）。树闭合裁决：APPROVE（CTO 小狄，版本 bump commit 本地已落，push 待网络恢复）
- **Q3 Phase 2 统一发布管线完成（2026-07-24，CTO 小狄）**：`source_publish_check.py` 新增 `--publish-agents` 模式（dry-run by default, `--agent-execute` 显式写入）。核心函数：`run_agent_publish()`、`_filter_agent_publish_entries()`、`_publish_single_agent()`。manifest 动态派生 `AGENT_PUBLISH_ALLOWED_TARGETS` 白名单。`employee_host_publish.py` 末尾追加 subprocess 委托。验证：`source_publish_check_validation.py` 33/33 全部通过（13 回归 + 20 agent publish 新增）。独立于 `--sync` 模式，可与 `--check` 组合使用。关联：`TriCompany/runtime/cognition/source_publish_check.py`、`TriCompany/runtime/cognition/employee_host_publish.py`、`TriCompany/source-agents/registries/trimetaverse-live-agent-publish-manifest.json`
- **TriMC agent-core 共享化阶段 2 测试侧更新完成（2026-07-26，小全）**：CTO 小狄阶段 1（agent-core 共享化契约基准 + 灰区裁决 + 18 项逐项指令）APPROVE 全走测试侧（0 后端修复）。小全更新 8 个测试文件让 18 项失败转绿：sub-agent.test.ts（import 改 `@trimetaverse/agent-core`）、context-builder.test.ts（加 tools.js import 触发 registry + subagent 工具数 5→2）、gater.test.ts（5 处 reason 文案改 anti-recursion guard / requires tier ... or higher）、agent-tools.test.ts（error null→undefined、Unknown tool 大写 U）、pipeline.test.ts（两处 write_file@subagent 语义反转 main-only）、chat-endpoint.test.ts（unknown model 字面量化）、http-agent-endpoint.test.ts（加 tools.js import）、e2e/real-model-agent.test.ts（文件内容检查移入 toolCalls>0 块）。#18 第3项复跑暴露 2 处 tier 失败已补改：gater edge cases（write_file@subagent 改 read_file 反映新 tier 契约）+ agent-tools shell_exec stderr（CTO #2 模板三重障碍 → 改 where/which）。结果 `npm test` 455/455 pass / 0 fail。技术债务：CTO #2 的 `${process.execPath} -e "..."` 模板经实测存在 allowlist baseCmd 短名匹配 + cmd PATH 缺 nodejs + cmd 引号吞单引号三重障碍，已改 where/which 方案让测试转绿，待 CTO 确认。
- **packages/agent-core contracts 模块死形状登记 + O2-B 处置完成（2026-08-13，CTO 小狄）**：CodeRegistry 首次登记 `packages/agent-core`（此前零登记）。代码事实：合同体系两代并存——`source-agents/*`（v2，contract.version 2.0，contract+paths+decision_rights+runtime_baseline，TriLC 消费 14 份，4.2 已验 14/14）与 `docs/registry/*.contract.yaml`（v1，contract+identity+responsibilities+decision_rights+collaborators+tools+io_contract，TriMC `src/contracts/resolver.ts` 消费 11 份，io_contract 必填）；两代字段互不互通。风险事实：agent-core `src/contracts/` zod schema（metadata/capabilities/instances/rules）为早期设计残留第三形状，CTO 实测 safeParse 对两代合同全部失败（`metadata: Required`），零生产消费方（TriMC 仅 import agent-core 的 loop/permissions/tools/sub-agent 模块，合同走自有 resolver）。O2-B 处置：`src/contracts/` 三文件加死形状警示头注释、`ContractResolver` 类与 4 个契约类型标 `@deprecated`、dist 重建、TriMC `tsc --noEmit` 验证零影响。O2-A（合同真源统一 + schema 对齐，以 v2 为基础收敛，双域 resolver 迁 thin adapter）已列 M3 前置（OP M3 note），统一方向见 `docs/engineering/trilc-trimc-runtime-parity.md` §6.2。
- **合同收敛 schema v3.0 落地 agent-core（2026-08-13，CTO 小狄 / r13-1 A 段）**：O2-A 进入执行。规格文档 `docs/engineering/agent-contract-v3-spec.md`（单一权威 schema v3.0 = v2 基础 + TriMC 编排字段；无向后兼容分支；5 步迁移序列；thin adapter 边界；可检验性 10 项）。实现：`packages/agent-core/src/contracts/` 原位重建——`AgentContractV3Schema`（zod `.strict()`，version/type literal 3.0/agent-contract，family 枚举，io_contract inputs/outputs 非空必填，runtime_baseline 对象形状裁决）、`loadContractV3`/`resolveContractsV3`/`ContractV3Error`（负路径含版本指引）；旧符号与 @deprecated 双清零。测试：`test/contract-v3.test.mjs` node:test 8/8 全绿（正例默认值填充、1.0/2.0 拒绝、strict 未知字段拒绝、缺 io_contract、坏枚举、批量收集、文件缺失）。TriMC/TriLC `tsc --noEmit` 零影响（旧导出删除无消费方）。Step 0 golden 基线已冻结：r13 树 golden/ 下 v1-trimc.json（11 份）+ v2-trilc.json（14 份），r13-2 等价性比对以此为基准。后续：r13-2（B 段小全）按规格 §三/§四执行合同迁移与双域 adapter 切换；v1 11 份退役在 Step 4。
- **r13-4 收口更正两笔（2026-08-13，CTO 小狄）**：① business-strategy family Role→Registry（commit `60bc197`）——CTO 裁决依据：合同自证中央 registry 职能、employee-roster 13 员工不含该 agent（第 14 agent 非员工）、CLAUDE.md Registry Routing 惯例、v2 原值 Role 属历史笔误；roster 不动（不在名册，`families: {Role: 13}` 统计不变）。② test-engineer forbidden 回补"替代 BusinessStrategy 做中央战略裁决"（commit `9273782`）——r13-3 小柯 30 差异审计发现唯一真丢（v1 6 条在 v2 迁移前已缺 1 条，非 B 段丢失），对称护栏（CTO/CPO/BusinessStrategy 并列）缺一即约束弱化，从 git `2c2ccf5~1` 取回原文回补。两份合同均经 loadContractV3 解析验证通过。
- **ADE 整合阶段 0/1/2 代码落地（2026-08-20，CEO 启动，编排层收口）**：阶段 0 `004a506`（employee_host_publish 默认 dry-run `execute = args.execute`；`--publish-agents` 白名单∩禁区=∅ 硬校验 + 逃逸防护双层纵深——`_resolve_agent_target_path` resolve+relative_to + 静态 `..` 拦截；manifest 变更审计 changes before/after）；阶段 1 `856338e`（三 scope 统一 envelope 合同：protocol/version/scope/run_id/mode/check_time/status/summary{total,changed,skipped,errors}/items[七字段基座]/scope_specific；action 词表契约化 ADE_ACTIONS + 域子集；errors>0→rc=1；drive-relative 拒绝）；阶段 2 `fd59157`（`--run-id` 显式优先/时间戳回退 + 组合容器顶层聚合 errors 优先/直和守恒 + `ade_envelope.py` 公共解析器 + Close CLI `--close`：裁决校验→`.close-ade.json` 终态审计→CLOSE_REJECTED 非静默 + Score CLI `--score`：测试集覆盖检查 omission/quality-scores 注入合并/双门槛三态）。编码修复：subprocess `encoding="utf-8"` 4 处 + JSON 出口 `sys.stdout.reconfigure(encoding="utf-8")` + validation 侧 16 处配套（消除 GBK 隐式环境依赖）。验证基线：source_publish_check_validation 97 + employee_host_publish_validation 5 + employee_onboard_validation 33，小柯独立复测 50/50 + 47/47。
- **ADE 技术风险登记（2026-08-20，CTO 终审）**：① spec §2.5「权限」校验载体=宿主层（TriLC/Agent loop permission 系统），CLI 层本轮未实现（无权威身份源，硬造 --actor 是假权限门）；② 试卷阈值设计为实例责任（total_max < threshold 永不达线，模板 §二 已补设计约束文字）；③ 编码环境依赖已消除（见上）。
- **知识注入 MVP 落地（2026-08-20，CEO 启动，commit TriLC `180cfbf`）**：runtime 侧知识形态与注入链路（FADE-ASSESS-003）——knowledge.db v2（knowledge_documents 契约注入面 SHA-256 幂等 / knowledge_consumption 消费记录面 / knowledge_metrics 验证指标分子面）；同步（启动全量 + watch 增量，dry-run/隔离/源只读）；注入（`<knowledge-context>` 块 Memory→Colleagues→Social，三挂接点：session-initializer 主路径 / /agents system-prompt / heartbeat，降级不阻断）；指标（escalation_blocked + routing_error 三埋点 + GET /internal/v1/knowledge/metrics，CPO 三条可观测指标量化面）；supermemory phase-1 归档不演进生产。规范：TriMetaverse/docs/execution/knowledge-injection-spec.md。后置：TriMC 同构、内容层、org 注入、hermes 全量、主会话越权埋点、heartbeat 注入单测。
- **ADE-B 渲染改造落地（2026-08-20，CEO 启动，commit `4ce113d`）**：`--host {copilot|claude}`（默认 copilot 兼容现状）——HOST_RENDER_REGISTRY 宿主注册表（frontmatter 形状映射/目标派生/工具名映射/豁免前缀），渲染引擎"源+宿主模板→渲染"（manifest liveEntries 元数据 renderTemplate/extraSections，缺省=复制面字节保留向后兼容），派生一致校验（derived_identical/derived_drift 词表项）。保护链闭环：白名单∩禁区跑派生后目标 + **翻转逻辑（CTO 定口径：非精确 landing zone 即禁，不枚举变体）**——裸 binding-profiles 顶层、copilot→claude 跨宿主写、agents-backup 变体（含跨模块面）全堵。验证：validation 127/127 + 5/5 + employee_onboard 33/33 + 小柯终测门禁 73/73（含 e2e 零写入 8 项）+ 真实 manifest 多宿主（当前 copilot/claude 两宿主）18 条零拒绝。后续工作包：13 role-agent 渲染元数据落地 + `--agent-execute` 重渲染（消 live 漂移）、TriLC init-assemble 切换交接、工具名映射表覆盖度评估（execute 语义）、binding profile 生成管线一致性校验。

## Change Tracking Baseline

- 重大边界变化应先更新 docs/product 与 docs/engineering
- registry 仅在明确要求记录时同步更新
- 总助套件、Hermes 融合规则和 .github 宿主资产的耐久变化应视作仓库结构变化，必要时回写 code-state
- 模块进入正式模块面后，应由对应 CTO / CodeRegistry 在同轮或下一轮补齐 git / `README.md` / `docs/` 六件套 / `.gitignore` / CodeGraph 标配，并登记摘要与刷新节律说明
- 若涉及既有正式模块，`Discovery` 阶段必须先完成 `ModuleTargetingReport` 与 `ModuleReadinessInit`，再进入后续阶段
- 若涉及新增正式模块，`Discovery` 阶段必须先完成 `NewModuleBaselineRelease` 的 `candidate -> approved`，再允许 `TriDev init` 落下骨架并进入后续阶段

## Local CodeGraph Index

- 2026-05-24 已由 CTO 小狄技术线完成本地 CodeGraph 试点初始化，并由 TriCompanyCodeRegistry 接管索引摘要。
- 索引范围为仓根干净索引；`.gitignore` 已排除 `.codegraph/`、`.tricompany-cognition/`、`node_modules/`、`vendor/`、构建产物、缓存和环境文件。
- 当前摘要：100 files，1,494 nodes，3,042 edges，language `python`。
- 当前 pending changes 为 `0/0/0`；`.codegraph/` 只作为本地缓存，不作为仓库真源提交。

## Git Health

- `CodeRegistry` 负责维护活跃模块的 `Git Health` 事实：dirty worktree 基线、已知未提交切片、风险说明和升级提示。
- `CodeRegistry` 不直接代替 owner 做本地提交；本地提交责任仍归对应模块 owner 或当前实际开发 owner。
- 活跃模块若跨过一个会议周期仍保持 dirty，应把原因、风险、是否已有可提交切片与预计收口时间补回 `Git Health` 或 operating record。
- 对存在治理中 `vendor/` 冻结基线的模块，`vendor/` 默认进入模块 `.gitignore`，主 `CodeGraph` 默认排除 `vendor/`；专项吸收任务再临时切到 vendor 视图。

## Quality Risks

- 若把 TriCompany 误当作正式宿主，会造成后续宿主集成返工
- 若混淆 TriMetaverse/.github 生效宿主资产与 TriCompany-copilot-host-assets support root，会导致当前正式接管路径失真
- 若把“当前由 copilot 宿主承载 skill / cron 可用验证”误写成“copilot 等同于 TriMC”，会直接破坏宿主边界治理
- 若不持续区分身份层和记忆层，总助仍会退化为显式操作底层文件的设计
- 若不明确 .github 当前是本地正式接管宿主资产层而非 TriMC 正式宿主层，后续容易把阶段边界写乱
- 若把元认知层做成全员共享单一记忆池，会破坏员工人格边界和审计边界
- 若把元认知层做成每个员工一整套独立 runtime，会破坏公司级共享结论与回迁一致性
- 若 CPO / CTO 上岗后不及时输出首轮接管判断并接管 ProductRegistry / CodeRegistry，总助会继续代管过多边界
- 若后续验证不继续沿用 TriCompany-copilot-host-assets 作为唯一 support root，会导致当前生效路径与宿主资产说明失真
- 若把 Supermemory 官方 schema 验证等同于真实 Supermemory live 接入，会高估 production 接入成熟度
- 若把 Supermemory SDK seam 验证等同于真实官方 SDK 包接通或真实账号可用，也会高估 production 接入成熟度
- 若把 live smoke 脚本已存在等同于 live smoke 已执行，也会高估 production 接入成熟度
- 若把 ten-phase case line 已落地误写成 PRD 分叉并行、多分支 delivery 聚合、完整岗位 adapter 或正式宿主都已完成，会再次高估当前成熟度

## Sources

- ../engineering/DESIGN.md
- ../engineering/ROADMAP.md
- ../engineering/STATE.md
- ../engineering/metacognition-architecture.md
- ../workflow/chief-of-staff-rd-orchestration.md
- ../workflow/github-backport-manifest.md
- ../workflow/hermes-copilot-host-migration.md
- ../../TriMetaverse/docs/workflow/tricompany-copilot-host-assets-migration-matrix.md
- ../../source-agents/
- ../../README.md
