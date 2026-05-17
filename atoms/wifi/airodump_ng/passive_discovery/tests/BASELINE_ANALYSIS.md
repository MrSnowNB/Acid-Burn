# Baseline Data Collection — Analysis Report
## wifi.airodump_ng.passive_discovery

### Environment
- **OS:** Kali Linux 6.19.14+kali-amd64
- **Interface:** wlan1 (mt7921u, MediaTek wireless adapter)
- **Monitor interface:** wlan1mon (created via airmon-ng start wlan1)
- **External antenna:** Connected

---

### Tier Results Summary

| Tier | Duration | Band | APs Found | Clients Found |
|------|----------|------|-----------|---------------|
| basic | 20s | 2.4 GHz (bg) | 3 | 11 |
| intermediate | 60s | All (no --band flag) | 3 | 13 |

---

### Access Points Detected (All Tiers)

| BSSID | ESSID | Channel | Signal (dBm) | Encryption |
|-------|-------|---------|-------------|------------|
| B8:F8:53:97:9A:DA | RainbowUnicorn | 1 | -12 | WPA2 |
| 6A:F8:53:97:9A:DB | Unicorn_Guest | 1 | -13 | WPA2 |
| 24:41:FE:45:BA:F3 | Verizon_Z9VHJJ | 11 | -69 | WPA2 |

**Notes:**
- RainbowUnicorn and Unicorn_Guest are on the same physical router (same OUI B8:F8:53:97:9A).
- Verizon_Z9VHJJ is a neighbor's network (different OUI 24:41:FE).
- All three APs are on 2.4 GHz channels (1 or 11) — no 5 GHz networks were detected.
- No 6 GHz (Wi-Fi 6E) networks in range.
- No WEP, WPA3, or open networks detected.

---

### Client Station Analysis

**Basic tier (20s, 11 clients):**
- 9 clients associated with RainbowUnicorn
- 1 client associated with Unicorn_Guest
- 1 unassociated client (NB-ESPORTS probe request)

**Intermediate tier (60s, 13 clients):**
- 10 clients associated with RainbowUnicorn
- 1 client associated with Unicorn_Guest
- 2 unassociated clients (probe requests)

**Key observations:**
- 9 out of 13 unique clients in intermediate tier were also seen in basic tier (70% overlap).
- Signal strength of client devices ranges from -1 dBm (essentially attached to the AP itself) to -63 dBm.
- -1 dBm readings likely indicate the AP itself or devices extremely close to it.
- Packet counts scale proportionally with scan duration (as expected for passive monitoring).
- Two unassociated clients sent probe requests, indicating devices that are roaming or searching for networks.

---

### Parser Validation

The output_parser.py had two bugs that were fixed:

1. **Missing `_parse_section` function** — referenced but never defined. Added the function using `csv.DictReader`.
2. **Column name whitespace** — airodump-ng CSV headers have leading spaces (e.g., `" First time seen"`). Added header stripping in `_parse_section`.

After fixes, the parser correctly extracts all fields from real airodump-ng CSV output:
- BSSID, ESSID, channel, signal strength, encryption type
- Client MAC, associated BSSID, signal strength, packet count
- Probe request ESSIDs

---

### Comparison: Basic vs Intermediate

| Metric | Basic (20s) | Intermediate (60s) | Delta |
|--------|------------|-------------------|-------|
| APs found | 3 | 3 | 0 |
| Clients found | 11 | 13 | +2 |
| Unique client MACs | ~9 | ~11 | +2 |
| Scan duration | 20s | 60s | 3x |

**Interpretation:**
- The 20s basic tier captured ~85% of all detectable clients.
- The additional 40s of intermediate scanning found 2 new clients (likely roaming or waking up devices).
- No new APs were discovered in the extended scan — all networks are consistently on 2.4 GHz.
- For most operational purposes, a 20s basic scan provides sufficient reconnaissance.

---

### RF Environment Characteristics

- **2.4 GHz density:** Low (3 networks total)
- **5 GHz density:** Zero (no 5 GHz networks in range)
- **Encryption landscape:** 100% WPA2
- **Channel usage:** Channels 1 and 11 (both congested with APs + neighbor)
- **Interference potential:** Moderate (neighbor on channel 11, own on channel 1)

---

### Files Produced

| File | Description |
|------|-------------|
| tests/data/captures/capture-basic-YYYYMMDD-HHMMSS-01.csv | Raw airodump-ng CSV (basic tier) |
| tests/data/captures/capture-intermediate-YYYYMMDD-HHMMSS-01.csv | Raw airodump-ng CSV (intermediate tier) |
| tests/results/result-basic-YYYYMMDD-HHMMSS.json | Parsed result (basic tier) |
| tests/results/result-intermediate-YYYYMMDD-HHMMSS.json | Parsed result (intermediate tier) |

All raw capture data is gitignored. Parsed JSON results contain no sensitive RF data.
