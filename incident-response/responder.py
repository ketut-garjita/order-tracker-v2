import json
import os
from datetime import datetime, timezone
from pathlib import Path

from evidence import collect_evidence
from agent import run_agent


from pathlib import Path
INCIDENTS_DIR = Path(os.getenv("INCIDENTS_DIR", Path(__file__).resolve().parent.parent / "incident-response/incidents"))
INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)


def handle_alert(payload: dict) -> dict:
    timestamp = datetime.now(timezone.utc)
    incident_id = timestamp.strftime("%Y%m%dT%H%M%SZ")

    incident_dir = INCIDENTS_DIR / incident_id
    incident_dir.mkdir(parents=True, exist_ok=True)

    alert_file = incident_dir / "alert.json"

    alert_file.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    evidence = collect_evidence(
        payload=payload,
        incident_dir=incident_dir,
    )

    agent_result = run_agent(
        incident_dir=incident_dir,
        evidence=evidence,
    )

    return {
        "incident_id": incident_id,
        "agent_started": agent_result["started"],
        "agent_exit_code": agent_result["exit_code"],
    }
