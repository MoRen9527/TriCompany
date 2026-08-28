# FADE-003 共学周记深度教程：一条 runId 如何走到 98/100 升完整档

> - 教程性质：技术研发新人接手培训材料（非事实裁决，真源见文末「使用依据」）
> - 教学对象：要接手 `journal-cli.mjs`、共学周记规范与 FADE-003 registry 条目的研发新人
> - 版本基准：2026-08-29（升档完成日）；所有 hash/行号/数字均用 Read 从仓库实取，引用格式为 `文件:行号`
> - 涉及仓库：`D:/Code/ai/TriMetaverse`（执行体+审计+规范）、`D:/Code/ai/TriCompany`（协议+registry+试卷卷宗）

---

## 一、培训判断与学习路径

### 1.1 这篇教程解决什么问题

FADE-003（共学周记记录）在 2026-08-29 完成了一次完整的「兼容档 → 完整档」升档。这个实例的特殊价值在于：它是全部 FADE 实例里**唯一一个把「评分段从无到有建出来、并立刻用真实 run 跑完首评」的全过程留了完整审计链**的案例。读完本篇，你应该能：

1. 复述 FADE 十段协议在 003 实例的逐段落地载体（到 file:line 粒度）；
2. 接手 `journal-cli.mjs` 六个子命令（begin/init/qualify/append/score/close）的代码与退出码契约；
3. 讲清 W34 违规 → D-06 立纪律 → 80 卡线 → 降档标注 → 升档 98/100 这条故障弧线；
4. 独立在沙箱里复跑六分支 E2E。

### 1.2 学习路径

| 步 | 读什么 | 验证方式 |
| --- | --- | --- |
| 1 | 本篇 §二（大结果） | 能一句话说出 003 现在的档位和三条证据 |
| 2 | `ade-journal-recording-spec.md` 全文（v1.1） | 能背出四问 Q1-Q4、五查 C1-C5、终态词表 |
| 3 | 本篇 §三-§四（十段落地 + CLI 走读） | 对照源码 `journal-cli.mjs` 逐行读完一遍 |
| 4 | 本篇 §五-§六（运行证据 + 故障弧线） | 打开 `journal-run-log.jsonl` 逐行核对 15 行 |
| 5 | 本篇 §七（卷宗对照） | 并排打开两份卷 JSON 对照读 |
| 6 | `fade-protocol-spec.md` §2.5-§2.8 + 本篇 §八 | 能说出 §2.8 细则 10 是什么 |
| 7 | 本篇 §九，动手跑沙箱六分支 | 六个退出码全部复现 |

---

## 二、先讲大的结果：FADE-003 现在是什么

一句话：**共学周记记录是 TriCompany 的 FADE-003 完整档实例**——把「对话中出现值得沉淀的大模型使用经验 → 追加进当周共学周记」这个动作，做成「agent 负责判断与撰写、CLI 负责格式与落点、评分与收口由确定性代码守门」的全生命周期链。

升完整档（registry `fade-registry.md:88`、`:110`）的三条支柱证据：

1. **载体落地**：`TriMetaverse/scripts/journal/journal-cli.mjs` 新增 score 子命令（S1-S7 确定性覆盖）+ close 三态扩值 + revision 授权域 + logRun 告警，单 commit `17649d7d` 落地（W35 `daily-progress.md:26`）；
2. **首评实跑**：首个真实 run `7a85e3e0`（W35 周记条目 2.2）全链 begin→qualify→append→score→close，score **PASS 98/100**（S 80/80 满分地板 + W 18/20），close APPROVED（`journal-run-log.jsonl:11-15`）；
3. **卷宗与登记**：升格卷 `FADE-003-paper-upgrade.json` 双 hash `5220091c45c16b04b0159b3cfac0598d548da494c8f013f38c24a278d4750cf9` 冻结（TCO `9b0b378`），registry 升完整档（TCO `9393893`）。

在此之前它是兼容档：首评 **PASS 80/100 卡线**（2026-08-20，`FADE-003-score-2026-08-20.json:115-122`），2026-08-28 被 CEO 判定「非标准 FADE 流程」成立、降档标注（TCO `3d1c45a`，`daily-progress.md:43`）。升档后降档标注**撤销但保留为历史档案**（registry `:88`），这个「历史不抹掉、只标注」的做法本身就是要学的治理习惯。

---

## 三、协议十段在 FADE-003 的逐段落地形态

FADE 协议十段（`fade-protocol-spec.md:95`）：事件触发 → 登记 → Qualify → Plan Skill → DCE → Verify(可选) → Score CLI → Score Skill → Close Skill → Close CLI → 终态。下表是 003 的逐段对照，随后逐段展开。规范真源 = `ade-journal-recording-spec.md`（下称「周记 spec」），执行体 = `journal-cli.mjs`（下称「CLI」），路径省略前缀 `D:/Code/ai/TriMetaverse/`。

| 段 | 003 载体 | 关键证据 |
| --- | --- | --- |
| 事件触发 | prompt 手动入口；cron 自动待 resident | 周记 spec `:19`、registry `:92` |
| 登记 | CLI `begin` 生成 runId + run-log 落行 | CLI `:132-149` |
| Qualify | agent 语义四问 + CLI 机械资格 | 周记 spec `:46-53`、CLI `:182-191` |
| Plan Skill | 格式三查 + 草拟 entry.json 七字段 | 周记 spec `:57-62`、CLI `:54` |
| DCE | CLI `qualify`→`append` 固定格式写入 | CLI `:87-107`、`:193-250` |
| Verify | 可选段，未启用（职能并入 Score/Close） | registry 段表 `:92-100` 无 Verify 行 |
| Score CLI | CLI `score --run`，S1-S7 确定性覆盖 | CLI `:350-466` |
| Score Skill | W1-W4 语义四维 + 双席抽验 | 周记 spec `:98`、registry `:97` |
| Close Skill | agent 三态裁决 + note | 周记 spec `:84-92` |
| Close CLI | CLI `close`，裁决校验 + 五查 + 终态 | CLI `:252-332` |
| 终态 | APPROVED / ESCALATED / RETRY（+BLOCKED 结构态） | 周记 spec `:111-116` |

### 3.1 事件触发：人是触发源，自动化挂账

事件 =「对话中出现可沉淀内容，或 CEO 指令“记入周记”」（周记 spec `:36`）。手动入口是 `.github/prompts/项目级 AI 共学周记.prompt.md`（固定格式真源，Copilot-host 可直调）；cron 自动触发**明确待 resident 能力**（registry `:92`），按 FADE-002 先例「手动/指令触发列增强项、不影响档位」（方案包 `fade-003-upgrade-review.md:98`）。注意这里没有纸面法：触发自动化的缺口挂的是 automation-backlog 增强项，不是谎称已接线。

### 3.2 登记：begin 生成 runId，四不变量怎么满足

`cmdBegin`（CLI `:132-149`）做三件事：解析当周（`resolveCurrentWeek`，`:33-48`）、同题预检（`:137-140`，命中则 `ESCALATED` 退出码 3，提示「修订走 CEO 明确指令，勿重复登记」）、生成 runId：

```js
const runId = randomUUID().slice(0, 8);   // CLI :141
```

然后 `logRun({ action: 'begin', runId, week, title, dupHint })`（`:142`）写入审计。对照协议 §2.8 登记段四不变量（`fade-protocol-spec.md:241`）：

- **唯一性**：一次运行一个 8 位 runId，后续所有段按它聚合；
- **去重性**：begin 同题预检 + append 二次同题去重（`:227-229`）双保险；
- **关联性**：run-log（`journal-run-log.jsonl`，路径定于 CLI `:24`）按 runId 过滤即得全链（`:153`、`:271`、`:355`）；
- **恢复锚**：run-log 行带 week/entryNo/title/path，断点可定位现场。

协议正文在 §2.8 合法载体示例里**点名**了这一形态：「journal runId（共学周记）」（`fade-protocol-spec.md:253`）。

### 3.3 Qualify：语义四问（agent）+ 机械资格（CLI）双层

语义层是四问（周记 spec `:46-53`）：Q1 可复述、Q2 有产出、Q3 可对外、Q4 有共学价值（纯内部工程台账不入册）；任一问不确定 → ESCALATED 请 CEO 裁决。机械层是 `cmdQualify`（CLI `:182-191`）：七字段结构检查（`loadEntry`，`:65-75`，title 超 60 字也拦）+ 脱敏扫描（`:77-84`）。三条出口：

- 结构不完整 → `REJECTED` 退出码 1（`:187`）；
- 命中脱敏 → `ESCALATED` 退出码 3，交 agent/CEO 裁决语义脱敏（`:188`）；
- 全过 → `QUALIFIED`（`:189`）。

**S5 立法的关键**：QUALIFIED 判定必须落 run-log 行（裁定 5）——W35 的 append BLOCKED 样本实证了「不入链 = 链上无凭」的风险，见 §5.2。

脱敏扫描表只有两条正则，值得背下来：

```js
const SENSITIVE_PATTERNS = [                                   // CLI :60-63
  [/sk-[A-Za-z0-9]{16,}/, '疑似 API key（sk-…）'],
  [/(api[_-]?key|secret|password|token)\s*[:=]\s*["']?[A-Za-z0-9_\-]{12,}/i, '疑似凭据赋值'],
];
```

### 3.4 Plan Skill：格式三查 + entry.json 七字段

Plan 段做格式三查 P1（周记 spec `:57-61`）：必读 prompt 固定格式、归档 README、**最近一个已存在周**的周记（禁止跨多周翻旧模板——W34 违规正是栽在这一条，见 §六）。落点 P2 = 当周目录 `project-ai-community-weekly-YYYY-Wnn.md`。P3 只追加不重写，v1.1 增补豁免：「评分驱动的 RETRY 修订——限本次 run 产出条目且须 run 链 revision 行授权，他人/已签发条目绝对禁区」（`:62`）。

entry.json 七字段定义在 CLI `:54`：

```js
const FIELDS = ['title', 'phenomenon', 'detail', 'solution', 'impact', 'projExp', 'modelSelfCheck'];
```

对应渲染标签 `FIELD_LABELS`（`:55-58`）：现象/具体表现/解决方案/问题影响/项目经验/模型自查。

### 3.5 DCE：格式由代码保证，不靠 agent 纪律

DCE 段是 `append`（普通路径 `:223-250`）：定位插入点（最后一个 `### 2.n` 之后、下一个 `##` 级标题之前；无条目则插到「## 2.」节标题后，`:233-245`），用 `renderEntry`（`:87-107`）把 JSON 渲染成固定五件格式，`bumpSyncedAt`（`:126-129`）同步文件头日期，写盘后输出 `APPENDED: <路径> 条目 2.n「标题」`（`:248`）。周记 spec `:145` 对这段的定性是 DCE 确定性成立的根：「格式由 CLI 代码保证（JSON 进、固定结构出），不依赖 agent 纪律」。

### 3.6 Verify：可选段的诚实空缺

协议里 Verify 是可选段（`fade-protocol-spec.md:245`）。003 没有单列 Verify 载体——registry 段表（`:92-100`）干脆没有 Verify 行。这不是遗漏而是口径：结构/路径/脱敏的后置校验职能由 Score CLI 的 S1-S6 承担，落盘持久化由 Close 五查的 git 项承担。对照 FADE-006 映射表里「可选段未启用（诚实空缺——不凑段）」（registry `:164`）同一口径。

### 3.7 Score CLI：score --run 的 S1-S7

升档新增段，CLI `:350-466`，逐项走读见 §4.5。协议定位：「Score CLI 检查测试集覆盖（确定性遗漏检测）」（`fade-protocol-spec.md:87`），产物为 §2.6 评分合同。

### 3.8 Score Skill：W1-W4 语义四维

四个维度各 0-5 分（周记 spec `:98`）：W1 现象捕捉、W2 解决方案可操作性、W3 影响面真实度、W4 经验提炼 + **对外口径双判问**（通用性、无内部黑话、无内部台账形态——这条把立册反模式「commit 索引入册」变成了评分判据）。载体是撰写 agent 自评 JSON（`--skill-json` 传入，CLI `:438-444`），evidence_ref 要求用 2.n 内原句引文。**判定人独立性**：首 3 个功能期 run 双席抽验（registry `:97`）——组织者利益声明在册，因为 FADE-003 执行体含本席，自证风险结构性存在（方案包 `:53`）。

### 3.9 Close Skill：校验者之前的语义终裁

agent 读回追加结果 + 评分 JSON，做三查（准确性/对外口径/无误伤，周记 spec `:84-92`），输出三态裁决 `approved | escalated | retry` + note。首评 run 的真实 note 见 run-log `:15`：「升档首评：score 全链 PASS（素材=LG-012 crash loop 潜伏损坏诊断），W 自评 18/20 双席抽验在案」。注意升档联审校准过一点：Close Skill **并非缺位**（W35 双判实跑在案），升档增量是「裁决输入含 score JSON + 程序化三态」（方案包 §十一 `:120`）。

### 3.10 Close CLI：裁决的校验者，不是发起者

`cmdClose`（CLI `:252-332`）。核心原则一句话（周记 spec `:144`）：「Close CLI 是裁决的**校验者**而非发起者」——`--verdict` 只接受 Close Skill 的合法值，机械查不过时即使 agent 裁 approved 仍会改判。三态扩值、RETRY 前置、程序化改判的实现细节见 §4.6。

### 3.11 终态

词表三态 APPROVED / ESCALATED / RETRY + 结构态 BLOCKED（周记 spec `:111-116`）。v1.1 词表统一：原 `APPENDED` 终态值并入 `APPROVED`（`:113`）；存量 run-log 里的 W34 `CLOSED` 行历史冻结不动（append-only + 不溯及既往，方案包 `:78`）。

---

## 四、journal-cli.mjs 五子命令全解（正典链与 runId 贯穿）

正典链（周记 spec `:129-138`）：

```text
begin（登记，生成 runId）→ qualify（机械资格）→ append（写入 2.n）
→ score（S1-S7 + W 合并）→ close（校验裁决 + 五查 → 终态）
→ 审计：journal-run-log.jsonl（runId 贯穿 begin→qualify→append→score→close）
```

### 4.0 全局骨架

- **路径解析**（CLI `:20-24`）：`RECORDS_ROOT` 默认 `<repo>/docs/workflow/operating-records`，可被环境变量 `TRIMV_JOURNAL_ROOT` 整体覆盖（`:12`、`:21-22`）——这是沙箱隔离的唯一开关，§九全靠它。
- **周解析**（`:33-48`）：扫 `2026-Wnn` 目录，读各目录 `OP-*.json`，`status==='active' || latestActiveWeek===true` 者为 active；无 active 则回退最大周号。坏 index 跳过不炸（`:43`）。
- **logRun 审计**（`:109-119`）：每次动作 append 一行 JSON 到 run-log。升档裁定⑦改了它的失败语义——写失败**不再抛错**，改为 stderr 告警 + 模块级 `AUDIT_LOG_ERROR` 变量，最终记进 score envelope 的 `audit_log_error` 字段（`:456`）。为什么？原实现里审计写失败会让 qualify 行缺失，进而 S5 判 FAIL——**用审计故障冤枉好 run**。改后审计故障与业务判定解耦，故障本身仍可见（envelope 字段 + stderr）。
- 一个容易迷惑的细节：`logRun` 头部兜底生成随机 runId（`:113`），但 spread 的 `...rec` 在后面——所以 begin/qualify/append/close 都显式传 `runId`（没传则记 `null`），唯独 `init` 不传（`:178`），于是 run-log 里 init 行的 runId（如 `dde77db9`）是一次性随机值，**不属于任何执行链**。看到它别当成链断了。

### 4.1 begin：登记

```
node journal-cli.mjs begin --title "条目标题"
```

同题已存在 → `ESCALATED: 同题条目已存在（…）——修订走 CEO 明确指令，勿重复登记`，退出码 3（`:143-146`）。正常输出两行：`RUN <runId> week=<周>` 和周记文件绝对路径（`:147-148`）。**这个 runId 要一路带到 qualify/append/score/close 的 `--run` 参数**——它是正典链的缝合线。

### 4.2 init：建当周草稿骨架

```
node journal-cli.mjs init
```

当周文件已存在 → `BLOCKED` 退出码 2（`:159`）——**这是正常路径不是错误**（周记 spec `:115`：BLOCKED「属于正常路径，建后转 APPROVED」）。新建骨架含元信息三行（sourceOfTruth/syncMode: audit-record/lastSyncedAt）+ 记录人行 + 「## 2.」节标题（`:162-176`），骨架保持最小，内容按条目增量生长（反模式第四条，周记 spec `:123`）。

### 4.3 qualify：机械资格

```
node journal-cli.mjs qualify --entry entry.json --run <runId>
```

判定顺序（`:182-191`）：先报结构问题（`FAIL <字段>`），再报脱敏命中（`SENSITIVE <标签>`）；结构问题 → `REJECTED` 退出码 1；脱敏 → `ESCALATED` 退出码 3；全过 → `QUALIFIED`。语义四问不在此判——「语义四问仍归 agent」（`:189`）。

### 4.4 append：写入与 revision 授权域

普通路径：文件不存在 → `BLOCKED` 退出码 2（先 init）；同题已存在 → `BLOCKED-dup` 退出码 2（去重，提示「如需修订走 CEO 明确指令」）；成功 → `APPENDED` 退出码 0。

revision 路径（升档裁定 2① 落地，`:196-222`）：

```
node journal-cli.mjs append --entry entry.json --run <runId> --revision <entryNo>
```

机器校验逻辑（`:198-204`）：从 run-log 取出**同 runId** 的链，必须找到 `action==='append' && verdict==='APPENDED' && entryNo===目标` 的先行行，否则：

```console
REJECTED: revision 越权——runId <id> 链上无 entryNo=<n> 的 APPENDED 行（仅本 run 产出条目可 revision）
```

退出码 1。合法则把原 `### 2.n` 条目整段（到下一 `###` 或 `##` 边界，`:209-215`）替换为重渲染文本，输出 `REVISED`。这就是「P3 评分修订豁免」的代码化：**修订权 = 本 run 产出 + 链上授权行**，他人条目/已签发内容在机器层就改不了，不靠自觉。

### 4.5 score：S1-S7 确定性覆盖 + W 合并

```
node journal-cli.mjs score --week 2026-W35 --run <runId> [--json] [--skill-json w.json]
```

**条目定位**（裁定 S5 补强细则，`:359-363`）：取链上**最近一行 APPENDED** 的 entryNo+title，在周记里定位对应条目块（`entryBlocks`，`:335-348`）。这保证了多 run 多条目的周记里，score 永远评「本次 run 写的那条」。

七项检查与权重（满分 80）：

| 项 | 检查内容 | 权重 | 实现要点 | 行号 |
| --- | --- | --- | --- | --- |
| S1 | 本次 2.n 五件结构逐件解析 | 20 | 七个前缀逐个找（现象/具体表现/解决方案/问题影响/项目经验/模型自查/当前经验），标签后首个非空行即内容；遇下一标签/「当前经验」/「##」边界或 EOF 仍空 → 记缺失 | `:365-385` |
| S2 | 元信息头 + lastSyncedAt 为当日 | 10 | 三正则：`## 文档同步元信息`、`sourceOfTruth:`、`- lastSyncedAt: <今日>` | `:387-390` |
| S3 | 落盘路径在当周目录 | 10 | 路径前缀校验（与 Close C-1 同源） | `:392-394` |
| S4 | 同题去重 + 2.x 序号唯一 | 10 | 全周标题集零重复 + entryNo 零重复；**断号只发 `seq_gap_warning` 不计分**（裁定 5：断号可能是历史删除，不该罚本次 run） | `:396-403` |
| S5 | run 链完整 | 15 | begin 在链 + **qualify 判 QUALIFIED 在链** + append APPENDED 在链——「QUALIFIED 必须入链」是裁定 5，W35 append BLOCKED 样本实证必要性 | `:405-409` |
| S6 | 脱敏复核 | 5 | **对落盘后的条目文本重扫**（qualify 扫的是 entry.json，防止「json 干净、落盘时被改脏」的窗口） | `:411-415` |
| S7 | 守恒基线（只追加不重写） | 10 | 见下 | `:417-434` |

S7 值得单独讲。期望集来自 **run-log 全历史**的 APPENDED/REVISED 行，按 entryNo 取最新 title：

```js
for (const r of allLog) {
  if (r.action === 'append' && (r.verdict === 'APPENDED' || r.verdict === 'REVISED') && r.entryNo != null) {
    expected.set(r.entryNo, { title: r.title, runId: r.runId });      // CLI :420-423
  }
}
```

然后三方对账：期望集里的条目若在文件中缺失或标题变了（且不是本 run 的 revision 授权域条目，`:428` 显式跳过）→ `changed_others`；文件里有、run-log 里从没登记过的条目 → `unregistered`。任一非空 → S7 FAIL。**这一项把 P3「只追加不重写」从纪律变成了机器可判定的守恒律**——绕过 CLI 手改周记、改别人条目、塞未登记条目，全会在评分层暴露。

**W 合并与双门槛**（`:436-446`）：`--skill-json` 提供 `{w1..w4}` 各 0-5（越界 clamp），`total = S合计 + W合计`；判定：

```js
const allPass = items.every((i) => i.pass);
const verdict = allPass && (total === null || total >= 90) ? 'PASS' : 'FAIL';   // CLI :445-446
```

即双门槛：S1-S7 全过（必选）且总分 ≥90。90 这个数是联审修正——原方案包提案 80（`:58`），双席裁定改 90：「S 满分 80=地板，W≥10=最小裁判权——80 卡线史是教训不是基准」（周记 spec `:99`、升格卷 threshold note）。**接手者注意一个宽容路径**：不传 `--skill-json` 时 total=null，门槛退化为 S 全过即可 PASS。CLI 无法强迫 agent 提交 W——「W≥10 最小裁判权」在 W 缺席时靠流程约束（首评实跑提交了 W 18/20）。别用这个口子绕开语义评分，双席抽验会抓。

输出两轨：`--json` 出 envelope（`:449-458`，`protocol: 'journal-score'`，`threshold: { must_pass: 'S1-S7', total_min: 90 }`，含 `audit_log_error`）；人读轨逐项 `PASS S1 20/20（证据路径）` + 汇总行。**无论 PASS/FAIL 退出码都是 0**（`:465`）——评分高低是业务结果走 RETRY 状态机，只有工具/IO 故障才非零（方案包 `:42`）。

### 4.6 close：三态扩值 + RETRY→APPROVED 前置 + 程序化改判 + 五查

```
node journal-cli.mjs close --week 2026-W35 --run <runId> --verdict approved --note "…"
```

**裁决词表三态**（`:266-269`）：

```js
const verdictNorm = (verdictArg ?? '').toLowerCase();                  // 大小写归一
const VALID = ['approved', 'escalated', 'retry']; // 三态（FROZEN 留口正名后扩值——2026-08-28 裁定）
```

四个要点：

1. **三态而不是方案包提的四态**：合成裁定把 `frozen` 从输入词表拿掉了——「无场景的态=纸面态」（细则 10，registry `:107`）。协议 §8.3 家族里有 FROZEN，但 003 当前没有「签发归档冻结」的真实场景，先留口正名后扩值，避免立一条永远没人走的纸面法。输入 `frozen` 现在被拒、退出码 1（E2E 第六分支就是测这个）。
2. **RETRY→APPROVED 前置机器校验**（裁定 2②，`:276-285`）：agent 裁 approved，但链上存在 RETRY 终态行时，必须在其后存在**同 runId 的 score PASS 行**（比较 ts），否则 `REJECTED` 退出码 1，note 记 `approve-precondition-fail`。「重评必经」由此从口头纪律变成可机器复放的时序断言。
3. **程序化三态改判**（裁定 8，`:286-293`）：agent 裁 approved 但链上最近一行 score 是 FAIL（且无后继 PASS）→ CLI 直接把有效裁决改成 retry 并打印 NOTE。「校验者非发起者」在这里反向发力：agent 也不能把不达线的 run 送进 APPROVED。
4. **收口五查**（`:309-325`）：C-1 路径在当周目录 / C-2 条目五件结构 / C-3 元信息+记录人行 / C-4 lastSyncedAt 为今日 / C-5 git 已提交（`git status --porcelain -- <文件>`，非 git 环境按 FAIL 处理 `:323-324`）。加上带 `--run` 时的 C-0（run 链完整）与 C-0b（裁决合法在案），registry 升档记录里写的「C-0..C-5 全过」就是这七个（registry `:110`）。

退出码全景：`REJECTED` 1（词表非法/前置不满足）/ `BLOCKED` 2（文件不存在）/ `ESCALATED` 3（agent 裁 escalated，或五查未全过——`:328` `verdict = all ? 'APPROVED' : 'ESCALATED'` 退出 1）/ `RETRY` 4 / `APPROVED` 0。

一个规范与代码的编号错位要心里有数：周记 spec §2.6 的五查是 C4=git、C5=回报 CEO（`:105-109`），代码把「元信息在」与「lastSyncedAt 为今日」拆成了 C-3/C-4，git 是 C-5；「回报 CEO」是会话行为不可机查，留在会话侧（原卷 notes 也如实标注过这一点）。以代码为准机查，以规范为准流程。

### 4.7 六子命令退出码速查

| 命令 | 0 | 1 | 2 | 3 | 4 | 64 |
| --- | --- | --- | --- | --- | --- | --- |
| begin | 正常 | — | — | 同题 dup ESCALATED | — | — |
| init | 新建 | — | 已存在 BLOCKED | — | — | — |
| qualify | QUALIFIED | 结构 REJECTED | — | 脱敏 ESCALATED | — | — |
| append | APPENDED/REVISED | 越权/结构 REJECTED | 无文件/同题/目标缺失 BLOCKED | — | — | — |
| score | PASS 或 FAIL（评分不动 rc） | 未捕获异常 | 文件缺失 BLOCKED | — | — | — |
| close | APPROVED | REJECTED/五查不过 | BLOCKED | ESCALATED | RETRY | 用法错误 |

### 4.8 append --revision 的三分支（沙箱测过）

1. 越权（链上无该 entryNo 的 APPENDED 行）→ REJECTED 退出码 1；
2. 链上有授权但文件里找不到 `### 2.n` 标题 → `BLOCKED: 找不到条目 2.n（revision 目标缺失）` 退出码 2（`:211`）；
3. 合法 → 整段替换 + bumpSyncedAt → REVISED 退出码 0。

---

## 五、本周真实运行证据（全部仓库核验）

### 5.1 journal-run-log.jsonl 全景：15 行

实读 `D:/Code/ai/TriMetaverse/docs/workflow/operating-records/项目级 AI 共学周记/journal-run-log.jsonl`，当前 15 行，三段历史：

| 行 | runId | action/verdict | 时刻（UTC Z 原值） | 要点 |
| --- | --- | --- | --- | --- |
| 1 | 0f1a4035 | qualify **ESCALATED** | 2026-08-18T03:34:41Z | hits=["疑似 API key（sk-…）"]——脱敏扫描真实命中样本 |
| 2 | fa623b3d | close **CLOSED** | 2026-08-18T03:35:00Z | W34 终态，旧词表；无 begin/append 行（孤儿链） |
| 3-10 | 541da30c (+dde77db9) | 完整链双判 | 2026-08-25T07:59-08:00Z | 见 §5.2 |
| 11-15 | **7a85e3e0** | 升档首评全链 | 2026-08-28T16:26-18:38Z | 见 §5.2/§5.4 |

注意：方案包 §十一（2026-08-29 备料时点）如实写「run-log 实 10 行」（`:119`），修正了备料时按 registry 旧注记误写的「2 行」；首评 run 又追加了 5 行，现在是 15 行。**引用审计行数必须带时点**，这是本仓反复交过学费的教训（方案包 §十一整节就是干这个的）。

### 5.2 三条 run 的故事

**W34 孤儿链（行 1-2）**：只有 qualify 和 close 两行，缺 begin/append——因为当时链路还没跑完整或未入链。原卷因此把 run-chain 项按证据不足扣到 3/10（`FADE-003-score-2026-08-20.json:92-102`）。行 1 的 ESCALATED 反而是个**正面样本**：`sk-` 形态真实命中、机械拦下。行 2 的 `CLOSED` 是旧词表，历史冻结不改（不溯及既往）。

**W35 双判链 541da30c（行 3-10）**：完整跑出了 close 的双判机制——08:00:28Z 第一次 close 判 **ESCALATED**（agentVerdict 仍是 approved，note 四问全过），19 秒后 08:00:47Z 第二次 close 判 **APPROVED**。这正是「机械查不过时即使 agent 裁 approved 仍 ESCALATED」的实跑证据（周记 spec `:144`）；第一次败在哪个 C 查，log 行未记——按当时实现最可能是 C-5 git 未提交（推断，非行内实证），补提交后过。这条链同时贡献了 S5 的立法样本：行 5 是 append **BLOCKED**（当周文件还不存在），紧接着行 6 dde77db9 init 建骨架、行 7 重新 qualify QUALIFIED、行 8 才 APPENDED——如果没有行 7 的 QUALIFIED 入链，「资格检查过没过」就无从机器回放了。

**升档首评 7a85e3e0（行 11-15）**：begin（16:26:12Z，标题「内存存活掩盖重启必炸——dist 生产形态服务的潜伏损坏与诊断路径」）→ qualify QUALIFIED（16:26:13Z）→ append APPENDED entryNo=2（18:37:14Z，中间 2 小时是草拟与修订）→ **score PASS subtotal_s=80, total=98**（18:38:46Z）→ close APPROVED（18:38:47Z，agentVerdict approved）。首评对象就是周记里 `project-ai-community-weekly-2026-W35.md:34-50` 的条目 2.2，素材来自当日 LG-012 复盘（TriMC restart 崩循环，`daily-progress.md:20`）。

### 5.3 commit 链与双仓记账

升档一周内的 commit 链（全部核验自 W35 `daily-progress.md`，TMV=TriMetaverse 仓、TCO=TriCompany 仓）：

| commit | 仓 | 内容 | 出处 |
| --- | --- | --- | --- |
| `caeec035` | TMV | 升档方案包 `fade-003-upgrade-review.md`（LG-013 备料） | `daily-progress.md:51`、`:25` |
| `3d1c45a` | TCO | 降档标注 FADE 兼容档 + 升完整路线五项（08-28） | `daily-progress.md:43` |
| `17649d7d` | TMV | **D0+1 实现窗**：journal-cli score 子命令 + close 三态扩值（retry 退出码 4）+ RETRY→APPROVED 前置机器校验 + revision 授权域 + logRun 告警；周记 spec v1.1 | `daily-progress.md:26` |
| `9b0b378` | TCO | **升格卷冻结**：双 hash `5220091c…750cf9`，载体定版同盘 | `daily-progress.md:26`、registry `:110` |
| `9393893` | TCO | **registry 升完整档** + 兼容档标注撤销（留历史档案） | `daily-progress.md:27` |

另外原卷 notes 里记着 W34 周记的提交 `83f2c1a9`（`FADE-003-paper.json:8`）。**声明**：以上 hash 均转录自仓库内台账文件（本任务无 git 执行权限，未跑 `git log` 复核对象库）；台账与 registry 双处一致，可信度足够接手学习，但接手后第一次动这个仓时建议顺手 `git log --oneline` 对一遍。

### 5.4 首评 98/100 的数字拆解

run-log 行 14：`{"action":"score","verdict":"PASS","subtotal_s":80,"total":98,"omission":false}`。拆开：

- S 侧：80/80 满分地板——S1(20)+S2(10)+S3(10)+S4(10)+S5(15)+S6(5)+S7(10) 全过，omission=false；
- W 侧：18/20（close note「W 自评 18/20 双席抽验在案」，run-log `:15`；哪一维扣了分，evidence_ref 在会话侧自评表，仓库内未落独立文件——这是当前审计的真实边界）；
- 98 ≥ 90 双门槛过 → PASS → close APPROVED。

## 六、故障弧线与教训（D-06 关联）

### 6.1 五幕弧线

1. **事故（2026-08-18）**：W34 周记首次写入违规——跳过规范查找、按任意旧周模板（W29，隔了 4 周）自创「理论小节」结构、塞入内部 commit 索引表（周记 spec 反模式 §三 `:118-123`，每条都是实录）。
2. **立纪律 + 立规范（同日）**：工程纪律 **D-06** 立册（`TriCompany/docs/workflow/engineering-disciplines.md:56-58`：「记入周记/共学」类动作先查规范再动笔，五件结构/当周目录/只追加不重写/台账不入册）；共学周记 ADE 规范 v1.0 立册，触发事件就写明是这次违规（周记 spec `:9`）。
3. **首评 80 卡线（2026-08-20）**：按当时试卷评 PASS 80/100，必选 6/6，但 run-chain 只有 3/10（孤儿链证据不足），且 registry 还做过一次描述修正——把「run log 完整审计链」的失实表述修正为「完整 run 链待补证」（registry `:108-109`）。**评分诚实，档案才可信。**
4. **降档标注（2026-08-28，`3d1c45a`）**：v2.0.2 逐段对照，CEO 判定「非标准 FADE 流程」成立（registry `:106`）。降档依据五项：Score CLI/Score Skill 双段缺失（**质量评价缺位=W34 首写违规 D-06 的制度根源**）、Verify 缺失、触发手动化、终态两态分辨率不足、Qualify 自判无独立裁判。注意措辞——不是「agent 犯错」而是「制度根源」：只有格式纪律、没有评分门槛时，违规只能靠人肉发现。
5. **修后放行 + 首评升档（2026-08-29）**：方案包（`caeec035`）→ 双席修后放行 + 一处分歧裁（升格卷 freeze.authority）→ 实现窗（`17649d7d`/`9b0b378`）→ 沙箱 E2E 六分支全绿 → 首个真实 run 7a85e3e0 全链 98/100 → registry 升完整档（`9393893`）。

### 6.2 D-06 在这条弧线里的两重角色

D-06 既是弧线的**起点**（事故直接产物），又升档后依然是**活纪律**——registry FADE-003 条目「纪律」行至今挂着它（registry `:104`）。区别在于执行层变了：D-06 立册时靠「先查规范再动笔」的自觉，升档后五件结构/当周目录/只追加/脱敏全部有 S1-S7 与五查机器兜底。教训可以浓缩成一句：**纪律管第一次，评分管每一次。**

### 6.3 同源事件的双通道分流（Q4 边界活教材）

首评条目 2.2 的素材（LG-012 TriMC restart 崩循环）同时进了两条通道：工程纪律 **D-03 v3**（dist 形态服务 restart 前置检查两项 + 重检出后必须重建 dist，`engineering-disciplines.md:33`）和共学周记 2.2（诊断路径叙事）。为什么分流？D-03 是内部行为规则（纪律通道），周记 2.2 提炼的是「运行中≠可重启」这种对一切用 AI 做项目的人可复用的经验（Q4 共学价值）。同一事件、两个出口、各自守边界——这就是 Q4「纯内部工程台账不入册」的正确打开方式。

### 6.4 联审修正清单九条（落点锚定）

双席「修后放行」共提出九条修正。联审裁定正本在会话侧台账，仓库内可复核的是每条的**落点锚**——接手时按这张表反查即可：

| # | 修正 | 方案包原稿 | 落定形态与证据 |
| --- | --- | --- | --- |
| 1 | 阈值 80 → **90**（S 满分地板 80 + W≥10 最小裁判权；「80 卡线史是教训不是基准」双席一致） | §四 提案 ≥80（`:58`） | 升格卷 threshold（`FADE-003-paper-upgrade.json:76-81`）；周记 spec `:99`；CLI `:446`/`:455` |
| 2 | RETRY 修一：**RETRY→APPROVED 前置**机器校验（retry 行后同 runId 须有 score PASS 行） | §五 状态机（无此断言） | CLI `:276-285`；升格卷 approve_precondition `:85` |
| 3 | RETRY 修二：**程序化三态改判**（agent 裁 approved 不达线 → 校验者裁 RETRY） | §五（无此分支） | CLI `:286-293`；升格卷 close_skill `:86` |
| 4 | RETRY 修三：**revision 授权域**（本 run 条目 + APPENDED 行授权，越权 REJECTED） | §五（仅「同 runId」一句） | CLI `:196-222`；周记 spec P3 豁免 `:62`；升格卷 T7 `:65` |
| 5 | 词表四态提案 → **三态**，FROZEN 留口正名后扩值（细则 10：无场景的态=纸面态）+ 大小写归一 | §六 提案四态含 frozen（`:76`） | CLI `:266-269`；registry `:107`⑤；升格卷 `:83`/`:87` |
| 6 | 试卷冻结时点 = **载体定版 commit 同盘**（双 hash 于冻结 commit 消息与登记册留痕，不入卷内防自引用） | §七 提案（`:95`） | 升格卷 freeze `:5-11`；`9b0b378`；hash `5220091c…` |
| 7 | logRun 吞错改 stderr 告警 + envelope `audit_log_error`（防审计写失败让 S5 误判 FAIL 冤枉好 run） | 未涉及 | CLI `:109-119`/`:456`；升格卷 audit `:89-91`（裁定⑦） |
| 8 | S5 补强：**QUALIFIED 必须入链**（W35 append BLOCKED 样本实证必要性）+ S1 逐件解析 + S4 断号告警不计分 | §二 表（S5 只有 begin+append） | CLI `:405-409`/`:365-385`/`:396-403`；升格卷 T5 `:47-54` |
| 9 | 事实补录三条校准（合成裁定 9）：run-log 实 10 行非 2 行 / Close Skill 非缺位（校准为「升档增量=裁决输入含 score JSON+程序化三态」）/「close 仅扩词表」校准为「close 增分支不重构」 | 全文多处旧表述 | 方案包 §十一 `:117-121`；升格卷 close_skill `:86`；代码实证（close 实增 retry 分支+前置校验，`:276-307`） |

这张表本身就是一份「如何读联审文档」的教学材料：**方案包是提案、裁定是合同、代码是落点**——三者的差异处（80→90、四态→三态）正是联审真正的决策内容。

---

## 七、评分卷宗解读：升格卷 vs 原 80 卡线卷

两份卷都在 `D:/Code/ai/TriCompany/docs/engineering/fade-papers/`。**它们不是同一张考卷的两次考试，而是两种不同层次的考卷**——这是理解升档的一把钥匙。

### 7.1 原 80 卡线卷（FADE-003-paper.json + score JSON）

- **考什么**：实例工件的存在性与质量——「这个 FADE 实例建得好不好」。一次性评分，2026-08-20 定格（`FADE-003-score-2026-08-20.json:122`，`scored_at 2026-08-20T04:29:25Z`）。
- **结构**：10 项 × 各 10 分 = 100，阈值 80；其中 6 项必选（trigger-config / run-id-carrier / skill-docs / cli-report / audit-record / terminal-sample，卷 `:12-65`），4 项可选（格式三查 / 脱敏扫描 / run 链 / 收口五查，卷 `:66-101`）。
- **得分明细**（score JSON 逐项）：trigger-config 9、run-id-carrier 8、skill-docs 9、cli-report 8、audit-record 9、terminal-sample 10、format-three-check 7、sensitive-scan 10、**run-chain 3**、five-check-close 7 → 合计 80，`required_all_passed=true`，80≥80 卡线 PASS。
- **最低项 run-chain 3/10** 的扣分理由写在卷 notes 与 verify_method 里：「本机仅 qualify+close 两条——证据不足如实扣分」（卷 `:91`）。这条 3 分项就是后来 S5（权重还升到 15）的直接前身——**扣分项变立法**是这份卷最有教学价值的读法。
- notes 三条全是「如实」样本：run-log 缺 begin/append 扣分、W34 终态样本带 commit `83f2c1a9` 在案、cron 自动触发如实标注待 resident（卷 `:6-10`）。

### 7.2 升格卷（FADE-003-paper-upgrade.json，v1.0-frozen）

- **考什么**：`scoreable_run` =「自然周记 run：begin→qualify QUALIFIED→append APPENDED→score→close 全链同 runId；W34 后首个真实 run 起适用」（卷 `:12`）——**每次 run 的覆盖与质量**，不是实例的一次性体检。
- **结构**：T1-T8 权重 100 = Score CLI 承载的 T1-T7（即 S1-S7：20/10/10/10/15/5/10）+ Score Skill 承载的 T8（W1-W4 各 5，卷 `:18-75`）。
- **双门槛**：必选 T1-T7 全过（omission=0；S 满分 80=地板）+ 总分 ≥90（W≥10=最小裁判权；「权重与阈值同盘冻结」，卷 `:76-81`）。
- **冻结三要素**（卷 `:5-11`）：Plan 时点冻结（=载体定版时点，静态固化域口径——FADE-001 扩维卷/FADE-003 升格卷「同一原则两投影」）、双 hash `_fadehash.dual_sha256` canonical（raw+LF，行尾漂移按 SOFT-DRIFT 留痕）、authority=联审合成裁定。**双 hash 不入卷内**——防自引用（考卷自己给自己作证的悖论），hash 留在冻结 commit 消息与 registry 升档条目里。
- **honesty 条款**（卷 `:93`）：「Score 实跑=对真实 run 的评分（首跑待 W35/W36 自然 run）；journal-cli 改版沙箱 E2E……为载体质量门，两者层次不同，禁混同宣称」。

### 7.3 两卷对照的五处关键演进

| 维度 | 原 80 卷 | 升格卷 | 为什么改 |
| --- | --- | --- | --- |
| 考试对象 | 实例工件存在性（一次性） | 每个 run 的全链覆盖+质量（持续） | 评分要管每一次执行，不是一次验收 |
| run 链 | 可选项 10 分，实评 3/10 | T5 必选 15 分，QUALIFIED 必须入链 | W34 孤儿链 + W35 BLOCKED 样本的制度回应 |
| 阈值 | 80（卡线 PASS） | 90 = S 满分地板 + W≥10 | 80 卡线史是教训不是基准 |
| 冻结 | 无（时点未立法） | 载体定版同盘 + 双 hash | spec v2.0.3 试卷 Plan 时点冻结立法（`fade-protocol-spec.md:187-193`） |
| 诚实边界 | notes 如实标注 | 独立 honesty 字段（E2E 禁混同） | 细则 10 立法完成度自我适用 |

### 7.4 评分合同对照（模板 §三 vs journal-score envelope）

协议规定 Score CLI 输出 §2.6 评分合同、与载体无关（`fade-protocol-spec.md:118`），模板合同见 `fade-assessment-paper-template.md:72-83`。003 的 `score --json` envelope（CLI `:451-458`）是这份合同的实例化投影，字段语义同构但形态有四处差异，接手者对表：

| 模板合同 | journal-score envelope | 说明 |
| --- | --- | --- |
| `verdict: "PASS\|FAIL"` + `status` | `status`（承载 PASS/FAIL）+ 顶层 `protocol:"journal-score", version, mode:"score"` | 003 合一字段、增协议头 |
| `total: {score, max, threshold}` | `total`（数）+ `threshold: {must_pass:"S1-S7", total_min:90}` | 003 把双门槛拆成显式对象 |
| `items[].required` | 无（S1-S7 全为必选，等价 required=true） | 必选集在 threshold.must_pass 表达 |
| `required_all_passed` | `summary.omission`（+逐项 `omission`） | 语义相同：必选全过判定 |
| — | `w_scores`、`audit_log_error`、`summary.items_total` | 003 增补：W 合并、审计故障透传、守恒对账（items_total=7） |

判定语义完全同构：模板「PASS ⇔ required_all_passed=true 且 total.score ≥ threshold」（模板 `:85`）≈ 代码 `allPass && total>=90`（CLI `:446`）。协议 §2.8 细则 3 给了这种差异合法性：产物合同层封闭可校验，载体层开放由映射表声明。

---

## 八、与 FADE 协议 v2.0.0（§2.7/§2.8）对照

### 8.1 §2.7 节点收口报告：为什么 003 豁免

§2.7（`fade-protocol-spec.md:195-223`）要求多节点任务包的每个节点落 `reports/node-<NODE-ID>.md` 十字段收口报告。registry v1.2 注记明确豁免口径：「节点收口报告仅适用多节点树实例——001/002/003 单段脚本/CLI 实例豁免，004 HTTP 链多节点按段适用」（`fade-registry.md:17`）。003 是单段 CLI 实例：一次 run 只有一个执行单元，无节点可收。但 §2.7 的两大职能（断电恢复 + 审计）在 003 有等价物——run-log 行的 week/entryNo/path 充当恢复锚，action/verdict/ts 链充当审计。**豁免的是载体形式，不是职能不变量。**

### 8.2 §2.8 十段合同逐行对照

§2.8 的分层立法是「协议管不变量，实例管载体」（`fade-protocol-spec.md:227-234`）。003 逐段对账：

| 段 | 协议不变量（spec `:236-249`） | 003 载体与证据锚 |
| --- | --- | --- |
| 事件触发 | 可重放、可归因 | prompt 手动入口+CEO 指令；归因=周记 spec `:36` 事件定义（cron 待 resident，如实标注） |
| 登记 | 四不变量：唯一/去重/关联/恢复锚 | begin+runId+run-log（§3.2 已逐条对过）；协议正文点名「journal runId」（`:253`） |
| Qualify | 机械可判定或语义判定留痕（细则 9 profile 限定） | 双层：语义四问留痕（run-log verdict 行）+ 机械 qualify 门 |
| Plan | 结构化计划+试卷声明（第三件 Plan 时点冻结件，v2.0.3） | 静态固化域映射声明：「Plan 时点=载体定版时点」（周记 spec `:11`/`:140`）；升格卷冻结即试卷冻结 |
| DCE | 确定性、可复现、结构化自检 | append 渲染（JSON 进固定格式出）+ run-log APPENDED 行 |
| Verify | 可选 | 未启用，职能并入 S1-S6 与五查（诚实空缺，§3.6） |
| Score CLI | 覆盖遗漏检测确定性可复算 | S1-S7 全部可离线复放：输入=周记 md + run-log，无随机无网络 |
| Score Skill | 逐项语义分 + evidence_ref | W1-W4，evidence_ref=2.n 内引文；首 3 run 双席抽验 |
| Close Skill | 语义终裁引用评分证据 | 三态裁决+note，输入含 score JSON（run-log `:15` 实证） |
| Close CLI | 终态持久化 + 合同校验（§2.5） | cmdClose 词表/前置/五查 + run-log 终态行 |

### 8.3 运行标识与细则 6

细则 6（`fade-protocol-spec.md:262`）：「被评分卷宗/周检报告/跨实例战役引用的 run 必须可被单一显式标识引用」。7a85e3e0 被升格卷 `scoreable_run` 与 registry 升档记录（`:110`）引用——8 位 runId 就是那个单一显式标识，且 run-log 15 行随时可机器回放验证。

### 8.4 细则 10 立法完成度的自我适用

细则 10（v2.0.2 正式法条，`:266`）：「接线（执行路径真实存在）+ 实测（模拟或真跑证伪过）才算立法完成」，未接线的一律是纸面法。003 升档全程是这条法条的**自我示范**：

1. 方案包开篇自我声明「本包为纸面方案件；Score 实跑未发生，禁在实施前宣称档位变化」（`:11`）；
2. 实现后先做沙箱 E2E（载体质量门），但明确「两者层次不同，禁混同宣称」（升格卷 honesty `:93`）——E2E 绿了**仍不算**评分实跑；
3. 直到首个真实自然 run 全链 PASS，registry 才落「升完整档」（`:110`）。纸面法清单（registry `:172-178`）至今对 003 无挂账条目。

---

## 九、沙箱 E2E 六分支（接手者第一课）

隔离开关只有一个：环境变量 `TRIMV_JOURNAL_ROOT`（CLI `:12`、`:21-22`）——`RECORDS_ROOT`/`SPEC_DIR`/`RUN_LOG` 全部由它派生，沙箱里怎么折腾都不碰真周记。六分支与代码锚：

| # | 分支 | 操作 | 期望 | 代码锚 |
| --- | --- | --- | --- | --- |
| 1 | score PASS | 合法链跑完后 `score --week <周> --run <id> --json` | status=PASS，rc=0 | `:446`/`:465` |
| 2 | retry | `close --verdict retry` | 终态 RETRY，rc=4 | `:301-307` |
| 3 | 前置 REJECTED | 链上有 RETRY 行后无 score PASS 行，`close --verdict approved` | REJECTED rc=1，note=approve-precondition-fail | `:276-285` |
| 4 | revision 三分支 | `append --revision`：越权 / 目标缺失 / 合法 | REJECTED rc=1 / BLOCKED rc=2 / REVISED rc=0 | `:201-205`/`:211`/`:216-221` |
| 5 | APPROVED | approved + 五查全过 | 终态 APPROVED，rc=0 | `:328-331` |
| 6 | FROZEN | `close --verdict frozen` | 词表拒绝 REJECTED，rc=1（留口未扩值） | `:266-269` |

复跑要点（PowerShell）：

```powershell
$env:TRIMV_JOURNAL_ROOT = "D:/tmp/journal-sandbox"
node D:/Code/ai/TriMetaverse/scripts/journal/journal-cli.mjs init
node D:/Code/ai/TriMetaverse/scripts/journal/journal-cli.mjs begin --title "沙箱条目"
# 用返回的 runId 依次 qualify / append / score / close
```

三个沙箱搭建注意（机制推导，接手时自行验证）：其一，省略 `--week` 时 `resolveCurrentWeek` 依赖 OP index 文件，沙箱里建议**一律显式 `--week`**；其二，五查的 C-5 在非 git 目录按 FAIL 处理（`:323-324` 的 catch 分支），要复现「APPROVED exit0」需让沙箱周记处于已提交干净状态（如沙箱本身建为独立 git 仓）；其三，别忘 `Remove-Item Env:TRIMV_JOURNAL_ROOT` 收尾，否则后续真跑会写进沙箱。

---

## 十、接手任务与常见误区

**常见误区**：

1. 手改周记 md 不走 append/revision → S7 报 `changed_others`/`unregistered`，评分 FAIL；
2. 把 init 的 BLOCKED 退出码 2 当故障——它是正常路径（周记 spec `:115`）；
3. close/score 忘带 `--run` → score 的 S5 必 FAIL（`:408` 要求 runIdArg），close 走旧五查分支绕过了 run 链校验——升档后正典必须 `--run`；
4. score 不传 `--skill-json` 钻 total=null 的宽容路径 → 流程上 W≥10 是最小裁判权，双席抽验会抓；
5. 把沙箱 E2E 全绿说成「已评分/已升档」——违反升格卷 honesty 条款与细则 10；
6. 把 run-log 里 init 行的随机 runId（如 dde77db9）当成断链；
7. 引用 run-log 行数不带时点（备料时 10 行、首评后 15 行都是真的，时点不同）。

**文档卫生观察（接手后顺手项，报秘书处而非自行改）**：周记 spec 头部 lastSyncedAt 仍为 2026-08-18（`:7`）而 v1.1 内容日期是 2026-08-29（`:11`）；registry 头部版本 v2.1/08-28（`:7-9`）未随 08-29 升档记录 bump。冲突时以条目内容+commit 链为准。

**合理的接手任务**：复跑沙箱六分支作为熟悉代码的第一课；cron 触发自动化（automation-backlog，002 先例不影响档位）；FROZEN 场景真实出现（README 签发归档冻结）时做「正名后扩值」；把 W 自评表从会话侧落为仓库工件（当前 W 的 evidence_ref 链在仓库内不可独立复核，是已知审计边界）；W35/W36 后续自然 run 继续积累双席抽验样本（首 3 run 常设）。

---

## 十一、使用依据

本教程全部事实取自以下文件（Read 实取，未凭记忆）：

- `D:/Code/ai/TriMetaverse/scripts/journal/journal-cli.mjs`（489 行全文：子命令、S1-S7、退出码、行号引用）
- `D:/Code/ai/TriMetaverse/docs/workflow/operating-records/项目级 AI 共学周记/ade-journal-recording-spec.md`（v1.1：§2.5/§2.6/终态/反模式/执行链路）
- `D:/Code/ai/TriMetaverse/docs/workflow/operating-records/项目级 AI 共学周记/journal-run-log.jsonl`（15 行实态逐行）
- `D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W35/project-ai-community-weekly-2026-W35.md`（条目 2.1/2.2）
- `D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W35/daily-progress.md`（commit 链：caeec035/3d1c45a/17649d7d/9b0b378/9393893/83f2c1a9 线索、E2E 六分支、LG-012 素材）
- `D:/Code/ai/TriMetaverse/docs/execution/fade-003-upgrade-review.md`（方案包+§十一事实补录+修正落点）
- `D:/Code/ai/TriCompany/docs/engineering/fade-registry.md`（FADE-003 条目 `:88-110`：完整档标题/段表/历史档案/路线销账/升档记录）
- `D:/Code/ai/TriCompany/docs/engineering/fade-papers/FADE-003-paper-upgrade.json`（升格冻结卷：freeze/T1-T8/threshold/state_machine/honesty）
- `D:/Code/ai/TriCompany/docs/engineering/fade-papers/FADE-003-paper.json` 与 `FADE-003-score-2026-08-20.json`（原 80 卡线卷与评分明细）
- `D:/Code/ai/TriCompany/docs/engineering/fade-protocol-spec.md`（§1.1/§2.5/§2.6/§2.7/§2.8、细则 1-10、生命周期图）
- `D:/Code/ai/TriCompany/docs/engineering/fade-assessment-paper-template.md`（§三 评分输出合同）
- `D:/Code/ai/TriCompany/docs/workflow/engineering-disciplines.md`（D-06 `:56-58`、D-03 v3 `:33`）

**诚实声明**：本任务无 git 执行权限，commit hash 全部转录自上述台账文件（双处交叉一致）；两处推断已显式标注（541da30c 首次 close 的败项最可能是 C-5、沙箱搭建注意为机制推导）。本教程是培训材料，不是事实裁决——冲突时回到上述真源。
