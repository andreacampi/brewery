"""Tests for the bottle label generator."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from generate_labels import BreweryLabelGenerator

RECIPE = Path(__file__).parent.parent / 'recipes' / 'ancient-orange-mead-2026-06.json'


def make_generator():
    return BreweryLabelGenerator(
        batch_name='Wilton Way',
        style='Citrus Mead',
        recipe_path=RECIPE,
        abv='14.4',
        url='https://example.test/',
        lot_number='LOT 106',
    )


class ExtractIngredientsTest(unittest.TestCase):
    def test_excludes_yeast_without_the_word_yeast_in_its_name(self):
        """EC-1118 is yeast but its name lacks 'yeast'; it must not appear on the label."""
        ingredients = make_generator().ingredients
        self.assertNotIn('ec-1118', ingredients.lower())

    def test_includes_the_flavour_ingredients(self):
        ingredients = make_generator().ingredients.lower()
        for expected in ('honey', 'orange', 'cinnamon', 'cloves', 'allspice', 'raisins'):
            self.assertIn(expected, ingredients)


if __name__ == '__main__':
    unittest.main()
