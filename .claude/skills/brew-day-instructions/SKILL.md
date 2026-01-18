# Brew Day Instructions Generator

Generate printable brew day instruction sheets (PDF) from recipe JSON files.

## Purpose

This skill automates the creation of compact, printer-friendly brew sheets that include:
- Ingredient checklist with amounts and timing
- Step-by-step brew day instructions
- Fermentation schedule with nutrient additions
- Expected gravity ranges and ABV calculations
- Key notes and troubleshooting tips

## Usage

### Basic Usage

```
/brew-day-instructions <recipe-file>
```

**Example:**
```
/brew-day-instructions recipes/blackberry-mead-2026-01.json
```

### Options

- `--format compact` (default) - 1-2 page condensed format
- `--format detailed` - Full detailed brew sheet with extensive notes
- `--pdf-only` - Skip markdown, generate PDF only
- `--markdown-only` - Generate markdown only, skip PDF

**Examples:**
```
/brew-day-instructions recipes/citrus-mead.json --format detailed
/brew-day-instructions recipes/junction.json --markdown-only
```

## What It Does

1. **Reads Recipe JSON**: Parses the recipe file to extract:
   - Ingredients (fermentables, adjuncts, hops, yeast)
   - Mashing/brewing steps and temperatures
   - Fermentation stages and schedules
   - Expected beer stats (OG, FG, ABV, IBU, SRM)

2. **Generates Markdown Brew Sheet**: Creates a formatted markdown document with:
   - **Header**: Recipe name, batch size, style, stats
   - **Ingredient Table**: Organized by category with amounts and timing
   - **Brew Day Steps**: Sequential instructions with temperatures and durations
   - **Fermentation Schedule**: Daily/weekly tasks with additions
   - **Gravity Calculations**: OG/FG ranges based on yeast attenuation
   - **Key Notes**: Important reminders, substitutions, troubleshooting

3. **Converts to HTML**: Uses pandoc to create standalone HTML with styling

4. **Generates PDF**: Uses Chrome headless to print HTML to PDF
   - Optimized for printing (0.5" margins)
   - Fits on 1-2 pages for compact format
   - Professional table formatting

5. **Outputs Files**:
   - `output/<recipe-id>-brew-sheet.md` - Markdown source
   - `output/<recipe-id>-brew-sheet.html` - Styled HTML
   - `output/<recipe-id>-brew-sheet.pdf` - Printable PDF

## File Locations

- **Output directory**: `output/` (gitignored - build artifacts)
- **Naming convention**: `<recipe-id>-brew-sheet.[md|html|pdf]`
- **Why separate?** Generated files are derived content that can be recreated from recipes anytime

## Compact Format Sections

1. **Header**: Recipe ID, batch size, style, OG, FG, ABV range
2. **Ingredients Table**: Category, item, amount, timing
3. **Brew Day Steps**: Numbered sequential instructions
4. **Fermentation Schedule**: Day-by-day tasks table
5. **Expected Gravity Range**: Table with min/max attenuation scenarios
6. **Key Notes**: Bullet points for critical information

## Detailed Format Sections

1. **Recipe Overview**: Full metadata, source, description
2. **Equipment Checklist**: Recommended equipment
3. **Ingredient Details**: Extended info (dry yield, moisture, alpha acid, etc.)
4. **Detailed Instructions**: Step-by-step with explanations
5. **Fermentation Notes**: Temperature profiles, timing, signs of completion
6. **Post-Fermentation**: Conditioning, packaging, storage
7. **Troubleshooting**: Common issues and solutions
8. **Recipe Notes**: Private notes, adjustments, sources

## Gravity & ABV Calculations

For yeast with attenuation ranges (e.g., M05 with 95-100%):
- Calculates FG at minimum attenuation
- Calculates FG at maximum attenuation
- Computes ABV for both scenarios: `(OG - FG) × 131.25`
- Displays as range in table format

## Template Customization

The skill uses templates for different recipe types:
- **Mead template**: No boil, staggered nutrients, fruit handling
- **Beer template**: Mash schedule, boil additions, hop schedule
- **Ginger beer template**: Spice additions, fermentation temps

Auto-detects based on recipe category or can be specified.

## Requirements

- `pandoc` - Markdown to HTML conversion (auto-installed via Homebrew)
- Chrome - PDF generation (uses headless mode)

## Implementation Notes

**Data Extraction:**
- Parses JSON recipe using `jq` for ingredient extraction
- Handles different `addition_step` formats (PRE-PITCH, 0-0, 1-0, etc.)
- Groups ingredients by timing for fermentation schedule
- Calculates attenuation ranges from yeast properties

**Formatting:**
- Uses markdown tables for compact presentation
- Applies pandoc template for consistent HTML styling
- Chrome print settings optimized for single-page-per-sheet

**Error Handling:**
- Validates recipe JSON structure
- Checks for required fields (OG, yeast attenuation)
- Falls back to defaults if optional fields missing
- Warns if calculations impossible (missing attenuation data)

## Examples

### Example 1: Mead Recipe
```
/brew-day-instructions recipes/blackberry-mead-2026-01.json
```
**Output:**
- Extracts honey, fruit, spice additions
- Creates PRE-PITCH and staggered nutrient schedule
- Calculates FG range from M05 attenuation (95-100%)
- Generates 1-page compact PDF

### Example 2: Beer Recipe
```
/brew-day-instructions recipes/munkner-helles.json --format detailed
```
**Output:**
- Extracts grain bill, mash schedule
- Lists hop additions with alpha acids and timing
- Includes boil duration and cool-down instructions
- Generates 2-page detailed PDF with equipment list

### Example 3: Markdown Only
```
/brew-day-instructions recipes/citrus-mead.json --markdown-only
```
**Output:**
- Generates markdown file only
- Useful for editing before PDF generation
- Can be version controlled with recipe

## Future Enhancements

- QR code generation linking to recipe source
- Batch scaling calculator (e.g., scale 5L recipe to 10L)
- Shopping list generation from recipe
- Timeline visualization for multi-day brews
- Export to Brewfather/BeerXML format
