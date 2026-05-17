#!/usr/bin/env python3
"""
Baseline Data Collection for wifi.airodump_ng.passive_discovery

Runs real airodump-ng captures across multiple tiers and collects
structured results. Uses /usr/bin/timeout to stop airodump-ng after
the specified duration, with sudo for packet capture privileges.
"""

import subprocess
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from output_parser import parse_output

# Import the health monitoring module from the tools directory
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from monitor_interface_health import MonitorHealth


TIER_CONFIGS = {
    "basic": {
        "duration": 20,
        "band": "bg",
        "band_label": "2.4 GHz",
        "description": "Quick passive discovery on 2.4 GHz (common quick recon)",
    },
    "intermediate": {
        "duration": 60,
        "band": None,
        "band_label": "All (2.4 + 5 GHz)",
        "description": "Longer scan across all bands with client discovery",
    },
    "edge": {
        "duration": 120,
        "band": None,
        "band_label": "All (2.4 + 5 GHz)",
        "description": "Extended scan - stress test for crowded/weak signal environments",
    },
}


def run_capture(interface: str, duration: int, band: str | None, output_prefix: str,
                health_checker: MonitorHealth | None = None) -> dict:
    """Run airodump-ng for the specified duration and parse results.

    Uses /usr/bin/timeout to automatically stop airodump-ng after duration seconds.
    Uses sudo for packet capture privileges.

    Includes pre-flight and post-capture health monitoring to detect
    when the external USB antenna drops during the capture.
    """
    if health_checker is None:
        health_checker = MonitorHealth()

    # Pre-flight health check
    pre_status = health_checker.pre_flight(interface)
    capture_result = {
        "interface": interface,
        "duration": duration,
        "band": band,
        "pre_flight": pre_status,
    }

    if not pre_status.get("can_run", False):
        capture_result["returncode"] = -1
        capture_result["error"] = f"Pre-flight check failed: {pre_status['reason']}"
        print(f"  SKIPPED: {capture_result['error']}")
        return capture_result

    cmd = ["/usr/bin/timeout", str(duration), "sudo", "airodump-ng",
           interface, "--write", output_prefix, "--output-format", "csv",
           "--uptime", "--manufacturer"]
    if band:
        cmd.extend(["--band", band])

    csv_path = f"{output_prefix}-01.csv"

    print(f"  Starting airodump-ng... ({duration}s)")
    print(f"  Pre-flight: HEALTHY (interface={interface}, usb=connected)")
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=duration + 15,
    )

    # Post-capture health check
    post_status = health_checker.check(interface)
    capture_result["post_capture_health"] = post_status

    # Give airodump-ng time to flush files
    time.sleep(3)

    # Parse the CSV
    if Path(csv_path).exists():
        parsed = parse_output(csv_path=csv_path)
        capture_result["parsed"] = parsed
        capture_result["csv_path"] = str(csv_path)
    else:
        capture_result["parsed"] = {
            "error": "csv_file_not_found",
            "access_points": [],
            "clients": [],
        }

    capture_result["returncode"] = proc.returncode
    capture_result["stderr_preview"] = proc.stderr[:500] if proc.stderr else ""

    return capture_result


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Baseline data collection for airodump-ng passive discovery"
    )
    parser.add_argument("--interface", default="wlan1mon", help="Monitor-mode interface")
    parser.add_argument("--tiers", nargs="+",
                        choices=["basic", "intermediate", "edge"],
                        default=["basic", "intermediate"],
                        help="Tiers to run")
    parser.add_argument("--pre-flight-only", action="store_true",
                        help="Only run pre-flight check, don't capture")
    parser.add_argument("--skip-health", action="store_true",
                        help="Skip health monitoring (use only when health checks are known to be unreliable)")
    args = parser.parse_args()

    if args.pre_flight_only:
        health_checker = MonitorHealth()
        status = health_checker.pre_flight(args.interface)
        print(f"\nPre-flight check for {args.interface}:")
        print(f"  Healthy: {status['healthy']}")
        print(f"  Can run: {status.get('can_run', 'N/A')}")
        if status.get("reason"):
            print(f"  Reason: {status['reason']}")
        if status.get("recommendations"):
            print(f"  Recommendations:")
            for rec in status["recommendations"]:
                print(f"    - {rec}")
        sys.exit(0 if status.get("can_run", False) else 1)

    # Initialize health checker for normal runs (skip if --skip-health)
    health_checker = MonitorHealth() if not args.skip_health else None

    base_dir = Path(__file__).parent
    captures_dir = base_dir / "data" / "captures"
    results_dir = base_dir / "results"
    captures_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = []

    for tier in args.tiers:
        config = TIER_CONFIGS[tier]
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_id = f"{tier}-{timestamp}"
        output_prefix = str(captures_dir / f"capture-{run_id}")

        band_flag = config["band"]
        band_label = config.get("band_label", band_flag or "all")

        print(f"\n{'='*60}")
        print(f"TIER: {tier.upper()}")
        print(f"Description: {config['description']}")
        print(f"Interface: {args.interface}")
        print(f"Duration: {config['duration']}s")
        print(f"Band: {band_label}")
        print(f"{'='*60}")

        result = run_capture(
            interface=args.interface,
            duration=config["duration"],
            band=band_flag,
            output_prefix=output_prefix,
        )

        result["run_id"] = run_id
        result["tier"] = tier
        result["timestamp"] = timestamp
        result["inputs"] = {
            "interface": args.interface,
            "duration": config["duration"],
            "band": config.get("band", "all"),
        }
        cmd_parts = ["sudo", "airodump-ng", args.interface,
                     "--write", output_prefix, "--output-format", "csv",
                     "--uptime", "--manufacturer"]
        if band_flag:
            cmd_parts.extend(["--band", band_flag])
        result["command"] = " ".join(cmd_parts)

        if "parsed" in result:
            ap_count = len(result["parsed"].get("access_points", []))
            client_count = len(result["parsed"].get("clients", []))
            print(f"  Access Points found: {ap_count}")
            print(f"  Clients found: {client_count}")
            print(f"  CSV: {result.get('csv_path', 'N/A')}")
        else:
            print("  Tier was skipped (pre-flight failed). No capture data.")

        # Save result
        result_file = results_dir / f"result-{run_id}.json"
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"  Result file: {result_file}")
        all_results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("BASELINE SUMMARY")
    print(f"{'='*60}")
    for r in all_results:
        if "parsed" in r:
            ap_count = len(r["parsed"].get("access_points", []))
            client_count = len(r["parsed"].get("clients", []))
        else:
            ap_count = 0
            client_count = 0
        tier = r["tier"]
        print(f"  {tier:12s}: {ap_count:3d} APs, {client_count:3d} clients")

    # Detailed AP listing
    print(f"\n{'='*60}")
    print("DETAILED ACCESS POINT LIST")
    print(f"{'='*60}")
    for r in all_results:
        tier = r["tier"]
        aps = r["parsed"].get("access_points", [])
        print(f"\n  [{tier}] {len(aps)} access points:")
        for ap in aps:
            e = ap.get("essid", "HIDDEN") or "HIDDEN"
            print(f"    {ap['bssid']}  {e:20s}  ch={str(ap.get('channel','?')):>3s}  "
                  f"sig={str(ap.get('signal','?')):>4s}  enc={ap.get('encryption','?') or 'OPN':>5s}")

    # Detailed client listing
    print(f"\n{'='*60}")
    print("DETAILED CLIENT LIST")
    print(f"{'='*60}")
    for r in all_results:
        tier = r["tier"]
        clients = r["parsed"].get("clients", [])
        print(f"\n  [{tier}] {len(clients)} clients:")
        for c in clients:
            probes = c.get("probes", "") or ""
            bssid = c.get("bssid", "?")
            print(f"    {c['station_mac']:17s}  {bssid:17s}  sig={str(c.get('signal','?')):>4s}  "
                  f"pkts={str(c.get('packets','?')):>4s}  probe={probes}")

    # Health summary
    if health_checker and any(r.get("pre_flight") for r in all_results):
        print(f"\n{'='*60}")
        print("HEALTH MONITORING SUMMARY")
        print(f"{'='*60}")
        for r in all_results:
            tier = r["tier"]
            pre = r.get("pre_flight", {})
            post = r.get("post_capture_health", {})
            pre_ok = pre.get("can_run", False)
            post_healthy = post.get("healthy", False)
            pre_status = "OK" if pre_ok else f"FAILED ({pre.get('reason', 'unknown')})"
            post_status = "OK" if post_healthy else f"UNHEALTHY ({post.get('reason', 'unknown')})"
            print(f"  [{tier}] Pre-flight: {pre_status:45s} Post-capture: {post_status}")

    print(f"\n{'='*60}")
    print("BASELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Captures dir: {captures_dir}")
    print(f"Results dir:  {results_dir}")


if __name__ == "__main__":
    main()
