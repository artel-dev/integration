from odoo import models
import datetime


class AtaVoipPhoneCall(models.Model):
    _inherit = 'voip.phonecall'

    def write(self, vals):
        for record in self:
            body = ''
            if vals.get("state") is None and vals.get("start_time") is not None:
                timestamp = datetime.datetime.fromtimestamp(vals["start_time"])
                body = '{} {} {} start time: {}' \
                       '<div class="o_Activity_voipNumberPhone">' \
                       '<a class="o_Activity_voipCallPhone" t-on-click="activityView.onClickLandlineNumber" href="#">{}</a>' \
                       '</div>'.format(record.state,
                                       record.direction,
                                       record.display_name,
                                       timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                       record.phone)
            elif vals.get("state") == 'done' and vals.get("duration") is not None:
                duration_seconds = round(vals["duration"]*60, 0)
                minutes = int(vals["duration"])
                seconds = int(duration_seconds - minutes * 60)
                duration_log = "{}min {}sec".format(minutes, seconds)
                body = '{} {} {} duration: {}' \
                       '<div class="o_Activity_voipNumberPhone">' \
                       '<a class="o_Activity_voipCallPhone" t-on-click="activityView.onClickLandlineNumber" href="#">{}</a>' \
                       '</div>'.format('done',
                                       record.direction,
                                       record.display_name,
                                       duration_log,
                                       record.phone)

            if body:
                sanitized_phone = self.env['res.partner']._voip_sanitization(record.phone)
                finded_leeds_count = self.env['crm.lead'].search_count([('phone_mobile_search', 'like', sanitized_phone)])
                if finded_leeds_count == 1:
                    finded_leed = self.env['crm.lead'].search([('phone_mobile_search', 'like', sanitized_phone)])
                    finded_leed.message_post(body=body)
                    if finded_leed.partner_id:
                        finded_leed.partner_id.message_post(body=body)
                elif finded_leeds_count == 0 and record.partner_id:
                    record.partner_id.message_post(body=body)
                else:
                    finded_partner = self.env['res.partner'].search([('phone_mobile_search', 'like', sanitized_phone)])
                    finded_partner.message_post(body=body)

        return super(AtaVoipPhoneCall, self).write(vals)
