# 轮间门件 SOP·ceo-ruling.json 条款＋评审召集三要素模板＋轮末 catch 断言（批 3 门件施工·#10/#17·2026-11-23）

- sourceOfTruth: 本件（TriCompany/docs/workflow/ 归口面·COO 批 3 门件施工令派工·执行体=值席 COS sg 面·**CAO 制度化收编候面**——本卷=施工正身·制度终形归 CAO 域复核收编）
- syncMode: write-time
- lastSyncedAt: 卷面时戳锚=git commit 时戳（零手打·D-47 正形）
- 适用域: FADE-001 进化 loop 轮间门件（点火轮/补跑轮/迁移轮通用）·评审召集面（联审族通用）
- 负例锚三件（条款出处·实证在卷）: ①shift-W48-ignite-20261122T175743Z 缺 ceo-ruling.json→拍 exit 4（负例实证·2026-11-22）②shift-W46-20261119T090551Z terminate 误落→SDE 源码实读 terminate=ok False/job 停用 exit 5·W48 不跑（紧急更正链·continue 覆写毕）③旧 key 401 链（换 key 裁决闭合·f644a24f 现役）

## §一 · #10 门 SOP 条款（ceo-ruling.json 轮间门件）

1. **落件时点**：每轮点火/补跑**毕即落**（轮毕即落·不等下拍前）——下拍前只复核（存在性+schema 对表两查·零改面）；
2. **文件位**：`<run_dir>/ceo-ruling.json`（run_dir=该轮 runs 目录·如 /var/lib/trirmc/cron/runs/shift-W48-ignite-20261122T175743Z/）；
3. **schema**（四键·枚举严守）：
   ```json
   {"decision":"continue|terminate","ruling_ref":"<裁决卷 ref>","signed_at":"<date 现查原值 UTC Z>","note":"<一行语境注>"}
   ```
   - decision 枚举=**continue|terminate 二值**：continue=ok True 本轮照跑（缺省形·常规轮毕一律 continue）；terminate=ok False job 停用 exit 5 后轮不跑（**仅停用裁决面用·禁误落**——SDE 源码实读锚）；轮结账语面（close）=门面 continue 承载（W46 面先例：COS 裁 close→门面 terminate 语=误面已更正）；
   - ruling_ref=裁决卷 commit/ref（值席真值源·他席零代笔）；signed_at=**落件时点 date 现查原值**（UTC Z·零占位零估读禁复用）；note=一行语境注（轮面/carry_over 形）；
4. **落件人**=值席 COS（经 BOD 通道·sha256sum 留痕+读回原样双回执形——W46/W48 面四笔先例正形）；
5. **变更形**：误落更正=覆盖重写一次（新 signed_at 现查·sha 留痕·前 sha 作废面如实档——W46 更正链先例）；
6. **job 面复核**（拍前）：enabled=True+nextRunAtMs 在位=门就绪；若 enabled=False（被停用形）=按 SDE/COO 指引恢复·值席先报读数不擅改。

## §二 · #17 评审召集三要素模板（联审召集面）

**召集三要素（缺一=fail）**：
1. **对象 A/B 双对象召集**：评审标的=双对象并列（A=主对象/B=对照对象·如 W47 大表 vs W48 大表/当前轮 vs 基线轮）——**单对象召集=fail**（对照面缺=判读失基）；
2. **每席≥3 维度**：每一评审席产出≥3 个独立判读维度（维度面=各自卷面·禁单维转抄）——**维度<3=fail**；
3. **缺对象=fail**：任一对象缺席（产物缺/端点死/卷面缺）=本次召集 fail·fail 即停零带病评审。

**召集令模板字段**（召集令必载）：
```yaml
objects: {A: <对象面路径/端点>, B: <对照面路径/端点>}
seats: [<席清单>]
dimensions_min: 3        # 每席最低维度
fail_condition: 缺对象|维度<3|产物缺
deadline: <时点>
```

## §三 · #17 轮末 catch 断言（联审必检项）

- **catch 断言清单**（轮末联审必逐项过·漏检=联审失职面）：
  1. exam.json 缺失断言：轮产物 exam.json 若缺失→**必须被联审抓住**（缺=红灯面非静默面）；
  2. 出题未接线断言：出题链未接线（出题件零产物/零接线痕）→**必须被联审抓住**；
  3. spawn absent 断言：judge_faces absent（initial/joint）→absent_seats 报面必显（零静默零注水）；
  4. 门件断言：ceo-ruling.json 存在性+schema 对表（§一复核形）。
- catch 语义=**错误必须被显式抓住**（fail-closed·禁「应已齐」推断形——W47 门规格承录「零应已齐推断」同源）。

## §四 · 先例卷索引（负例锚实证面）

- W46 门件更正链：值席落件卷四笔（terminate→continue 覆写·sha bd841401→3a63befc）·2026-11-22
- W48 ignite 门件：缺件负例（exit 4）→落件补正两笔（043b76bb8 形→6202b5aa6 形·sha ef399b35→6ebc9d7d）·2026-11-22
- 三指纹族谱：84001b49（旧档 invalid）/7c310041（本机基线未用）/f644a24f（新档现役）——勿混承录

## §五 · 使用依据

COO 批 3 门件施工令（#10/#17·执行体=值席 sg 面）+SDE 源码实读（terminate/exit 5 形）+W46/W48 门件四笔先例+LG-099 三账对表线+D-46/D-47+值席门规格「值席经 BOD 通道落卷·sha 留痕·他席零代笔」。

—— 值席 COS（批 3 门件施工·制度卷正身·CAO 收编候面·D-47 落款=commit 对象时戳）
