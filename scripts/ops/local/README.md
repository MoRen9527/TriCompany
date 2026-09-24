# restore-claude-config — Claude Code 配置一键恢复（3333 兜底·LG-041 ③）

- 设计正身：`TriMetaverse/docs/workflow/operating-records/2026-W39/trees/tri-model-3333-incident/bottleneck-architecture-plan-v2.md` §三
- 紧要目标：3333 挂时，配置恢复**一条命令内完成**（带外通道：零 3333/daemon/网络依赖）
- 实施席：DE（TriDeployer）；落位：本目录=真源化域（TriCompany 源侧），本机部署位=dev 机 TriCompany 工作区同径 + `~/.claude/settings.presets/`

## 文件清单

| 文件 | 用途 |
| --- | --- |
| `restore-claude-config.ps1` | 一键恢复脚本（PowerShell 5.1+，Windows 出厂自含）；内置占位符凭据防呆（含 `PLACEHOLDER` 的预设拒切） |
| `presets/direct.json` | 直连 bigmodel 官方端点 + glm-5.3-flash 正典 ID；**仓库侧=占位符形**（凭据=`GLM_API_KEY_PLACEHOLDER__DEPLOY_INJECT`） |
| `presets/relay-3333.json` | **dev 机部署日生成**（`-CaptureRelay` 现役固化；本域不预置，防跨机编造 env 形） |

## 密钥卫生红线（CTO 复验 2026-09-24 增）

**真钥预设永不入 git。** 仓库内 `presets/direct.json` 永为占位符形；真钥版预设仅存本机部署位 `~/.claude/settings.presets/direct.json`（与 `settings.json` 同位级卫生），部署日自本地密钥源注入。脚本对含 `PLACEHOLDER` 的预设 fail-closed 拒切。

## 用法

```powershell
restore-claude-config.ps1                 # 切 direct（缺省，安全侧默认）
restore-claude-config.ps1 -Mode relay     # 切回 3333 中转现役形
restore-claude-config.ps1 -CaptureRelay   # 部署日一次性：现役 settings.json env 固化为 relay-3333.json
```

行为：备份现 settings.json（`.bak-<ts>`，轮换保留近 5 份）→ 预设 env 子集原子覆写（temp+rename）→ 输出结果行。
只覆写预设 env 子集键，settings.json 其余键值级保留（最小侵入，与 TriModel claude-fallback 写形同语义）。

## dev 机部署 checklist（m-cos 对接版·每锚单命令；通道=CTO 裁定交互位 COS）

执行序：**①对齐仓 ②注入真钥 ③语法冒烟 ④CaptureRelay ⑤四锚**。`%TC%`=dev 机 TriCompany 工作区根。

**① 仓对齐（注意：sg origin 的 LG-041 提交已经 force 重写——勿 pull merge，须硬对齐）**
```
git -C %TC% fetch origin
git -C %TC% reset --hard origin/dev
git -C %TC% reflog expire --expire=now --all && git -C %TC% gc --prune=now   （若此前拉过含钥旧版，清本地史）
```

**② 注入真钥（本地密钥源二选一：dev 现役 settings.json 的 token / BOD·CEO 供急救夜原 key）**
```powershell
powershell -NoProfile -Command "$src=Get-Content \"$env:USERPROFILE\.claude\settings.json\" -Raw | ConvertFrom-Json; $k=$src.env.ANTHROPIC_AUTH_TOKEN; $d=\"$env:USERPROFILE\.claude\settings.presets\"; New-Item -ItemType Directory -Force $d | Out-Null; ((Get-Content \"%TC%\scripts\ops\local\presets\direct.json\" -Raw) -replace 'GLM_API_KEY_PLACEHOLDER__DEPLOY_INJECT',$k) | Set-Content \"$d\direct.json\" -Encoding UTF8"
```
（示例=以本机现役 settings.json token 注入；钥值全程不经 checklist/日志/transcript）

**③ 语法冒烟（sg 无 pwsh 未预验——如实项，此步必做；注入前占位符态跑应得拒切报错=防呆自检通过）**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "%TC%\scripts\ops\local\restore-claude-config.ps1"
```
期望输出：`已切换至 direct，备份于 ...`

**④ CaptureRelay（3333 健康日执行一次，固化 relay 形）**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "%TC%\scripts\ops\local\restore-claude-config.ps1" -CaptureRelay
```

**⑤ 验收四锚（规格表 §三）**

1. **两预设合法 JSON**：
   `powershell -NoProfile -Command "ConvertFrom-Json (Get-Content \"$env:USERPROFILE\.claude\settings.presets\direct.json\" -Raw); ConvertFrom-Json (Get-Content \"$env:USERPROFILE\.claude\settings.presets\relay-3333.json\" -Raw); 'ANCHOR1 OK'"`
2. **双向切换实证**：`-Mode relay` → 查 settings.json env `ANTHROPIC_BASE_URL` 含 `:3333` → direct 切回 → 查 BASE_URL=`https://open.bigmodel.cn/api/anthropic`；
3. **备份轮换实证**：连续切换 ≥7 次后：
   `powershell -NoProfile -Command "(Get-ChildItem \"$env:USERPROFILE\.claude\" -Filter 'settings.json.bak-*').Count"` → ≤5 且保留最新；
4. **断网演练**：断 3333/断网状态下执行切换成功（纯本地文件操作，应天然通过）。

## 回滚

- 任一次切换后异常：取最新 `settings.json.bak-*` 拷回 `settings.json`；
- 或再执行一次对侧切换（direct↔relay 互为回滚）；
- 真源回退：git revert 本目录提交。

## 边界

不装 cc-switch、不建 proxy、不动 3333/watchdog；弃用本脚本不伤现役配置（最小侵入只覆 env 子集）。

## 部署凭据注记（DE 落笔，CTO 复验后终形）

仓库侧 direct.json=占位符形（红线见上）；真钥注入在 dev 机部署位完成（checklist ②）。direct 凭据候选=sg 现役 settings.json 活 token（49 位）或 BOD/CEO 供急救夜原 key（CTO 不持有，实测路由 BOD/CEO）；dev 侧首次部署后一条验证：`-Mode direct` 后起测试会话或 curl 直连端点实测。**含钥旧版（aec6650）若曾被 dev 侧拉取，本地史面清指令见 checklist ①；该 key 无论重写与否标「候轮换」入台账。**
