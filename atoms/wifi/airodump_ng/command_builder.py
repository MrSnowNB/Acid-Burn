#!/usr/bin/env python3
"""
airodump-ng Command Builder — Acid Burn WiFi Atom

Deterministic builder for airodump-ng (part of the aircrack-ng suite on Kali).

This module is the single source of truth for turning clean Atom parameters
into the exact command line that will be executed.

Design goals:
- Pure functions where possible (easy to test and reason about)
- No side effects
- Correct flag ordering and quoting
- Explicit handling of monitor-mode requirements
"""

import shlex
from typing import Any


def build_command(params: dict[str, Any]) -> list[str]:
    """
    Build the airodump-ng command line from validated Atom parameters.

    Args:
        params: Dictionary matching the parameters defined in airodump_ng.yaml

    Returns:
        List of command arguments ready for subprocess (no shell=True)
    """
    cmd = ["airodump-ng"]

    interface = params["interface"]
    cmd.append(interface)

    # Duration is handled by the runner (timeout + kill), not by airodump-ng flags.
    # airodump-ng itself runs until interrupted.

    if params.get("channel"):
        cmd.extend(["--channel", str(params["channel"])])

    if params.get("bssid"):
        cmd.extend(["--bssid", params["bssid"]])

    if params.get("essid"):
        cmd.extend(["--essid", params["essid"]])

    # Output format — we always want CSV for structured parsing
    output_prefix = params.get("output_prefix", "/tmp/airodump")
    cmd.extend(["--write", output_prefix, "--output-format", "csv"])

    # Be quiet and deterministic
    cmd.extend(["--background", "1"])   # run in background mode (no ncurses)

    # Additional useful flags for clean recon
    cmd.append("--uptime")              # show uptime of APs when available
    cmd.append("--manufacturer")        # show vendor names

    return cmd


def get_expected_output_files(params: dict[str, Any]) -> dict[str, str]:
    """
    Returns the expected output file paths airodump-ng will create.
    Useful for the runner and parser.
    """
    prefix = params.get("output_prefix", "/tmp/airodump")
    return {
        "csv": f"{prefix}-01.csv",
        "cap": f"{prefix}-01.cap",
        "kismet_csv": f"{prefix}-01.kismet.csv",
        "kismet_netxml": f"{prefix}-01.kismet.netxml",
    }


def estimate_duration(params: dict[str, Any]) -> int:
    """Return the recommended wall time for this capture."""
    return int(params.get("duration", 30))


if __name__ == "__main__":
    # Quick manual test
    test_params = {
        "interface": "wlan1mon",
        "duration": 45,
        "channel": 6,
    }
    print("Command:", " ".join(shlex.quote(x) for x in build_command(test_params)))
    print("Expected files:", get_expected_output_files(test_params))
