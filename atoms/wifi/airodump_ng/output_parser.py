#!/usr/bin/env python3
"""
airodump-ng Output Parser — Acid Burn WiFi Atom

Parses the CSV output produced by airodump-ng into clean, structured data
matching the output_schema declared in airodump_ng.yaml.

airodump-ng CSV format notes:
- It writes two logical tables in one file separated by a blank line:
  1. Access Point (BSSID) table
  2. Client (Station) table
- Columns can shift slightly between versions; we use header-based parsing.
"""

import csv
from pathlib import Path
from typing import Any


def parse_csv_output(csv_path: str | Path, **kwargs) -> dict[str, Any]:
    """
    Parse airodump-ng's CSV output into the Atom output schema.

    Args:
        csv_path: Path to the -01.csv file produced by airodump-ng

    Returns:
        {
            "access_points": [...],
            "clients": [...],
            "raw_csv_path": "..."
        }
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return {
            "error": "csv_not_found",
            "path": str(csv_path),
            "access_points": [],
            "clients": [],
        }

    raw_text = csv_path.read_text(encoding="utf-8", errors="replace")

    # airodump-ng separates the two sections with a blank line
    sections = raw_text.split("\n\n")

    access_points = []
    clients = []

    if len(sections) >= 1:
        access_points = _parse_ap_section(sections[0])

    if len(sections) >= 2:
        clients = _parse_client_section(sections[1])

    return {
        "access_points": access_points,
        "clients": clients,
        "raw_csv_path": str(csv_path),
        "raw_lines": len(raw_text.splitlines()),
    }


def _parse_ap_section(text: str) -> list[dict[str, Any]]:
    """Parse the Access Point table (first section)."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return []

    # First line after header is usually the column names
    header_line = lines[0]
    # airodump-ng headers are a bit messy (contain spaces and commas)
    # Common header pattern:
    # BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key
    reader = csv.reader(lines[1:], delimiter=",", quotechar='"')

    aps = []
    for row in reader:
        if len(row) < 5:
            continue
        try:
            ap = {
                "bssid": row[0].strip(),
                "first_seen": row[1].strip() if len(row) > 1 else None,
                "last_seen": row[2].strip() if len(row) > 2 else None,
                "channel": int(row[3]) if row[3].strip().isdigit() else None,
                "speed": row[4].strip() if len(row) > 4 else None,
                "encryption": row[5].strip() if len(row) > 5 else None,
                "cipher": row[6].strip() if len(row) > 6 else None,
                "authentication": row[7].strip() if len(row) > 7 else None,
                "signal": int(row[8]) if len(row) > 8 and row[8].strip().lstrip("-").isdigit() else None,
                "beacons": int(row[9]) if len(row) > 9 and row[9].strip().isdigit() else 0,
                "data_packets": int(row[10]) if len(row) > 10 and row[10].strip().isdigit() else 0,
                "essid": row[13].strip() if len(row) > 13 else None,
            }
            aps.append(ap)
        except Exception:
            continue
    return aps


def _parse_client_section(text: str) -> list[dict[str, Any]]:
    """Parse the Client (Station) table (second section)."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return []

    clients = []
    reader = csv.reader(lines[1:], delimiter=",", quotechar='"')
    for row in reader:
        if len(row) < 6:
            continue
        try:
            client = {
                "station_mac": row[0].strip(),
                "first_seen": row[1].strip() if len(row) > 1 else None,
                "last_seen": row[2].strip() if len(row) > 2 else None,
                "bssid": row[5].strip() if len(row) > 5 else None,
                "signal": int(row[3]) if len(row) > 3 and row[3].strip().lstrip("-").isdigit() else None,
                "packets": int(row[4]) if len(row) > 4 and row[4].strip().isdigit() else 0,
                "probes": row[6].strip() if len(row) > 6 else None,
            }
            clients.append(client)
        except Exception:
            continue
    return clients


if __name__ == "__main__":
    # Manual test helper
    import sys
    if len(sys.argv) > 1:
        result = parse_csv_output(sys.argv[1])
        print(f"Found {len(result['access_points'])} APs and {len(result['clients'])} clients")
    else:
        print("Usage: python output_parser.py /tmp/airodump-01.csv")
