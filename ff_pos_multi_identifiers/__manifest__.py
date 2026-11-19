{
    "name": "Flous Flow POS Multi Identifiers",
    "summary": "Resolve product aliases in Odoo POS offline barcode and search flows",
    "version": "20.0.1.0.0",
    "category": "Point of Sale",
    "author": "Flous Flow",
    "website": "https://flousflow.com",
    "license": "LGPL-3",
    "images": [
        "static/description/icon.png",
        "static/description/banner.jpg",
    ],
    "depends": ["point_of_sale", "ff_product_multi_identifiers"],
    "data": [],
    "assets": {
        "point_of_sale._assets_pos": [
            "ff_pos_multi_identifiers/static/src/js/product_identifier.js",
            "ff_pos_multi_identifiers/static/src/js/product_product.js",
            "ff_pos_multi_identifiers/static/src/js/product_screen.js",
        ],
    },
    "installable": True,
    "application": False,
}
