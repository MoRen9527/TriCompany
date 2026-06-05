# TriCompany 技术设计初版

版本：V0.1
日期：2026-04-16
状态：初版

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/DESIGN.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/engineering/DESIGN.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-04-28

## 1. 设计目标

TriCompany 的技术设计目标不是直接宣称自己已经成为 TriMC 正式宿主，而是先把赛博公司的研发资产、Hermes 融合分层和当前阶段 Copilot 本地正式接管宿主资产清楚落盘。

## 2. 当前设计判断

### 2.1 TriCompany 是研发仓，同时承载当前阶段 Copilot 本地正式接管宿主资产

- TriCompany 当前承载文档、registry、agent 草案、会议 prompt、Hermes 融合设计和当前阶段放在 .github 下的 Copilot 宿主资产
- 这代表当前阶段正式接管，不代表正式宿主切换
- 因此 TriCompany 当前不承诺服务端、网关或正式记忆后端已经完成

### 2.2 总助采用 Hermes 化分层设计，而不是“一个 agent 知道所有底层文件”

基于 Hermes 的研究结论，首版总助在 TriCompany 内采用以下逻辑分层：

1. 身份层：soul
2. 运行时 contract 层：chief-of-staff agent 本体
3. 认知资产层：memory、colleagues、social
4. 协作入口层：开始会议 / 结束会议 prompt
5. registry bridge 层：TriCompanyProductRegistry、TriCompanyCodeRegistry
6. Copilot 宿主层：TriCompany/.github 下当前阶段可调用资产
7. Hermes 融合层：recall、sync、session-end consolidate 的设计与后续验证入口

其中 soul 定义“是谁、怎么说话、什么气质”，不与普通记忆混写；memory、colleagues、social 负责阶段记忆、工作关系和社交关系，也不应在对话里作为底层文件被总助显式提及。

### 2.2.1 元认知层采用“统一内核 + 员工私域 + 组织共享”混合结构

- 不采用“所有员工共用一个大元认知池”的做法，因为这会打穿人格边界、岗位边界和审计边界。
- 也不采用“每个员工复制一整套元认知 runtime”的做法，因为这会让 recall、sync、consolidate 和共享事实漂移。
- 当前采用混合结构：
  1. 统一一个公司级元认知内核，负责 provider 生命周期、recall、sync、session-end consolidate 和审计。
  2. 每个员工保留独立私域命名空间，持有自己的 soul、memory、colleagues、social 与岗位私有记忆。
  3. 公司层保留一个受审计的组织共享命名空间，承载会议纪要、经营结论、registry 快照和跨角色共享事实。
- 因此，统一的是 kernel 和协议，不统一的是人格与私域记忆。

### 2.3 registry 与总助是协作关系，不是主从替代关系

- Product Registry 维护产品真源与产品状态
- Code Registry 维护技术真源、结构状态与执行层纪律
- 总助在需要核对事实或推动同步时调用 registry，但不长期代替 registry 维护事实

## 3. 仓库结构

- docs/product/: 项目定位、需求、路线和状态
- docs/engineering/: 设计、技术路线和技术状态
- docs/registry/: 模块级事实快照
- docs/workflow/: 研发编排、Hermes 融合与秘书处草案
- docs/execution/: 当前启动阶段的计划、总结、验证
- vendor/reference/: Hermes 参考代码冻结副本
- runtime/cognition/: TriCompany 自己的元认知 contracts、kernel 和 providers 原型
- .github/source-agents/: registry agent 草案与当前阶段 Copilot 宿主源侧员工五件套；不作为 VS Code agent discovery 入口
- .github/instructions/: 总助维护边界
- .github/manifests/: 回迁 TriMetaverse/.github 的宿主资产清单
- .github/prompts/: 会议入口

## 4. 当前编排流

1. 当前用户通过 TriCompany/.github 下的 Copilot 宿主资产进入
2. 总助先按产品、技术、执行、会议四类判断路由
3. 涉及产品事实时优先核对 docs/product 与 TriCompanyProductRegistry
4. 涉及技术事实时优先核对 docs/engineering、docs/execution 与 TriCompanyCodeRegistry
5. 涉及会议节奏时通过开始会议 / 结束会议 prompt 进入正式口径
6. Hermes 相关结论优先沉淀到 TriCompany 的设计与执行层文档
7. 只有形成稳定跨仓结论时，再考虑同步回 TriMetaverse

## 5. 与 Hermes 的关系

当前已明确可借鉴的 Hermes 思路：

- soul 属于身份层，而不是普通记忆层
- 持久记忆、用户画像、会话搜索和外部 memory provider 应是分层而不是一锅端
- 运行时应由统一编排层处理 recall、sync、session-end consolidate，而不是让 agent 在对话里显式知道底层存储
- 当前阶段 Copilot 宿主资产应只暴露可调用入口，不暴露底层记忆存储细节

当前已在 TriCompany 中落实的代码边界为：

- vendor/reference/hermes-agent-memory/src/：冻结参考副本，仅保留 memory_provider、memory_manager、memory_tool
- runtime/cognition/contracts/：TriCompany 自己的元认知契约
- runtime/cognition/kernel/：统一元认知内核骨架
- runtime/cognition/providers/：内建 markdown、组织共享和外部适配 provider 骨架
- .github/manifests/：记录从 shadow-test 收口到本地正式接管的宿主资产 manifest

TriCompany 当前不仅沉淀这些设计结论，也把它们落到 .github 下的当前阶段 Copilot 宿主资产里；但仍不宣称已经完成生产级 Hermes 运行时集成。

## 6. 待实现与待确认

- 当前阶段 Copilot 宿主资产的验证与迭代
- recall / consolidate 的真正运行契约
- CPO / CTO 上岗后对设计的接管与重构
- 是否需要把认知资产进一步抽象为独立 Cognition agent
