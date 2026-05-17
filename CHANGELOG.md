# Changelog: Acid Burn - White Hat Multi-Tool

All notable changes to the Acid Burn toolkit and the security auditing pipeline are documented here.

## [v2.2.0] - 2026-05-17 - "The Cyberpunk Expansion & Hardening"

### Core & Rebranding
- **Migration:** 100% complete nomenclature migration from SecuraTron to **Acid Burn**. All 66+ files updated.
- **Root:** System root migrated from `~/.securatron` to `~/.acid-burn`.
- **Identity:** Renamed core binaries to `acid-burn` and `acid_burn.py`.
- **Repository:** Official synchronization with `https://github.com/MrSnowNB/Acid-Burn`.

### Hardening & Field Readiness
- **Biometrics:** Integrated biometric (fingerprint) authorization into the system authentication pipeline (PAM/fprintd).
- **Vectors:** Verified PolicyKit as a reliable high-speed authorization vector (`pkexec`).
- **Doctrine:** Added `global/doctrine/biometrics.md` documenting hardware bypass blueprints for field readiness.
- **Swarm Repair:** Fixed the "Blank Check Bug" (P-1) by blocking empty DAG plans in the inbox watcher.
- **Crypto-Integrity:** Fixed session ID predictability (P-3) using a cryptographic generator (`sha256(urandom + timestamp)`).
- **Wireless Atom:** Implemented the "Gold Standard" `wifi.airodump_ng.passive_discovery` atom with a specialized Python toolchain.
- **Generalized Dispatch:** Refactored engine to support `kali_cli` implementation kind, enabling first-class Python toolchains for all security tools.
- **Payloads:** Initialized `global/payloads/field_readiness_suite.yaml` with verified, IDS-safe scan configurations.
- **Sudoers:** Configured specialized `sudoers.d/airodump-ng` rules for autonomous, passwordless execution of airodump, airmon, and nmap.

### Environment & Tools
- **Added:** Official **Visual Studio Code** installation via Microsoft repository.
- **Added:** **Google Antigravity** AI-powered IDE installation for agentic workflows.
- **Added:** Official **xAI Grok CLI** (version 0.1.211) for SuperGrok Heavy accounts.
- **Desktop:** Added launcher shortcuts for VS Code, Antigravity, and Screensaver Settings.

### Cyberpunk Hub Visuals
- **Added:** **XScreenSaver** suite with classic hacker visuals (GLMatrix, Phosphor, GLSlideshow).
- **Added:** **CMatrix** for terminal-based digital rain effects.
- **Added:** Full suite of official **Kali Linux Wallpapers** (2019-2025).
- **Fixed:** Resolved conflicts between `xfce4-screensaver` and `xscreensaver`, ensuring cyberpunk visuals autostart on login.

## [v2.1.0] - 2026-05-13

### Acid Burn Engine
- **Added:** Advanced Conditional Execution for Molecules. Steps now support `condition` gates with Python expression evaluation and nested key access (e.g., `{{steps.X.result.key}}`).
- **Added:** `base_dir` injection into all tool execution contexts.
- **Improved:** `parsers.py` now includes structured output handlers for:
    - Browser Automation (`web.browser.inspect`, `interact`, `drill`).
    - Exploit Discovery (`exploit.search` via Searchsploit).
    - Post-Exploitation Reconnaissance (`post.exploit.recon`).
    - Port-specific boolean flags (e.g., `port_22_open`) in `kali.nmap` for easy molecule gating.

### New Skills & Tools
- **Added:** `ctf.full.pwn` Molecule — A complete autonomous attack chain from recon to persistence.
- **Added:** `auth.network.spray` Molecule — Multi-protocol credential auditing with conditional gating.
- **Added:** `auth.hydra` Tool — Structured atom for high-speed network authentication brute-forcing.
- **Added:** Browser Automation Suite — Playwright-backed atoms for deep DOM interaction and visual context analysis.

### COBOL-to-AI Pipeline
- **Fixed:** Port shadowing issues by ensuring single-instance `lemond` execution.
- **Optimized:** Inference configuration tuned for UMA hardware (max 3 loaded models, Vulkan contention resolved).
- **Refactored:** Harness logic migrated to atomic workers (`cobol_pipeline_worker.py`, `cobol_llm_evaluate.py`).
- **Infrastructure:** Added `FastFlowLM` to `.gitignore` to preserve repository hygiene.

---
*Built for the Strix Halo AI Homelab.*
