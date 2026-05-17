#!/usr/bin/env python3
"""
airodump-ng Passive Discovery — Output Parser

Gold Standard Reference Implementation
"""

import csv
import os
from pathlib import Path
from typing import Any
from datetime import datetime


def parse_output(
    csv_path: str | Path | None = None,
    raw_text: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Parse airodump-ng CSV output into structured data.
    """
    # Auto-detect csv_path from output_prefix if provided in kwargs
    if not csv_path and "output_prefix" in kwargs:
        prefix = kwargs["output_prefix"]
        if prefix:
            csv_path = f"{prefix}-01.csv"

    # EMERGENCY DEBUG
    with open("/tmp/parser_emergency.log", "a") as f:
        f.write(f"--- {datetime.now()} ---\n")
        f.write(f"Looking for: {csv_path}\n")
        if csv_path:
            f.write(f"Exists (os): {os.path.exists(csv_path)}\n")
            try:
                f.write(f"Files in /tmp: {os.listdir('/tmp')}\n")
            except:
                f.write("Cannot list /tmp\n")

    if csv_path and os.path.exists(csv_path):
        raw_text = Path(csv_path).read_text(encoding="utf-8", errors="replace")
        source = "file"
    elif raw_text:
        source = "raw_text"
    else:
        return {
            "error": "csv_file_not_found",
            "path": str(csv_path),
            "access_points": [],
            "clients": [],
        }

    try:
        access_points, clients = _parse_airodump_csv(raw_text)
        return {
            "access_points": access_points,
            "clients": clients,
            "source": source or "unknown",
            "raw_length": len(raw_text),
        }
    except Exception as e:
        return {
            "error": f"parse_failed: {str(e)}",
            "source": "exception",
            "access_points": [],
            "clients": [],
        }


def _parse_section(section_text: str) -> list[dict]:
    records = []
    try:
        reader = csv.DictReader(section_text.strip().splitlines())
        if reader.fieldnames:
            reader.fieldnames = [f.strip() for f in reader.fieldnames]
        for row in reader:
            records.append(row)
    except Exception:
        pass
    return records


def _parse_airodump_csv(raw_text: str) -> tuple[list[dict], list[dict]]:
    sections = raw_text.split("\n\n")
    aps = _parse_section(sections[0]) if len(sections) > 0 else []
    clients = _parse_section(sections[1]) if len(sections) > 1 else []

    access_points = []
    for row in aps:
        if not row.get("BSSID"):
            continue
        access_points.append({
            "bssid": row.get("BSSID", "").strip(),
            "essid": row.get("ESSID", "").strip() or None,
            "channel": _safe_int(row.get("channel")),
            "signal": _safe_int(row.get("Power")),
            "encryption": row.get("Privacy", "").strip() or None,
            "cipher": row.get("Cipher", "").strip() or None,
            "authentication": row.get("Authentication", "").strip() or None,
            "beacons": _safe_int(row.get("# beacons")),
            "data_packets": _safe_int(row.get("# IV")),
            "first_seen": row.get("First time seen", "").strip() or None,
            "last_seen": row.get("Last time seen", "").strip() or None,
        })

    client_list = []
    for row in clients:
        if not row.get("Station MAC"):
            continue
        client_list.append({
            "station_mac": row.get("Station MAC", "").strip(),
            "bssid": row.get("BSSID", "").strip() or None,
            "signal": _safe_int(row.get("Power")),
            "packets": _safe_int(row.get("# packets")),
            "probes": row.get("Probed ESSIDs", "").strip() or None,
        })

    return access_points, client_list


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None
