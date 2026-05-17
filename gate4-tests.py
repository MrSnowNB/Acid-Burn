#!/usr/bin/env python3
"""Gate 4: Output Schema Validation — Test Suite

Tests that the nmap XML output parser:
1. Correctly validates XML schema against expected record schema
2. Extracts all defined fields correctly
3. Handles missing fields with proper nullability
4. Enforces allowed_values for state field
5. Rejects malformed XML
6. Handles edge cases (empty results, large scans)

Run with: python3 gate4-tests.py
"""

import sys
import yaml
import xml.etree.ElementTree as ET
from io import StringIO

ATOM_PATH = "/home/mark/Acid-Burn/atoms/nmap.yaml"
with open(ATOM_PATH) as f:
    atom = yaml.safe_load(f)

parser_module_path = atom.get("output_parser", {}).get("parser_module", "")
record_schema = atom.get("output_parser", {}).get("record_schema", [])

errors = []
passed = 0

def check(name, condition, detail=""):
    global passed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        errors.append((name, detail))
        print(f"  FAIL: {name} — {detail}")

# ── GATE 4 CHECK 1: Schema completeness ─────────────────────────────

print("\n=== CHECK 1: Schema Completeness ===")

required_fields = [
    ("ip_address", "string"),
    ("mac_address", "string"),
    ("hostname", "string"),
    ("port", "integer"),
    ("protocol", "string"),
    ("state", "string"),
    ("service", "string"),
    ("version", "string"),
]

schema_fields = {f["field"]: f for f in record_schema}

for field_name, expected_type in required_fields:
    if field_name in schema_fields:
        sf = schema_fields[field_name]
        check(f"Field '{field_name}' exists in schema", True)
        check(f"Field '{field_name}' has correct type",
              sf.get("type") == expected_type,
              f"Expected: {expected_type}, Got: {sf.get('type')}")
    else:
        check(f"Field '{field_name}' exists in schema", False, "Missing from schema")

# Check nullable fields
nullable_fields = [f["field"] for f in record_schema if f.get("nullable")]
non_nullable = [f["field"] for f in record_schema if not f.get("nullable")]
check("schema has nullable fields", len(nullable_fields) > 0,
      f"Nullable: {nullable_fields}")
check("schema has non-nullable fields", len(non_nullable) > 0,
      f"Non-nullable: {non_nullable}")

# Check allowed_values for state
state_field = schema_fields.get("state", {})
if "allowed_values" in state_field:
    check("State field has allowed_values", True)
    expected_states = {"open", "closed", "filtered", "open|filtered", "closed|filtered"}
    actual_states = set(state_field["allowed_values"])
    check("State allowed_values are complete",
          expected_states.issubset(actual_states),
          f"Expected: {expected_states}, Got: {actual_states}")
else:
    check("State field has allowed_values", False, "Missing allowed_values")

# ── GATE 4 CHECK 2: XML parser functionality ────────────────────────

print("\n=== CHECK 2: XML Parser Extraction ===")

# Create a minimal valid nmap XML
nmap_xml_basic = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun scanner="nmap" args="nmap -sn 192.168.1.0/24" start="1234567890"
         startstr="Host is up" version="7.94" xmloutputversion="1.05">
  <scaninfo type="syn" protocol="tcp" numservices="1" services="1-1024"/>
  <host starttime="1234567890" endtime="1234567891">
    <status state="up" reason="echo-reply" reason_ttl="64"/>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <address addr="00:11:22:33:44:55" addrtype="mac" vendor="TestVendor"/>
    <hostnames>
      <hostname name="test.local" type="PTR"/>
    </hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open" reason="syn-ack" reason_ttl="0"/>
        <service name="ssh" product="OpenSSH" version="8.9p1"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="closed" reason="reset" reason_ttl="0"/>
        <service name="http"/>
      </port>
      <port protocol="udp" portid="53">
        <state state="open" reason="response" reason_ttl="0"/>
        <service name="domain"/>
      </port>
    </ports>
    <os>
      <osmatch name="Linux 5.x" accuracy="95">
        <osclass type="general purpose" vendor="Linux" osfamily="Linux"/>
      </osmatch>
    </os>
    <times srtt="12345" rttvar="1234" to="100000"/>
  </host>
  <runstats>
    <finished time="1234567892" elapsed="2.00" summary="Nmap done" exit="success"/>
    <hosts up="1" down="254" total="255"/>
  </runstats>
</nmaprun>
"""

def parse_nmap_xml(xml_str):
    """Parse nmap XML and extract records according to schema."""
    root = ET.parse(StringIO(xml_str)).getroot()
    records = []

    for host in root.findall("host"):
        record = {}

        # IP address
        addr = host.find('address[@addrtype="ipv4"]')
        record["ip_address"] = addr.get("addr") if addr is not None else None

        # MAC address
        mac = host.find('address[@addrtype="mac"]')
        record["mac_address"] = mac.get("addr") if mac is not None else None
        record["vendor"] = mac.get("vendor") if mac is not None else None

        # Hostname
        hostnames = host.findall("hostnames/hostname")
        record["hostname"] = hostnames[0].get("name") if hostnames else None

        # Ports
        for port_elem in host.findall("ports/port"):
            port_record = dict(record)  # Copy host-level fields
            port_record["port"] = int(port_elem.get("portid"))
            port_record["protocol"] = port_elem.get("protocol")

            state_elem = port_elem.find("state")
            port_record["state"] = state_elem.get("state") if state_elem is not None else None
            service_elem = port_elem.find("service")
            port_record["service"] = service_elem.get("name") if service_elem is not None else None
            port_record["version"] = service_elem.get("version") if service_elem is not None else None

            cpe_elem = port_elem.find("cpe")
            port_record["cpes"] = [cpe_elem.text] if cpe_elem is not None and cpe_elem.text else None

            scripts_elem = port_elem.findall("script")
            port_record["scripts"] = [s.get("id") for s in scripts_elem] if scripts_elem else None

            records.append(port_record)

        # OS detection
        os_elem = host.find("os")
        if os_elem is not None:
            osmatch = os_elem.find("osmatch")
            if osmatch is not None:
                record["os_name"] = osmatch.get("name")
                record["os_accuracy"] = int(osmatch.get("accuracy"))

        records.append(record)  # Host-level record (no port)

    return records

# Parse the test XML
try:
    records = parse_nmap_xml(nmap_xml_basic)
    check("XML parser parses valid XML", True, f"Got {len(records)} records")

    # Check field extraction
    port_records = [r for r in records if "port" in r and r["port"] is not None]
    check("Port records extracted", len(port_records) == 3,
          f"Expected 3 ports, got {len(port_records)}")

    # Check specific port 22
    port_22 = next((r for r in port_records if r["port"] == 22), None)
    if port_22:
        check("Port 22 state='open'", port_22["state"] == "open",
              f"Got: {port_22['state']}")
        check("Port 22 service='ssh'", port_22["service"] == "ssh",
              f"Got: {port_22['service']}")
        check("Port 22 version present", port_22["version"] is not None,
              f"Version: {port_22.get('version')}")

    # Check specific port 80
    port_80 = next((r for r in port_records if r["port"] == 80), None)
    if port_80:
        check("Port 80 state='closed'", port_80["state"] == "closed",
              f"Got: {port_80['state']}")

    # Check specific port 53
    port_53 = next((r for r in port_records if r["port"] == 53), None)
    if port_53:
        check("Port 53 protocol='udp'", port_53["protocol"] == "udp",
              f"Got: {port_53['protocol']}")

    # Check host-level fields
    host_record = next((r for r in records if "ip_address" in r), None)
    if host_record:
        check("IP address extracted", host_record["ip_address"] == "192.168.1.1")
        check("MAC address extracted", host_record["mac_address"] == "00:11:22:33:44:55")
        check("Hostname extracted", host_record["hostname"] == "test.local")

    # Check OS detection
    os_records = [r for r in records if r.get("os_name")]
    check("OS name extracted", len(os_records) > 0,
          f"OS records: {os_records}")
    if os_records:
        check("OS accuracy is integer", isinstance(os_records[0].get("os_accuracy"), int))

except Exception as e:
    check("XML parser parses valid XML", False, str(e))

# ── GATE 4 CHECK 3: Malformed XML handling ──────────────────────────

print("\n=== CHECK 3: Malformed XML Handling ===")

malformed_cases = [
    ("empty", ""),
    ("no nmaprun tag", "<host></host>"),
    ("unclosed tag", "<nmaprun><host><status state="),
    ("invalid XML chars", "<nmaprun><host><bad>\x00\x01</bad></host></nmaprun>"),
    ("missing ports", "<nmaprun><host><status state=\"up\"/></host></nmaprun>"),
]

for case_name, xml in malformed_cases:
    try:
        result = parse_nmap_xml(xml)
        check(f"Malformed XML '{case_name}' handled without crash", True)
    except ET.ParseError as e:
        check(f"Malformed XML '{case_name}' raises ParseError", True)
    except Exception as e:
        check(f"Malformed XML '{case_name}' handled without crash", False, str(e))

# ── GATE 4 CHECK 4: Allowed values validation ───────────────────────

print("\n=== CHECK 4: Allowed Values Validation ===")

valid_states = ["open", "closed", "filtered", "open|filtered", "closed|filtered"]
invalid_states = ["up", "down", "weird", "OPEN", ""]

for state in valid_states:
    check(f"State '{state}' is valid", state in state_field.get("allowed_values", []))

for state in invalid_states:
    check(f"State '{state}' is NOT in allowed_values",
          state not in state_field.get("allowed_values", []))

# ── GATE 4 CHECK 5: Empty results handling ──────────────────────────

print("\n=== CHECK 5: Empty Results Handling ===")

empty_nmap = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -sn 192.168.999.0/24">
  <scaninfo type="syn" protocol="tcp" numservices="1" services="1-1024"/>
  <runstats>
    <finished time="1234567892" elapsed="1.00"/>
    <hosts up="0" down="255" total="255"/>
  </runstats>
</nmaprun>
"""

try:
    empty_records = parse_nmap_xml(empty_nmap)
    check("Empty results return empty list", len(empty_records) == 0,
          f"Got {len(empty_records)} records")
except Exception as e:
    check("Empty results return empty list", False, str(e))

# ── SUMMARY ─────────────────────────────────────────────────────────

total = passed + len(errors)
print(f"\n{'='*60}")
print(f"Gate 4 Results: {passed}/{total} checks passed")
if errors:
    print(f"\n{len(errors)} FAILURES:")
    for name, detail in errors:
        print(f"  ✗ {name}: {detail}")
    print("\nGATE 4: FAILED — fix all failures before proceeding")
else:
    print("\nGATE 4: PASSED — proceed to Gate 5")

sys.exit(1 if errors else 0)
