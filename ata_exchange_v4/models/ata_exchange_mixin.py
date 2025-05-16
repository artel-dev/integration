from odoo import api, models

from typing import TypedDict, Optional
from datetime import datetime
from requests.structures import CaseInsensitiveDict
from requests_toolbelt import MultipartEncoder
from requests.auth import HTTPBasicAuth

class AtaExchangeMixin(models.AbstractModel):
    _name = "ata.exchange.mixin"
    _description = "Exchange mixin"

    @api.model
    def get_meta_data(self, *kwargs) -> dict:
        return {
            'meta': {
                'db_name': self._cr.dbname,
            },
        }

    def cron_exchange(self):
        #start outgoing queue
        self.env['ata.exchange.queue'].exchange()
        
        #start request_data
        methods = self.env['ata.exchange.method'].search([
            ('type', '=', 'request_data'),
            ('start_over_cron', '=', True)
        ])
        self.env['ata.exchange.base.requestdata'].ata_exchange_requestdata(methods)

class ExtResponse(TypedDict):
    result: str
    result_json: Optional[dict]
    status_code: Optional[int]
    error: bool
    error_msg: str    
    start_date: Optional[datetime]
    finish_date: Optional[datetime]
    headers: CaseInsensitiveDict

class ExtRequestMethodParameters(TypedDict):
    # parameters for request.method()
    http_method: str
    url: str
    params: dict|MultipartEncoder
    request_body: str|dict|list
    headers: CaseInsensitiveDict
    auth: Optional[HTTPBasicAuth]
    token: str

class ExtRequest(TypedDict):
    # general
    name: Optional[str]
    create_date: datetime
    method_name: Optional[str]
    exchange_id: Optional[str]
    
    method_params: ExtRequestMethodParameters
    
    # execution parameters
    timeout: int
    is_executed: bool   # is request executed
    execution_date: Optional[datetime]
    is_processed: bool  # is request processed
    processing_date: Optional[datetime]

    response: Optional[ExtResponse]