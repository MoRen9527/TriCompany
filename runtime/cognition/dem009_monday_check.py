"""dem009_monday_check — DEM-009 P1 周一晨检（查上周周迁移终态→异常 notify COS·信到人）。

DP-20261123-011 扩形（option② 双判据·CTO 批 2026-11-23）：
  判据 = job-state ok（lastRunStatus==ok 且 lastRunAtMs ≤8 天）**OR** 周产物存在
  （<records_root>/<当周 ISO 周>/.shift-ade.json：to_week==当周、status=='pass'、
   dry_run is False、check_time(UTC)→now(UTC) ≤9 天）。前者保留照役（防陈旧 ok 误
   短路）；后者覆盖点火形/手工补跑（job state 不回写场景·防每周一误报）。
  鲜度基准注（CTO 微调①）：check_time 为 UTC Z·now 同基准比较（防时区坑）。

cron 接法（TriRMC 8710 job dem009-monday-migration-check·周一 09:00 Asia/Shanghai）:
  cd /srv/fleet/TriCompany && python3 -m runtime.cognition.dem009_monday_check
退出码：0=正常静默（任一判据达标）｜9=异常已告警｜5=告警发送失败。
环境：TRIRMC_INTERNAL_TOKEN（daemon 内网门）；DEM009_DAEMON_URL 可覆；
      DEM009_RECORDS_ROOT 可覆（缺省 /srv/fleet/TriMetaverse/docs/workflow/operating-records）。
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DAEMON = os.environ.get("DEM009_DAEMON_URL", "http://127.0.0.1:8710")
RECORDS_ROOT = os.environ.get(
    "DEM009_RECORDS_ROOT", "/srv/fleet/TriMetaverse/docs/workflow/operating-records"
)
JOB = "weekly-plane-shift"
JOB_FRESH_DAYS = 8
ARTIFACT_FRESH_DAYS = 9


def _load_job():
    tok = os.environ.get("TRIRMC_INTERNAL_TOKEN", "")
    req = urllib.request.Request(DAEMON + "/internal/v1/cron/jobs", headers={"X-Internal-Token": tok})
    with urllib.request.urlopen(req, timeout=8) as r:
        d = json.load(r)
    jobs = d.get("jobs") or []
    hit = [j for j in jobs if j.get("name") == JOB]
    return hit[0] if hit else None


def iso_week(d: date) -> str:
    y, wk, _ = d.isocalendar()
    return f"{y}-W{wk:02d}"


def read_artifact(records_root: str, week: str, now: datetime) -> dict:
    """周产物面读（fail-closed：任何异常→ok=False）。"""
    p = Path(records_root) / week / ".shift-ade.json"
    rec = {"ok": False, "path": str(p), "reason": None, "data": None}
    try:
        if not p.is_file():
            rec["reason"] = "absent"
            return rec
        d = json.loads(p.read_text(encoding="utf-8"))
        rec["data"] = {k: d.get(k) for k in ("from_week", "to_week", "status", "dry_run", "check_time")}
        if d.get("dry_run") is not False:
            rec["reason"] = "dry_run"
            return rec
        if d.get("to_week") != week:
            rec["reason"] = "week_mismatch"
            return rec
        if d.get("status") != "pass":
            rec["reason"] = "status_not_pass"
            return rec
        ct = d.get("check_time")
        if not isinstance(ct, str):
            rec["reason"] = "check_time_missing"
            return rec
        ctd = datetime.fromisoformat(ct)
        if ctd.tzinfo is None:
            ctd = ctd.replace(tzinfo=timezone.utc)
        if now - ctd > timedelta(days=ARTIFACT_FRESH_DAYS):
            rec["reason"] = "stale"
            return rec
        rec["ok"] = True
        return rec
    except Exception as e:  # noqa: BLE001
        rec["reason"] = "read_error:" + str(e)[:120]
        return rec


def assess(now: datetime, job: dict | None, artifact: dict) -> bool:
    """双判据（OR）：job-state ok 鲜度 ≤8d 在前（照役保留）｜产物 pass 鲜度 ≤9d。"""
    st = (job or {}).get("state") or {}
    status = st.get("lastRunStatus")
    last = st.get("lastRunAtMs")
    if job and status == "ok" and isinstance(last, (int, float)):
        if now - datetime.fromtimestamp(last / 1000, tz=timezone.utc) <= timedelta(days=JOB_FRESH_DAYS):
            return True
    return bool(artifact.get("ok"))


def main() -> int:
    now = datetime.now(timezone.utc)
    week = iso_week(date.today())
    job = None
    err = None
    try:
        job = _load_job()
    except Exception as e:  # noqa: BLE001
        err = str(e)[:200]
    artifact = read_artifact(RECORDS_ROOT, week, now)
    ok = assess(now, job, artifact)
    st = (job or {}).get("state") or {}
    reading = {
        "check_time": now.isoformat(),
        "job": JOB,
        "job_found": job is not None,
        "lastRunStatus": st.get("lastRunStatus"),
        "lastRunAtMs": st.get("lastRunAtMs"),
        "consecutiveErrors": st.get("consecutiveErrors"),
        "job_err": err,
        "week": week,
        "artifact_ok": artifact["ok"],
        "artifact_reason": artifact["reason"],
        "artifact_data": artifact["data"],
        "verdict_ok": ok,
    }
    print("dem009-monday-check:", json.dumps(reading, ensure_ascii=False))
    if ok:
        return 0
    sys.path.insert(0, "/srv/fleet/TriCompany")
    from runtime.cognition.weekly_plane_shift import _notify_blocking, _resolve_notify_to

    fails = _notify_blocking(
        subject="[TriCade] DEM-009 周一晨检：上周周迁移终态异常 " + now.strftime("%Y-%m-%d"),
        body="DEM-009 P1 周一晨检（TriRMC 8710）— 判定=异常：job-state 与周产物双判据皆未达\n读数:\n"
        + json.dumps(reading, ensure_ascii=False, indent=2),
        to=_resolve_notify_to(),
        context_id="dem009-monday-check",
    )
    print("alert_failures=", fails)
    return 5 if fails else 9


if __name__ == "__main__":
    sys.exit(main())
