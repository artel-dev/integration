from odoo import fields, models


class AtaExchangeMethod(models.Model):
	_name = "ata.exchange.method"
	_description = "Methods of exchange with external systems"
	_rec_name = 'description'

	name = fields.Char(
		string="Name method",
		required=True)
	description = fields.Char(
		string="Description",
		translate=True)
	type = fields.Selection(
		string="Type",
		selection=[
			('outgoing_data', 'Transfer data from Odoo to external system'),
			('request_data', 'Request data from external systems'),
			('incoming_request', 'Incoming request handler'),
		],
		required=True)
	start_over_cron = fields.Boolean(
		string="Start over cron")	
	model_name = fields.Char(
		string="Model name")
	model_id = fields.Many2one('ir.model', string="Model")
	need_api_key = fields.Boolean(
		string="Need API key",
		compute='_compute_need_api_key',)

	def _compute_need_api_key(self):
		for record in self:
			record.need_api_key = bool(self.env['ata.exchange.api.key'].search([('methods_ids', 'in', record.id)], limit=1))

	notification_queue_add 		= fields.Boolean(string="Addition to the exchange queue")
	notification_queue_remove 	= fields.Boolean(string="Removal from the exchange queue")
	notification_validation 	= fields.Boolean(string="Data validation errors")
	notification_first_failed 	= fields.Boolean(string="First unsuccessful exchange attempt")
	notification_successful 	= fields.Boolean(string="Successful exchange")
