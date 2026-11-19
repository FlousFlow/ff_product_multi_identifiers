import { patch } from "@web/core/utils/patch";
import { ProductProduct } from "@point_of_sale/app/models/product_product";

patch(ProductProduct.prototype, {
    get searchString() {
        const values = this.ff_internal_identifier_values || [];
        return `${super.searchString} ${values.join(" ")}`.trim();
    },
});
