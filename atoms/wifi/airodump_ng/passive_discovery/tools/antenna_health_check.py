#!/usr/bin/env python3
"""
Antenna & Monitor Interface Health Check

Purpose:
    A small, standalone helper script designed to be read and used by the local LLM
    (Qwen via Hermes) when working with the wifi.airodump_ng.passive_discovery Atom.

    It helps the LLM answer questions like:
    - Is the expected monitor interface actually present and in monitor mode?
    - Is the external MediaTek antenna (0e8d:7961) in a healthy power state?
    - Did the USB device recently disconnect?

Usage (for operator or LLM):

    python3 antenna_health_check.py --interface wlan1mon --json

    python3 antenna_health_check.py --interface wlan1mon

The script is intentionally self-contained so the LLM can copy patterns from it
when writing more robust wireless tooling.

Recommended: Run this before any long passive scan as a pre-flight check.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


TARGET_VID = "0e8d"
TARGET_PID = "7961"  # External MediaTek mt7921u antenna


def run_cmd(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout + result.stderr
    except Exception as e:
        return f"ERROR running {' '.join(cmd)}: {e}"


def check_interface(interface: str) -> dict[str, Any]:
    """Check if the interface exists and is in monitor mode."""
    output = run_cmd(["iw", "dev", interface, "info"])
    info = {"exists": False, "type": None, "phy": None, "raw": output}

    if "Interface" in output and "type" in output:
        info["exists"] = True
        type_match = re.search(r"type\s+(\S+)", output)
        if type_match:
            info["type"] = type_match.group(1)
        phy_match = re.search(r"wiphy\s+(\d+)", output)
        if phy_match:
            info["phy"] = f"phy{phy_match.group(1)}"

    return info


def check_usb_power_state() -> dict[str, Any]:
    """Check power management state of the target MediaTek USB device."""
    result = {
        "device_found": False,
        "power_control": None,
        "autosuspend_delay_ms": None,
        "bus_port": None,
    }

    for dev_path in Path("/sys/bus/usb/devices").glob("*"):
        id_vendor = (dev_path / "idVendor").read_text().strip() if (dev_path / "idVendor").exists() else ""
        id_product = (dev_path / "idProduct").read_text().strip() if (dev_path / "idProduct").exists() else ""

        if id_vendor == TARGET_VID and id_product == TARGET_PID:
            result["device_found"] = True
            result["bus_port"] = dev_path.name

            control_file = dev_path / "power" / "control"
            delay_file = dev_path / "power" / "autosuspend_delay_ms"

            if control_file.exists():
                result["power_control"] = control_file.read_text().strip()
            if delay_file.exists():
                result["autosuspend_delay_ms"] = delay_file.read_text().strip()
            break

    return result


def check_recent_usb_events() -> list[str]:
    """Look for recent USB disconnect / reset events related to the target device."""
    dmesg_out = run_cmd(["dmesg", "-T"])
    events = []
    for line in dmesg_out.splitlines():
        if "usb" in line.lower() and ("disconnect" in line.lower() or "reset" in line.lower()):
            if TARGET_VID in line or TARGET_PID in line or "mt7921" in line.lower():
                events.append(line.strip())
    return events[-5:]  # last 5 relevant events


def main():
    parser = argparse.ArgumentParser(description="Health check for external monitor-mode antenna")
    parser.add_argument("--interface", required=True, help="Expected monitor interface (e.g. wlan1mon)")
    parser.add_argument("--json", action="store_true", help="Output structured JSON")
    args = parser.parse_args()

    report = {
        "interface": args.interface,
        "interface_status": check_interface(args.interface),
        "usb_device": check_usb_power_state(),
        "recent_events": check_recent_usb_events(),
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Antenna Health Check — Interface: {args.interface}\n")
        iface = report["interface_status"]
        print(f"Interface exists: {iface['exists']}")
        if iface["exists"]:
            print(f"  Type: {iface['type']}")
            print(f"  PHY : {iface['phy']}")
        else:
            print("  WARNING: Interface not found. Antenna may have dropped.")

        usb = report["usb_device"]
        print(f"\nExternal MediaTek device (0e8d:7961):")
        print(f"  Found: {usb['device_found']}")
        if usb["device_found"]:
            print(f"  Bus/Port      : {usb['bus_port']}")
            print(f"  power/control : {usb['power_control']}")
            if usb["power_control"] == "auto":
                print("  *** RECOMMENDATION: Create udev rule to set power/control=on ***")
            print(f"  autosuspend   : {usb['autosuspend_delay_ms']} ms")

        if report["recent_events"]:
            print("\nRecent USB events for this device:")
            for ev in report["recent_events"]:
                print(f"  {ev}")
        else:
            print("\nNo recent USB disconnect/reset events found in dmesg.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
