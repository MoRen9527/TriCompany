<#
triladder.ps1 — TriModel 恢复阶梯执行面（LG-053 §一/§二/§三 · batch-15 件①）

设计正身: TriMetaverse docs/workflow/operating-records/2026-W40/trees/bod-pipeline-batch-12/lg053-recovery-ladder-final.md（v1.0 终稿 §一四态/§二阶梯/§三介入点）
接口正身: 同周 trees/bod-pipeline-batch-13/lg053-interface-review.md（CTO 技审两条款·采纳裁态+v1.1 合流定义直采）
铸: FSD 小全（m-fsd）2026-10-03 · BOD 复工令（return-to-work-batch-15.md 2ec7dfe4）+CEO 01:38 亲裁追认

四态判定（§一·探活双面制: healthz 进程面+功能探针业务面 两探皆判）:
  T-OK    = 端口通 + healthz 2xx + 功能探 2xx
  T-1     = 端口通 + 功能探 5xx/503 族（重试可愈）
  T-2     = 端口通 + healthz 2xx + 功能探 401/403（写面未启用·401 配置族，重试不可愈）
            detail=probe-unauthenticated（探针未持令形，带令复探再判）/ auth-rejected（带令仍拒=真 T-2）
  T-3     = 端口死（-Pid 给出且进程活=T-3 进程活端口死；否则=T-3 全亡，全亡并入注记照 §一）

A1-A3（§二·逐级触发留痕；默认全部干跑，真动作必须 -Execute）:
  a1  重启:   前置=probe 判 T-1/T-3；防环=watchdog 窗口检查（细则 3，≤5min 复活且已 T-OK 则拒触发）；
              动作=token 门优雅停（POST /shutdown，-ShutdownToken/-ShutdownTokenEnvFile）+启动器拉活（-Launcher）；
              （Rider② CTO 裁卷 2026-10-03：shutdown 头默认 Authorization Bearer=daemon 门内建 fallback 实际可达；
                daemon 认证门收紧时须显式传 -TokenHeader X-Internal-Token）——仅注释，代码行为零动；
              后置=probe 回归读数+5min 探活回归纪律注记+P1 通报行
  a2  重建:   配置面子件=restore-claude-config.ps1 调用（本文件同目录，接口透传）；进程面子件=dist 重建
              （npm run build，工作目录 -AppDir）——两子件并列显式分列（意见书条款 1 修改①：restore=配置面子件，
              进程面子件并列另列，防「调了 restore 就当 A2 完了」覆盖误读）
              前置=回滚锚 declared（-RollbackAnchor 必填）+值席判位（-Judge 声明，P2）
  a3  回退:   配置 bak 链点选回滚（-Backup 显式路径；回滚前 JSON 合法校验前置，意见书条款 1 合流定义）；
              git revert/端口宿主拓扑维度=restore 面之外独立执行（提示行，本工具不代执行）
              前置=BOD 裁门（-BodGate <裁决凭据串>，P3；缺省拒执行）

边界: R-HY 域不触（进程面切分照 CTO 意见书条款 1 修改②——本工具=本机域形）；3333 退役面不入框架；
      零敏感值出机（token 只存在进程 env/参数，RESULT 行零值面）；frozen 纪律。

用法:
  triladder.ps1 probe  -Port 8712 [-Pid <pid>] [-HealthPath /health] [-ProbePath /v1/models] [-EnvFile <path>] [-Json]
  triladder.ps1 probe  -Port 8711 -HealthPath /healthz -ProbePath /internal/v1/models -EnvFile <channel.cmd>
  triladder.ps1 a1     -Port 8712 -Launcher <cmd> [-ShutdownPort 8712 -ShutdownTokenEnvFile <env>] [-Execute]
  triladder.ps1 a2     -AppDir D:\Code\ai\TriModel -RollbackAnchor <锚描述> -Judge <值席名> [-RestoreMode direct] [-Execute]
  triladder.ps1 a3     -Backup <bak路径> -Target <现役文件> -BodGate <裁决凭据> [-Execute]
#>
[CmdletBinding()]
param(
  [Parameter(Position = 0)]
  [string]$Command,

  # probe 参数
  [int]$Port = 0,
  [int]$Pid2 = 0,            # -Pid 与自动变量冲突，用 -Pid2；兼容别名下方处理
  [string]$HealthPath = '/health',
  [string]$ProbePath = '/v1/models',
  [string]$EnvFile = '',
  [string]$TokenKey = '',          # 显式令键名；缺省自动序 TRILC_INTERNAL_TOKEN→TRIMODEL_API_TOKEN
  [string]$TokenHeader = 'Authorization',  # daemon 门=TRILC_INTERNAL_TOKEN 可用 X-Internal-Token（裸值）；默认 Bearer
  [switch]$Json,

  # a1 参数
  [string]$Launcher = '',
  [int]$ShutdownPort = 0,
  [string]$ShutdownToken = '',
  [string]$ShutdownTokenEnvFile = '',
  [switch]$Execute,

  # a2 参数
  [string]$AppDir = '',
  [string]$RollbackAnchor = '',
  [string]$Judge = '',
  [string]$RestoreMode = 'direct',

  # a3 参数
  [string]$Backup = '',
  [string]$Target = '',
  [string]$BodGate = ''
)

# -Pid 别名（-Pid 与 PowerShell 自动变量 $PID 冲突，参数名用 Pid2，此处接受 -Pid 形参）
if (-not $Pid2 -and $MyInvocation.BoundParameters.ContainsKey('Pid')) { $Pid2 = $MyInvocation.BoundParameters['Pid'] }

$ErrorActionPreference = 'Stop'
$stateFile = Join-Path $PSScriptRoot 'triladder-state.json'
$script:ts = { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ') }

function Fail([string]$msg) {
  # 参数校验门：stderr+exit 2——不走 Write-Error（脚本 EAP=Stop 下抛 terminating
  # 异常，exit 2 永不到达，校验门失效；实测在案）
  [Console]::Error.WriteLine($msg)
  exit 2
}

function Save-State([hashtable]$s) {
  $s['ts'] = & $script:ts
  # 龄算用 epoch 秒：ConvertFrom-Json 会把 ISO 串自动转 datetime 且 Kind 面降级
  # （Unspecified/Local），再 Parse 二次转换必漂——epoch 整数零时区零文化坑。
  $s['tsEpoch'] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  $s | ConvertTo-Json -Depth 4 | Set-Content -Path $stateFile -Encoding UTF8
}

function Read-EnvKey([string]$file, [string]$key) {
  # 从 env/cmd 文件读键值（零回显；供 token 门/探针令）——5.1 兼容逐行解析
  if ([string]::IsNullOrEmpty($file) -or -not (Test-Path $file)) { return '' }
  foreach ($line in (Get-Content $file)) {
    if ($line -match ('^\s*(?:set\s+)?' + [regex]::Escape($key) + '\s*=(.*)$')) {
      return $Matches[1].Trim().Trim('"')
    }
  }
  return ''
}

function Get-LadderToken([string]$file, [string]$explicitKey) {
  # 令序：显式 -TokenKey > TRILC_INTERNAL_TOKEN（daemon 门族）> TRIMODEL_API_TOKEN（模型网关门族）
  if ($explicitKey) { return (Read-EnvKey $file $explicitKey) }
  $tok = Read-EnvKey $file 'TRILC_INTERNAL_TOKEN'
  if (-not $tok) { $tok = Read-EnvKey $file 'TRIMODEL_API_TOKEN' }
  return $tok
}

function New-AuthHeaders([string]$token, [string]$headerName) {
  # Authorization=Bearer 前缀形；X-Internal-Token=裸值形（TriRLC/TriMLC app.ts 门优先头）
  $h = @{}
  if ($token) {
    if ($headerName -eq 'Authorization') { $h['Authorization'] = ('Bearer ' + $token) }
    else { $h[$headerName] = $token }
  }
  return $h
}

function Invoke-HttpStatus([string]$method, [string]$url, [hashtable]$headers) {
  # 返回 @{ code=<int>; err=<string> }——5.1 无 -SkipHttpErrorCheck，用异常捕状态码
  try {
    $resp = Invoke-WebRequest -Uri $url -Method $method -Headers $headers -UseBasicParsing -TimeoutSec 6
    return @{ code = [int]$resp.StatusCode; err = '' }
  } catch {
    $sc = 0
    if ($_.Exception.Response) { $sc = [int]$_.Exception.Response.StatusCode }
    return @{ code = $sc; err = $_.Exception.Message }
  }
}

function Get-LadderState([int]$port, [int]$ownerPid, [string]$healthPath, [string]$probePath, [hashtable]$authHeaders) {
  # §一 双面制判定树
  $tcp = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -InformationLevel Detailed -WarningAction SilentlyContinue
  if (-not $tcp.TcpTestSucceeded) {
    $form = 'all-dead'
    if ($ownerPid -gt 0) {
      $procAlive = $null -ne (Get-Process -Id $ownerPid -ErrorAction SilentlyContinue)
      if ($procAlive) { $form = 'process-alive-port-dead' }
    }
    return @{ state = 'T-3'; detail = $form; healthz = 'unreachable'; probe = 'unreachable' }
  }

  $h = Invoke-HttpStatus 'GET' ("http://127.0.0.1:{0}{1}" -f $port, $healthPath) @{}
  $p = Invoke-HttpStatus 'GET' ("http://127.0.0.1:{0}{1}" -f $port, $probePath) $authHeaders

  if ($h.code -ge 200 -and $h.code -lt 300) {
    if ($p.code -ge 200 -and $p.code -lt 300) {
      return @{ state = 'T-OK'; detail = 'both-green'; healthz = $h.code; probe = $p.code }
    }
    if ($p.code -eq 401 -or $p.code -eq 403) {
      $d = if ($authHeaders.Count -gt 0) { 'auth-rejected' } else { 'probe-unauthenticated' }
      return @{ state = 'T-2'; detail = $d; healthz = $h.code; probe = $p.code }
    }
    if ($p.code -ge 500) {
      return @{ state = 'T-1'; detail = ('probe-5xx:' + $p.code); healthz = $h.code; probe = $p.code }
    }
    # 功能探其他 4xx=探针路径形不配（配置族），归 T-2 候判
    return @{ state = 'T-2'; detail = ('probe-4xx:' + $p.code); healthz = $h.code; probe = $p.code }
  }
  # healthz 拒/异常但端口通=进程半可用心（T-1 前置观察窗形态；端口在监听说明栈活着）
  return @{ state = 'T-1'; detail = ('healthz-abnormal:' + $h.code + ' ' + $h.err); healthz = $h.code; probe = $p.code }
}

function Out-Result([hashtable]$r) {
  # RESULT 结构化行（restore v2 修-6 同语义：完成即报可粘贴载体；零值面）
  $r['ts'] = & $script:ts
  $json = $r | ConvertTo-Json -Compress -Depth 4
  Write-Output ("RESULT " + $json)
}

# ═══ 子命令分派 ═══

switch ($Command) {

  'probe' {
    if ($Port -le 0) { Fail 'probe 需要 -Port' }
    $tok = ''
    if ($EnvFile) { $tok = Get-LadderToken $EnvFile $TokenKey }
    $auth = New-AuthHeaders $tok $TokenHeader
    $r = Get-LadderState $Port $Pid2 $HealthPath $ProbePath $auth
    $r['op'] = 'probe'; $r['port'] = $Port
    Save-State @{ op = 'probe'; port = $Port; state = $r.state; detail = $r.detail }
    if ($Json) { Write-Output ($r | ConvertTo-Json -Depth 4) }
    else {
      Write-Output ("probe port={0} -> {1} ({2})  healthz={3} probe={4}" -f $Port, $r.state, $r.detail, $r.healthz, $r.probe)
    }
    Out-Result $r
    exit 0
  }

  'a1' {
    if ($Port -le 0) { Fail 'a1 需要 -Port' }
    if (-not $Launcher) { Fail 'a1 需要 -Launcher（启动器 cmd/命令行）' }

    # 前置: probe 判定（T-OK/T-2 拒 A1——§一 T-2 走开关面，§二 A1 触发=T-3/T-1 确认）
    # 前置探针令源=-EnvFile（探针形）优先，回退 -ShutdownTokenEnvFile
    $tok = ''
    if ($EnvFile) { $tok = Get-LadderToken $EnvFile $TokenKey }
    elseif ($ShutdownTokenEnvFile) { $tok = Get-LadderToken $ShutdownTokenEnvFile $TokenKey }
    $auth = New-AuthHeaders $tok $TokenHeader
    $pre = Get-LadderState $Port 0 $HealthPath $ProbePath $auth
    if ($pre.state -eq 'T-OK') { Out-Result @{ op = 'a1'; result = 'rejected'; why = 'probe=T-OK 无触发条件'; state = 'T-OK' }; exit 1 }
    if ($pre.state -eq 'T-2') { Out-Result @{ op = 'a1'; result = 'rejected'; why = 'probe=T-2 写面未启用——走开关/命令通道面（§一 T-2 处置指向），非重启'; state = 'T-2' }; exit 1 }

    # 防环（意见书条款 2 细则 3）: watchdog ≤5min 复活窗口检查
    if (Test-Path $stateFile) {
      try {
        $st = Get-Content $stateFile -Raw | ConvertFrom-Json
        if ($st.op -eq 'watchdog-revive' -and $st.state -eq 'T-OK') {
          # 龄算走 tsEpoch（epoch 秒差）——ISO 串经 ConvertFrom-Json 自动转 datetime
          # 会丢 Kind，字符串 Parse 双重转换必漂（两坑实测在案，见 Save-State 注）
          if (-not $st.tsEpoch) { throw 'state 缺 tsEpoch（旧形），防环龄算不可靠' }
          $age = (([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - [long]$st.tsEpoch) / 60.0)
          if ($age -lt 5) {
            Out-Result @{ op = 'a1'; result = 'rejected'; why = ('watchdog 已于 {0:N1}min 前复活且 T-OK——防环（细则 3），人工阶梯不重复触发' -f $age); state = 'T-OK' }
            exit 1
          }
        }
      } catch { Write-Output "WARN state 文件解析失败（防环检查跳过）: $($_.Exception.Message)" }
    }

    $plan = @()
    if ($pre.state -eq 'T-1' -and $ShutdownPort -gt 0) {
      # T-1 半死形: 先优雅停再拉活；T-3 全亡形: 直接拉活
      $tok = $ShutdownToken
      if (-not $tok -and $ShutdownTokenEnvFile) { $tok = Get-LadderToken $ShutdownTokenEnvFile $TokenKey }
      if ($tok) {
        $plan += ("POST http://127.0.0.1:{0}/shutdown ({1} ***, len={2})" -f $ShutdownPort, $TokenHeader, $tok.Length)
      } else {
        $plan += ("POST http://127.0.0.1:{0}/shutdown (无令形——令面缺位如实注记)" -f $ShutdownPort)
      }
    }
    $plan += ("启动器拉活: {0}" -f $Launcher)

    if (-not $Execute) {
      Out-Result @{ op = 'a1'; result = 'dry-run'; pre_state = $pre.state; pre_detail = $pre.detail; plan = $plan; note = '真动作加 -Execute；重启后 5min 探活回归（§二 A1 时限纪律）' }
      exit 0
    }

    # 真动作（-Execute）
    if ($pre.state -eq 'T-1' -and $ShutdownPort -gt 0) {
      $tok = $ShutdownToken
      if (-not $tok -and $ShutdownTokenEnvFile) { $tok = Get-LadderToken $ShutdownTokenEnvFile $TokenKey }
      $hh = New-AuthHeaders $tok $TokenHeader
      try { Invoke-WebRequest -Uri ("http://127.0.0.1:{0}/shutdown" -f $ShutdownPort) -Method POST -Headers $hh -UseBasicParsing -TimeoutSec 8 | Out-Null
      } catch { Write-Output "shutdown 响应异常（继续拉活）: $($_.Exception.Message)" }
      Start-Sleep -Seconds 2
    }
    Start-Process cmd.exe -ArgumentList ('/c', $Launcher) -WindowStyle Hidden
    Write-Output 'P1 通报: A1 重启已触发（§三 P1——BOD/值班面知悉级；本行即通报载体，notify 链候接）'
    Start-Sleep -Seconds 3
    $post = Get-LadderState $Port 0 $HealthPath $ProbePath @{}
    $post['op'] = 'a1'; $post['result'] = 'executed'; $post['pre_state'] = $pre.state
    $post['note'] = '5min 内复探回归（§二 A1 时限纪律）；未回归转 A2（A1×2 无效触发条件）'
    Save-State @{ op = 'a1'; port = $Port; state = $post.state; detail = $post.detail }
    Out-Result $post
    exit 0
  }

  'a2' {
    if (-not $AppDir) { Fail 'a2 需要 -AppDir' }
    if (-not $RollbackAnchor) { Fail 'a2 前置: 回滚锚 declared 必填（-RollbackAnchor，§二 A2 纪律）' }
    if (-not $Judge) { Fail 'a2 前置: 值席判位必填（-Judge，§三 P2）' }

    $restoreScript = Join-Path $PSScriptRoot 'restore-claude-config.ps1'
    $plan = @(
      @{ 子件 = '配置面（restore 吸收，意见书条款1）'; 动作 = ('restore-claude-config.ps1 -Mode {0} -WhatIf→{1}' -f $RestoreMode, $(if ($Execute) { '真切' } else { '干跑' })) },
      @{ 子件 = '进程面（并列另列——修改①防覆盖误读）'; 动作 = ('cd {0}; npm run build（dist 重建）' -f $AppDir) }
    )
    if (-not $Execute) {
      Out-Result @{ op = 'a2'; result = 'dry-run'; judge = $Judge; rollback_anchor = $RollbackAnchor; plan = $plan; note = 'A2 触发条件=A1×2 无效（§二）；真动作 -Execute（配置面与进程面各一真跑）' }
      exit 0
    }
    # 真动作: 配置面子件（restore 带 WhatIf 先验——restore 自身有断言回滚，安全）
    & $restoreScript -Mode $RestoreMode -WhatIf
    $rc = $LASTEXITCODE
    Out-Result @{ op = 'a2'; result = 'executed-restore-whatif'; restore_exit = $rc; judge = $Judge; rollback_anchor = $RollbackAnchor; note = ('restore WhatIf 已执行（exit={0}——0=预览成；2=restore 凭据健康门拦（仓库模板占位符形按设计拒切，真窗 -InjectKey 后可用），读数见上行）；进程面 build/真切候值席窗逐件放行——本工具不一次连发两面真动作（P2 判间留隙）' -f $rc) }
    exit 0
  }

  'a3' {
    if (-not $Backup -or -not $Target) { Fail 'a3 需要 -Backup <bak路径> -Target <现役文件>' }
    if (-not $BodGate) { Fail 'a3 前置: BOD 裁门必填（-BodGate 裁决凭据串，§三 P3 三类口径）' }

    # 前置：bak 存在性断言（Rider① 2026-10-03 COO 发现项②——Test-Path 须在 JSON
    # 校验之前，否则缺失 bak 会先被 ConvertFrom-Json 捕获报「JSON 校验失败」误报文案）
    if (-not (Test-Path $Backup)) { Out-Result @{ op = 'a3'; result = 'rejected'; why = 'bak 文件不存在'; backup = $Backup }; exit 1 }

    # 回滚前 JSON 合法校验（意见书条款 1 合流定义；非 json 文件跳过校验照 bak 形）
    $isJson = $Target -match '\.json$' -or $Backup -match '\.json$'
    if ($isJson) {
      try { Get-Content $Backup -Raw | ConvertFrom-Json | Out-Null
      } catch { Out-Result @{ op = 'a3'; result = 'rejected'; why = ('bak JSON 校验失败（回滚前置门）: ' + $_.Exception.Message); backup = $Backup }; exit 1 }
    }

    if (-not $Execute) {
      Out-Result @{ op = 'a3'; result = 'dry-run'; bod_gate = $BodGate; backup = $Backup; target = $Target; plan = @('拷回 bak→target（写前现役再备份）'); note = 'git revert/端口宿主拓扑维度=restore 面之外独立执行（意见书合流定义）；真动作 -Execute' }
      exit 0
    }
    $pre = Join-Path $PSScriptRoot ('a3-pre-{0}.bak' -f (Get-Date -Format 'yyyyMMddTHHmmss'))
    Copy-Item $Target $pre -Force
    Copy-Item $Backup $Target -Force
    Save-State @{ op = 'a3'; backup = $Backup; target = $Target }
    Out-Result @{ op = 'a3'; result = 'executed'; backup = $Backup; target = $Target; pre_backup = $pre; note = 'P4 恢复后验证=值席+发起席双签（§三 P4 防自证）' }
    exit 0
  }

  default {
    Write-Output '用法: triladder.ps1 <probe|a1|a2|a3> [参数]——详见面头注释（LG-053 §一/§二/§三+CTO 意见书合流定义）'
    exit 1
  }
}
