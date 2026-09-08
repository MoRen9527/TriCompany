<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-006/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-006 代码版——编排器、工具族与树合同实现地图

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-006/03-code-map.md
- syncMode: source-only
- lastSyncedAt: 2026-09-07

读者：要接手拾取编排、fade 工具族或树运维的工程师。
纪律声明：本文锚点为 **2026-09-07 现行版实读**——R 面编排器=`TriRMC/scripts/rmc_tick.py`（**442 行**，下称 tick）；工具族=`TriMetaverse/scripts/fade/` 四件（_fadehash 27 行/seal-materials 147 行/node-report-check 84 行/run-root 185 行）。行号漂移防护同前两单：语义优先，接手先 `git log` 再按符号重定位。
**双 tick 拓扑（诚实边界）**：R 面 tick=TriRMC rmc_tick.py（本文主标本，本机实勘）；M 面 tick=TriMMC `src/orchestration/`（TS 模块，sg 部署态本机无直读）——两 tick 同守三重门语义，面路由各取各的树。fade-watch.ps1（本地监控面，80 行）在盘，本文未逐行实勘，接手时按现状读。

前置：已读 [产品版](02-product-guide.md)。

---

## 一、R 面 tick 走读（rmc_tick.py，442 行）

**一轮 tick 做的事**：扫周平面树 → 三重门筛选 → 锁+冷却判重 → 预算检查 → 组 BRIEF+治理注入 → spawn 执行会话 → 回填 registry ticks。

### 1.1 三重门现行实现（evaluate_backlog，L124-150）

```python
L132:  if d.get("status") != "active":        # 门1：树状态=active（定稿）
L134:  if d.get("domainRouting") != "server-executable":  # 门2：路由字段值
L136-138:  if d.get("face") != "r-face":      # 面门：R 面严格制——只取显式 r-face
L140:  pending = [n for n in nodes if n.status == "pending"]
L143-145: TIME_GATE_RE 匹配 pending 节点 → 全带时间门则跳过   # 门3：无时间门
L150:  fingerprint = sorted((treeId, pendingNodes 元组))       # 变更指纹（判重基元）
```

**三个易错点（读码才能发现的）**：

1. 门 2 检查的是 **`domainRouting` 字段的值**等于字符串 `"server-executable"`——不是独立状态位。W37 现役树 duty-night-patrol 的 `domainRouting: "sg-duty-executable"`（值班类路由）**即使改 active 也不会进 R 面 tick**——它是给其他执行形态的路由值。面单上写什么值=选哪条通道，抄错值=树躺在架上没人拿。
2. face 是**严格制**：不写 face 或写 m-face 的树**不归本 tick**（缺省视为 m-face 由 TriMMC 侧承接）——两 tick 分工靠这个字段绝对切割。
3. 门 3 是"全部 pending 都带时间门才跳"（L145：`len(gated)==len(pending)`）——部分带门的节点先干，带门的等条件，不是一票否决。时间门正则 L90：`r"(≥?\s*\d+\s*(周|天|小时)|时间门)"`——节点 action 里写"≥3 天"这类字样即被识别。

### 1.2 锁、冷却、预算

- **锁**：`_lock_stale_or_absent`（L107）——O_EXCL 原子锁+进程存活判定，同刻单会话，死进程自动让位。
- **冷却**（L363）：`eligible = last.rc==0 or age > 1800`——上一轮**成功（rc=0）就不再重入**，失败或超 1800 秒才允许再来。`--监督模式`（L322）跳冷却但锁照查。
- **预算**：`_tokens_today`（L118）查台账——15 亿 token/日双门的 tick 侧实现位。
- **判重指纹**（L150）：`sorted(treeId, pendingNodes 元组)` 序列化——pending 集合没变=指纹没变=1800s 内不重入。

### 1.3 派工面

- `RFACE_SYSTEM_PROMPT`（L50）：R 面执行者人格底座（"autonomous worker, end-to-end"）。
- `_tree_brief`（L167）：树→BRIEF（含"Execute each pending node action yourself"+完成判定="All pending nodes done + top-level done + closeout commit pushed"，L203）。
- `build_governance_injection`（L237）：**LG-016 件 3 治理注入**——D-04/D-01/D-10 纪律从正身程序化提取+sha1-12 机器锚+"真源即模板"，`--print-injection` 可断言。纪律不再靠抄写进 prompt，靠运行时提取投影。
- `run_trilc_task`（L257）：spawn 主流程。

## 二、树合同（tree-op.json ↔ 三重门对应表）

| 字段 | 门/用途 | 合格值例 |
| --- | --- | --- |
| `status` | 门 1 | `"active"`（W35 收口树）/`"pending"`（W37 duty-night-patrol=躺架上） |
| `domainRouting` | 门 2 | `"server-executable"`（R 面通行证）；其他值（如 sg-duty-executable）走别的执行形态 |
| `face` | 面路由 | `"r-face"`（本 tick 认）；m-face/缺省归 TriMMC |
| `nodes[].status` | 门 3+派工范围 | `pending`（拾取对象）→执行后翻转 |
| `nodes[].action` | 门 3 正则扫描对象 | 含"≥N 天/时间门"字样=带门节点 |
| `sourceMaterials` | 卷封（开工验卷） | seal-materials --attach 写入的指纹数组 |

活体对照：W35 `p0fix1..4/trilc-lineage-merge`（active+done 全链，reports/ 齐备）vs W37 `duty-night-patrol`（pending+sg-duty-executable——双门未过，教学标本）。

## 三、工具族四件（scripts/fade/）

### 3.1 _fadehash.py（27 行）——单一 canonical 双 hash

`dual_sha256(p) -> (raw_sha256, bytes, lf_sha256)`：raw=字节原样，lf=行尾归一后。**存在的意义**：seal-materials（卷封）与 run-root（run 根）共享同一实现，防"两套 hash 各自漂移"（LG-008 双席调和案：CPO 单一 hash 纪律 × CTO 分文件结构，独立脚本+共享模块各得其所）。**SOFT-DRIFT 判据**（CTO-F6）：raw≠lf=行尾漂移，警告留痕**不按材料污染**处理——跨 Win/Unix 流转的现实宽容。

### 3.2 seal-materials.py（147 行）——卷封三态

`--attach`：算 sha256 写入 tree-op.json 的 sourceMaterials；**同 path 重复封=违例拒绝（封卷只许一次）**。`--verify`：逐项重算对照，全一致 exit 0；漂移 exit 2 逐项差异（开工验卷/收口对卷/编排层三处调用）。`--manifest`：只打印不改文件。

### 3.3 node-report-check.py（84 行）——节点翻转前置门（§2.7 立法落地）

校验三件：①`reports/node-<NODE-ID>.md` 存在；②内含 ```json fenced 块、键集 ⊇ **核心九键**（nodeId/agent/startedAt/finishedAt/baselineCommit/trigger/actions/artifacts/gateResults）；③散文必备三节（异常与处置/断点交接/使用依据，标题级匹配）。**退出码合同：0=过 | 2=缺失或不全（翻转门必须拦）| 3=用法错**。用法：`--tree-dir <树目录> --node <ID>...` 或 `--all --pending-from tree-op.json`。编排层收口对全部节点复跑=双门。

### 3.4 run-root.py（185 行）——run 根存照（v2，append-only）

run-root.json 合同（trilc-lineage-merge 实件）：`kind/version/treeId/producedAt/initialRoot/initialProvenance/root/algorithm/recompute_history[]`。**algorithm 口径**：按 path 排序，逐文件 `path\0raw_sha256\0lf_sha256` 拼接后 sha256（canonical=_fadehash.dual_sha256）。**append-only 铁律**：补算只能向 recompute_history 追加（实件里的 initialProvenance 就是 LG-008 高界评审补算案：董事会授权第三席复算+输入对照全记录）——**"永不覆盖"必须是代码路径而非注释口径**（LG-008 教训：初版 appendOnlyNote 写"另档新文件"却与覆盖写并存，验收实测抓出）。

## 四、节点报告与 run root 标本（trilc-lineage-merge，W35）

- `reports/node-TM-1.md`：**散文十节**（起止/基线 commit/触发来源/动作序列/工件清单/门禁结果/异常处置/断点交接/使用依据）+ **机读核心 fenced json 九键**——注意文件内注记"机读核心为 v1.4.1 格式增补（2026-08-28），事实同上散文节"：立法晚于运行的 run 是**回填增补**的，增补必须声明时点、事实同源，不重写叙事。
- `reports/run-root.json`：见 §3.4。`merge-log.md` 同目录——业务日志与协议工件分居，各是各的证据。

## 五、接手任务清单（第一周）

1. 读 tick 三重门段（L124-150）+ 冷却行（L363），对照 W37 pending 树与 W35 active 树各验一遍门判定（纸面推演，不动服务器）。
2. 本机跑工具族安全件：`node-report-check.py --tree-dir <W35 树> --all --pending-from <tree-op.json>`（只读校验）；`seal-materials.py --manifest <某文件>`（只打印）。**--attach/--verify 不在沙箱外试**。
3. 读 run-root.json 实件（trilc-lineage-merge），手验 algorithm 口径：按 path 排序逐文件三段拼接的复算路径想一遍。
4. 读 node-TM-1.md 一次，对照 node-report-check 九键清单逐键指认。
5. M 面 tick（TriMMC src/orchestration，TS）只读勘目录结构；sg 部署态差异以 API/台账读数为准，本机不直断。

**误区速查**：把 domainRouting 其他值当通行证／给 m-face 树找 R 面 tick 算账／手工翻节点 status 不过校验器／对行尾漂移按污染裁决（SOFT-DRIFT 是警告）／把 recompute_history 当可改写字段。

## 使用依据

- tick 全函数锚：TriRMC/scripts/rmc_tick.py 442 行（2026-09-07 实读：L50/L90/L107/L118/L124-150/L167/L203/L237/L257/L322/L363）
- 工具族四件全文：scripts/fade/（_fadehash 27/seal-materials 147/node-report-check 84/run-root 185 行）
- 标本：W35 trilc-lineage-merge（tree-op.json+merge-log.md+reports/node-TM-1.md+run-root.json 亲读）；W37 duty-night-patrol（pending 态亲读）
- 立法锚：fade-registry FADE-006 条映射表+LG-008 升格记录；spec §九卷封制（fade-pipeline-design v1.1）
- 未逐行实勘如实注：fade-watch.ps1（80 行）、TriMMC orchestration TS 模块、sg 部署态
