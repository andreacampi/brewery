---
name: inventory
description: Manage ingredient inventory and bottle cellar in Notion. Use when checking stock levels, adding purchases, updating quantities after brewing, checking expiration dates, or tracking bottled beers.
---

# Ingredient Inventory & Cellar

Manage brewing ingredients and bottled beers in Notion.

## Setup (First-Time Use)

**Before using this skill, check if `notion.yaml` exists and is complete.**

### Step 1: Check notion.yaml

Read `notion.yaml` and verify it contains:
- `ingredients_page` - parent page URL
- `databases.fermentables.data_source_id`
- `databases.hops.data_source_id`
- `databases.yeast.data_source_id`
- `databases.flavoring.data_source_id`
- `databases.additives.data_source_id`
- `cellar.data_source_id`

If the file doesn't exist or is missing entries, proceed to Step 2.

### Step 2: Ask user for parent page

Ask the user:
> "Where should I create the inventory databases? You can:
> 1. Provide a Notion page URL to use as parent
> 2. Let me create a new 'Brewing Inventory' page"

Use `mcp__notion__notion-search` to help them find existing pages if needed.

### Step 3: Create parent page (if needed)

If creating new:
```
mcp__notion__notion-create-pages
- parent: {"type": "workspace"}
- pages: [{"properties": {"title": "Brewing Inventory"}}]
```

### Step 4: Create databases

Create each database under the parent page. Use `mcp__notion__notion-create-database` with the schemas defined below.

**Fermentables:**
```
mcp__notion__notion-create-database
- parent: {"type": "page_id", "page_id": "<parent_page_id>"}
- title: "Fermentables"
- properties: {
    "Name": {"type": "title"},
    "Inventory Amount": {"type": "number", "number": {"format": "number"}},
    "Cost (£/kg)": {"type": "number", "number": {"format": "pound"}},
    "Sub-Category": {"type": "select", "select": {"options": [
      {"name": "Base Malt"}, {"name": "Crystal Malt"}, {"name": "Specialty Malt"}, {"name": "Adjunct"}
    ]}},
    "Dry Yield %": {"type": "number", "number": {"format": "percent"}},
    "Moisture %": {"type": "number", "number": {"format": "percent"}},
    "SRM": {"type": "number", "number": {"format": "number"}},
    "Brand/Supplier": {"type": "rich_text"},
    "Country of Origin": {"type": "select"},
    "Purchase Date": {"type": "date"},
    "Expiration Date": {"type": "date"}
  }
```

**Hops:**
```
mcp__notion__notion-create-database
- parent: {"type": "page_id", "page_id": "<parent_page_id>"}
- title: "Hops"
- properties: {
    "Name": {"type": "title"},
    "Inventory Amount": {"type": "number", "number": {"format": "number"}},
    "Cost (£/g)": {"type": "number", "number": {"format": "pound"}},
    "Sub-Category": {"type": "select", "select": {"options": [
      {"name": "Bittering"}, {"name": "Aroma"}, {"name": "Dual Purpose"}
    ]}},
    "Alpha Acid %": {"type": "number", "number": {"format": "percent"}},
    "Harvest Year": {"type": "number", "number": {"format": "number"}},
    "Brand/Supplier": {"type": "rich_text"},
    "Country of Origin": {"type": "select"},
    "Purchase Date": {"type": "date"},
    "Expiration Date": {"type": "date"}
  }
```

**Yeast:**
```
mcp__notion__notion-create-database
- parent: {"type": "page_id", "page_id": "<parent_page_id>"}
- title: "Yeast"
- properties: {
    "Name": {"type": "title"},
    "Inventory Amount": {"type": "number", "number": {"format": "number"}},
    "Cost (£/g)": {"type": "number", "number": {"format": "pound"}},
    "Sub-Category": {"type": "select", "select": {"options": [
      {"name": "Ale"}, {"name": "Lager"}, {"name": "Wine"}, {"name": "Mead"}
    ]}},
    "Attenuation %": {"type": "number", "number": {"format": "percent"}},
    "Flocculation": {"type": "select", "select": {"options": [
      {"name": "Low"}, {"name": "Medium"}, {"name": "High"}
    ]}},
    "Pitch Rate (g/L)": {"type": "number", "number": {"format": "number"}},
    "Temperature Range": {"type": "rich_text"},
    "Brand/Supplier": {"type": "rich_text"},
    "Country of Origin": {"type": "select"},
    "Purchase Date": {"type": "date"},
    "Expiration Date": {"type": "date"}
  }
```

**Flavoring:**
```
mcp__notion__notion-create-database
- parent: {"type": "page_id", "page_id": "<parent_page_id>"}
- title: "Flavoring"
- properties: {
    "Name": {"type": "title"},
    "Inventory Amount": {"type": "number", "number": {"format": "number"}},
    "Cost (£/g)": {"type": "number", "number": {"format": "pound"}},
    "Sub-Category": {"type": "select", "select": {"options": [
      {"name": "Spice"}, {"name": "Fruit"}
    ]}},
    "Brand/Supplier": {"type": "rich_text"},
    "Country of Origin": {"type": "select"},
    "Purchase Date": {"type": "date"},
    "Expiration Date": {"type": "date"}
  }
```

**Additives:**
```
mcp__notion__notion-create-database
- parent: {"type": "page_id", "page_id": "<parent_page_id>"}
- title: "Additives"
- properties: {
    "Name": {"type": "title"},
    "Inventory Amount": {"type": "number", "number": {"format": "number"}},
    "Cost (£/g)": {"type": "number", "number": {"format": "pound"}},
    "Sub-Category": {"type": "select", "select": {"options": [
      {"name": "Adjunct"}, {"name": "Water Mineral"}, {"name": "Nutrients"}
    ]}},
    "Brand/Supplier": {"type": "rich_text"},
    "Country of Origin": {"type": "select"},
    "Purchase Date": {"type": "date"},
    "Expiration Date": {"type": "date"}
  }
```

**Cellar:**
```
mcp__notion__notion-create-database
- parent: {"type": "page_id", "page_id": "<parent_page_id>"}
- title: "Cellar"
- properties: {
    "Name": {"type": "title"},
    "Category": {"type": "select", "select": {"options": [
      {"name": "Beer"}, {"name": "Mead"}, {"name": "Ginger Beer"}, {"name": "Other"}
    ]}},
    "Style": {"type": "rich_text"},
    "Quantity": {"type": "number", "number": {"format": "number"}},
    "Volume": {"type": "number", "number": {"format": "number"}},
    "ABV": {"type": "number", "number": {"format": "percent"}},
    "Brew Date": {"type": "date"},
    "Bottled Date": {"type": "date"},
    "Best Before": {"type": "date"},
    "Status": {"type": "select", "select": {"options": [
      {"name": "Conditioning"}, {"name": "Ready"}, {"name": "Aging"}
    ]}},
    "Location": {"type": "rich_text"},
    "Notes": {"type": "rich_text"}
  }
```

### Step 5: Save to notion.yaml

After creating databases, save the IDs to `notion.yaml`:

```yaml
# Notion database IDs and URLs
# This file is not committed - add your own IDs

ingredients_page: <parent_page_url>

databases:
  fermentables:
    url: <database_url>
    data_source_id: <data_source_id>
  hops:
    url: <database_url>
    data_source_id: <data_source_id>
  yeast:
    url: <database_url>
    data_source_id: <data_source_id>
  flavoring:
    url: <database_url>
    data_source_id: <data_source_id>
  additives:
    url: <database_url>
    data_source_id: <data_source_id>

cellar:
  url: <database_url>
  data_source_id: <data_source_id>

naming_page: <naming_page_url>  # optional, for bottle naming conventions
```

---

## Daily Use

Once setup is complete, read `notion.yaml` to get database IDs for operations below.

## Error Handling: Notion API Timeouts

**CRITICAL: If any Notion MCP request times out or fails:**

1. Retry **AT MAXIMUM** once
2. If the retry also fails, prompt the user to reconnect to the Notion MCP server
3. **NEVER** try workarounds such as asking the user to paste information manually
4. If you are in plan mode and cannot continue without Notion data, you **MUST** suggest to the user that you need to exit plan mode

**Example user instruction when timeout occurs:**
> "The Notion API request timed out. Please run the `/mcp` command to reconnect to the Notion server, then let me know when you're ready to retry."

## Ingredient Databases

- **Fermentables** - grains, malts, sugars
- **Hops** - bittering and aroma hops
- **Yeast** - ale, lager, wine, mead yeasts
- **Flavoring** - spices, fruit
- **Additives** - water minerals, nutrients, adjuncts

## Common Schema (all ingredient databases)

| Property | Type | Notes |
|----------|------|-------|
| `Name` | title | Required |
| `Inventory Amount` | number | In kg (Fermentables) or g (all others) |
| `Expiration Date` | date | Use `date:Expiration Date:start` when creating |
| `Purchase Date` | date | Use `date:Purchase Date:start` when creating |
| `Brand/Supplier` | text | e.g., "Fermentis", "Wyeast" |
| `Country of Origin` | select | Germany, United States, Belgium, etc. |

## Type-Specific Properties

**Fermentables:** `Cost (£/kg)`, `Sub-Category` (Base Malt, Crystal Malt, Specialty Malt, Adjunct), `Dry Yield %`, `Moisture %`, `SRM`

**Hops:** `Cost (£/g)`, `Sub-Category` (Bittering, Aroma, Dual Purpose), `Alpha Acid %`, `Harvest Year`

**Yeast:** `Cost (£/g)`, `Sub-Category` (Ale, Lager, Wine, Mead), `Attenuation %`, `Flocculation`, `Pitch Rate (g/L)`, `Temperature Range`

**Flavoring:** `Cost (£/g)`, `Sub-Category` (Spice, Fruit)

**Additives:** `Cost (£/g)`, `Sub-Category` (Adjunct, Water Mineral, Nutrients)

## Creating Ingredients

```
mcp__notion__notion-create-pages with:
- parent: {"type": "data_source_id", "data_source_id": "<data_source_id>"}
- pages: [{"properties": {...}}]
```

Date properties require expanded format:
- `"date:Expiration Date:start": "2026-08-01"`
- `"date:Expiration Date:is_datetime": 0`

### Example: Add new hops

```
mcp__notion__notion-create-pages
- parent: {"type": "data_source_id", "data_source_id": "<from notion.yaml>"}
- pages: [{"properties": {
    "Name": "Citra",
    "Inventory Amount": 100,
    "Alpha Acid %": 12.5,
    "Sub-Category": "Dual Purpose",
    "Brand/Supplier": "Yakima Chief",
    "Country of Origin": "United States",
    "date:Purchase Date:start": "2026-01-15",
    "date:Purchase Date:is_datetime": 0,
    "date:Expiration Date:start": "2027-01-15",
    "date:Expiration Date:is_datetime": 0
  }}]
```

## Updating Ingredients

```
mcp__notion__notion-update-page with:
- data: {"page_id": "<id>", "command": "update_properties", "properties": {...}}
```

### Example: Update quantity after brewing

```
mcp__notion__notion-update-page
- data: {
    "page_id": "<ingredient_page_id>",
    "command": "update_properties",
    "properties": {"Inventory Amount": 50}
  }
```

## Cellar (Bottle Inventory)

Tracks bottled homebrew inventory (see `notion.yaml` for database URL and ID):
- **Category**: Beer, Mead, Ginger Beer, Other
- **Style**: Beer style name
- **Quantity**: Number of bottles
- **Volume**: Bottle size (ml)
- **ABV**: Alcohol percentage
- **Dates**: Brew Date, Bottled Date, Best Before
- **Status**: Conditioning, Ready, etc.
- **Location**: Where stored
- **Notes**: Tasting notes, etc.

## Naming Conventions

Maps street names to brew types (e.g., "Junction" = Basic Mead). See `naming.md` for the full list.

## Known Limitations

- **Page icons cannot be set via MCP** - must be set manually in Notion UI
  (see: https://github.com/makenotion/notion-mcp-server/issues/165)
