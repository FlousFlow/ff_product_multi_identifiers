import { registry } from "@web/core/registry";
import { Base } from "@point_of_sale/app/models/related_models";

export class ProductIdentifier extends Base {
    static pythonModel = "ff.product.identifier";
}

registry.category("pos_available_models").add(ProductIdentifier.pythonModel, ProductIdentifier);
