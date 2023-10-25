from odoo import api, fields, models


class AtaExchangeQueue(models.Model):
    """
    stored objects that need to be exchanged with external systems
    """
    _name = "ata.exchange.queue"
    _description = "Exchange queue objects with external systems"

    ref_object = fields.Reference(
        selection=[],
        string="Object exchange")
    method = fields.Char(
        string='Method exchange in model')
    state_exchange = fields.Selection(
        selection=[
            ('new', 'New'),
            ('idle', 'Idle'),
            ('in_exchange', 'In exchange')],
        string='State exchange objects',
        default='new')

    @api.model
    def add(self, records, method=''):
        for record in records:
            ref_record = self._fields['ref_object'].convert_to_cache(record, self)
            if ref_record is not None:
                # check record in DB
                record_exist = self.sudo().search([
                    ('ref_object', '=', ref_record),
                    ('state_exchange', 'in', ('new', 'idle'))
                ])
                if not record_exist:
                    # add new record to DB
                    vals = {
                        'ref_object': ref_record,
                        'state_exchange': 'new',
                        'method': method
                    }
                    record_add = self.create(vals)
                    # start manual exchange over cron
                    if self.env["ata.exchange.queue.usage"].use_immediate_exchange(record_add.ref_object._name):
                        self.env.ref('ata_external_connection.ata_exchange_queue_cron_immediately')._trigger()

    def exchange(self, records=None):
        if not records:
            records = self.sudo().search([
                ('state_exchange', 'in', ('new', 'idle'))
            ], limit=100)

        records.write({'state_exchange': 'in_exchange'})

        for record in records:
            result_update = self.env["ata.external.connection.base"].exchange(record.ref_object, record.method)
            if result_update:
                record.unlink()
            else:
                record.write({'state_exchange': 'idle'})

    def exchange_immediately(self):
        records = self.sudo().search([
            ('state_exchange', '=', 'new')
        ], limit=100)
        records.write({'state_exchange': 'idle'})
        self.exchange(records)