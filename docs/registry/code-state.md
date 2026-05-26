# TriCompany Code State

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/registry/code-state.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: active-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/registry/code-state.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-05-24

## Repository Map

- TriMetaverse/.github/agents/: 当前生效的本地正式接管 registry agent 与总助研发套件
- TriMetaverse/.github/instructions/: 当前生效的总助维护规则
- TriMetaverse/.github/manifests/: 记录从 shadow-test 收口到本地正式接管的宿主资产清单
- TriMetaverse/.github/prompts/: 当前生效的会议开始 / 结束入口
- TriMetaverse/.github/: 当前生效的 Copilot 本地正式接管宿主资产层
- support root: 当前生效本地正式接管资产统一回看的支撑根目录，负责提供 docs、runtime 与 vendor 参考副本；当前固定为 TriCompany-copilot-host-assets
- historical support root name: `TriCompany-shadow-host` 仅保留为 phase-1 已验证证据链对应的历史路径名
- .github/source-agents/: registry agent 草案与员工源侧五件套；不作为 VS Code agent discovery 入口
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
- 当前 CPO / CTO 已采用既有 `TriMetaverse/.github` live entry 上岗，并已补齐 `TriCompany/.github/source-agents/chief-product-officer/**`、`TriCompany/.github/source-agents/chief-technology-officer/**`、host object generation、CLI 与 support `knowledge/{roles,employees}/chief-{product,technology}-officer/**` 对象载荷；这不代表 TriMC 正式宿主切换
- 当前 CodeRegistry 由 CTO 小狄管理，负责代码事实、CodeGraph 摘要、技术风险、实现边界、仓库健康与工程门禁；CEOChiefOfStaff 只负责技术事项的公司级路由、协调、催办、升级与中央收口
- 当前集成产品开发流程（IPD 流程）由 TriCompany source 侧维护；TriDev 只作为产品开发执行段 phase engine / local engine 被调用，不承接 COO / CFO 持续运营监控或公司级总编排
- 当前已把 `runtime/cognition/ipd_case_engine.py` 改写为一比一 ten-phase case line：阶段模板、work item、phase package draft、participant roles 与总助 / CEO 顺序签核已按 `DISCOVERY -> DELIVERY` 对齐
- 当前已具备 source 侧回归入口：`python -m unittest runtime.cognition.chief_of_staff_bridge_validation`、`python -m unittest runtime.cognition.chief_of_staff_workflow_validation`、`python -m unittest runtime.cognition.chief_of_staff_schedule_staging_validation`
- 当前已具备 closeout 相关 source 侧回归入口：`python -m unittest runtime.cognition.chief_of_staff_registry_closeout_validation`、`python -m unittest runtime.cognition.chief_of_staff_operating_review_closeout_validation`
- 当前已具备 source 侧 CLI / staging 入口：`python -m runtime.cognition.chief_of_staff_schedule_staging --help`
- 当前已具备 source 侧 resident / closeout CLI 入口：`python -m runtime.cognition.chief_of_staff_resident_runner --help`、`python -m runtime.cognition.chief_of_staff_operating_review_closeout --help`
- 当前已具备 source 侧 wiki batch refresh CLI 入口：`python -m runtime.cognition.chief_of_staff_wiki_batch_refresh --help`
- 当前“代码健康”主要体现为结构边界、文档一致性和当前阶段宿主资产口径的清晰度
- 当前已具备一个未执行的 Supermemory live smoke 入口，用于承接真实账号验证前的最后一层门禁
- 当前已明确公司级技术纪律：模块一旦进入真实开发启动，默认由 CTO 与对应 CodeRegistry 完成本地 CodeGraph 初始化、忽略规则与索引摘要维护；`TriDev` 已作为当前首个执行对象落地该基线

## Change Tracking Baseline

- 重大边界变化应先更新 docs/product 与 docs/engineering
- registry 仅在明确要求记录时同步更新
- 总助套件、Hermes 融合规则和 .github 宿主资产的耐久变化应视作仓库结构变化，必要时回写 code-state
- 模块进入真实开发启动后，应由对应 CTO / CodeRegistry 在同轮或下一轮补齐 CodeGraph 初始化、摘要登记和刷新节律说明

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
- ../../.github/source-agents/
- ../../README.md
