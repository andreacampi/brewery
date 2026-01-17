# Dalston Rooftop Brewery

Homebrewing recipes and inventory management, powered by [Claude Code](https://claude.ai/code).

## What We Brew

- Beer (IPAs, lagers, Belgian styles, and more)
- Mead
- Soft drinks (ginger beer, etc.)

## Features

This repo includes Claude Code skills for:

- **recipe-finder** - Search cached recipes by ingredient, style, ABV, or IBU
- **community-recipes** - Fetch and sync recipes from MiniBrew
- **inventory** - Manage ingredient inventory and bottle cellar in Notion

## Setup

1. Clone the repo
2. Copy credential templates:
   ```bash
   cp auth.yaml.example auth.yaml      # MiniBrew API credentials
   cp notion.yaml.example notion.yaml  # Notion database IDs
   ```
3. Fill in your credentials
4. Run Claude Code - the inventory skill will help create Notion databases if needed

## Structure

```
.cache/recipes/       # Cached MiniBrew community recipes
recipes/              # Our custom recipes
.claude/skills/       # Claude Code skills
```

## License

Personal project - recipes are shared from the MiniBrew community.
