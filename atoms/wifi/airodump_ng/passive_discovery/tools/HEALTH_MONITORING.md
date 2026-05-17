# Health Monitoring & Recovery for WiFi Atoms

## Purpose

This document defines the philosophy and safety boundaries for health monitoring tools used with Gold Standard WiFi Atoms (starting with `wifi.airodump_ng.passive_discovery`).

## Core Principle

Hardware used for monitor mode on consumer USB WiFi adapters (especially the MediaTek mt7921u) is **unreliable** under sustained load. The system must be able to detect when the monitor interface or the USB device itself disappears and respond intelligently.

However, **automatic recovery is dangerous**.

## Safety Rules for All Health & Recovery Code

1. **Detection is always safe.** Reporting that something is wrong is encouraged.
2. **Recovery is high-risk.** Any code that brings interfaces down, creates monitor interfaces, resets USB devices, or writes to `/sys/bus/usb/.../power/control` must:
   - Default to `dry_run=True`
   - Never execute without explicit human confirmation in the current session
   - Clearly list every command it would run
   - Log the decision and outcome

3. **The LLM must never run recovery autonomously** unless the operator has explicitly enabled "auto-recovery" mode for a specific, trusted environment (not recommended for the first Gold Standard Atom).

## Current Implementation

- `antenna_health_check.py` — Lightweight, safe, recommended for most pre-flight checks.
- `monitor_interface_health.py` — More comprehensive. Contains the `recover()` method, which is intentionally conservative in its current form.

## Recommended Pattern for LLMs

When working with any WiFi Atom that requires a monitor interface:

```python
health = MonitorHealth()
status = health.pre_flight("wlan1mon")

if not status["healthy"]:
    print("Health check failed:", status["reason"])
    recovery = health.recover("wlan1mon")   # dry_run=True by default
    print("Suggested recovery commands:")
    for cmd in recovery.get("commands_to_run", []):
        print("  ", cmd)
    # Do NOT proceed with capture until operator approves
else:
    # Safe to start capture
    ...
```

## Future Evolution

As more Gold Standard Atoms are completed (targeted_capture, kismet, etc.), this health monitoring approach should be generalized into a shared `tools/wifi/` module rather than duplicated per Atom.

---

**Status:** Draft — 2026-05-17
**Owner:** Acid Burn Gold Standard Process
**Review:** After the passive_discovery Atom passes its full agent red team.