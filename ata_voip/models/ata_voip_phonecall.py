from odoo import models
import datetime


class AtaVoipPhoneCall(models.Model):
    _inherit = 'voip.phonecall'

    def write(self, vals):
        for record in self:
            if record.partner_id:
                if vals.get("state") is None and vals.get("start_time") is not None:
                    timestamp = datetime.datetime.fromtimestamp(vals["start_time"])
                    body = "{} {} {} start time: {}".format(record.state, record.direction,
                                                            record.display_name,
                                                            timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                    record.partner_id.message_post(body=body)
                elif vals.get("state") == 'done':
                    body = "{} {} {} duration: {}".format('done', record.direction,
                                                          record.display_name, vals["duration"])
                    record.partner_id.message_post(body=body)
        return super(AtaVoipPhoneCall, self).write(vals)
