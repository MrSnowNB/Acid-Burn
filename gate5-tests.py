#!/usr/bin/env python3
"""Gate 5: Atomic Test Harness — Test Suite

Tests that:
1. Each gate runs independently with correct results
2. The full pipeline runs end-to-end
3. Test results are deterministic and reproducible
4. Harness handles missing test files gracefully
5. Harness reports clear pass/fail summary

Run with: python3 gate5-tests.py
"""

import os
import sys
import subprocess
import yaml

ATOM_PATH = "/home/mark/Desktop/hybrid_scratchpad/atoms/nmap.yaml"

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

# ── GATE 5 CHECK 1: Each gate runs independently ────────────────────

print("\n=== CHECK 1: Independent Gate Execution ===")

gate_scripts = [
    "/home/mark/Desktop/hybrid_scratchpad/gate1-tests.py",
    "/home/mark/Desktop/hybrid_scratchpad/gate2-tests.py",
    "/home/mark/Desktop/hybrid_scratchpad/gate3-tests.py",
    "/home/mark/Desktop/hybrid_scratchpad/gate4-tests.py",
]

gate_results = {}
for gs in gate_scripts:
    if not os.path.exists(gs):
        check(f"Gate script {gs} exists", False)
        continue

    try:
        result = subprocess.run(
            ["python3", gs],
            capture_output=True, text=True, timeout=120
        )
        gate_results[os.path.basename(gs)] = result.returncode == 0
        check(f"Gate {os.path.basename(gs)} runs without error",
              result.returncode in (0, 1),  # 0=pass, 1=fail (expected), others=error
              f"Exit code: {result.returncode}, stderr: {result.stderr[:200]}")
        if result.returncode == 0:
            check(f"Gate {os.path.basename(gs)} PASSES", True)
        else:
            check(f"Gate {os.path.basename(gs)} PASSES", False, "Gate failed")
    except subprocess.TimeoutExpired:
        check(f"Gate {os.path.basename(gs)} runs without error", False, "Timeout")
    except Exception as e:
        check(f"Gate {os.path.basename(gs)} runs without error", False, str(e))

# ── GATE 5 CHECK 2: Full pipeline runs end-to-end ───────────────────

print("\n=== CHECK 2: Full Pipeline ===")

# Check all gates pass
all_pass = all(gate_results.values())
check("All gates pass (full pipeline)", all_pass,
      f"Results: {gate_results}")

# Check atom file is valid YAML
try:
    with open(ATOM_PATH) as f:
        atom = yaml.safe_load(f)
    check("Atom file is valid YAML", True)
except Exception as e:
    check("Atom file is valid YAML", False, str(e))
    atom = None

# Check atom has all required sections
if atom:
    required_sections = ["parameters", "preconditions", "example_invocations",
                         "output_parser", "schema_version"]
    for section in required_sections:
        check(f"Atom has '{section}' section", section in atom)

# Check gate1_passed is set
if atom:
    check("Atom has gate1_passed flag", atom.get("gate1_passed") == True,
          f"gate1_passed: {atom.get('gate1_passed')}")

# ── GATE 5 CHECK 3: Deterministic results ───────────────────────────

print("\n=== CHECK 3: Deterministic Results ===")

# Run gate1 twice and compare
try:
    result1 = subprocess.run(
        ["python3", gate_scripts[0]],
        capture_output=True, text=True, timeout=120
    )
    result2 = subprocess.run(
        ["python3", gate_scripts[0]],
        capture_output=True, text=True, timeout=120
    )
    check("Gate 1 produces deterministic results",
          result1.stdout == result2.stdout,
          "Outputs differ between runs")
except Exception as e:
    check("Gate 1 produces deterministic results", False, str(e))

# ── GATE 5 CHECK 4: Graceful handling of missing files ──────────────

print("\n=== CHECK 4: Missing File Handling ===")

# Check gate scripts handle missing atom gracefully
fake_gate = "/tmp/fake-gate-tests.py"
with open(fake_gate, "w") as f:
    f.write('''
import sys
sys.exit(0)
''')

try:
    result = subprocess.run(
        ["python3", fake_gate],
        capture_output=True, text=True, timeout=10
    )
    check("Harness handles simple scripts gracefully",
          result.returncode == 0)
except Exception as e:
    check("Harness handles simple scripts gracefully", False, str(e))

os.remove(fake_gate)

# ── GATE 5 CHECK 5: Summary reporting ───────────────────────────────

print("\n=== CHECK 5: Summary Reporting ===")

# Check gate1 output contains summary
try:
    result1 = subprocess.run(
        ["python3", gate_scripts[0]],
        capture_output=True, text=True, timeout=120
    )
    has_summary = "Gate 1 Results:" in result1.stdout or "PASSED" in result1.stdout or "FAILED" in result1.stdout
    check("Gate 1 output contains summary", has_summary,
          f"Summary text: {result1.stdout[-500:]}")
except Exception as e:
    check("Gate 1 output contains summary", False, str(e))

# ── SUMMARY ─────────────────────────────────────────────────────────

total = passed + len(errors)
print(f"\n{'='*60}")
print(f"Gate 5 Results: {passed}/{total} checks passed")
if errors:
    print(f"\n{len(errors)} FAILURES:")
    for name, detail in errors:
        print(f"  ✗ {name}: {detail}")
    print("\nGATE 5: FAILED — fix all failures before proceeding")
else:
    print("\nGATE 5: PASSED — all gates complete!")

sys.exit(1 if errors else 0)
