/** @odoo-module **/


import { useBus, useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { StatusBarField } from "@web/views/fields/statusbar/statusbar_field";
import { WarningDialog } from "@web/core/errors/error_dialogs";

const PhoneCallDetails = require('voip.PhoneCallDetails');
const config = require('web.config');

patch(PhoneCallDetails.prototype, "ata_voip.PhoneCallDetails", {
     async _onClickToPartner(ev) {
        const _super = this._super.bind(this);
        await Promise.resolve();

        ev.preventDefault();
        if (!config.device.isMobileDevice) {
            this.trigger_up('fold_panel');
        }
        let resId = this.partnerId;
        if (!this.partnerId) {
            let domain = [];
            if (this.phoneNumber && this.mobileNumber) {
                domain = ['|',
                    ['phone', '=', this.phoneNumber],
                    ['mobile', '=', this.mobileNumber]];
            } else if (this.phoneNumber) {
                domain = ['|',
                    ['phone', '=', this.phoneNumber],
                    ['mobile', '=', this.phoneNumber]];
            } else if (this.mobileNumber) {
                domain = ['|',
                    ['phone', '=', this.mobileNumber],//+ATA Boretskiy
                    ['mobile', '=', this.mobileNumber]];
            }
            const ids = await this._rpc({
                method: 'search_read',
                model: "res.partner",
                kwargs: {
                    domain,
                    fields: ['id'],
                    limit: 1,
                }
            });
            if (ids.length) {
                resId = ids[0].id;
            }
        }
        if (resId !== undefined) {
            this.do_action({
                res_id: resId,
                res_model: "res.partner",
                target: 'new',
                type: 'ir.actions.act_window',
                views: [[false, 'form']],
            }, {
                fullscreen: config.device.isMobile
            });
        } else {
            const context = {};
            if (this.phoneNumber) {
                context.phoneNumber = this.phoneNumber;
            }
            if (this.email) {
                context.email = this.email;
            }
            if (this.mobileNumber) {
                context.mobileNumber = this.mobileNumber;
            }
            context['default_phone'] = this.phoneNumber //+ATA Boretskiy
            context['default_mobile'] = this.mobileNumber //+ATA Boretskiy
            this.do_action({
                context,
                res_model: 'res.partner',
                target: 'new',
                type: 'ir.actions.act_window',
                views: [[false, 'form']],
            }, {
                fullscreen: config.device.isMobile
            });
        }
    },
});