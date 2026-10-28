"""Renders a recorded E2E trace as a scrollable transcript clip (1080p).

This does NOT re-run anything: it reads a trace produced by ``run_e2e_demo.py`` and
renders exactly what that run reported, with its provenance header (timestamp,
fixture, engine rows, audit hash). Useful as B-roll that can replace conceptual
scenes in the demo video.

Output: ``docs/evidence/zetaris/gridmind_e2e_transcript_<stamp>.webm`` (+ a PNG still).

Usage
-----
    python integrations/zetaris/evidence/render_transcript_clip.py \
        --trace integrations/zetaris/evidence/07_e2e_trace_INC8812.json
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[3]


def build_lines(trace: dict) -> list[tuple[str, str]]:
    prov = trace.get("provenance", {})
    lines: list[tuple[str, str]] = [
        ("title", "HG GridMind x Zetaris - end-to-end trace (captura de ejecucion)"),
        ("meta", f"run started {trace.get('started_utc')}  |  finished {trace.get('finished_utc')}"),
        ("meta", f"fixture {trace.get('fixture')}  |  incident {trace.get('incident_id')}  |  asset {trace.get('asset_id')}"),
        ("sep", "-" * 96),
        ("head", "[1] FUENTES FEDERADAS (zero-ETL, sin mover datos)"),
        ("body", "gridmind_scada_pg.scada_telemetry   -> PostgreSQL JDBC datasource (SCADA)"),
        ("body", "gridmind_files.maintenance_history  -> CSV Lightning filestore table (DGA)"),
        ("body", "gridmind_files.tickets_database     -> CSV Lightning filestore table (tickets)"),
        ("ok", f"filas devueltas por el motor real: {prov.get('real_engine_rows')} | fallback simulacion: {prov.get('is_simulation_fallback')}"),
        ("sep", "-" * 96),
        ("head", "[2] SQL EJECUTADO POR EL MOTOR"),
    ]
    detail = trace.get("real_engine_detail", {})
    sql = (detail.get("sql") or "").strip().splitlines()
    for ln in sql:
        lines.append(("sql", "  " + ln))
    lines.append(("ok", f"engine={detail.get('engine')} | rows={detail.get('row_count')} | {detail.get('elapsed_ms')} ms"))
    lines.append(("sep", "-" * 96))
    lines.append(("head", "[3] RESULTADO: filas citables (row_id por fuente)"))
    cols = detail.get("columns", [])
    for row in (detail.get("rows") or [])[:10]:
        rec = dict(zip(cols, row)) if isinstance(row, list) else row
        lines.append(("body", "  " + " | ".join(
            f"{k}={rec.get(k)}" for k in ("scada_row_id", "ts", "neutral_current_amps", "maint_row_id", "dga_verdict", "ticket_row_id")
            if k in rec)))
    lines.append(("sep", "-" * 96))
    lines.append(("head", "[4] HIPOTESIS FALSADAS (descarte activo)"))
    for f in trace.get("hypotheses", {}).get("falsified", []):
        lines.append(("bad", f"  [X] {f.get('hypothesis')}"))
        lines.append(("body", f"      ref: {f.get('falsified_by_citation')}"))
    lines.append(("head", "[5] EVIDENCIA QUE SOSTIENE LA CAUSA"))
    for c in trace.get("hypotheses", {}).get("supported_citations", []):
        lines.append(("good", f"  [+] {c.get('source_table')}:{c.get('row_id')}"))
    lines.append(("sep", "-" * 96))
    lines.append(("head", "[6] CAUSA RAIZ CONFIRMADA"))
    lines.append(("body", "  " + str(trace.get("root_cause"))))
    lines.append(("head", "[7] ACCION RECOMENDADA + HUMAN APPROVAL GATE"))
    lines.append(("body", "  " + str(trace.get("recommended_action"))[:220]))
    gate = trace.get("gate", {})
    lines.append(("body", f"  approval_required={gate.get('approval_required')} authorized={gate.get('authorized')}"))
    lines.append(("ok", f"  audit ACK {trace.get('audit_ack')}"))
    lines.append(("meta", "  Trazabilidad: integrations/zetaris/evidence/*.json (SQL, filas, motor, timestamps)"))
    return lines


CSS = """
body{margin:0;background:#0b1016;color:#c9d6e4;font:16px/1.55 'Cascadia Mono','Consolas',monospace}
.wrap{max-width:1500px;margin:0 auto;padding:48px 56px}
.hdr{display:flex;gap:14px;align-items:center;margin-bottom:26px;color:#7f96ad;font-size:15px}
.badge{background:#132033;border:1px solid #23374f;border-radius:6px;padding:5px 10px;color:#8fb3d9}
.title{color:#e8f1fa;font-weight:700;font-size:24px;margin:0 0 10px}
.meta{color:#7f96ad}
.head{color:#5ea8ff;font-weight:700;margin-top:12px}
.body{color:#c9d6e4}
.sql{color:#8fbf8f;white-space:pre}
.ok,.good{color:#63d68a}
.bad{color:#f08a8a}
.sep{color:#23374f}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", default=str(REPO_ROOT / "integrations" / "zetaris" / "evidence" / "07_e2e_trace_INC8812.json"))
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "docs" / "evidence" / "zetaris"))
    ap.add_argument("--seconds", type=float, default=26.0)
    args = ap.parse_args()

    trace = json.loads(Path(args.trace).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tmp = Path(tempfile.mkdtemp(prefix="gridmind-clip-"))

    body = "\n".join(f'<div class="{cls}">{html.escape(text)}</div>' for cls, text in build_lines(trace))
    page_html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="wrap">
  <div class="hdr"><span class="badge">REAL ZETARIS ENGINE</span><span class="badge">LOCAL DOCKER</span>
    <span class="badge">COST USD 0</span><span>{trace.get('started_utc')}</span></div>
  <div class="title">HG GridMind — investigacion con evidencia federada real</div>
  <div class="meta">Transcripcion de la ejecucion registrada en {Path(args.trace).name} (no es un diagrama: son los valores devueltos por el motor).</div>
  <div style="height:18px"></div>
  {body}
</div></body></html>"""
    page_path = tmp / "transcript.html"
    page_path.write_text(page_html, encoding="utf-8")

    video_dir = tmp / "video"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(video_dir),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = ctx.new_page()
        page.goto(page_path.as_uri(), wait_until="load")
        page.wait_for_timeout(2500)
        still = out_dir / f"gridmind_e2e_transcript_{stamp}.png"
        page.screenshot(path=str(still))
        steps = max(6, int(args.seconds / 2))
        for _ in range(steps):
            page.mouse.wheel(0, 190)
            page.wait_for_timeout(int(args.seconds * 1000 / steps))
        ctx.close()
        browser.close()

    videos = sorted(video_dir.glob("*.webm"))
    target = out_dir / f"gridmind_e2e_transcript_{stamp}.webm"
    if videos:
        shutil.copy(videos[0], target)
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"video": target.name if videos else None, "still": still.name,
                      "source_trace": Path(args.trace).name}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
