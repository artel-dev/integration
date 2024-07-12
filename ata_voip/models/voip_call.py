from odoo import models
import datetime


class AtaVoipCall(models.Model):
    _inherit = 'voip.call'

    def write(self, vals):
        dt = datetime.datetime
        for record in self:
            body = ''
            if (vals.get("state") is None and
                    vals.get("start_date") is not None):
                # timestamp = dt.fromtimestamp(vals["start_date"])
                timestamp = vals["start_date"]
                body = ('<div class ="o-mail-Activity-voip-landline-number">'
                        '<span>{} {} {} start time: {}</span>'
                        '<a href="#">{}</a>'
                        '</div>').format(
                    record.state,
                    record.direction,
                    record.display_name,
                    timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    record.phone_number)

            elif (vals.get("state") == 'done' and
                  vals.get("end_date") is not None):
                # start_time = dt.fromtimestamp(vals["start_date"])
                # end_time = dt.fromtimestamp(vals["end_date"])
                start_time = vals["start_date"]
                end_time = vals["end_date"]
                delta = end_time - start_time
                duration_seconds = round(delta.total_seconds())
                minutes = round(duration_seconds/60)
                seconds = int(duration_seconds - minutes * 60)
                duration_log = "{}min {}sec".format(minutes, seconds)
                body = ('<div class ="o-mail-Activity-voip-landline-number">'
                        '<span>{} {} {} duration: {}</span>'
                        '<a href="#">{}</a>'
                        '</div>').format(
                    'done',
                    record.direction,
                    record.display_name,
                    duration_log,
                    record.phone_number)

            if body:
                partner_manager = self.env['res.partner']
                sanitized_phone = partner_manager._voip_sanitization(
                    record.phone_number)
                lead_manager = self.env['crm.lead']
                domain = [('phone_mobile_search', 'like', sanitized_phone)]
                found_leads_count = lead_manager.search_count(domain)
                if found_leads_count == 1:
                    found_lead = lead_manager.search(domain)
                    found_lead.message_post(body=body, phone=sanitized_phone)
                    if found_lead.partner_id:
                        found_lead.partner_id.message_post(body=body)
                elif found_leads_count == 0 and record.partner_id:
                    record.partner_id.message_post(
                        body=body, phone=sanitized_phone)
                else:
                    found_partner = partner_manager.search(domain)
                    if found_partner and len(found_partner) == 1:
                        found_partner.message_post(body=body)

        return super().write(vals)
