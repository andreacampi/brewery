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

## Brew Day Workflows

**Generating Brew Sheets:**
- Use the `brew-day-instructions` skill (not manual markdown generation)
- Syntax: `/brew-day-instructions <recipe-path>`
- Outputs PDF to `output/` directory for printing
- Example: `/brew-day-instructions .cache/recipes/648432.json`

## Post-Fermentation Handling

**CRITICAL:** Beer and mead require different handling due to oxygen sensitivity.

### Beer (Oxygen-Sensitive)
**Workflow:** Ferment in keg → Either tap and drink OR bottle directly to crown bottles with CO2 gun

- **Never** rack beer to intermediate containers - oxygen exposure degrades hop character and freshness
- Two options after fermentation:
  1. Tap from keg and drink fresh
  2. Bottle directly to crown bottles using CO2 gun to prevent oxygen exposure
- No intermediate conditioning bottles

### Mead (Oxygen-Tolerant)
**Workflow:** Ferment → Rack to 1L screw-top bottles → Taste/evaluate → Final crown bottles for aging

- **Can** rack to intermediate containers - aeration is acceptable
- Use 1L screw-top bottles for conditioning and tasting
- Easy to sample and evaluate before final bottling
- Final bottling to crown bottles only after tasting confirms readiness

**Brew Log Interpretation:**
- Beer: "Still in keg" = awaiting tap/bottle decision
- Mead: "Racked to 1L bottles" = intermediate conditioning stage, not final bottling

## MiniBrew API

**Note:** This is reverse-engineered from the MiniBrew web portal. No official API documentation exists.

**Base URL:** `https://api.minibrew.io/`

**Required Headers:**
- `Client: Breweryportal` (exact value required)
- `Authorization: Bearer <session_token>` (for queries)

**Credentials:** Stored in `auth.yaml` (not committed):
- `email` - account email
- `auth_token` - long-lived auth token (for TOKEN header)
- `session_token` - short-lived request token (for Bearer header)
- `user_id` - user ID for filtering results

**Known Endpoints:**

- `/v1/devices` - List brewing devices
  - Returns device information including references to current/recent brew sessions
  - Example: Device shows session ID 75556 (LOT 099)

- `/v1/sessions/{id}/` - Brew session details
  - Tracks actual brew performed on MiniBrew device
  - Contains phase information, temperatures, timings, etc.
  - Example: `/v1/sessions/75556/` = LOT 099 (Double Hazy Jane)

- `/v1/sessions/{id}/user_actions/` - List all instruction guides
  - Returns 58 different manual instruction guides (e.g., "Add brew water", "Connect pressurizer", "Check Carbonation")
  - Each user action has step-by-step instructions with images/videos
  - Detail endpoint: `/v1/sessions/{id}/user_actions/{action_id}/`
  - **Note:** User action IDs (e.g., 31, 65) are global MiniBrew instruction IDs, not session-specific
  - **Unknown:** How the web app determines which actions to show at each stage (possibly based on device `process_state` or brewing profile)

- `/v1/recipes/{id}/` - User's own recipes
  - Personal recipes (not shared community recipes)
  - Different from `/v1/shared_recipes/`

- `/v1/shared_recipes/` - Community recipes
  - Public recipes shared by other users
  - Cached locally in `.cache/recipes/` (see community-recipes skill)
  - List endpoint: `/v1/shared_recipes/?limit=1000`
  - Detail endpoint: `/v1/shared_recipes/{id}/`

**Authentication:** See community-recipes skill for token refresh flow.

### Response Examples

**`/v1/devices/` response:**
```json
[
  {
    "uuid": "2130K0547-6RNKMJ14",
    "serial_number": "2130K0547-6RNKMJ14",
    "current_state": 1,
    "process_type": 4,
    "process_state": 94,
    "user_action": 0,
    "active_session": 75556,
    "connection_status": 1,
    "last_time_online": "2026-01-24T20:35:21Z",
    "software_version": "3.2.3, idf-v4.2-50-g11005797d",
    "custom_name": "Keg 2130K0547",
    "device_type": 1,
    "image": "https://minibrew.s3.amazonaws.com/static/devices/keg.png",
    "last_process_state_change": "2026-01-27T18:53:46Z",
    "process_estimate_remaining": "2026-01-27T19:25:38.287223Z",
    "text": "is fermenting",
    "updating": false
  }
]
```

**Key fields:**
- `active_session` - ID of current brew session (null if idle)
- `text` - Human-readable status (e.g., "is fermenting", "is ready to start a fresh brew")
- `process_type` - Type of process (4 = fermenting)
- `process_state` - Detailed state within process
- `connection_status` - 0 = offline, 1 = online
- `device_type` - 0 = base unit, 1 = keg

**`/v1/sessions/{id}/` response:**
```json
{
  "id": 75556,
  "profile": 3832,
  "beer": {
    "id": 17196,
    "name": "Double Hazy Jane",
    "image": null,
    "style_name": "New England IPA"
  },
  "device": {
    "uuid": "2130K0547-6RNKMJ14",
    "device_type": 1,
    "connection_status": 1,
    "process_type": 4,
    "process_state": 94
  },
  "status": 1,
  "beer_recipe_id": 1442881,
  "beer_recipe_version": "1",
  "brew_timestamp": 1767527648.349407,
  "original_gravity": null,
  "is_brewpack": false
}
```

**Key fields:**
- `beer_recipe_id` - User's personal recipe ID (use with `/v1/recipes/{id}/`)
- `beer.name` - Name of the beer being brewed
- `status` - Session status (1 = active)
- `brew_timestamp` - Unix timestamp when brew started
- `device.process_type` and `device.process_state` - Current phase

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

