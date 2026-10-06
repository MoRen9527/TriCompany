' run-sync-memory-mirror.vbs — 无窗包装（D-29：powershell 直启必闪 conhost 黑窗，VBS Run 第二参=0）
CreateObject("Wscript.Shell").Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""D:\Code\ai\TriCompany\scripts\ops\launch\sync-memory-mirror.ps1""", 0, False
