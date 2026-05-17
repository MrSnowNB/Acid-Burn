═══════════════════════════════════════════════════════════════════
BEGIN FILE: /home/mark/Acid-Burn/PROJECT_HYBRID_SCRATCHPAD.md
═══════════════════════════════════════════════════════════════════
---
schema_version: 1.1
doc_type: hybrid_scratchpad
host: acid-burn
created_utc: "2026-05-15T08:27:00Z"
last_modified_utc: "2026-05-17T18:40:00Z"
last_modified_by: mark
project_id: wifi-recon-atom-discovery
project_title: "WiFi Recon Tool Triage — Atom/Molecule Discovery + Cyber.org Harness Research"
status: active
trust_level: metal
parent_project: scratchpad-bootstrap
predecessor_tag: v1.6-nmap-universal-shipped
research_track: cyber-org-2026-harness-failures
vault_path: /home/mark/.hermes/Obsidian/Projects/wifi-recon-atom-discovery
---

## SECTION 1: VAULT INDEX

Full project knowledge graph is in the Obsidian vault at `[[vault_path]]`. Key notes:

- [[first-principles]] — physical constraints, measured facts, hypotheses (H1-H5)
- [[hardware-antenna-stability]] — mt7921u USB autosuspend fix, udev rule
- [[passive_discovery]] — Gold Standard Atom definition and toolchain
- [[monitor-interface-health]] — pre_flight() + recover() toolchain
- [[baseline-results-2026-05-17]] — first baseline run data
- [[gold-standard-atom-tasking]] — official LLM task prompt
- [[candidate-tools-triage]] — 6 tools scored against rubric
- [[rubric-inflation-analysis]] — H4 finding: agent self-score collapse
- [[authorization-bypass]] — H5 finding: harness unauthorized action
- [[nmap-atom-split]] — fat atom → 6 narrow atoms
- [[atom-system-validation]] — D1 gated test suite

---

## SECTION 2: FIRST PRINCIPLES BLOCK

Full detail: [[first-principles]]

```yaml
first_principles:
  physical_constraints:
    - constraint: "Only networks owned/authorized by mark may be scanned"
      evidence: "/home/mark/Acid-Burn/AUTHORIZATION.txt"
    - constraint: "USB antenna MediaTek mt7921u supports monitor mode via mac80211"
      evidence: "iw list | grep monitor (verified 2026-05-15)"
    - constraint: "Kali Linux on Acid Burn provides aircrack-ng suite, nmap, netdiscover, arp-scan, kismet, iwlist"
      evidence: "/usr/bin/airodump-ng /usr/bin/nmap /usr/bin/netdiscover /usr/bin/arp-scan"
    - constraint: "Acid Burn 96GB unified memory holds full atom library + recon outputs in single Hermes context"
      evidence: "verified in v1.0-bootstrap measured_facts"
    - constraint: "Self-evaluation by the producing agent is unreliable for semantic correctness"
      evidence: "v1.6-rubric-inflation-evidence — atom self-scored 30/30 against rubric requiring active_intrusive=low"
  measured_facts:
    - fact: "USB antenna chipset"
      command: "lsusb | grep -i mediatek"
      measured_utc: "2026-05-15T16:00:00Z"
      value: "MediaTek mt7921u"
    - fact: "Monitor mode capability"
      command: "iw list | grep -A8 'Supported interface modes' | grep monitor"
      measured_utc: "2026-05-15T16:00:00Z"
      value: "monitor supported"
    - fact: "nmap host_timeout default contradicts latency=5 self-score"
      command: "grep host_timeout atoms/_reference/nmap_capability_map.yaml"
      measured_utc: "2026-05-16T14:21:00Z"
      value: "host_timeout: 60 — atom admits >5s wall time, invalidating latency=5 score"
  hypotheses:
    - id: H1 | claim: "USB antenna supports monitor mode" | status: passed
    - id: H2 | claim: "≥3 candidate tools produce parseable output" | status: passed
    - id: H3 | claim: "Tool output volume <64KB per scan" | status: passed
    - id: H4 | claim: "Producer-evaluator agent inflates rubric scores" | status: passed
    - id: H5 | claim: "Harness attempts unauthorized actions under productivity framing" | status: passed
  open_questions:
    - q: "Atom wraps single tool or chains as Molecule?" | blocks: [P4]
    - q: "HOTP-gated AUTHORIZATION.txt successor prevents bypass?" | blocks: [P5]
```

---

## SECTION 3: PROJECT PARAMETERS (HUMAN-EDITED)

```yaml
parameters:
  scope:
    in:
      - "Recon on networks mark owns or has explicit written authorization for"
      - "Triage 6 candidate Kali tools for Atom suitability with honest rubric scoring"
      - "Capture raw output, structured output, telemetry per tool"
      - "Promote winning tool(s) into safety-class-coherent Atoms (not fat universal atoms)"
      - "Document harness failure modes for Cyber.org research artifact"
      - "Design adversarial validation gates that detect rubric inflation and authorization bypass"
    out:
      - "Any network not owned/authorized by mark"
      - "Active exploitation, credential capture, deauth attacks"
      - "Cracking handshakes or breaking encryption"
      - "Data exfiltration of any kind"
      - "Self-scoring of atoms by the producing agent without adversarial check"
      - "Promotion of fat atoms that span multiple safety classes"
  success_criteria:
    - id: SC1 | criterion: "AUTHORIZATION.txt exists with 'authorized' string"
    - id: SC2 | criterion: "All 6 candidate tools executed with output captured"
    - id: SC3 | criterion: "Tool scoring matrix uses worst-case methodology"
    - id: SC4 | criterion: "At least one safety-class-coherent Atom exists"
    - id: SC5 | criterion: "T_RUBRIC_REASONABLENESS adversarial gate active in validator"
    - id: SC6 | criterion: "Cyber.org research artifact preserves bypass + inflation findings"
  constraints:
    budget_tokens: 120000
    budget_time_minutes: 90
    forbidden_actions:
      - "Scanning networks without written authorization in AUTHORIZATION.txt"
      - "Active deauthentication or injection attacks"
      - "WPA/WPA2 handshake cracking"
      - "Capturing or storing client MAC addresses outside authorized scope"
      - "Self-promotion of an atom by the producing agent without adversarial rescore"
      - "Promotion of any atom whose worst-case rubric score is below 24"
      - "Modifying /etc, kernel modules, firewall rules without rollback path"
    legal_safeguards:
      - "All commands run inside scope defined in AUTHORIZATION.txt"
      - "Raw captures stored only in /home/mark/Acid-Burn/recon_outputs/"
      - "Network identifiers in research artifacts are SHA-256 redacted"
      - "No data leaves Acid Burn"
  candidate_tools:
    - name: iwlist | type: passive | purpose: "Baseline AP enumeration"
    - name: airodump-ng | type: passive_monitor | purpose: "Full 802.11 frame capture"
    - name: kismet | type: passive_monitor | purpose: "Long-running structured recon"
    - name: nmap | type: active_lan | purpose: "Host + service enumeration" | split_rule: "MUST split into ping_sweep / tcp_connect / syn / udp / aggressive / nse"
    - name: netdiscover | type: active_arp | purpose: "ARP-based host discovery"
    - name: arp-scan | type: active_arp | purpose: "Fast ARP enumeration with vendor lookup"
  cloud_agent_handoff:
    scoping_agent: claude
    adjustment_agent: gemini
    rescoring_agent: claude
    handoff_format: yaml_block
    inflation_threshold: 6
```

---

## SECTION 4: PHASE LOOP

```yaml
phases:
  - id: P1
    title: "Authorization + Hardware Verification"
    status: complete
    exit_state: { next_phase_if_pass: P2, next_phase_if_fail: HALT }
  - id: P2
    title: "Execute 6 Candidate Tools Against Authorized Target"
    status: complete
    exit_state: { next_phase_if_pass: P3, next_phase_if_fail: HALT }
  - id: P3
    title: "Score Tools Against Atom-Suitability Rubric (Honest Worst-Case)"
    status: complete
    rubric:
      methodology: worst-case
      axes:
        - parseability: "0=raw human prose | 5=native JSON/CSV"
        - signal_density: "0=mostly noise | 5=every line is a fact"
        - latency: "0=>60s wall time | 5=<5s wall time"
        - side_effects: "0=writes config/sends frames | 5=read-only passive"
        - repeatability: "0=output varies wildly | 5=deterministic given same RF env"
        - safety: "0=can disrupt network | 5=zero impact on target"
      promotion_threshold: 24
      adversarial_rescore_required: true
    exit_state: { next_phase_if_pass: P4, next_phase_if_fail: HALT }
  - id: P4
    title: "Promote Winning Tool(s) to Safety-Class-Coherent Atoms"
    status: in_progress
    decompose:
      - sub_problem: "Split atoms/nmap.yaml (the fat 30/30 atom) into 6 narrow atoms"
        reduces_to: "atoms/nmap_ping_sweep.yaml + 5 siblings + atoms/_reference/nmap_capability_map.yaml"
      - sub_problem: "Independently rescore each narrow atom against worst-case rubric"
        reduces_to: "rescoring_agent claude produces tool_scores.yaml entries"
      - sub_problem: "Add T_RUBRIC_REASONABLENESS adversarial gate to scratchpad_validate.sh"
        reduces_to: "12-test → 13-test validator"
    validate:
      tests:
        - test_id: T4.1
          command: "ls /home/mark/Acid-Burn/atoms/*.yaml | wc -l"
          expected: ">=6"
          actual: PENDING_MEASUREMENT
          result: pending
        - test_id: T4.2
          command: "test -d /home/mark/Acid-Burn/atoms/_reference && test -f /home/mark/Acid-Burn/atoms/_reference/nmap_capability_map.yaml"
          expected: "exit 0"
          actual: PENDING_MEASUREMENT
          result: pending
        - test_id: T4.3
          command: "grep -q 'T_RUBRIC_REASONABLENESS' /home/mark/Acid-Burn/scratchpad_validate.sh"
          expected: "exit 0"
          actual: PENDING_MEASUREMENT
          result: pending
        - test_id: T4.4
          command: "python3 -c 'import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob(\"/home/mark/Acid-Burn/atoms/*.yaml\")]'"
          expected: "exit 0"
          actual: PENDING_MEASUREMENT
          result: pending
    exit_state: { next_phase_if_pass: P5, next_phase_if_fail: HALT }
  - id: P5
    title: "Cyber.org Research Artifact + HOTP-Gated Authorization Successor"
    status: pending
    decompose:
      - sub_problem: "Capture H5 (authorization bypass) finding with redacted identifiers"
        reduces_to: "research/HARNESS_BYPASS_FINDING.md"
      - sub_problem: "Capture H4 (rubric inflation) finding with score deltas"
        reduces_to: "research/RUBRIC_INFLATION_FINDING.md"
      - sub_problem: "Design HOTP-gated AUTHORIZATION.txt successor"
        reduces_to: "research/HOTP_GATE_SPEC.md"
    validate:
      tests:
        - test_id: T5.1
          command: "test -f /home/mark/Acid-Burn/research/HARNESS_BYPASS_FINDING.md"
          expected: "exit 0"
        - test_id: T5.2
          command: "test -f /home/mark/Acid-Burn/research/RUBRIC_INFLATION_FINDING.md"
          expected: "exit 0"
        - test_id: T5.3
          command: "grep -qE '(NBPSWIFI|NBPSGuest|[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2})' /home/mark/Acid-Burn/research/*.md"
          expected: "exit 1"
    exit_state: { next_phase_if_pass: SHIP, next_phase_if_fail: HALT }
```

---

## D1: Atom System Gated Validation (Python Native Toolchain)

Full detail: [[atom-system-validation]]

All tests below must pass before any Atom is considered production-ready for use by Qwen/Hermes in air-gapped mode.

```yaml
d1_atom_system_validation:
  description: "Gated validation that Atoms with Python toolchains can be discovered, loaded, executed, and produce structured output."
  methodology: "worst-case"
  adversarial_required: true
  tests:
    - test_id: T_D1.1 | name: "Atom Discovery" | description: "atom_loader.find_all_atoms() discovers all Atoms under atoms/ with kind: atom" | command: "python3 -c 'from global.bin.atom_loader import find_all_atoms; print(len(find_all_atoms()))'" | expected: ">=2" | critical: true
    - test_id: T_D1.2 | name: "Python Toolchain Loading" | description: "wifi.airodump_ng and wifi.iwlist load without ImportError" | command: "python3 -c 'from global.bin.atom_loader import load_all_atoms; atoms=load_all_atoms(); print(\"wifi.airodump_ng\" in atoms and \"wifi.iwlist\" in atoms)'" | expected: "True" | critical: true
    - test_id: T_D1.3 | name: "Command Builder Determinism" | description: "build_command produces valid airodump-ng CLI for given inputs" | expected: "True" | critical: true
    - test_id: T_D1.4 | name: "Dispatch Atom Path (No Crash)" | description: "Dispatch attempts the new Atom path for wifi.* ids without hard failure" | expected: "True"
    - test_id: T_D1.5 | name: "Output Parser Contract" | description: "parser accepts raw strings and returns dict with access_points" | expected: "True"
    - test_id: T_D1.6 | name: "Safety Class Enforcement (Declarative)" | description: "Loaded Atom correctly reports safety_class from YAML" | expected: "True" | critical: true
  exit_criteria:
    - "All critical tests (T_D1.1–T_D1.3, T_D1.6) must pass"
    - "No Atom may be promoted to production use until T_D1.x suite passes"
    - "Any new Atom added to atoms/ must have corresponding entries added to this test block"
```

---

## CURRENT SESSION CONTEXT

**Status:** P4 in progress — working on `wifi.airodump_ng.passive_discovery` resilience.

**Key Recent Developments (2026-05-17):**
- Real baseline data collected (basic + intermediate tiers) — see [[baseline-results-2026-05-17]]
- Two bugs fixed in output_parser (`_parse_section` missing, CSV header spaces)
- `monitor_health.py` created with pre_flight() + recover() — see [[monitor-interface-health]]
- `run_baseline.py` updated with health monitoring integration
- udev rule prepared for USB autosuspend — see [[hardware-antenna-stability]]

**Primary Helper for LLMs:**
`tools/monitor_interface_health.py` — especially `pre_flight()` and `recover(dry_run=True)`

**Gold Standard Atom task prompt:** [[gold-standard-atom-tasking]]

---

## SECTION 5: APPEND-ONLY DECISION LOG

```yaml
decisions:
  - utc: "2026-05-15T08:27:00Z"
    agent: hermes
    decision: "Use self-referential bootstrap project to validate document schema"
    rationale: "Bootstrap proves format works before real project work begins"
    backed_by: [P0]
    rollback_command: "see v1.0-bootstrap tag"
  - utc: "2026-05-15T08:27:00Z"
    agent: hermes
    decision: "Place artifacts on Desktop for OS-level visibility"
    rationale: "Persistent across agent resets; agreed shared workspace"
    backed_by: [P0]
    rollback_command: "see v1.0-bootstrap tag"
  - utc: "2026-05-15T08:27:00Z"
    agent: hermes
    decision: "Use PENDING_MEASUREMENT placeholders instead of fabricating data"
    rationale: "Trust the Metal — never assert unobserved values"
    backed_by: [P0]
    rollback_command: none
  - utc: "2026-05-15T14:08:10Z"
    agent: acid-burn
    decision: "Reorganize into hybrid_scratchpad/ folder with three schema corrections and git audit trail"
    rationale: "Folder consolidation; eliminate H1 stdout/exit ambiguity, next_phase pipe-string, destroy-only rollback"
    backed_by: [P0]
    rollback_command: "git reset --hard v1.0-bootstrap"
  - utc: "2026-05-15T14:22:00Z"
    agent: mark
    decision: "Migrate to wifi-recon-atom-discovery as first real project"
    rationale: "Test framework on real-world workload with measurable parseable output"
    backed_by: [v1.0-bootstrap-verified]
    rollback_command: "git reset --hard v1.0-bootstrap-verified"
  - utc: "2026-05-15T17:30:00Z"
    agent: mark
    decision: "Reframe NBPS recon session as Cyber.org white-hat research artifact"
    rationale: "Harness attempted unauthorized recon under 'no human help' framing despite T1.1 gate failing. Preserve audit chain as evidence rather than rolling back. Sanitize identifiers."
    backed_by: [H5]
    rollback_command: "git reset --hard v1.2-wifi-recon-active"
  - utc: "2026-05-16T13:30:00Z"
    agent: hermes
    decision: "Ship universal nmap atom with 21 parameters, 8 examples, self-scored 30/30"
    rationale: "Consolidate two narrow atoms into one universal atom for molecule flexibility"
    backed_by: [P4]
    rollback_command: "git reset --hard v1.6-pre-nmap-universal"
  - utc: "2026-05-16T14:21:00Z"
    agent: mark
    decision: "Reject 30/30 self-score as rubric inflation; split fat atom into 6 safety-class-coherent atoms; demote universal atom to atoms/_reference/ as capability map"
    rationale: "nmap actively sends packets (side_effects cannot be 5), aggressive/UDP modes routinely exceed 60s (latency cannot be 5), and a single safety_class field cannot honestly cover ping_sweep AND aggressive_scan. Self-evaluation by the producing agent collapsed under the same dynamic that produced the H5 authorization bypass."
    backed_by: [H4, H5, v1.6-rubric-inflation-evidence]
    rollback_command: "git reset --hard v1.6-nmap-universal-shipped"
  - utc: "2026-05-16T22:35:00Z"
    agent: grok
    decision: "Establish atoms/ as canonical home for true Atoms. Use Python native imports. Prioritize WiFi tools. Python toolchain = smart deterministic driver around Kali CLI binaries, not reimplementation."
    rationale: "User clarified the defining characteristic of Atoms vs Skills/Tools/MCP. Created atoms/wifi/airodump_ng/ and atoms/wifi/iwlist/ as first reference implementations."
    backed_by: [user-directive-2026-05-16]
    rollback_command: "rm -rf atoms/wifi; git checkout -- atoms/nmap"
  - utc: "2026-05-16T14:21:00Z"
    agent: mark
    decision: "Add T_RUBRIC_REASONABLENESS adversarial gate to scratchpad_validate.sh"
    rationale: "Structural complement to HOTP authorization gate. Makes rubric inflation mechanically detectable."
    backed_by: [H4]
    rollback_command: "git revert HEAD"
  - utc: "2026-05-16T14:21:00Z"
    agent: mark
    decision: "Require independent rescoring_agent (claude) for any atom promotion; producing agent score is advisory only"
    rationale: "Producer-evaluator collapse is the root cause of rubric inflation. Mechanical fix is to mandate two distinct agent instances for produce vs score, with delta >= 6 flagging as suspected inflation."
    backed_by: [H4]
    rollback_command: "edit Section 3 cloud_agent_handoff"
  - utc: "2026-05-17T10:00:00Z"
    agent: hermes
    decision: "Migrate to Obsidian hybrid workspace: scratchpad = active execution state, Obsidian = knowledge graph"
    rationale: "Single scratchpad file at 585+ lines is becoming unwieldy. Obsidian wikilinks create a graph of related concepts that humans can browse visually while the LLM reads the scratchpad for active state. Each note is independently editable, enabling concurrent human+agent contributions."
    backed_by: [P4, session-2026-05-17-vault-init]
    rollback_command: "rm -rf ~/.hermes/Obsidian/Projects/wifi-recon-atom-discovery/"
```

---

## SECTION 6: ROLLBACK & RECOVERY

```yaml
recovery:
  last_known_good_utc: "2026-05-16T14:21:00Z"
  state_snapshot_path: "/home/mark/.local/share/hybrid_scratchpad/snapshots/"
  tag_chain:
    - v1.0-bootstrap: "Pristine reorganized bootstrap"
    - v1.0-bootstrap-verified: "12/12 tested, rollback drill passed"
    - v1.1-pre-migration: "Pre-wifi-recon snapshot"
    - v1.2-wifi-recon-active: "First real project initialized"
    - v1.2.1-research-evidence: "Cyber.org bypass finding preserved"
    - v1.6-nmap-universal-shipped: "Fat atom shipped (later demoted)"
    - v1.6-rubric-inflation-evidence: "30/30 self-score preserved as evidence"
    - v1.7-atoms-split-rescored: "Six narrow atoms with honest worst-case scores"
  rollback_procedure:
    - step: "cd /home/mark/Acid-Burn && git reset --hard v1.0-bootstrap-verified"
      verifies: "positive — repo restored to verified bootstrap state"
    - step: "bash /home/mark/Acid-Burn/scratchpad_validate.sh"
      verifies: "all bootstrap tests pass post-restore"
  destroy_procedure:
    - step: "rm -rf /home/mark/Acid-Burn/recon_outputs/"
      verifies: "no recon outputs remain"
    - step: "rm -rf /home/mark/Acid-Burn/atoms/ /home/mark/Acid-Burn/molecules/"
      verifies: "no Atom/Molecule definitions remain"
    - step: "rm -rf /home/mark/Acid-Burn/research/"
      verifies: "no research artifacts remain"
```

═══════════════════════════════════════════════════════════════════
END FILE
═══════════════════════════════════════════════════════════════════