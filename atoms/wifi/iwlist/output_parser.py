#!/usr/bin/env python3
"""iwlist Output Parser — Baseline"""

from pathlib import Path
from typing import Any


def parse_iwlist_output(raw_stdout: str, **kwargs) -> dict[str, Any]:
    """
    Very basic parser for `iwlist <iface> scan` text output.
    Returns a minimal list of cells.
    """
    aps = []
    current = {}
    for line in raw_stdout.splitlines():
        line = line.strip()
        if line.startswith("Cell "):
            if current:
                aps.append(current)
            current = {"bssid": line.split("Address: ")[-1].strip() if "Address" in line else None}
        elif "ESSID:" in line:
            current["essid"] = line.split("ESSID:")[-1].strip().strip('"')
        elif "Channel:" in line:
            try:
                current["channel"] = int(line.split("Channel:")[-1].strip())
            except ValueError:
                pass
        elif "Quality=" in line or "Signal level=" in line:
            current["signal_raw"] = line
    if current:
        aps.append(current)

    return {"access_points": aps, "raw": raw_stdout[:2000]}
