from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductIdentifiers(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Samsung Charger 25W"})
        cls.identifier_model = cls.env["ff.product.identifier"]

    def test_primary_and_alternatives_keep_native_fields(self):
        self.product.write({"default_code": " CHG-001 ", "barcode": "6221234567890"})
        self.identifier_model.create(
            {
                "product_id": self.product.id,
                "name": "SAM-25W",
                "identifier_type": "internal",
            }
        )
        self.identifier_model.create(
            {
                "product_id": self.product.id,
                "name": "6289876543210",
                "identifier_type": "barcode",
            }
        )
        self.product.invalidate_recordset()
        self.assertEqual(self.product.default_code, "CHG-001")
        self.assertEqual(self.product.barcode, "6221234567890")
        self.assertEqual(
            self.product.ff_identifier_ids.mapped("name"), ["SAM-25W", "6289876543210"]
        )
        self.assertEqual(self.env["product.product"]._fields["default_code"].type, "char")
        self.assertEqual(self.env["product.product"]._fields["barcode"].type, "char")

    def test_first_identifier_becomes_primary(self):
        product = self.env["product.product"].create({"name": "First Alias Product"})
        self.identifier_model.create(
            {"product_id": product.id, "name": "FIRST-001", "identifier_type": "internal"}
        )
        self.assertEqual(product.default_code, "FIRST-001")
        self.assertFalse(product.ff_identifier_ids)

    def test_remove_primary_promotes_earliest_alias(self):
        product = self.env["product.product"].create(
            {"name": "Promotion Product", "barcode": "100000000001"}
        )
        alias = self.identifier_model.create(
            {"product_id": product.id, "name": "100000000002", "identifier_type": "barcode"}
        )
        alias_name = alias.name
        product.write({"barcode": False})
        self.assertEqual(product.barcode, alias_name)
        self.assertFalse(alias.exists())

    def test_alias_search_returns_same_variant(self):
        product = self.env["product.product"].create(
            {"name": "Search Product", "default_code": "SEARCH-PRIMARY"}
        )
        self.identifier_model.create(
            {"product_id": product.id, "name": "SEARCH-ALIAS", "identifier_type": "internal"}
        )
        result = self.env["product.product"].name_search("SEARCH-ALIAS", operator="=")
        self.assertIn(product.id, [record_id for record_id, _label in result])
        template_result = self.env["product.template"].name_search("SEARCH-ALIAS", operator="=")
        self.assertIn(product.product_tmpl_id.id, [record_id for record_id, _label in template_result])

    def test_duplicate_alias_is_rejected(self):
        first = self.env["product.product"].create({"name": "First Duplicate Product"})
        second = self.env["product.product"].create({"name": "Second Duplicate Product"})
        self.identifier_model.create(
            {"product_id": first.id, "name": "DUP-001", "identifier_type": "barcode"}
        )
        with self.assertRaises(ValidationError):
            self.identifier_model.create(
                {"product_id": second.id, "name": "DUP-001", "identifier_type": "barcode"}
            )

    def test_payload_adapter_is_idempotent(self):
        product = self.env["product.product"].create(
            {"name": "Payload Product", "default_code": "PAY-001"}
        )
        product.ff_internal_identifier_data = [
            {"name": "PAY-002", "sequence": 10},
            {"name": "PAY-003", "sequence": 20},
        ]
        product.flush_recordset()
        product.invalidate_recordset()
        self.assertEqual(product.ff_identifier_ids.mapped("name"), ["PAY-002", "PAY-003"])
        product.ff_internal_identifier_data = [{"name": "PAY-003", "sequence": 10}]
        product.flush_recordset()
        product.invalidate_recordset()
        self.assertEqual(product.ff_identifier_ids.mapped("name"), ["PAY-003"])
