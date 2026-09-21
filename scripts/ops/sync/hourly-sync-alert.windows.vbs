' 用途：hourly-sync-alert.vbs 真源化迁移件（原 .fade/hourly-sync-alert.vbs，原文照搬）
' 目标机：本机（M 面本地）
' 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
' 真源位：TriCompany/scripts/ops/sync/hourly-sync-alert.windows.vbs

' hourly-sync-alert.vbs — 无窗包装（根治计划任务闪黑屏）
CreateObject("Wscript.Shell").Run "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""D:\Code\ai\TriMetaverse\.fade\hourly-sync-alert.ps1""", 0, False
