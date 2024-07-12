import datetime
from odoo import models


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
                lead_manager = self.env['crm.lead']
                sanitized_phone = lead_manager._phone_format(
                    number=record.phone_number)
                domain = [('phone_mobile_search', 'like', sanitized_phone)]
                partner_domain = domain
                if 'phone_mobile_search' not in partner_manager._fields:
                    partner_domain = ['|',
                                      ('phone', 'like', sanitized_phone),
                                      ('mobile', 'like', sanitized_phone)
                                      ]
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
                    found_partner = partner_manager.search(partner_domain)
                    if found_partner and len(found_partner) == 1:
                        found_partner.message_post(body=body)

        return super().write(vals)

    def get_contact_info(self):
        self.ensure_one()
        number = self.phone_number
        # Internal extensions could theoretically be one or two digits long.
        # phone_mobile_search doesn't handle numbers that short: do a regular
        # search for the exact match:
        if len(number) < 3:
            domain = ["|", ("phone", "=", number), ("mobile", "=", number)]
        # 00 and + both denote an international prefix. phone_mobile_search will
        # match both indifferently.
        elif number.startswith(("+", "00")):
            domain = [("phone_mobile_search", "=", number)]
        # USA: Calls between different area codes are usually prefixed with 1.
        # Conveniently, the country code for the USA also happens to be 1, so we
        # just need to add the + symbol to format it like an international call
        # and match what's supposed to be stored in the database.
        elif number.startswith("1"):
            domain = [("phone_mobile_search", "=", f"+{number}")]
        # 0 is the national prefix recommended by the ITU-T. This means that a
        # number starting with 0 will identify a national call in most
        # countries. We don't know the country code, so we can't convert the
        # number to the international format: Replace the prefix with a
        # wildcard.
        elif number.startswith("0"):
            domain = [("phone_mobile_search", "=like", f"%{number[1:]}")]
        # The phone number doesn't match any expected format. Could it be some
        # kind of internal extension? Try looking for an exact match:
        else:
            # domain = [("phone_mobile_search", "=", number)]
            number = '+' + number
            domain = [("phone_mobile_search", "=", number)]
        partner = self.env["res.partner"].search(domain, limit=1)
        if not partner:
            return False
        self.partner_id = partner
        return self.partner_id._format_contacts()[0]
