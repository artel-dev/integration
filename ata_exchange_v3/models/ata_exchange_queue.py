from odoo import api, fields, models, _

from typing import Tuple, List, Union, Dict, cast, Optional

from .ata_exchange_method import AtaExchangeMethod as ExMethod
from .ata_exchange_base   import AtaExchangeClass  as ExClass


class AtaExchangeQueue(models.Model):
    """
    stored objects that need to be exchanged with external systems
    """
    _name = "ata.exchange.queue"
    _description = "Exchange queue objects with external systems"
    _inherit = ['ata.exchange.method.mixing']

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
    attempt_number = fields.Integer(
        string='Attempt number',
        default=0)
    error_last = fields.Text(string="Last error")

    # region [ref_object] fold
    @api.model
    def _selection_ref_object_model(self):
        models = self.env['ir.model'].sudo().search([
            ('model', 'in',
            [model_method.model_name for model_method in self.env['ata.exchange.method'].sudo().search([])]
            ),
        ])
        return [(model.model, model.name) for model in models]

    @api.onchange('method')
    def _compute_ref_object(self):
        if self.method:
            self.ref_object = self.env[self.method.model_name].sudo().search([], limit=1)

    @property
    def ref_object_model(self) -> Optional[models.BaseModel]:
        if self.ref_object:
            return cast(models.BaseModel, self.ref_object)
        return None

    def _update_ref_object(self):
        ref_object = self.ref_object_model
        if ref_object:
            ref_model, ref_id = ref_object._name, ref_object.id
            # якщо змінилась модель для об'єкта, то очищуємо об'єкт
            if not self.env[ref_model].sudo().search([('id', '=', ref_id)], limit=1):
                self.ref_object = False
    
    def _check_ref_object(self):
        # записи можуть бути видалені з БД, тому перед обміном перевіряємо, щоб вони ще були в БД
        to_unlink = self.filtered(lambda r: not r.ref_object_model or not r.ref_object_model.exists())
        to_unlink.unlink()
        return self - to_unlink

    def get_ref_object_as_exclass(self) -> Union[ExClass, None]:
        self.ensure_one()
        ref_object = self.ref_object_model
        if isinstance(ref_object, ExClass):
            return cast(ExClass, ref_object)
        return None
    # endregion

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        records = super(AtaExchangeQueue, self).search(domain, offset, limit, order, count)
        if limit:
            return records
        for record in records:
            record._update_ref_object()
        return records

    @api.model
    def add_to_queue(self, record: ExClass):
        ExBase = self.env["ata.exchange.base"]
        if isinstance(record.id, models.NewId):
            return False

        for method in record.ata_exchange_compute_methods():
            if not ExBase._re_exchanged_in(record):
                if self.env["ata.exchange.queue.usage"].use_exchange_queue(method):
                    self._add_to_queue(record, method)
                else:
                    ExBase.exchange(record, method)

    @api.model
    def _add_to_queue(self, records: ExClass, method: ExMethod):
        for record in records:
            ref_record = self._fields['ref_object'].convert_to_cache(record, self)
            if ref_record is not None:
                # check record in DB
                record_exist = self.sudo().search([
                    ('ref_object', '=', ref_record),
                    ('state_exchange', 'in', ('new', 'idle')),
                    ('method', '=', method.id)
                ])
                if not record_exist:
                    # check the need over domain
                    ext_systems = self.env["ata.exchange.domain"].get_ext_systems(record, method)
                    if ext_systems and record.ata_exchange_validate_main(method):
                        # add new record to DB                        
                        self.create({
                            'ref_object': ref_record,
                            'state_exchange': 'new',
                            'method': method.id
                        })
                        # start manual exchange over cron
                        if self.env["ata.exchange.queue.usage"].use_immediate_exchange(method):
                            self.env.ref('ata_exchange_v3.ata_exchange_queue_cron_immediately')._trigger()

    def test_queue(self):
        records = self.sudo().search([
            ('state_exchange', 'in', ('new', 'idle'))
        ], limit=100)

        records._check_ref_object()

    @api.model
    def exchange(self, records=None):
        if not records:
            records = self.sudo().search([
                ('state_exchange', 'in', ('new', 'idle'))
            ], order="state_exchange DESC, attempt_number", limit=10)

        records = records._check_ref_object()

        records.write({'state_exchange': 'in_exchange'})

        for record in records:
            if (ref_object_exclass := record.get_ref_object_as_exclass()):
                result_update = self.env["ata.exchange.base"].exchange(ref_object_exclass, record.method)
                if result_update.success:
                    if record.method.notification_successful and (ref_object := record.get_ref_object_as_exclass()):
                        ref_object.ata_exchange_notification(_("Exchange successful"))
                
                if result_update.delete_queue:
                    record.unlink()
                else:
                    record.write({
                        'state_exchange': 'idle',
                        'error_last': result_update.error,
                    })

    def exchange_immediately(self):
        records = self.sudo().search([
            ('state_exchange', '=', 'new')
        ], limit=10)
        records.write({'state_exchange': 'idle'})
        self.exchange(records)

    def action_start_exchange(self):
        self.exchange(self)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.method.notification_queue_add and (ref_object:=record.get_ref_object_as_exclass()):
                ref_object.ata_exchange_notification(_("Added to the exchange queue"))

        return records

    def write(self, vals):
        for record in self:
            # при додаванні на обмін збільшуємо лічильник спроб
            super(AtaExchangeQueue, record).write({
                **vals,
                **({"attempt_number": record.attempt_number + 1}
                    if "state_exchange" in vals and vals.get("state_exchange", False) == 'in_exchange'
                    else {})
            })

            # при першій невдалій спробі обміну відправляємо повідомлення
            if record.method.notification_first_failed and \
                record.state_exchange == 'idle' and \
                record.attempt_number == 1 and \
                (ref_object := record.get_ref_object_as_exclass()):
                    ref_object.ata_exchange_notification(_("Failed to exchange: ") + record.error_last)

    def unlink(self):
        for record in self:
            if record.method.notification_queue_remove and (ref_object := record.get_ref_object_as_exclass()):
                ref_object.ata_exchange_notification(_("Removed from the exchange queue"))

        return super().unlink()
