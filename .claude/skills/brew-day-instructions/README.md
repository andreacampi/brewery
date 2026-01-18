# Brew Day Instructions Generator Skill

Automatically generate printable PDF brew sheets from recipe JSON files.

## Quick Start

```bash
# Generate brew sheet for any recipe
/brew-day-instructions recipes/blackberry-mead-2026-01.json

# Or use the script directly
./.claude/skills/brew-day-instructions/generate_brew_sheet.py recipes/citrus-mead.json
```

## Features

- 📋 **Compact Format**: 1-2 page brew sheets optimized for printing
- 🧪 **Gravity Calculations**: Automatic OG/FG/ABV range based on yeast attenuation
- 📅 **Fermentation Schedule**: Day-by-day nutrient addition timeline
- ✅ **Checklists**: Ingredient lists with amounts and timing
- 📄 **Multi-Format**: Outputs Markdown, HTML, and PDF

## Output Files

All files are generated in the `output/` directory (gitignored):

For recipe `blackberry-mead-2026-01.json`, generates:
- `output/blackberry-mead-2026-01-brew-sheet.md` - Markdown source
- `output/blackberry-mead-2026-01-brew-sheet.html` - Styled HTML
- `output/blackberry-mead-2026-01-brew-sheet.pdf` - Printable PDF

**Note:** The `output/` directory is in `.gitignore` - these are build artifacts that can be regenerated from recipes anytime.

## Requirements

- Python 3.7+ (built-in on macOS)
- `pandoc` - Installed via Homebrew
- Google Chrome - For PDF generation

## How It Works

1. Parses recipe JSON using Python's built-in JSON module
2. Calculates gravity/ABV ranges from yeast attenuation
3. Generates formatted markdown with clean templates
4. Converts to HTML via pandoc
5. Prints to PDF using Chrome headless

**Why Python?** Clean JSON parsing, proper data structures, easy to extend for beer recipes (hop schedules, boil additions), and maintainable code.

## Future Enhancements

- [ ] Beer-specific formatting (hop schedules, multi-step mashes, boil additions)
- [ ] Detailed format with equipment checklist
- [ ] Template selection based on recipe type (auto-detect mead/beer/ginger beer)
- [ ] QR code generation with recipe link
- [ ] Batch scaling support (scale 5L recipe to 10L)
- [ ] Multiple fermentation stages (secondary, tertiary)
- [ ] Water chemistry additions

## Customization

To customize the brew sheet format, edit the methods in the `BrewSheetGenerator` class in `generate_brew_sheet.py`. The code is well-structured with separate methods for each section.

## Examples

### Generate compact PDF (default)
```bash
/brew-day-instructions recipes/junction.json
```

### Generate detailed format
```bash
/brew-day-instructions recipes/citrus-mead.json --format detailed
```

### Markdown only (for editing)
```bash
/brew-day-instructions recipes/hibiscus-mead.json --markdown-only
```
