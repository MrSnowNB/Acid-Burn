#!/usr/bin/env python3
"""
Atom Runner — Acid Burn

Handles the actual execution of a loaded Atom:
- Builds the command using the Atom's toolchain
- Executes it with proper timeout, sudo handling, and artifact capture
- Parses the output using the Atom's parser
- Records a trial to the ledger

This is the bridge between the clean Atom definition and real execution on Kali.
"""

import subprocess
import time
import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from atom_loader import AtomDefinition


def run_atom(
    atom: AtomDefinition,
    inputs: dict[str, Any],
    project_id: str = "lab-internal",
    session_id: str = None,
    timeout: int = None,
    dry_run: bool = False,
    base_dir: Path = None,
) -> dict[str, Any]:
    """
    Execute a true Atom using its declared Python toolchain.
    """
    if session_id is None:
        session_id = f"atom-{int(time.time())}"

    # Default base_dir to ~/.acid-burn if not provided
    if base_dir is None:
        base_dir = Path.home() / ".acid-burn"

    start_time = time.time()

    # 1. Build the command
    try:
        cmd = atom.toolchain.command_builder(inputs)
    except Exception as e:
        return {
            "status": "failed",
            "error": f"command_builder_failed: {e}",
            "atom_id": atom.id,
        }

    if dry_run:
        return {
            "status": "dry_run",
            "command": cmd,
            "atom_id": atom.id,
            "inputs": inputs,
        }

    # 2. Determine timeout
    duration = inputs.get("duration", 60)
    try:
        duration_int = int(duration)
    except (ValueError, TypeError):
        duration_int = 60
        
    effective_timeout = timeout or duration_int + 30

    # 3. Execute
    try:
        # Prepend sudo if required
        exec_cmd = cmd
        if atom.requires_sudo:
            exec_cmd = ["sudo"] + cmd

        proc = subprocess.run(
            exec_cmd,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
            cwd="/tmp",
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # 3.1 Write Artifacts
        ts = str(int(time.time()))
        artifact_id = f"{atom.id}-{ts}"
        artifact_rel_path = f"sessions/{session_id}/artifacts/{artifact_id}.raw"
        artifact_full_path = base_dir / artifact_rel_path
        artifact_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        raw_output = f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n\nEXIT_CODE: {proc.returncode}"
        artifact_full_path.write_text(raw_output)

    except subprocess.TimeoutExpired as e:
        duration_ms = int((time.time() - start_time) * 1000)
        # Write timeout artifact
        ts = str(int(time.time()))
        artifact_rel_path = f"sessions/{session_id}/artifacts/{atom.id}-{ts}.timeout"
        artifact_full_path = base_dir / artifact_rel_path
        artifact_full_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_full_path.write_text(f"TIMEOUT EXCEEDED ({effective_timeout}s)\nSTDOUT SO FAR:\n{e.stdout}\nSTDERR SO FAR:\n{e.stderr}")
        
        return {
            "status": "timeout",
            "atom_id": atom.id,
            "duration_ms": duration_ms,
            "command": cmd,
            "artifact_path": artifact_rel_path,
        }
    except Exception as e:
        return {
            "status": "execution_failed",
            "error": str(e),
            "atom_id": atom.id,
        }

    # 4. Parse output using the Atom's parser
    try:
        # Give tools a moment to flush files to disk after termination
        time.sleep(1)
        
        # Most parsers will expect either raw strings or a path to CSV
        # Passing inputs as kwargs allows parser to find files if needed
        import sys
        sys.stderr.write(f"[DEBUG] run_atom: calling parser for {atom.id} with keys {list(inputs.keys())}\n")
        parsed = atom.toolchain.output_parser(proc.stdout, stderr=proc.stderr, returncode=proc.returncode, **inputs)
    except Exception as e:
        parsed = {"error": f"parser_failed: {e}", "raw_stdout": proc.stdout[:2000]}

    result = {
        "status": "success" if proc.returncode in (0, 124, -9, -15) else "tool_error",
        "atom_id": atom.id,
        "inputs": inputs,
        "command": cmd,
        "returncode": proc.returncode,
        "duration_ms": duration_ms,
        "parsed_output": parsed,
        "artifact_path": artifact_rel_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "session_id": session_id,
    }

    return result
