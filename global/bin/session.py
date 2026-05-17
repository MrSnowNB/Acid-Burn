#!/usr/bin/env python3
"""
Acid Burn Session Manager

Manages session lifecycle: creation with cryptographic session IDs,
scratchpad persistence, and summary recording.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Standardize project root detection (Acid Burn Field Readiness)
ACID_BURN_ROOT = os.environ.get("ACID_BURN_ROOT") or str(Path(__file__).parent.parent.parent.absolute())
BASE_DIR = Path(ACID_BURN_ROOT)
if not (BASE_DIR / "global" / "tools").exists():
    BASE_DIR = Path.home() / ".acid-burn"


def _generate_session_id() -> str:
    """Generate a cryptographically sound 24-character hex session ID.
    96 bits of cryptographic randomness + timestamp.
    """
    entropy = os.urandom(12)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    raw = entropy + ts.encode("ascii")
    digest = hashlib.sha256(raw).hexdigest()
    return digest[:24]


def open_session(project_id: str) -> str:
    """Open a new session with a cryptographic session ID."""
    session_id = _generate_session_id()
    session_dir = BASE_DIR / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Write plan.json with project_id and empty steps
    (session_dir / "plan.json").write_text(
        json.dumps({"project_id": project_id, "steps": []}, indent=2)
    )

    (session_dir / "scratchpad.md").write_text("# Session Scratchpad\n")
    (session_dir / "artifacts").mkdir(exist_ok=True)

    return session_id


def close_session(session_id: str, summary: str) -> None:
    """Close a session and write summary."""
    session_dir = BASE_DIR / "sessions" / session_id
    if not session_dir.exists():
        return

    summary_file = session_dir / "summary.json"
    data = {
        "closed_at": datetime.now(timezone.utc).isoformat() + "Z",
        "summary": summary
    }
    summary_file.write_text(json.dumps(data, indent=2))
