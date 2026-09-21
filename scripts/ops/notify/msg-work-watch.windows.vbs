' 用途：msg-work-watch.vbs 真源化迁移件（原 .fade/msg-work-watch.vbs，原文照搬）
' 目标机：本机（M 面本地）
' 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
' 真源位：TriCompany/scripts/ops/notify/msg-work-watch.windows.vbs

CreateObject("WScript.Shell").Run """D:\Code\ai\TriMetaverse\.fade\msg-work-watch.cmd""", 0, False
