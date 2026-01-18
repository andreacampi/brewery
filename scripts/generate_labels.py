#!/usr/bin/env python3
"""
Bottle Label Generator for Dalston Rooftop Brewery

Generates back bottle labels (4cm x 6cm) with ingredients, ABV, and QR code.
Multiple labels per A4 page for efficient printing.
"""

import json
import argparse
from pathlib import Path
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
import qrcode


class BreweryLabelGenerator:
    """Generate bottle labels for Dalston Rooftop Brewery."""

    # Brand colors
    NAVY_BLUE = HexColor('#1a2838')
    WARM_BEIGE = HexColor('#d4c5a9')
    SUNSET_ORANGE = HexColor('#ff8c42')
    DARK_GRAY = HexColor('#2a2a2a')

    # QR code color palette (warm colors from brewery branding)
    QR_COLORS = [
        '#ff8c42',  # Sunset orange
        '#ffb366',  # Lighter orange
        '#ffa94d',  # Medium orange
        '#d4a574',  # Light brown
        '#c9a772',  # Tan
        '#d4c5a9',  # Warm beige
        '#e6c79c',  # Pale tan
        '#ffcc80',  # Light orange/peach
    ]

    # QR code color mode: 'single' or 'cycle'
    QR_COLOR_MODE = 'single'  # Set to 'cycle' to rotate through palette
    QR_SINGLE_COLOR_INDEX = 7  # Index in QR_COLORS (7 = #ffcc80, light orange/peach)

    # Label dimensions (in points, 1mm = 2.834645669 points)
    LABEL_WIDTH = 40 * mm
    LABEL_HEIGHT = 60 * mm
    MARGIN = 2 * mm  # Reduced from 5mm
    GAP = 10 * mm
    HEADER_HEIGHT = 8 * mm  # Reduced from 10mm

    def __init__(self, batch_name, style, recipe_path, abv, url, lot_number=None):
        """
        Initialize the label generator.

        Args:
            batch_name: Display name of the batch (e.g., "Navarino Road")
            style: Style of the brew (e.g., "Hibiscus Mead")
            recipe_path: Path to recipe JSON file
            abv: ABV percentage as string (e.g., "11.81")
            url: URL to the product page
            lot_number: Lot number (e.g., "LOT 098" or "LOT 098-A")
        """
        self.batch_name = batch_name
        self.style = style
        self.recipe_path = Path(recipe_path)
        self.abv = abv
        self.url = url
        self.lot_number = lot_number
        self.ingredients = self.extract_ingredients()

    def extract_ingredients(self):
        """
        Parse recipe JSON and extract ingredients, applying marketing filters.

        Returns:
            Formatted ingredient string (e.g., "Honey, hibiscus, ginger, cinnamon.")
        """
        with open(self.recipe_path, 'r') as f:
            recipe = json.load(f)

        ingredients = []

        # Extract from mashing section
        for mash in recipe.get('mashing', []):
            for ing in mash.get('ingredient_additions', []):
                name = ing['ingredient_name']
                if self._should_include_ingredient(name):
                    ingredients.append(self._clean_ingredient_name(name))

        # Extract from fermenting section (yeast)
        for ferment in recipe.get('fermenting', []):
            for yeast in ferment.get('yeast', []):
                name = yeast['ingredient_name']
                if self._should_include_ingredient(name):
                    ingredients.append(self._clean_ingredient_name(name))

        # Extract from while_fermenting (dry hops, adjuncts)
        while_ferm = recipe.get('while_fermenting', {})
        for ing in while_ferm.get('other_ingredients', []):
            name = ing['ingredient_name']
            if self._should_include_ingredient(name):
                ingredients.append(self._clean_ingredient_name(name))

        # Format as lowercase, comma-separated with period
        if ingredients:
            return ', '.join(ingredients).lower() + '.'
        return ''

    def _should_include_ingredient(self, name):
        """
        Check if ingredient should be included per marketing rules.

        Marketing rules:
        - Skip water (implicit in all recipes)
        - Skip yeast nutrients
        - Skip fining agents
        - Skip yeast (implicit)

        Args:
            name: Ingredient name

        Returns:
            True if ingredient should be included
        """
        name_lower = name.lower()

        # Skip water
        if 'water' in name_lower:
            return False

        # Skip yeast nutrients
        if 'nutrient' in name_lower:
            return False

        # Skip fining agents
        fining_agents = ['bentonite', 'gelatin', 'isinglass', 'calcium bentonite']
        if any(agent in name_lower for agent in fining_agents):
            return False

        # Skip yeast (implicit in all fermented beverages)
        if 'yeast' in name_lower:
            return False

        return True

    def _clean_ingredient_name(self, name):
        """
        Clean up ingredient name by removing obvious processing details.
        Keep descriptive details that add flavor context.

        Args:
            name: Raw ingredient name

        Returns:
            Cleaned ingredient name
        """
        # Remove obvious processing details
        clean_name = name
        clean_name = clean_name.replace('(steeped)', '').strip()
        clean_name = clean_name.replace('steeped', '').strip()

        return clean_name

    def generate_qr_code(self, color="#ff8c42"):
        """
        Generate QR code image for URL.

        Args:
            color: Hex color for QR code (default: sunset orange)

        Returns:
            BytesIO buffer containing PNG image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(self.url)
        qr.make(fit=True)

        # Convert to BytesIO for ReportLab ImageReader
        img = qr.make_image(fill_color=color, back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    def draw_page_header(self, c):
        """
        Draw page header at top of A4 page for tracking.

        Args:
            c: ReportLab canvas
        """
        width, height = A4

        # Header text
        c.setFillColor(self.NAVY_BLUE)
        c.setFont("Helvetica-Bold", 12)
        header_text = f"🍯 {self.batch_name} ({self.style})"
        text_width = c.stringWidth(header_text, "Helvetica-Bold", 12)
        x = (width - text_width) / 2
        y = height - self.MARGIN + 5 * mm
        c.drawString(x, y, header_text)

    def draw_label(self, c, x, y, label_index=0):
        """
        Draw a single label at position (x, y).

        Args:
            c: ReportLab canvas
            x: X position (bottom-left corner)
            y: Y position (bottom-left corner)
            label_index: Index of this label (for color rotation)
        """
        # Draw border (light cutting guide)
        c.setStrokeColor(self.WARM_BEIGE)
        c.setLineWidth(0.5)
        c.rect(x, y, self.LABEL_WIDTH, self.LABEL_HEIGHT)

        # Ingredients section
        y_pos = y + self.LABEL_HEIGHT - 8 * mm

        # Combine "Ingredients: " with the ingredient list on same line
        c.setFillColor(self.NAVY_BLUE)
        c.setFont("Helvetica-Bold", 8)
        label_text = "Ingredients: "
        label_width = c.stringWidth(label_text, "Helvetica-Bold", 8)
        c.drawString(x + 5 * mm, y_pos, label_text)

        # Draw ingredients continuing on same line
        c.setFillColor(self.DARK_GRAY)
        c.setFont("Helvetica", 7)

        # Simple text wrapping, starting after "Ingredients: " label
        max_width_first = self.LABEL_WIDTH - 10 * mm - label_width
        max_width = self.LABEL_WIDTH - 10 * mm
        words = self.ingredients.split()
        lines = []
        current_line = []
        first_line = True

        for word in words:
            test_line = ' '.join(current_line + [word])
            current_max = max_width_first if first_line else max_width
            if c.stringWidth(test_line, "Helvetica", 7) <= current_max:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    first_line = False
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        x_offset = x + 5 * mm + label_width
        for i, line in enumerate(lines):
            if i == 0:
                # First line continues after "Ingredients: "
                c.drawString(x_offset, y_pos, line)
            else:
                # Subsequent lines start at left margin - reduced spacing
                y_pos -= 2.5 * mm
                c.drawString(x + 5 * mm, y_pos, line)

        # ABV - more space before, bold label to match Ingredients
        y_pos -= 4 * mm
        c.setFillColor(self.NAVY_BLUE)
        c.setFont("Helvetica-Bold", 8)
        abv_label = "ABV: "
        abv_label_width = c.stringWidth(abv_label, "Helvetica-Bold", 8)
        c.drawString(x + 5 * mm, y_pos, abv_label)

        c.setFillColor(self.DARK_GRAY)
        c.setFont("Helvetica", 7)
        c.drawString(x + 5 * mm + abv_label_width, y_pos, f"{self.abv}%")

        # Lot Number - if provided
        if self.lot_number:
            y_pos -= 3 * mm
            c.setFillColor(self.NAVY_BLUE)
            c.setFont("Helvetica-Bold", 8)
            lot_label = "Lot: "
            lot_label_width = c.stringWidth(lot_label, "Helvetica-Bold", 8)
            c.drawString(x + 5 * mm, y_pos, lot_label)

            c.setFillColor(self.DARK_GRAY)
            c.setFont("Helvetica", 7)
            c.drawString(x + 5 * mm + lot_label_width, y_pos, self.lot_number)

        # QR Code - use color from palette
        if self.QR_COLOR_MODE == 'cycle':
            qr_color = self.QR_COLORS[label_index % len(self.QR_COLORS)]
        else:
            qr_color = self.QR_COLORS[self.QR_SINGLE_COLOR_INDEX]
        qr_buffer = self.generate_qr_code(color=qr_color)
        qr_img = ImageReader(qr_buffer)
        qr_size = 32 * mm  # Increased from 25mm
        qr_x = x + (self.LABEL_WIDTH - qr_size) / 2
        qr_y = y + 5 * mm
        c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

    def generate_pdf(self, output_path, num_labels=16):
        """
        Generate PDF with multiple labels on A4.

        Args:
            output_path: Path to save PDF
            num_labels: Number of labels to generate (max 16 per page)
        """
        c = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4

        # Draw page header
        self.draw_page_header(c)

        # Calculate grid layout (4 columns x 4 rows)
        labels_per_row = 4
        labels_per_col = 4

        # Adjust top margin to account for header
        top_margin = self.MARGIN + self.HEADER_HEIGHT

        label_count = 0
        for row in range(labels_per_col):
            for col in range(labels_per_row):
                if label_count >= num_labels:
                    break

                x = self.MARGIN + col * (self.LABEL_WIDTH + self.GAP)
                y = height - top_margin - (row + 1) * self.LABEL_HEIGHT - row * self.GAP

                self.draw_label(c, x, y, label_index=label_count)
                label_count += 1

            if label_count >= num_labels:
                break

        c.save()
        print(f"Generated {label_count} labels: {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate bottle labels for Dalston Rooftop Brewery',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s navarino-road
  %(prog)s navarino-road --labels 12
        '''
    )
    parser.add_argument(
        'batch',
        help='Batch slug (e.g., navarino-road)'
    )
    parser.add_argument(
        '--labels',
        type=int,
        default=16,
        help='Number of labels to generate (default: 16, max: 16)'
    )
    parser.add_argument(
        '--lot',
        type=str,
        help='Lot number (e.g., LOT 098 or LOT 098-A for variants)'
    )

    args = parser.parse_args()

    # Batch configuration
    # Future: Could parse from brew-log.md automatically
    batch_config = {
        'navarino-road': {
            'name': 'Navarino Road',
            'style': 'Hibiscus Mead',
            'recipe': 'recipes/hibiscus-mead.json',
            'abv': '11.81',
            'url': 'https://andreacampi.github.io/brewery/navarino-road/',
            'lot': 'LOT 098',
        }
    }

    config = batch_config.get(args.batch)
    if not config:
        print(f"Error: Unknown batch '{args.batch}'")
        print(f"Available batches: {', '.join(batch_config.keys())}")
        return 1

    # Validate label count
    if args.labels < 1 or args.labels > 16:
        print("Error: Labels must be between 1 and 16")
        return 1

    # Set up paths
    base_dir = Path(__file__).parent.parent
    recipe_path = base_dir / config['recipe']
    output_dir = base_dir / 'output' / 'labels'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.batch}-labels.pdf"

    # Determine lot number (CLI arg overrides config)
    lot_number = args.lot or config.get('lot')

    # Generate labels
    generator = BreweryLabelGenerator(
        batch_name=config['name'],
        style=config['style'],
        recipe_path=recipe_path,
        abv=config['abv'],
        url=config['url'],
        lot_number=lot_number
    )

    generator.generate_pdf(output_path, num_labels=args.labels)
    return 0


if __name__ == '__main__':
    exit(main())
