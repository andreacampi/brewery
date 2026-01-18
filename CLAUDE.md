# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Dalston Rooftop Brewery - homebrewing recipes and inventory management.

**What we brew:** Beer, mead, and soft drinks (ginger beer, etc.)

**Recipe sources:**
- Community recipes from MiniBrew (cached in `.cache/recipes/`)
- Our own custom recipes (in `recipes/`)

## Data Structure

**Community recipes** (MiniBrew cache):
- `.cache/recipes/recipes.json` - Recipe list (metadata)
- `.cache/recipes/{id}.json` - Individual recipe files

**Custom recipes** (our own):
- `recipes/{name}.json` - Our custom recipes

## Recipe JSON Schema

Each recipe contains:
- **Metadata**: `id`, `beer_id`, `beer_name`, `version_name`, `shared`, `favourite`
- **Beer stats**: `abv`, `ibu`, `srm`, `og`, `fg`, `kcal`
- **Water**: `water_amount`, `kettle_water`
- **Mashing**: Multi-step mash schedules with fermentable ingredients (grains, malts)
- **Boiling**: Duration and hop additions with alpha acid percentages
- **Fermenting**: Primary/secondary/conditioning stages with yeast and temperature steps
- **While Fermenting**: Dry hop and adjunct additions
- **Style/Brewer**: Beer style category and brewer profile info

## Brew Tracking

**Brew Log**: [brew-log.md](brew-log.md) - Authoritative record of all brews with lot numbers, including both metadata (stats, ingredients, pitch) and detailed day-by-day process logs.

**Lot Number System**: Each brew is assigned a sequential lot number (LOT XXX) across all products for traceability. Bottling variants use letter suffixes (e.g., LOT 097-A, LOT 097-B).

**Street Names**: Marketing names for specific brew types (e.g., "Wilton Way" for Citrus Mead, "Navarino Road" for Hibiscus Mead). See [naming.md](naming.md) for conventions.

## Planning

See [future-brews.md](future-brews.md) for upcoming brews and [shopping-list.md](shopping-list.md) for ingredients to buy.

## Marketing Website (GitHub Pages)

**Location:** `docs/` directory

**IMPORTANT:** The `docs/` directory contains DERIVED content generated from authoritative sources (brew-log.md, recipes/*.json). Never use it as reference material.

### Structure

```
docs/
├── index.html           # List of all brews
├── style.css            # Shared stylesheet
└── {batch-slug}/
    └── index.html       # Individual batch page
```

### Design Rules

**Color Palette (from brewery logo):**
- Navy blue: `#1a2838`
- Warm beige: `#d4c5a9`
- Sunset orange: `#ff8c42`, `#ff6b35`
- Background: `#f5f1e8`

**Visual Distinctions:**
- Meads: 🍯 emoji + warm beige gradient background
- Beers: 🍺 emoji + slight orange gradient background

### Content Rules

**Index Page:**
- Only show bottled brews (exclude fermenting batches)
- Display: ABV, Brew date, Bottling date
- No IBU for meads (only for beers)
- Status badges: Only "Gone!" for consumed batches (no "Bottled" badges)

**Detail Pages:**
- Stats: ABV only (no OG, FG, or Status)
- No "Brewing Details" section
- Ingredients section:
  - Remove all quantities (grams, counts, volumes)
  - Remove water
  - Remove yeast nutrients
  - Remove fining agents
  - Remove obvious processing details (e.g., "steeped")
  - Keep descriptive details that add flavor context (e.g., "caramelized", "with zest")
  - Use simple headings: "Ingredients" not "Key Ingredients"

**Tone:**
- Simple, friendly language
- Focus on flavor and character, not technical brewing data
- Marketing-focused, not brewer-focused

