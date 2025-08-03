from odoo import api, fields, models
from typing import TYPE_CHECKING

from .ata_exchange_system_types import ExtRequest, ExtResponse
if TYPE_CHECKING:
    from .ata_exchange_class import AtaExchangeClass


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
			('inner_types', 'For inner matching data'),
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
	resource_url = fields.Char(
		string="Resource URL",
		help="If not defined, will be calculated from the system URL")

	def _compute_need_api_key(self):
		for record in self:
			record.need_api_key = bool(self.env['ata.exchange.api.key'].search([('methods_ids', 'in', record.id)], limit=1))

	notification_queue_add 		= fields.Boolean(string="Addition to the exchange queue")
	notification_queue_remove 	= fields.Boolean(string="Removal from the exchange queue")
	notification_validation 	= fields.Boolean(string="Data validation errors")
	notification_first_failed 	= fields.Boolean(string="First unsuccessful exchange attempt")
	notification_successful 	= fields.Boolean(string="Successful exchange")

	get_request_body_method = fields.Selection(selection=[])

	def get_xml_id(self) -> str|None:
		return self.get_external_id().get(self.id)

	#region overload methods
	def set_request_valid_codes(self, ext_request: ExtRequest) -> None:
		ext_request['method_params']['valid_codes'] = [200]
	
	def get_request_body(self, request_data: list[dict]|dict|str) -> dict:
		return {
            **self.env['ata.exchange.mixin'].get_meta_data(),
            "data": request_data,
        }
	
	def read_response(self, ext_request: ExtRequest) -> ExtResponse | None:
		return self.read_response_standard(ext_request)
	
	def get_response_data(self, response: ExtResponse) -> dict:
		# typical parse response
		return (result_dict:=response['result_json']) and isinstance(result_dict, dict) and result_dict or {}
		
	def response_post_processing(self,
		response: ExtResponse,
		response_data: dict,
		record: 'AtaExchangeClass | None' = None) -> bool:
		
		return True

	def response_error_post_processing(self, response: ExtResponse) -> bool:
		return False

	#endregion

	@api.model
	def read_response_standard(self, ext_request: ExtRequest) -> ExtResponse | None:
		if not (ext_response:=ext_request['response']):
			return None

		# check error in response
		if not ext_response["status_code"] in ext_request['method_params']['valid_codes']:
			ext_response["error"] = True
			ext_response["error_msg"] = f'Status code {ext_response["status_code"]} is invalid. {ext_response["result"]}'
		if not ext_response["result"]:
			ext_response["error"] = True
			ext_response["error_msg"] = 'Result is empty'

		self.response_extract_json_data(ext_response)

		return ext_response

	def response_extract_json_data(self, ext_response: ExtResponse):
		if not ext_response["error"] and \
			"application/json" in ext_response['headers'].get('Content-Type','').lower():
			
			result_json = self.env['ata.exchange.json'].loads(ext_response["result"])

			if isinstance(result_json, dict) and result_json.get("jsonrpc") == "2.0":
				# extract json-rpc 2.0 data
				if (error_jsonrpc := result_json.get('error', False)):
					ext_response["error"] = True
					ext_response["error_msg"] = error_jsonrpc
				else:
					ext_response["result_json"] = result_json.get("result", False)
			else:
				ext_response["result_json"] = result_json