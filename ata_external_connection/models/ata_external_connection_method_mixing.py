from odoo import fields, models, api
from .ata_external_connection_method import AtaExternalConnectionMethod as ExtMethod


class AtaExternalConnectionMethodMixing(models.AbstractModel):
    _name = "ata.external.connection.method.mixing"
    _description = "Exchange http methods"

    method = fields.Many2one('ata.external.connection.method', string='Method of exchange')

    model_id = fields.Many2one('ir.model', string="Model", compute="_compute_model_name")
    model_name = fields.Char(string='Model Name', compute="_compute_model_name")
    model_desc = fields.Char(string="Model description", compute="_compute_model_name")

    @api.depends('method')
    @api.onchange('method')
    def _compute_model_name(self):
        for record in self:
            record.model_id, record.model_name, record.model_desc = record._get_model_data()

    def _get_model_data(self):
        method_model_name = self.method.model_name if self.method else False
        model_id = self.env['ir.model'].sudo().search([('model', '=', method_model_name)]) if method_model_name else False
        model_name = model_id.model if model_id else False
        model_desc = f'{model_id.name} ({model_id.model})' if model_id else f'All models'

        return model_id, model_name, model_desc

    @api.model
    def _get_method_for_name(self, method_name: str) -> ExtMethod:
        return self.env['ata.external.connection.method'].sudo().search([('name', '=', method_name)])

    @api.model
    def _get_ref_from_record(self, record):
        return "%s,%s" % (record._name, record.id) if record else None
