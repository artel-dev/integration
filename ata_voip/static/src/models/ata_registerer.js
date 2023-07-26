/** @odoo-module **/

import { registerPatch } from "@mail/model/model_core";
import { attr } from "@mail/model/model_field";

registerPatch({
    name: "Registerer",
    lifecycleHooks: {
        _created() {
            const sipJsRegisterer = new window.SIP.Registerer(this.userAgent.__sipJsUserAgent, { expires: 60 });
            sipJsRegisterer.stateChange.addListener((state) => this.update({ state }));
            this.update({
                state: sipJsRegisterer.state,
                __sipJsRegisterer: sipJsRegisterer,
            });
        },
    },
});
