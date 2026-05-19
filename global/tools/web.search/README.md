# web.search — Hermes Internet Search Tool

Powered by `ddgr` (DuckDuckGo from the terminal).

## Why this instead of Playwright scraping Google?

- DuckDuckGo is far more friendly to automation
- `ddgr` already solves cookies, regions, pagination, and output formatting
- Native support for **DuckDuckGo Bangs** (`!g`, `!w`, `!gh`, `!so`, `!yt`, etc.)
- No fragile HTML selectors that break every time Google ships a new frontend
- No CAPTCHA hell

## Installation (required on the host)

```bash
# Debian / Ubuntu / Kali
sudo apt install ddgr

# Fedora
sudo dnf install ddgr

# macOS
brew install ddgr
```

## Usage from Hermes

Once the tool is loaded, Hermes can call it like any other atom:

```
web.search(query="latest open source LLMs 2026", num_results=8)
```

Bangs work transparently:

```
web.search(query="Qwen3 35B MTP !g")     # forces Google results
web.search(query="Strix Halo !w")        # Wikipedia
```

## Files

- `web.search.yaml` — tool registration
- `web_search.py`   — the actual implementation

## Output

Clean, numbered results with title + URL + snippet, perfect for feeding back into the agent context.
