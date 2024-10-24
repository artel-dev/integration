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

//        if (!this.partner) {
//            let domain = [];
//            if (this.landlineNumber && this.mobileNumber) {
//                domain = ['|',
//                    ['phone', '=', this.landlineNumber],
//                    ['mobile', '=', this.mobileNumber]];
//            }
//            else if (this.landlineNumber) {
//                domain = ['|',
//                    ['phone', '=', this.landlineNumber],
//                    ['mobile', '=', this.landlineNumber]];
//            }
//            else if (this.mobileNumber) {
//                domain = ['|',
//                    ['phone', '=', this.mobileNumber],
//                    ['mobile', '=', this.mobileNumber]];
//            }
//            const ids = this.orm.call(
//                "res.partner",
//                'search_read',
//                [],
//                {
//                domain: domain,
//                fields: ['id'],
//                limit: 1,
//                }
//                );
//            if (ids.length) {
//                action.res_id = ids[0].id;
//            }
//        }
        if (action.res_id === undefined) {
            const context = {};
            if (this.landlineNumber) {
                context.phoneNumber = this.landlineNumber;
            }
            context['default_phone'] = this.landlineNumber
            context['default_mobile'] = this.mobileNumber
            action.context = context;
        }

        this.action.doAction(action);
    },


});