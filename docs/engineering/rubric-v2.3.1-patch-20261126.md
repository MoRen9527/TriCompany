# rubric-v2.3.1 补丁稿·A 族 scope 明确化（CTO 出稿·2026-11-26）

- sourceOfTruth: 本件（TriCompany/docs/engineering/rubric-v2.3.1-patch-20261126.md·A 族 scope 补丁提案正身）
- syncMode: write-time
- 承接: v2.3.0 施工后 BOD 读码抓出语义矛盾（2026-11-26 21:47·BOD「迁移成功会 fail？」）→CTO 三问答+BOD 确认修法（21:50）→实现修正 a8cc5f1 已验收（21:47）
- **状态=提案**（rubric 文本修订须 CEO 批·**批前 rubric 文本仍 v2.3.0·不阻塞实现**）

## §一 · 矛盾与结论

**矛盾（BOD 读码抓出）**：v2.3.0 的 `_collect_a` 按「同一目录 pre vs cur 对照·增件=violation」——但 **fade-001 的迁移=carry_periodic（W47 白名单条目 copy 到 W48·`to_dir.mkdir`）·目标周必然增件** → **迁移成功会被判 fail**。

**结论（CTO 裁·BOD 确认）**：**A 族判据对象=被迁移的源件集，不是目标周目录整集**。
- CEO 原意直译：「迁移前把不可变量快照·迁移后对照·保证**迁移过程中**对象没被篡改」——**「对象」=被 carry 的源件**。
- **目标周新增件=迁移的正常产物·不判 violation**；**白名单外突变**（不该有的增/删）**不归 A 族**（归 plan_scope 五分类/keep 面）。

## §二 · rubric 文本补丁（A 族三字段·其余不动）

| 字段 | v2.3.0 现文 | **v2.3.1 补丁** |
|---|---|---|
| reading_point | 目标周目录树全卷（`operating-records/<W>/`·trees 递归）逐件 sha256_16+size+parse_ok 迁移前快照 | **源周（plan.from_week）的 carry 白名单条目源件集**（读 `carry_periodic_whitelist.json`·path_pattern 渲染·defer_to_impl 跳过）逐件 `{path, sha256_16, size}` 迁移前快照 |
| verdict_rule | 同对象·同集·同 hash（件集一致+逐件 sha256_16 一致+parse_ok 全 true；任一 violation=fail） | **双向对照**：(a) **源未篡改**——源件仍存在且 sha256_16 不变；(b) **搬运无损**——目标周对应位置存在且 sha256_16==源。(a∧b→pass；任一→fail·明细 `source_tampered`/`dest_missing`/`dest_hash_mismatch`) |
| special_clause | 新基准=每次迁移前实时快照（`migration-pre-snapshot.json`）·旧 vB `4f990e911c3f` 退役·scope 不含 jobs.json | **保留前三项** + **新增 scope 明写：判据对象=carry 白名单源件集·目标周新增件不判 violation·白名单外突变归 plan_scope/keep 面** |

**不变**：family_name=迁移完整性·weight=6·三守卫退役（qualify→E 族·trap/RCguard 删）·version 面→**v2.3.1**。

## §三 · 分工

- **实现修正=已落**（a8cc5f1·本机 96 passed／三套 111·三明细+双向+白名单 5 entries 实读）——**修 BUG 非改判据口径·批前可落**。
- **本补丁=rubric 文本**（scope 明确化）→ **呈 CEO 批**。

## §四 · 实读锚

| 锚 | 值/位置 |
|---|---|
| carry 实现 | `carry_periodic.py` L30-60（`to_dir.mkdir(parents=True, exist_ok=True)`·mode=copy·「逐白名单条目 glob from-week 源→机械搬运 to-week 正形目录」） |
| 白名单 | `carry_periodic_whitelist.json`·**5 entries**（company-demand-pool.md／daily-progress.md／task-inventory-*.md copy-latest 等） |
| 实现修正 | `score_engine.py` L355-380（源件快照）/L344（双向 verdict）/L432-434（三明细）·commit **a8cc5f1** |
| v2.3.0 rubric | `rubric-firstshoot.json` A 族（d5ac089·RUBRIC_VERSION="2.3.0" L97） |

## §五 · 使用依据

BOD 读码质疑（21:47）+CTO 三问答（21:45）+BOD 确认修法（21:50）+实现修正验收读数（a8cc5f1）++carry_periodic 实读+白名单实读。

---
—— CTO 小狄（m-cto）·写前现查 2026-11-26T13:47Z（+0800=21:47）
