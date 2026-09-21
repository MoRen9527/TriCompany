$t = Get-Content 'D:\Code\ai\TriMetaverse\.fade\seat-watchdog.ps1' -Raw -Encoding UTF8
$m = '# generated from TriCompany/scripts/ops — 禁直写（sync.ps1 单向维护）'
Write-Host ('like: ' + ($t -like ('*' + $m + '*')))
Write-Host ('contains: ' + $t.Contains($m))
Write-Host ('first3: ' + (($t.Substring(0, 3).ToCharArray() | ForEach-Object { [int]$_ }) -join ','))
