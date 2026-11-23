"""dem009_monday_check — DEM-009 P1 周一晨检（查上周周迁移终态→异常 notify COS·信到人）。

cron 接法（TriRMC 8710 job dem009-monday-migration-check·周一 09:00 Asia/Shanghai）:
  cd /srv/fleet/TriCompany && python3 -m runtime.cognition.dem009_monday_check
退出码：0=正常（静默）｜9=异常已告警｜5=告警发送失败（stderr 留痕）。
环境：TRIRMC_INTERNAL_TOKEN（daemon 内网门）；daemon URL 缺省 127.0.0.1:8710（DEM009_DAEMON_URL 可覆）。
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

DAEMON = os.environ.get("DEM009_DAEMON_URL", "http://127.0.0.1:8710")
JOB = "weekly-plane-shift"


def _load_job():
    tok = os.environ.get("TRIRMC_INTERNAL_TOKEN", "")
    req = urllib.request.Request(DAEMON + "/internal/v1/cron/jobs", headers={"X-Internal-Token": tok})
    with urllib.request.urlopen(req, timeout=8) as r:
        d = json.load(r)
    jobs = d.get("jobs") or []
    hit = [j for j in jobs if j.get("name") == JOB]
    return hit[0] if hit else None


def main() -> int:
    now = datetime.now(timezone.utc)
    job = None
    err = None
    try:
        job = _load_job()
    except Exception as e:  # noqa: BLE001
        err = str(e)[:200]
    st = (job or {}).get("state") or {}
    status = st.get("lastRunStatus")
    last = st.get("lastRunAtMs")
    consec = st.get("consecutiveErrors")
    ok = False
    if job and status == "ok" and isinstance(last, (int, float)):
        if now - datetime.fromtimestamp(last / 1000, tz=timezone.utc) <= timedelta(days=8):
            ok = True
    reading = {
        "check_time": now.isoformat(),
        "job": JOB,
        "job_found": job is not None,
        "lastRunStatus": status,
        "lastRunAtMs": last,
        "consecutiveErrors": consec,
        "err": err,
    }
    print("dem009-monday-check:", json.dumps(reading, ensure_ascii=False))
    if ok:
        return 0
    sys.path.insert(0, "/srv/fleet/TriCompany")
    from runtime.cognition.weekly_plane_shift import _notify_blocking, _resolve_notify_to

    fails = _notify_blocking(
        subject="[TriCade] DEM-009 周一晨检：上周周迁移终态异常 " + now.strftime("%Y-%m-%d"),
        body="DEM-009 P1 周一晨检（TriRMC 8710）— 判定=异常：上周周迁移终态非 ok 或缺失\n读数:\n"
        + json.dumps(reading, ensure_ascii=False, indent=2),
        to=_resolve_notify_to(),
        context_id="dem009-monday-check",
    )
    print("alert_failures=", fails)
    return 5 if fails else 9


if __name__ == "__main__":
    sys.exit(main())
