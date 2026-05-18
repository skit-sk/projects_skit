# agent-browser + Playwright Chrome Integration Guide

## Current Status (2026-05-01)

| Component | Status | Location |
|-----------|--------|----------|
| **agent-browser CLI** | ✅ Working | `/home/user_aioc/.local/lib/node_modules/agent-browser/bin/agent-browser-linux-x64` |
| **Playwright Chrome** | ✅ Working | `/tmp/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome` |
| **Chrome libraries** | ✅ Extracted | `/tmp/pango_libs/usr/lib/x86_64-linux-gnu/` |
| **Wrapper script** | ✅ Working | `/home/user_aioc/workspace/tools/agent-browser/bin/agent-browser.sh` |

---

## Quick Start

### Option 1: Use wrapper script (RECOMMENDED)
```bash
./tools/agent-browser/bin/agent-browser.sh open https://example.com
./tools/agent-browser/bin/agent-browser.sh snapshot -i
./tools/agent-browser/bin/agent-browser.sh click @e2
./tools/agent-browser/bin/agent-browser.sh close
```

### Option 2: Set environment variables manually
```bash
export LD_LIBRARY_PATH="/tmp/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export HOME=/tmp
export AGENT_BROWSER_STATE_DIR=/tmp/.agent-browser
export PATH="/home/user_aioc/.local/bin:$PATH"

# Open page with Playwright Chrome
agent-browser open https://example.com --executable-path /tmp/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome
```

---

## Why This Configuration?

1. **agent-browser's Chrome** (`/tmp/.agent-browser/browsers/chrome-148.0.7778.97/chrome`) requires system libraries that are missing in the container (libpango, libXdamage, etc.)

2. **Playwright's Chrome** has all dependencies bundled and works correctly

3. The wrapper script automatically uses Playwright's Chrome with `--executable-path`

---

## Browser Options

### Option A: Playwright Chrome (DEFAULT - works)
```bash
./tools/agent-browser/bin/agent-browser.sh open <url>
```
Uses: `/tmp/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome`

### Option B: Lightpanda (alternative - experimental)
```bash
# Start Lightpanda server
/tmp/lightpanda serve --port 9322 &

# Use agent-browser with Lightpanda CDP
agent-browser open <url> --cdp ws://localhost:9322
```
Note: Lightpanda is lightweight but has limited features compared to Chrome.

### Option C: Use agent-browser's Chrome (if libraries are installed)
```bash
# Install system libraries (requires root/sudo)
apt-get install -y libpango-1.0-0 libxdamage1 libasound2t64

# Then agent-browser will use its default Chrome
agent-browser open <url>
```

---

## AI Agent Commands

The following commands are **understood by the AI agent** and should work:

### Navigation
```bash
agent-browser open <url>              # Open URL
agent-browser goto <url>              # Same as open
agent-browser back                    # Go back
agent-browser forward                 # Go forward
agent-browser reload                  # Reload page
```

### Interact with elements
```bash
agent-browser snapshot [-i]           # Get accessibility tree
agent-browser click @eN              # Click by ref
agent-browser fill @eN "text"        # Fill input
agent-browser hover @eN              # Hover
agent-browser find role button click --name "Submit"  # Semantic locator
```

### Screenshot
```bash
agent-browser screenshot              # Simple screenshot
agent-browser screenshot --annotate   # With element labels
```

### Batch execution (for complex workflows)
```bash
agent-browser batch "open <url>" "snapshot -i" "click @e1" "screenshot"
```

---

## Troubleshooting

### Error: "Chrome exited early"
```bash
# Close all sessions and retry
agent-browser close --all
agent-browser open <url>
```

### Error: "Failed to create socket directory"
```bash
# Ensure state directory exists
mkdir -p /tmp/.agent-browser
export AGENT_BROWSER_STATE_DIR=/tmp/.agent-browser
```

### Error: "daemon already running"
```bash
agent-browser close --all
sleep 1
agent-browser open <url>
```

---

## Dependencies

Chrome requires these libraries. They are extracted to `/tmp/pango_libs/`:
- libpango-1.0-0
- libxdamage1
- libfribidi0
- libthai0
- libharfbuzz0b
- libdatrie1
- libgraphite2-3

If you need to add more:
```bash
apt-get download <package>
dpkg -x <package>.deb /tmp/pango_libs/
export LD_LIBRARY_PATH="/tmp/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
```

---

## When to Use Which

| Task | Recommended Browser | Command |
|------|---------------------|---------|
| Simple page navigation | Playwright Chrome | `./agent-browser.sh open <url>` |
| AI agent web scraping | Playwright Chrome | `./agent-browser.sh batch "open <url>" "snapshot -i"` |
| Screenshot with annotations | Playwright Chrome | `./agent-browser.sh screenshot --annotate` |
| Lightweight browsing | Lightpanda | `agent-browser --engine lightpanda open <url>` |
| Full Chrome features | Playwright Chrome | Default |

---

## Files Structure

```
/home/user_aioc/workspace/
├── tools/
│   └── agent-browser/
│       ├── bin/
│       │   ├── agent-browser.sh    # Wrapper with correct libs (RECOMMENDED)
│       │   └── quick-snapshot.sh   # Quick snapshot utility
│       ├── workflows/              # Pre-built workflows
│       ├── config/
│       └── README.md
└── skills/
    └── agent-browser/             # AI agent skill instructions
```

---

## For AI Agent

When asking the AI agent to use browser automation, use these commands:

```bash
# Basic workflow
./tools/agent-browser/bin/agent-browser.sh open <url>
./tools/agent-browser/bin/agent-browser.sh snapshot -i
./tools/agent-browser/bin/agent-browser.sh click @eN

# With screenshot
./tools/agent-browser/bin/agent-browser.sh screenshot --annotate

# Close when done
./tools/agent-browser/bin/agent-browser.sh close
```

The AI will understand: `@eN` references from snapshots, `-i` for interactive elements only, `--annotate` for labeled screenshots.