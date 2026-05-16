# Nmap Atom Privilege Model

**Atom Version:** 1.1
**Date:** 2026-05-16T19:20Z

## Principle

Privilege escalation (sudo) must only be triggered when absolutely necessary for the requested scan type, and must be conditional — not automatic.

## Privilege Requirements by Scan Type

| Scan Type | Requires Root? | Why | Fallback if Unprivileged |
|-----------|---------------|-----|--------------------------|
| host-discovery (-sn) | No | Uses ICMP ping or TCP SYN ping | Works unprivileged |
| syn-scan (-sS) | **Yes** | Raw socket required for SYN half-open | Falls back to connect-scan (-sT) |
| connect-scan (-sT) | No | Uses standard TCP connect() | Works unprivileged |
| udp-scan (-sU) | **Yes** | Raw socket required for UDP probes | Limited to privileged ports only |
| os-detect (-O) | **Yes** | Requires raw packet crafting | Inaccurate results without root |
| version-detect (-sV) | No | Works unprivileged (connect-based) | May miss some services |
| script-scan (-sC) | No (most) | NSE scripts run in interpreter | Some scripts require root |
| traceroute (--traceroute) | **Yes** | Raw UDP probe required | Limited traceroute functionality |
| aggressive (-A) | **Yes** | Combines OS detection + version + scripts | Partial scan without root |
| stealth-udp | **Yes** | Same as udp-scan | Same |

## Conditional Sudo Implementation

```
IF scan_type IN (syn-scan, udp-scan, os-detect, traceroute) AND capability(raw_socket):
    prefix = "sudo"
ELSE:
    prefix = ""
```

## Capability Matrix

| Capability | Check Command | Required For |
|-----------|--------------|--------------|
| nmap binary | `command -v nmap` | All scans |
| nmap version >= 7.0 | `nmap --version` | All scans (XML output) |
| scripts directory | `test -d /usr/share/nmap/scripts` | script-scan |
| raw sockets | `python3 -c 'import socket; socket.socket(socket.AF_INET, socket.SOCK_RAW)' 2>/dev/null` | syn-scan, udp-scan, os-detect |
| pcap | `python3 -c 'import pcapy' 2>/dev/null` | (future: packet capture) |
| output directory | `test -w $(dirname output_file)` | All scans with file output |
| python3 | `command -v python3` | Parser execution |
| xml.etree | `python3 -c 'import xml.etree.ElementTree' 2>/dev/null` | XML parser |

## Safety: No Unconditional Sudo

- **v1.0 violation:** Precondition `sudo nmap -sn -PR 127.0.0.0/24` performed an ARP scan as a precondition
- **v1.1 fix:** Preconditions are pure checks only (command existence, version, directory writability)
- **Sudo only at execution time**, conditional on scan_type requiring raw sockets
- **Passwordless sudo requires:** `sudo visudo` entry for the specific nmap binary only, with NO sudoers wildcard
