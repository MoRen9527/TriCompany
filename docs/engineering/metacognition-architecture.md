# TriCompany 元认知层架构

版本：V0.1
日期：2026-04-16
状态：已完成 Supermemory 官方 schema 验证

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/metacognition-architecture.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/engineering/metacognition-architecture.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-04-28

## 1. 文档定位

本文用于定义 TriCompany 在 Hermes 融合阶段采用的元认知层架构。

它回答两个核心问题：

1. Hermes 的 memory 编排应该如何落到 TriCompany 项目结构。
2. 元认知层是全员共用一个，还是每个员工各自一套。

## 2. 核心结论

当前采用混合结构，而不是二选一。

- 统一一个公司级元认知内核。
- 每个员工拥有自己的私域记忆空间。
- 公司层再保留一个受审计的组织共享记忆空间。

因此，统一的是 kernel、命名空间策略、审计与 recall / sync / consolidate 协议；不统一的是人格、岗位私域记忆和员工社交连续性。

## 3. 为什么不是“一个全员共用元认知池”

- 会打穿 CEO 总助、CPO、CTO、CFO 等角色的人格边界。
- 会让岗位私有判断和共享经营事实混在一起。
- 会让审计难以回答“是谁写入了什么、写到哪里”。

## 4. 为什么不是“每个员工一整套元认知 runtime”

- 会让 recall、sync、session-end consolidate 的规则漂移。
- 会让会议纪要、经营结论和 registry 快照难以复用。
- 会让后续回迁 TriMetaverse/.github 时需要搬运多套不一致宿主资产。

## 5. 当前结构分层

### 5.1 冻结参考层

- vendor/reference/hermes-agent-memory/
- 只保留 Hermes 的 memory_provider、memory_manager、memory_tool 作为本地锚点

### 5.2 TriCompany 元认知原型层

- runtime/cognition/contracts/
- runtime/cognition/kernel/
- runtime/cognition/providers/

### 5.3 Copilot 宿主资产层

- source-agents/
- .github/prompts/
- .github/instructions/
- .github/manifests/

## 6. 员工与组织的记忆拓扑

每个员工至少对应三类作用域：

1. 私域记忆：岗位自身的工作连续性
2. 组织共享：会议结论、经营事实、跨角色可复用信息
3. 审计空间：记录写入动作、回忆来源和回迁边界

对应关系如下：

- soul、memory、colleagues、social 继续属于员工私域表达层
- registry 快照、会议纪要、经营结论优先进入组织共享层
- runtime/cognition/kernel 负责决定什么时候读私域、什么时候读共享、什么时候写审计

## 7. 与 TriMetaverse 回迁的关系

当前阶段回迁 TriMetaverse/.github 时，回迁的是 Copilot 宿主资产层，而不是把 runtime/cognition 直接当正式宿主部署。

因此必须区分：

- TriCompany：研发与本地正式接管宿主资产收口仓
- TriMetaverse/.github：当前 Copilot-host 正式接管的宿主位置，起点为 shadow-test 回迁验证
- TriMC：未来赛博公司正式服务域宿主

## 8. 当前已验证的 Hermes 核心契约

1. recalled context 在注入前必须先去除内嵌 memory-context/system note，再统一外层 fenced context 注入
2. 内建 provider 可以并存，但外部 cognition provider 在同一内核里一次只允许一个
3. session-end consolidate 只能写回当前 actor 的私域、组织共享和审计三类命名空间，不能越界写入其他员工私域
4. 上述契约已可通过 python -m runtime.cognition.contract_validation 直接验证
5. builtin_markdown 与 org_shared 已可通过 python -m runtime.cognition.integration_validation 完成私域/共享/审计落盘与跨实例 recall 验证
6. TRICOMPANY_COGNITION_HOME 驱动的后端根目录、跨会话追加写入和 audit 元数据已可通过 python -m runtime.cognition.backend_validation 直接验证
7. ExternalCognitionAdapter 已可通过 python -m runtime.cognition.external_validation 验证 query 命名空间过滤，以及与 builtin_markdown / org_shared 的并存和 recall 联动
8. HttpExternalCognitionBackend 已可通过 python -m runtime.cognition.http_backend_validation 验证 Bearer 认证、401 拒绝、timeout 失败，以及与 builtin_markdown / org_shared 的并存和远端 recall 联动
9. SupermemoryExternalBackend 已可通过 python -m runtime.cognition.supermemory_validation 验证 `/v3/documents`、`/v4/search`、namespace 到 containerTag 的 vendor 映射、429 retry，以及 vendor 错误体解析

## 9. 下一步

- 引入真实 Supermemory API key 下的 live 调用与官方 SDK 集成验证
- 在现有本地 provider-backed 基线之上扩展更细粒度的 recall 排序与 consolidate 策略
- 在保持同一契约的前提下继续推进 TriMetaverse 当前本地正式接管宿主验证，并为未来 TriMC 宿主验证保留平行入口
