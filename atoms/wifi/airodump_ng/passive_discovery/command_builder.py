#!/usr/bin/env python3
"""
airodump-ng Passive Discovery — Command Builder

Gold Standard Reference Implementation

This module is responsible for turning validated, clean parameters into
the exact command line arguments for airodump-ng in passive discovery mode.

Design goals:
- Deterministic output
- Clear, auditable logic
- Focused strictly on passive discovery (no targeting logic here)
"""

import shlex
from typing import Any


def build_command(params: dict[str, Any]) -> list[str]:
    """
    Build the airodump-ng command for passive discovery.
    Uses '/usr/bin/timeout -k 5' to ensure clean termination.
    """
    duration = params.get("duration", 30)
    cmd: list[str] = ["/usr/bin/timeout", "-k", "5", str(duration), "/usr/sbin/airodump-ng"]

    # Interface (required)
    interface = params["interface"]
    cmd.append(interface)

    # Output handling - always CSV for structured parsing
    output_prefix = params.get("output_prefix", "/tmp/airodump-passive")
    cmd.extend(["--write", output_prefix])
    cmd.extend(["--output-format", "csv"])

    # Run in background (no ncurses)
    cmd.append("--background")
    cmd.append("1")

    # Useful passive discovery flags
    cmd.extend(["--uptime", "--manufacturer"])

    # Band selection
    band = params.get("band", "abg")
    if band == "2.4":
        cmd.extend(["--band", "bg"])
    elif band == "5":
        cmd.extend(["--band", "a"])
    elif band == "6":
        cmd.extend(["--band", "6"])
    # "abg" uses default (all bands)

    # Specific channels (takes precedence over band if provided)
    channels = params.get("channels")
    if channels and isinstance(channels, list) and len(channels) > 0:
        channel_str = ",".join(str(c) for c in channels)
        cmd.extend(["--channel", channel_str])

    return cmd


def get_expected_output_files(params: dict[str, Any]) -> dict[str, str]:
    """Returns expected output file paths."""
    prefix = params.get("output_prefix", "/tmp/airodump-passive")
    return {
        "csv": f"{prefix}-01.csv",
        "cap": f"{prefix}-01.cap",
    }


def estimate_runtime(params: dict[str, Any]) -> int:
    """Returns expected wall-clock time in seconds."""
    return int(params.get("duration", 30)) + 8  # small buffer for startup/shutdown


if __name__ == "__main__":
    test_params = {
        "interface": "wlan1mon",
        "duration": 45,
        "band": "5",
        "include_clients": True,
    }
    cmd = build_command(test_params)
    print("Generated command:")
    print(" ".join(shlex.quote(part) for part in cmd))
    print("\nExpected files:", get_expected_output_files(test_params))
