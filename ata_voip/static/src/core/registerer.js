/** @odoo-module **/

import { Registerer } from "@voip/core/registerer";
import { patch } from "@web/core/utils/patch";

patch(Registerer, {

    EXPIRATION_INTERVAL: 180,

});
