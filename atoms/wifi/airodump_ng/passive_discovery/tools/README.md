# Tools & Helpers (LLM Reference Material)

This directory contains small, focused helper scripts intended primarily as **reference and training material** for the local LLM (Qwen via Hermes).

## Philosophy

These scripts exist so that the reasoning engine can study real, working patterns for:

- Detecting hardware state (monitor interfaces, USB devices, power management)
- Pre-flight health checks before long-running operations
- Graceful error handling and recovery strategies
- Producing structured, machine-readable output (JSON) when possible

The goal is to help the LLM internalize good practices for writing robust wireless and security tooling, rather than having to guess or hallucinate solutions.

## Current Helpers

### `antenna_health_check.py`

**Purpose:** Lightweight pre-flight and diagnostic tool for the external monitor-mode WiFi antenna (MediaTek mt7921u).

It answers the most common questions the LLM needs before starting a capture.

**Usage:**

```bash
python3 tools/antenna_health_check.py --interface wlan1mon
python3 tools/antenna_health_check.py --interface wlan1mon --json
```

### `monitor_interface_health.py`

**Purpose:** More advanced health monitoring and recovery assistant.

This is the primary tool for robustness around the known external antenna stability problem (USB autosuspend causing monitor interfaces to disappear).

Key capabilities:
- `check(interface)` — single health snapshot
- `pre_flight(interface)` — strict validation before starting a capture
- `recover(interface, dry_run=True)` — reports exact recovery commands (never executes destructive actions by default)
- `periodic_check(...)` — for long-running captures

**Critical Safety Rule (for LLMs):**
The `recover()` method **defaults to `dry_run=True`**. It will not execute any commands that change interface state unless explicitly told otherwise **and** after human approval. All suggested recovery commands are returned in the `commands_to_run` list for the operator to review.

**Usage examples:**

```bash
# Quick health check
python3 tools/monitor_interface_health.py --interface wlan1mon

# Pre-flight before starting a long scan
python3 tools/monitor_interface_health.py --interface wlan1mon --pre-flight

# Get recovery commands (safe, does not execute)
python3 tools/monitor_interface_health.py --interface wlan1mon --recover
```

This module is the current recommended pattern for handling unreliable USB WiFi hardware in Acid Burn.

## Guidelines for Future Helpers

When adding new tools to this directory, follow these principles:

1. **Single Responsibility** — Each script should answer one clear class of question the LLM needs.
2. **LLM-Friendly** — Include excellent docstrings and comments. The LLM will read these files as training material.
3. **Structured Output** — Prefer `--json` mode when the primary consumer is the model.
4. **Real Hardware Focus** — These tools are meant to be run against actual systems, not simulations.
5. **Self-Contained** — Minimize external dependencies so the LLM can easily understand and adapt the code.

## Relationship to the Atom

These helpers are **supporting infrastructure** for the `wifi.airodump_ng.passive_discovery` Gold Standard Atom. They are not part of the core `command_builder` / `output_parser` contract, but they are essential for reliable real-world operation and for teaching the LLM how to build dependable tools.