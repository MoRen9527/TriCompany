# 任务书检查规范 v1.0（CAO 职责范围·机器可跑形）

- sourceOfTruth: 本件（`TriCompany/docs/standard-templates/taskcharter-check-spec-v1.0.md`·CAO 检查判据正身）
- syncMode: write-time
- lastSyncedAt: 2026-11-26T22:57:21+08:00（date 现查原值·写前跑·D-47 正形）
- 令锚: CEO 2026-11-26 22:57 令——「挂任务书必须有 CAO 批标志位·机器可检·没有不让挂」+「CAO 主要检查命名规范、任务书格式是否符合要求等 CAO 职责范围的内容」
- 模板联动: `taskcharter-template-v1.0.1.md` §⓪ `cao_approval` 块

## 一 · 检查范围（**CAO 域三项·不越界**）

| # | 检查项 | 判据 | 机器可判？ |
|---|---|---|---|
| **C1 命名规范** | `task_id` 匹配 `^TC-\d{8}-\d{3}$`（如 `TC-20261126-001`）；`charter-<ISOts>.json` 文件名匹配 `^charter-\d{8}T\d{6}Z\.(json|md)$` | ✓ 正则 |
| **C2 格式自洽** | ①`form` 与 `complexity` 同向（simple↔inline／complex↔index·矛盾=fail）②`index` 形须有 `prd_ref`+`techplan_ref` 且指针一步可达 ③`inline` 形须有 `product_design`+`tech_design` | ✓ 枚举比对+指针 ckeck |
| **C3 必填区块齐** | 四块齐：`cao_approval`／`authorization`／`tri_source_assertion`／`verify`——缺任一=fail | ✓ 键存在性 |
| **C4 schema 校验** | 各块必填字段非空+枚举值合法（如 `authorization.scope ∈ {ignition,construction,result_approval}`） | ✓ 类型/枚举 |
| **C5 引用可验** | `tri_source_assertion.impl` 的 path/函数**真实存在**（`git cat-file -e` 或文件存在）——不存在=fail-closed | ✓ 可验 |
| **C6 doc 面真源可验**（2026-11-27 10:32:31 补·CTO 延伸·今晚总纲落条） | `tri_source_assertion.doc` **须指向唯一真源件**（文件路径·可 cat-file/存在）——**禁指「信/对话/口头/摘要」**：信会散、对话不可复算，**只有真源件能被后续引用核验**（「信里说清了」≠「三面同源」） | ✓ 路径存在性 |

**C6 补注**：`doc` 面判据的来历=2026-11-26/27 跨夜四轮对齐的总纲——「**口径收敛不是「说清楚就完了」，是「把说清楚的东西放进唯一真源」**」（CTO 记为技术面惯例第一条）；本检查规范的 C1-C6 本身即该总纲的落地。

**不在 CAO 域的（明确排除·防越界）**：产品判断（CPO）／技术可行性（CTO）／成本（CFO）／责任归属（CHO）／排程（COO）——**CAO 只查「形」不查「实」**（内容对不对不归我）。

## 二 · 机器可跑形（check 脚本骨架·伪代码）

```bash
# check-taskcharter.sh <charter.json>
fail=0
# C1 命名
tid=$(jq -r '.task_id' "$1"); [[ "$tid" =~ ^TC-[0-9]{8}-[0-9]{3}$ ]] || { echo "C1 FAIL: task_id=$tid"; fail=1; }
# C2 形态自洽
form=$(jq -r '.form' "$1"); cplx=$(jq -r '.complexity' "$1")
[[ "$form$cplx" =~ ^(inline(simple)?|index(complex)?)$ ]] || { echo "C2 FAIL: form=$form complexity=$cplx 不同向"; fail=1; }
# C3 必填四块
for k in cao_approval authorization tri_source_assertion verify; do jq -e ".$k" "$1" >/dev/null || { echo "C3 FAIL: 缺 $k"; fail=1; }; done
# C4 schema 枚举（示例两处·余同）
jq -e '.authorization.scope | IN("ignition","construction","result_approval")' "$1" >/dev/null || { echo "C4 FAIL: scope 非法"; fail=1; }
jq -e '.cao_approval.approved == true' "$1" >/dev/null || { echo "C4 FAIL: cao_approval.approved != true"; fail=1; }
# C5 引用可验（impl 指向的 path 存在）+ C6 doc 面真源可验（doc 须为文件路径·非信/对话）
doc=$(jq -r ".tri_source_assertion.doc" "$1")
[[ -f "$doc" ]] || git cat-file -e "HEAD:$doc" 2>/dev/null || { echo "C6 FAIL: doc=${doc} 非真源件（禁信/对话）"; fail=1; }
impl=$(jq -r '.tri_source_assertion.impl' "$1")
echo "$impl" | grep -oE '[A-Za-z0-9_/.-]+\.(py|ts|mjs|md|json)' | while read p; do
  [ -f "$p" ] || git cat-file -e "HEAD:$p" 2>/dev/null || { echo "C5 FAIL: $p 不存在"; exit 1; }
done || fail=1
exit $fail   # 0=通过·非0=拒挂
```

**铁律三条**：①**脚本 EXIT≠0 = 拒挂**（fail-closed·不给人眼复核的裁量口）②**每项 FAIL 必打具体值**（禁只说「不通过」）③**C5 只验存在性·不验正确性**（实现对不对归 CTO/STE·我不越界）。

## 三 · 批与拒（CAO 签署形）

- **通过**：`cao_approval = {approved: true, approver: CAO, approved_at: <现查>, commit: <CAO 批 commit 锚>, checks: {naming:{ok:true}, format:{ok:true}, required_blocks:{ok:true,missing:[]}}}`——**commit 锚须可 `cat-file` 验**。
- **拒**：**不写 `approved:true`**（保持 false 或缺块）→ 挂载面 `fail-closed` 拒挂；**拒因须书面回执**（哪项 FAIL+具体值+修复建议）——**拒不能只留一个 false**。
- **批后变更**：任务书内容改 → `cao_approval` **须重签**（旧 commit 锚失效·防「批后偷改」）。

## 三A · (b) 形态处置（run_dir 临时件·2026-11-26 22:58:53 补·CTO 反馈真缺口）

**问题（CTO 实勘）**：charter 有两种存在形态——**(a) 树挂载件**（git 内·commit 锚可验）／**(b) run_dir 临时件**（未入 git·**无 commit 锚**）。本规范 §三 原只写 (a)。

**裁定（本席定形·CTO 按此实现）**：

1. **(b) 允许挂载·降级形三项**：①`approved===true` 仍是**唯一硬条件**（不变）②`commit` 字段**留空**（**不得填假锚**·宁缺勿造）③**增 `binding_weak: true`** 标记（明示「内容绑定弱·批后偷改不可见」）。
2. **(b) 的批的前置约束（关键·防「批了看不见的东西」）**：CAO 批须**能读到 charter 内容**——若 charter 仅存 run_dir（CAO 不可达），**须由供料席提供内容或临时入 git**；**CAO 未读到内容的「批」= 无效**（这是 (b) 形态下批可信度的唯一保障）。
3. **(b)→(a) 转化义务**：挂载后 charter **应尽快入 git**（**close 时落树为最低要求**）；转 (a) 后**须补 commit 锚并重签**（`binding_weak` 摘除·旧批失效）。
4. **如实注**：(b) 形态的批可信度**天然低于 (a)**——这是**如实标注的降级形态**，**非等价形态**；台账统计 (b) 挂载数应单列（便于观察临时件泛滥）。
5. **`content_sha256_16` 字段（2026-11-26 22:59:50 补·CTO 技术建议采纳）**：`cao_approval` 增可选字段=**CAO 批时所见内容的 sha256 前 16 位**——作用=**把「CAO 是否真看见内容」从口头约束变机器可检**。**必填面**：(b) 形态**建议必填**（否则 ② 的前置约束无法机械验）／(a) 形态**可省**（commit 锚已覆盖内容绑定）。**门的用法**：(b) 上比对 `content_sha256_16` vs 现文件 hash——**不等=拒「批后内容变更·须重签」**（**(b) 的批后偷改检测因此恢复可用**·此前系如实限制）。**填则必真**：批时真算·**禁凭记忆填**（D-47 一族·与「未现查不得写现查」同根）。

## 三B · 拒因 code 与宽容面（2026-11-26 23:02:22 补·CTO/FSD 已按此实现·**三处引用本表不各自复写**）

### 拒因 code 三值（两层·拒因可分）

| code | 层 | 触发 |
|---|---|---|
| **`CAO_NOT_APPROVED`** | **第一层·准入** | 缺 `cao_approval` 块／`approved !== true` |
| **`ANCHOR_MISMATCH`** | **第二层·批的有效性** | `commit` 非空且 `git show <commit>:<path>` 的 sha16 ≠ 现文件 sha16 |
| **`CONTENT_CHANGED`** | **第二层·批的有效性** | `content_sha256_16` 有值且 ≠ 现文件 sha256_16 |

**铁律**：**两层任一不过皆拒·但拒因 code 必须不同**——**不是「只有一个判据」，是「一个准入判据 + 一个有效性校验·两者拒因可分」**（只写「不是第二挂载条件」会漏「第二层失败也必须拒」这一半·2026-11-26 双方对勘定谳）。
**拒因三要素**（照 #5）：每 code 附 `detail`（具体值）/`expected`（应是什么）/`fix`（修复指向）——**非空**。

### 宽容面（四条·放行 + `binding_weak` 或 `note`·**不走第二层拒**）

| # | 情形 | 处置 |
|---|---|---|
| 1 | `commit` 空（(b) 形态） | 放行 + `binding_weak: true` + note |
| 2 | `content_sha256_16` 无值（(a) 形态·commit 锚已覆盖） | 放行（commit 锚验仍生效） |
| 3 | `content_sha256_16` 无值（(b) 形态） | 放行 + `binding_weak`（**内容绑定弱·如实降级**） |
| 4 | 现文件不可读（如 run_dir 已归档） | 放行 + note「内容不可复核」 |

**宽容面原则**：**仅「有值且不符」走第二层拒**——**无值/不可读=放行+留痕**（**宁放行留痕·不硬拒可行流程**；但留痕使「弱绑定件」可被统计与追查）。
**note 强制律（2026-11-27 10:39:33 补·CTO 面加固·「有记名的宽容」落条）**：**宽容面四条放行时 `note` 必写**——**空 note 的放行=不合格**（视同 `CAO_NOT_APPROVED` 拒）。**定性**：**「放行不是没看见·是看见并记账」**——**宽容 ≠ 放任·宽容 = 有记名的宽容**；**无名放行=默许**（与「静默用旧件」同族·属未受控态伪装成受控态）。

## 四 · 边界（不越界声明）

本规范只覆盖 **C1-C5 五项形检查**；**语义/内容/技术/产品/成本/责任判断一律不在内**（各归其主）。**「C1-C5 全过」≠「任务书是好任务书」**——只等于「形合格·可挂」。

## 使用依据

- CEO 2026-11-26 22:57 令（BOD 转·原文两句）；`taskcharter-template-v1.0.1.md` §⓪；`taskcharter-template-v1.0.0.md` 校验铁律六条（本规范 C1-C5 为其在「挂载门」面的具体化）；D-98（可机械判者一律程序化·本条即其落地）。

—— CAO 小行（m-cao）·2026-11-26 22:57:21 +0800（date 现查原值·写前跑）
