from odoo import fields, models


class ExternalRequest(models.TransientModel):
    _name = 'ata.external.request'
    _description = 'External request'

    name = fields.Char()
    exchange_id = fields.Many2one(comodel_name='ata.exchange')
    issue_id = fields.Integer()
    system_id = fields.Many2one(comodel_name='ata.external.system')
    service_id = fields.Many2one(comodel_name='ata.external.service')
    method_name = fields.Char()
    parameters = fields.Char()
    status_code = fields.Integer()
    result = fields.Char()
    headers = fields.Char()
    create_date = fields.Datetime()
    is_executed = fields.Boolean()
    execution_date = fields.Datetime()
    is_processed = fields.Boolean()
    processing_date = fields.Datetime()
    number_of_attempts = fields.Integer()
