#!/usr/bin/env python3
"""
Generate brew day instruction sheets from recipe JSON files.

Creates markdown, HTML, and PDF brew sheets with:
- Ingredient checklist
- Step-by-step brew day instructions
- Fermentation schedule
- Gravity/ABV calculations
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class BrewSheetGenerator:
    """Generate brew sheets from recipe JSON."""

    def __init__(self, recipe_path: Path, lot_number: Optional[str] = None, extra_note: Optional[str] = None):
        self.recipe_path = recipe_path
        self.lot_number = lot_number
        self.extra_note = extra_note

        with open(recipe_path) as f:
            self.recipe = json.load(f)

        # Extract common fields
        # For custom recipes, use filename; for community recipes, use ID
        if 'recipes/' in str(recipe_path):
            self.recipe_id = recipe_path.stem  # filename without extension
        else:
            self.recipe_id = self.recipe['id']
        self.recipe_name = self.recipe['beer_name']
        self.water_amount = self.recipe['water_amount']
        self.og = float(self.recipe['og'])
        self.style = self.recipe['beer']['style']['name']
        self.private_note = self.recipe.get('private_note', '')

        # Detect if this is a MiniBrew recipe by structure (has boiling section)
        # MiniBrew beer recipes have a boiling section, meads don't
        self.is_minibrew = 'boiling' in self.recipe and len(self.recipe.get('boiling', [])) > 0

        # Mashing info
        mashing = self.recipe['mashing'][0]
        self.mash_name = mashing.get('name', 'Must preparation')
        mash_step = mashing['steps'][0]
        self.mash_start_temp = mash_step['temperature']
        self.mash_end_temp = mash_step['end_temperature']
        self.mash_duration = mash_step['duration']

        # Fermentation info
        fermenting = self.recipe['fermenting'][0]
        self.yeast = fermenting['yeast'][0]
        self.yeast_name = self.yeast['ingredient_name']
        self.yeast_amount = self.yeast['amount']
        self.yeast_atten = self.yeast['ingredient_attenuation']

        ferment_step = fermenting['steps'][0]
        self.ferment_temp = ferment_step['temperature']
        self.ferment_days = int(ferment_step['duration'])

        # Calculate attenuation range
        self.atten_min, self.atten_max = self._parse_attenuation(self.yeast_atten)

        # Calculate FG and ABV ranges
        self.fg_min, self.fg_max, self.abv_min, self.abv_max = self._calculate_ranges()

    def _parse_attenuation(self, atten_str: str) -> tuple:
        """Parse attenuation string into min/max range."""
        if '-' in atten_str:
            parts = atten_str.split('-')
            return float(parts[0]), float(parts[1])
        else:
            atten = float(atten_str)
            return atten - 2.5, atten + 2.5

    def _calculate_ranges(self) -> tuple:
        """Calculate FG and ABV ranges based on attenuation."""
        gravity_points = (self.og - 1.000) * 1000

        # FG = OG - (OG - 1.000) * (attenuation / 100)
        fg_min = 1.000 + (gravity_points * (1 - self.atten_max / 100)) / 1000
        fg_max = 1.000 + (gravity_points * (1 - self.atten_min / 100)) / 1000

        # ABV = (OG - FG) * 131.25
        abv_max = (self.og - fg_min) * 131.25
        abv_min = (self.og - fg_max) * 131.25

        return fg_min, fg_max, abv_min, abv_max

    def _get_ingredients(self, ingredient_type: str, section: str = 'mashing') -> List[Dict]:
        """Get ingredients of a specific type from recipe."""
        if section == 'mashing':
            return [ing for ing in self.recipe['mashing'][0]['ingredient_additions']
                   if ing['ingredient_type'] == ingredient_type]
        elif section == 'fermenting':
            return self.recipe['fermenting'][0].get('yeast', [])
        elif section == 'while_fermenting':
            return self.recipe['while_fermenting'].get('other_ingredients', [])
        return []

    def _format_amount(self, ing: Dict) -> str:
        """Format ingredient amount with units."""
        amount = ing['amount']
        units = ing.get('amount_units', 'GR')

        if units == 'UNIT':
            return f"{amount} units"
        elif units == 'ML':
            return f"{amount}ml"
        else:  # GR
            return f"{amount}g"

    def generate_ingredients_table(self) -> str:
        """Generate ingredients table markdown."""
        lines = [
            "| Category | Item | Amount | Timing |",
            "|----------|------|--------|--------|"
        ]

        # Fermentables
        fermentables = self._get_ingredients('FERM')
        for ferm in fermentables:
            lines.append(f"| **Fermentables** | {ferm['ingredient_name']} | {self._format_amount(ferm)} | Brew day |")

        # Fruit/Spices (ADJ in mashing)
        adjuncts = self._get_ingredients('ADJ')
        for i, adj in enumerate(adjuncts):
            category = "**Fruit/Spices**" if i == 0 else ""
            # Remove parenthetical details
            name = adj['ingredient_name'].split(' (')[0]
            lines.append(f"| {category} | {name} | {self._format_amount(adj)} | Brew day |")

        # Yeast
        lines.append(f"| **Yeast** | {self.yeast_name} | {self.yeast_amount}g | Brew day |")

        # Additives (PRE-PITCH)
        prepitch = [ing for ing in self._get_ingredients('ADJ', 'while_fermenting')
                   if ing.get('addition_step') == 'PRE-PITCH']
        for prep in prepitch:
            name = prep['ingredient_name'].split(' (')[0]
            lines.append(f"| **Additives** | {name} | {self._format_amount(prep)} | Pre-pitch |")

        # Nutrients (staggered additions)
        nutrients = [ing for ing in self._get_ingredients('ADJ', 'while_fermenting')
                    if ing.get('addition_step') == '0-0' and ing.get('duration') is not None]

        if nutrients:
            nutrient_name = nutrients[0]['ingredient_name'].split(' (')[0]
            nutrient_amount = nutrients[0]['amount']
            nutrient_count = len(nutrients)

            # Format timings
            timings = []
            for nut in nutrients:
                dur = nut['duration']
                if dur == 1.0:
                    timings.append('24h')
                elif dur == 2.0:
                    timings.append('48h')
                elif dur == 3.0:
                    timings.append('72h')
                elif dur == 7.0:
                    timings.append('1wk')
                else:
                    timings.append(f"{int(dur)}d")

            timing_str = ', '.join(timings)
            lines.append(f"| **Nutrients** | {nutrient_name} | {nutrient_amount}g × {nutrient_count} | {timing_str} |")

        return '\n'.join(lines)

    def generate_brew_steps(self) -> str:
        """Generate brew day steps."""
        steps = []
        step_num = 1

        # Step 1: Hot water infusion if temp changes
        if self.mash_start_temp != self.mash_end_temp:
            steps.append(
                f"{step_num}. **{self.mash_name} ({self.mash_duration} min):** "
                f"Heat {self.water_amount}L water to {self.mash_start_temp}°C. "
                f"Add spices/adjuncts. Steep while cooling to {self.mash_end_temp}°C."
            )
            step_num += 1

        # Step 2: Add fermentables
        fermentables = self._get_ingredients('FERM')
        ferm_list = ', '.join([f"{f['amount']}g {f['ingredient_name']}" for f in fermentables])
        steps.append(f"{step_num}. **Add Fermentables:** Dissolve {ferm_list} in hot water.")
        step_num += 1

        # Step 3: Add adjuncts if present
        adjuncts = self._get_ingredients('ADJ')
        if adjuncts:
            adj_list = ', '.join([f"{self._format_amount(a)} {a['ingredient_name']}" for a in adjuncts])
            steps.append(f"{step_num}. **Add Adjuncts:** Add {adj_list}. Stir well.")
            step_num += 1

        # Step 4: Cool
        steps.append(f"{step_num}. **Cool:** Cool to {self.ferment_temp}°C. Take OG reading (target: {self.og:.3f}).")
        step_num += 1

        # Step 5: PRE-PITCH additives
        prepitch = [ing for ing in self._get_ingredients('ADJ', 'while_fermenting')
                   if ing.get('addition_step') == 'PRE-PITCH']
        if prepitch:
            prep_list = ', '.join([f"{p['amount']}g {p['ingredient_name']}" for p in prepitch])
            steps.append(f"{step_num}. **Pre-Pitch Additives:** Add {prep_list}. Wait 30 min.")
            step_num += 1

        # Step 6: Pitch yeast
        steps.append(
            f"{step_num}. **Pitch Yeast:** Rehydrate {self.yeast_amount}g {self.yeast_name} "
            f"in warm water (38-40°C) for 15 min. Pitch into must."
        )
        step_num += 1

        # Step 7: Seal
        steps.append(f"{step_num}. **Seal:** Add airlock. Ferment at {self.ferment_temp}°C.")

        return '\n'.join(steps)

    def generate_fermentation_schedule(self) -> str:
        """Generate fermentation schedule table."""
        lines = [
            "| Day | Task |",
            "|-----|------|",
            "| **Daily (Days 1-7)** | Degas - swirl gently to release CO₂, prevent mold on fruit |"
        ]

        # Check if there are adjuncts for racking
        has_adjuncts = len(self._get_ingredients('ADJ')) > 0

        # Nutrient additions
        nutrients = [ing for ing in self._get_ingredients('ADJ', 'while_fermenting')
                    if ing.get('addition_step') == '0-0' and ing.get('duration') is not None]

        for nut in nutrients:
            dur = nut['duration']
            if dur == 1.0:
                day = "1"
            elif dur == 2.0:
                day = "2"
            elif dur == 3.0:
                day = "3"
            elif dur == 7.0:
                day = "7"
            else:
                day = str(int(dur))

            nutrient_name = nut['ingredient_name'].split(' (')[0]
            task = f"Add {nut['amount']}g {nutrient_name}"

            # Add racking note to Day 7 if there are adjuncts
            if dur == 7.0 and has_adjuncts:
                task += " + **Rack through cheesecloth** to remove fruit"

            lines.append(f"| **Day {day}** | {task} |")

        lines.append(f"| **Days 8-{self.ferment_days}** | Continue primary fermentation (no fruit) |")
        lines.append("| **Week 4-5** | Monitor activity. Take FG reading when stable. |")

        return '\n'.join(lines)

    def generate_minibrew_ingredients(self) -> str:
        """Generate simple ingredient checklist for MiniBrew recipes."""
        lines = ["**Grains & Fermentables:**", ""]

        # Fermentables from mashing
        fermentables = self._get_ingredients('FERM')
        for ferm in fermentables:
            lines.append(f"- {ferm['ingredient_name']}: {self._format_amount(ferm)}")

        lines.append("")
        lines.append("**Hops (Boil - in slot order):**")
        lines.append("")

        # Hops from boiling - SORT BY DURATION (highest first = added earliest)
        if 'boiling' in self.recipe and self.recipe['boiling']:
            # Collect all hops
            all_hops = []
            for boil_stage in self.recipe['boiling']:
                all_hops.extend(boil_stage.get('hops', []))

            # Sort by duration descending (60 min before flameout)
            all_hops.sort(key=lambda h: h['duration'], reverse=True)

            # Number slots in chronological order
            for slot, hop in enumerate(all_hops, 1):
                time = hop['duration']
                time_str = f"{time} min" if time > 0 else "flameout"
                lines.append(f"- Slot {slot}: {hop['ingredient_name']}: {self._format_amount(hop)} @ {time_str}")


        # Dry hops from while_fermenting - PRESERVE EXACT ORDER
        dry_hops = self.recipe['while_fermenting'].get('hops', [])
        if dry_hops:
            lines.append("")
            lines.append("**Dry Hops (in order):**")
            lines.append("")
            for i, hop in enumerate(dry_hops, 1):
                lines.append(f"- Slot {i}: {hop['ingredient_name']}: {self._format_amount(hop)}")

        # Yeast
        lines.append("")
        lines.append("**Yeast:**")
        lines.append("")
        lines.append(f"- {self.yeast_name}: {self.yeast_amount}g")

        return '\n'.join(lines)

    def generate_minibrew_schedule(self) -> str:
        """Generate fermentation schedule for MiniBrew recipes."""
        # Build a day-by-day schedule first
        schedule = {}
        schedule[1] = ["**🔔 Brew day:** MiniBrew handles mash/boil/cooling. **PITCH YEAST** when prompted."]

        # Get fermentation stages
        current_day = 1
        final_day = 1
        for stage in self.recipe['fermenting']:
            stage_type = stage.get('fermentation_stage_type', 'PRIM')
            for step in stage['steps']:
                duration = int(step['duration'])
                if duration > 0:
                    temp = step['temperature']
                    stage_name = {
                        'PRIM': 'Primary fermentation',
                        'SECO': 'Secondary fermentation',
                        'COND': 'Conditioning',
                        'COLD': 'Cold crash'
                    }.get(stage_type, 'Fermentation')

                    # Add fermentation to each day in range
                    for day in range(current_day, current_day + duration):
                        if day not in schedule:
                            schedule[day] = []
                        schedule[day].append(f"{stage_name} @ {temp}°C")

                    final_day = current_day + duration
                    current_day = final_day

        # Add hop additions during fermentation
        ferm_hops = self.recipe['while_fermenting'].get('hops', [])
        if ferm_hops:
            hop_schedule = {}
            for hop in ferm_hops:
                day = int(hop.get('duration', 3))
                if day not in hop_schedule:
                    hop_schedule[day] = []
                hop_schedule[day].append(f"{self._format_amount(hop)} {hop['ingredient_name']}")

            for day, hops in hop_schedule.items():
                if day not in schedule:
                    schedule[day] = []
                hops_str = ', '.join(hops)
                # Day 1 hops are brew day additions, not dry hops
                if day == 1:
                    schedule[day].insert(0, f"**🔔 Add hops:** {hops_str}")
                else:
                    schedule[day].insert(0, f"**🔔 DRY HOP:** Add {hops_str}")

        # Build the table from the schedule
        lines = [
            "| Day | Task |",
            "|-----|------"
        ]

        for day in sorted(schedule.keys()):
            tasks = schedule[day]
            if len(tasks) == 1:
                lines.append(f"| **Day {day}** | {tasks[0]} |")
            else:
                lines.append(f"| **Day {day}** | {' + '.join(tasks)} |")

        # Bottling day
        lines.append(f"| **Day {final_day}** | **🔔 BOTTLE** with priming sugar (or keg for natural carbonation) |")
        lines.append("| Week 2+ | Condition in bottles, ready to drink! |")

        return '\n'.join(lines)

    def generate_key_notes(self) -> str:
        """Generate key notes section."""
        notes = []

        # Extract notes from private_note
        if self.private_note:
            for line in self.private_note.split('\n'):
                if line.startswith('-') or 'Recipe from' in line or 'Substitute' in line or line.startswith('No '):
                    # Remove leading dash if present
                    clean_line = line.lstrip('- ')
                    notes.append(f"- {clean_line}")

        # Add adjunct handling notes
        if self._get_ingredients('ADJ'):
            notes.append("- **Remove adjuncts Day 7:** Prevents tannin overextraction")
            notes.append("- **Daily degassing critical:** Prevents mold on floating ingredients")

        # Yeast character
        notes.append(f"- **Yeast character:** {self.yeast_name} ({self.atten_min:.2f}-{self.atten_max:.2f}% attenuation)")

        # Aging
        notes.append("- **Age:** Minimum 2-4 weeks after fermentation, 1-3 months in bottle for best flavor")

        # Extra note if provided
        if self.extra_note:
            notes.append(f"- **Brew day note:** {self.extra_note}")

        return '\n'.join(notes)

    def generate_markdown(self) -> str:
        """Generate complete markdown brew sheet."""
        # Build header line with optional lot number
        lot_prefix = f"**Lot:** {self.lot_number} | " if self.lot_number else ""

        # Use MiniBrew template for community recipes
        if self.is_minibrew:
            abv = self.recipe.get('abv', 'N/A')
            ibu = self.recipe.get('ibu', 'N/A')
            # MiniBrew keg recipes yield 5.5L final product
            batch_size = "5.5L"

            markdown = f"""# {self.recipe_name}

{lot_prefix}**Recipe:** {self.recipe_id} | **Batch:** {batch_size} | **Style:** {self.style} | **ABV:** {abv}% | **IBU:** {ibu}

## Ingredients

{self.generate_minibrew_ingredients()}

## Fermentation Schedule

{self.generate_minibrew_schedule()}

## Notes

- MiniBrew handles mash, boil, and cooling automatically
- Pitch yeast when device prompts
- Bottle on final day with priming sugar (or keg for natural carbonation)
"""
            if self.extra_note:
                markdown += f"\n**Brew day note:** {self.extra_note}\n"

            return markdown

        # Original mead/manual template
        # Determine if yeast ferments dry
        dry_note = ""
        if self.atten_min > 85:
            dry_note = " Expect a dry finish."

        markdown = f"""# {self.recipe_name}

{lot_prefix}**Recipe:** {self.recipe_id} | **Batch:** {self.water_amount}L | **Style:** {self.style} | **OG:** {self.og:.3f} | **FG:** {self.fg_min:.3f}-{self.fg_max:.3f} | **ABV:** {self.abv_min:.1f}-{self.abv_max:.1f}%

## Ingredients

{self.generate_ingredients_table()}

## Brew Day Steps

{self.generate_brew_steps()}

## Fermentation Schedule

{self.generate_fermentation_schedule()}

## Expected Gravity Range

| Attenuation | Final Gravity | ABV |
|-------------|---------------|-----|
| {self.atten_min:.2f}% (minimum) | {self.fg_max:.3f} | {self.abv_min:.1f}% |
| {self.atten_max:.2f}% (maximum) | {self.fg_min:.3f} | {self.abv_max:.1f}% |

**Note:** {self.yeast_name} has {self.atten_min:.2f}-{self.atten_max:.2f}% attenuation.{dry_note}

## Key Notes

{self.generate_key_notes()}
"""
        return markdown

    def save_markdown(self, output_path: Path):
        """Save markdown to file."""
        output_path.write_text(self.generate_markdown())

    def convert_to_html(self, md_path: Path, html_path: Path):
        """Convert markdown to HTML using pandoc."""
        subprocess.run([
            'pandoc', str(md_path), '-o', str(html_path), '-s'
        ], check=True)

    def convert_to_pdf(self, html_path: Path, pdf_path: Path):
        """Convert HTML to PDF using Chrome headless."""
        subprocess.run([
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '--headless',
            '--disable-gpu',
            f'--print-to-pdf={pdf_path}',
            str(html_path)
        ], check=True, stderr=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser(description='Generate brew day instruction sheets')
    parser.add_argument('recipe', type=Path, help='Recipe JSON file')
    parser.add_argument('--format', choices=['compact', 'detailed'], default='compact',
                       help='Brew sheet format (default: compact)')
    parser.add_argument('--pdf-only', action='store_true',
                       help='Generate PDF only (skip markdown)')
    parser.add_argument('--markdown-only', action='store_true',
                       help='Generate markdown only (skip PDF)')
    parser.add_argument('--lot', type=str,
                       help='Lot number for this brew (e.g., LOT 100)')
    parser.add_argument('--note', type=str,
                       help='Extra note to add to brew sheet')

    args = parser.parse_args()

    if not args.recipe.exists():
        print(f"Error: Recipe file not found: {args.recipe}", file=sys.stderr)
        sys.exit(1)

    # Determine output type
    if args.markdown_only:
        output_type = 'markdown'
    elif args.pdf_only:
        output_type = 'pdf'
    else:
        output_type = 'all'

    # Create generator
    generator = BrewSheetGenerator(args.recipe, args.lot, args.note)

    # Output files - use output/ directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    base_name = f"{generator.recipe_id}-brew-sheet"
    md_file = output_dir / f"{base_name}.md"
    html_file = output_dir / f"{base_name}.html"
    pdf_file = output_dir / f"{base_name}.pdf"

    print(f"Generating brew sheet for: {generator.recipe_name}")
    print(f"Recipe ID: {generator.recipe_id}")
    print(f"Format: {args.format}")
    print()

    # Generate markdown
    if output_type in ['all', 'markdown']:
        print("Generating markdown...")
        generator.save_markdown(md_file)
        print(f"✓ Markdown created: {md_file}")

    # Generate HTML
    if output_type in ['all', 'pdf']:
        print("Converting to HTML...")
        generator.convert_to_html(md_file, html_file)
        print(f"✓ HTML created: {html_file}")

    # Generate PDF
    if output_type in ['all', 'pdf']:
        print("Generating PDF...")
        generator.convert_to_pdf(html_file, pdf_file)
        pdf_size = pdf_file.stat().st_size // 1024
        print(f"✓ PDF created: {pdf_file} ({pdf_size}K)")

    print()
    print("Brew sheet generation complete!")


if __name__ == '__main__':
    main()
