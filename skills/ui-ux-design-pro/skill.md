# ui-ux-design-pro Skill for AI Agent

## Description

**ui-ux-design-pro** is a senior-level AI skill for premium, production-grade UI/UX generation. It provides data-driven design intelligence with 107+ UI styles, 127+ color palettes, and 150+ reasoning rules.

**Source:** [saifyxpro/ui-ux-design-pro-skill](https://github.com/saifyxpro/ui-ux-design-pro-skill) (25 stars)

## Features

| Feature | Count |
|---------|-------|
| UI Styles | 107+ (Glassmorphism, Cyberpunk, Spatial UI, AI-Native, etc.) |
| Color Palettes | 127+ (SaaS, Fintech, Healthcare, E-commerce) |
| Font Pairings | 107+ (Google Fonts with mood keywords) |
| Reasoning Rules | 150+ (industry-specific design generation) |
| UX Guidelines | 150+ (accessibility, animation, forms) |
| Tech Stacks | 16 (React, Next.js, Vue, Angular, Svelte, Astro) |

## Prerequisites

- **Bun** 1.0+ (required runtime)

```bash
# Install Bun (macOS/Linux/WSL)
curl -fsSL https://bun.sh/install | bash

# Windows (PowerShell)
powershell -c "irm bun.sh/install.ps1 | iex"
```

## Installation

```bash
# Quick install via npx
npx skills add https://github.com/saifyxpro/ui-ux-design-pro-skill --skill ui-ux-design-pro

# Or clone manually
git clone https://github.com/saifyxpro/ui-ux-design-pro-skill.git
cd ui-ux-design-pro-skill/skills/ui-ux-design-pro/cli
bun install
```

## CLI Commands

```bash
# Search across all design databases
bun run skills/ui-ux-design-pro/cli/index.ts search "SaaS dashboard" --domain style

# Search for icons
bun run skills/ui-ux-design-pro/cli/index.ts icons "arrow"

# Generate full design system (Markdown output)
bun run skills/ui-ux-design-pro/cli/index.ts generate "fintech dashboard" --stack nextjs --output design.md

# Audit UI code quality
bun run skills/ui-ux-design-pro/cli/index.ts audit src/App.tsx
```

## Design Generation Workflow

```
1. AI analyzes project requirements
2. Orama search matches 96 product categories
3. Selected: 107 styles, 127 palettes, 107 fonts
4. Output: Complete DESIGN.md with tokens
```

## Token Presets

| Preset | Primary | Font | Radius |
|--------|---------|------|--------|
| `fintech` | #2563EB | Inter | 8px |
| `healthcare` | #059669 | Source Sans Pro | 12px |
| `ecommerce` | #DC2626 | Poppins | 8px |
| `saas` | #7C3AED | Inter | 12px |
| `education` | #2563EB | Nunito | 16px |
| `gaming` | #EF4444 | Orbitron | 4px |
| `luxury` | #1E293B | Playfair Display | 0px |
| `startup` | #8B5CF6 | DM Sans | 12px |

## 107 UI Styles

Examples:
- Minimalism & Swiss Style
- Glassmorphism
- Neumorphism
- Brutalism
- 3D & Hyperrealism
- Dark Mode (OLED)
- Claymorphism
- Aurora UI
- Spatial UI (VisionOS)
- AI-Native UI
- Cyberpunk UI
- Data Brutalism

## AI Workflow

```
1. Analyze: "Build a fintech analytics dashboard"
2. Search: bun run cli/index.ts search "fintech dashboard"
3. Generate: bun run cli/index.ts generate "fintech dashboard" --stack nextjs
4. Apply: Use generated DESIGN.md for UI generation
```

## Audit Command

Detect AI hallucinations in UI code:

```bash
# Fail test (expects errors)
/bun run cli/index.ts audit test/audit_fail.tsx

# Pass test (expects success)
bun run cli/index.ts audit test/audit_pass.tsx
```

Detects: Tailwind interpolation, hallucinated utilities, low contrast, layout shifts, accessibility issues.

## Files Location

```
/home/user_aioc/workspace/skills/ui-ux-design-pro/skills/ui-ux-design-pro/
├── SKILL.md          # Main prompt instructions
├── cli/              # Bun CLI with Orama search
│   ├── index.ts      # Entry point
│   ├── commands/     # search, generate, icons, audit
│   └── data/          # 27 CSV databases (1,875+ rows)
└── references/       # 11 design methodology docs
```

## Notes

- Recommended models: GPT-5.3 Codex xhigh or Gemini 3.0 Pro
- Works with: Claude, Cursor, Windsurf, Copilot, Antigravity, Cline
- Generates React/Tailwind code snippets
- Includes WCAG accessibility notes