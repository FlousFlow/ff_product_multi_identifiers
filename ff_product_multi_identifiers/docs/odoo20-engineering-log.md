# Odoo 20 Engineering Log

## 2026-11-19 — Multiple product identifiers

- Verified the Odoo 20 `product.product`/`product.template` reference and barcode
  fields remain native `Char` fields.
- Implemented aliases in a separate `ff.product.identifier` model, with variant
  ownership, normalization, uniqueness checks, primary promotion, ORM search,
  security, and Arabic translations.
- Added an OWL field widget that keeps the native Reference and Barcode positions
  while rendering values as editable tags.
- Added the optional POS loader/search/barcode fallback addon without changing
  core POS files.
- Backend tests and POS loader tests passed on the isolated `ff_module_dev20`
  database. Browser verification confirmed the product form loads and accepts
  primary/alternate tag input; a complete hardware scanner/offline tour remains
  a separate acceptance step.

## 2026-11-19 — Apps packaging

- Added the supplied Flous Flow cover artwork as `static/description/banner.jpg`.
- Added 128x128 Apps icons and Odoo Apps description pages to both addons.
- Added manifest `images` metadata and documented Odoo Apps compatibility,
  installation, scope, and known boundaries in the README.
- Static manifest, XML, Python compile, and asset-presence checks passed.
