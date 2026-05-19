#!/usr/bin/env python3
"""
web.search atom for Hermes / Acid Burn

Uses ddgr (DuckDuckGo from the terminal) to perform fast, private,
no-API-key web searches. Supports full DuckDuckGo Bang syntax so the
agent can force specific engines when needed (!g, !w, !gh, etc.).

This is the recommended general-purpose web search tool when running
locally on a machine with ddgr installed.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


def check_ddgr() -> str | None:
    """Return path to ddgr if available, else None."""
    path = shutil.which("ddgr")
    if path:
        return path
    return None


def run_ddgr(query: str, num_results: int) -> list[dict]:
    """Execute ddgr and return parsed JSON results."""
    ddgr_bin = check_ddgr()
    if not ddgr_bin:
        return [{
            "error": "ddgr not found",
            "message": "ddgr is required for web.search. Install with: sudo apt install ddgr"
        }]

    cmd = [
        ddgr_bin,
        "--json",
        "-n", str(num_results),
        "--unsafe",           # allow NSFW-ish results if user wants them
        "--nocolor",          # no ANSI codes
        query
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return [{"error": "ddgr failed", "stderr": result.stderr.strip()[:500]}]

        data = json.loads(result.stdout or "[]")
        return data if isinstance(data, list) else []

    except subprocess.TimeoutExpired:
        return [{"error": "timeout", "message": "ddgr took too long"}]
    except json.JSONDecodeError as e:
        return [{"error": "json_parse_failed", "raw": result.stdout[:800]}]
    except Exception as e:
        return [{"error": str(e)}]


def format_for_agent(results: list[dict], query: str) -> str:
    """Produce clean, LLM-friendly output."""
    if not results:
        return f"No results found for: {query}"

    if "error" in results[0]:
        err = results[0]
        msg = err.get('message') or err.get('error')
        if 'stderr' in err:
            msg += f" | Details: {err['stderr']}"
        return f"Search failed: {msg}"

    lines = [f"Web search results for: {query}\n"]

    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled").strip()
        url = r.get("url", "")
        abstract = (r.get("abstract") or "").strip().replace("\n", " ")

        lines.append(f"[{i}] {title}")
        lines.append(f"     {url}")
        if abstract:
            # Keep snippets reasonable length for context
            if len(abstract) > 380:
                abstract = abstract[:377] + "..."
            lines.append(f"     {abstract}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Hermes web search via ddgr")
    parser.add_argument("--query", required=True, help="Search query (supports !bangs)")
    parser.add_argument("--num-results", type=int, default=8, help="Number of results")
    parser.add_argument("--artifact", help="Path to write raw JSON artifact")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format for the agent")

    args = parser.parse_args()

    results = run_ddgr(args.query, args.num_results)

    # Write raw artifact (best effort)
    if args.artifact:
        try:
            os.makedirs(os.path.dirname(args.artifact) or ".", exist_ok=True)
            with open(args.artifact, "w", encoding="utf-8") as f:
                json.dump({
                    "query": args.query,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tool": "web.search",
                    "backend": "ddgr",
                    "results": results
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[web.search] Warning: could not write artifact: {e}", file=sys.stderr)

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_for_agent(results, args.query))


if __name__ == "__main__":
    main()
