# Shopping List Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open WebUI tool and skill for managing a brewing ingredient shopping list in Notion.

**Architecture:** Single Python tool file (same pattern as brew log tool) + skill front matter. No k8s deployment needed — everything lives in Open WebUI.

**Tech Stack:** Python, httpx, Pydantic, Notion API, Open WebUI

**Spec:** `docs/superpowers/specs/2026-09-19-shopping-list-design.md`

## Global Constraints

- Follow the brew log tool pattern exactly: Valves for API key + database ID, httpx async client, Pydantic BaseModel
- Amount is text (mixed units: g, kg, packets)
- Case-insensitive matching on ingredient names
- Merge on add: append amounts with " + ", notes with "; "
- `shopping_list_done` takes `list[str]`, not comma-separated string
- Tool code lives in Open WebUI (pasted via UI), with a copy kept in `tools/` for version control

---

### Task 1: Create the Shopping List Tool

**Files:**
- Create: `tools/shopping_list.py`

**Interfaces:**
- Consumes: Notion API (same integration token as brew log tool)
- Produces: Three tool methods callable by the Open WebUI agent

- [ ] **Step 1: Write the tool file**

```python
"""
title: Shopping List
author: Andrea Campi
description: Manage the brewery shopping list in Notion. Add ingredients, check pending items, and mark items as ordered.
requirements: httpx
version: 1.0.0
"""

import httpx
from pydantic import BaseModel, Field
from typing import Optional


class Tools:
    class Valves(BaseModel):
        notion_api_key: str = Field("", description="Notion internal integration token")
        database_id: str = Field("", description="Shopping List database ID")

    NOTION_API = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.valves.notion_api_key}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def _find_pending_by_name(self, client: httpx.AsyncClient, name: str) -> Optional[dict]:
        resp = await client.post(
            f"{self.NOTION_API}/databases/{self.valves.database_id}/query",
            headers=self._headers(),
            json={
                "filter": {
                    "and": [
                        {"property": "Done", "checkbox": {"equals": False}},
                        {"property": "Name", "title": {"equals": name}},
                    ]
                },
                "page_size": 1,
            },
        )
        if resp.status_code != 200:
            return None
        results = resp.json().get("results", [])
        return results[0] if results else None

    async def shopping_list_add(self, name: str, amount: str, notes: str = "") -> str:
        """
        Add an ingredient to the shopping list. Merges with an existing pending entry if one exists.
        :param name: Ingredient name (e.g. "Crisp Best Pale Ale Malt")
        :param amount: Quantity with unit (e.g. "100g", "1 packet", "20kg")
        :param notes: Context (e.g. "for London Porter", "general restocking")
        :return: Confirmation of what was added or merged
        """
        async with httpx.AsyncClient() as client:
            existing = await self._find_pending_by_name(client, name)

            if existing:
                props = existing["properties"]
                old_amount = self._extract_rich_text(props.get("Amount", {}).get("rich_text", []))
                old_notes = self._extract_rich_text(props.get("Notes", {}).get("rich_text", []))

                new_amount = f"{old_amount} + {amount}" if old_amount else amount
                new_notes = f"{old_notes}; {notes}" if old_notes and notes else (old_notes or notes)

                update_props = {
                    "Amount": {"rich_text": [{"text": {"content": new_amount}}]},
                }
                if new_notes:
                    update_props["Notes"] = {"rich_text": [{"text": {"content": new_notes}}]}

                resp = await client.patch(
                    f"{self.NOTION_API}/pages/{existing['id']}",
                    headers=self._headers(),
                    json={"properties": update_props},
                )
                if resp.status_code != 200:
                    return f"Error merging {name}: {resp.status_code} — {resp.text}"
                return f"Merged with existing: {name} now {new_amount}"

            properties = {
                "Name": {"title": [{"text": {"content": name}}]},
                "Amount": {"rich_text": [{"text": {"content": amount}}]},
                "Done": {"checkbox": False},
            }
            if notes:
                properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}

            resp = await client.post(
                f"{self.NOTION_API}/pages",
                headers=self._headers(),
                json={
                    "parent": {"database_id": self.valves.database_id},
                    "properties": properties,
                },
            )
            if resp.status_code != 200:
                return f"Error adding {name}: {resp.status_code} — {resp.text}"
            return f"Added {amount} {name}{f' ({notes})' if notes else ''}"

    async def shopping_list_get(self) -> str:
        """
        List all pending (not yet ordered) items on the shopping list.
        :return: Markdown table of pending items
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.NOTION_API}/databases/{self.valves.database_id}/query",
                headers=self._headers(),
                json={
                    "filter": {"property": "Done", "checkbox": {"equals": False}},
                    "sorts": [{"property": "Name", "direction": "ascending"}],
                },
            )
            if resp.status_code != 200:
                return f"Error reading shopping list: {resp.status_code} — {resp.text}"
            results = resp.json().get("results", [])

        if not results:
            return "Shopping list is empty — nothing to order."

        lines = ["| Ingredient | Amount | Notes |"]
        lines.append("|------------|--------|-------|")
        for page in results:
            props = page["properties"]
            name = self._extract_title(props)
            amount = self._extract_rich_text(props.get("Amount", {}).get("rich_text", []))
            notes = self._extract_rich_text(props.get("Notes", {}).get("rich_text", []))
            lines.append(f"| {name} | {amount} | {notes} |")

        return "\n".join(lines)

    async def shopping_list_done(self, names: list[str]) -> str:
        """
        Mark items as ordered. Use after placing an order.
        :param names: List of ingredient names to mark as done (e.g. ["Crisp Best Pale Ale Malt", "Rice Hulls"])
        :return: Summary of which items were ticked off and which weren't found
        """
        ticked = []
        not_found = []

        async with httpx.AsyncClient() as client:
            for name in names:
                existing = await self._find_pending_by_name(client, name)
                if not existing:
                    not_found.append(name)
                    continue

                resp = await client.patch(
                    f"{self.NOTION_API}/pages/{existing['id']}",
                    headers=self._headers(),
                    json={"properties": {"Done": {"checkbox": True}}},
                )
                if resp.status_code == 200:
                    ticked.append(name)
                else:
                    not_found.append(f"{name} (error: {resp.status_code})")

        parts = []
        if ticked:
            parts.append(f"Ordered: {', '.join(ticked)}")
        if not_found:
            parts.append(f"Not found: {', '.join(not_found)}")
        return ". ".join(parts) if parts else "Nothing to update."

    @staticmethod
    def _extract_title(props: dict) -> str:
        return "".join(t.get("plain_text", "") for t in props.get("Name", {}).get("title", []))

    @staticmethod
    def _extract_rich_text(rich_text: list) -> str:
        return "".join(t.get("plain_text", "") for t in rich_text)
```

- [ ] **Step 2: Verify the tool file is valid Python**

Run: `cd ~/beers && python -c "import ast; ast.parse(open('tools/shopping_list.py').read()); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add tools/shopping_list.py
git commit -m "Add shopping list Open WebUI tool"
```

---

### Task 2: Deploy and Test the Tool

This task requires Andrea's involvement — the tool is configured via the Open WebUI UI.

- [ ] **Step 1: Create the Notion database**

Andrea creates a new database in Notion called "Shopping List" with these properties:
- Name (title) — ingredient name
- Amount (text) — quantity with unit
- Notes (text) — context
- Done (checkbox) — ordered or not

Share the database with the existing Notion integration (same one used for brew log).

- [ ] **Step 2: Add the tool to Open WebUI**

In Open WebUI → Workspace → Tools → Create New Tool:
- Paste the contents of `tools/shopping_list.py`
- Save

- [ ] **Step 3: Configure Valves**

Set the tool's Valves:
- `notion_api_key`: same token as brew log tool
- `database_id`: the ID of the new Shopping List database

- [ ] **Step 4: Attach tool to Brew agent**

In the Brew agent configuration, add the Shopping List tool alongside the existing brew log tool.

- [ ] **Step 5: Test add**

Ask the Brew agent: "Add 100g Rice Hulls to the shopping list, for 4 Day Kveik IPA"

Expected: item appears in Notion database.

- [ ] **Step 6: Test merge**

Ask: "Add 200g Rice Hulls to the shopping list, for Double Hazy Jane"

Expected: existing Rice Hulls entry updated to "100g + 200g", notes "for 4 Day Kveik IPA; for Double Hazy Jane".

- [ ] **Step 7: Test get**

Ask: "What's on the shopping list?"

Expected: markdown table showing the merged Rice Hulls entry.

- [ ] **Step 8: Test done**

Ask: "I ordered the Rice Hulls"

Expected: Rice Hulls entry marked Done in Notion.

- [ ] **Step 9: Test done with empty list**

Ask: "What's on the shopping list?"

Expected: "Shopping list is empty — nothing to order."

---

### Task 3: Write the Shopping List Skill

- [ ] **Step 1: Write the skill front matter**

The skill is added in Open WebUI → Workspace → Skills (or via agent configuration). The front matter:

```
Add items to the shopping list, check what needs ordering, or mark items as ordered. Use when Andrea asks to add ingredients, check the shopping list, see what to order, or mark items as bought/ordered.
```

No skill body needed — the tool docstrings are sufficient for the agent to use the methods correctly.

- [ ] **Step 2: Test skill trigger**

Start a new chat and ask: "What do I need to order?"

Expected: the skill triggers and calls `shopping_list_get`.

- [ ] **Step 3: Test cross-skill flow**

Ask: "Look at beers we brewed again. Do we have stocks to make any of them? Add anything missing to the shopping list."

Expected: recipe-finder skill identifies gaps, then shopping list tool adds them.

- [ ] **Step 4: Commit the plan as complete**

```bash
git add docs/superpowers/plans/2026-09-19-shopping-list-plan.md
git commit -m "Add shopping list implementation plan"
```
