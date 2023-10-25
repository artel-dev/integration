from odoo import api, fields, models


class AtaExchangeQueueUsage(models.Model):
    _name = "ata.exchange.queue.usage"
    _description = "Using exchange queue objects with external system"

    model_id = fields.Many2one('ir.model', copy=False)
    model_name = fields.Char(string='Model Name', readonly=True, store=True, index=True, compute="_compute_model_name")
    model_desc = fields.Char(string="Model description", compute="_compute_model_description")
    usage = fields.Boolean(string="Use exchange queue")
    immediate = fields.Boolean(string="Immediate", store=True)

    @api.depends('model_id')
    def _compute_model_name(self):
        for record in self:
            record.model_name = record.model_id.model if record.model_id else False

    @api.depends('model_id')
    def _compute_model_description(self):
        for record in self:
            if record.model_id:
                record.model_desc = f'{record.model_id.name} ({record.model_id.model})'
            else:
                record.model_desc = f'All models'

    @api.onchange('model_id')
    def _compute_immediate(self):
        for record in self:
            record.immediate = min(record.immediate, bool(record.model_id))

    @api.model
    def use_exchange_queue(self, model_name):
        return bool(self.search([
            ('model_name', 'in', (model_name, False)),
            ('usage', "=", True)
        ]))

    @api.model
    def use_immediate_exchange(self, model_name):
        return bool(self.search([
            ('model_name', '=', model_name),
            ('usage', "=", True),
            ('immediate', '=', True)
        ]))
