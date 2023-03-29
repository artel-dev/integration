from odoo import fields, models


class ExternalService(models.Model):
    """
    External service keeps datas about a method and parameters
    for a request to the server
    """
    _name = 'ata.external.service'
    _description = 'External service'

    name = fields.Char()
    description = fields.Char()
    active = fields.Boolean(default=True)
    system_id = fields.Many2one(comodel_name='ata.external.system')
    method_name = fields.Char()
    http_method = fields.Selection(selection=[
        ('GET', 'GET'),
        ('POST', 'POST')
    ])
    parameter_ids = fields.One2many(
        comodel_name='ata.external.service.parameter',
        inverse_name='service_id'
    )
