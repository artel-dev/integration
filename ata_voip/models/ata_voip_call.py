from odoo import models
import datetime


class AtaVoipCall(models.Model):
    _inherit = 'voip.call'

    def write(self, vals):
        for record in self:
            body = ''
            if vals.get("state") is None and vals.get("start_time") is not None:
                timestamp = datetime.datetime.fromtimestamp(vals["start_time"])
                body = '{} {} {} start time: {}' \
                       '<div class="o_Activity_voipNumberPhone">' \
                       '<a class="o_Activity_voipCallPhone" href="#">{}</a>' \
                       '</div>'.format(record.state,
                                       record.direction,
                                       record.display_name,
                                       timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                       record.phone_number)
            elif vals.get("state") == 'done' and vals.get("duration") is not None:
                duration_seconds = round(vals["duration"] * 60, 0)
                minutes = int(vals["duration"])
                seconds = int(duration_seconds - minutes * 60)
                duration_log = "{}min {}sec".format(minutes, seconds)
                body = '{} {} {} duration: {}' \
                       '<div class="o_Activity_voipNumberPhone">' \
                       '<a class="o_Activity_voipCallPhone" href="#">{}</a>' \
                       '</div>'.format('done',
                                       record.direction,
                                       record.display_name,
                                       duration_log,
                                       record.phone_number)

            if body:
                partner_manager = self.env['res.partner']
                lead_manager = self.env['crm.lead']
                domain = [('phone_mobile_search', 'like', record.phone_number)]
                found_leads_count = lead_manager.search_count(domain)
                if found_leads_count == 1:
                    found_lead = lead_manager.search(domain)
                    found_lead.message_post(
                        body=body,
                        phone=record.phone_number)
                    if found_lead.partner_id:
                        found_lead.partner_id.message_post(body=body)
                elif found_leads_count == 0 and record.partner_id:
                    record.partner_id.message_post(
                        body=body,
                        phone=record.phone_number)
                else:
                    found_partner = partner_manager.search(domain)
                    if found_partner and len(found_partner) == 1:
                        found_partner.message_post(body=body)

        return super(AtaVoipCall, self).write(vals)
