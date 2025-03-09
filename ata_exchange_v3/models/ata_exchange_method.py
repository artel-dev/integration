from odoo import fields, models


class AtaExchangeMethod(models.Model):
	_name = "ata.exchange.method"
	_description = "Methods of exchange with external systems"
	_rec_name = 'description'

	name = fields.Char(string="Name method")
	description = fields.Char(string="Description", translate=True)
	model_name = fields.Char(string="Model name")
	notification_queue_add = fields.Boolean(string="Addition to the exchange queue")
	notification_queue_remove = fields.Boolean(string="Removal from the exchange queue")
	notification_validation = fields.Boolean(string="Data validation errors")
	notification_first_failed = fields.Boolean(string="First unsuccessful exchange attempt")
	notification_successful = fields.Boolean(string="Successful exchange")
