# 用途：admin-fix.ps1 真源化迁移件（原 .fade/admin-fix.ps1，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/admin/admin-fix.windows.ps1

$log = 'D:\Code\ai\TriMetaverse\.fade\admin-fix-log.txt'
"=== hosts fix $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Out-File $log -Encoding utf8
$h = 'C:\Windows\System32\drivers\etc\hosts'
(Get-Content $h) | Where-Object { $_ -notmatch '^140\.82\.(114\.3|112\.5|121\.4|121\.5)\s' } | Set-Content $h -Encoding ascii
ipconfig /flushdns | Out-String | Out-File $log -Append -Encoding utf8
"--- hosts github lines after fix ---" | Out-File $log -Append -Encoding utf8
Select-String -Path $h -Pattern 'github' | Out-String | Out-File $log -Append -Encoding utf8
"=== TriMLC elevated enumeration ===" | Out-File $log -Append -Encoding utf8
Get-ScheduledTask | Where-Object {$_.TaskName -like '*Tri*'} | Select-Object TaskName, State | Format-Table -AutoSize | Out-String -Width 120 | Out-File $log -Append -Encoding utf8
"--- schtasks LIST TriMLC ---" | Out-File $log -Append -Encoding utf8
schtasks /query /fo LIST 2>&1 | Select-String -Pattern 'TriMLC' | Out-String | Out-File $log -Append -Encoding utf8
"=== DONE ===" | Out-File $log -Append -Encoding utf8
