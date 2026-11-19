from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    ff_identifier_ids = fields.One2many(
        "ff.product.identifier",
        "product_id",
        string="Alternative Identifiers",
        copy=False,
    )
    ff_internal_identifier_data = fields.Json(
        string="Internal Reference Tags",
        compute="_compute_ff_identifier_data",
        inverse="_inverse_ff_internal_identifier_data",
        copy=False,
    )
    ff_barcode_identifier_data = fields.Json(
        string="Barcode Tags",
        compute="_compute_ff_identifier_data",
        inverse="_inverse_ff_barcode_identifier_data",
        copy=False,
    )
    ff_internal_identifier_values = fields.Json(
        string="Internal Reference Values",
        compute="_compute_ff_identifier_values",
        copy=False,
    )

    @api.depends("ff_identifier_ids.name", "ff_identifier_ids.identifier_type", "ff_identifier_ids.sequence")
    def _compute_ff_identifier_data(self):
        for product in self:
            aliases = product.ff_identifier_ids.filtered("active").sorted(
                key=lambda alias: (alias.identifier_type, alias.sequence, alias.id)
            )
            product.ff_internal_identifier_data = [
                {"id": alias.id, "name": alias.name, "sequence": alias.sequence}
                for alias in aliases
                if alias.identifier_type == "internal"
            ]
            product.ff_barcode_identifier_data = [
                {"id": alias.id, "name": alias.name, "sequence": alias.sequence}
                for alias in aliases
                if alias.identifier_type == "barcode"
            ]

    @api.depends("ff_identifier_ids.name", "ff_identifier_ids.identifier_type", "ff_identifier_ids.active")
    def _compute_ff_identifier_values(self):
        for product in self:
            product.ff_internal_identifier_values = product.ff_identifier_ids.filtered(
                lambda alias: alias.active and alias.identifier_type == "internal"
            ).mapped("name")

    def _inverse_ff_internal_identifier_data(self):
        for product in self:
            product._ff_apply_identifier_payload("internal", product.ff_internal_identifier_data)

    def _inverse_ff_barcode_identifier_data(self):
        for product in self:
            product._ff_apply_identifier_payload("barcode", product.ff_barcode_identifier_data)

    def _ff_apply_identifier_payload(self, identifier_type, payload):
        self.ensure_one()
        primary_field = "default_code" if identifier_type == "internal" else "barcode"
        names = []
        for item in payload or []:
            value = item.get("name") if isinstance(item, dict) else item
            value = self.env["ff.product.identifier"]._normalize_name(value)
            if value and value not in names:
                names.append(value)

        primary = self[primary_field] or ""
        if not primary and names:
            primary = names.pop(0)
            self.with_context(ff_identifier_sync=True).write({primary_field: primary})
        names = [name for name in names if name != primary]
        aliases = self.ff_identifier_ids.filtered(
            lambda alias: alias.active and alias.identifier_type == identifier_type
        )
        existing = {alias.name: alias for alias in aliases}
        for alias in aliases:
            if alias.name not in names:
                alias.unlink()
        for sequence, name in enumerate(names, start=1):
            alias = existing.get(name)
            if alias and alias.exists():
                alias.sequence = sequence * 10
                continue
            self.env["ff.product.identifier"].with_context(ff_identifier_apply=True).create(
                {
                    "product_id": self.id,
                    "name": name,
                    "identifier_type": identifier_type,
                    "sequence": sequence * 10,
                }
            )

    def _ff_sync_primary_fields(self):
        if self.env.context.get("ff_identifier_sync"):
            return
        Identifier = self.env["ff.product.identifier"]
        for product in self:
            for identifier_type, primary_field in (
                ("internal", "default_code"),
                ("barcode", "barcode"),
            ):
                aliases = product.ff_identifier_ids.filtered(
                    lambda alias: alias.active and alias.identifier_type == identifier_type
                ).sorted(key=lambda alias: (alias.sequence, alias.id))
                primary = (product[primary_field] or "").strip()
                if primary:
                    duplicate = aliases.filtered(lambda alias: alias.name == primary)
                    if duplicate:
                        duplicate.unlink()
                elif aliases:
                    promoted = aliases[0]
                    product.with_context(ff_identifier_sync=True).write(
                        {primary_field: promoted.name}
                    )
                    promoted.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            for field_name in ("default_code", "barcode"):
                if isinstance(values.get(field_name), str):
                    values[field_name] = values[field_name].strip()
        products = super().create(vals_list)
        products._ff_sync_primary_fields()
        return products

    def write(self, vals):
        vals = dict(vals)
        for field_name in ("default_code", "barcode"):
            if isinstance(vals.get(field_name), str):
                vals[field_name] = vals[field_name].strip()
        result = super().write(vals)
        self._ff_sync_primary_fields()
        return result

    @api.model
    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        if name:
            alias_domain = [
                ("name", operator, name),
                ("active", "=", True),
            ]
            alias_products = self.env["ff.product.identifier"].search(
                alias_domain, limit=limit
            ).mapped("product_id")
            if alias_products:
                products = self.search_fetch(
                    [("id", "in", alias_products.ids), *(domain or [])],
                    ["display_name"],
                    limit=limit,
                )
                if products:
                    return [(product.id, product.display_name) for product in products.sudo()]
        return super().name_search(name, domain, operator, limit)

    @api.model
    def ff_find_by_identifier(self, value, identifier_type=None):
        """Return one accessible product for integrations that need exact lookup."""
        value = self.env["ff.product.identifier"]._normalize_name(value)
        if not value:
            return self.browse()
        domain = [("name", "=", value), ("active", "=", True)]
        if identifier_type:
            domain.append(("identifier_type", "=", identifier_type))
        aliases = self.env["ff.product.identifier"].search(domain)
        products = aliases.mapped("product_id")
        if identifier_type in (None, "internal"):
            products |= self.search([("default_code", "=", value), ("active", "=", True)])
        if identifier_type in (None, "barcode"):
            products |= self.search([("barcode", "=", value), ("active", "=", True)])
        products = products._filtered_access("read")
        if len(products) > 1:
            raise ValidationError(
                _(
                    'Identifier "%(identifier)s" matches more than one accessible product.',
                    identifier=value,
                )
            )
        return products[:1]
