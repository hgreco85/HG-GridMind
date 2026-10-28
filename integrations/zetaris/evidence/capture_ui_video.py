"""Records the authentic Zetaris UI executing the GridMind federated SQL.

Produces (in ``docs/evidence/zetaris/`` by default):
* ``zetaris_ui_live_<stamp>.webm``  1080p screen recording of the real UI
* ``ui_live_<stamp>_*.png``          keyframes (login/tree/sql/results)
* ``ui_live_<stamp>.json``           sidecar: timestamp, SQL, UI result text, engine info

The admin password is read from the platform ``.env`` and typed into a masked
``input[type=password]``; it is never written to disk, printed, or committed.
Session cookies are kept in the OS temp dir, outside the repository.

Usage
-----
    python integrations/zetaris/evidence/capture_ui_video.py --ui-url http://localhost:3000
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[3]
PLATFORM_ENV = Path(r"C:\Users\Administrator\hg-sandbox\zetaris\zetaris-platform\.env")
FEDERATED_SQL = (REPO_ROOT / "integrations" / "zetaris" / "sql" / "04_federated.sql")

QUERY_1 = """
SELECT s.row_id AS scada_row_id, s.ts, s.current_phase_b_amps, s.neutral_current_amps,
       m.row_id AS maint_row_id, m.verdict AS dga_verdict, m.acetylene_ppm,
       t.row_id AS ticket_row_id, t.ticket_type, t.reported_at
FROM gridmind_scada_pg.scada_telemetry s
JOIN gridmind_files.maintenance_history m ON m.asset_id = s.asset_id AND m.verdict <> 'NORMAL'
JOIN gridmind_files.tickets_database t ON t.affected_feeder = s.feeder_id
WHERE s.asset_id = 'TR-102' AND s.neutral_current_amps > 15
ORDER BY s.ts DESC, t.row_id
""".strip()


def read_password() -> str:
    for line in PLATFORM_ENV.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("ZETARIS_ADMIN_PASSWORD="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ZETARIS_ADMIN_PASSWORD not found in the platform .env")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ui-url", default="http://localhost:3000")
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "docs" / "evidence" / "zetaris"))
    ap.add_argument("--user", default="admin@zetaris.com")
    ap.add_argument("--wait-ms", type=int, default=25000)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tmp = Path(tempfile.mkdtemp(prefix="zetaris-ui-"))
    sidecar = {
        "captured_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ui_url": args.ui_url,
        "sql": QUERY_1,
        "screenshots": [],
    }

    def shot(page, name):
        path = out_dir / f"ui_live_{stamp}_{name}.png"
        page.screenshot(path=str(path))
        sidecar["screenshots"].append(path.name)
        return path

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        login_ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = login_ctx.new_page()
        page.goto(f"{args.ui_url}/login", wait_until="networkidle")
        page.fill("input[type=text]", args.user)
        page.fill("input[type=password]", read_password())  # masked field, never logged
        shot(page, "01_login")
        page.click("text=Sign In")
        page.wait_for_timeout(6000)
        state = tmp / "state.json"
        login_ctx.storage_state(path=str(state))
        login_ctx.close()

        video_dir = tmp / "video"
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            storage_state=str(state),
            record_video_dir=str(video_dir),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = ctx.new_page()
        page.goto(args.ui_url, wait_until="networkidle")
        page.wait_for_timeout(2500)
        shot(page, "02_home")
        try:
            page.click("text=Database", timeout=15000)
            page.wait_for_timeout(2000)
            shot(page, "03_catalog_tree")
        except Exception as exc:  # noqa: BLE001
            sidecar.setdefault("warnings", []).append(f"tree: {exc}"[:200])
        page.click("text=Workbench", timeout=15000)
        page.wait_for_timeout(1000)
        page.click("text=SQL Workspace", timeout=15000)
        page.wait_for_timeout(3000)
        page.click("text=New Query", timeout=15000)
        page.wait_for_timeout(3500)
        page.click(".monaco-editor")
        page.keyboard.press("Control+A")
        page.keyboard.press("Delete")
        for line in QUERY_1.splitlines():
            page.keyboard.insert_text(line)
            page.keyboard.press("Enter")
        page.wait_for_timeout(1500)
        shot(page, "04_sql_typed")
        page.keyboard.press("Control+Enter")
        page.wait_for_timeout(args.wait_ms)
        shot(page, "05_results")
        body = page.inner_text("body")
        for _ in range(3):
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(700)
        shot(page, "06_results_scrolled")
        ctx.close()
        browser.close()

    videos = sorted(video_dir.glob("*.webm"))
    if videos:
        target = out_dir / f"zetaris_ui_live_{stamp}.webm"
        shutil.copy(videos[0], target)
        sidecar["video"] = target.name
    sidecar["ui_result_text"] = body[:6000]
    sidecar["ui_result_lines"] = len([ln for ln in body.splitlines() if ln.strip()])
    (out_dir / f"ui_live_{stamp}.json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"video": sidecar.get("video"), "screenshots": sidecar["screenshots"],
                      "sidecar": f"ui_live_{stamp}.json"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
