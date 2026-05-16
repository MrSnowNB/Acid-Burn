#!/usr/bin/env python3
"""
Gate 4: Schema Validation — Gobuster parser output validator.

Validates that the gobuster parser produces structurally-correct output
with all required fields, proper types, and semantic correctness.

Usage: python3 validate_gobuster_schema.py
"""

import json
import sys

REQUIRED_FIELDS = {
    "total_findings": ["int"],
    "found_paths": ["list"],
    "scan_info": ["dict"],
    "stats": ["dict"],
}

VALID_STATUS_CODES = {
    200, 201, 204, 301, 302, 307, 401, 403, 405, 429, 500
}


def validate_schema(data):
    """Validate gobuster parser output schema. Returns (ok, errors)."""
    errors = []

    # Check required fields
    for field, expected_types in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"MISSING field: {field}")
            continue

        value = data[field]
        valid_type = False
        for expected in expected_types:
            if expected == "int" and isinstance(value, int):
                valid_type = True
            elif expected == "list" and isinstance(value, list):
                valid_type = True
            elif expected == "dict" and isinstance(value, dict):
                valid_type = True
            elif expected == "str" and isinstance(value, str):
                valid_type = True
        if not valid_type:
            errors.append(f"WRONG TYPE: {field} expected {expected_types}, got {type(value).__name__}")

    # Semantic validation: total_findings must match found_paths length
    if "total_findings" in data and "found_paths" in data:
        if data["total_findings"] != len(data["found_paths"]):
            errors.append(
                f"SEMANTIC ERROR: total_findings={data['total_findings']} "
                f"but found_paths has {len(data['found_paths'])} entries"
            )

    # Validate found_paths entries
    if "found_paths" in data and isinstance(data["found_paths"], list):
        for i, path_entry in enumerate(data["found_paths"]):
            if not isinstance(path_entry, dict):
                errors.append(f"found_paths[{i}] is not a dict: {type(path_entry).__name__}")
                continue
            for pf in ["path", "status_code", "size"]:
                if pf not in path_entry:
                    errors.append(f"found_paths[{i}] missing field: {pf}")
            if "status_code" in path_entry:
                try:
                    code = int(path_entry["status_code"])
                    if code not in VALID_STATUS_CODES:
                        errors.append(f"found_paths[{i}] unexpected status_code: {code}")
                except (ValueError, TypeError):
                    errors.append(f"found_paths[{i}] status_code not numeric: {path_entry['status_code']}")

    # Validate scan_info
    if "scan_info" in data and isinstance(data["scan_info"], dict):
        for sf in ["target", "wordlist", "concurrency", "start_time"]:
            if sf not in data["scan_info"]:
                errors.append(f"scan_info missing field: {sf}")

    # Validate stats
    if "stats" in data and isinstance(data["stats"], dict):
        for sf in ["elapsed_seconds", "requests_sent"]:
            if sf not in data["stats"]:
                errors.append(f"stats missing field: {sf}")

    # Edge case: empty result (no findings) is valid — but must have 0 total_findings
    if data.get("total_findings", None) is not None and data["total_findings"] == 0:
        if len(data.get("found_paths", [])) != 0:
            errors.append("total_findings=0 but found_paths is non-empty")

    return len(errors) == 0, errors


def main():
    # Read parser output from stdin (JSON)
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "valid": False,
            "errors": [f"Invalid JSON: {str(e)}"],
            "schema_version": "1.1"
        }))
        sys.exit(1)

    ok, errors = validate_schema(data)

    result = {
        "valid": ok,
        "errors": errors,
        "schema_version": "1.1",
    }

    print(json.dumps(result, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
