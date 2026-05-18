# awesome-design-md - Installation & Usage Guide

## What is DESIGN.md?

DESIGN.md is a design system document format introduced by Google Stitch. It's a plain markdown file that AI coding agents read to understand how to generate consistent UI matching a specific brand or style.

**Key advantage:** No Figma exports, no JSON schemas, no special tooling. Just drop a markdown file into your project and any AI agent understands your design instantly.

## Installation

The skill files are located at:
```
/home/user_aioc/workspace/skills/awesome-design-md/
```

No additional installation required - the design files are ready to use.

## Using a Design System

### Step 1: Choose a Design

Browse the available designs:
```bash
ls /home/user_aioc/workspace/skills/awesome-design-md/design-md/
```

Categories:
- `ai-llm/` - AI/LLM platforms (claude, elevenlabs, minimax, etc.)
- `developer-tools/` - IDEs and dev tools (cursor, vercel, raycast, etc.)
- `backend/` - Databases and DevOps (supabase, mongodb, sentry)
- `fintech/` - Finance and crypto (stripe, coinbase, kraken)
- `ecommerce/` - Retail and consumer (shopify, airbnb, apple)
- `productivity/` - SaaS tools (linear, notion, cal)

### Step 2: Copy to Your Project

```bash
# Example: Use Vercel's design for a new landing page
cp /home/user_aioc/workspace/skills/awesome-design-md/design-md/vercel/DESIGN.md ./DESIGN.md
```

### Step 3: Use in AI Conversation

Tell your AI agent:
```
Use DESIGN.md for this project. Build a landing page that matches the Vercel aesthetic.
```

## Design File Structure

Each DESIGN.md contains:

| Section | Description |
|---------|-------------|
| `colors` | Color palette with semantic names (primary, accent, surface) |
| `typography` | Font families, sizes, weights, line-heights |
| `components` | Button, card, input, navigation variants |
| `spacing` | Spacing scale tokens |
| `rounded` | Border radius scale |
| `layout` | Grid, max-width, section rhythm |
| `elevation` | Shadows and depth |
| `do-donts` | Design rules and anti-patterns |
| `responsive` | Breakpoints and behavior |

## Example: Building with DESIGN.md

### Original Request
"Build a pricing page for my SaaS"

### With DESIGN.md
1. Copy `design-md/stripe/DESIGN.md` to project root
2. Tell AI: "Create a pricing page following the Stripe DESIGN.md"
3. AI generates matching Stripe's signature purple gradients and elegant typography

## Preview Files

Many designs include:
- `preview.html` - Visual catalog with color swatches, components
- `preview-dark.html` - Same catalog with dark surfaces

Open these in browser to see the design system in action.

## Creating Custom DESIGN.md

### When to Create
- Building a new product with specific brand guidelines
- Need consistent design across multiple AI-generated pages
- Want to establish reusable design tokens

### How to Create
1. Start with an existing DESIGN.md as template
2. Define your color palette with semantic names
3. Set typography scale (display, headings, body, caption)
4. Define component variants (primary button, card, input)
5. Document do's and don'ts
6. Test with AI generation

## Tips for AI Agents

1. **Always reference tokens directly**: Use `{colors.primary}`, `{typography.body-md}` etc.
2. **Check component variants**: Each has default, hover, active, disabled states
3. **Use spacing scale**: Don't use arbitrary values, use tokens like `{spacing.lg}`
4. **Respect do-donts section**: These guardrails ensure consistent output

## Alternative: ui-ux-design-pro

For **generating custom design systems** (not copying existing), see:
```
/home/user_aioc/workspace/skills/ui-ux-design-pro/
```
This CLI generates design tokens, palettes, and styles from scratch based on requirements.

## Resources

- [Google Stitch DESIGN.md](https://stitch.withgoogle.com/docs/design-md/overview/)
- [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)