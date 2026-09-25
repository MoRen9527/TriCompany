# restore-claude-config — Claude Code 配置一键恢复（3333 兜底·LG-041 ③）v2

- 设计正身：`TriMetaverse/docs/workflow/operating-records/2026-W39/trees/tri-model-3333-incident/bottleneck-architecture-plan-v2.md` §三
- 修复正身：TASK-INCIDENT-SDE-SETTINGS-01 CTO 复盘报告 §六 修-1..6（`TriMetaverse/docs/workflow/operating-records/2026-W39/trees/incident-sde-settings-01/cto-review-report.md`）
- 事故档案：同目录 `FROZEN-NOTICE-restore-claude-config-20260925.md`（2026-09-25 活体覆写事故；冻结笔 TC dev `897b0da`，解冻=BOD 验收 revert）
- 紧要目标：3333 挂时，配置恢复**一条命令内完成**（带外通道：零 3333/daemon/网络依赖）
- 实施席：DE（TriDeployer）原版 / FSD v2 修复（2026-09-25）；落位：本目录=真源化域（TriCompany 源侧），本机部署位=dev 机 TriCompany 工作区同径 + `~/.claude/settings.presets/`

## v2 修复摘要（对照事故五缺陷）

| 缺陷（FROZEN-NOTICE §二） | v2 落法 |
| --- | --- |
| ①空串凭据无防呆 | 修-1 凭据健康门：PLACEHOLDER/空串/纯空白 三态全拒（fail-closed） |
| ②注钥序依赖活体现役 | 修-2 `-InjectKey`：keyfile(`.deploy-key`) > 活体双键探测 + 非空断言（空即 Fail 禁注入） |
| ③测试无隔离 | 修-3 `-WhatIf` 全路径干跑 + `-TargetDir` 沙箱目标 + 活体路径警告 + `FROZEN-BACKUPS` 轮换豁免 |
| ④事后自验缺 token 断言 | 修-4 写后回读断言（非空+值一致+JSON 合法）+失败自动回滚 + `-SmokeTest` auth 冒烟 |
| ⑤事故后零报告零回滚 | 修-6 结构化结果行 `RESULT`/`FAIL`（完成即报可粘贴载体）；强制步条款归制度面（P-4） |
| ②-6 双键形歧义（复盘增补） | 修-5 仓库模板单键制 + 注入键形同形生成（见〈双键语义注〉） |

## 文件清单

| 文件 | 用途 |
| --- | --- |
| `restore-claude-config.ps1` | 一键恢复脚本 v2（PowerShell 5.1+，Windows 出厂自含）；参数面：`-Mode` / `-WhatIf` / `-TargetDir` / `-InjectKey` / `-CaptureRelay` / `-SmokeTest` / `-SelfTestBreakAssert`（测试钩子，生产禁用） |
| `presets/direct.json` | 直连 bigmodel 官方端点 + glm-5.3-flash 正典 ID；**仓库侧=占位符形；v2 单键制**（仅 `ANTHROPIC_AUTH_TOKEN` 单占位符） |
| `presets/relay-3333.json` | **dev 机部署日生成**（`-CaptureRelay` 现役固化；本域不预置，防跨机编造 env 形） |

## 密钥卫生红线（CTO 复验 2026-09-24 增；v2 扩）

**真钥预设永不入 git。** 仓库内 `presets/direct.json` 永为占位符形；真钥版预设仅存本机部署位 `~/.claude/settings.presets/direct.json`。**独立钥源**=部署位 `settings.presets/.deploy-key`（部署日 BOD/CEO 供钥落位，`.gitignore` 已防仓内手滑）。脚本值脱敏：钥值全程不经输出/日志/transcript（干跑 diff 与 RESULT 行凭据键只出 `len=<n>`）。

## 沙箱纪律（v2 新增·事故直接产物）

1. **测试/锚验证必须 `-TargetDir <沙箱目录>`**——缺省目标=活体 `$HOME\.claude`，脚本将打印醒目警告行；2026-09-25 事故（对活体连跑覆写）根因形态零容忍；
2. **`-WhatIf` 全路径干跑**：打印将写入的键值 diff（凭据脱敏），零写动作（含备份与目录创建均不发生）；
3. **`FROZEN-BACKUPS` 轮换豁免**：目标目录放置同名哨兵文件即跳过 `.bak-*` 轮换（防回滚锚被轮换自毁——事故 ②-3 加重项；P-3 脚本级前置落法）；
4. 写后断言失败**自动回滚**（本次备份拷回）并 `FAIL | code=1`。

## 用法

```powershell
restore-claude-config.ps1                              # 切 direct（缺省，安全侧默认）——活体路径打印警告
restore-claude-config.ps1 -Mode relay                  # 切回 3333 中转现役形
restore-claude-config.ps1 -WhatIf                      # 全路径干跑：键值 diff，零写动作
restore-claude-config.ps1 -TargetDir C:\temp\sandbox   # 沙箱目标（测试/锚验证必须用此）
restore-claude-config.ps1 -InjectKey                   # 部署日注钥：keyfile > 活体双键探测 → 生成部署位预设
restore-claude-config.ps1 -CaptureRelay                # 部署日一次性：现役 env 固化为 relay-3333.json
restore-claude-config.ps1 -SmokeTest                   # 切换后 auth 冒烟（增强非前置，网络不可达自动跳过）
```

行为：备份现 settings.json（`.bak-<ts>`，轮换保留近 5 份，哨兵豁免）→ 凭据健康门 → 预设 env 子集原子覆写（temp+rename）→ 写后回读断言（失败自动回滚）→ 结构化结果行。
只覆写预设 env 子集键，settings.json 其余键值级保留（最小侵入，与 TriModel claude-fallback 写形同语义）。

退出码：`0`=成功（含干跑）；`1`=写后断言失败（已自动回滚）/ auth 冒烟 401·403；`2`=前置 fail-closed（健康门/钥源空/预设缺/JSON 坏/模式互斥）。

## dev 机部署 checklist v2（m-cos 对接版；**全锚沙箱化**——原活体实证锚 v2 起废止）

执行序：**①对齐仓 ②注入真钥 ③沙箱冒烟 ④CaptureRelay ⑤锚电池 v2**。`%TC%`=dev 机 TriCompany 工作区根；`%SB%`=沙箱根（如 `%TEMP%\restore-sandbox`，先 `mkdir %SB%` 并预置假活体）。

**① 仓对齐（注意：sg origin 的 LG-041 提交已经 force 重写——勿 pull merge，须硬对齐；解冻后本节随 BOD revert 同步）**
```
git -C %TC% fetch origin
git -C %TC% reset --hard origin/dev
git -C %TC% reflog expire --expire=now --all && git -C %TC% gc --prune=now   （若此前拉过含钥旧版，清本地史）
```

**② 注入真钥 v2（`-InjectKey`；原单键一行式命令 v2 废止）**

钥源优先级：**独立 keyfile** `%USERPROFILE%\.claude\settings.presets\.deploy-key`（部署日 BOD/CEO 供钥落位，首选）> **活体现役**（双键探测 AUTH_TOKEN/API_KEY 取非空者）。钥源全空=脚本 fail-closed 拒注入（事故 ②-2 拦截）。
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "%TC%\scripts\ops\local\restore-claude-config.ps1" -InjectKey
```
（键形按活体非空键名同形生成（修-5）；钥值全程不经 checklist/日志/transcript，输出只有钥源与 `len=<n>`。）

**③ 沙箱冒烟 v2（原「语法冒烟」沙箱化；占位符态应得健康门拒切=防呆自检）**
```powershell
mkdir "%SB%" 2>nul & echo {"env":{"ANTHROPIC_BASE_URL":"https://example.invalid"}}> "%SB%\settings.json"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TC%\scripts\ops\local\restore-claude-config.ps1" -TargetDir "%SB%" -WhatIf
```
期望：干跑 diff 打印（凭据 `len=` 脱敏）+ `[WhatIf] 干跑完成，零写动作`；占位符态实切（去 `-WhatIf`）应得 `FAIL | code=2`（凭据健康门拒切）。

**④ CaptureRelay（3333 健康日执行一次，固化 relay 形；活体固化=部署日显式授权动作）**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "%TC%\scripts\ops\local\restore-claude-config.ps1" -CaptureRelay
```

**⑤ 验收锚电池 v2（规格表 §三 沙箱版）**

1. **两预设合法 JSON**（部署位）：
   `powershell -NoProfile -Command "ConvertFrom-Json (Get-Content \"$env:USERPROFILE\.claude\settings.presets\direct.json\" -Raw); 'ANCHOR1 OK'"`
2. **双向切换实证（沙箱）**：`-TargetDir "%SB%" -Mode relay` → 查 `%SB%\settings.json` env `ANTHROPIC_BASE_URL` 含 `:3333` → direct 切回 → 查 BASE_URL=`https://open.bigmodel.cn/api/anthropic`；每步 RESULT 行 `assert=pass`；
3. **备份轮换实证（沙箱）**：连续切换 ≥7 次后 `(Get-ChildItem "%SB%" -Filter 'settings.json.bak-*').Count` → ≤5 且保留最新；**豁免实证**：放 `%SB%\FROZEN-BACKUPS` 哨兵后连切，备份数不减少且 RESULT 行 `rotation=轮换跳过`；
4. **断网演练（沙箱）**：断网状态执行切换成功（纯本地文件操作，应天然通过）；`-SmokeTest` 断网时输出 `跳过（网络不可达）不阻塞`；
5. **写后断言/自动回滚实证（沙箱，测试钩子）**：`-TargetDir "%SB%" -SelfTestBreakAssert` → 应得 `FAIL | code=1`（写后断言失败+已自动回滚），且 `%SB%\settings.json` 内容==最新备份内容；
6. **auth 冒烟实证（部署位真钥态）**：`-SmokeTest` → RESULT 行 `smoke=PASS（HTTP 2xx）`；401/403 时 `FAIL | code=1`（凭据被拒，核查钥值/键形）。

## 双键语义注（修-5）

仓库模板 v2 起**单键制**（仅 `ANTHROPIC_AUTH_TOKEN` 单占位符）——v1 双键同占位符形废止（键名错位=事故第一清空点指令层根因）。部署日 `-InjectKey` 按活体非空键名**同形生成**预设（活体 known-good 键形=权威形；活体双键全空的灾备态缺省 `ANTHROPIC_AUTH_TOKEN` 并在 RESULT 行 `keyshape=default` 标注）。Claude Code 认证面 AUTH_TOKEN/API_KEY 双键并存的消解优先级**版本敏感**（2026-09-15 核查在案，引 memory `claude-code-model-env-semantics`）——单键制+同形生成即为此歧义的规避落法。

## 回滚

- 脚本级：写后断言失败**自动回滚**（本次备份拷回）；
- 手动级：任一次切换后异常，取最新 `settings.json.bak-*` 拷回 `settings.json`；或再执行一次对侧切换（direct↔relay 互为回滚）；
- 事故级：目标目录放 `FROZEN-BACKUPS` 哨兵冻结轮换后再排查（防回滚锚被轮换淘汰）；
- 真源回退：git revert 本目录提交。

## 边界

不装 cc-switch、不建 proxy、不动 3333/watchdog；弃用本脚本不伤现役配置（最小侵入只覆 env 子集）。

## 部署凭据注记（DE 落笔，CTO 复验后终形）

仓库侧 direct.json=占位符形（红线见上）；真钥注入在 dev 机部署位完成（checklist ②）。direct 凭据候选=独立 keyfile（BOD/CEO 供钥，v2 首选）或活体双键 fallback；dev 侧首次部署后一条验证：`-SmokeTest` 冒烟（锚 6）。**含钥旧版（aec6650）若曾被 dev 侧拉取，本地史面清指令见 checklist ①；该 key 无论重写与否标「候轮换」入台账。**
