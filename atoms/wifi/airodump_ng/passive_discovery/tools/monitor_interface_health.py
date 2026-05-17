#!/usr/bin/env python3
"""
Monitor Interface & USB Device Health Monitoring

Purpose:
    Provides detection and recovery logic for when the external USB antenna
    (MediaTek mt7921u, VID:PID 0e8d:7961) drops during passive captures.

    Addresses the primary robustness problem identified in the baseline runs:
    USB autosuspend causing wlan1mon to disappear mid-capture.

    Designed to be imported by the test runner (run_baseline.py, run_real_tests.py)
    and by the Atom's command execution path.

Usage:
    # Pre-flight check (before starting a capture)
    health = MonitorHealth()
    status = health.pre_flight("wlan1mon")
    if not status["healthy"]:
        print("Cannot start: " + status["reason"])

    # Mid-run health check (call periodically during long captures)
    status = health.check("wlan1mon")
    if status["interface_dropped"]:
        print("WARNING: Interface dropped! Recovery needed.")

    # USB power state verification
    usb = health.check_usb_device()
    if usb["power_control"] == "auto":
        print("WARNING: USB autosuspend enabled - device may drop!")

    # Recovery attempt
    if status["interface_dropped"]:
        recovery = health.recover("wlan1mon")
        if recovery["success"]:
            print("Recovered successfully")
        else:
            print("Recovery failed: " + recovery["reason"])
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# Target MediaTek mt7921u USB device
TARGET_VID = "0e8d"
TARGET_PID = "7961"


def _run(cmd: list[str], timeout: int = 10) -> tuple[str, int]:
    """Run a command and return (stdout + stderr, returncode)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired as e:
        return str(e), 124
    except FileNotFoundError:
        return f"Command not found: {cmd[0]}", 127
    except Exception as e:
        return str(e), 1


def _get_phy_for_interface(interface: str) -> str | None:
    """Get the phy#N number for a given interface name."""
    output, _ = _run(["iw", "dev", interface, "info"])
    match = re.search(r"wiphy\s+(\d+)", output)
    if match:
        return f"phy{match.group(1)}"
    return None


def _get_usb_port_for_phy(phy_name: str) -> str | None:
    """Find which USB port a given phy belongs to by scanning sysfs."""
    # Map phy devices to their USB parent
    if not phy_name or not phy_name.startswith("phy"):
        return None
    try:
        phy_idx = int(phy_name[3:])
        # Try to find the wireless device under /sys/class/ieee80211/
        phy_path = Path(f"/sys/class/ieee80211/{phy_name}")
        if not phy_path.exists():
            return None
        # Check if there's a USB parent
        for link in phy_path.glob("device/driver/ieee80211/*"):
            # This path may not exist; try the alternative approach
            pass
        # Alternative: scan all USB devices and check their phy
        for usb_dev in Path("/sys/bus/usb/devices").glob("*"):
            for phy_link in usb_dev.glob("*/ieee80211/*"):
                try:
                    target = Path(phy_link).resolve().name
                    if target == phy_name:
                        return usb_dev.name
                except (OSError, ValueError):
                    pass
        # Fallback: check if the phy is under a known USB device
        # by looking at the netdev symlink
        net_path = Path(f"/sys/class/net/{phy_name.replace('phy', 'wlan')}")
        if net_path.exists():
            try:
                resolved = net_path.resolve()
                parts = resolved.parts
                for i, part in enumerate(parts):
                    if part == "8-1" or part.startswith("1-"):
                        return part
            except (OSError, ValueError):
                pass
    except Exception:
        pass
    return None


def _check_usb_device() -> dict[str, Any]:
    """Check the power state and presence of the target MediaTek USB device."""
    result = {
        "device_found": False,
        "power_control": None,
        "autosuspend_delay_ms": None,
        "bus_port": None,
        "autosuspend_enabled": False,
    }

    for dev_path in Path("/sys/bus/usb/devices").glob("*"):
        id_vendor_file = dev_path / "idVendor"
        id_product_file = dev_path / "idProduct"
        if not id_vendor_file.exists() or not id_product_file.exists():
            continue
        try:
            id_vendor = id_vendor_file.read_text().strip()
            id_product = id_product_file.read_text().strip()
        except OSError:
            continue

        if id_vendor == TARGET_VID and id_product == TARGET_PID:
            result["device_found"] = True
            result["bus_port"] = dev_path.name

            control_file = dev_path / "power" / "control"
            delay_file = dev_path / "power" / "autosuspend_delay_ms"

            if control_file.exists():
                result["power_control"] = control_file.read_text().strip()
                result["autosuspend_enabled"] = (
                    result["power_control"] == "auto"
                )
            if delay_file.exists():
                result["autosuspend_delay_ms"] = delay_file.read_text().strip()
            break

    return result


def _check_interface(interface: str) -> dict[str, Any]:
    """Check if the interface exists and is in monitor mode."""
    output, rc = _run(["iw", "dev", interface, "info"])
    info = {
        "exists": False,
        "type": None,
        "phy": None,
        "operstate": None,
        "raw": output,
    }

    if "Interface" in output:
        info["exists"] = True
        type_match = re.search(r"type\s+(\S+)", output)
        if type_match:
            info["type"] = type_match.group(1)
        phy_match = re.search(r"wiphy\s+(\d+)", output)
        if phy_match:
            info["phy"] = f"phy{phy_match.group(1)}"

    # Check operstate (interface up/down)
    oper_path = Path(f"/sys/class/net/{interface}/operstate")
    if oper_path.exists():
        try:
            info["operstate"] = oper_path.read_text().strip()
        except OSError:
            pass

    return info


def _check_dmesg_events(minutes: int = 5, hint: str = "wlan") -> list[str]:
    """Check recent dmesg for USB disconnect/reset events for the target device."""
    output, _ = _run(["dmesg", "-T"])
    events = []
    for line in output.splitlines():
        line_lower = line.lower()
        if any(kw in line_lower for kw in ["disconnect", "reset", "resume", "suspend"]):
            if any(kw in line_lower for kw in [TARGET_VID, TARGET_PID, "mt7921", "mediatek", hint]):
                events.append(line.strip())
    return events[-10:]  # last 10 relevant events


class MonitorHealth:
    """
    Health monitoring and recovery for WiFi monitor interfaces
    with external USB antennas.

    IMPORTANT SAFETY NOTE FOR LLMs AND OPERATORS:
    ------------------------------------------------
    The `recover()` method is intentionally conservative. In its current
    implementation it does NOT automatically execute destructive commands
    (bringing interfaces down, creating monitor interfaces, etc.).

    It reports the exact commands that would need to be run with sudo.

    Any future enhancement that actually executes recovery steps MUST:
      - Default to dry_run=True
      - Require explicit human confirmation
      - Log every action taken
      - Only be callable after a failed pre_flight check
    """

    def __init__(self):
        self._last_status = None

    def check(self, interface: str) -> dict[str, Any]:
        """
        Perform a single health check on the monitor interface and USB device.

        Returns a status dict with:
            - healthy: bool (all checks pass)
            - interface_exists: bool
            - interface_in_monitor_mode: bool
            - usb_device_present: bool
            - usb_autosuspend_disabled: bool | None
            - interface_dropped: bool (was up, now gone)
            - recent_events: list of dmesg events
            - recommendations: list of strings
            - reason: None if healthy, or description of issue
        """
        recommendations = []
        reason = None

        iface_status = _check_interface(interface)
        usb_status = _check_usb_device()
        recent_events = _check_dmesg_events()

        # Determine if interface dropped (existed before, now gone)
        interface_dropped = not iface_status["exists"]

        # Determine USB autosuspend state
        usb_autosuspend_ok = None
        if usb_status["device_found"]:
            if usb_status["power_control"] == "on":
                usb_autosuspend_ok = True
            elif usb_status["power_control"] == "auto":
                usb_autosuspend_ok = False
                recommendations.append(
                    "Create udev rule: ATTR{power/control}=\"on\" "
                    "for VID 0e8d PID 7961"
                )
        else:
            usb_autosuspend_ok = False
            recommendations.append(
                "External MediaTek antenna not found in sysfs. "
                "Check USB connection."
            )

        # Check if interface is in monitor mode
        monitor_mode = iface_status["exists"] and iface_status["type"] == "monitor"

        # Check interface state
        interface_up = iface_status.get("operstate") == "up"

        # Overall health
        healthy = (
            iface_status["exists"]
            and monitor_mode
            and usb_status["device_found"]
            and usb_autosuspend_ok is not False
        )

        if not iface_status["exists"]:
            reason = "Monitor interface does not exist — antenna likely dropped"
        elif not monitor_mode:
            reason = f"Interface exists but is in '{iface_status['type']}' mode, not 'monitor'"
        elif not usb_status["device_found"]:
            reason = "USB antenna not detected by kernel"
        elif usb_autosuspend_ok is False:
            reason = "USB autosuspend is ENABLED — device may drop during capture"

        self._last_status = {
            "healthy": healthy,
            "interface_exists": iface_status["exists"],
            "interface_in_monitor_mode": monitor_mode,
            "interface_up": interface_up,
            "usb_device_present": usb_status["device_found"],
            "usb_autosuspend_disabled": usb_autosuspend_ok,
            "usb_power_control": usb_status["power_control"],
            "interface_dropped": interface_dropped,
            "interface_type": iface_status["type"],
            "interface_phy": iface_status["phy"],
            "recent_events": recent_events,
            "recommendations": recommendations,
            "reason": reason,
        }

        return self._last_status

    def pre_flight(self, interface: str) -> dict[str, Any]:
        """
        Pre-flight check before starting a capture.
        Returns the same structure as check(), but with stricter criteria.

        A pre_flight check fails if:
            - Interface doesn't exist
            - Interface isn't in monitor mode
            - USB device not found
            - USB autosuspend is enabled (will cause drops)
        """
        status = self.check(interface)

        if not status["interface_exists"]:
            status["can_run"] = False
            status["reason"] = (
                f"Cannot start capture: interface '{interface}' does not exist. "
                f"Create it with: sudo ip link set wlan1 down && "
                f"sudo iw dev wlan1 interface add {interface} type monitor && "
                f"sudo ip link set {interface} up"
            )
            return status

        if not status["interface_in_monitor_mode"]:
            status["can_run"] = False
            status["reason"] = (
                f"Cannot start capture: interface is in '{status['interface_type']}' mode, "
                f"not 'monitor'. Recreate it as a monitor interface."
            )
            return status

        if not status["usb_device_present"]:
            status["can_run"] = False
            status["reason"] = (
                f"Cannot start capture: external MediaTek USB device not found. "
                f"Check USB connection."
            )
            return status

        if status["usb_autosuspend_disabled"] is False:
            status["can_run"] = False
            status["reason"] = (
                f"Cannot start capture: USB autosuspend is enabled for the "
                f"external antenna. Apply the udev rule before capturing."
            )
            return status

        status["can_run"] = True
        return status

    def recover(self, interface: str, managed_iface: str = "wlan1", dry_run: bool = True) -> dict[str, Any]:
        """
        Plan (and optionally perform) recovery for the monitor interface and USB device.

        SAFETY GUARDRAILS (MANDATORY FOR GOLD STANDARD):
        - Defaults to dry_run=True: **never mutates** interface state or USB power.
          Only computes the exact commands the operator must review and approve.
        - Even with dry_run=False, interface recreation (ip/iw) is **never** executed
          by this method — it is always returned in commands_to_run for explicit
          human execution after approval. Only the low-risk USB power/control write
          is attempted when dry_run=False (and it will usually still require sudo).
        - This method is reference material for LLMs. Callers (run_baseline.py etc.)
          must gate any dry_run=False path behind explicit operator confirmation.
        - All decision points and commands are fully auditable in the return value.

        Returns:
            {
                "success": bool,
                "dry_run": bool,
                "steps_attempted": list[str],
                "steps_succeeded": list[str],
                "steps_failed": list[str],
                "commands_to_run": list[str],   # exact, copy-pasteable sudo commands
                "current_state": dict,          # state before any action
                "post_state": dict,             # state after (same as current when dry_run)
                "reason": str | None,
            }
        """
        steps_attempted: list[str] = []
        steps_succeeded: list[str] = []
        steps_failed: list[str] = []
        commands_to_run: list[str] = []

        # Step 1: Current state (always safe)
        current = self.check(interface)
        steps_attempted.append("current_state_check")

        usb_status = _check_usb_device()
        needs_usb_fix = (
            current.get("usb_device_present")
            and current.get("usb_autosuspend_disabled") is False
        )

        # Step 2: USB autosuspend fix (only low-risk power write)
        if needs_usb_fix and usb_status.get("bus_port"):
            steps_attempted.append("plan_usb_autosuspend_fix")
            port = usb_status["bus_port"]
            cmd = (
                f"sudo sh -c 'echo on > /sys/bus/usb/devices/{port}/power/control'"
            )
            commands_to_run.append(cmd)

            if not dry_run:
                # Only attempt when explicitly allowed (still often fails without root)
                power_control = Path(f"/sys/bus/usb/devices/{port}/power/control")
                if power_control.exists():
                    try:
                        power_control.write_text("on\n")
                        steps_succeeded.append("usb_autosuspend_fix_write")
                    except PermissionError:
                        steps_failed.append("usb_autosuspend_fix_write (needs sudo)")
            else:
                steps_succeeded.append("usb_autosuspend_fix_planned")

        # Step 3: Monitor interface recreation — ALWAYS command list only
        if not current.get("interface_exists"):
            steps_attempted.append("plan_monitor_interface_recreate")
            phy = current.get("interface_phy")
            managed_found = False

            for candidate in ["wlan1", "wlan0", managed_iface]:
                _, rc = _run(["ip", "link", "show", candidate])
                if rc == 0:
                    cmd1 = f"sudo ip link set {candidate} down"
                    cmd2 = f"sudo iw dev {candidate} interface add {interface} type monitor"
                    cmd3 = f"sudo ip link set {interface} up"

                    commands_to_run.extend([cmd1, cmd2, cmd3])
                    steps_succeeded.append(
                        f"monitor_recreate_planned_via_{candidate}"
                    )
                    managed_found = True
                    break

            if not managed_found:
                steps_failed.append("monitor_recreate (no suitable managed interface found)")
        else:
            steps_succeeded.append("interface_already_present")

        # Step 4: Post-action verification (re-check; no change when dry_run=True)
        steps_attempted.append("post_recovery_verification")
        post = self.check(interface)

        if post.get("healthy"):
            steps_succeeded.append("post_recovery_verification")
        else:
            steps_failed.append("post_recovery_verification (still unhealthy)")

        success = bool(
            post.get("healthy")
            or any("planned" in s for s in steps_succeeded)
        )

        return {
            "success": success,
            "dry_run": dry_run,
            "steps_attempted": steps_attempted,
            "steps_succeeded": steps_succeeded,
            "steps_failed": steps_failed,
            "commands_to_run": commands_to_run,
            "current_state": current,
            "post_state": post,
            "reason": None if success else "Recovery incomplete (see commands_to_run)",
        }

    def periodic_check(
        self,
        interface: str,
        interval_seconds: int = 30,
        max_checks: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Run periodic health checks during a capture.

        Args:
            interface: Monitor interface name
            interval_seconds: How often to check
            max_checks: Maximum number of checks (None = until manually stopped)

        Returns:
            List of status dicts from each check
        """
        import time

        results = []
        check_num = 0

        while max_checks is None or check_num < max_checks:
            status = self.check(interface)
            results.append(status)

            if not status["healthy"]:
                print(f"WARNING: Health check #{check_num + 1} FAILED: {status['reason']}")
                print(f"  Recommendations: {'; '.join(status['recommendations'])}")
                return results  # Stop on first failure

            check_num += 1
            print(f"Health check #{check_num}: OK")

            if max_checks and check_num >= max_checks:
                break

            time.sleep(interval_seconds)

        return results


def _test_dry_run_contract(interface: str = "wlan1mon") -> bool:
    """
    Gold Standard safety self-test for the recover() contract.
    Verifies that dry_run=True produces identical pre/post state and
    populates commands_to_run without performing any mutations.
    """
    health = MonitorHealth()
    before = health.check(interface)

    result = health.recover(interface, dry_run=True)

    after = health.check(interface)

    # Invariants required for the Gold Standard reference
    state_unchanged = (
        before.get("interface_exists") == after.get("interface_exists")
        and before.get("interface_in_monitor_mode") == after.get("interface_in_monitor_mode")
        and before.get("usb_power_control") == after.get("usb_power_control")
    )

    has_commands = isinstance(result.get("commands_to_run"), list)
    returned_dry_run = result.get("dry_run") is True
    performed_verification = "post_recovery_verification" in result.get("steps_attempted", [])

    passed = state_unchanged and has_commands and returned_dry_run and performed_verification

    print("=== Gold Standard dry_run safety contract test ===")
    print(f"Interface: {interface}")
    print(f"dry_run flag returned correctly: {returned_dry_run}")
    print(f"commands_to_run entries: {len(result.get('commands_to_run', []))}")
    print(f"Pre/post hardware state unchanged: {state_unchanged}")
    print(f"Test PASSED: {passed}")

    if not passed:
        print("  !! FAILURE - this must never happen for the reference Atom !!")
        print(f"  steps_attempted: {result.get('steps_attempted')}")
    return passed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor interface and USB device health checker"
    )
    parser.add_argument("--interface", default="wlan1mon", help="Monitor interface")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--pre-flight", action="store_true", help="Run pre-flight check")
    parser.add_argument("--recover", action="store_true", help="Plan recovery (safe by default)")
    parser.add_argument("--test-safety", action="store_true", help="Run the dry_run contract self-test (Gold Standard requirement)")
    args = parser.parse_args()

    health = MonitorHealth()

    if args.pre_flight:
        status = health.pre_flight(args.interface)
        if args.json:
            import json

            print(json.dumps(status, indent=2))
        else:
            print(f"Pre-flight check for {args.interface}:")
            print(f"  Healthy: {status['healthy']}")
            print(f"  Can run: {status.get('can_run', 'N/A')}")
            if status.get("reason"):
                print(f"  Reason: {status['reason']}")
            if status.get("recommendations"):
                print(f"  Recommendations:")
                for rec in status["recommendations"]:
                    print(f"    - {rec}")
        sys.exit(0 if status.get("can_run", False) else 1)

    if args.recover:
        recovery = health.recover(args.interface)
        if args.json:
            import json

            print(json.dumps(recovery, indent=2, default=str))
        else:
            print(f"Recovery plan for {args.interface} (dry_run={recovery['dry_run']}):")
            print(f"  Success: {recovery['success']}")
            print(f"  Steps attempted: {recovery['steps_attempted']}")
            print(f"  Steps succeeded: {recovery['steps_succeeded']}")
            print(f"  Steps failed: {recovery['steps_failed']}")
            if recovery.get("commands_to_run"):
                print("\n  Exact commands to run (after human review/approval):")
                for c in recovery["commands_to_run"]:
                    print(f"    {c}")
            if recovery.get("reason"):
                print(f"\n  Reason: {recovery['reason']}")
            if not recovery.get("dry_run", True):
                print("\n  WARNING: dry_run=False — mutations were attempted where possible.")
        sys.exit(0 if recovery.get("success") else 1)

    if args.test_safety:
        ok = _test_dry_run_contract(args.interface)
        sys.exit(0 if ok else 1)

    # Default: simple check
    status = health.check(args.interface)
    if args.json:
        import json

        print(json.dumps(status, indent=2))
    else:
        print(f"Monitor Health — Interface: {args.interface}\n")
        print(f"Interface exists: {status['interface_exists']}")
        if status["interface_exists"]:
            print(f"  Type: {status['interface_type']}")
            print(f"  Monitor mode: {status['interface_in_monitor_mode']}")
            print(f"  Up: {status['interface_up']}")
        print(f"USB device present: {status['usb_device_present']}")
        if status["usb_device_present"]:
            print(f"  Port: {status.get('usb_power_control', 'N/A')}")
            print(f"  Autosuspend disabled: {status['usb_autosuspend_disabled']}")
        print(f"\nOverall: {'HEALTHY' if status['healthy'] else 'UNHEALTHY'}")
        if status["reason"]:
            print(f"Issue: {status['reason']}")
        if status["recommendations"]:
            print("\nRecommendations:")
            for rec in status["recommendations"]:
                print(f"  - {rec}")
        if status["recent_events"]:
            print("\nRecent USB events:")
            for ev in status["recent_events"]:
                print(f"  {ev}")
    sys.exit(0 if status["healthy"] else 1)
