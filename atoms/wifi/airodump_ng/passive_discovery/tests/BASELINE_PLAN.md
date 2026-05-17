# Baseline Data Collection Plan — wifi.airodump_ng.passive_discovery

## Current Hardware State (Observed)

| Item | Value |
|------|-------|
| OS | Kali Linux (6.19.14+kali-amd64) |
| Interface 1 | wlan1 — managed mode, connected to "RainbowUnicorn" (5.66 GHz, ch 132, 80 MHz, -34 dBm signal) |
| Interface 2 | wlan0 — DOWN, no carrier |
| airodump-ng | Installed at /usr/sbin/airodump-ng |
| Monitor interface | **NOT YET CREATED** (must be created manually) |
| External antenna | Connected (per operator setup) |
| Sudo | Password required (no NOPASSWD) |

## Prerequisite

Before running any test, you MUST create a monitor-mode interface:

```bash
sudo airmon-ng start wlan1
# This creates wlan1mon (or similar) from wlan1
```

**Warning:** This will disconnect wlan1 from RainbowUnicorn. Reconnect after baseline is complete with `sudo airmon-ng stop wlan1mon` then reconnect manually.

## Proposed Baseline Plan

### Scope: Basic + Intermediate Tiers Only

I recommend running **basic + intermediate** tiers for the baseline. Here is the reasoning:

### Tier Selection Rationale

**BASIC (20s, 2.4 GHz only)** — INCLUDE
- 2.4 GHz is the most populated band (Wi-Fi, Bluetooth, Zigbee, microwave interference)
- Captures the largest number of APs in a residential environment
- 20 seconds is sufficient for beacon accumulation on nearby networks
- Establishes a quick snapshot of the 2.4 GHz RF environment

**INTERMEDIATE (60s, all bands abg)** — INCLUDE
- Captures both 2.4 GHz and 5 GHz networks in a single extended sweep
- 60 seconds is enough to see channel-hopping APs and roaming clients
- Client discovery is significantly better at 60s vs 20s (roaming events, probe requests)
- Allows comparison of AP density between bands

**EDGE (120s, stress test)** — SKIP FOR NOW
- 120 seconds is excessive for baseline (diminishing returns)
- Edge tier is designed for stress testing: crowded environments, weak signals, channel-congested areas
- Save for later when we need to validate long-duration behavior and parser resilience
- Baseline should be repeatable and fast for comparison across sessions

### What Good Baseline Data Looks Like

After running basic + intermediate, good baseline data should include:

1. **Access Points (expected 5-30 in a residential area):**
   - Each AP with: BSSID, ESSID, channel, signal strength (dBm), encryption type, beacon count
   - Mix of WPA2 and WPA3 encryption
   - Signal range from strong (-40 dBm, nearby) to moderate (-70 dBm, distant)
   - At least one hidden ESSID (if any)

2. **Clients (expected 0-20 depending on activity):**
   - Station MAC, associated BSSID, signal, packet count
   - Probe requests (ESIDs the client has searched for — indicates roaming/visited networks)
   - Some clients should be associated with detected APs

3. **Metadata:**
   - Timestamp, duration, interface, band, command used
   - CSV capture file path
   - Parsed JSON result file path

### Expected Learnings

- **RF environment density:** How many networks in range, what bands they occupy
- **Encryption landscape:** Percentage of WPA2 vs WPA3 vs WEP (legacy) vs OPEN
- **Client behavior:** Probe request patterns, roaming frequency
- **Signal distribution:** Signal strength spread across detected networks
- **Parser validation:** Does the output_parser correctly handle real airodump-ng CSV?
- **Timing behavior:** How much data accumulates in 20s vs 60s (comparison point)

### Exact Commands to Run

Run these in order (after creating monitor mode interface):

```bash
# Step 0: Create monitor mode interface
sudo airmon-ng start wlan1

# Step 1: Verify monitor interface (usually wlan1mon)
iw dev | grep monitor

# Step 2: Run basic tier
cd /home/mark/Acid-Burn/atoms/wifi/airodump_ng/passive_discovery/tests
python3 run_real_tests.py --interface wlan1mon --tier basic

# Step 3: Run intermediate tier
python3 run_real_tests.py --interface wlan1mon --tier intermediate

# Step 4: Analyze results
ls -la results/
cat results/result-*.json | python3 -m json.tool | head -100
```

### Post-Run Analysis

After both tiers complete:
1. Compare AP counts: basic vs intermediate (should be similar or intermediate >= basic)
2. Compare client counts: intermediate should find more clients than basic
3. Verify parser correctly extracted all fields from real CSV output
4. Check signal strength distribution
5. Identify any APs with unusual characteristics (hidden ESSIDs, WEP, etc.)
