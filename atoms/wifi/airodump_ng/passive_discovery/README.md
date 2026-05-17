# wifi.airodump_ng.passive_discovery

**Gold Standard Reference Atom** — Passive 802.11 discovery using airodump-ng (part of the aircrack-ng suite on Kali Linux).

This is the first fully matured Gold Standard Atom in Acid Burn. It is intended to serve as a high-quality example that both human operators and the local LLM (Qwen via Hermes) can study and emulate.

## Purpose

Perform safe, passive monitor-mode WiFi reconnaissance:
- Discover nearby Access Points and (optionally) associated clients
- No active attacks, no deauthentication, no injection
- Designed for real-world field and training use with an external monitor-mode antenna

## Structure (Reference Implementation)

```
passive_discovery/
├── passive_discovery.yaml      # Declarative contract (parameters, safety class, output schema)
├── command_builder.py          # Deterministic translation of clean inputs → airodump-ng CLI
├── output_parser.py            # Robust parser for airodump-ng CSV (supports file + raw text)
├── __init__.py
├── README.md                   # This file
├── tools/                      # LLM reference helpers
│   ├── antenna_health_check.py
│   └── README.md
└── tests/                      # Real hardware test infrastructure
    ├── run_baseline.py
    ├── README.md
    ├── data/captures/          # Raw captures (gitignored)
    └── results/                # Structured results (gitignored)
```

## Key Design Decisions

- **Narrow scope**: Strictly passive discovery (safety class = `passive_monitor`).
- **Python-native toolchain**: The Atom is not just a YAML declaration — it is backed by deterministic, importable Python code.
- **Real hardware focus**: All primary testing uses actual monitor-mode interfaces and external antennas (no synthetic data).
- **LLM-friendly**: Includes dedicated helper scripts and rich context so the local model can reason about and improve the Atom.

## Usage (via the Acid Burn harness)

The Atom is invoked through the standard `atom_loader` + `atom_runner` mechanism:

```python
from global.bin.atom_loader import load_atom
from global.bin.atom_runner import run_atom

atom = load_atom("atoms/wifi/airodump_ng/passive_discovery/passive_discovery.yaml")
result = run_atom(atom, inputs={"interface": "wlan1mon", "duration": 30, "band": "2.4"})
```

For direct development and debugging, the toolchain can also be used standalone:

```python
from command_builder import build_command
from output_parser import parse_output

cmd = build_command({"interface": "wlan1mon", "duration": 30, "band": "2.4"})
# ... run cmd with timeout + sudo ...
parsed = parse_output(csv_path="capture-xxx-01.csv")
```

## Pre-flight Recommendation (for LLM and Operators)

Before any long-running passive scan, run the health check:

```bash
python3 tools/antenna_health_check.py --interface wlan1mon
# or the more advanced version
python3 tools/monitor_interface_health.py --interface wlan1mon --pre-flight
```

These tools check:
- Whether the monitor interface actually exists and is in monitor mode
- USB power state of the external MediaTek antenna (autosuspend issues)
- Recent USB disconnect events

See `tools/HEALTH_MONITORING.md` and `tools/README.md` for details on the health monitoring philosophy and safety rules.

## Related Files

- `tests/README.md` — How to run real hardware tests
- `tools/README.md` — Philosophy and guidelines for LLM reference helpers
- `../README.md` (parent) — Overview of all WiFi Atoms

## Status

This Atom is the current reference implementation for the "Coherent Capability Unit" standard in Acid Burn. It has undergone real hardware validation, parser hardening, and robustness improvements based on actual field usage with an external antenna.

Future narrow airodump-ng Atoms (targeted_capture, etc.) should follow the same structure and quality bar.