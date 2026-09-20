# Shopping List Design

**Goal:** Let the Open WebUI brewmaster agent manage a shopping list of brewing ingredients in Notion, so Andrea can build up an order and tick items off as they're purchased.

**Architecture:** A Notion database stores shopping list items. An Open WebUI tool provides CRUD access via the Notion API (same pattern as the brew log tool). No dedicated skill needed — the tool docstrings are sufficient for the agent to use it correctly.

**Tech Stack:** Python (Open WebUI tool), Notion API

**Status:** Implemented and deployed.

---

## 1. Notion Database Schema

Database "Shopping List", child of the Brewing page in Notion.
Database ID: `3e166956-14a6-81d6-b184-de76599bb4ae`

### Properties

| Property | Notion Type | Description |
|----------|-------------|-------------|
| Name | title | Ingredient name (e.g. "Crisp Best Pale Ale Malt") |
| Quantity | number | Numeric amount (e.g. 100, 1, 20) |
| Unit | select | Unit of measure (g, kg, packet) |
| Notes | rich_text | Context (e.g. "for London Porter", "general restocking") |
| Done | checkbox | Ticked when ordered; pending items have this unchecked |

### Merge Behaviour

When `shopping_list_add` is called for an ingredient that already has a pending (not Done) entry:

- **Quantity**: summed numerically. If units differ but are convertible (g/kg), the new quantity is normalized to the existing entry's unit before summing.
- **Notes**: appended with "; " separator.
- No new row is created — the existing row is updated.

Matching is case-insensitive on the Name property. Exact match only.

## 2. Open WebUI Tool

Source: `tools/shopping_list.py`

### Methods

#### `shopping_list_add(items)`

Add one or more ingredients to the shopping list. Each item merges with existing pending entries.

- `items`: list of dicts, each with `name` (str), `quantity` (float), `unit` (str), and optional `notes` (str)

#### `shopping_list_get()`

List all pending (not Done) items as a markdown table.

#### `shopping_list_done(names)`

Mark items as ordered.

- `names`: list of ingredient names

### Valves

- `notion_api_key` — same Notion integration token as the brew log tool
- `database_id` — `3e166956-14a6-81d6-b184-de76599bb4ae`

## 3. What This Does NOT Cover

- **Receiving inventory**: Adding purchased items to the Notion inventory databases is a separate workflow and tool.
- **Future brews**: Scoped out. Shopping list items stand on their own with notes for context.
- **Supplier integration**: No scraping or API integration with The Malt Miller.
- **Sync to markdown**: The `shopping-list.md` file in the beers repo is obsolete.
- **Price tracking**: No cost or pricing information.
- **Dedicated skill**: Not needed — the agent uses the tool correctly from docstrings alone.
