# Changelog: Acid Burn - White Hat Multi-Tool

All notable changes to the Acid Burn toolkit and the security auditing pipeline are documented here.

## [v2.2.0] - 2026-05-16 - "The Cyberpunk Expansion"

### Core & Rebranding
- **Rebranded:** Project officially branched from Acid Burn to **Acid Burn**.
- **Added:** New comprehensive `README.md` with multi-tool architecture mapping.
- **Added:** **Grok-Driven Intelligence** integration. Leverages xAI Grok Build CLI for autonomous evaluation and strategic planning.
- **Added:** **5-Gate Validation Protocol** design (Network, Postcondition, Timeout, Schema, and Test Harness).
- **Added:** Mandatory **Template Resolution** enforcement in `HERMES.md` to prevent placeholder hallucinations.
- **Repository:** Migration to official repository: `https://github.com/MrSnowNB/Acid-Burn`.

### Environment & Tools
- **Added:** Official **Visual Studio Code** installation via Microsoft repository.
- **Added:** **Google Antigravity** AI-powered IDE installation for agentic workflows.
- **Added:** Official **xAI Grok CLI** (version 0.1.211) for SuperGrok Heavy accounts.
- **Desktop:** Added launcher shortcuts for VS Code, Antigravity, and Screensaver Settings.

### Cyberpunk Hub Visuals
- **Added:** **XScreenSaver** suite with classic hacker visuals:
    - **GLMatrix:** 3D Matrix digital rain.
    - **Phosphor:** Retro 1980s green-screen terminal simulation.
    - **GLSlideshow:** Integrated for tech-feed visualization.
- **Added:** **CMatrix** for terminal-based digital rain effects.
- **Added:** Full suite of official **Kali Linux Wallpapers** (2019-2025).
- **Added:** **Telnet** integration for ASCII-based Star Wars animation.
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
