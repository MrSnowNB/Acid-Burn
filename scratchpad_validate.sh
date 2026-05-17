#!/usr/bin/env bash
# scratchpad_validate.sh — Runs all gating tests for PROJECT_HYBRID_SCRATCHPAD.md
# Usage: bash /home/mark/Acid-Burn/scratchpad_validate.sh
# Exit code: 0 if all tests pass, 1 if any fail

set -uo pipefail

SCRATCHPAD="/home/mark/Acid-Burn/PROJECT_HYBRID_SCRATCHPAD.md"
PYTHON="/usr/bin/python3"
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0

run_test() {
    local test_id="$1"
    local description="$2"
    local command="$3"
    local expected="$4"
    local test_type="$5"  # "exit" = compare exit code, "output" = compare stdout

    local actual_exit=0
    local actual=""
    local actual_output=""

    # Run command and capture both exit code and stdout
    actual_output=$(eval "$command" 2>&1) || actual_exit=$?
    actual="$actual_output"
    # Strip trailing whitespace/newlines
    actual=$(echo "$actual" | sed 's/[[:space:]]*$//')

    local test_pass=false

    if [[ "$test_type" == "exit" ]]; then
        # Compare exit code
        if [[ "$actual_exit" == "$expected" ]]; then
            test_pass=true
        fi
    elif [[ "$test_type" == "output" ]]; then
        if [[ "$expected" == ">=2" ]]; then
            if [[ "$actual" =~ ^[0-9]+$ ]] && [[ "$actual" -ge 2 ]]; then
                test_pass=true
            fi
        elif [[ "$expected" == "PASS" ]] || [[ "$expected" == "YES" ]] || [[ "$expected" == "ALL_OK" ]]; then
            if echo "$actual" | grep -qF "$expected"; then
                test_pass=true
            fi
        else
            # Numeric output comparison
            if [[ "$actual" == "$expected" ]]; then
                test_pass=true
            fi
        fi
    fi

    TOTAL_COUNT=$((TOTAL_COUNT + 1))

    if $test_pass; then
        echo "  [PASS] $test_id: $description (expected=$expected, actual=$actual)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "  [FAIL] $test_id: $description (expected=$expected, actual=$actual)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

echo "═══════════════════════════════════════════════════════"
echo "  PROJECT HYBRID SCRATCHPAD — GATING TEST RUNNER"
echo "═══════════════════════════════════════════════════════"
echo "  Target: $SCRATCHPAD"
echo "  Time:   $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── T0.1: File exists (exit code test) ──
echo "── TEST T0.1: File existence ──"
run_test "T0.1" "PROJECT_HYBRID_SCRATCHPAD.md exists at expected path" \
    "test -f $SCRATCHPAD; exit $?" \
    "0" "exit"
echo ""

# ── T0.2: YAML parseability (output test) ──
echo "── TEST T0.2: YAML parseability ──"
cat > /tmp/scratchpad_yaml_test.py << 'PYEOF'
import sys
import re

try:
    import yaml
except ImportError:
    print("FAIL")
    sys.exit(1)

filepath = "/home/mark/Acid-Burn/PROJECT_HYBRID_SCRATCHPAD.md"
with open(filepath, 'r') as f:
    content = f.read()

# Extract YAML blocks from fenced code blocks
blocks = re.findall(r'```yaml(.*?)```', content, re.S)
parsed_count = 0
for b in blocks:
    if b.strip():
        try:
            yaml.safe_load(b)
            parsed_count += 1
        except yaml.YAMLError as e:
            print(f"FAIL: {e}")
            sys.exit(1)

if parsed_count == 0:
    print("FAIL: No YAML blocks found")
    sys.exit(1)
print(f"PASS ({parsed_count} blocks)")
sys.exit(0)
PYEOF
run_test "T0.2" "All YAML code blocks parse without error" \
    "$PYTHON /tmp/scratchpad_yaml_test.py" \
    "PASS" "output"
echo ""

# ── T0.3: Frontmatter delimiters (output test) ──
echo "── TEST T0.3: Frontmatter delimiter count ──"
run_test "T0.3" "At least 2 '---' delimiter lines present" \
    "grep -c '^---$' $SCRATCHPAD" \
    ">=2" "output"
echo ""

# ── T0.4: Validate script executable (exit test) ──
echo "── TEST T0.4: Validate script ──"
run_test "T0.4" "scratchpad_validate.sh exists and is executable" \
    "test -x /home/mark/Acid-Burn/scratchpad_validate.sh; exit $?" \
    "0" "exit"
echo ""

# ── T0.5: Snapshot script executable (exit test) ──
echo "── TEST T0.5: Snapshot script ──"
run_test "T0.5" "scratchpad_snapshot.sh exists and is executable" \
    "test -x /home/mark/Acid-Burn/scratchpad_snapshot.sh; exit $?" \
    "0" "exit"
echo ""

# ── T0.6: Snapshot directory creation (exit test) ──
echo "── TEST T0.6: Snapshot directory ──"
run_test "T0.6" "Snapshot directory can be created" \
    "bash /home/mark/Acid-Burn/scratchpad_snapshot.sh > /dev/null 2>&1; exit $?" \
    "0" "exit"
echo ""

# ── T0.7: Required sections present (output test) ──
echo "── TEST T0.7: Section headers ──"
SECTION_COUNT=0
for section in \
    "SECTION 2: FIRST PRINCIPLES" \
    "SECTION 3: PROJECT PARAMETERS" \
    "SECTION 4: PHASE LOOP" \
    "SECTION 5: APPEND-ONLY DECISION LOG" \
    "SECTION 6: ROLLBACK"; do
    if grep -q "$section" "$SCRATCHPAD" 2>/dev/null; then
        SECTION_COUNT=$((SECTION_COUNT + 1))
    fi
done
run_test "T0.7" "All 5 required section headers present in markdown" \
    "echo $SECTION_COUNT" \
    "5" "output"
echo ""

# ── T0.8: No forbidden words (output test) ──
echo "── TEST T0.8: No forbidden hedge words ──"
HEDGE_COUNT=$(grep -ciE 'approximately|should work|likely|probably' "$SCRATCHPAD" 2>/dev/null)
HEDGE_COUNT=${HEDGE_COUNT:-0}
run_test "T0.8" "No forbidden hedge words found in file content" \
    "echo $HEDGE_COUNT" \
    "0" "output"
echo ""

# ── T0.9: Absolute paths (output test) ──
echo "── TEST T0.9: Absolute paths ──"
REL_PATHS=$(grep -cE '~/' "$SCRATCHPAD" 2>/dev/null)
REL_PATHS=${REL_PATHS:-0}
run_test "T0.9" "No tilde-abbreviated paths used (must be absolute)" \
    "echo $REL_PATHS" \
    "0" "output"
echo ""

# ── T0.10: Git repo present ──
echo "── TEST T0.10: Git repository ──"
run_test "T0.10" "Git repo present at expected location" \
    "test -d /home/mark/Acid-Burn/.git; exit $?" \
    "0" "exit"
echo ""

# ── T0.11: v1.0-bootstrap tag exists ──
echo "── TEST T0.11: Git tag ──"
run_test "T0.11" "v1.0-bootstrap tag exists" \
    "cd /home/mark/Acid-Burn && git tag | grep -q v1.0-bootstrap; exit $?" \
    "0" "exit"
echo ""

# ── T0.12: No forbidden hedge words inside YAML field values (output test) ──
echo "── TEST T0.12: No hedge words inside YAML blocks ──"
HEDGE_YAML=$(grep -ciE '(should|approximately|likely|probably)' /home/mark/Acid-Burn/PROJECT_HYBRID_SCRATCHPAD.md 2>/dev/null || true)
HEDGE_YAML=${HEDGE_YAML:-0}
run_test "T0.12" "No forbidden hedge words inside YAML field values" \
    "echo $HEDGE_YAML" \
    "0" "output"
echo ""

# ── Cleanup ──
rm -f /tmp/scratchpad_yaml_test.py

# ── SUMMARY ──
echo "═══════════════════════════════════════════════════════"
echo "  SUMMARY: $PASS_COUNT passed, $FAIL_COUNT failed out of $TOTAL_COUNT tests"
echo "═══════════════════════════════════════════════════════"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo ""
    echo "  RESULT: FAILURE — $FAIL_COUNT test(s) failed."
    echo "  Do NOT proceed. Inspect the [FAIL] lines above."
    echo "═══════════════════════════════════════════════════════"
    exit 1
else
    echo ""
    echo "  RESULT: ALL TESTS PASSED."
    echo "  Bootstrap validation complete. Safe to proceed to P1."
    echo "═══════════════════════════════════════════════════════"
    exit 0
fi
