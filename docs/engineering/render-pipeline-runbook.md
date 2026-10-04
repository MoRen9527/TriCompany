# 渲染管线 Runbook（13 席发布位渲染操作规程）

- sourceOfTruth: 本件（渲染管线操作真源；管线实现正身=`runtime/cognition/source_publish_check.py`，本件为其操作面 companion）
- syncMode: manual（管线 CLI 变更时随更；变更须 CTO 技审+CAO 定位核）
- lastSyncedAt: 2026-10-04T13:52:31Z（+8=21:52:31，date 现查 shell 注入原值零手打；CTO 技审三条勘意随更。勘误注：本笔前两写均预填（21:53:30/21:52:40）非现查值，三犯连击自报——手打时点字符串系预填根因，改 shell 变量注入法候 CAO 入记忆面）
- 立件缘起: LG-063 三并批渲染炉 2026-10-04 执行位缺位事故（CAO 裁① 正身化；卷锚=TriMetaverse `docs/workflow/operating-records/2026-W40/trees/lg063-render-batch-20261004/cos-render-exec-readout-20261004.md`）
- 适用域: 本机 dev 车道（执行位历史先例=STE 值席/COS 值席，随组窗令派定）；sg 面渲染另按 M-SG 面规程（本件不覆盖）

## §一 管线正身与配方

**渲染管线唯一正身**（D-07 禁手编红线——发布位渲染必须走本管线，禁手编渲染位文件）：

```bash
# 在 TriCompany 仓根执行
cd <TriCompany-root>

# 三面干跑（默认 dry-run，零写入——FADE §2.4 safety gate 同构）
python runtime/cognition/source_publish_check.py --publish-agents --host claude
python runtime/cognition/source_publish_check.py --publish-agents --host copilot
python runtime/cognition/source_publish_check.py --publish-agents --host claude-session

# 三面实写（显式 --execute 才写盘）
python runtime/cognition/source_publish_check.py --publish-agents --host claude --agent-execute
python runtime/cognition/source_publish_check.py --publish-agents --host copilot --agent-execute
python runtime/cognition/source_publish_check.py --publish-agents --host claude-session --agent-execute
```

- 三面目标（`HOST_RENDER_REGISTRY` 定义于 source_publish_check.py L174）：
  - `claude` → TriMetaverse `.claude/agents/*.md`（manifest entries 19=13 席+registry 型）
  - `copilot` → TriMetaverse `.github/agents/*.agent.md`（manifest entries 19）
  - `claude-session` → TriMetaverse `.claude/compass/*.session.md`（13 entries，无 sessionBody 的 entry 零行为）
- **entries 数语境钉死**（CTO 技审勘意①，2026-10-04）：读数里的 entries=**管线 manifest 处理数**（claude/copilot 19、session 13），非目录物理文件数（实盘 `.claude/agents` 22/`.github/agents` 22/compass 13——差 3=正名残留双胞胎 2+待勘差 1，残留件归 143 行批次窗处理不新增）。执行者勿拿目录物理数对 manifest 数误报差。
- 参数面：`--source-root`（默认 `.`=TriCompany 仓根）、`--support-root`（默认 `../TriMetaverse`）、`--employees`（逗号分隔单席过滤，仅 --publish-agents 面）、`--format json`（唯一输出格式，人类可读报告走 stderr）
- 关联管线（非本件主对象，认面勿混）：`employee_host_publish.py` 渲 binding-profiles+knowledge README 面（13 席 pass/26 generated/13 published 形读数）；`host_object_generation.py`/`employee_host_object_generation.py` 属 manifest 派生链

## §二 标准工序（五步）

1. **源侧先行断言**：渲染位忠实源侧——渲染前先确认源侧正身（`TriCompany/source-agents/`）无待带出遗漏（正名/改写类施工是否已含全部席位五件套；2026-10-04 案例=C1 施工漏 COS agent-body 2 处，渲染后 COS 席仍带旧名）。源侧有漏先补漏 commit 再渲染。
2. **三面干跑**：逐面 dry-run，解析 `items[].action` 得真 drift 清单（**勿信 summary 单层**，见 §四断言①）。
3. **实写**：dry-run drift 清单与预期炉料对表一致后，三面 `--agent-execute`。
4. **断言四绿**（§四全过）。
5. **落盘推平**：TriMetaverse 仓渲染位 commit（message 带三面读数）+push+`ls-remote` 同顶核验；读数卷落 operating-records 当前周 trees/。

## §三 读数形样板（消费与回报统一形）

管线 JSON 关键字段（`--format json` 为 stdout 唯一格式）：

```
status: pass
scope_specific.counts: {"created":N,"updated":N,"skipped_identical":N,"skipped_dry_run":N,"derived_identical":N,"derived_drift":N}
items[]: [{action: created|updated|derived_drift|derived_identical|skipped_*, source, target, before_hash, after_hash}]
```

回报读数形（卷面/毕报统一，batch-17 先例形）：

> claude 面：19 entries，updated 14，Derived(ok) 5，drift 0，errors 0；copilot 面：19 entries，updated 14，skipped(same) 5，drift 0，errors 0；claude-session 面：13 entries，updated 13，drift 0，errors 0
>
> 〔括注（CTO 技审勘意③）：「Derived(ok)」读数形正形字段=**derived_identical**（counts 六键之一），回报可用读数形简称、消费校验须按 derived_identical 字面 grep。〕

## §四 断言清单（实写后四绿门，缺一不闭）

1. **drift 真值断言（最要紧）**：**drift 读数必须解析 `items[].action` 统计 `derived_drift`，勿信顶层 `summary` 单层；`status` 字段同不可单信**（L1600 status 仅看 errors，drift>0 仍 pass）——summary 会把 derived_drift 吞进 skipped（2026-10-04 实证：summary 显示 changed 0/skipped 19 全绿假象，items 层实有 derived_drift=14）。**drift 唯一权威=items[].action 统计**；drift>0 时禁 --execute（先勘漂移根因：源侧漏项或渲染位手编污染）。〔长期修：status 判定扩容一行 drift>0→非 pass，禁动顶层 summary 四键（ADE 不变式 total==changed+skipped+errors+下游聚合器 L2281/2288 按四键 sum），候 10-06 攒批炉——CTO 技审长期修法约束 2026-10-04。〕
2. **旧名零回流**：`grep -rl <旧名> <渲染位三目录>` =0 命中（正名类炉必做；对照炉前命中数报清零量）。
3. **新名在位抽验**：目标席渲染位 grep 新名 ≥ 预期处数。
4. **他区零扰动**：`git status --porcelain` 渲染位目录外无新增 M（既有在途 M 逐一归因非本炉产物）。

## §五 边界与事故教训（在案案例索引）

- **在途笔隔离**（多席共享工作区）：渲染读源侧工作区文件——渲染前 `git status` 勘源侧在途笔；非本炉授权的在途内容变更笔须隔离剥离（备份+恢复原文+pathspec 限定 commit+回植原状）再渲染，防未审内容渲入发布位（2026-10-04 COS agent-body L19 案例在卷）。
- **执行位缺位教训**：定炉/定窗令应一令双带（炉料时点+执行派令或显式「起炉另令」标注）——候选条候 D-43 打包窗统裁（CAO 2026-10-04 裁③）。
- **执行位先例**：整炉渲染历史执行位=STE 值席车道（batch-17 先例 514e56b4）；值席车道/COS 自跑为组窗令明示时的合规形态（2026-10-04 A 案先例）。派工随组窗令落，勿悬空。
- **GitHub 443 欠推常态**：origin fetch=GitHub（443 常断），推平核验走 sg bare（`git ls-remote sg-server dev` 或 origin push 第二 URL）；GitHub 批量补推照欠推面挂账。

## §六 维护

- 本件由 COS 席主笔立件（CAO 裁① 2026-10-04）；管线 CLI 面变更（参数/注册表/counts 口径）须 CTO 技审后随更本件并刷新 lastSyncedAt。
- 审链记录：CAO 定位核绿（2026-10-04 21:48，零双写实核 PASS）+CTO 技审 APPROVE（2026-10-04 21:51，三条勘意已随更：entries 语境钉死/status 同不可单信/Derived(ok) 括注；技审卷=Trees/lg063-render-batch-20261004/cto-runbook-tech-review-20261004.md，ec1c3664）。长期修法约束在案：§四① 括注，候 10-06 攒批炉。
- 长期候办（CTO 面）：summary 口径修（derived_drift 出 skipped 单列）——CAO 转候办，候 10-06 攒批炉或 CTO 另窗。
