/** @odoo-module **/

import { Registerer } from "@voip/core/registerer";
import { patch } from "@web/core/utils/patch";

patch(Registerer.prototype, {

    constructor(voip, sipJsUserAgent) {
        this.voip = voip;
        this.__sipJsRegisterer = new SIP.Registerer(sipJsUserAgent, {
            expires: 180,
        });
        this.__sipJsRegisterer.stateChange.addListener((state) => this._onStateChanged(state));
    },

});
