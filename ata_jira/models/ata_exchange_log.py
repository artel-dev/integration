from datetime import datetime
from odoo import fields, models, api


class ExchangeLog(models.Model):
    """
    Exchange log keeps information about server connection's session
    """
    _name = 'ata.exchange.log'
    _description = 'Exchange log'

    name = fields.Char()
    service_id = fields.Many2one(comodel_name='ata.external.service')
    server_address = fields.Char()
    server_port = fields.Integer()
    method_name = fields.Char()
    parameters = fields.Char()
    request = fields.Char()
    response = fields.Text()
    headers = fields.Char()
    status_code = fields.Integer()
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
            obj.day_delta = (datetime.today() - obj.start_date).days
