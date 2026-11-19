# Flous Flow Product Multi Identifiers

Odoo 20 Community addon that stores alternative internal references and ordinary
unit barcodes for an existing `product.product` variant.

The native `default_code` and `barcode` fields remain `Char` fields and remain the
primary values. Alternatives are owned by `ff.product.identifier` and are shown
as tags in the original product form positions.

## Odoo Apps package

This addon is packaged for Odoo 20 Community with an Apps-ready icon and
description page under `static/description`. The optional POS companion is a
separate addon named `ff_pos_multi_identifiers` and depends on this module.

## Installation

Install `ff_product_multi_identifiers` from Apps. The optional POS integration is
provided by `ff_pos_multi_identifiers` and is not required by the base addon.

After installation, open Products and use the native Reference and Barcode
fields. Enter a value and press Enter to create a tag; the first value remains
the native primary value and subsequent values become aliases.

## Behavior

- The first value entered becomes the native primary field.
- Later values are stored as aliases of the exact same product variant.
- Removing the primary promotes the earliest remaining alias.
- Exact duplicate aliases and ambiguous barcode assignments are rejected.
- Identifier records can be imported/exported by product managers from the
  technical `ff.product.identifier` model/action when needed; the normal product
  form remains the primary user entry point.

## Scope

Aliases are ordinary unit identifiers. They are not product packaging codes and
do not change quantity, pricing, taxes, valuation, or accounting behavior.

## Compatibility

- Odoo 20 Community
- License: LGPL-3
- Python server-side validation with an OWL backend tags widget
- No Odoo core files are modified

## Known boundaries

The addon does not parse GS1 weight/quantity barcodes, does not replace native
packaging logic, and does not include a physical scanner or production-load test.
