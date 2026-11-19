from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

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

    @api.depends(
        "product_variant_ids.default_code",
        "product_variant_ids.barcode",
        "product_variant_ids.ff_identifier_ids.name",
        "product_variant_ids.ff_identifier_ids.identifier_type",
        "product_variant_ids.ff_identifier_ids.sequence",
    )
    def _compute_ff_identifier_data(self):
        for template in self:
            variant = template.product_variant_ids[:1] if len(template.product_variant_ids) == 1 else self.env["product.product"]
            template.ff_internal_identifier_data = variant.ff_internal_identifier_data if variant else []
            template.ff_barcode_identifier_data = variant.ff_barcode_identifier_data if variant else []

    def _inverse_ff_internal_identifier_data(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids[:1]._ff_apply_identifier_payload(
                    "internal", template.ff_internal_identifier_data
                )

    def _inverse_ff_barcode_identifier_data(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids[:1]._ff_apply_identifier_payload(
                    "barcode", template.ff_barcode_identifier_data
                )

    @api.model
    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        if name:
            alias_products = self.env["ff.product.identifier"].search(
                [("name", operator, name), ("active", "=", True)],
                limit=limit,
            ).mapped("product_id.product_tmpl_id")
            if alias_products:
                templates = self.search_fetch(
                    [("id", "in", alias_products.ids), *(domain or [])],
                    ["display_name"],
                    limit=limit,
                )
                if templates:
                    return [(template.id, template.display_name) for template in templates.sudo()]
        return super().name_search(name, domain, operator, limit)
