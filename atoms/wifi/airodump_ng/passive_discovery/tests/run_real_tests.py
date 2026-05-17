#!/usr/bin/env python3
"""
Real Hardware Test Runner for wifi.airodump_ng.passive_discovery

This script executes the Atom against real WiFi environments using the
external antenna and monitor-mode interface.

All raw data is stored locally in the tests/ directory (gitignored).

Usage examples:
    python3 run_real_tests.py --interface wlan1mon
    python3 run_real_tests.py --interface wlan1mon --tier basic
    python3 run_real_tests.py --interface wlan1mon --tier intermediate --duration 60
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the parent directory so we can import the Atom's own toolchain
sys.path.insert(0, str(Path(__file__).parent.parent))

from command_builder import build_command, get_expected_output_files
from output_parser import parse_output


def get_tier_config(tier: str) -> dict:
    """Return realistic parameters for each real-world workflow tier."""
    if tier == "basic":
        return {
            "duration": 20,
            "band": "2.4",
            "include_clients": True,
            "description": "Quick passive discovery on 2.4 GHz (common quick recon)",
        }
    elif tier == "intermediate":
        return {
            "duration": 60,
            "band": "abg",
            "include_clients": True,
            "description": "Longer scan across bands with client discovery",
        }
    elif tier == "edge":
        return {
            "duration": 120,
            "band": "abg",
            "include_clients": True,
            "description": "Extended scan - stress test for crowded / weak signal environments",
        }
    else:
        raise ValueError(f"Unknown tier: {tier}")


def run_real_test(interface: str, tier: str, custom_duration: int | None = None):
    base_dir = Path(__file__).parent
    captures_dir = base_dir / "data" / "captures"
    results_dir = base_dir / "results"
    captures_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    config = get_tier_config(tier)
    duration = custom_duration or config["duration"]

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{tier}-{timestamp}"
    output_prefix = str(captures_dir / f"capture-{run_id}")

    inputs = {
        "interface": interface,
        "duration": duration,
        "band": config["band"],
        "include_clients": config["include_clients"],
        "output_prefix": output_prefix,
    }

    print(f"\n=== Running {tier.upper()} real-world test ===")
    print(f"Description : {config['description']}")
    print(f"Interface   : {interface}")
    print(f"Duration    : {duration}s")
    print(f"Band        : {config['band']}")
    print(f"Output prefix: {output_prefix}")
    print("Starting airodump-ng...\n")

    cmd = build_command(inputs)

    try:
        # We run with timeout slightly longer than requested duration
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration + 15,
        )
    except subprocess.TimeoutExpired:
        print("Test timed out (as expected for long-running capture).")
        proc = None

    # Expected files from the builder
    expected_files = get_expected_output_files(inputs)
    csv_path = expected_files["csv"]

    # Give airodump-ng a moment to flush files
    time.sleep(2)

    # Parse using the Atom's own parser (supports file path)
    parsed = parse_output(csv_path=csv_path)

    # Save structured result
    result_file = results_dir / f"result-{run_id}.json"
    import json
    result_data = {
        "run_id": run_id,
        "tier": tier,
        "timestamp": timestamp,
        "inputs": inputs,
        "command": cmd,
        "returncode": proc.returncode if proc else "timeout",
        "parsed": parsed,
        "csv_path": str(csv_path),
        "cap_path": expected_files.get("cap"),
    }

    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=2)

    print(f"\n=== Test Complete ===")
    print(f"CSV capture : {csv_path}")
    print(f"Result file : {result_file}")
    print(f"Access Points found: {len(parsed.get('access_points', []))}")
    print(f"Clients found      : {len(parsed.get('clients', []))}")

    return result_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real hardware test runner for passive discovery Atom")
    parser.add_argument("--interface", required=True, help="Monitor-mode interface (e.g. wlan1mon)")
    parser.add_argument("--tier", choices=["basic", "intermediate", "edge"], default="basic",
                        help="Real-world workflow tier")
    parser.add_argument("--duration", type=int, default=None,
                        help="Override duration in seconds")

    args = parser.parse_args()

    run_real_test(args.interface, args.tier, args.duration)
