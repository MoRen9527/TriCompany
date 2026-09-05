<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-002/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-002 产品版——功能面、工作流与使用旅程

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-002/02-product-guide.md
- syncMode: source-only
- lastSyncedAt: 2026-09-05

读者：要**使用/协作**这条管线的人（改真源的员工、发布窗口的规划与联审角色、运维值班），
以及想判断"它值不值得依赖"的评审者。不需要读代码。
前置：已读 [小白版](01-beginner-guide.md)（或已懂 真源/dry-run/manifest 三概念）。

---

## 一、模块导读四要素

| 要素 | 内容 |
| --- | --- |
| **定位** | FADE-002"公司文档管理"实例（登记册历史代号**发布域**）：TriCompany 源侧 → 发布侧的确定性同步管线，一个 CLI 管三类资产、两个宿主面+一个会话面 |
| **成熟度** | **已实现并在役**：三业务 scope DCE、生命周期骨架（run-id/Score CLI/Close CLI）、event-watch 检测面、三宿主发布、校验套件 180 项全绿（2026-09-05 实测）。**人工态/待增强**：Plan Skill 与 Close Skill 仍是人工联审（manifest `adeLifecycle` 如实标注 `lifecycle-pending`）、文件/Git 事件**自动写入**增强挂 automation-backlog |
| **真源路径** | 协议 `docs/engineering/fade-protocol-spec.md`；登记册 `docs/engineering/fade-registry.md`（FADE-002 条）；规范 `docs/workflow/project-source-document-sync-ade.md`；执行体 `runtime/cognition/source_publish_check.py`；清单 `.github/manifests/project-source-doc-sync-manifest.json`（均在 TriCompany 仓） |
| **常见误区** | ① 直接改发布面文件（会被下次发布覆盖且无审计）；② 把 `partial` 当故障（等摘要候选=常态）；③ 把 event-watch 的顶层 status 当业务检查结果（它只报触发面健康度）；④ 以为机器会写摘要内容（永不，必须候选喂入） |

## 二、功能面全景

一个 CLI（`python -m runtime.cognition.source_publish_check`），五类能力：

**三类资产业务 scope**

| scope 命令 | 管什么 | 写入开关 |
| --- | --- | --- |
| `--check`（+`--sync`） | 兼容目录扫描域：按目录扫源/发布两侧漂移（hash/git/codegraph/JSON 语义四路 diff） | `--sync` |
| `--project-docs` | **项目真源文档**：manifest 驱动，逐条目核对——CLAUDE.md/AGENTS.md（字节复制类）、tricompany.md 等两份摘要类 | `--project-docs-execute` |
| `--publish-agents`（+`--host`） | **员工/registry 定义发布**：源侧定义 → 各宿主 live 入口 | `--agent-execute` |

**一个 `--host` 参数，三种宿主面**（多宿主渲染模型：未来加宿主=注册表加一条，流程零改动）

| host | 落点 | 形态 |
| --- | --- | --- |
| `copilot`（默认） | `.github/agents/` | 字节保真复制 |
| `claude` | `.claude/agents/` | 渲染（工具名映射+白名单+派生标记） |
| `claude-session` | `.claude/hub/<id>.session.md` | 会话变体渲染：合成件正文+M-001 公共段+会话补充段，无 frontmatter |

**两个生命周期/触发面 scope**（复用同一份报告合同）

- `--close`：终态收口 CLI——校验裁决/证据/run-id/版本四输入，全过才写终态审计文件，不过则 `CLOSE_REJECTED` 非零退出。
- `--event-watch` / `--watch`：文件指纹∪Git HEAD/refs 轮询（默认 30 秒），变更→去重→派生 scope 自动跑 dry-run 检查、审计落 `.ade/event-watch/`。检测与建议自动，**写入永远要人显式给 `--auto-sync`**，且 project-docs 永不自动写。

**两段评分收口**：`--score`（确定性覆盖检查，输出评分合同）+ 联审语义评分（Score Skill），合成双门槛判定（必选项全过∧总分≥阈值）。

## 三、使用旅程

### 旅程 A：发布一份项目真源文档（以 CLAUDE.md 为例）

这是最常走的路。2026-09-04 深夜 LG-028"CLAUDE.md 真源减法"实战走的就是这条路。

```
[改内容的人]        [规划/联审]              [执行]                  [收口]
改真源文件    →   小贾规划候选      →    dry-run 预检       →    核对小票
(TriCompany/       (摘要类才需要；        --project-docs            execute
 docs/project-      字节复制类免)          （只看不改）              --project-docs-execute
 sources/…)    →   小乔核产品语义   →    确认 planned_*     →    复核 in_sync
               →   小狄核版本与安全门     逐条清单                 逐字节零终验
                                              ↓
                                     两仓各留 commit + envelope 小票（run_id 可溯源）
```

关键点：

- **字节复制类**（CLAUDE.md/AGENTS.md）：`in_sync` = 复印件与真源指纹一致，无事发生；
  有差异则 dry-run 报 `planned_update`，execute 后变 `updated`。
- **摘要类**（tricompany.md、dynamic-task-tree-protocol.md 两份）：目标过期时机器报
  `requires_candidate`，**等小贾把候选喂进来**（`--project-doc-candidate 条目ID=候选文件路径`）。
  候选文件头部必须带四项元信息（sourceOfTruth 指回真源 / syncMode / sourceRevision 指纹 /
  lastSyncedAt），机器逐项校验，一项不对就拒收。
- **验收口径**：发布域的"完成"以逐字节比对为准——2026-09-04 有过一次教训：
  用"行数一致"当判据放行了带排版漂移的发布面，当晚返工并把判据改成立法级
  "逐字节比对为唯一判据"（详见[深度研究版](04-deep-research.md)字节漂移案）。

### 旅程 B：发布员工定义到宿主面（--publish-agents）

场景：某员工的源侧五件套/合成件改了（岗位调整、域知识更新），要把变更送到运行面。

1. **检查**：`--publish-agents --host claude`（默认 dry-run）→ 报告逐条给
   `derived_drift`（渲染结果与 live 现状漂移）或 `derived_identical`（一致）。
   注意 claude 面比的不是"文件等不等于源"，是"文件等不等于**渲染(源+模板)**"——
   因为 live 文件是派生加载壳，天生和源长得不一样。
2. **执行**：加 `--agent-execute`（可加 `--employees` 只发某人；`--run-id` 给本次运行
   起可读名字，如 `lg024-batch2-rdt-render`，事后审计按名索骥）。
3. **宿主差异自然发生**：同一次发布，copilot 面走字节复制（`skipped_identical`），
   claude 面走渲染（`derived_identical`）——一份源、两张面孔，各是各的正确。
4. **会话面**（claude-session）：只对 manifest 里声明了 `sessionBody` 键的条目生效，
   其余条目在该面零行为；渲染正文=合成件全量+全席公共段（M-001 状态条合同，运行时
   从纪律册正身抽取注入）+该席会话补充片段，尾附"禁人工编辑"派生标记。

### 旅程 C（值班视角）：event-watch 巡检

daemon/cron 定期唤起 `--event-watch`（单次）或 `--watch`（循环）：

- 无变化 → 单条 `deduped`，连日志都不写（防噪音）；
- 有变化 → 一条批次记录 + 各 scope 自动 dry-run + 建议（变更数≥阈值或含关键文件才建议 sync）；
- 顶层 `status` **只回答"巡检这一趟健康吗"**——业务上的 partial（如等候选）不会顶上来，
  否则巡检天天误报。业务细节在 `scope_specific` 里分层看。

## 四、为什么敢托付（三道安全门 + 一套审计）

1. **默认不写**：三个业务 scope 全部 dry-run 起步；写入必须显式配对开关（`--sync` /
   `--agent-execute` / `--project-docs-execute`），开关与 scope 绑死，错配直接报错。
2. **禁区硬编码**：员工五件套（soul/memory/colleagues/social/body）、binding profiles、
   live 入口被写死在 CLI 保护清单；发布白名单落在禁区=整轮否决（不是跳过，是拒绝）；
   路径逃逸（绝对路径/盘符相对/`..` 越界）在解析层直接拒。
3. **单写者纪律**：每个宿主面只有管线自己是合法写入者（翻转逻辑：授权落区之外全是禁区）。
4. **全程小票**：每次运行输出 envelope（协议报告合同）：七字段基座 + 守恒不变量
   （`total == changed + skipped + errors`，校验套件强制）+ 退出码契约（有 error → 非零，
   CI 可感知）。`--run-id` 让每次运行可命名、可引用。

## 五、价值主张（对组织回答"为什么要它"）

- **可控**：写什么、写到哪、谁批准，三件事分别在 manifest/保护链/联审记录里，全部版本化。
- **可审计**：任何一次发布，凭 run_id 能拉出当次小票+两仓 commit；凭 hash 能证明"发布后发布面与真源逐字节一致"。
- **可扩展**：新宿主=渲染注册表加一条；新文档=manifest 加一个条目；管线本体零改动。
- **省人**：确定性环节（比对、复制、校验、记账）机器全包，人只做语义决策（写什么、批不批）——这是"13 名 AI 员工的定义能一晚全量重渲上线"的前提。

## 六、诚实边界（用前必读）

- **已实现**：上文全部命令与安全门（校验套件 180 项，2026-09-05 全绿实测）。
- **人工态**：Plan Skill / Close Skill 未结构化装载——发布窗口的规划与终裁由人（小贾/联审）承载，manifest `adeLifecycle` 字段如实标注 pending，不是缺陷是现状。
- **待增强**：文件/Git 事件的**自动写入**挂 automation-backlog（CTO 2026-08-21 裁决）；检测面已落地。
- **历史档提示**：`docs/workflow/project-source-document-sync-ade.md` §7 的报告形状是 envelope 立位前的旧合同，现行以协议 §2.2 与代码为准；读旧规范先看版本行。

## 七、验证方式（学完自测）

1. 跑 `--project-docs`（dry-run）：能说出 4 个条目各自的 action 与原因。
2. 跑 `--publish-agents --host claude-session`（dry-run）：观察哪些条目有行为、哪些零行为，能说出"零行为"的判定条件（manifest 有无 sessionBody 键）。
3. 跑校验套件 `python -m unittest runtime.cognition.source_publish_check_validation`：全绿（当前基线 180 项）。
4. 口测：向同事复述旅程 A 全流程不卡壳，并指出两道最关键的门（dry-run 默认 / 禁区整轮否决）。

## 使用依据

- 命令面：`source_publish_check.py` `build_parser` L3033-3286（全部参数定义实读）；宿主注册表 L174-226；保护清单 L47-103
- 功能语义：协议 `fade-protocol-spec.md` §2.2（envelope 合同）/§2.4（安全门）/§6.1（发布域条目）/§8.6（event-watch）；登记册 FADE-002 条（评分 90→93）
- manifest：`project-source-doc-sync-manifest.json`（4 条目+notes 三条克制条款）
- 成熟度标注：manifest `adeLifecycle` 字段原文；automation-backlog 裁决见登记册 FADE-002 补齐项
- 旅程 A 实战底本：2026-09-04/05 LG-028 第二步发布窗（TriMetaverse commit fe60f355/82babd95，台账镜像 `.fade/hub-snapshots/ledger-mirror.md`）
