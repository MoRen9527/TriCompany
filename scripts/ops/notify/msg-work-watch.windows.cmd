rem 用途：msg-work-watch.cmd 真源化迁移件（原 .fade/msg-work-watch.cmd，原文照搬）
rem 目标机：本机（M 面本地）
rem 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
rem 真源位：TriCompany/scripts/ops/notify/msg-work-watch.windows.cmd

@echo off
"C:\Program Files\Git\bin\bash.exe" -lc "D:/Code/ai/TriMetaverse/docs/workflow/operating-records/2026-W38/ops-msg-work-watch.sh --once >> D:/Code/ai/TriMetaverse/.fade/msg-work-watch.log 2>&1"
