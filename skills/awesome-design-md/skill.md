# awesome-design-md Skill for AI Agent

## Description

Collection of DESIGN.md files inspired by popular brand design systems. Drop one into your project and tell your AI agent "build me a page that looks like this" for pixel-perfect UI matching.

**Source:** [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (70.8k stars)

## Concept

DESIGN.md is a concept from Google Stitch - a plain-text design system document that AI agents read to generate consistent UI.

| File | Who reads it | What it defines |
|------|-------------|-----------------|
| `AGENTS.md` | Coding agents | How to build the project |
| `DESIGN.md` | Design agents | How the project should look and feel |

## Installation

```bash
# Skill files are in workspace/skills/awesome-design-md/
# No additional installation needed
```

## How to Use

1. Browse available DESIGN.md files in `design-md/` directory
2. Copy desired DESIGN.md into your project root
3. Tell AI agent to use it

## Available Designs (71+)

### AI & LLM Platforms
- **claude** - Anthropic's AI assistant. Warm terracotta accent
- **minimax** - Bold dark interface with neon accents
- **elevenlabs** - Dark cinematic UI, audio-waveform aesthetics
- **ollama** - Terminal-first, monochrome simplicity
- **replicate** - Clean white canvas, code-forward
- **opencode.ai** - Developer-centric dark theme
- **voltagent** - Void-black canvas, emerald accent

### Developer Tools & IDEs
- **cursor** - AI-first code editor. Sleek dark interface
- **vercel** - Black and white precision, Geist font
- **expo** - React Native platform. Dark theme
- **raycast** - Productivity launcher. Vibrant gradients
- **lovable** - AI full-stack builder. Playful gradients
- **warp** - Modern terminal. Dark IDE-like

### Backend & DevOps
- **supabase** - Dark emerald theme, code-first
- **mongodb** - Green leaf branding
- **sentry** - Dark dashboard, pink-purple accent
- **posthog** - Playful hedgehog branding
- **clickhouse** - Yellow-accented, technical docs

### Fintech & Crypto
- **stripe** - Signature purple gradients, weight-300 elegance
- **coinbase** - Clean blue identity, trust-focused
- **binance** - Bold yellow on monochrome
- **kraken** - Purple-accented dark UI
- **revolut** - Sleek dark interface, gradient cards

### E-commerce & Retail
- **shopify** - Dark-first cinematic, neon green accent
- **airbnb** - Warm coral accent, photography-driven
- **apple** - Premium white space, SF Pro
- **spotify** - Vibrant green on dark

### Productivity & SaaS
- **linear** - Ultra-minimal, precise, purple accent
- **notion** - Warm minimalism, serif headings
- **cal** - Open-source scheduling. Clean neutral UI
- **mintlify** - Clean, green-accented, reading-optimized

## Quick Reference

```bash
# List all available design systems
ls skills/awesome-design-md/design-md/

# Copy a design to your project
cp skills/awesome-design-md/design-md/vercel/DESIGN.md ./DESIGN.md

# Then tell AI agent:
# "Build this page using DESIGN.md from Vercel"
```

## Structure of DESIGN.md

Each DESIGN.md contains:

1. **Visual Theme & Atmosphere** - Mood, density, philosophy
2. **Color Palette & Roles** - Semantic names + hex + function
3. **Typography Rules** - Font families, hierarchy table
4. **Component Stylings** - Buttons, cards, inputs, nav
5. **Layout Principles** - Spacing scale, grid, whitespace
6. **Depth & Elevation** - Shadow system, surface hierarchy
7. **Do's and Don'ts** - Design guardrails
8. **Responsive Behavior** - Breakpoints, touch targets
9. **Agent Prompt Guide** - Quick reference, prompts

## Related Skill

For **generating custom** design systems, see also:
- `skills/ui-ux-design-pro/` - 107 UI styles, 127 palettes, design generation CLI