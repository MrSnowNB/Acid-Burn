#!/usr/bin/env python3
"""iwlist Command Builder — Minimal baseline WiFi Atom"""

import shlex
from typing import Any


def build_command(params: dict[str, Any]) -> list[str]:
    iface = params["interface"]
    return ["iwlist", iface, "scan"]


def estimate_duration(params: dict[str, Any]) -> int:
    return int(params.get("duration", 10))
