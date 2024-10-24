from odoo import api, fields, models
from .ata_external_connection_method import AtaExternalConnectionMethod as ExtMethod
from .ata_external_connection_base import AtaExternalConnectionClass as ExtClass


class AtaExchangeQueue(models.Model):
    """
    stored objects that need to be exchanged with external systems
    """
    _name = "ata.exchange.queue"
    _description = "Exchange queue objects with external systems"
    _inherit = ['ata.external.connection.method.mixing']

    @api.model
    def _selection_ref_object_model(self):
        models = self.env['ir.model'].sudo().search([
            ('model', 'in',
            [model_method.model_name for model_method in self.env['ata.external.connection.method'].sudo().search([])]
            ),
        ])
        return [(model.model, model.name) for model in models]

    ref_object = fields.Reference(
        selection='_selection_ref_object_model',
        string="Object exchange",
        ondelete='cascade')
    state_exchange = fields.Selection(
        selection=[
            ('new', 'New'),
            ('idle', 'Idle'),
            ('in_exchange', 'In exchange')],
        string='State exchange objects',
        default='new')

    @api.onchange('method')
    def _compute_ref_object(self):
        if self.method:
            self.ref_object = self.env[self.method.model_name].sudo().search([], limit=1)

    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        records = super(AtaExchangeQueue, self).search(args, offset, limit, order)
        if limit:
            return records
        for record in records:
            record._update_ref_object()
        return records

    def _update_ref_object(self):
        if self.ref_object:
            ref_model, ref_id = self.ref_object._name, self.ref_object.id
            if not self.env[ref_model].sudo().search([('id', '=', ref_id)], limit=1):
                self.ref_object = False

    @api.model
    def add_to_queue(self, record:ExtClass) -> bool:
        ExtConnection = self.env["ata.external.connection.base"]
        if isinstance(record.id, models.NewId):
            return False

        for method in record.ata_exchange_method_ids:
            if not ExtConnection._re_exchanged_in(record):
                if self.env["ata.exchange.queue.usage"].use_exchange_queue(method):
                    self._add(record, method)
                else:
                    ExtConnection.exchange(record, method)

    @api.model
    def _add(self, records: list[ExtClass], method: ExtMethod):
        for record in records:
            ref_record = self._fields['ref_object'].convert_to_cache(record, self)
            if ref_record is not None:
                # check record in DB
                record_exist = self.sudo().search([
                    ('ref_object', '=', ref_record),
                    ('state_exchange', 'in', ('new', 'idle'))
                ])
                if not record_exist:
                    # check the need over domain
                    ext_systems = self.env["ata.external.connection.domain"].get_ext_systems(record, method)
                    if ext_systems:
                        # add new record to DB
                        vals = {
                            'ref_object': ref_record,
                            'state_exchange': 'new',
                            'method': method.id
                        }
                        self.create(vals)
                        # start manual exchange over cron
                        if self.env["ata.exchange.queue.usage"].use_immediate_exchange(method):
                            self.env.ref('ata_external_connection.ata_exchange_queue_cron_immediately')._trigger()

    def test_queue(self):
        records = self.sudo().search([
            ('state_exchange', 'in', ('new', 'idle'))
        ], limit=100)

        self._check_ref_object(records)

    @api.model
    def _check_ref_object(self, records):
        # записи можуть бути видалені з БД, тому перед обміном перевіряємо, щоб вони ще були в БД
        for record in records:
            if not record.ref_object or not record.ref_object.exists():
                record.unlink()
                records -= record

    @api.model
    def exchange(self, records=None):
        if not records:
            records = self.sudo().search([
                ('state_exchange', 'in', ('new', 'idle'))
            ], limit=11)

        self._check_ref_object(records)

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
        ], limit=10)
        records.write({'state_exchange': 'idle'})
        self.exchange(records)

    def action_start_exchange(self):
        self.exchange(self)
