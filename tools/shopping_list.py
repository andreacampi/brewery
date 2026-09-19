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
