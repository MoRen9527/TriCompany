# TriCompany Runtime Cognition

版本：V0.1
日期：2026-04-16
状态：原型骨架

## 1. 定位

本目录是 TriCompany 的元认知运行时原型层。

它不等于正式宿主，也不等于把 Hermes 原样搬过来；它的作用是把 Hermes 的核心 memory / metacognition 编排思路转成 TriCompany 自己可持续演进的结构。

## 2. 当前结构

- contracts/: provider 生命周期、命名空间和 recall 数据结构
- kernel/: 统一元认知内核骨架
- providers/: 内建 markdown、组织共享和外部适配 provider；其中 builtin_markdown 与 org_shared 已具备本地文件落盘能力，external_adapter 已支持注入式外部后端适配，external_http_backend 已补齐最小 HTTP 传输层，supermemory_backend 已按官方 schema 落地 vendor 适配，supermemory_sdk_backend 已补齐官方 SDK 形状的注入式 seam
- knowledge_workspace.py: role / employee / org shared / audit knowledge workspace 的最小源侧路径抽象
- host_object_generation.py: role / employee / org shared / audit workspace 发布到当前 host support root 的对象生成逻辑，并声明 RAndDTrainer 与 CEOChiefOfStaff 兼容对象集
- employee_host_object_generation.py: 统一员工 host object payload CLI，可生成全部已声明员工或单个员工对象集
- employee_host_binding_profile_generation.py: 员工级 host binding profile 导出 CLI，把当前宿主阶段、live 入口和 support payload 路径落到源侧 `.github/binding-profiles/*.json`
- employee_host_publish.py: 推荐的员工发布 wrapper，在同一条命令里同时生成 support payload 和员工级 binding profile
- ipd_case_engine.py: TriCompany IPD 主动交付线的一比一 ten-phase case state machine，负责 intake briefing gate、`DISCOVERY -> ... -> DELIVERY` 阶段 work item、phase package draft、书面签核和自动推进
- chief_of_staff_ipd_case.py: IPD case CLI；推荐顺序是先用 task-intake 接一句 CEO / 总助任务形成粗草案，再用 init 对同一 case 做 intake briefing refinement，之后再 intake-approve / submit / signoff / status / step
- chief_of_staff_legacy_path_deprecation_readiness.py: 总助 legacy `knowledge/chief-of-staff/**` 路径的 deprecation readiness 扫描入口
- chief_of_staff_legacy_path_shadow_gate.py: 总助 legacy 路径迁移的显式 shadow gate，验证旧目录保留、新 employee workspace 并行可用、当前 workbench 不再回指旧路径，并确认 manifest 已进入 deprecated compatibility 状态
- smoke_test.py: 最小可执行 smoke test，用于验证命名空间边界和 provider 生命周期
- contract_validation.py: Hermes 核心 recall/consolidate 契约验证，用于验证 fencing、单外部 provider 与 consolidate 命名空间约束
- integration_validation.py: provider-backed 集成验证，用于验证私域/共享/审计落盘与跨实例 recall
- backend_validation.py: production 风格后端验证，用于验证环境变量驱动的后端根目录、跨会话追加写入和审计元数据
- external_validation.py: 模拟外部后端兼容性验证，用于验证 ExternalCognitionAdapter 的命名空间过滤、与 builtins 并存和 recall 生命周期联动
- http_backend_validation.py: HTTP 外部后端验证，用于验证 Bearer 认证、JSON 协议、超时失败，以及与 builtins 并存时的远端 recall 生命周期联动
- supermemory_validation.py: Supermemory 官方 schema 验证，用于验证 `/v3/documents`、`/v4/search`、vendor-specific payload 映射、429 retry 与错误体解析
- supermemory_sdk_validation.py: Supermemory 官方 SDK seam 验证，用于验证 documents.add / search.documents 调用映射、命名空间到 containerTag 的 SDK 参数映射，以及不依赖真实包安装的注入式集成边界
- supermemory_live_validation.py: 显式 opt-in 的 Supermemory live smoke 入口；仅在设置环境变量后执行真实远端写入与召回，默认跳过
- role_employee_workspace_validation.py: role / employee knowledge workspace 路径、目录生成和 recall 顺序验证
- rd_trainer_host_object_generation_validation.py: RAndDTrainer、CEOChiefOfStaff 兼容 support object payload 与 host-object-manifest 生成验证
- employee_host_publish_validation.py: 员工发布 wrapper 的聚合验证，确认同一条命令会同时生成 support payload 和员工级 binding profile
- chief_of_staff_legacy_path_deprecation_validation.py: 总助 legacy 路径 deprecation readiness 扫描规则验证

## 3. 当前核心判断

- 全员共用一个统一元认知内核
- 每个员工保留自己的私域人格与记忆空间
- 公司层保留一个受审计的组织共享记忆空间

## 4. 与其他层的关系

- vendor/reference/：冻结 Hermes 参考副本
- runtime/cognition/：TriCompany 自有元认知原型
- .github/：当前阶段可回迁的宿主资产层

## 5. 当前可执行验证

- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.smoke_test
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.contract_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.integration_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.backend_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.external_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.http_backend_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.supermemory_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.supermemory_sdk_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.supermemory_live_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m unittest runtime.cognition.role_employee_workspace_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m unittest runtime.cognition.rd_trainer_host_object_generation_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.chief_of_staff_legacy_path_deprecation_readiness
- 运行命令：在 TriCompany 仓库根目录执行 python -m unittest runtime.cognition.chief_of_staff_legacy_path_deprecation_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.chief_of_staff_legacy_path_shadow_gate --require-ready
- 运行命令：在 TriCompany 仓库根目录执行 python -m unittest runtime.cognition.chief_of_staff_legacy_path_shadow_gate_validation
- 运行命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.chief_of_staff_ipd_case --help
- 粗任务入口：在 TriCompany 仓库根目录执行 python -m runtime.cognition.chief_of_staff_ipd_case task-intake "<CEO 或总助任务描述>"
- refinement 入口：在 TriCompany 仓库根目录执行 python -m runtime.cognition.chief_of_staff_ipd_case init --case-id <已有-case-id> ...
- 推荐发布命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee all
- 拆分发布命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.employee_host_object_generation --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee all
- 拆分发布命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.employee_host_binding_profile_generation --source-root . --employee all
- 兼容生成命令：在 TriCompany 仓库根目录执行 python -m runtime.cognition.rd_trainer_host_object_generation --support-root ..\TriMetaverse\TriCompany-copilot-host-assets
- 运行命令：在 TriCompany 仓库根目录执行 python -m unittest runtime.cognition.employee_host_publish_validation
- live 运行前提：设置 TRICOMPANY_ENABLE_SUPERMEMORY_LIVE_VALIDATION=1 与 SUPERMEMORY_API_KEY；可选设置 SUPERMEMORY_BASE_URL、SUPERMEMORY_USE_BEARER_AUTH、SUPERMEMORY_TIMEOUT_SECONDS、SUPERMEMORY_LIVE_SEARCH_ATTEMPTS、SUPERMEMORY_LIVE_SEARCH_DELAY_SECONDS
- live 默认落档：docs/execution/hermes-copilot-host/phase-1/SUPERMEMORY-LIVE-VALIDATION.latest.json；如需自定义可设置 TRICOMPANY_SUPERMEMORY_LIVE_REPORT_PATH
- live 收口预览：在 TriCompany 仓库根目录执行 python -m runtime.cognition.supermemory_live_finalize
- live 收口回写：在 TriCompany 仓库根目录执行 python -m runtime.cognition.supermemory_live_finalize --apply
- 当前已通过的覆盖面：共享内核下的私域/共享命名空间边界、prefetch 查询命名空间、sync_turn 与 session_end 的 provider 生命周期闭环
- 当前已通过的 Hermes 核心契约：recalled context 的清洗与 fencing、单外部 provider 限制、session-end consolidate 的命名空间越界校验
- 当前已通过的 provider-backed 集成：builtin_markdown 与 org_shared 可把私域/共享/审计信息写入本地 markdown 文件，并被新的内核实例跨实例 recall
- 当前已通过的 production 风格后端验证：TRICOMPANY_COGNITION_HOME 驱动的后端根目录、跨会话追加写入，以及 audit 文件的 provider/timestamp/namespace 元数据
- 当前已通过的模拟外部后端兼容性验证：ExternalCognitionAdapter 可过滤 query 命名空间外的 recall 结果，并与 builtin_markdown / org_shared 并存完成 recall 与 session 生命周期联动
- 当前已通过的 HTTP 外部后端验证：HttpExternalCognitionBackend 可完成 Bearer 认证、401 拒绝、timeout 失败，以及与 builtin_markdown / org_shared 并存时的远端 recall 联动
- 当前已通过的 Supermemory schema 验证：SupermemoryExternalBackend 已按官方 `/v3/documents` 与 `/v4/search` schema 完成 containerTag 映射、429 retry、401 非重试错误和 vendor 错误体解析验证
- 当前已通过的 Supermemory SDK seam 验证：SupermemorySdkExternalBackend 已完成 documents.add / search.documents 的参数映射、containerTag 命名空间映射与 provider 生命周期联动验证
- 当前已提供但未默认执行的 live smoke：supermemory_live_validation.py 可在显式启用时验证 private/shared/audit 三类命名空间的真实远端写入与召回
- 当前已通过的 role / employee workspace 验证：knowledge_workspace.py 可生成 role、employee、org shared、audit 四类知识空间路径，并固定 employee -> role -> org shared -> audit 的 recall 顺序
- 当前已通过的员工 host object generation / publish 验证：可通过统一 wrapper 同时生成 support payload 与员工级 binding profile，并登记 `TriCompany-copilot-host-assets/host-object-manifest.json` 与 `TriCompany/.github/binding-profiles/*.json`；CEOChiefOfStaff 的 `knowledge/chief-of-staff/**` 已降为 deprecated legacy 兼容路径，RAndDTrainer 不预创建 `.tricompany-cognition` 运行态文件
- 当前已建立并通过的 legacy path deprecation readiness 验证：可扫描 runtime、support runtime、live `.github` 入口与中央治理锚点，判断 `knowledge/chief-of-staff/**` 是否仍有阻塞正式 deprecation 的活依赖
- 当前已建立并通过的 legacy path shadow gate：在保留旧目录的同时，验证 `knowledge/employees/ceo-chief-of-staff/**` 具备并行对象、当前 workbench 不再回指旧路径、source/support manifest 均为 `deprecated-legacy-path`
- 当前已建立 IPD 主动交付线一比一 ten-phase runtime slice：CEO / 总助输入先进入 intake briefing gate；总助需先把机会信号、对当前商业模式的适配、对当前阶段的适配、公司现状、owner 建议、资源 envelope、前置条件、所需支持和预期成果整理成入口 briefing，再由 CEO / CEOChiefOfStaff 书面签核；通过后系统按 `DISCOVERY -> INTELLIGENCE -> DESIGNING -> CODING -> VERIFY-INTEGRATION -> REDTEAM -> QA -> DEPLOYMENT -> ASSURANCE -> DELIVERY` 的顺序自动生成阶段 work item，并把公司员工参与、资料与核签要求挂到各 phase
- 当前未覆盖：真实 Supermemory API key 下的 live 调用结果、账号级限流/配额语义、真实官方 SDK 包安装与 production 级远端后端差异
