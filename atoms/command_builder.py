#!/usr/bin/env python3
"""Nmap Atom Command Builder — Gate 3

Maps atom parameters to nmap command-line flags and produces correct command strings.
Supports dry_run mode (returns command string without executing).

Usage:
    python3 command_builder.py --dry-run '{"target": "192.168.9.1", "scan_type": "syn-scan", ...}'
    python3 command_builder.py --exec '{"target": "192.168.9.1", "scan_type": "syn-scan", ...}'
"""

import json
import shlex
import subprocess
import sys
from typing import Optional

# ── Flag mapping table ────────────────────────────────────────────────
# Maps parameter name → nmap flag(s) with correct ordering and quoting

FLAG_MAP = {
    # Scan type flags (mutually exclusive in single invocation)
    "scan_type": {
        "host-discovery": ["-sn"],
        "syn-scan": ["-sS"],
        "connect-scan": ["-sT"],
        "udp-scan": ["-sU"],
        "os-detect": ["-O"],
        "version-detect": ["-sV"],
        "script-scan": ["-sC"],
        "traceroute": ["--traceroute"],
    },
    "ports": lambda v: ["-p", v] if v else None,
    "output_format": {
        "xml": ["-oX"],
        "normal": ["-oN"],
        "grepable": ["-oG"],
        "xml_and_normal": ["-oX", "-oN"],
        "xml_and_grepable": ["-oX", "-oG"],
        "all": ["-oA"],
    },
    "timing_template": {
        "paranoid": ["-T0"],
        "sneaky": ["-T1"],
        "polite": ["-T2"],
        "normal": ["-T3"],
        "aggressive": ["-T4"],
        "insane": ["-T5"],
    },
    # Single-value flags
    "host_timeout": lambda v: ["--host-timeout", str(v)],
    "max_retries": lambda v: ["--max-retries", str(v)],
    "version_intensity": lambda v: ["--version-intensity", str(v)],
    "data_length": lambda v: ["--data-length", str(v)] if v > 0 else None,
    "source_port": lambda v: ["--source-port", str(v)] if v > 0 else None,
    "max_rate": lambda v: ["--max-rate", str(v)] if v > 0 else None,
    "min_rate": lambda v: ["--min-rate", str(v)] if v > 0 else None,
    "top_ports": lambda v: ["--top-ports", str(v)] if v > 0 else None,
    "max_hosts": lambda v: ["--max-hosts", str(v)] if v > 0 else None,
    "verbose": lambda v: ["-v"] * v if v > 0 else None,
    # Boolean flags
    "dns_resolution": {"true": None, "false": ["--disable-lookup"]},
    "version_all": lambda v: ["--version-all"] if v else None,
    "fragment": lambda v: ["-f"] if v else None,
    "skip_host_discovery": lambda v: ["-Pn"] if v else None,
    # String flags
    "interface": lambda v: ["-e", v] if v else None,
    "proxy": lambda v: ["-x", v] if v else None,
    "script": lambda v: ["--script", v] if v else None,
    "dns_servers": lambda v: ["--dns-servers", ",".join(v)] if v else None,
    "reason": lambda v: ["--reason", v] if v else None,
}

# ── Command builder ───────────────────────────────────────────────────

def build_command(params: dict, dry_run: bool = True) -> str:
    """Build nmap command string from atom parameters.

    Args:
        params: Atom parameter dict (from example_invocations input)
        dry_run: If True, return command string. If False, execute.

    Returns:
        Command string (dry_run) or exit code (exec)
    """
    cmd = ["nmap"]

    # 1. Add scan type flag
    scan_type = params.get("scan_type", "host-discovery")
    if scan_type in FLAG_MAP["scan_type"]:
        cmd.extend(FLAG_MAP["scan_type"][scan_type])

    # 2. Add ports
    ports = params.get("ports")
    if ports and ports != "1-1024":  # Skip default
        flag_fn = FLAG_MAP.get("ports")
        if flag_fn and callable(flag_fn):
            result = flag_fn(ports)
            if result:
                cmd.extend(result)

    # 3. Add timing
    timing = params.get("timing_template")
    if timing:
        if timing in FLAG_MAP["timing_template"]:
            cmd.extend(FLAG_MAP["timing_template"][timing])

    # 4. Add host_timeout
    ht = params.get("host_timeout")
    if ht and ht != 60:
        flag_fn = FLAG_MAP.get("host_timeout")
        if flag_fn and callable(flag_fn):
            result = flag_fn(ht)
            if result:
                cmd.extend(result)

    # 5. Add version_intensity
    vi = params.get("version_intensity")
    if vi and vi != 7:
        flag_fn = FLAG_MAP.get("version_intensity")
        if flag_fn and callable(flag_fn):
            result = flag_fn(vi)
            if result:
                cmd.extend(result)

    # 6. Add boolean flags
    if not params.get("dns_resolution", True):
        cmd.extend(["--disable-lookup"])
    if params.get("version_all"):
        cmd.extend(["--version-all"])
    if params.get("fragment"):
        cmd.extend(["-f"])
    if params.get("skip_host_discovery"):
        cmd.extend(["-Pn"])

    # 7. Add output format
    of = params.get("output_format")
    if of and of != "xml":
        if of in FLAG_MAP["output_format"]:
            cmd.extend(FLAG_MAP["output_format"][of])

    # 8. Add output file
    ofile = params.get("output_file")
    if ofile and ofile != "stdout":
        cmd.extend(["-o", ofile])

    # 9. Add safety controls
    mr = params.get("max_rate")
    if mr and mr > 0:
        flag_fn = FLAG_MAP.get("max_rate")
        if flag_fn and callable(flag_fn):
            result = flag_fn(mr)
            if result:
                cmd.extend(result)

    mr2 = params.get("min_rate")
    if mr2 and mr2 > 0:
        flag_fn = FLAG_MAP.get("min_rate")
        if flag_fn and callable(flag_fn):
            result = flag_fn(mr2)
            if result:
                cmd.extend(result)

    mh = params.get("max_hosts")
    if mh and mh > 0:
        flag_fn = FLAG_MAP.get("max_hosts")
        if flag_fn and callable(flag_fn):
            result = flag_fn(mh)
            if result:
                cmd.extend(result)

    tp = params.get("top_ports")
    if tp and tp > 0:
        flag_fn = FLAG_MAP.get("top_ports")
        if flag_fn and callable(flag_fn):
            result = flag_fn(tp)
            if result:
                cmd.extend(result)

    # 10. Add reason
    reason = params.get("reason")
    if reason:
        flag_fn = FLAG_MAP.get("reason")
        if flag_fn and callable(flag_fn):
            result = flag_fn(reason)
            if result:
                cmd.extend(result)

    # 11. Add script
    script = params.get("script")
    if script:
        flag_fn = FLAG_MAP.get("script")
        if flag_fn and callable(flag_fn):
            result = flag_fn(script)
            if result:
                cmd.extend(result)

    # 12. Add dns_servers
    dns_srv = params.get("dns_servers")
    if dns_srv:
        flag_fn = FLAG_MAP.get("dns_servers")
        if flag_fn and callable(flag_fn):
            result = flag_fn(dns_srv)
            if result:
                cmd.extend(result)

    # 13. Add interface
    iface = params.get("interface")
    if iface:
        flag_fn = FLAG_MAP.get("interface")
        if flag_fn and callable(flag_fn):
            result = flag_fn(iface)
            if result:
                cmd.extend(result)

    # 14. Add proxy
    proxy = params.get("proxy")
    if proxy:
        flag_fn = FLAG_MAP.get("proxy")
        if flag_fn and callable(flag_fn):
            result = flag_fn(proxy)
            if result:
                cmd.extend(result)

    # 15. Add data_length
    dl = params.get("data_length")
    if dl and dl > 0:
        flag_fn = FLAG_MAP.get("data_length")
        if flag_fn and callable(flag_fn):
            result = flag_fn(dl)
            if result:
                cmd.extend(result)

    # 16. Add source_port
    sp = params.get("source_port")
    if sp and sp > 0:
        flag_fn = FLAG_MAP.get("source_port")
        if flag_fn and callable(flag_fn):
            result = flag_fn(sp)
            if result:
                cmd.extend(result)

    # 17. Add verbose
    vb = params.get("verbose")
    if vb and vb > 0:
        flag_fn = FLAG_MAP.get("verbose")
        if flag_fn and callable(flag_fn):
            result = flag_fn(vb)
            if result:
                cmd.extend(result)

    # 18. Add targets (must be last, unquoted)
    target = params.get("target")
    if target:
        cmd.append(target)

    return cmd


def dry_run_command(params: dict) -> str:
    """Build and return the command string for dry_run mode."""
    cmd = build_command(params, dry_run=True)
    return " ".join(shlex.quote(part) for part in cmd)


def execute_command(params: dict) -> int:
    """Build and execute the command. Returns exit code."""
    cmd = build_command(params, dry_run=False)
    # Prepend sudo if scan_type requires raw sockets
    requires_root = params.get("scan_type") in ("syn-scan", "udp-scan", "os-detect", "traceroute")
    if requires_root:
        # Check raw socket capability
        try:
            subprocess.run(
                ["python3", "-c", "import socket; socket.socket(socket.AF_INET, socket.SOCK_RAW)"],
                capture_output=True, timeout=5
            )
            cmd = ["sudo"] + cmd
        except (subprocess.TimeoutExpired, Exception):
            # Fall back to connect-scan if no raw sockets
            params["scan_type"] = "connect-scan"
            cmd = build_command(params)
            print("WARNING: Raw socket unavailable, falling back to connect-scan")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"nmap exit code: {result.returncode}", file=sys.stderr)
        print(result.stderr[:500], file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nmap Atom Command Builder")
    parser.add_argument("--dry-run", action="store_true", help="Return command string without executing")
    parser.add_argument("--exec", action="store_true", help="Execute the command")
    parser.add_argument("input", nargs="?", default="{}", help="JSON input of atom parameters")
    args = parser.parse_args()

    params = json.loads(args.input)
    if args.dry_run:
        print(dry_run_command(params))
    elif args.exec:
        rc = execute_command(params)
        sys.exit(rc)
    else:
        # Default: dry_run
        print(dry_run_command(params))
