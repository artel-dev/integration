from odoo import api, fields, models


class AtaExchangeObjects(models.Model):
    """
    stored objects that need to be exchanged with external systems
    """
    _name = "ata.exchange.objects"
    _description = "Exchange objects with external systems"

    ref_object = fields.Reference(
        selection=[('res.partner', 'Partner'), ('crm.lead', 'Lead')],
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
                    # record_add.exchange()
                    self.env.ref('ata_external_connection.ata_exchange_objects_cron_immediately')._trigger()

    def exchange(self, records=None):
        if not records:
            records = self.sudo().search([
                ('state_exchange', 'in', ('new', 'idle'))
            ], limit=100)

        records.write({'state_exchange': 'in_exchange'})

        for record in records:
            model_id = record.ref_object._name
            records_update = self.env[model_id].search([('id', '=', record.ref_object.id)])
            func_name = f'ata_update_{record.method}' if record.method else 'ata_update_ext_system'
            if hasattr(records_update, func_name):
                func_update = getattr(records_update, func_name)
                if func_update():
                    record.unlink()
                else:
                    record.write({'state_exchange': 'idle'})
            else:
                pass

    def exchange_immediately(self):
        records = self.sudo().search([
            ('state_exchange', '=', 'new')
        ], limit=100)
        records.write({'state_exchange': 'idle'})
        self.exchange(records)
