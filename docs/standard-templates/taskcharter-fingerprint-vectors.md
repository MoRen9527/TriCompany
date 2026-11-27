# 测试向量·任务书 `content_sha256_16`（规范 v1.1 附件）

> 三处实现（CTO/TriRMC、COS 树挂载门、CAO 参考实现）以本表对表——**不靠各自读文字**。输入件逐字节固定，`␤`=LF、`␍␤`=CRLF。
> 参考实现（同目录·两套独立实现·互不共享代码）：`taskcharter-fingerprint-ref.py`（Python）、`taskcharter-fingerprint-ref.mjs`（JS/TS）。生成时两套各算一遍 10 组·全部相等。

| ID | 形 | 说明 | 期望指纹（16 hex） | n |
|---|---|---|---|---|
| V01 | json | LF·两键空（签时形态） | `490cc48e4f6b2d4b` | 2 |
| V02 | json | 与 V01 同内容·两键有值（签后/回填形态）·须=V01 | `490cc48e4f6b2d4b` | 2 |
| V03 | json | V01 的 CRLF 版·须=V01 | `490cc48e4f6b2d4b` | 2 |
| V04 | json | V01 前加 U+FEFF·须≠V01 | `8a06be45d680813f` | 2 |
| V05 | json | 含中文·字符串值内含转义引号与反斜杠 | `6176f7265754955f` | 2 |
| V06 | raw | 非 UTF-8 原字节（GBK）·走原字节分支 n=-1 | `29d8e31bbe8b6e0c` | -1 |
| V07 | json | 块前字符串值内含伪键形文字（防置空错对象） | `83c38c47515c6c24` | 2 |
| V08 | yaml | md/YAML·LF·两键空（签时形态） | `ec7a2f97f57ee7a3` | 2 |
| V09 | yaml | V08 的 CRLF 版·须=V08 | `ec7a2f97f57ee7a3` | 2 |
| V10 | yaml | 正文含同名键示例·须≠V08（是内容） | `29012c5d480e5beb` | 2 |

## 等式（实现须全部满足）

- `V01 == V02 == V03`（两键的值、CRLF 不影响指纹）
- `V04 != V01`（U+FEFF 计入）
- `V09 == V08`
- `V10 != V08`、`V07 != V01`、`V05` 与其余互异（内容不同则指纹不同）
- `V06` 的 `n = -1`（原字节分支）；其余 `n = 2`

## 输入件（逐字节）

**V01**```
{"task_id":"TC-20261127-001","authorization":{"scope":"construction"},"cao_approval":{"approved":true,"approver":"CAO","approved_at":"2026-11-27T22:42:00+08:00","commit":"","content_sha256_16":""},"verify":["x -> EXIT=0"]}␤
```

**V02**```
{"task_id":"TC-20261127-001","authorization":{"scope":"construction"},"cao_approval":{"approved":true,"approver":"CAO","approved_at":"2026-11-27T22:42:00+08:00","commit":"0123456789abcd","content_sha256_16":"0123456789abcdef"},"verify":["x -> EXIT=0"]}␤
```

**V03**```
{"task_id":"TC-20261127-001","authorization":{"scope":"construction"},"cao_approval":{"approved":true,"approver":"CAO","approved_at":"2026-11-27T22:42:00+08:00","commit":"","content_sha256_16":""},"verify":["x -> EXIT=0"]}␤
```

**V04**```
﻿{"task_id":"TC-20261127-001","authorization":{"scope":"construction"},"cao_approval":{"approved":true,"approver":"CAO","approved_at":"2026-11-27T22:42:00+08:00","commit":"","content_sha256_16":""},"verify":["x -> EXIT=0"]}␤
```

**V05**```
{"task_id":"任务·二〇二六","note":"含 \"引号\" 与 \\ 反斜杠","cao_approval":{"approved":true,"commit":"","content_sha256_16":""}}␤
```

**V06**（GBK 字节）```
c8cecef1cae9
```

**V07**```
{"note":"例 content_sha256_16: \"AAAA\"","cao_approval":{"approved":true,"commit":"","content_sha256_16":""}}␤
```

**V08**```
---␤
task_id: TC-20261127-001␤
form: inline␤
cao_approval:␤
  approved: true␤
  approver: CAO␤
  commit: ""␤
  content_sha256_16: ""␤
verify:␤
  - "x -> EXIT=0"␤
---␤
␤
# 任务书␤
␤
正文。␤
```

**V09**```
---␍␤␤
task_id: TC-20261127-001␍␤␤
form: inline␍␤␤
cao_approval:␍␤␤
  approved: true␍␤␤
  approver: CAO␍␤␤
  commit: ""␍␤␤
  content_sha256_16: ""␍␤␤
verify:␍␤␤
  - "x -> EXIT=0"␍␤␤
---␍␤␤
␍␤␤
# 任务书␍␤␤
␍␤␤
正文。
␤
```

**V10**```
---␤
task_id: TC-20261127-001␤
form: inline␤
cao_approval:␤
  approved: true␤
  approver: CAO␤
  commit: ""␤
  content_sha256_16: ""␤
verify:␤
  - "x -> EXIT=0"␤
---␤
␤
# 任务书␤
␤
正文。例 content_sha256_16: "d"␤
```

## 自检（生成时跑过）

- V01==V02==V03: True
- V04!=V01: True
- V09==V08: True
- V06 n=-1: True
- 互异 7 件: True
- 其余 n=2: True
