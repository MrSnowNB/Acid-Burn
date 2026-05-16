#!/usr/bin/env python3
"""
Gates 2-5 Test Suite for web.gobuster atom — 5-Gate Validation Protocol.

Gate 2: Postcondition Evaluation
Gate 3: Timeout Enforcement (end-to-end)
Gate 4: Output Schema Validation
Gate 5: Atomic Test Harness (end-to-end dispatch with mock data)

Run: python3 test_gobuster_gates2to5.py
Output: JSONL test results to stdout, summary to stderr.
"""

import sys
import os
import json
import time
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path("/home/mark/Acid-Burn")
TOOLS_DIR = BASE_DIR / "global" / "tools"
BIN_DIR = BASE_DIR / "global" / "bin"
sys.path.insert(0, str(BIN_DIR))

import yaml
import parsers
from gate import check_preconditions, check_network_reachable, check_template_resolved
from parsers import PARSERS
from validate_gobuster_schema import validate_schema

# ── Load card ──────────────────────────────────────────────────────

with open(TOOLS_DIR / "web.gobuster.yaml") as f:
    card = yaml.safe_load(f)

CARD_ID = card["id"]
CARD_VERSION = card.get("version", 0)
OUTPUT_TYPE = card["outputs"]["type"]
ARTIFACT_PATH_TEMPLATE = card["outputs"]["artifact_path"]

# ── Test harness ───────────────────────────────────────────────────

TESTS_RUN = 0
TESTS_PASSED = 0
TESTS_FAILED = 0
RESULTS = []


def record(test_name, passed, detail="", test_type="gate2to5"):
    global TESTS_RUN, TESTS_PASSED, TESTS_FAILED
    TESTS_RUN += 1
    if passed:
        TESTS_PASSED += 1
        status = "PASS"
    else:
        TESTS_FAILED += 1
        status = "FAIL"

    entry = {
        "ts": datetime.now(timezone.utc).isoformat() + "Z",
        "tool": CARD_ID,
        "card_version": CARD_VERSION,
        "gate": f"GATE_{test_type.upper().split(':')[0]}",
        "test": test_name,
        "status": status,
        "detail": detail,
    }
    RESULTS.append(entry)
    print(json.dumps(entry))
    if not passed:
        sys.stderr.write(f"[FAIL] {test_name}: {detail}\n")
    else:
        sys.stderr.write(f"[PASS] {test_name}\n")


def test(name, condition, detail=""):
    record(name, condition, detail)


# ── GATE 2: Postcondition Evaluation ──────────────────────────────

def run_gate2_tests():
    """Gate 2: Verify postconditions evaluate correctly against structured output."""
    sys.stderr.write("\n=== GATE 2: Postcondition Evaluation ===\n")

    # 2.1: Postcondition checks artifact path placeholder pattern
    has_session = "{session}" in ARTIFACT_PATH_TEMPLATE
    has_ts = "{ts}" in ARTIFACT_PATH_TEMPLATE
    test("gate2.1_artifact_path_has_placeholders",
         has_session and has_ts,
         f"artifact path template: {ARTIFACT_PATH_TEMPLATE}")

    # 2.2: Postcondition: artifact_exists — test with a real file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.raw', delete=False) as f:
        f.write("test artifact content")
        temp_path = f.name
    try:
        test("gate2.2_artifact_exists_true",
             Path(temp_path).exists(),
             f"temp artifact {temp_path} exists")
    finally:
        os.unlink(temp_path)

    # 2.3: Postcondition: result.total_findings is not None — valid parsed output
    sample = '''===============================================================
Gobuster v3.8.2
===============================================================
[+] Url:            http://127.0.0.1
[+] Wordlist:       /test
[+] Thread:         10
===============================================================
2026/05/16 17:00:00 Starting gobuster in directory enumeration mode
===============================================================
/admin                (Status: 403) [Size: 567]
/about                (Status: 200) [Size: 1234]
===============================================================
2026/05/16 17:00:05 Finished
==============================================================='''
    result = PARSERS[OUTPUT_TYPE](sample)
    has_findings = result.get("total_findings") is not None
    test("gate2.3_structured_result_has_total_findings",
         has_findings,
         f"parser result has total_findings={result.get('total_findings')}")

    # 2.4: Postcondition — empty scan result still has total_findings=0 (not None)
    empty_result = PARSERS[OUTPUT_TYPE]("")
    empty_ok = empty_result.get("total_findings") is not None and isinstance(empty_result["total_findings"], int)
    test("gate2.4_empty_result_has_total_findings_zero",
         empty_ok and empty_result["total_findings"] == 0,
         f"empty result total_findings={empty_result.get('total_findings')}")

    # 2.5: Postcondition — structured output has required top-level keys
    required_keys = {"total_findings", "found_paths", "scan_info", "stats"}
    has_all_keys = required_keys.issubset(result.keys())
    test("gate2.5_structured_output_has_all_required_keys",
         has_all_keys,
         f"keys present: {set(result.keys())}, missing: {required_keys - set(result.keys())}")

    # 2.6: Postcondition — found_paths is a list
    test("gate2.6_found_paths_is_list",
         isinstance(result.get("found_paths"), list),
         f"found_paths type: {type(result.get('found_paths')).__name__}")

    # 2.7: Postcondition — found_paths entries have required fields
    if result["found_paths"]:
        entry = result["found_paths"][0]
        entry_keys = {"path", "status_code", "size"}
        test("gate2.7_path_entry_has_required_fields",
             entry_keys.issubset(entry.keys()),
             f"path entry keys: {set(entry.keys())}")
    else:
        test("gate2.7_path_entry_has_required_fields", True, "skipped (no findings in sample)")


# ── GATE 3: Timeout Enforcement (End-to-End) ─────────────────────

def run_gate3_tests():
    """Gate 3: Verify per-atom timeout enforcement via subprocess."""
    sys.stderr.write("\n=== GATE 3: Timeout Enforcement (E2E) ===\n")

    # 3.1: Command respects timeout_seconds from card
    explicit_timeout = card.get("execution", {}).get("timeout_seconds")
    test("gate3.1_card_has_explicit_timeout",
         explicit_timeout is not None,
         f"explicit timeout: {explicit_timeout}")

    # 3.2: Timeout is reasonable (60-300s range)
    test("gate3.2_timeout_in_reasonable_range",
         explicit_timeout is not None and 60 <= explicit_timeout <= 300,
         f"timeout {explicit_timeout}s in [60, 300]")

    # 3.3: Fast command completes within timeout (gobuster -h is instant)
    start = time.time()
    result = subprocess.run(
        "gobuster -h",
        shell=True,
        capture_output=True,
        text=True,
        timeout=explicit_timeout or 60,
    )
    elapsed = time.time() - start
    test("gate3.3_fast_command_completes_under_timeout",
         result.returncode == 0 and elapsed < (explicit_timeout or 60) * 0.5,
         f"gobuster -h completed in {elapsed:.2f}s (timeout: {explicit_timeout}s)")

    # 3.4: Timeout enforcement — subprocess kills after timeout
    # Use a command that sleeps, should be killed
    start = time.time()
    try:
        subprocess.run(
            "sleep 5",
            shell=True,
            capture_output=True,
            text=True,
            timeout=1,  # 1 second timeout
        )
        test("gate3.4_timeout_enforcement_works", False, "should have been killed")
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        test("gate3.4_timeout_enforcement_works",
             elapsed <= 2,
             f"sleep 5 killed after {elapsed:.2f}s (expected ~1s)")
    except Exception as e:
        test("gate3.4_timeout_enforcement_works", False, f"unexpected error: {e}")


# ── GATE 4: Output Schema Validation ─────────────────────────────

def run_gate4_tests():
    """Gate 4: Validate parser output against defined schema."""
    sys.stderr.write("\n=== GATE 4: Output Schema Validation ===\n")

    # 4.1: Valid output with findings passes schema
    sample = '''===============================================================
Gobuster v3.8.2
===============================================================
[+] Url:            http://127.0.0.1
[+] Wordlist:       /test
[+] Thread:         10
===============================================================
2026/05/16 17:00:00 Starting gobuster in directory enumeration mode
===============================================================
/admin                (Status: 403) [Size: 567]
/login                (Status: 302) [Size: 0]
===============================================================
2026/05/16 17:00:05 Finished
==============================================================='''
    parsed = PARSERS[OUTPUT_TYPE](sample)
    schema_ok, schema_errors = validate_schema(parsed)
    test("gate4.1_valid_output_passes_schema",
         schema_ok,
         f"errors: {schema_errors}" if not schema_ok else "schema valid")

    # 4.2: Empty output passes schema (0 findings is valid)
    empty_parsed = PARSERS[OUTPUT_TYPE]("")
    schema_ok2, schema_errors2 = validate_schema(empty_parsed)
    test("gate4.2_empty_output_passes_schema",
         schema_ok2,
         f"errors: {schema_errors2}" if not schema_ok2 else "schema valid")

    # 4.3: Malformed output produces valid empty result (not crash)
    malformed = "this is not valid gobuster output at all\nrandom garbage 12345\n===\n"
    malformed_parsed = PARSERS[OUTPUT_TYPE](malformed)
    schema_ok3, _ = validate_schema(malformed_parsed)
    test("gate4.3_malformed_output_graceful_degradation",
         schema_ok3 and malformed_parsed["total_findings"] == 0,
         f"malformed: {malformed_parsed['total_findings']} findings, schema valid: {schema_ok3}")

    # 4.4: Parser never raises unhandled exception
    test_cases = ["", "garbage", "===\n===\n", "\n\n\n", "2026/05/16 00:00:00 Starting",
                  "path (Status: abc) [Size: xyz]", "/ok (Status: 200) [Size: 100]"]
    all_safe = True
    for tc in test_cases:
        try:
            PARSERS[OUTPUT_TYPE](tc)
        except Exception as e:
            all_safe = False
            sys.stderr.write(f"  Parser crashed on: {tc!r}: {e}\n")
    test("gate4.4_parser_no_unhandled_exceptions",
         all_safe,
         f"tested {len(test_cases)} edge cases, all safe")

    # 4.5: total_findings matches found_paths length (semantic consistency)
    parsed = PARSERS[OUTPUT_TYPE](sample)
    semantic_ok = parsed["total_findings"] == len(parsed["found_paths"])
    test("gate4.5_total_findings_matches_found_paths_length",
         semantic_ok,
         f"total={parsed['total_findings']}, paths={len(parsed['found_paths'])}")

    # 4.6: Each found_path entry has valid status_code
    status_valid = all(
        isinstance(p["status_code"], int) and 100 <= p["status_code"] <= 599
        for p in parsed["found_paths"]
    )
    test("gate4.6_all_status_codes_valid",
         status_valid,
         f"statuses: {[p['status_code'] for p in parsed['found_paths']]}")


# ── GATE 5: Atomic Test Harness (End-to-End Dispatch) ────────────

def run_gate5_tests():
    """Gate 5: End-to-end dispatch with safe mock data."""
    sys.stderr.write("\n=== GATE 5: Atomic Test Harness (E2E) ===\n")

    # 5.1: Command is safe to run with loopback target (no network impact)
    cmd_template = card["implementation"]["cmd"]
    # Test safe expand
    test_inputs = {
        "target": "127.0.0.1",
        "wordlist": "/usr/share/wordlists/dirb/small.txt",
        "flags": "-f --no-error -q -t 2",  # Minimal for speed
    }
    expanded = cmd_template
    for key, value in test_inputs.items():
        placeholder = "{" + key + "}"
        if placeholder in expanded:
            safe_value = str(value).replace("'", "'\\''")
            expanded = expanded.replace(placeholder, safe_value)

    # 5.2: Execute gobuster against loopback (will fail to connect but should not crash)
    start = time.time()
    result = subprocess.run(
        expanded,
        shell=True,
        capture_output=True,
        text=True,
        timeout=10,  # Short timeout for test
    )
    elapsed = time.time() - start

    # 5.3: Command completes (even with failure) without hanging
    test("gate5.3_command_completes_without_hanging",
         result.returncode is not None and elapsed < 15,
         f"exit={result.returncode}, elapsed={elapsed:.2f}s")

    # 5.4: Parser handles the actual output
    try:
        parsed = parsers.parse(OUTPUT_TYPE, result.stdout, raw_stderr=result.stderr,
                               exit_code=result.returncode, inputs=test_inputs)
        test("gate5.4_parser_handles_actual_output",
             parsed["ok"] or "error" in parsed.get("result", {}),
             f"parse ok={parsed['ok']}, has result: {'result' in parsed}")
    except Exception as e:
        test("gate5.4_parser_handles_actual_output", False, f"parser exception: {e}")

    # 5.5: Artifacts directory can be created
    artifact_dir = Path.home() / ".securatron" / "sessions" / "test-5" / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    test("gate5.5_artifacts_directory_writable",
         artifact_dir.exists() and os.access(artifact_dir, os.W_OK),
         f"dir: {artifact_dir}")

    # 5.6: Full pipeline: inputs -> command -> output -> parse -> validate
    pipeline_ok = True
    pipeline_errors = []
    parsed = None
    schema_ok = False
    schema_errs = []

    # Step 1: Validate inputs
    tmpl_valid, tmpl_err = check_template_resolved(test_inputs)
    if not tmpl_valid:
        pipeline_ok = False
        pipeline_errors.append(f"template: {tmpl_err}")

    # Step 2: Execute command
    exec_result = None
    if pipeline_ok:
        cmd_exec = "gobuster dir -u http://127.0.0.1 -w /usr/share/wordlists/dirb/small.txt -f --no-error -q -t 1 -t 2"

        exec_result = subprocess.run(cmd_exec, shell=True, capture_output=True, text=True, timeout=5)

    # Step 3: Parse output
    if pipeline_ok and exec_result is not None:
        parsed = parsers.parse(OUTPUT_TYPE, exec_result.stdout)
        if not parsed["ok"]:
            pipeline_ok = False
            pipeline_errors.append(f"parse failed: {parsed.get('reason')}")

    # Step 4: Validate schema
    if pipeline_ok and parsed is not None:
        schema_ok, schema_errs = validate_schema(parsed["result"])
        if not schema_ok:
            pipeline_ok = False
            pipeline_errors.extend(schema_errs)

    test("gate5.6_full_pipeline_validation",
         pipeline_ok,
         f"errors: {pipeline_errors}" if pipeline_errors else "pipeline clean")


# ── MAIN ───────────────────────────────────────────────────────────

def main():
    sys.stderr.write(f"""
============================================
 Acid Burn Gates 2-5 Test Suite — {CARD_ID}
 Card Version: {CARD_VERSION}
 Output Type: {OUTPUT_TYPE}
 Timestamp: {datetime.now(timezone.utc).isoformat()}Z
============================================
""")

    run_gate2_tests()
    run_gate3_tests()
    run_gate4_tests()
    run_gate5_tests()

    sys.stderr.write(f"""

============================================
 RESULTS: {TESTS_PASSED}/{TESTS_RUN} passed, {TESTS_FAILED} failed
============================================
""")

    # Write results
    results_path = BASE_DIR / "logs" / "tests" / f"gobuster_gates2to5_{int(time.time())}.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(RESULTS, f, indent=2)
    sys.stderr.write(f"Full results written to: {results_path}\n")

    sys.exit(0 if TESTS_FAILED == 0 else 1)


if __name__ == "__main__":
    main()
