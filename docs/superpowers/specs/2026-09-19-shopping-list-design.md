# Shopping List Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the Open WebUI brewmaster agent manage a shopping list of brewing ingredients in Notion, so Andrea can build up an order and tick items off as they're purchased.

**Architecture:** A new Notion database stores shopping list items. A new Open WebUI tool provides CRUD access via the Notion API (same pattern as the existing brew log tool). A new Open WebUI skill triggers the tool when Andrea asks about ordering or adding items.

**Tech Stack:** Python (Open WebUI tool), Notion API, Open WebUI skills

**Spec:** This document.

## Global Constraints

- Follow the existing brew log tool pattern exactly (Valves for API key and database ID, httpx for HTTP, Pydantic for config)
- The tool runs inside Open WebUI — no k8s deployment, no CronJob, no oikb sync needed
- Amount is text, not numeric — ingredients use mixed units (g, kg, packets)
- Merging: when adding an ingredient that already exists as pending, combine the amounts and append notes rather than creating a duplicate
- The tool must handle the `shopping_list_done` operation on multiple items in a single call
- No integration with The Malt Miller or any supplier website
- The `shopping-list.md` file in the beers repo becomes obsolete once this ships — it will not be kept in sync

---

## 1. Notion Database Schema

A new Notion database called "Shopping List" in Andrea's brewing workspace.

### Properties

| Property | Notion Type | Description |
|----------|-------------|-------------|
| Name | title | Ingredient name (e.g. "Crisp Best Pale Ale Malt") |
| Amount | rich_text | Quantity with unit (e.g. "100g", "1 packet", "20kg") |
| Notes | rich_text | Context (e.g. "for London Porter", "general restocking") |
| Done | checkbox | Ticked when ordered; pending items have this unchecked |

Andrea creates this database manually in Notion and provides the database ID for the tool's Valves configuration.

### Merge Behaviour

When `shopping_list_add` is called for an ingredient that already has a pending (not Done) entry:

- **Amount**: append with " + " separator (e.g. "100g" + "200g" → "100g + 200g"). Do not attempt to parse or sum — units vary and may include free text.
- **Notes**: append with "; " separator (e.g. "for London Porter; for Kveik IPA").
- No new row is created — the existing row is updated.

Matching is case-insensitive on the Name property. Exact match only — no fuzzy matching or ingredient aliasing.

## 2. Open WebUI Tool

A single Python tool file following the brew log tool pattern.

### Tool Class: `Tools`

**Valves:**
- `notion_api_key` — Notion internal integration token
- `database_id` — Shopping List database ID

### Methods

#### `shopping_list_add(name, amount, notes="")`

Add an ingredient to the shopping list.

1. Query the database for pending items (Done = false) matching `name` (case-insensitive)
2. If a match exists, update it: append amount and notes per merge rules above
3. If no match, create a new page with Done = false
4. Return confirmation: "Added {amount} {name}" or "Merged with existing: {name} now {merged_amount}"

#### `shopping_list_get()`

List all pending (not Done) items.

1. Query the database filtered by Done = false, sorted by Name ascending
2. Return a markdown table: Name, Amount, Notes

#### `shopping_list_done(names)`

Mark items as ordered.

- `names`: list of ingredient names (e.g. `["Crisp Best Pale Ale Malt", "Rice Hulls"]`)

1. For each name, find the pending entry (case-insensitive match)
2. Set Done = true
3. Return summary: which items were ticked off, which weren't found

## 3. Open WebUI Skill

A skill with front matter that triggers on shopping-related queries.

### Front Matter

```
Add items to the shopping list, check what needs ordering, or mark items as ordered. Use when Andrea asks to add ingredients, check the shopping list, see what to order, or mark items as bought/ordered.
```

### Skill Body

Instruct the agent to:

1. **Adding items**: Use `shopping_list_add` with the ingredient name, amount, and optional notes. When adding gaps identified from a recipe analysis, include the recipe name in notes.
2. **Checking the list**: Use `shopping_list_get` to show pending items.
3. **Marking as ordered**: Use `shopping_list_done` with the ingredient names. Accept partial orders — only mark what was actually bought.

### Integration with Recipe Finder

The recipe-finder skill already identifies inventory gaps. When it does, the agent can suggest adding them to the shopping list. This is a conversational flow, not an automatic action — the agent asks "want me to add these to the shopping list?" and Andrea confirms.

No code change to the recipe-finder skill is needed — the agent can call shopping list tools from any conversation where both tools are available.

## 4. What This Does NOT Cover

- **Receiving inventory**: Adding purchased items to the Notion inventory databases is a separate workflow and tool, not part of this spec.
- **Future brews**: Scoped out. Shopping list items stand on their own with notes for context.
- **Supplier integration**: No scraping or API integration with The Malt Miller.
- **Sync to markdown**: The `shopping-list.md` file is not updated by this tool. It becomes obsolete.
- **Price tracking**: No cost or pricing information.
