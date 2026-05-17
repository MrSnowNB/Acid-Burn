import sys
from pathlib import Path

# Ensure global/bin is in path to import parsers
sys.path.append(str(Path(__file__).parent.parent.parent / "global/bin"))

import parsers

def parse(stdout, stderr="", returncode=0, **kwargs):
    """
    Wrapper for the centralized nmap.scan.v1 parser.
    """
    result = parsers.parse("nmap.scan.v1", stdout, raw_stderr=stderr, exit_code=returncode, **kwargs)
    if result.get("ok"):
        return result["result"]
    else:
        return {"error": result.get("reason"), "raw": stdout[:1000]}
