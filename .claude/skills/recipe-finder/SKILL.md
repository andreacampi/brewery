---
name: recipe-finder
description: Search local recipe cache by ingredient, style, ABV, or IBU. Use when finding recipes that match available ingredients, looking for specific beer styles, or filtering by bitterness/alcohol level. For fetching new recipes from online, use community-recipes instead.
allowed-tools: Read, Bash(jq:*), Bash(grep:*), Bash(cat:*)
---

# Recipe Finder

Search the beer recipe collection by various criteria.

## Data Structure

- **`.cache/recipes/recipes.json`** - Collection with metadata only: id, beer_name, ibu, abv, style
- **`.cache/recipes/{id}.json`** - Individual recipe files with full details including ingredients

## Quick Filters (metadata)

Filter recipes by IBU, ABV, or style using `.cache/recipes/recipes.json`:

```bash
# Filter by IBU (low = under 30)
jq '.results[] | select(.ibu < 30) | {id, beer_name, ibu, abv}' .cache/recipes/recipes.json

# Filter by style
jq '.results[] | select(.beer.style.name | test("Wheat|Weizen"; "i")) | {id, beer_name, ibu, style: .beer.style.name}' .cache/recipes/recipes.json

# Filter by ABV
jq '.results[] | select((.abv | tonumber) < 6) | {id, beer_name, abv}' .cache/recipes/recipes.json
```

## Deep Filters (ingredients)

For ingredient searches, use grep first to find candidates efficiently:

```bash
# Find recipes containing US-05 yeast
grep -l "US-05" .cache/recipes/[0-9]*.json

# Find recipes with a specific fermentable
grep -l "Maris Otter" .cache/recipes/[0-9]*.json

# Find recipes with a specific hop
grep -l "Mosaic" .cache/recipes/[0-9]*.json
```

Then use jq on matched files for details:

```bash
# Get yeast from a recipe
jq '.fermenting[0].yeast[]?.ingredient_name' .cache/recipes/699675.json

# Get fermentables from a recipe
jq '[.mashing[].ingredient_additions[].ingredient_name]' .cache/recipes/699675.json

# Get hops from a recipe
jq '[.boiling[].hops[].ingredient_name]' .cache/recipes/699675.json
```

## Combined Workflow

Example: Find low-IBU recipes using US-05 yeast:

```bash
# 1. Get IDs of low-IBU recipes from metadata
jq -r '.results[] | select(.ibu < 30) | .id' .cache/recipes/recipes.json > /tmp/low_ibu_ids.txt

# 2. Use grep to find US-05 recipes (fast)
grep -l "US-05" .cache/recipes/[0-9]*.json > /tmp/us05_files.txt

# 3. Find intersection and get details
for id in $(cat /tmp/low_ibu_ids.txt); do
  if grep -q "${id}.json" /tmp/us05_files.txt; then
    jq '{id, beer_name, ibu, abv}' .cache/recipes/${id}.json
  fi
done
```

## Notes

- "Low IBU" = under 30 IBU (mild bitterness suitable for those who don't like bitter beers)
- Always use grep before jq for ingredient searches to avoid reading all files
