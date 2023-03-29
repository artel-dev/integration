from odoo import fields, models


class ExternalServiceParameter(models.Model):
    """
    External service parameter keeps additional parameter
    for a method to a connection to the server
    """
    _name = 'ata.external.service.parameter'
    _description = 'External service parameter'

    name = fields.Char()
    service_id = fields.Many2one(comodel_name='ata.external.service')
    value = fields.Char()
    description = fields.Char()
