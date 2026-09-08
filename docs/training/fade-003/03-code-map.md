<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-003/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-003 代码版——journal-cli.mjs 实现地图

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-003/03-code-map.md
- syncMode: source-only
- lastSyncedAt: 2026-09-09

读者：要接手 `journal-cli.mjs` 的工程师。
纪律声明：本文锚点为 **2026-09-09 对 489 行现行版实读**（`TriMetaverse/scripts/journal/journal-cli.mjs`，下称 CLI）。行号漂移防护同前三单：语义优先，接手先 `git log --oneline` 再按符号重定位。
前置：已读 [产品版](02-product-guide.md)。

---

## 一、培训判断与命令族总览

学完本篇你应能：①画出一条 runId 的完整审计链形状；②指认 qualify 三出口/close 五查/score 七项的实现行；③说清"机器两处否决 agent"的精确代码条件；④跑通一条沙箱 run（或读通一条历史 run）。

```text
node journal-cli.mjs <command> [args]
  init                                   # 建当周草稿骨架（active 周由 OP index 判定）
  begin --title "…"                      # 领 runId + 同题去重提示
  qualify --entry <json> --run <runId>   # 机械资格：结构+脱敏（三出口）
  append --entry <json> --run <runId> [--revision <n>]  # 固定格式渲染 2.n
  score --week <周> --run <runId> [--json] [--skill-json <自评>]
  close --week <周> --run <runId> --verdict <approved|escalated|retry> --note "…"
```

三要素贯穿：**entry.json**（七字段输入，agent 拟）/ **week**（当周目录落点）/ **runId**（审计链主键，`logRun` 每步写 `journal-run-log.jsonl`）。

## 二、领号与建草稿（cmdBegin L132 / cmdInit L156）

- `cmdBegin`：生成 runId+**同题去重提示**（dupHint 写进日志不硬拦——硬拦在 append 的 BLOCKED-dup）；`logRun({action:'begin', …})` 开链。
- `cmdInit`：当周文件不存在时建**最小骨架**（元信息+记录人行+第 2 节标题）——实案 dde77db9：541da30c 的 append BLOCKED 后由它解围。骨架最小是规矩，内容按条目生长。

## 三、qualify 机械门（cmdQualify L182-191）——三出口

```text
结构不完整 → REJECTED   exit 1（agent 补字段重来）
脱敏命中   → ESCALATED  exit 3（agent/CEO 裁决；scanSensitive L77 扫描，实案 0f1a4035 拦"疑似 API key（sk-…）"）
全过       → QUALIFIED  （入链；score 的 S5 要求 QUALIFIED 必须在链上）
```

两个出口都 `process.exit(非零)`——**CLI 是门，不是建议箱**。

## 四、append 上版（cmdAppend L193-250）——只追加铁律的实现

- **revision 链**：`--revision <n>` 修订路径要求 run 链上存在该 entryNo 的既有 APPENDED 行（L200 prior 检查），否则 REJECTED——**修订权绑定本 run 的产出史**，他人/已签发条目从代码层就改不了。
- **BLOCKED-dup**（L228）：同题条目已存在 → exit 2，提示"如需修订走 CEO 明确指令"。
- **BLOCKED**（L225）：当周文件不存在 → exit 2 提示先 init。
- 成功路径：`renderEntry`（L87，JSON→固定五件文本）+ `nextEntryNo`（L121 自动编 2.n）+ `bumpSyncedAt`（L126 同步文件头）→ `APPENDED` 入链。

## 五、close 五查（cmdClose L252-330）——两处机器否决 agent

**否决一（L290-293）**：`--verdict approved` 但链上最近 score=FAIL →
`effective='retry'`，终端打 "agent 裁 approved 但评分未达线——校验者裁 RETRY"，exit 4。

**否决二**：run 链不完整（begin/qualify/append 不齐，L273）→ 即使 agent 裁 approved 仍
**ESCALATED**（L276-283 一带，exit 3）——实案 541da30c 双判弧的第一判。

**五查原文**（APPROVED 前置，`verdict = all ? 'APPROVED' : 'ESCALATED'`，exit 0/1）：

| # | 查 | 实现 |
| --- | --- | --- |
| 1 | 落盘路径在当周目录 | `p.includes(join(RECORDS_ROOT, week))` |
| 2 | 条目五件结构 | 正则抓 `### 2.n`+两组标签全文匹配（现象/具体表现/解决方案/问题影响+项目经验/模型自查） |
| 3 | 元信息+记录人行 | `## 文档同步元信息`+`sourceOfTruth:`+`> 记录人：` 三正则 |
| 4 | lastSyncedAt 为今日 | 当日日期精确正则 |
| 5 | git 已提交 | `git status --porcelain -- <file>` 为空（非 git 环境降级=false 如实报） |

RETRY→APPROVED 前置（L276-279）：retry 行之后、同 runId、存在 score PASS 行——重评必经，机器可校验。

## 六、score 七项（cmdScore L350-473）——权重表与精确语义

定位细则（S5 补强裁定）：评分对象=runId 链上**最近 APPENDED 行的 entryNo+title** 对应条目（L369-373），不是"最新一条"——防串号。

| 项 | 权重 | 查什么 | 行锚 |
| --- | --- | --- | --- |
| S1 五件结构 | 20 | 本次 2.n 逐件解析（bodyAfter 逐前缀取正文） | L365/L385 |
| S2 元信息当日 | 10 | 文件头 sourceOfTruth+lastSyncedAt | L390 |
| S3 落盘当周 | 10 | 路径含当周目录 | L394 |
| S4 去重+序号唯一 | 10 | 同题 dup 列表；序号断号=警告不计分（seq_gap_warning） | L403 |
| S5 run 链完整 | 15 | begin+QUALIFIED+APPENDED 在链（QUALIFIED 必须入链） | L409 |
| S6 脱敏复扫 | 5 | **落盘条目文本重扫**（进门扫过的再扫一遍落盘态） | L415 |
| S7 守恒基线 | 10 | 非 run 产物条目 diff 零变化；期望集=run-log 全历史 APPENDED/REVISED 最新 title | L417/L434 |
| 合计 | **80** | （地板） | |

**W 合并与 verdict 精确语义（L438-446，接手最易误读处）**：

```js
total = S 合计 + Σ clamp(w1..w4, 0, 5)      // --skill-json 提供；各 0-5 防越界
verdict = allPass && (total === null || total >= 90) ? 'PASS' : 'FAIL'
```

- W **合并后**：双门槛强制（S 全过 ∧ total≥90）。
- W **未合并**（不给 --skill-json）：`total===null` 通道——机检 PASS 即 PASS，但输出明示"W 未合并——总分门槛 90 含 W≥10"。**W≥10 的地板是流程性约束**（Close Skill 语义裁决+首 3 功能期 run 双席抽验），CLI 不强制——接手者要分清"代码强制"与"流程约束"两层，改这里前先读升档联审裁定原文。
- `audit_log_error` 字段（L456 envelope）：审计写失败=stderr 告警+字段带出——**防 S5 因审计自身故障误判 FAIL 冤枉好 run**。
- 输出双形态：`--json` 合同（protocol: journal-score, threshold 字段）人读两用。

## 七、审计合同（logRun L110 + jsonl）

- 每步一行 JSON：`{runId, ts, action, verdict, week?, entryNo?, title?, path?, subtype?, agentVerdict?, note?}`——字段随 action 增减，runId 恒在。
- 生命周期动作枚举：begin/init/qualify/append（含 subtype: revision）/score/close；verdict 词表见 spec §2.7 三态+REJECTED/BLOCKED 族中间态。
- 审计文件本体=`docs/workflow/operating-records/项目级 AI 共学周记/journal-run-log.jsonl`——**读它就是读流水线的监控录像**（新人第一课，同小白版）。

## 八、接手任务清单（第一周）

1. 读 audit jsonl，任选 runId 拼全程并按 §五/§六 表逐行指认实现。
2. 沙箱跑一条最小 run（自建测试周目录+假 entry.json：begin→qualify→append→score）——**勿在真 W36/W37 目录试 append**（只追加铁律对真条目生效）。
3. 手验两处机器否决：构造"score FAIL 后 close --verdict approved"看降级 retry 输出（沙箱）。
4. 读 close 五查五正则与 score S1 的 bodyAfter 解析——格式判定的全部实现就在这些正则里，改格式=改正则=改合同（须同步 prompt 真源与 spec）。
5. 读 spec §2.5 升档裁定原文再动 score——W 门槛的"代码强制 vs 流程约束"分层是本 CLI 最敏感的一处。

**误区速查**：把 BLOCKED 当失败（它是缺前置的信号）／绕过 revision 链手改条目（S7 会抓）／把 W 未合并 PASS 当"满分通过"（envelope 明示门槛含 W）／对审计文件手工增删行（S5/S7 的期望集就是它，改它=改证据）。

## 使用依据

- CLI 全函数锚：journal-cli.mjs 489 行（2026-09-09 实读：L77/L87/L110/L121/L126/L132/L156/L182/L193/L252/L290-293/L334/L350/L365/L385/L390/L394/L403/L409/L415/L417/L434/L438-473）
- 审计标本：journal-run-log.jsonl（0f1a4035/541da30c/dde77db9/7a85e3e0 原行）
- 规范裁定：ade-journal-recording-spec.md v1.1 §2.5/§2.6/§2.7；登记册 FADE-003 升档记录
- 卷宗：fade-papers/FADE-003-paper-upgrade.json（98 分卷双 hash 冻结）
