from odoo import fields, models


class AtaExchangeMethod(models.Model):
	_name = "ata.exchange.method"
	_description = "Methods of exchange with external systems"
	_rec_name = 'description'

	name = fields.Char(string="Name method")
	description = fields.Char(string="Description", translate=True)
	model_name = fields.Char(string="Model name")
