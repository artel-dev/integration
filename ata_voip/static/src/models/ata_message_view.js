/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';

registerPatch({
    name: "MessageView",
    recordMethods: {
        /**
         * @override
         */
        async onClick(ev) {
            await this._super(...arguments);
            if (ev.target.tagName === 'A') {
                if (ev.target.closest('.o_Activity_voipCallPhone')){
                    ev.preventDefault();
                    this.env.services.voip.call({
                        number: ev.target.text,
                        resModel: this.messaging.currentPartner.model,
                        resId: this.messaging.currentPartner.id,
                        fromActivity: false,
                    });
                }
                return;
            }
        },
    },
});
