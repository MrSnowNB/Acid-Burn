# Acid Burn Atoms

This directory is the home of **true Atoms** — the highest tier of capability in the Acid Burn harness.

## Definition

An Atom is a narrow, safety-class-coherent capability backed by:
- A declarative YAML contract (`*.yaml`)
- A deterministic Python toolchain (importable as `atoms.<category>.<name>`)
- Execution against real Kali Linux CLI tools (or other system binaries)

The Python toolchain is what makes Atoms different from Skills and Tools.

## Organization (Current)

- `wifi/` — 802.11 / wireless reconnaissance Atoms (airodump-ng, iwlist, kismet, ...)
- `lan/` or `nmap/` — LAN/service discovery Atoms (future home of split nmap atoms)
- `_reference/` — Design documents (orthogonality, privilege model, etc.)

## Python Native Imports

Atoms are designed to be imported directly:

```python
from atoms.wifi.airodump_ng import command_builder, output_parser
```

## Status

This structure was established during the WiFi Recon Atom Discovery sprint (May 2026).

See `wifi/README.md` for WiFi-specific details.
