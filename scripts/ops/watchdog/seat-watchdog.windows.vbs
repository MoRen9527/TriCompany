' 用途：seat-watchdog.vbs 真源化迁移件（原 .fade/seat-watchdog.vbs，原文照搬）
' 目标机：本机（M 面本地）
' 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
' 真源位：TriCompany/scripts/ops/watchdog/seat-watchdog.windows.vbs

CreateObject("WScript.Shell").Run "powershell -ExecutionPolicy Bypass -File ""D:\Code\ai\TriMetaverse\.fade\seat-watchdog.ps1""", 0, False
