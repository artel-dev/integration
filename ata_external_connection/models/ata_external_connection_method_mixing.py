from odoo import fields, models, api


class AtaExternalConnectionMethodMixing(models.AbstractModel):
    _name = "ata.external.connection.method.mixing"
    _description = "Exchange http methods"

    model_id = fields.Many2one('ir.model', string="Model", compute="_compute_model_name")
    model_name = fields.Char(string='Model Name', readonly=True, compute="_compute_model_name")

    method = fields.Selection(
        selection=[],
        string="Exchange http methods"
    )

    # dictionary of correspondence methods and models that are used to define a domain
    _method_model_dict = {}

    @api.depends('method')
    @api.onchange('method')
    def _compute_model_name(self):
        for record in self:
            record.model_id, record.model_name = self._get_model_data_from_dict(record.method)

            # _model = record._method_model_dict.get(record.method, False)
            # record.model_id = self.env['ir.model'].sudo().search([('model', '=', _model)])
            # record.model_name = record.model_id.model

    @api.model
    def _get_model_data_from_dict(self, method):
        _model = self._method_model_dict.get(method, False)
        model_id = self.env['ir.model'].sudo().search([('model', '=', _model)])
        model_name = model_id.model

        return model_id, model_name

    def method_model_add(self, data: dict):
        self._method_model_dict.update(data)
