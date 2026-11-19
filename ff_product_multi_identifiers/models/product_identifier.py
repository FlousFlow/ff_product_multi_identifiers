from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductIdentifier(models.Model):
    _name = "ff.product.identifier"
    _description = "Product Identifier Alias"
    _order = "identifier_type, sequence, id"

    product_id = fields.Many2one(
        "product.product",
        string="Product Variant",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(string="Identifier", required=True, index=True)
    identifier_type = fields.Selection(
        [
            ("internal", "Internal Reference"),
            ("barcode", "Barcode"),
        ],
        string="Type",
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True, index=True)
    sequence = fields.Integer(default=10, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="product_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    _unique_identifier = models.Constraint(
        "UNIQUE(product_id, identifier_type, name)",
        "The same identifier cannot be assigned twice to one product.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        normalized = []
        for values in vals_list:
            values = dict(values)
            values["name"] = self._normalize_name(values.get("name"))
            if not values["name"]:
                raise ValidationError(_("An identifier cannot be empty."))
            product = self.env["product.product"].browse(values.get("product_id")).exists()
            if not product:
                raise ValidationError(_("A product variant is required for an identifier."))
            identifier_type = values.get("identifier_type")
            if identifier_type not in ("internal", "barcode"):
                raise ValidationError(_("The identifier type is invalid."))
            values["product_id"] = product.id
            if not values.get("sequence"):
                values["sequence"] = self._next_sequence(product, identifier_type)

            # The first value is the native primary field. Only subsequent values
            # are stored as aliases, so the core Char field remains authoritative.
            primary_field = "default_code" if identifier_type == "internal" else "barcode"
            if not product[primary_field]:
                self._check_identifier_conflicts(product, values["name"], identifier_type)
                product.with_context(ff_identifier_sync=True).write({primary_field: values["name"]})
                continue

            self._check_identifier_conflicts(product, values["name"], identifier_type)
            normalized.append(values)
        return super().create(normalized) if normalized else self.browse()

    def write(self, vals):
        vals = dict(vals)
        if "name" in vals:
            vals["name"] = self._normalize_name(vals["name"])
            if not vals["name"]:
                raise ValidationError(_("An identifier cannot be empty."))
        if "identifier_type" in vals and vals["identifier_type"] not in ("internal", "barcode"):
            raise ValidationError(_("The identifier type is invalid."))
        if "name" in vals or "identifier_type" in vals or "product_id" in vals:
            for identifier in self:
                product = self.env["product.product"].browse(
                    vals.get("product_id", identifier.product_id.id)
                ).exists()
                self._check_identifier_conflicts(
                    product,
                    vals.get("name", identifier.name),
                    vals.get("identifier_type", identifier.identifier_type),
                    exclude=identifier,
                )
        return super().write(vals)

    @api.constrains("name", "product_id", "identifier_type", "active")
    def _check_identifier_constraints(self):
        for identifier in self.filtered("active"):
            self._check_identifier_conflicts(
                identifier.product_id,
                identifier.name,
                identifier.identifier_type,
                exclude=identifier,
            )

    @staticmethod
    def _normalize_name(value):
        return value.strip() if isinstance(value, str) else value

    def _next_sequence(self, product, identifier_type):
        aliases = self.search(
            [
                ("product_id", "=", product.id),
                ("identifier_type", "=", identifier_type),
            ],
            order="sequence desc, id desc",
            limit=1,
        )
        return (aliases.sequence + 10) if aliases else 10

    def _company_domain(self, product):
        if product.company_id:
            return [("company_id", "in", [False, product.company_id.id])]
        # A shared product is visible in every company, so its identifiers must
        # not collide with any company-specific identifier.
        return []

    def _check_identifier_conflicts(self, product, name, identifier_type, exclude=None):
        if not product or not name:
            return
        name = self._normalize_name(name)
        company_domain = self._company_domain(product)
        alias_domain = [
            ("name", "=", name),
            ("active", "=", True),
            *company_domain,
        ]
        aliases = self.search(alias_domain)
        if exclude:
            aliases -= exclude
        other_aliases = aliases.filtered(lambda alias: alias.product_id != product)
        if other_aliases:
            raise ValidationError(
                _(
                    'Identifier "%(identifier)s" is already assigned to another product.',
                    identifier=name,
                )
            )

        product_domain = [("active", "=", True), *company_domain]
        if identifier_type == "barcode":
            primary_matches = self.env["product.product"].search(
                [("barcode", "=", name), *product_domain]
            )
            primary_matches |= self.env["product.template"].search(
                [("barcode", "=", name), *product_domain]
            ).mapped("product_variant_id")
            if primary_matches.filtered(lambda candidate: candidate != product):
                raise ValidationError(
                    _(
                        'Barcode "%(barcode)s" is already assigned to another product.',
                        barcode=name,
                    )
                )
            packaging_domain = [("barcode", "=", name)]
            if product.company_id:
                packaging_domain.append(("company_id", "in", [False, product.company_id.id]))
            if self.env["product.uom"].search_count(packaging_domain, limit=1):
                raise ValidationError(
                    _("Barcode \"%s\" is already used by a product packaging or unit.", name)
                )
        else:
            primary_matches = self.env["product.product"].search(
                [("default_code", "=", name), *product_domain]
            )
            if primary_matches.filtered(lambda candidate: candidate != product):
                raise ValidationError(
                    _(
                        'Internal reference "%(reference)s" is already assigned to another product.',
                        reference=name,
                    )
                )

        # Do not allow a new code to resolve to two different products through
        # the two supported lookup namespaces.
        opposite_type = "barcode" if identifier_type == "internal" else "internal"
        opposite_aliases = self.search(
            [
                ("name", "=", name),
                ("identifier_type", "=", opposite_type),
                ("active", "=", True),
                *company_domain,
            ]
        ).filtered(lambda alias: alias.product_id != product)
        if opposite_aliases:
            raise ValidationError(
                _(
                    'Identifier "%(identifier)s" conflicts with another product lookup code.',
                    identifier=name,
                )
            )
