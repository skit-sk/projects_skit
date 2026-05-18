# agent-browser Instructions

Complete installation and usage instructions for agent-browser with Playwright Chrome.

---

## Installation Status (2026-05-01)

All components are installed and working:

| Component | Path | Status |
|-----------|------|--------|
| agent-browser CLI | `/home/user_aioc/.local/lib/node_modules/agent-browser/bin/agent-browser-linux-x64` | ✅ |
| Playwright Chrome | `/tmp/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome` | ✅ |
| Chrome libraries | `/tmp/pango_libs/usr/lib/x86_64-linux-gnu/` | ✅ |
| Wrapper script | `/home/user_aioc/workspace/tools/agent-browser/bin/agent-browser.sh` | ✅ |

---

## Quick Start

```bash
# Always use the wrapper script
./tools/agent-browser/bin/agent-browser.sh open https://example.com
./tools/agent-browser/bin/agent-browser.sh snapshot -i
./tools/agent-browser/bin/agent-browser.sh click @e2
```

---

## Wrapper Script Setup

The wrapper automatically handles:
- `LD_LIBRARY_PATH` for Chrome libraries
- `HOME=/tmp` for temp files
- `AGENT_BROWSER_STATE_DIR` for session state
- `--executable-path` pointing to Playwright's Chrome

If you need to set up manually:
```bash
export LD_LIBRARY_PATH="/tmp/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export HOME=/tmp
export AGENT_BROWSER_STATE_DIR=/tmp/.agent-browser
export PATH="/home/user_aioc/.local/bin:$PATH"
```

---

## Snapshot and References

### How refs work

agent-browser assigns short refs (`@e1`, `@e2`) to interactive elements:

```
button "Sign In" [ref=e1]
textbox "Email" [ref=e2]
textbox "Password" [ref=e3]
```

Use refs instead of CSS selectors - more reliable for AI agents.

### Snapshot flags

| Flag | Description | Use Case |
|------|-------------|----------|
| `-i` | Interactive elements only | **AI default** - compact |
| `--urls` | Include href URLs | Link navigation |
| `-c` | Compact - no empty elements | Token savings |
| `-d N` | Tree depth limit N | Shallow pages |
| `-s <sel>` | Scope to CSS selector | Specific areas |

**Recommended for AI:**
```bash
snapshot -i              # Interactive only
snapshot -i --urls       # + href URLs
snapshot -i -c -d 5     # Compact, depth 5
```

---

## Element Interaction

### Via refs (recommended)
```bash
agent-browser click @e2           # Click
agent-browser fill @e3 "text"     # Fill input
agent-browser hover @e1           # Hover
agent-browser focus @e2           # Focus
agent-browser press @e2 Enter    # Press key
agent-browser type @e2 "hello"   # Type character by char
```

### Via semantic locators
```bash
find role button click --name "Submit"
find text "Sign In" click
find label "Email" fill "test@test.com"
find placeholder "Search" fill "query"
find testid my-id click
```

### Via CSS selectors (legacy)
```bash
click "#submit"
fill "#email" "test@example.com"
```

---

## Navigation

```bash
open <url>           # Open URL (or: goto, navigate)
back                 # Go back
forward             # Go forward
reload              # Reload page
pushstate <url>     # SPA navigation
```

---

## Tabs

```bash
tab new <url>                  # New tab
tab new --label docs <url>     # New tab with label
tab docs                       # Switch to tab by label
tab t2                         # Switch to tab by ID
tab close docs                 # Close tab by label
```

---

## Sessions

For isolated browser instances:
```bash
agent-browser --session agent1 open site-a.com
agent-browser --session agent2 open site-b.com
agent-browser session list
```

---

## Screenshot

```bash
screenshot                     # Simple
screenshot --annotate         # With numbered element labels
screenshot page.png           # To file
screenshot --full             # Full page
screenshot --screenshot-dir ./shots
```

---

## Batch Execution

For complex workflows, batch is faster (single process):
```bash
agent-browser batch \
  "open https://example.com" \
  "snapshot -i" \
  "click @e1" \
  "fill @e2 \"text\"" \
  "screenshot result.png"
```

---

## AI Chat

Natural language browser control:
```bash
agent-browser chat "open google.com and search for cats"
agent-browser chat  # Interactive REPL
```

Requires `AI_GATEWAY_API_KEY` environment variable.

---

## Cookies and Storage

```bash
agent-browser cookies                    # Get all cookies
agent-browser cookies set <name> <val>  # Set cookie
agent-browser cookies clear             # Clear cookies

agent-browser storage local             # localStorage
agent-browser storage session           # sessionStorage
```

---

## Network Interception

```bash
agent-browser network route <url> --abort                    # Block
agent-browser network route <url> --body '{"fake":true}'    # Mock
agent-browser network requests                               # View
```

---

## Troubleshooting

### Chrome exited early
```bash
agent-browser close --all
sleep 1
agent-browser open <url>
```

### Failed to create socket directory
```bash
mkdir -p /tmp/.agent-browser
```

### Install more libraries
```bash
apt-get download <package>
dpkg -x <package>.deb /tmp/pango_libs/
```

---

## Files Reference

- Wrapper: `./tools/agent-browser/bin/agent-browser.sh`
- Workflows: `./tools/agent-browser/workflows/`
- Config: `./tools/agent-browser/config/agent-browser.json`
- Integration: `./tools/agent-browser/INTEGRATION.md`
- Skill: `./skills/agent-browser/skill.md`