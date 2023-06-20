odoo.define('ata_unitalk.PhoneCallDetailsOverride', function (require) {
    "use strict";

    var PhoneCallDetails = require('voip.phone_call_details');
    var patchMixin = require('web.patchMixin');

    var PhoneCallDetailsOverride = PhoneCallDetails.extend(patchMixin.patchMixin, {
        /**
         * Оновлена реалізація функції _onClickToPartner
         */
        async _onClickToPartner(ev) {
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
                    domain = [['mobile', '=', this.mobileNumber]];
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
                    default_phoneNumber: this.phoneNumber,
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
   return PhoneCallDetailsOverride;
});