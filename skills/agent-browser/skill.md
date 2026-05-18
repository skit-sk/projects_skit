# agent-browser Skill for AI Agent

## Description

**agent-browser** is a CLI tool for browser automation designed for AI agents. It uses references (`@e1`, `@e2`) instead of CSS selectors for more reliable element interaction.

## Current Configuration

- **CLI**: agent-browser v0.26.0 at `/home/user_aioc/.local/lib/node_modules/agent-browser/bin/agent-browser-linux-x64`
- **Chrome**: agent-browser's own Chrome at `/tmp/.agent-browser/browsers/chrome-148.0.7778.97/chrome`
- **Libraries**: Chrome dependencies at `/tmp/pango_libs/usr/lib/x86_64-linux-gnu/`
- **Wrapper**: `/home/user_aioc/workspace/tools/agent-browser/bin/agent-browser.sh` (RECOMMENDED)

## How to Use

### ALWAYS use the wrapper script:
```bash
./tools/agent-browser/bin/agent-browser.sh <command>
```

This automatically handles:
- Library paths (`LD_LIBRARY_PATH`)
- State directory (`AGENT_BROWSER_STATE_DIR`)
- Chrome executable path (`--executable-path`)

---

## AI Agent Command Reference

### Navigation
| Command | Description | Example |
|---------|-------------|---------|
| `open <url>` | Open URL in browser | `open https://habr.com` |
| `goto <url>` | Same as open | `goto https://example.com` |
| `back` | Go back | `back` |
| `forward` | Go forward | `forward` |
| `reload` | Reload page | `reload` |
| `close` | Close browser | `close` |

### Interaction (using refs from snapshot)
| Command | Description | Example |
|---------|-------------|---------|
| `snapshot [-i]` | Get interactive elements with refs | `snapshot -i` |
| `click @eN` | Click element by ref | `click @e2` |
| `fill @eN "text"` | Fill input by ref | `fill @e3 "admin@example.com"` |
| `hover @eN` | Hover element | `hover @e1` |
| `focus @eN` | Focus element | `focus @e2` |
| `type @eN "text"` | Type character by character | `type @e3 "hello"` |
| `press @eN Enter` | Press key | `press @e2 Enter` |

### Semantic Locators (alternative to refs)
```bash
find role button click --name "Submit"
find text "Sign In" click
find label "Email" fill "test@test.com"
find placeholder "Search" fill "query"
```

### Screenshot
```bash
screenshot                           # Simple screenshot
screenshot --annotate                # With numbered element labels
screenshot page.png                  # Save to file
```

### Batch Execution (recommended for complex workflows)
```bash
batch "open <url>" "snapshot -i" "click @e1" "screenshot"
```

### Example AI Workflow

```
1. agent-browser.sh open https://habr.com
   → Opens Habr, returns: ✓ Publications / My feed / Habr, https://habr.com/en/feed/

2. agent-browser.sh snapshot -i
   → Returns list of elements with refs:
     - button "Login" [ref=e12]
     - link "All streams" [ref=e9]

3. agent-browser.sh click @e12
   → Clicks Login button

4. agent-browser.sh snapshot -i
   → Shows login form elements:
     - textbox "Email" [ref=e1]
     - textbox "Password" [ref=e2]
     - button "Sign In" [ref=e3]

5. agent-browser.sh fill @e1 "admin@example.com"
   agent-browser.sh fill @e2 "password"
   agent-browser.sh click @e3
   → Fills and submits login form
```

---

## Snapshot Flags for AI Optimization

| Flag | Effect | Use Case |
|------|--------|----------|
| `-i` | Interactive elements only | **Default for AI** - much smaller output |
| `-c` | Compact - remove empty elements | Reduce tokens |
| `-d N` | Limit tree depth to N | Shallow pages |
| `--urls` | Include href URLs | Link navigation |

**Recommended for AI:**
```bash
snapshot -i          # Interactive elements only
snapshot -i --urls   # + link URLs
snapshot -i -c -d 5  # Compact, depth 5
```

---

## Troubleshooting

### "daemon already running"
```bash
agent-browser.sh close --all
```

### "Chrome exited early"
```bash
agent-browser.sh close --all
sleep 1
agent-browser.sh open <url>
```

### "Failed to create socket directory"
```bash
mkdir -p /tmp/.agent-browser
export AGENT_BROWSER_STATE_DIR=/tmp/.agent-browser
```

---

## When to Use

- AI agent needs to interact with web pages
- Testing frontend components autonomously
- Web scraping with reliable element selection
- Taking screenshots of pages

## Files

- Wrapper: `./tools/agent-browser/bin/agent-browser.sh`
- Workflows: `./tools/agent-browser/workflows/`
- Config: `./tools/agent-browser/config/agent-browser.json`
- Docs: `./tools/agent-browser/INTEGRATION.md`

## Alternative: Lightpanda (experimental)

For lightweight browsing without full Chrome:
```bash
# Start Lightpanda server
/tmp/lightpanda serve --port 9322 &

# Use with agent-browser
agent-browser open <url> --cdp ws://localhost:9322
```

Note: Lightpanda has limited features but works in constrained environments.