from datetime import datetime
from odoo import fields, models, api


class ExchangeLog(models.Model):
    """
    Exchange log keeps information about server connection's session
    """
    _name = 'ata.exchange.log'
    _description = 'Exchange log'
    _order = 'start_date desc'

    name = fields.Char()
    exchange_id = fields.Char()
    system_id = fields.Many2one(
        comodel_name='ata.external.system',
    )
    server_address = fields.Char()
    server_port = fields.Integer()
    method_name = fields.Char()
    parameters = fields.Char()
    request_body = fields.Text()
    request = fields.Char()
    response = fields.Text()
    headers = fields.Char()
    status_code = fields.Integer()
    create_date = fields.Datetime()
    is_executed = fields.Boolean()
    execution_date = fields.Datetime()
    is_processed = fields.Boolean()
    processing_date = fields.Datetime()
    number_of_attempts = fields.Integer()
    start_date = fields.Datetime()
    finish_date = fields.Datetime()
    execution_time = fields.Float(
        digits=(15, 2),
        compute='_compute_execution_time',
        store=True
    )
    day_delta = fields.Integer(compute='_compute_day_delta', store=True)
    color = fields.Integer()

    @api.depends('start_date', 'finish_date')
    def _compute_execution_time(self):
        for obj in self:
            execution_timedelta = obj.finish_date - obj.start_date
            if execution_timedelta:
                obj.execution_time = execution_timedelta.total_seconds()

    @api.depends('start_date')
    def _compute_day_delta(self):
        for obj in self:
            obj.day_delta = (datetime.today() -
                (obj.start_date if isinstance(obj.start_date, datetime) else datetime.today())).days

    def action_delete_all(self):
        self.sudo().search([]).unlink()
