from types import SimpleNamespace

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosMultiIdentifiers(TransactionCase):
    def test_pos_loads_identifier_model_and_product_alias_values(self):
        models_to_load = self.env["pos.session"]._load_pos_data_models(False)
        self.assertIn("ff.product.identifier", models_to_load)
        fields_to_load = self.env["product.product"]._load_pos_data_fields(
            SimpleNamespace(company_id=self.env.company)
        )
        self.assertIn("ff_internal_identifier_values", fields_to_load)

    def test_identifier_alias_is_available_to_pos_loader(self):
        product = self.env["product.product"].create(
            {
                "name": "POS Alias Product",
                "available_in_pos": True,
                "default_code": "POS-001",
            }
        )
        self.env["ff.product.identifier"].create(
            {
                "product_id": product.id,
                "name": "POS-ALIAS-001",
                "identifier_type": "internal",
            }
        )
        self.assertIn("POS-ALIAS-001", product.ff_internal_identifier_values)
