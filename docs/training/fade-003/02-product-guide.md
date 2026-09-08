<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-003/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-003 产品版——记一条周记的完整旅程

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-003/02-product-guide.md
- syncMode: source-only
- lastSyncedAt: 2026-09-09

读者：要**记周记/审周记/维护这条流水线**的人——任何收到"记入周记"指令或自主判断有可沉淀
内容的 agent，以及审阅周记的 CEO/双席。前置：已读 [小白版](01-beginner-guide.md)。

---

## 一、模块导读四要素

| 要素 | 内容 |
| --- | --- |
| **定位** | FADE-003"共学周记记录"：把"值得沉淀的经验→当周周记"固化为确定性流水线（journal-cli.mjs），**agent 管判断与撰写，CLI 管格式/落点/去重/脱敏/收口**——公司 Agent-owned 手动触发实例的升格标本（98/100 完整档） |
| **成熟度** | **完整档**（2026-08-29 升格，runId 7a85e3e0 首评 98）：十段中触发=手动（自动化挂 backlog，FADE-002 先例不影响档位）；Score 双段/RETRY/三态词表/映射声明全部落地。现存周记 W34/W35，W36/W37 无新册=现状如实注 |
| **真源路径** | 规范 `docs/workflow/operating-records/项目级 AI 共学周记/ade-journal-recording-spec.md` v1.1；执行体 `scripts/journal/journal-cli.mjs`；审计 `journal-run-log.jsonl`；格式真源 `.github/prompts/项目级 AI 共学周记.prompt.md`；登记册 FADE-003 条；纪律 D-06 |
| **常见误区** | ①跳过必读三件凭记忆写（立册反模式第一条）；②跨周找旧模板（格式基准=最近已存在周，禁止翻旧）；③内部台账入册（commit 索引违反 Q4）；④一次写完整册（规范=逐条追加，骨架最小生长）；⑤自己判 approved 就当完了（Close CLI 会再验，机器可否决） |

## 二、生命周期与两道门

```text
事件或检测（对话中出现可沉淀内容 / CEO 指令）
→ 登记 begin（去重提示+runId）
→ Agent Qualify（语义四问）
→ Agent Plan（格式三查+草拟 entry.json 七字段）
→ DCE：CLI qualify（机械资格：结构+脱敏）→ CLI append（固定格式渲染 2.n）
→ Score：CLI score（S1-S7 机检 + W1-W4 语义合并）
→ Agent Close Skill（读回+语义裁决 approved|escalated|retry）
→ Close CLI（校验裁决+run 链+收口五查）
→ 终态：APPROVED | ESCALATED | RETRY（BLOCKED=结构障碍，建草稿后转正）
```

**第一道门——Qualify 语义四问**（agent 判断）：

| 问 | 判什么 | 不过 |
| --- | --- | --- |
| Q1 可复述 | 有具体现象，非模糊感受 | 任一问不确定 → |
| Q2 有产出 | 有方案/workaround/明确教训 | **ESCALATED** |
| Q3 可对外 | 脱敏后可分享 | （列理由请 CEO 裁决） |
| Q4 有共学价值 | 对"用 AI 做项目的人"通用；纯内部台账不入册 | |

**第二道门——qualify 机械资格**（CLI 判定）：结构完整扫描+脱敏扫描。命中 API key/私人内容
→ ESCALATED 转 agent/CEO 裁决（实案：runId 0f1a4035 真拦"疑似 API key（sk-…）"）；
结构缺 → REJECTED 补字段重来。

## 三、记一条周记的完整动作序（含三条岔路)

**主路**：

1. `begin --title "…"` → 领 runId，同题去重提示。
2. 读**必读三件**（顺序不可省）：prompt 固定格式 → 周记目录 README → **最近一个已存在周**的周记（格式漂移以最近周为准）。
3. 四问自评 → 草拟 entry.json（七字段）。
4. `qualify --entry <json> --run <runId>` → 过机械门。
5. `append --entry <json> --run <runId>` → 渲染为下一个 2.n，同步 bump lastSyncedAt。
6. `score --run <runId>` → S1-S7 机检（五件结构/元信息当日/路径当周/去重序号唯一/run 链完整/脱敏复扫/守恒基线）+ W1-W4 语义分合并（各 0-5，W4 含对外口径双判问）。
7. Close Skill 读回裁决 → `close --run <runId> --verdict … --note "…"` → 五查 + 终态。
8. 回报 CEO：文件路径+条目编号+是否新建草稿（C5）。

**岔路一（脱敏拦截）**：qualify ESCALATED → 按命中提示脱敏 → 重新 qualify。**没有任何绕行。**
**岔路二（去重/缺前置）**：append BLOCKED-dup（同题已存在→需要修订走 CEO 明确指令）或
BLOCKED（当周文件不存在→`init` 建最小骨架后重走——实案 541da30c 即此弧）。
**岔路三（RETRY 重评）**：score FAIL → Close Skill 裁 retry → close 终态 RETRY（stage=score）
→ 修订（须 run 链 revision 行授权，限本次 run 产出条目）→ **重评**：retry 行之后同 runId
出现 score PASS 行，APPROVED 才可达（机器可校验的前置）。

## 四、评分怎么读（双门槛）

- **机检 S1-S7**：每项过/不过，**全部必选**——omission≠0 直接 FAIL。S 满分 80 =地板。
- **语义 W1-W4**：各 0-5 分（现象捕捉/方案可操作/影响真实/经验提炼+对外口径），evidence_ref
  取条目内引文；首 3 个功能期 run 双席抽验。
- **及格线**：总分 ≥90（S80+W20=100）。**80 卡线是教训不是基准**——升档联审明文
  "W≥10=最小裁判权"，防止只有机检没有语义评判的空转及格。
- 读分实存：7a85e3e0 的 score 行 `subtotal_s:80, total:98, omission:false`——机检满分+
  评委 18/20，这就是 98 分的全部来源。

## 五、价值主张

- **公司级学习沉淀不靠自觉**：立册前的三类翻车（自创结构/旧模板/内部台账入册）被流水线结构性消灭。
- **敏感信息零外泄**：脱敏双扫（qualify 进门扫+score 落盘复扫），实拦记录在案。
- **审计可复算**：一条 runId 拼出全程，每步 verdict 留痕；机器否决 agent 的实案（541da30c 双判弧）证明校验独立。
- **人机分权范本**：四问/语义裁决/对外口径=人；格式/去重/脱敏/链路/守恒=机器。

## 六、诚实边界

- **触发手动**：对话检测/cron 自动触发挂 automation-backlog（四项：自动建草稿/对话后自动判断/周六午前更新/签发提醒）——不影响档位（FADE-002 先例）。
- **现存节奏**：W34 立册、W35 两条成品，W36/W37 无新册——手动触发下的自然节奏，如实注。
- **push 不查**：close 五查中 git 提交为 C4，审计文件 push 持久化不强制（纯本地确定性，映射表注记）。
- **修订边界**：只追加不重写；豁免仅限 CEO 明确指令与 run 链 revision 授权的本次条目——他人/已签发绝对禁区。

## 七、验证方式（学完自测）

1. 打开 journal-run-log.jsonl，任选 runId 拼全程，指出关键 verdict。
2. 口测主路八步+三条岔路，说出 RETRY→APPROVED 的机器可校验前置。
3. 读 W35 周记 2.2 条，对照五件结构逐件指认，并读出它的 runId 与 98 分构成。
4. 进阶：读 spec §2.5，说出 S7"守恒基线"检查防的是什么（他人/已签发条目被动过）。

## 使用依据

- spec v1.1 全文（四问/P1-P3/五件/Score 段/RETRY/五查/反模式，2026-09-08 实读）
- 审计日志原行（0f1a4035/541da30c/dde77db9/7a85e3e0，2026-09-08 实读引用）
- CLI 命令族与退出码：journal-cli.mjs 结构勘定（cmdQualify 三出口/cmdAppend BLOCKED-dup/cmdClose 五查+retry 前置）
- 登记册 FADE-003 条（升档五销账+98 分记录）；fade-papers/FADE-003-* 六卷
