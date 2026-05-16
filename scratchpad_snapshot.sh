#!/usr/bin/env bash
# scratchpad_snapshot.sh — Creates a timestamped backup of PROJECT_HYBRID_SCRATCHPAD.md
# Usage: bash /home/mark/Desktop/hybrid_scratchpad/scratchpad_snapshot.sh
# Creates: ~/.local/share/hybrid_scratchpad/snapshots/<ISO-8601>.md
# This script is idempotent — calling it multiple times creates separate snapshots.
# Always call this BEFORE any destructive edit to the scratchpad.

set -euo pipefail

SCRATCHPAD="/home/mark/Desktop/hybrid_scratchpad/PROJECT_HYBRID_SCRATCHPAD.md"
SNAPSHOT_DIR="/home/mark/.local/share/hybrid_scratchpad/snapshots"

# ── Pre-flight checks ──
if [[ ! -f "$SCRATCHPAD" ]]; then
    echo "ERROR: $SCRATCHPAD does not exist. Nothing to snapshot."
    exit 1
fi

# ── Create snapshot directory ──
mkdir -p "$SNAPSHOT_DIR"

# ── Generate timestamped filename ──
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
SNAPSHOT_FILE="$SNAPSHOT_DIR/${TIMESTAMP}.md"

# ── Create backup ──
cp -p "$SCRATCHPAD" "$SNAPSHOT_FILE"

# ── Verify integrity ──
ORIG_HASH=$(sha256sum "$SCRATCHPAD" | awk '{print $1}')
SNAP_HASH=$(sha256sum "$SNAPSHOT_FILE" | awk '{print $1}')

if [[ "$ORIG_HASH" != "$SNAP_HASH" ]]; then
    echo "ERROR: Snapshot integrity check failed!"
    echo "  Source:    $ORIG_HASH"
    echo "  Snapshot:  $SNAP_HASH"
    exit 1
fi

echo "SNAPSHOT OK"
echo "  Source:      $SCRATCHPAD"
echo "  Snapshot:    $SNAPSHOT_FILE"
echo "  SHA-256:     $SNAP_HASH"
echo "  Time:        $TIMESTAMP"
echo "═══════════════════════════════════════════════════════"
