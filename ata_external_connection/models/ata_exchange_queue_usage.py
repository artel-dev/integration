from odoo import api, fields, models

from .ata_external_connection_method import AtaExternalConnectionMethod as ExtMethod


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
    def use_exchange_queue(self, method: ExtMethod):
        return bool(self.search([
            ('method', 'in', (method.id, False)),
            ('usage', "=", True)
        ]))

    @api.model
    def use_immediate_exchange(self, method: ExtMethod):
        return bool(self.search([
            ('method', '=', method.id),
            ('usage', "=", True),
            ('immediate', '=', True)
        ]))

    def action_test_queue(self):
        self.env["ata.exchange.queue"].test_queue()
