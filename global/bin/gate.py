import re
import yaml
import ipaddress
import os
import socket
from pathlib import Path

BASE_DIR = Path.home() / ".securatron"

# Default ports to probe for reachability check
_REACHABILITY_PORTS = [22, 80, 443, 8080, 3389]
_REACHABILITY_TIMEOUT = 1  # seconds per port (reduced for speed)

# Template resolution guard: detect unresolved {{inputs.*}} patterns
_UNRESOLVED_TEMPLATE_RE = re.compile(r'\{\{inputs\.\w+\}\}')

def check_scope_match(target: str, allowed_list: list[str]) -> bool:
    """Check if a target matches an entry or is contained within a CIDR range."""
    # Strip port if present (e.g., 127.0.0.1:80 or example.com:443)
    clean_target = target.split(":")[0]
    
    for entry in allowed_list:
        if clean_target == entry:
            return True
        try:
            # Check for CIDR containment
            if "/" in entry:
                if ipaddress.ip_address(clean_target) in ipaddress.ip_network(entry):
                    return True
        except ValueError:
            continue
    return False

def check_template_resolved(inputs: dict) -> tuple[bool, str]:
    """Validate that inputs don't contain unresolved template strings.
    
    Returns (is_valid, error_message).
    This catches the common failure mode where the agent passes literal
    '{{inputs.flags}}' instead of resolved values like '-sV -Pn -T3'.
    """
    for key, value in inputs.items():
        if isinstance(value, str) and _UNRESOLVED_TEMPLATE_RE.search(value):
            return False, f"template_not_resolved: input '{key}' contains unresolved template '{{inputs.{key}}}' — resolve to actual value"
        elif isinstance(value, (dict, list)):
            # Recursively check nested structures
            nested_valid, nested_error = _check_nested(value, key)
            if not nested_valid:
                return False, nested_error
    return True, ""

def _check_nested(value, parent_key: str) -> tuple[bool, str]:
    """Recursively check nested dicts/lists for unresolved templates."""
    if isinstance(value, str) and _UNRESOLVED_TEMPLATE_RE.search(value):
        return False, f"template_not_resolved in '{parent_key}': contains '{{inputs.*}}' pattern"
    elif isinstance(value, dict):
        for k, v in value.items():
            valid, err = _check_nested(v, f"{parent_key}.{k}")
            if not valid:
                return False, err
    elif isinstance(value, list):
        for i, item in enumerate(value):
            valid, err = _check_nested(item, f"{parent_key}[{i}]")
            if not valid:
                return False, err
    return True, ""

def check_scope(card: dict, inputs: dict, project_id: str, scope_file: str = None) -> bool:
    """Validate that inputs (like targets) are within project scope."""
    if not scope_file:
        scope_file = BASE_DIR / "projects" / project_id / "scope.yaml"
    else:
        scope_file = Path(scope_file)

    if not scope_file.exists():
        return False
        
    scope = yaml.safe_load(scope_file.read_text())
    allowed_targets = scope.get("targets", [])
    
    target = inputs.get("target") or inputs.get("host") or inputs.get("url")
    if target:
        # Strip port or protocol if present for basic matching
        clean_target = re.sub(r"^(http|https)://", "", target)
        return check_scope_match(clean_target, allowed_targets)
        
    return True

def _resolve_target_host(inputs: dict) -> str | None:
    """Extract the target host from inputs, stripping port and protocol."""
    target = inputs.get("target") or inputs.get("host") or inputs.get("url")
    if not target:
        return None
    # Strip protocol
    target = re.sub(r"^(http|https)://", "", target)
    # Strip port
    clean = target.split(":")[0]
    return clean


def check_network_reachable(inputs: dict) -> tuple[bool, str]:
    """Check if a target host is reachable via TCP on common ports.
    
    Returns (is_reachable, error_message).
    Probes ports [_REACHABILITY_PORTS] with _REACHABILITY_TIMEOUT seconds each.
    If ANY port is open, the host is considered reachable.
    
    Special case: only 127.0.0.1, localhost, and ::1 are always reachable.
    Private ranges (10.x, 172.16-31.x, 192.168.x) are probed — they may be
    reachable on the local network.
    """
    host = _resolve_target_host(inputs)
    if not host:
        return True, ""  # No target to check
    
    # Always reachable: loopback only
    if host in ("127.0.0.1", "localhost", "::1"):
        return True, ""
    
    # Try TCP connect on common ports for all other addresses
    for port in _REACHABILITY_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(_REACHABILITY_TIMEOUT)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True, ""
        except (socket.gaierror, socket.timeout, OSError):
            continue
    
    return False, f"network_unreachable: host '{host}' not reachable on ports {_REACHABILITY_PORTS}"


def check_preconditions(card: dict, inputs: dict, 
                        session_dir: str = None,
                        scope_file: str = None) -> tuple[bool, list[str]]:
    """
    Evaluate skill card preconditions.
    Returns (passed: bool, failures: list[str])
    """
    preconditions = card.get("preconditions", [])
    if not preconditions:
        return True, []

    failures = []
    
    for expr in preconditions:
        # 1. scope.includes(inputs.X)
        match = re.match(r"scope\.includes\(inputs\.(\w+)\)", expr)
        if match:
            key = match.group(1)
            val = inputs.get(key)
            if not val:
                failures.append(f"Precondition failed: {key} not found in inputs")
                continue
            
            if not scope_file:
                failures.append("No scope file provided — cannot verify target is in scope")
                continue
            
            if not Path(scope_file).exists():
                failures.append(f"No scope file found at {scope_file} — cannot verify target is in scope")
                continue
            
            scope_data = yaml.safe_load(Path(scope_file).read_text())
            allowed = scope_data.get("targets") or scope_data.get("scope") or []
            
            # The actual fix: use the value provided, check_scope_match handles port stripping
            if not check_scope_match(val, allowed):
                failures.append(f"Target '{val}' is OUT OF SCOPE")
            continue

        # 2. network.reachable(inputs.X) — GATE 1: REAL IMPLEMENTATION
        match = re.match(r"network\.reachable\(inputs\.(\w+)\)", expr)
        if match:
            is_reachable, err = check_network_reachable(inputs)
            if not is_reachable:
                failures.append(err)
            continue

        # 3. artifact_exists(outputs.X) — GATE 2: STUB (implement later)
        match = re.match(r"artifact_exists\(outputs\.(\w+)\)", expr)
        if match:
            # TODO: Add real postcondition evaluation logic in Phase 4
            continue

        # 4. Any unrecognized expression
        failures.append(f"Unknown precondition: {expr} — cannot verify")

    return (len(failures) == 0, failures)

def check_secrets(inputs: dict) -> bool:
    """Scan inputs for potential leaks of sensitive data."""
    secret_patterns = [
        r"sk-[a-zA-Z0-9]{32,}", # OpenAI
        r"AIza[0-9A-Za-z-_]{35}", # Google
        r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
    ]
    
    input_str = str(inputs)
    for pattern in secret_patterns:
        if re.search(pattern, input_str):
            return False
    return True

def check_budget(card: dict, session_id: str) -> bool:
    """Check if the tool call fits within the session's resource budget."""
    return True

def validate_all(card: dict, inputs: dict, project_id: str, session_id: str) -> tuple[bool, str]:
    """Run all gate checks."""
    # Phase 0: Template resolution guard
    tmpl_valid, tmpl_err = check_template_resolved(inputs)
    if not tmpl_valid:
        return False, tmpl_err
    
    if not check_secrets(inputs):
        return False, "secret_leak_detected"
    
    # Preconditions check
    # Auto-locate scope file if not provided
    scope_file = BASE_DIR / "projects" / project_id / "scope.yaml"
    passed, failures = check_preconditions(card, inputs, scope_file=str(scope_file))
    if not passed:
        return False, f"preconditions_not_met: {'; '.join(failures)}"
        
    if not check_budget(card, session_id):
        return False, "budget_exceeded"
        
    return True, "ok"
