# ADE 四候选整合提案：发布域 + 员工域两 ADE

版本：v1.0（提案稿）
日期：2026-08-19
状态：CEO 已采纳（2026-08-19），待分阶段执行

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/ade-consolidation-proposal.md
- syncMode: follow-spec（2026-08-19 CEO 定调：本提案是为修订 ade-pattern-spec.md 而生的需求文档且 spec 挂链引用，随 spec 联动发布；spec 当前 source-only，未发布前本档仅存源侧）
- syncWith: docs/engineering/ade-pattern-spec.md
- lastSyncedAt: 2026-08-19

来源：CEO 2026-08-19 指令（四候选整合分析）——小贾牵头七维分析，小乔（产品语义）、小狄（技术合同）独立视角合成
依据规范：[ade-pattern-spec.md](ade-pattern-spec.md) v1.1.3（§六 案例表、§1.1 十段三档、§2.4 安全门、§2.6 试卷—答卷—评分、§8 两 profile）

## 〇、结论摘要

**整合为 2 个 ADE**，不另立新 FADE：

- **ADE-A 发布域** = FADE-002 扩容（候选 1 源侧→发布侧同步 + 候选 2 项目真源文档同步 + 候选 3 Agent live entry 发布）
- **ADE-B 员工域** = FADE-004 扩容（候选 4 员工对象发布并入上岗链）

执行层收敛为"1 个 CLI 入口 + 统一报告合同 + scope 差异"；**先修两处合同级缺口，再统一生命周期骨架**。

## 一、现状盘点

基线修正：候选 1+2 已事实收编为 FADE-002（FADE 档），spec §六 案例表此前滞后于登记册（本次已同步）。

| 维度 | 1 源侧→发布侧同步 | 2 项目真源文档同步 | 3 Agent live entry 发布 | 4 员工对象发布 |
| --- | --- | --- | --- | --- |
| 触发 | 发布事件/小赛指令，无程序事件 | 发布事件/联审，manual agent-owned | 发布事件/小赛指令，无程序事件 | 上岗后/职责变动，manual |
| 登记 | 无 runId（CLI 报告隐式） | manifest 状态隐式 | 无 runId（manifest 隐式） | 无 runId |
| CLI | `source_publish_check --check --sync --scope` | 同 CLI `--project-docs [--execute]` | 同 CLI `--publish-agents [--agent-execute]` | 独立 CLI `employee_host_publish`（内部委托 3） |
| 驱动面 | 目录扫描（SYNC_SOURCE_DIRS+EXCLUDE+保护目标） | manifest 域 | manifest（liveEntries + status 资格） | 声明面（HostObjectSetDefinition）+ binding profile |
| 语义裁决链 | 无（纯机械） | 小贾候选→小乔产品→小狄 revision/安全门 | 无（status 资格过滤） | CHO 审批门在 staffing 决策点（不在发布 CLI） |
| Close 链 | 无 | 联审裁决记录于 manifest | 无 | 无 |
| 安全门 | 默认 dry-run | 默认 dry-run | 默认 dry-run | **默认 execute（违反 §2.4）** |
| FADE 状态 | 已收编 FADE-002 | 已收编 FADE-002 | 未入册 | 候补区 |

事实整合已存在：`source_publish_check.py` main() 三分支（`--project-docs` / `--publish-agents` / `--check`）输出包于同一 JSON 壳，共享 dry-run 默认与保护目标；候选 4 经 `_delegate_agent_publish` 子进程桥接 `--publish-agents`（employee_host_publish.py:281）——"统一发布管线"（code-state.md Q3 Phase 2，33/33）已有一轮事实整合。

## 二、共性判定

**真共享（可统一）**：① CLI 家族（1/2/3 同一 py 文件 + 4 委托）；② 同一 JSON 壳与 §2.2 报告骨架；③ 保护目标体系（PROTECTED_TARGET_PATTERNS 跨 scope 共用）；④ 同一生命周期缺口（runId / Close CLI / Score 全缺，各自补一遍即四倍成本）。

**实例特有（不可合并）**：① 发现机制——目录扫描（决定"哪些需同步"）vs manifest 域（决定"哪些受管"），语义不同（§6.1 口径）；② 语义候选链——published-summary 的 CLI 只校验候选、永不合成摘要；③ 声明面渲染——host object 生成是生成式而非复制式；④ 审批门——CHO 审批在组织语义层（staffing 决策点），不进 CLI 合同。

**关键机制（小乔）**：语义候选链与发布生命周期**可解耦**——生命周期（事件→登记→DCE→Close→终态）全复用，`syncMode` 字段即档位开关（published-copy 机械档 / published-summary 语义档）。防"整合后过治理"：机械发布不被拖进语义联审。

## 三、整合方案

### ADE-A 发布域 = FADE-002 扩容（并入候选 3）

- 结构：一个 CLI 三个 scope 面（目录扫描 / project-docs / publish-agents）+ **双档语义裁决**（机械档：Plan=范围确认、Close=报告核对，无语义联审；语义档：Plan=小贾候选→小乔/小狄联审，Close=小贾据 DCE 证据裁决四态）+ 统一生命周期骨架
- 统一报告合同：顶层 `{protocol, version, scope, run_id, mode, check_time, status, summary{total,changed,skipped,errors}, items[{action,source,target,before_hash,after_hash,scope_key,error}], scope_specific:{}}`——四域专有字段入 `scope_specific`；收益 = Score CLI / Close CLI 单解析器单校验 schema 消费四域证据（报告分裂则 Score 需四套覆盖检查，违 §2.2）
- 明确不做 argparse 子命令化（重构 + validation 回归成本 > 收益，列中期低优先）

### ADE-B 员工域 = FADE-004 扩容（并入候选 4）

- 候选 4 是 FADE-004"上岗"后的工件落地段（employee_onboard_stages 第 5-7 段已委托 employee_host_publish 与 `--publish-agents`），本是一条链——合并后员工生命周期一个 FADE，避免另立 FADE-005
- 候选 3 按调用上下文归属：独立调用走 ADE-A，被员工发布委托时走 ADE-B——共用 `--publish-agents` 不复制实现
- 执行体分层保留（TriLC staffing.ts daemon 名册 + 源侧 employee_onboard/employee_host_publish 载荷发布）：合并生命周期/登记/审计/评分骨架，不合并执行体（§8.5 口径）
- live entry 定性（2026-08-19 live entry 评审裁决）：contract 的**派生加载壳**——身份/职责语义收敛 contract（三端可读），live entry 为宿主发现面的**渲染产物**（源+渲染模板→渲染，非字节副本；host 附加段须模板化回归源侧，防第二语义真源），禁人工编辑（渲染不一致时 publish 重新渲染覆盖 + 审计留痕）；三层语义分离：名册=决策真源、contract=信息真源、live entry=适配面。前置工序：附加段回归源 → 渲染模板化（_publish_single_agent 复制改渲染 + manifest renderTemplate/extraSections）→ 派生校验落 check_items

## 四、员工对象发布 × 员工合约

CEO 提示成立（三方一致确认）：发布方向由**员工契约链**覆盖——contract v3 paths / runtime_baseline + HostObjectSetDefinition 声明面（live_entry_status/host_stage/live_entry_ref）+ binding-profiles liveEntry + live manifest liveEntries，四层承载。剩余语义面（binding 边界、live entry 唯一性）均为契约一致性校验，可落 DCE check_items，非自由裁量。

**不保留第二道 CHO 门**：审批只设在决策点（上岗：编制合理性/职责边界），执行点只做契约校验——重复审批是产品噪音。

## 五、FADE 衔接

- ADE-A：FADE-002 扩容（建议更名"公司发布管理 FADE"或维持原名加范围说明），补齐 runId 显式化、文件/Git 事件触发、Score CLI/Skill 试卷评分、Close CLI 落位；逐段工件 + 评分通过记录（v1.1.0 必要条件）
- ADE-B：FADE-004 扩容，补对象发布段工件（生成/binding/委托/治理回填）+ 试卷评分
- spec §六 案例表四行合并为两行指向两个 FADE 文档；fade-registry 候补区 employee_host_publish 条目迁入 FADE-004；两份实例试卷（固定文档 + 实例声明 + 测试集）

## 六、风险与不可合并边界

不可合并（§6.1 + 小狄四类）：目录扫描 vs manifest 域、语义候选链、声明面渲染 vs 复制、审批门在决策点。

**两处合同级缺口 = 整合前必修（阶段 0）**：

1. **employee_host_publish 安全默认违例**：无 `--dry-run`/`--execute` 时默认执行写入（`execute = not args.dry_run`，employee_host_publish.py 第 101-102 行），违反 §2.4"默认不写入"——改默认 dry-run + `--execute` 显式
2. **`--publish-agents` 白名单缺反向禁区校验**：`_publish_single_agent` 只比对 source/target 哈希，未见 PROTECTED_TARGET_PATTERNS 反向校验；manifest 被污染时白名单照单执行——补"白名单 ∩ 禁区 = ∅"硬校验 + manifest 变更走 Close CLI 审计

其余：保护边界双层结构（CLI 硬编码禁区管"不能写哪" + manifest 白名单管"谁有资格"）本身正确，补反向校验即闭环；委托 publish-agents 保持 dry-run 不擅自 auto-write；双域执行体只共享合同/审计 schema。

## 七、执行顺序

| 阶段 | 内容 | 性质 |
| --- | --- | --- |
| 阶段 0 | 修两处合同级缺口（安全默认 + 白名单反向校验） | 可独立先行，合规修复 |
| 阶段 1 | 统一报告合同（envelope + scope_specific） | 报告层收敛 |
| 阶段 2 | 生命周期骨架统一（runId / Close CLI / 试卷评分） | ADE 升格主体 |
| 阶段 3 | 文档与登记册落位（spec §六、fade-registry、candidate-staffing-fade.md 扩容、两份试卷模板、code-state/product-state 同步） | 收尾 |

## 八、决策记录

- 2026-08-19 CEO：采纳 2-ADE 方案，落本文档
- 2026-08-19 CEO 追加：① 本提案 syncMode 定调 follow-spec（随 ade-pattern-spec.md 联动发布，文档体系串链，FADE 源发布才完整）；② Trees 任务树融合（spec §8.6）——检测即触发、编排层建树多员工参与、触发与执行解耦（小赛等维护 Agent 只负责开启触发条件，不绑定执行）；③ 触发链补 daemon 层——定时巡检链（cron 唤起小赛巡检→写入周平面待办标注闲时执行→daemon 与小贾定期取任务自动执行，对应 §8.1 durable）／即时触发链（指令→小赛立即触发→小贾建树，对应 §8.2 interactive），spec §8.6 已落位
- 前置条件沿用周平面 FADE-ASSESS-20260818-001 口径：文档关系梳理清楚后启动，阶段 0 两处缺口修复不属返工范围（合规修复）

## 贡献点标注

- 小乔（产品语义）：语义裁决三档与 syncMode 档位开关、候选 3 按调用上下文双归属、不保留第二道 CHO 门（审批只在决策点）、避免另立 FADE-005
- 小狄（技术合同）：main() 三分支事实整合证据、统一报告合同 envelope 方案、两处合同级缺口定位（安全默认 101-102 行、白名单反向校验漏洞）、子命令化低优先建议
- 小贾（牵头）：七维框架、FADE-002/004 扩容路径、员工契约链四层覆盖证据、目录扫描 vs manifest 域边界、FADE 衔接与补齐项口径
