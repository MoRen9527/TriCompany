# 任务书模板 v1.0.2（公司标准文档资产·CAO 已批·已收归）

> **⚠️ 变更须 CAO 批**（CEO 2026-11-26 22:44 令）——本模板为公司标准资产，**任何修改须经 CAO 审批后方可落版**；变更记录见文末表。收归位=`TriCompany/docs/standard-templates/`（标准资产目录·正身）；起草源=TMV `trees/fade001-evolve-20261123/`（沿革留痕）。
> **v1.0.1 变更**（CEO 2026-11-26 22:57 令）：新增 **`cao_approval` 挂载前置门**（机器可检·**无此块或 approved!=true 一律拒挂**）——CAO 职责范围检查（命名/格式/必填区块）机器化。
> **v1.0.2 变更**（2026-11-27·规范 v1.1 随动）：`content_sha256_16` 由可选变**必填·唯一内容绑定**；`commit` 降为**信息字段**（锚验退役）；不再有 (a)/(b) 形态、`binding_weak`、宽容面。

- 模板号: **1.0.0**
- 依据: 七席合议格式提案（a1c53dd96·CEO 批 2026-11-26 22:37）+CAO 三条改进（form↔complexity 映射/task_id 定形/批准栏示范）
- 收归: **CAO 批·CEO 2026-11-26 22:49 准收归**（落 `TriCompany/docs/standard-templates/taskcharter-template-v1.0.0.md`）
- 变更规则: **每次改模板须 CAO 批**（改模板≠改任务书·模板是公司制度资产）

---

## 使用说明（三句话）

1. **先判形态**：CPO+CTO 联判复杂度 → 命中任一判据=**index 形**（另出 PRD/techplan）·全不中=**inline 形**（方案自含）；
2. **两种形态同一命名**：`charter-<ISOts>.json`（或 .md）·**靠 `form` 字段区分**·不靠文件名猜；
3. **前三块必填**：`authorization`（授权地基）+ `tri_source_assertion`（三面同源）+ verify（机器可跑）——**缺任一块=任务书不合格**。
4. **形态与复杂度必须同向**：`complexity=simple ↔ form=inline`·`complexity=complex ↔ form=index`——**矛盾=校验失败**（CAO 补①·v1.0.0）。

---

## 模板 A · inline 形（简单任务）

```yaml
# ═══ 任务书（inline 形）═══
task_id: TC-YYYYMMDD-NNN          # 定形·与 DP 号形同族（CAO 补②·v1.0.0）
title: <一句话任务名>
form: "inline"
complexity: "simple"

# ── ⓪ CAO 挂载前置门（必填·fail-closed·无此块或 approved!=true 一律拒挂）──
cao_approval:
  approved: true | false          # 仅 true 可挂载（G1）
  approver: CAO
  approved_at: "<ISO8601·写时现查>"
  content_sha256_16: "<16 位小写 hex·必填>"
  # ↑ 唯一内容绑定（G2/G3）：CAO 签时按检查规范 v1.1 §二 对「本字段与 commit 均为空串时」的文件算出·填入。
  #   门对当前文件重算·不等=拒 CONTENT_CHANGED。无此字段=拒 FINGERPRINT_MISSING（无「可省」形态）。
  #   填则必真：签时真算·禁凭记忆填（D-47 一族）。
  commit: "<CAO 批时仓 HEAD·信息字段·入库后可回填>"
  # ↑ 不参与任何判定·只供人读与审计追溯。回填不改变指纹（规范化时本键与 content_sha256_16 的值都被置空）。
  #   ⚠ 不再是「锚」：v1.0.x 的 commit 锚验（指向包含本文件的提交）在 charter 内自相矛盾·已退役（规范 v1.1 §〇）。
  checks:                          # CAO 职责范围三项·各带 ok 布尔（机器可判）
    naming:   { ok: true|false, actual: "TC-YYYYMMDD-NNN" }        # 实际 task_id 回填此处供核
    format:   { ok: true|false, rules: ["form↔complexity 同向", "必填区块齐", "schema 校验通过"] }
    required_blocks: { ok: true|false, missing: [] }                # 缺块清单·ok=true 时为空
  # 检查规范正身 = standard-templates/taskcharter-check-spec-v1.1.md（CAO 主笔·机器可跑形）；指纹参考实现与测试向量同目录
# ── ① 授权地基（必填·CFO 门）──
authorization:
  status: approved | pending_approval
  approver: CEO | <CEO明示代批人>
  approver_quote: "<原话逐字·禁转述>"
  approved_at: "<ISO8601>"
  scope: ignition | construction | result_approval
  # 查零判据 = approved ∧ scope==ignition ∧ approver==CEO
  # ignition（点火）仅 CEO 批；COS 代批限 construction / result_approval

# ── ② 三面同源（必填·CTO+CAO 门）──
tri_source_assertion:
  doc: <本卷锚>
  impl: <代码路径/函数+测试锚>
  semantics: <行为语义一句（归人判·显式标「待人工确认」）>
  # 引用不存在 = 校验失败（fail-closed 非警告）

# ── ③ 责任席（必填·CHO 门）──
owner_seat: <唯一 accountable 席>
backup_seat: <代行者·不得对 owner 自维行使 A>   # 可空
responsibility_face: 迁移 | 评审 | 批权 | 值席 | 岗位
depends_on: [<前置件>]                          # 可空

# ── ④ 产品面（必填·CPO 门）──
product_intent: "<目标用户/场景一句>"
observable_acceptance: ["<可感知验收 1>", "<2>"]   # 1-3 条
product_change: none | minor | major              # 不写=默认有变更（反形警示）
pricing_impact: none | <说明>

# ── ⑤ 执行面（必填·COS+COO 门）──
plan:                                       # 3-5 步
  - "<步骤 1>"
  - "<步骤 2>"
deliverables:
  - path: <产出路径>
    acceptance_anchor: "<验收锚>"
verify:
  - "<可执行命令> → 期望读数 → EXIT=0"          # 三项齐·禁「人工确认」
rollback: "<commit revert + 影响面一句>"
deadline: "<ISO 日期>"

# ── ⑥ 成本门（必填·CFO 审）──
cost_gate:
  estimate: {in: <n>, out: <n>, cache_read: <n>, cache_create: 0}
  stop_conditions: ["<停止条件>"]
  gate_required: true | false
```

**inline 形每 item 必含 `product_design` + `tech_design` 两段**（CEA 校验）。

---

## 模板 B · index 形（复杂任务）

```yaml
# ═══ 任务书（index 形）═══
task_id: <唯一标识>
title: <一句话任务名>
form: "index"
complexity: "complex"
summary: "<≤200 字摘要>"

# ── ① 授权地基（同 A·必填）──
authorization: { ...同 A... }

# ── ② 三面同源（同 A·必填）──
tri_source_assertion: { ...同 A... }

# ── ③ 责任席（同 A·必填）──
owner_seat / backup_seat / responsibility_face / depends_on: { ...同 A... }

# ── ④ 产品面（同 A·必填）──
product_intent / observable_acceptance / product_change / pricing_impact: { ...同 A... }
prd_ref: "<prd-<ts>.md 树内路径>"      # 复杂形必有（CPO 三问任一命中时）

# ── ⑤ 索引（复杂形核心）──
index:
  - {section: "<节名>", file: "<prd/techplan/正文>", lines: "<起-止>"}

# ── ⑥ 技术方案指针（复杂形必有·CTO）──
techplan_ref: "<techplan-<ts>.md 树内路径>"
# 技术方案必含（CTO 职责·CEO 22:41 补充）：
#   ① 技术架构选型（选型理由+被否选项）
#   ② 技术实现方案（测试计划/回滚方案/风险面）

# ── ⑦ 验收门清单（不复写细节·只列门）──
acceptance:
  - "<总纲 3-5 条>"
verify:
  - "<分层：①索引完整性+sha16 对表 ②PRD 总纲逐条 ③techplan 完成度>"
rollback: "<树级快照 tar/git revert>"
deadline: "<ISO>"

# ── ⑧ 成本门（同 A）──
cost_gate: { ...同 A... }
```

**同目录并列**：`prd-<ts>.md` + `techplan-<ts>.md`。

---

## 复杂度判据（任一命中 = complex）

| 面 | 判据 |
|---|---|
| 产品（CPO） | 用户可感知变化 / 新能力或新场景 / 价值交换变化 |
| 技术（CTO） | 跨模块（≥2 模块接口契约）/ 架构级（数据模型/持久化/判据或 rubric 定义/协议）/ 风险面（不可逆/生产写入/凭证/迁移） |
| 组织（CHO/COO） | 跨席≥3 / 岗位编制授权变更 / 不可逆·点火·门禁变更（D-39 三类） |
| 成本（CFO/COO） | 预估>4h / 轮次>2 / 跨仓 |

**判定链**：CPO+CTO 联判 → COS 复核 → **CEO 终裁**（批即认形）
**默认 simple·防膨胀·complex 无 PRD=拒收（fail-closed）·判错不对称（复杂误判为简单=重）**

---

## 校验铁律（机械门·入 D 系建议）

1. **verify 须机器可跑**（命令+读数+EXIT 三项·禁「人工确认/看情况」）；
2. **验收锚批时写定**（禁事后补）；
3. **引用可验**（指实现/文件/函数必带锚·不存在=fail-closed）；
4. **指针一步可达**（`git show <sha>:<path>`·index 形）；
5. **语义面归人**（机械只报它真能验的·不冒充）；
6. **三块必填**（authorization/tri_source_assertion/verify）——缺任一=不合格。

---

## 变更记录

| 版本 | 日期 | 变更 | 批准 |
|---|---|---|---|
| 1.0.0 | 2026-11-26 | 首版·七席合议格式提案落地+CAO 三条改进（form↔complexity 映射/task_id 定形/批准栏示范） | **CAO 批（commit 锚=TC@7a94656·收归笔）** |
| 1.0.1 | 2026-11-26 | 新增 `cao_approval` 挂载前置门（CEO 22:57 令）+**定稿过程补入** `content_sha256_16`（CTO 技术建议·(b) 形态内容绑定可验）+ §三A (b) 形态处置 | **CAO 批（commit 锚=TC@d810416 首落 + 本笔定稿）** |
| 1.0.2 | 2026-11-27 | §⓪ `content_sha256_16` 改必填·唯一内容绑定；`commit` 降信息字段（锚验退役——charter 内嵌 commit 锚自指矛盾·CAO/COS 各自实测正向路径不可达·CTO 22:41 采认）；(a)/(b) 形态、`binding_weak`、宽容面退役。随检查规范 v1.1。 | **CAO 批（自批·模板变更须 CAO 批=CEO 2026-11-26 22:44 令）·commit 锚=<本笔>** |

——BOD 起草（2026-11-26 22:45·候 CAO 批后收归标准资产）
