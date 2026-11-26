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
# C5 引用可验（impl 指向的 path 存在）
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

## 四 · 边界（不越界声明）

本规范只覆盖 **C1-C5 五项形检查**；**语义/内容/技术/产品/成本/责任判断一律不在内**（各归其主）。**「C1-C5 全过」≠「任务书是好任务书」**——只等于「形合格·可挂」。

## 使用依据

- CEO 2026-11-26 22:57 令（BOD 转·原文两句）；`taskcharter-template-v1.0.1.md` §⓪；`taskcharter-template-v1.0.0.md` 校验铁律六条（本规范 C1-C5 为其在「挂载门」面的具体化）；D-98（可机械判者一律程序化·本条即其落地）。

—— CAO 小行（m-cao）·2026-11-26 22:57:21 +0800（date 现查原值·写前跑）
