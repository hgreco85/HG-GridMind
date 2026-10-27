"""Live chain demo: real Zetaris federation -> real Meterless H-MEM -> recall with provenance + ledger.

Run (after integrations/zetaris and integrations/meterless/setup.sh are set up):
    GRIDMIND_ZETARIS_REAL=1 GRIDMIND_METERLESS_REAL=1 python integrations/meterless/demo_live_chain.py [out.json]
"""
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_connector import FederatedDataConnector  # noqa: E402
from src.sponsors.meterless_real import MeterlessHMemEngine  # noqa: E402

out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
state = tempfile.mkdtemp(prefix="gridmind_hmem_")  # fresh memory so the evidence is reproducible
conn = FederatedDataConnector(
    ROOT / "fixtures" / "incident_INC_2026_UTIL_5501.json",
    use_real_engine=True, use_real_meterless=True,
    meterless_engine=MeterlessHMemEngine(state_dir=state),
)
res = conn.execute_federated_query()
z, m = res["zetaris_real"], res["meterless_real"]
summary = {
    "ts_local": datetime.now().astimezone().isoformat(),
    "zetaris": {k: z.get(k) for k in ("used", "execution_mode", "row_count", "elapsed_ms", "reason")},
    "meterless": {k: m.get(k) for k in ("used", "execution_mode", "engine", "memories_total", "added", "reason")},
    "answers": m.get("answers", []),
    "ledger": m.get("ledger", {}),
}
txt = json.dumps(summary, indent=1)
if out_path:
    out_path.write_text(txt, encoding="utf-8")
print(txt)
sys.exit(0 if z.get("used") and m.get("used") else 1)
