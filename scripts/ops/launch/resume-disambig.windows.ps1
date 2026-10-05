# resume-disambig — resume-by-title 全库去歧义公共函数（2026-10-05 CEO 令：席位切 worktree 后重调保障）
# 真源位：TriCompany/scripts/ops/launch/resume-disambig.windows.ps1；部署位=.fade/resume-disambig.ps1（sync.ps1）
# 背景（2026-10-05 COS/FSD 弹窗根治实证，W40 发送账 #406/#407）：claude --resume <title> 匹配面=
#   projects/ 全部项目目录（CLI 2.1.289 实测），同名多命中=弹会话选择器卡席；唯一命中=直进。
# 语义：启动前归档非当前工作域的同名会话，保证全库唯一命中——「默认选最新会话」（CEO 原话）。
#   ①候选=projects/ 全域 jsonl 中 customTitle 恰为 -Name 的文件（-archived- 后缀件天然不匹配=复跑幂等）；
#   ②当前域判定=文件首段（兜底尾段）cwd（JSON 转义 \\ 还原后归一）以 -WorkingDir 归一为前缀且路径
#     边界完整（"TriMetaverse" 不得误吞 "TriMetaverse-worktrees"）；cwd 缺失视为非当前域；
#   ③当前域有保留件→候选全归档；当前域零保留件→仅保留 mtime 最新一份、其余归档（首启 worktree
#     保底：resume 永不零命中报错，直进最近会话）；候选 ≤1 份零动作（单份无歧义）；
#   ④归档=文件内 customTitle 值改 -Name-archived-<MMdd>（不删文件、可逆、动作留痕日志）；
#   ⑤fail-open：本函数任何异常静默跳过——去歧义自身故障绝不挡席位启动。
# 性能（首版逐行 PS 循环 40s+ / 二版 LINQ-Any 13s 迭代教训）：needle 判定=1MB 块读+重叠扫描
#   （C# 内核，免行级对象分配）；cwd=首/尾 64KB 段读，免全文件扫描。全库一次 ~数秒。
# 日志：.fade/resume-disambig.log

function Test-FileContains {
  # 块读+重叠 needle 扫描（1MB 块、重叠=needle 字节长+8——跨块 needle 不丢；UTF8 残缺序列
  # 输出 U+FFFD 不抛且 ASCII needle 不受影响）。FileShare ReadWrite=活跃会话件安全共读。
  param([Parameter(Mandatory=$true)][string]$Path, [Parameter(Mandatory=$true)][string]$Needle)
  try {
    $fs = [System.IO.File]::Open($Path, 'Open', 'Read', [System.IO.FileShare]::ReadWrite)
    try {
      $len = $fs.Length
      if ($len -eq 0) { return $false }
      $nBytes = [System.Text.Encoding]::UTF8.GetByteCount($Needle)
      $chunk = 1048576
      $overlap = $nBytes + 8
      $buf = [byte[]]::new($chunk + $overlap)
      $pos = 0
      while ($pos -lt $len) {
        $want = [int][Math]::Min($chunk + $overlap, $len - $pos)
        [void]$fs.Seek($pos, 'Begin')
        $got = 0
        while ($got -lt $want) {
          $r = $fs.Read($buf, $got, $want - $got)
          if ($r -le 0) { break }
          $got += $r
        }
        if ($got -lt $nBytes) { return $false }
        $txt = [System.Text.Encoding]::UTF8.GetString($buf, 0, $got)
        if ($txt.Contains($Needle)) { return $true }
        if ($len - $pos -le $chunk) { return $false }
        $pos += $chunk
      }
      return $false
    } finally { $fs.Close() }
  } catch { return $false }
}

function Get-SessionCwd {
  param([Parameter(Mandatory=$true)][string]$Path)
  try {
    $fs = [System.IO.File]::Open($Path, 'Open', 'Read', [System.IO.FileShare]::ReadWrite)
    try {
      $len = $fs.Length
      foreach ($seg in @('head', 'tail')) {
        $bufLen = [int][Math]::Min(262144, $len)
        if ($bufLen -le 0) { return $null }
        $buf = [byte[]]::new($bufLen)
        if ($seg -eq 'head') { [void]$fs.Seek(0, 'Begin') } else { [void]$fs.Seek($len - $bufLen, 'Begin') }
        [void]$fs.Read($buf, 0, $bufLen)
        $txt = [System.Text.Encoding]::UTF8.GetString($buf)
        $ms = [regex]::Matches($txt, '"cwd":"([^"]*)"')
        if ($ms.Count -gt 0) {
          if ($seg -eq 'head') { return $ms[0].Groups[1].Value }
          return $ms[$ms.Count - 1].Groups[1].Value
        }
      }
    } finally { $fs.Close() }
  } catch { }
  return $null
}

function Invoke-ResumeDisambig {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$WorkingDir
  )
  try {
    $projRoot = Join-Path $env:USERPROFILE '.claude\projects'
    if (-not (Test-Path $projRoot)) { return }
    $logFile = 'D:\Code\ai\TriMetaverse\.fade\resume-disambig.log'
    $stamp = Get-Date -Format 'MMdd'
    $wdNorm = ($WorkingDir -replace '/', '\').TrimEnd('\').ToLower()
    $needle = '"customTitle":"' + $Name + '"'
    $targets = [System.Collections.Generic.List[object]]::new()
    Get-ChildItem $projRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
      Get-ChildItem $_.FullName -Filter '*.jsonl' -File -ErrorAction SilentlyContinue
    } | ForEach-Object {
      $f = $_
      if (-not (Test-FileContains -Path $f.FullName -Needle $needle)) { return }
      $cwd = Get-SessionCwd -Path $f.FullName
      $inDomain = $false
      if ($cwd) {
        $cwdNorm = ($cwd.Replace('\\', '\') -replace '/', '\').TrimEnd('\').ToLower()
        if ($cwdNorm -eq $wdNorm -or $cwdNorm.StartsWith($wdNorm + '\')) { $inDomain = $true }
      }
      $targets.Add([pscustomobject]@{ Path = $f.FullName; InDomain = $inDomain; MTime = $f.LastWriteTime })
    }
    if ($targets.Count -le 1) { return }
    $keepPaths = @($targets | Where-Object { $_.InDomain } | ForEach-Object { $_.Path })
    if ($keepPaths.Count -eq 0) {
      $keepPaths = @(($targets | Sort-Object MTime -Descending | Select-Object -First 1).Path)
    }
    $archive = @($targets | Where-Object { $keepPaths -notcontains $_.Path })
    $oldTitle = '"customTitle":"' + $Name + '"'
    $newTitle = '"customTitle":"' + $Name + '-archived-' + $stamp + '"'
    foreach ($t in $archive) {
      $text = [System.IO.File]::ReadAllText($t.Path)
      $cnt = ([regex]::Matches($text, [regex]::Escape($oldTitle))).Count
      if ($cnt -eq 0) { continue }
      [System.IO.File]::WriteAllText($t.Path, $text.Replace($oldTitle, $newTitle), [System.Text.UTF8Encoding]::new($false))
      "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | archived $Name x$cnt | $(Split-Path (Split-Path $t.Path -Parent) -Leaf) | inDomain=$($t.InDomain) mtime=$($t.MTime.ToString('MM-dd HH:mm'))" | Add-Content -Path $logFile -Encoding UTF8
    }
  } catch { }   # fail-open：去歧义自身故障绝不挡启动
}
