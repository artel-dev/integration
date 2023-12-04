from odoo import api, fields, models


class AtaExchangeQueueUsage(models.Model):
    _name = "ata.exchange.queue.usage"
    _description = "Using exchange queue objects with external system"

    _inherit = ['ata.external.connection.method.mixing']

    usage = fields.Boolean(string="Use exchange queue")
    immediate = fields.Boolean(string="Immediate", store=True)

    @api.onchange('method')
    def _compute_immediate(self):
        for record in self:
            record.immediate = min(record.immediate, bool(record.method))

    @api.model
    def use_exchange_queue(self, method):
        return bool(self.search([
            ('method', 'in', (method, False)),
            ('usage', "=", True)
        ]))

    @api.model
    def use_immediate_exchange(self, method):
        return bool(self.search([
            ('method', '=', method),
            ('usage', "=", True),
            ('immediate', '=', True)
        ]))
