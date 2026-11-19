{
    "name": "Multi Product Identifiers",
    "summary": "Multiple internal references and barcodes per product variant",
    "version": "20.0.1.0.0",
    "category": "Inventory/Product",
    "author": "Flous Flow",
    "website": "https://flousflow.com",
    "license": "LGPL-3",
    "maintainer": "Flous Flow",
    "images": [
        "static/description/banner.jpg",
    ],
    "depends": ["product", "web"],
    "data": [
        "security/ir.access.csv",
        "views/product_identifier_views.xml",
        "views/product_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ff_product_multi_identifiers/static/src/js/identifier_tags_field.js",
            "ff_product_multi_identifiers/static/src/xml/identifier_tags_field.xml",
            "ff_product_multi_identifiers/static/src/scss/identifier_tags_field.scss",
        ],
    },
    "i18n": ["i18n/ar.po"],
    "installable": True,
    "application": True,
}
