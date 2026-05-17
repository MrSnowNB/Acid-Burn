# WiFi Atoms — Acid Burn

This directory contains true **Atoms** for wireless reconnaissance on Kali Linux.

## Design Decisions (May 2026)

- Atoms live in `atoms/` (separate from `global/tools/` and `global/skills/`)
- Every Atom has a deterministic Python toolchain (Python native imports)
- The Python layer is a **smart driver** for existing Kali CLI tools (`airodump-ng`, `iwlist`, `kismet`, etc.)
- We do **not** reimplement the wireless tools — we intelligently wrap them

## Current Structure

```
atoms/wifi/
├── airodump_ng/          # Primary high-value WiFi recon Atom
│   ├── airodump_ng.yaml
│   ├── command_builder.py
│   ├── output_parser.py
│   └── __init__.py
├── iwlist/               # Lightweight baseline
│   ├── iwlist.yaml
│   ├── command_builder.py
│   ├── output_parser.py
│   └── __init__.py
└── kismet/               # Future
```

## Philosophy

The YAML declares the **contract** (safety class, parameters, output schema, blast radius).

The Python toolchain (`command_builder` + `output_parser`) provides the **deterministic implementation** that actually drives the Kali binary safely and parses its output into the declared schema.

This is what makes something an **Atom** instead of a Skill or Tool card.

## Next Steps (WiFi Recon Sprint)

1. Complete `airodump_ng` toolchain (especially robust CSV parsing + runner that handles timeout + sudo)
2. Implement `kismet` Atom
3. Create narrow nmap Atoms under `atoms/lan/` or `atoms/nmap/`
4. Wire these Atoms into dispatch so they can be invoked cleanly without special cases
5. Score them using the worst-case rubric and promote through the gates

## Import Example

```python
from atoms.wifi.airodump_ng.command_builder import build_command
from atoms.wifi.airodump_ng.output_parser import parse_csv_output

cmd = build_command({"interface": "wlan1mon", "channel": 6, "duration": 60})
result = parse_csv_output("/tmp/airodump-01.csv")
```
