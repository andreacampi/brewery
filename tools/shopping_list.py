"""
title: Shopping List
author: Andrea Campi
description: Manage the brewery shopping list in Notion. Add ingredients, check pending items, and mark items as ordered.
requirements: httpx
version: 1.1.0
"""

import httpx
from pydantic import BaseModel, Field
from typing import Optional


UNIT_TO_GRAMS = {"g": 1, "kg": 1000}


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

    @staticmethod
    def _normalize_quantity(qty: float, unit: str, target_unit: str) -> Optional[float]:
        if unit == target_unit:
            return qty
        if unit in UNIT_TO_GRAMS and target_unit in UNIT_TO_GRAMS:
            return qty * UNIT_TO_GRAMS[unit] / UNIT_TO_GRAMS[target_unit]
        return None

    @staticmethod
    def _format_quantity(qty: float, unit: str) -> str:
        if qty == int(qty):
            return f"{int(qty)}{unit}"
        return f"{qty:.1f}{unit}"

    async def _add_one(self, client: httpx.AsyncClient, name: str, quantity: float, unit: str, notes: str) -> str:
        existing = await self._find_pending_by_name(client, name)

        if existing:
            props = existing["properties"]
            old_qty = props.get("Quantity", {}).get("number") or 0
            old_unit = (props.get("Unit", {}).get("select") or {}).get("name", "")
            old_notes = self._extract_rich_text(props.get("Notes", {}).get("rich_text", []))

            converted = self._normalize_quantity(quantity, unit, old_unit)
            if converted is None:
                return f"Cannot merge: existing {name} is in {old_unit}, new amount is in {unit}"

            new_qty = old_qty + converted
            new_notes = f"{old_notes}; {notes}" if old_notes and notes else (old_notes or notes)

            update_props = {
                "Quantity": {"number": new_qty},
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
            return f"Merged with existing: {name} now {self._format_quantity(new_qty, old_unit)}"

        properties = {
            "Name": {"title": [{"text": {"content": name}}]},
            "Quantity": {"number": quantity},
            "Unit": {"select": {"name": unit}},
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
        return f"Added {self._format_quantity(quantity, unit)} {name}{f' ({notes})' if notes else ''}"

    async def shopping_list_add(self, name: str, quantity: float, unit: str, notes: str = "") -> str:
        """
        Add an ingredient to the shopping list. Merges with an existing pending entry if one exists.
        :param name: Ingredient name (e.g. "Crisp Best Pale Ale Malt")
        :param quantity: Numeric quantity (e.g. 100, 1, 20)
        :param unit: Unit of measure (e.g. "g", "kg", "packet")
        :param notes: Context (e.g. "for London Porter", "general restocking")
        :return: Confirmation of what was added or merged
        """
        async with httpx.AsyncClient() as client:
            return await self._add_one(client, name, quantity, unit, notes)

    async def shopping_list_add_many(self, items: list[dict]) -> str:
        """
        Add multiple ingredients to the shopping list in one call. Each item merges with existing pending entries.
        :param items: List of items, each with keys: name (str), quantity (float), unit (str), and optional notes (str). Example: [{"name": "Rice Hulls", "quantity": 100, "unit": "g", "notes": "for Kveik IPA"}, {"name": "Dextrose", "quantity": 50, "unit": "g"}]
        :return: Summary of all additions
        """
        results = []
        async with httpx.AsyncClient() as client:
            for item in items:
                result = await self._add_one(
                    client,
                    item["name"],
                    item["quantity"],
                    item["unit"],
                    item.get("notes", ""),
                )
                results.append(result)
        return "\n".join(results)

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

        lines = ["| Ingredient | Quantity | Notes |"]
        lines.append("|------------|----------|-------|")
        for page in results:
            props = page["properties"]
            name = self._extract_title(props)
            qty = props.get("Quantity", {}).get("number") or 0
            unit = (props.get("Unit", {}).get("select") or {}).get("name", "")
            notes = self._extract_rich_text(props.get("Notes", {}).get("rich_text", []))
            lines.append(f"| {name} | {self._format_quantity(qty, unit)} | {notes} |")

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
