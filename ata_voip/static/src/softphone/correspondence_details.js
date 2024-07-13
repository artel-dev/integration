/* @odoo-module */

import { CorrespondenceDetails } from '@voip/softphone/correspondence_details'
import { patch } from "@web/core/utils/patch";

patch(CorrespondenceDetails.prototype, {

    /** @param {MouseEvent} ev */
    onClickPartner(ev) {
        this.softphone.fold();
        const action = {
            type: "ir.actions.act_window",
            res_model: "res.partner",
            views: [[false, "form"]],
            target: "new",
        };
        if (this.partner) {
            action.res_id = this.partner.id;
        }
        // TODO: Missing features from the previous code:
        // ─ if no partner but activity: prefill form with data from activity

        if (!this.partner) {
            let domain = [];
            if (this.phoneNumber) {
                domain = ['|',
                    ['phone', '=', this.phoneNumber],
                    ['mobile', '=', this.phoneNumber]];
            }
            const ids = this.orm.call(
                "res.partner",
                'search_read',
                [{
                domain: domain,
                fields: ['id'],
                limit: 1,
                }]);
            if (ids.length) {
                action.res_id = ids[0].id;
            }
        }
        if (action.res_id === undefined) {
            const context = {};
            if (this.phoneNumber) {
                context.phoneNumber = this.phoneNumber;
            }
            context['default_phone'] = this.phoneNumber
            context['default_mobile'] = this.phoneNumber
            action.context = context;
        }

        this.action.doAction(action);
    },


});