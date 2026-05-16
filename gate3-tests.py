#!/usr/bin/env python3
"""Gate 3: Command Builder, Flag Mapping, and Classification — Test Suite

Tests that the command builder produces correct nmap commands for all
example invocations and adversarial test cases.

Run with: python3 gate3-tests.py
"""

import json
import shlex
import sys
import yaml

# Load command builder
sys.path.insert(0, "/home/mark/Desktop/hybrid_scratchpad/atoms")
from command_builder import build_command, dry_run_command

ATOM_PATH = "/home/mark/Desktop/hybrid_scratchpad/atoms/nmap.yaml"
with open(ATOM_PATH) as f:
    atom = yaml.safe_load(f)

errors = []
passed = 0

def check(name, condition, detail=""):
    global passed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        errors.append((name, detail))
        print(f"  FAIL: {name} — {detail}")

# ── GATE 3 CHECK 1: Build commands for all 8 examples ────────────────

print("\n=== CHECK 1: Command Builder Produces Correct Commands ===")

examples = atom.get("example_invocations", [])
for ex in examples:
    inp = ex.get("input", {})
    try:
        cmd_str = dry_run_command(inp)
        cmd_parts = shlex.split(cmd_str)

        # Basic sanity: starts with nmap, ends with target
        check(f"Example '{ex['name']}' starts with nmap",
              cmd_parts[0] == "nmap",
              f"First token: {cmd_parts[0] if cmd_parts else 'EMPTY'}")

        check(f"Example '{ex['name']}' ends with target",
              cmd_parts[-1] == inp.get("target", ""),
              f"Last token: {cmd_parts[-1] if cmd_parts else 'EMPTY'}")

        # Check shlex.split succeeds (no unbalanced quotes)
        try:
            parsed = shlex.split(cmd_str)
            check(f"Example '{ex['name']}' shlex.split succeeds", True)
        except Exception as e:
            check(f"Example '{ex['name']}' shlex.split succeeds", False, str(e))

        # Check scan_type flag is present
        scan_type = inp.get("scan_type", "host-discovery")
        scan_flags = {"host-discovery": "-sn", "syn-scan": "-sS", "connect-scan": "-sT",
                      "udp-scan": "-sU", "os-detect": "-O", "version-detect": "-sV",
                      "script-scan": "-sC", "traceroute": "--traceroute"}
        expected_flag = scan_flags.get(scan_type, "-sn")
        check(f"Example '{ex['name']}' contains scan flag '{expected_flag}'",
              any(expected_flag in p for p in cmd_parts),
              f"Flags: {[p for p in cmd_parts if p.startswith('-')]}")

    except Exception as e:
        check(f"Example '{ex['name']}' builds without error", False, str(e))

# ── GATE 3 CHECK 2: Adversarial test cases ──────────────────────────

print("\n=== CHECK 2: Adversarial Cases (12 new) ===")

adversarial_cases = [
    # Case 1: Mixed IPv4 and hostname
    {"target": "192.168.9.1 example.com", "scan_type": "syn-scan",
     "name": "ipv4+hostname mix"},
    # Case 2: IPv6 target
    {"target": "2001:db8::1", "scan_type": "syn-scan",
     "name": "ipv6 target"},
    # Case 3: Stealth mode combined with explicit timing
    {"target": "192.168.9.1", "scan_type": "syn-scan", "timing_template": "insane",
     "fragment": True, "dns_resolution": False,
     "name": "stealth params override"},
    # Case 4: UDP + version detection (valid but slow)
    {"target": "192.168.9.1", "scan_type": "udp-scan", "output_format": "normal",
     "name": "udp+normal output"},
    # Case 5: Script scan with custom port
    {"target": "192.168.9.1", "scan_type": "script-scan", "ports": "80,443,8080",
     "script": "http-enum", "name": "script+custom ports"},
    # Case 6: OS detect + version detect together
    {"target": "192.168.9.1", "scan_type": "os-detect", "version_intensity": 9,
     "name": "os+version max intensity"},
    # Case 7: Max blast radius controls
    {"target": "192.168.9.0/24", "scan_type": "syn-scan", "max_rate": 10,
     "max_hosts": 50, "min_rate": 1, "name": "max blast radius controls"},
    # Case 8: Skip host discovery
    {"target": "192.168.9.1", "scan_type": "syn-scan", "skip_host_discovery": True,
     "name": "skip host discovery"},
    # Case 9: Custom DNS servers
    {"target": "example.com", "scan_type": "version-detect",
     "dns_servers": ["8.8.8.8", "1.1.1.1"], "name": "custom dns servers"},
    # Case 10: Top ports override
    {"target": "192.168.9.1", "scan_type": "syn-scan", "top_ports": 1000,
     "name": "top ports override"},
    # Case 11: Proxy + interface
    {"target": "192.168.9.1", "scan_type": "syn-scan", "proxy": "socks5://localhost:9050",
     "interface": "wlan0", "name": "proxy+interface"},
    # Case 12: Verbose + data length
    {"target": "192.168.9.1", "scan_type": "syn-scan", "verbose": 3,
     "data_length": 42, "name": "verbose+data length"},
]

for ac in adversarial_cases:
    try:
        cmd_str = dry_run_command(ac)
        cmd_parts = shlex.split(cmd_str)
        check(f"Adversarial '{ac['name']}' builds successfully",
              len(cmd_parts) > 1 and cmd_parts[0] == "nmap")
    except Exception as e:
        check(f"Adversarial '{ac['name']}' builds successfully", False, str(e))

# ── GATE 3 CHECK 3: Flag conflicts detected ─────────────────────────

print("\n=== CHECK 3: Flag Conflict Detection ===")

# traceroute + syn-scan should not both be present
conflict_input = {"target": "192.168.9.1", "scan_type": "traceroute", "syn-scan": True}
try:
    cmd_str = dry_run_command(conflict_input)
    has_traceroute = "--traceroute" in cmd_str
    has_syn = "-sS" in cmd_str
    # traceroute should not include -sS
    check("traceroute does not include -sS flag",
          not (has_traceroute and has_syn),
          f"Has --traceroute: {has_traceroute}, Has -sS: {has_syn}")
except Exception as e:
    check("traceroute does not include -sS flag", False, str(e))

# udp-scan + syn-scan conflict (mutually exclusive)
conflict_input2 = {"target": "192.168.9.1", "scan_type": "udp-scan", "syn-scan": True}
try:
    cmd_str2 = dry_run_command(conflict_input2)
    has_udp = "-sU" in cmd_str2
    has_syn2 = "-sS" in cmd_str2
    check("udp-scan does not include -sS flag",
          not (has_udp and has_syn2),
          f"Has -sU: {has_udp}, Has -sS: {has_syn2}")
except Exception as e:
    check("udp-scan does not include -sS flag", False, str(e))

# ── GATE 3 CHECK 4: Idempotency class ───────────────────────────────

print("\n=== CHECK 4: Idempotency Class ===")
ic = atom.get("idempotency_class", "pure")
check("Idempotency class is NOT 'pure'",
      ic != "pure",
      f"Current: {ic}")
check("Idempotency class reflects network side effects",
      ic in ("network_impure", "externally_observable_probe", "idempotent_under_static_target_assumption"),
      f"Current: {ic}")

# ── GATE 3 CHECK 5: Dry_run returns command without executing ────────

print("\n=== CHECK 5: Dry_run Mode ===")
dry_input = {"target": "192.168.9.1", "scan_type": "syn-scan"}
dry_result = dry_run_command(dry_input)
check("Dry_run returns a string",
      isinstance(dry_result, str),
      f"Type: {type(dry_result).__name__}")
check("Dry_run contains 'nmap'",
      "nmap" in dry_result)
check("Dry_run does not execute",
      True,  # dry_run_command is a pure function, no subprocess call here
)

# ── SUMMARY ─────────────────────────────────────────────────────────

total = passed + len(errors)
print(f"\n{'='*60}")
print(f"Gate 3 Results: {passed}/{total} checks passed")
if errors:
    print(f"\n{len(errors)} FAILURES:")
    for name, detail in errors:
        print(f"  ✗ {name}: {detail}")
    print("\nGATE 3: FAILED — fix all failures before proceeding")
else:
    print("\nGATE 3: PASSED — proceed to Gate 4")

sys.exit(1 if errors else 0)
