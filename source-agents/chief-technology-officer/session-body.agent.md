## TriRLC/构建/健康检查命令族（域知识族·LG-028 迁入）

> D 类域知识族首例（LG-028 第一步②；内容源=TriMetaverse CLAUDE.md Common Commands 节；CTO session 面工程域知识）。本件先落本节，session-body 完整化随 LG-024 批 1 管线窗。

### TriLC daemon（本地控制器）

```bash
trilc start              # Start daemon in background
trilc stop               # Stop daemon
trilc status             # Show daemon status (healthz + heartbeat + cron)
trilc daemon install     # Install as Windows scheduled task
trilc cron add/list/run  # Manage cron jobs
```

### 健康检查

```bash
curl http://127.0.0.1:8711/healthz
```

### Build pipeline（CI 触发）

Push `v*` tag 触发 `build-tricade.yml` → MSI + ZIP + GitHub Release。

### Install（统一脚本）

```powershell
.\scripts\install-tricade.ps1 -MsiPath <path> [-InstallService]
.\scripts\verify-trilc-24h.ps1 -DurationHours 1  # Quick stability test
```
