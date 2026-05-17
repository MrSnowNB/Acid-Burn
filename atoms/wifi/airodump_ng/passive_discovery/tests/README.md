# Real-World Testing for wifi.airodump_ng.passive_discovery

This directory contains **real hardware tests** only. No simulated data is used.

## Purpose

These tests exist so the local LLM (Qwen / Hermes) and human operators can:
- Validate the Atom against real WiFi environments
- Capture real-world behavior and edge cases
- Build better future Atoms using actual data
- Perform post-run analysis

## Important Security Note

All raw capture data (`.csv`, `.cap`, etc.) is **gitignored** and must never be committed to the public Acid Burn repository. This data contains sensitive information about your local networks and devices.

The local LLM has full access to this data when running on the machine. The public repo only contains safe context and code.

## Directory Layout

```
tests/
├── data/
│   └── captures/          # Raw airodump-ng output files (gitignored)
├── results/               # Parsed output + metadata from runs (gitignored)
├── run_real_tests.py      # Main test runner for real hardware
└── README.md
```

## How to Run Real Tests

1. Ensure you have a monitor-mode interface available with the external antenna.
2. Run the test script and provide the interface:

```bash
cd atoms/wifi/airodump_ng/passive_discovery/tests
python3 run_real_tests.py --interface wlan1mon
```

You can also run specific tiers:

```bash
python3 run_real_tests.py --interface wlan1mon --tier basic
python3 run_real_tests.py --interface wlan1mon --tier intermediate
python3 run_real_tests.py --interface wlan1mon --tier edge
```

## Test Tiers (Real-World Workflows)

- **basic**: Short passive scan (typical quick recon)
- **intermediate**: Longer scan across bands with clients
- **edge**: Stress cases (long duration, poor signal, crowded environment, etc.)

## Output

- Raw captures → `data/captures/`
- Parsed results + metadata → `results/`

Results are timestamped so multiple runs can be compared over time.

## For the Local LLM

When reviewing or using this Atom, read:
- `../passive_discovery.yaml`
- `../CONTEXT.md` (when created)
- The real data in `data/captures/` and `results/`

This gives the model actual operator experience instead of synthetic examples.
