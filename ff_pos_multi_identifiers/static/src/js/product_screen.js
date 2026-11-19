import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";

patch(ProductScreen.prototype, {
    async _getProductByBarcode(code) {
        const product = await super._getProductByBarcode(code);
        if (product) {
            return product;
        }
        const aliases = this.pos.models["ff.product.identifier"]?.getAllBy(
            "name",
            code.base_code
        );
        const barcodeAlias = aliases?.find(
            (alias) => alias.identifier_type === "barcode" && alias.active
        );
        return barcodeAlias?.product_id || null;
    },
});
