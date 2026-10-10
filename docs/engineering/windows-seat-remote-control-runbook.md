# Windows 席位窗口远控 runbook（代发命令/键入标准作业）

- sourceOfTruth: 本件
- syncMode: source-only
- lastSyncedAt: 2026-10-10T17:29+0800
- 缘起: CEO 令（2026-09-17 04:0x）——操作经验属 Windows 系统运维面，自 M 面优劣档案（`docs/product/m-face-strengths-and-limits.md`）迁出独立成文（时位=TriMetaverse 项目维度）
- **升维迁移（2026-10-10 17:27 CEO 令）**：通用能力进公司维度——正身自 `TriMetaverse/docs/execution/windows-seat-remote-control-runbook.md` 迁入本位（TriCompany/docs/engineering/，与 render-pipeline-runbook 同族），项目侧原位改指针；公司纪律登记由 CAO 知会链承接
- 适用: 本机（M 面 dev 机）代席位窗口键入/代发命令（如代发 `/compact`、跨窗派工、触发回合）；对照 sg 面=tmux `send-keys` 原生等价能力。**公司维度通用能力——各项目工作区（TriMetaverse/TriModel/TriRLC/TriRMC 等）同构适用，不绑单一项目**

## 一、已知坑位（实证累积：2026-09-17 四连败 + 2026-10-10 wt 多 tab 增量）

| 坑 | 实证 |
| --- | --- |
| SendKeys 直打中文→乱码 | "ack" 经微软拼音中文态组词成"啊惭愧" |
| 单回车易吞 | 文本进框、Enter 不生效（多轮复现） |
| VS Code 多 tab / 同进程第二窗无法唯一定位 | Get-Process MainWindowTitle 只报进程主窗 |
| Win11 前台锁 | AppActivate 可返回 True 但焦点未动（后台改焦点被拒） |
| CLAUDE_CODE_CHILD_SESSION=1 环境遗传 | BOD shell 代起的 claude 被标记子会话：不存转录/不注册名址/ListAgents 不可见（根因由 CEO 从窗口 banner 排出） |
| wt 多 tab 拓扑回车吞噬加重 | WindowsTerminal 单进程多 tab（13 tab 实例）：ENTER 双发 350ms 被吞（五步全绿但转录 4h 零动）；三发间隔 ≥450ms 过（2026-10-10 m-cos 两轮对照实证，唯一差异变量） |

## 二、远控五步法（已验证：/compact 送达 m-cos 并完成压缩，09-17 03:46；2026-10-10 复验：m-cos 中文打招呼全链通+ack 回）

1. **找窗**：`EnumWindows` P/Invoke 全量枚举可见窗（Get-Process 只报主窗会漏同进程第二窗），按标题含席位名取句柄（hWnd）。
2. **切焦点**：先发 ALT 键（`keybd_event(0x12,0,0,…)` down + `(…,0,2,…)` up 解前台锁）→ `SetForegroundWindow(hWnd)` → **`GetForegroundWindow()` 比对句柄验证**——不等即中止，绝不盲发。
3. **输文本**：`Set-Clipboard` → SendKeys `^v` 粘贴（绕 IME 组词，中英文免疫）——**禁直打**（中文必乱码，ASCII 也可能被组词）。
4. **提交**：先 `{ESC}` 清输入框（防残串拼接保险步）→ `{ENTER}` **三发、每发间隔 ≥450ms**（单发易吞；wt 多 tab 拓扑下双发 350ms 实证也被吞——2026-10-10）。
5. **守卫**：每步校验失败即中止不发（激活 False 照发=违断链纪律，初试实录在案）。

## 三、BOD 代起常驻 claude 进程前置

凡经 BOD shell 代起常驻 claude（继承 `CLAUDE_CODE_CHILD_SESSION=1`）：

```powershell
Remove-Item Env:CLAUDE_CODE_CHILD_SESSION -ErrorAction SilentlyContinue
$env:CLAUDE_CODE_FORCE_SESSION_PERSISTENCE = "1"
claude --resume <名> -n <名> --agent <PascalCase正名> --verbose --dangerously-skip-permissions --append-system-prompt-file <手册路径>
```

- **`--agent` 必须用 PascalCase 正名**（`CEOChiefOfStaff`/`ChiefFinancialOfficer`/`FSD`/`STE`/`RAndDTrainer`…）——kebab 文件名形（`ceo-chief-of-staff`）本机 2.1.273 与 sg 2.1.227 均拒绝（"not found"）；本版交互路径对无效名不致命但**静默不生效**（2026-09-17 实证：进程活着但 agent 层未挂，终验问询坐实）。

不清标记的后果：子会话态=不存转录、不注册名址（ListAgents 不可见/按名 SendMessage 不可达）——2026-09-17 COS 复活窗实证，修复后名册 13/13 复原。

**实操捷径**：把上述清理+启动逻辑存为 `launch-<席>.ps1`（样板：`.fade/launch-m-cos.ps1`，含清变量/设持久化/切工作目录/正名拉起四步），代起或复活只敲 `powershell -File <脚本>` 一行——避免长命令跨窗粘贴被啃（R 被吃/| 变 I 实证，2026-09-17）。

**worktree 起席**（2026-09-22 起）：参数化启动器 `TriCompany/scripts/ops/launch/launch-seat.windows.ps1` 支持可选 `-WorkingDir`（默认 `D:\Code\ai\TriMetaverse` 主仓，向后兼容）——例：`pwsh -File D:\Code\ai\TriCompany\scripts\ops\launch\launch-seat.windows.ps1 -Name <名> -Agent <PascalCase正名> -Manual <kebab手册名> -WorkingDir D:\Code\ai\TriMetaverse-worktrees\board`，工作目录与手册路径跟随同树（起席读该树 compass 发布拷贝，防跨树版本错位）。

## 四、单次调用要点

- PowerShell 工具每调用=新会话：`Add-Type`（P/Invoke 类）与使用**必须在同一调用内**（跨调用不存活）。
- **mode 态易碎**：键序误触会循环切走会话模式（bypass→plan→auto→manual 实证），manual 态下目标席全部命令卡审批弹窗——**每次远程操作后必须核屏底 mode 指示条**，偏离即 S-Tab 循环复位（逐次 capture 验证）。
- **生产故障态兼作测试夹具时，夹具消费排在测试就绪之后**：待验证的卡点（如候裁决实例）勿用旧通道提前解除——先部署验证通道，再让夹具流经新通道完成双重验证（2026-09-18 实证：A′ 裁决提前消费致 E2E 改用合成试信）。
- 结果验证双通道：转录文件 mtime/追加（`~/.claude/projects/**/*.jsonl`）+ 目标席 SendMessage 回执。
