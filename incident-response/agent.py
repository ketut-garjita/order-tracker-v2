import os
import shlex
import shutil
import subprocess
from pathlib import Path

REPO_DIR = Path(os.getenv("REPO_DIR", Path(__file__).resolve().parent.parent))
BASE_COMMAND = os.getenv("CODING_AGENT_COMMAND", "codex exec --skip-git-repo-check")


def _strip_managed_options(args):
    """Buang -C/--cd, --output-last-message (beserta nilainya) dan '-' di akhir,
    karena opsi itu ditambahkan oleh kode ini."""
    cleaned, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a in ("-C", "--cd", "--output-last-message"):
            skip = True
            continue
        cleaned.append(a)
    if cleaned and cleaned[-1] == "-":
        cleaned.pop()
    return cleaned


def build_prompt(incident_dir: Path, evidence: dict) -> str:
    return f"""
You are an incident-response coding agent.

Repository: {REPO_DIR}
Incident evidence directory: {incident_dir}
(alert.json, incident.md, logs.txt and traces.txt are in that directory)

Alert / evidence summary:
{evidence}

Tasks:
1. Inspect the repository and the evidence files.
2. Identify the root cause of the reported incident.
3. Make the smallest safe code change necessary. Do not make unrelated changes.
4. Do NOT run tests; the system runs them automatically after you finish.
5. Report the root cause, what you changed, and why.

If this is only a responder test (label test=true) and there is no real
incident, do not modify any code and do not run anything. State that no fix
is required.
"""


def verify_tests(incident_dir: Path) -> None:
    """Jalankan tes di host setelah agent selesai dan simpan hasilnya sebagai bukti."""
    python = REPO_DIR / ".venv" / "bin" / "python"
    exe = str(python) if python.exists() else "python3"
    out = incident_dir / "verification.txt"
    try:
        verify = subprocess.run(
            [exe, "-m", "pytest", "-q"],
            cwd=REPO_DIR, capture_output=True, text=True, timeout=120,
        )
        out.write_text(
            f"exit={verify.returncode}\n{verify.stdout}\n{verify.stderr}",
            encoding="utf-8",
        )
    except Exception as exc:
        out.write_text(f"Verification failed to run: {exc!r}\n", encoding="utf-8")


def run_agent(incident_dir: Path, evidence: dict) -> dict:
    out = incident_dir / "agent-response.txt"
    base = _strip_managed_options(shlex.split(BASE_COMMAND))

    if not base or shutil.which(base[0]) is None:
        out.write_text(f"Agent command not found: {base[:1]}\n", encoding="utf-8")
        return {"started": False, "exit_code": None}

    command = base + [
        "-C", str(REPO_DIR),
        "--output-last-message", str(incident_dir / "last-message.txt"),
        "-",  # baca prompt dari stdin
    ]
    prompt = build_prompt(incident_dir, evidence)

    try:
        result = subprocess.run(
            command, cwd=REPO_DIR, input=prompt, text=True,
            capture_output=True, timeout=900,
        )
    except Exception as exc:
        out.write_text(f"Agent failed to run: {exc!r}\n", encoding="utf-8")
        return {"started": False, "exit_code": None}

    out.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    verify_tests(incident_dir)
    return {"started": True, "exit_code": result.returncode}
