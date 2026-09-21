' 用途：seat-boot.vbs 真源化迁移件（原 .fade/seat-boot.vbs，原文照搬）
' 目标机：本机（M 面本地）
' 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
' 真源位：TriCompany/scripts/ops/launch/seat-boot.windows.vbs

CreateObject("WScript.Shell").Run "powershell -ExecutionPolicy Bypass -File ""D:\Code\ai\TriMetaverse\docs\workflow\operating-records\2026-W38\ops-seat-watchdog.ps1"" -Bootstrap", 0, False
