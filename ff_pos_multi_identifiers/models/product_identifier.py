from odoo import api, models


class ProductIdentifier(models.Model):
    _name = "ff.product.identifier"
    _inherit = ["ff.product.identifier", "pos.load.mixin"]

    @api.model
    def _load_pos_data_domain(self, data):
        templates = data.get("product.template")
        return [
            ("product_id.product_tmpl_id", "in", templates.ids if templates else []),
            ("active", "=", True),
        ]

    @api.model
    def _load_pos_data_dependencies(self):
        return ["product.product"]

    @api.model
    def _load_pos_data_fields(self, config):
        return ["id", "name", "identifier_type", "product_id", "active", "company_id"]
