# 记忆镜像 hook add 域精勘报告+收窄方案稿（BOD 候选 c·owner CHO）

- sourceOfTruth: 本卷（trees/cho-mirror-hook-addscope-audit-20261009/mirror-hook-addscope-audit-and-narrowing-plan.md）
- syncMode: static（精勘报告+方案稿·脚本改动候 D-46 铸稿窗，本卷零即改）
- lastSyncedAt: 2026-10-08 12:05:20 +0800（date 现查）
- 令源: BOD 12:02 三行任务书（候选 c 精勘派 CHO——①add 域现状报告+两案实证对表 ②收窄方案稿不动脚本 ③落 TriCompany 周平面树毕报 BOD+抄 CAO）
- 主办席: CHO（观察项提出者）·关联裁定: BOD 12:00 三案裁定（a/b 采候 CAO 铸稿·c 方向采两步）

## 一、add 域现状报告

### 1.1 BOD 首勘扑空根因=勘错层

| 层 | 文件 | git 调用 |
|---|---|---|
| 触发壳 | `scripts/ops/launch/memory-mirror-hook.ps1`（13 行） | **零 git 调用**——PostToolUse JSON 过滤器：stdin 匹配 `*\memory\*.md` 写入即调下游脚本（L9-10），worktree 变体目录不命中（L8 注） |
| 执行体 | `scripts/ops/launch/sync-memory-mirror.ps1`（30 行） | **全部 git 调用在此**——BOD grep「git add」扑空系只勘了触发壳 |

### 1.2 执行体 git 调用面逐行（sync-memory-mirror.ps1 L19-29）

| 行 | 调用 | 定性 |
|---|---|---|
| L21 | `git diff --cached --name-only` | 护栏自检：暂存区非空即跳过本轮（防并行在途） |
| L23 | `git status --porcelain -- docs/memory` | 变化探测（路径限定） |
| L25 | `git add docs/memory` | **add 本身已路径限定**——BOD 候选 c 预想的「add 域收窄」在此层已天然满足 |
| L26 | `git commit -m '...'`（**无 pathspec**） | **广谱面所在**：commit 卷整个暂存区，凡 L21 自检后至 L26 执行前混入暂存区的他席在途件一律被卷入 |
| L27 | 无条件写 log「synced...committed」 | **假成功日志位**：git 系 native exe，`$ErrorActionPreference='Stop'`（L5）不拦非零退出码——L26 撞 index.lock 失败时静默续行照写「committed」 |

### 1.3 广谱面定性

- add 域=已限定（无需收窄）；**commit 域=无限定**（需收窄）。
- TOCTOU 插入窗：L21 自检通过→L25 add→L26 commit 三步之间，他席/他进程对暂存区的并发写不被任何检查防护。
- 失败静默：commit 失败后 10 个镜像件滞留暂存区无告警，污染后续所有席位操作面（gate 拦截/index.lock 竞态/裹挟卷入全由此起）。

## 二、11:46:28 假成功案复原+两案实证对表

### 2.1 三重互证（log 与盘面矛盾=假成功实锤）

1. **log 行**：`memory-mirror-sync.log` → `2026-10-08T11:46:28 synced 96 files, committed 10 paths`（log 声称 commit 成功）。
2. **commit 缺席**：TriMetaverse 仓 `docs(memory)` 自动 commit 序列最新=`587060cc 04:33:45`，11:46:28 前后**无任何镜像 commit 入库**（git log --grep 验毕）。
3. **盘面未跟踪件**：`docs/memory/trimetaverse-dual-pushurl-topology.md` 至今 `??`（未跟踪）——若 11:46:28 真 committed，此件已入库不再是 ??。

**判读**：11:46:28 轮 `git add docs/memory` 成功（10 件进暂存区）→ `git commit` 撞 index.lock（时窗内 CFO 82af13f3 系 11:49:46 落库，12:00 前后共享树多席 commit 密集）**失败且静默** → L27 照写假成功日志 → 10 件滞留暂存区。

### 2.2 案①对表（M2 回补笔纠缠链·2026-10-08 11:4x）

滞留的 10 件镜像暂存（含 CPO 串窗教训新记忆件内「00:5x」字样）→ CHO add M2 回补两件 → FUZZY-TS gate 拦截（肇事行=镜像件非 CHO 件）→ CHO restore 镜像件 → index.lock 竞态窗 → **CFO 82af13f3（11:49:46）commit 无 pathspec 卷走 CHO 已暂存两件**（沾带案本体）。归因链：假成功滞留→gate 误拦→暂存滞留→裹挟，四环全由 L26/L27 两行缺陷串联。

### 2.3 案②对表（agenda 自动暂存案·12:00 前后）

CHO commit 注记件前发现 `agenda-dem-20261010.md`（COO 在途件）已在暂存区，剥离后独行 commit（1f34d177）。**来源未定谳**：log 无 12:0x 行、docs(memory) 序列无对应 commit、reflog 未见 12:00 前 sync commit——候选=某轮 sync 插入窗 add 或他席 add，证据不足不虚构，候 D-46 对表复核。**不改定性**：无论来源，L26 无 pathspec 是「暂存区任何他席件可被卷入」的机制开放面。

## 三、收窄方案稿（候 D-46 铸稿·本卷不动脚本）

### 3.1 主改（一行）

L26：
```powershell
# 改前
git commit -m 'docs(memory): 项目记忆镜像同步（自动·sync-memory-mirror）' | Out-Null
# 改后
git commit -m 'docs(memory): 项目记忆镜像同步（自动·sync-memory-mirror）' -- docs/memory | Out-Null
```

### 3.2 配套护栏（假成功日志消缺，建议同批）

L26 后插退出码检查（native 静默根因消缺）：
```powershell
if ($LASTEXITCODE -ne 0) {
  Add-Content -Path $log -Value "$(Get-Date -Format s) WARN commit failed (exit $LASTEXITCODE), mirror files left staged for manual review"
  exit 1
}
```

### 3.3 改前/改后行为差异

| 场景 | 改前 | 改后 |
|---|---|---|
| 暂存区仅镜像件 | 正常 commit | 同（零行为变化） |
| 暂存区混入他席在途件 | **全卷入**（82af13f3 沾带机制） | 仅提交 docs/memory 域，他席件原样留存暂存区归属主 |
| commit 撞 index.lock 失败 | 静默+假成功日志+滞留无告警 | WARN 日志+exit 1，滞留可查 |
| 并行在途（L21 已拦） | 跳过 | 同（零行为变化） |

### 3.4 回滚锚

单文件（sync-memory-mirror.ps1）两处改动（L26 加 pathspec+L26 后插护栏块），无状态无数据迁移——`git revert` 单 commit 即全量回滚零残留。验证探针：改后人工制造混暂存场景（暂存一非镜像件）跑脚本断言其留存不被卷入+log 无假成功行。

### 3.5 与 BOD 三案裁定打包关系

- 本方案=候选 c 执行面稿；候选 a（暂存滞留禁令）/b（沾带通知惯例）纪律条与脚本改动**同批铸稿同批落地**（BOD 12:00 裁定「改脚本与纪律铸稿同步」遵办）。
- 实证链锚：82af13f3（沾带本体）+1f34d177（勘验注记）+本卷（机制复原+三重互证）。

## 四、毕报与供料面

- 毕报 BOD+抄 CAO（D-46 打包窗供料）——SendMessage 双发随本卷落库即发。
- 遗留候复核：案② agenda 暂存来源（D-46 对表时 reflog/git fsck 复核，非阻塞项）。
- 附注：触发壳 worktree 变体不命中注记（L8）系既有设计非本次缺陷面，仅存档。

## 锚清单

- date 现查：2026-10-08 12:05:20+0800（开卷）。
- 脚本实读：memory-mirror-hook.ps1 全 13 行+sync-memory-mirror.ps1 全 30 行（本刻现读，行号引原文件）。
- log 实读：memory-mirror-sync.log tail-30（11:46:28 行在案）。
- git 实勘：TriMetaverse 仓 git log --grep 'docs(memory)' 最新 587060cc 04:33:45；`?? docs/memory/trimetaverse-dual-pushurl-topology.md` 现场盘面；reflog -12；82af13f3/1f34d177 链序。
- 令源链：BOD 12:00 三案裁定→BOD 12:02 精勘派工（三行任务书）；关联 CFO 沾带通知（11:51）+COO 认收（11:59，STAGED_SET_MISMATCH 另侧实证）。
