/** @odoo-module **/


import { patch } from "@web/core/utils/patch";

const UserAgent = require('voip.UserAgent');

patch(UserAgent.prototype, "ata_voip.UserAgent", {
    _formatPhoneNumber(number, prefix) {
        number = this._super(...arguments);
        if (number.startsWith("+")) {
            return number;
        }
        return `+${number}`;
    },
});
