# Naming Conventions

## Lot Numbers

**Purpose**: Sequential tracking across ALL products for traceability and production management.

**Format**: `LOT XXX` where XXX is a sequential number across all brews (beers, meads, etc.)

**Current Range**: LOT 091-099 (historical), LOT 100+ (new brews)

**Bottling Variants**: Use letter suffixes (e.g., LOT 097-A, LOT 097-B, LOT 097-C) for different treatments of the same brew batch.

**Assignment**:
- Lot numbers are assigned when planning a brew (before brew day)
- Each brew consumes exactly one lot number (variants share the base number)
- Numbers increment sequentially without gaps
- Failed brews still consume a lot number for complete traceability

## Street Names

**Purpose**: Marketing names for specific brew styles.

| Street Name | Brew Type |
|-------------|-----------|
| De Beauvoir | Saison |
| Ridley Road | Spicy Mead |
| Junction | Basic Mead |
| Wilton Way | Citrus Mead |
| Deorlaf's Tun | Pale Ale (Voss yeast) |
| Fenton Close | Ginger Ale (alcohol free) |
| Colvestone | Berry Mead |
| Navarino Road | Hibiscus Mead |

**Usage**: Street names identify the brew style, not individual batches. Multiple brews of the same style share the same street name (e.g., all citrus meads are "Wilton Way"), differentiated by lot numbers.

**TBD Street Names**: Some brews may not have street names assigned yet. These are marked "TBD" in brew-log.md and can be named later.

## Usage Examples

| Brew | Lot Number | Street Name | Display Name |
|------|------------|-------------|--------------|
| First citrus mead | LOT 097 | Wilton Way | Wilton Way |
| Second citrus mead | LOT 105 | Wilton Way | Wilton Way |
| Hibiscus mead base variant | LOT 098-A | Navarino Road | Navarino Road |
| Hibiscus mead lavender variant | LOT 098-B | Navarino Road | Navarino Road (Lavender) |

## Integration Points

- **brew-log.md**: Primary record with lot numbers and street names
- **Bottle labels**: Display lot number for traceability
- **Brew sheets**: Include lot number for production tracking
- **Cellar (Notion)**: Lot number field for inventory management
- **Marketing site**: Uses street names (lot numbers optional/hidden)
