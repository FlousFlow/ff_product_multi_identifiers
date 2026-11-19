from odoo import api, models


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = "product.product"

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        if "ff_internal_identifier_values" not in fields:
            fields.append("ff_internal_identifier_values")
        return fields
