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

## Planning

See [future-brews.md](future-brews.md) for upcoming brews and [shopping-list.md](shopping-list.md) for ingredients to buy.

