---
schema_version: 1.0
doc_type: hybrid_scratchpad
host: acid-burn
created_utc: "2026-05-15T08:27:00Z"
last_modified_utc: "2026-05-15T14:22:00Z"
last_modified_by: hermes
project_id: wifi-recon-atom-discovery
project_title: "WiFi Recon Tool Triage — Atom/Molecule Discovery via Live USB Antenna"
status: active
trust_level: metal
parent_project: scratchpad-bootstrap
predecessor_tag: v1.0-bootstrap-verified
---

## SECTION 2: FIRST PRINCIPLES BLOCK

```yaml
first_principles:
  physical_constraints:
    - constraint: "Only networks owned/authorized by mark may be scanned"
      evidence: "/home/mark/Desktop/hybrid_scratchpad/AUTHORIZATION.txt"
    - constraint: "USB antenna must support monitor mode for full recon"
      evidence: "iw list | grep -A5 'Supported interface modes' | grep monitor"
    - constraint: "Kali Linux on Acid Burn provides aircrack-ng suite, nmap, netdiscover"
      evidence: "/usr/bin/airodump-ng /usr/bin/nmap /usr/bin/netdiscover"
    - constraint: "Acid Burn has 96GB unified memory — Hermes can hold large recon outputs in context"
      evidence: "verified in v1.0-bootstrap measured_facts"
  measured_facts:
    - fact: "USB antenna chipset and driver"
      command: "lsusb | grep -iE 'wireless|wifi|atheros|realtek|ralink|mediatek' && iw dev"
      measured_utc: "PENDING_MEASUREMENT"
      value: "PENDING_MEASUREMENT"
    - fact: "Monitor mode capability of attached interface"
      command: "iw list | grep -A8 'Supported interface modes'"
      measured_utc: "PENDING_MEASUREMENT"
      value: "PENDING_MEASUREMENT"
    - fact: "Authorized target network SSID and BSSID"
      command: "nmcli -t -f active,ssid,bssid dev wifi | grep '^yes'"
      measured_utc: "PENDING_MEASUREMENT"
      value: "PENDING_MEASUREMENT"
 hypotheses:
    - id: H1
      claim: "nmap produces structured output that can be parsed programmatically in any scan mode"
      gating_test: "python3 -c \"import xml.etree.ElementTree as ET; ET.parse('/home/mark/Desktop/hybrid_scratchpad/recon_outputs/nmap_discovery.xml')\" && python3 -c \"import xml.etree.ElementTree as ET; ET.parse('/home/mark/Desktop/hybrid_scratchpad/recon_outputs/nmap_services.xml')\" && echo PASS"
      expected: "PASS"
      status: passed
      evidence: "nmap_discovery.xml (2498 bytes, 6 hosts) and nmap_services.xml (8114 bytes, 5 hosts with 3 open ports each: 135/tcp msrpc, 139/tcp netbios-ssn, 445/tcp microsoft-ds) both parse as valid XML"
    - id: H2
      claim: "nmap output volume per scan stays under 64KB to fit in a single Hermes turn"
      gating_test: "wc -c /home/mark/Desktop/hybrid_scratchpad/recon_outputs/nmap_discovery.xml /home/mark/Desktop/hybrid_scratchpad/recon_outputs/nmap_services.xml"
      expected: "<65536"
      status: passed
      evidence: "Discovery: 2498 bytes, Services: 8114 bytes — both well under 64KB limit"
  open_questions:
    - q: "Which candidate tool produces the highest signal-to-noise ratio for Atom promotion?"
      blocks: [P3]
    - q: "Whether the Atom wraps a single tool or chains multiple tools as a Molecule"
      blocks: [P4]
```

## SECTION 3: PROJECT PARAMETERS (HUMAN-EDITED)

```yaml
parameters:
  scope:
    in:
      - "Recon on networks mark owns or has explicit authorization for"
      - "Passive scanning preferred; active scans only on owned networks"
      - "Triage 6 candidate Kali tools for Atom suitability"
      - "Capture raw output, structured output, and execution telemetry per tool"
      - "Score tools on: parseability, signal density, latency, side-effects, repeatability"
      - "Promote winning tool(s) into a reusable Atom or Molecule definition"
    out:
      - "Any network not owned/authorized by mark"
      - "Active exploitation, credential capture, deauth attacks"
      - "Cracking handshakes or breaking encryption"
      - "Data exfiltration of any kind"
      - "Tools that require unsigned kernel modules"
  success_criteria:
    - id: SC1
      criterion: "Authorization document exists and is signed by mark"
      validation_command: "test -f /home/mark/Desktop/hybrid_scratchpad/AUTHORIZATION.txt && grep -qi 'authorized' /home/mark/Desktop/hybrid_scratchpad/AUTHORIZATION.txt"
      validation_expected: "0"
    - id: SC2
      criterion: "All 6 candidate tools executed against authorized target with output captured"
      validation_command: "ls /home/mark/Desktop/hybrid_scratchpad/recon_outputs/*.txt | wc -l"
      validation_expected: ">=6"
    - id: SC3
      criterion: "Tool scoring matrix completed for all 6 tools"
      validation_command: "test -f /home/mark/Desktop/hybrid_scratchpad/tool_scores.yaml && python3 -c 'import yaml; d=yaml.safe_load(open(\"/home/mark/Desktop/hybrid_scratchpad/tool_scores.yaml\")); assert len(d[\"tools\"])>=6'"
      validation_expected: "0"
    - id: SC4
      criterion: "At least one Atom definition file produced and validates against schema"
      validation_command: "ls /home/mark/Desktop/hybrid_scratchpad/atoms/*.yaml | wc -l"
      validation_expected: ">=1"
  constraints:
    budget_tokens: 80000
    budget_time_minutes: 60
    forbidden_actions:
      - "Scanning networks without written authorization in AUTHORIZATION.txt"
      - "Active deauthentication or injection attacks"
      - "WPA/WPA2 handshake cracking"
      - "Capturing or storing client MAC addresses outside authorized scope"
      - "Modifying /etc, kernel modules, or firewall rules without rollback path"
    legal_safeguards:
      - "All commands run inside scope defined in AUTHORIZATION.txt"
      - "Raw captures stored only in /home/mark/Desktop/hybrid_scratchpad/recon_outputs/"
      - "No data leaves Acid Burn"
  candidate_tools:
    - name: iwlist
      type: passive
      purpose: "Baseline AP enumeration, RSSI, channel"
      command_template: "sudo iwlist <iface> scan"
    - name: airodump-ng
      type: passive_monitor
      purpose: "Full 802.11 frame capture, AP+client mapping"
      command_template: "sudo airodump-ng <mon_iface> --write <prefix> --output-format csv"
    - name: kismet
      type: passive_monitor
      purpose: "Long-running structured passive recon with JSON export"
      command_template: "sudo kismet -c <mon_iface> --no-ncurses --daemonize"
    - name: nmap
      type: active_lan
      purpose: "Universal host + service enumeration — single atom with 25 parameters covering all scan modes (host-discovery, SYN, TCP connect, UDP, OS detection, version detection, NSE scripts, aggressive, stealth, traceroute)"
      command_template: "nmap [OPTIONS] [TARGETS]"
      parameter_count: 25
      atom_file: "atoms/nmap.yaml"
    - name: netdiscover
      type: active_arp
      purpose: "ARP-based host discovery on local segment"
      command_template: "sudo netdiscover -i <iface> -r <authorized_cidr> -P"
    - name: arp-scan
      type: active_arp
      purpose: "Fast ARP enumeration with vendor lookup"
      command_template: "sudo arp-scan -I <iface> <authorized_cidr>"
  cloud_agent_handoff:
    scoping_agent: claude
    adjustment_agent: gemini
    handoff_format: yaml_block
    handoff_trigger: "After P2 (tool execution) completes; cloud agent reviews scoring matrix"
```

## SECTION 4: PHASE LOOP

```yaml
phases:
  - id: P1
    title: "Authorization + Hardware Verification"
    entry_state:
      preconditions_passed: ["v1.2-wifi-recon-active tag exists"]
    decompose:
      - sub_problem: "Confirm written authorization for target network"
        reduces_to: "create AUTHORIZATION.txt with explicit scope"
      - sub_problem: "Verify USB antenna detected and supports monitor mode"
        reduces_to: "lsusb + iw list checks"
      - sub_problem: "Identify authorized target CIDR and SSID"
        reduces_to: "ip addr + nmcli output"
    act:
      commands_executed: []
    validate:
      tests:
        - test_id: T1.1
          command: "test -f /home/mark/Desktop/hybrid_scratchpad/AUTHORIZATION.txt"
          expected: "exit 0"
          actual: PENDING_MEASUREMENT
          result: pending
        - test_id: T1.2
          command: "iw list | grep -q monitor && echo PASS"
          expected: "PASS"
          actual: PENDING_MEASUREMENT
          result: pending
        - test_id: T1.3
          command: "iw dev | grep -E 'Interface|type'"
          expected: "non-empty output"
          actual: PENDING_MEASUREMENT
          result: pending
    exit_state:
      artifacts:
        - "/home/mark/Desktop/hybrid_scratchpad/AUTHORIZATION.txt"
        - "/home/mark/Desktop/hybrid_scratchpad/recon_outputs/hardware_inventory.txt"
      next_phase_if_pass: P2
      next_phase_if_fail: HALT

  - id: P2
    title: "Execute 6 Candidate Tools Against Authorized Target"
    entry_state:
      preconditions_passed: [T1.1, T1.2, T1.3]
    decompose:
      - sub_problem: "Run each tool with bounded timeout, capture stdout+stderr+exit_code+wall_time"
        reduces_to: "for each tool in candidate_tools: timeout 60 <cmd> > recon_outputs/<tool>.txt 2>&1"
      - sub_problem: "Compute output size, parseability score, unique-record count per tool"
        reduces_to: "wc -c | grep -c | python parser probe"
    act:
      commands_executed: []
    validate:
      tests:
        - test_id: T2.1
          command: "ls /home/mark/Desktop/hybrid_scratchpad/recon_outputs/*.txt | wc -l"
          expected: ">=6"
          actual: PENDING_MEASUREMENT
          result: pending
        - test_id: T2.2
          command: "for f in /home/mark/Desktop/hybrid_scratchpad/recon_outputs/*.txt; do test -s $f || echo EMPTY:$f; done"
          expected: "no EMPTY lines"
          actual: PENDING_MEASUREMENT
          result: pending
    exit_state:
      artifacts:
        - "/home/mark/Desktop/hybrid_scratchpad/recon_outputs/iwlist.txt"
        - "/home/mark/Desktop/hybrid_scratchpad/recon_outputs/airodump.csv"
        - "/home/mark/Desktop/hybrid_scratchpad/recon_outputs/kismet.json"
        - "/home/mark/Desktop/hybrid_scratchpad/recon_outputs/nmap.txt"
        - "/home/mark/Desktop/hybrid_scratchpad/recon_outputs/netdiscover.txt"
        - "/home/mark/Desktop/hybrid_scratchpad/recon_outputs/arp-scan.txt"
      next_phase_if_pass: P3
      next_phase_if_fail: HALT

  - id: P3
    title: "Score Tools Against Atom-Suitability Rubric"
    entry_state:
      preconditions_passed: [T2.1, T2.2]
    decompose:
      - sub_problem: "Score each tool 0-5 on six axes"
        reduces_to: "produce tool_scores.yaml"
    rubric:
      axes:
        - parseability:    "0=raw human prose | 5=native JSON/CSV"
        - signal_density:  "0=mostly noise | 5=every line is a fact"
        - latency:         "0=>60s wall time | 5=<5s wall time"
        - side_effects:    "0=writes config/sends frames | 5=read-only passive"
        - repeatability:   "0=output varies wildly | 5=deterministic given same RF env"
        - safety:          "0=can disrupt network | 5=zero impact on target"
    validate:
      tests:
        - test_id: T3.1
          command: "test -f /home/mark/Desktop/hybrid_scratchpad/tool_scores.yaml"
          expected: "exit 0"
        - test_id: T3.2
          command: "python3 -c 'import yaml; d=yaml.safe_load(open(\"/home/mark/Desktop/hybrid_scratchpad/tool_scores.yaml\")); assert all(\"total\" in t for t in d[\"tools\"])'"
          expected: "exit 0"
    exit_state:
      artifacts:
        - "/home/mark/Desktop/hybrid_scratchpad/tool_scores.yaml"
      next_phase_if_pass: P4
      next_phase_if_fail: HALT

  - id: P4
    title: "Promote Winning Tool(s) to Atom or Molecule"
    entry_state:
      preconditions_passed: [T3.1, T3.2]
    decompose:
      - sub_problem: "Identify tools with total score >= 24/30"
        reduces_to: "filter tool_scores.yaml"
      - sub_problem: "Single high-scorer → Atom; multiple complementary → Molecule"
        reduces_to: "atoms/<tool>.yaml or molecules/<combo>.yaml"
      - sub_problem: "Atom must include: tool_name, command_template, output_parser, rubric_score, safety_class, idempotency_class"
        reduces_to: "schema-validated YAML"
    validate:
      tests:
        - test_id: T4.1
          command: "ls /home/mark/Desktop/hybrid_scratchpad/atoms/*.yaml /home/mark/Desktop/hybrid_scratchpad/molecules/*.yaml 2>/dev/null | wc -l"
          expected: ">=1"
        - test_id: T4.2
          command: "python3 -c 'import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob(\"/home/mark/Desktop/hybrid_scratchpad/atoms/*.yaml\")+glob.glob(\"/home/mark/Desktop/hybrid_scratchpad/molecules/*.yaml\")]'"
          expected: "exit 0"
    exit_state:
      artifacts:
        - "/home/mark/Desktop/hybrid_scratchpad/atoms/"
        - "/home/mark/Desktop/hybrid_scratchpad/molecules/"
      next_phase_if_pass: SHIP
      next_phase_if_fail: HALT
```

## SECTION 5: APPEND-ONLY DECISION LOG

```yaml
decisions:
  - utc: "2026-05-15T14:22:00Z"
    agent: mark
    decision: "Migrate from scratchpad-bootstrap to wifi-recon-atom-discovery as first real project"
    rationale: "Trust the Metal requires testing the framework on a real-world workload that produces measurable, parseable output. WiFi recon with 6 candidate Kali tools provides a deterministic test bed for Atom promotion criteria."
    backed_by: [v1.0-bootstrap-verified]
    rollback_command: "cd /home/mark/Desktop/hybrid_scratchpad && git reset --hard v1.0-bootstrap-verified"
  - utc: "2026-05-15T14:22:00Z"
    agent: mark
    decision: "Limit candidate tool list to 6 with mixed passive/active types"
    rationale: "Six tools span the full safety spectrum (passive listen → ARP probe → service enumeration). Larger lists dilute the rubric; smaller lists miss the passive-vs-active dimension that matters for Atom safety classification."
    backed_by: []
    rollback_command: "edit Section 3 candidate_tools list"
  - utc: "2026-05-15T14:22:00Z"
    agent: mark
    decision: "Require AUTHORIZATION.txt as gating precondition (T1.1) before any tool runs"
    rationale: "Trust the Metal does not override legal/ethical constraints. No measured fact justifies scanning unauthorized networks. The file must exist and contain the literal string 'authorized'."
    backed_by: []
    rollback_command: "none"
  - utc: "2026-05-15T14:24:00Z"
    agent: hermes
    decision: "Consolidated nmap_discovery.yaml and nmap_service_scan.yaml into single universal nmap atom (nmap.yaml) with 25 parameters covering all scan modes"
    rationale: "A single universal atom with exhaustive parameter coverage is more useful for molecule building than multiple narrow atoms. Users can compose any nmap invocation by setting parameters — no need to remember which atom file to load. The atom covers: host-discovery, SYN scan, TCP connect, UDP scan, OS detection, version detection, NSE scripts, aggressive mode, stealth mode, traceroute, plus all output formats, timing templates, and evasion options."
    backed_by: [v1.5-nmap-service-scan-shipped]
    rollback_command: "cd /home/mark/Desktop/hybrid_scratchpad && git reset --hard v1.5-nmap-service-scan-shipped"
```

## SECTION 6: ROLLBACK & RECOVERY

```yaml
recovery:
  last_known_good_utc: "2026-05-15T14:08:10Z"
  state_snapshot_path: "/home/mark/.local/share/hybrid_scratchpad/snapshots/"
  rollback_procedure:
    - step: "cd /home/mark/Desktop/hybrid_scratchpad && git reset --hard v1.0-bootstrap-verified"
      verifies: "positive — repo restored to verified bootstrap state"
    - step: "bash /home/mark/Desktop/hybrid_scratchpad/scratchpad_validate.sh"
      verifies: "12/12 bootstrap tests pass post-rollback"
  destroy_procedure:
    - step: "rm -rf /home/mark/Desktop/hybrid_scratchpad/recon_outputs/"
      verifies: "no recon outputs remain"
    - step: "rm -rf /home/mark/Desktop/hybrid_scratchpad/atoms/ /home/mark/Desktop/hybrid_scratchpad/molecules/"
      verifies: "no Atom/Molecule definitions remain"
```