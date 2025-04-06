from odoo import api, fields, _, models
from odoo.exceptions import UserError

import base64
from datetime import datetime
import logging
from requests_toolbelt import MultipartEncoder
import requests
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from typing import TypedDict, Optional, Any

_logger = logging.getLogger(__name__)


class ExtResponse(TypedDict):
    result: str
    result_json: Optional[Any]
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
    

class AtaExchangeSystem(models.Model):
    """
    External system keeps datas about a connection to the server
    """
    _name = 'ata.exchange.system'
    _description = 'External system'

    disabled = fields.Boolean(default=False)
    name = fields.Char()
    description = fields.Char()
    server_address = fields.Char()
    server_port = fields.Integer()
    resource_address = fields.Char()
    is_secure_connection = fields.Boolean()
    login = fields.Char()
    password = fields.Char()
    is_token_authentication = fields.Boolean()
    use_proxy = fields.Boolean()
    proxy_login = fields.Char()
    proxy_password = fields.Char()
    content_type = fields.Selection(
        selection=[
            ("json", "JSON"),
            ("html", "HTML")
        ],
        default="json")

    parameter_ids = fields.One2many(
        comodel_name='ata.exchange.system.parameters',
        inverse_name='system_id',
        string='Parameters')


    @staticmethod
    def base64encodestring(s: str):
        return base64.b64encode(s.encode('ascii')).decode()

    @staticmethod
    def get_date_iso(date_str: str):
        date_str = date_str.split('.')[0]
        return datetime.fromisoformat(date_str)

    @api.model
    def get_all_ext_system(self):
        return self.sudo().search([('disabled', '=', False)])

    #region init instance classes
    def get_init_extrequest(self) -> ExtRequest:
        return {
            'name':             self.name,
            'method_name':      None,
            'exchange_id':      None,            
            'method_params':    self.get_init_extrequest_method_parameters(),
            'create_date':      datetime.now(),
            'timeout':          60,
            'execution_date':   None,
            'processing_date':  None,
            'is_executed':      False,
            'is_processed':     False,
            'response':         None,
        }

    def get_init_extrequest_method_parameters(self) -> ExtRequestMethodParameters:
        headers = CaseInsensitiveDict()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'

        return {
            'http_method': '',
            'url': '',
            'params': {},
            'request_body': '',
            'headers': headers,
            'auth': None,
            'token': '',
        }

    def get_init_extresponse(self) -> ExtResponse:
        return {
            'result':       '',
            'result_json':  None,
            'status_code':  None,
            'error':        False,
            'error_msg':    '',
            'start_date':   None,
            'finish_date':  None,
            'headers':      CaseInsensitiveDict(),
        }
    #endregion

    def execute(self, ext_request: ExtRequest) -> ExtResponse|None:
        self.execute_request(ext_request)
        if ext_request['response'] and ext_request['is_executed']:
            self.read_request(ext_request['response'])
            
            ext_request['is_processed'] = True
            ext_request['processing_date'] = datetime.now()
        self.create_exchange_log(ext_request)

        return ext_request['response']

    @api.model
    def execute_request(self, ext_request: ExtRequest):
        msg_prefix = f'External service {ext_request["name"]}:'

        method_params = ext_request["method_params"]
        http_method = method_params["http_method"]
        if http_method not in ['GET', 'POST']:
            msg = f'{msg_prefix} unknown HTTP method {http_method}'
            ext_request['response'] = {
                **self.get_init_extresponse(),
                'error': True,
                'error_msg': msg
            }
            return

        if not method_params['url']:
            method_params['url'] = self.get_url(ext_request, '', True)

        self.calc_headers_and_auth(ext_request)
        
        # convert request_body to json
        if isinstance(method_params["request_body"], dict) and 'application/json' in method_params['headers']['Content-Type']:
            data_post = self.env['ata.exchange.json'].dumps(method_params["request_body"])
        else:
            data_post = method_params["request_body"] or method_params["params"]

        start_date = datetime.now()

        # execute request
        try:
            ext_request['response'] = self.get_init_extresponse()

            if http_method == 'GET':
                response = requests.get(
                    url     = method_params['url'],
                    params  = method_params["params"] if isinstance(method_params["params"], dict) else None,
                    headers = method_params['headers'],
                    auth    = method_params['auth'],
                    timeout = ext_request['timeout']
                )
            elif http_method == 'POST':
                response = requests.post(
                    url     = method_params['url'],
                    data    = data_post,
                    headers = method_params['headers'],
                    auth    = method_params['auth'],
                    timeout = ext_request['timeout']
                )
            else:
                return
                
            finish_date = datetime.now()

            ext_request['response'] = {
                **ext_request['response'],
                'headers': response.headers,
                'status_code': response.status_code,
                'result': response.text,
                'start_date': start_date,
                'finish_date': finish_date,
            }
            ext_request['is_executed'] = True
            ext_request['execution_date'] = datetime.now()

        except Exception as e:
            msg = f'{msg_prefix} Can’t execute the request from URL {method_params["url"]}'
            ext_request['response'] = {
                **self.get_init_extresponse(),
                'error': True,
                'error_msg': msg
            }
            _logger.warning(msg)
            
    @api.model
    def read_request(self, ext_response: ExtResponse):
        if not ext_response["status_code"] in [200, 201]:
            ext_response["error"] = True
            ext_response["error_msg"] = f'Status code is {ext_response["status_code"]}. {ext_response["result"]}'
        if not ext_response["result"]:
            ext_response["error"] = True
            ext_response["error_msg"] = 'Result is empty'

        if not ext_response["error"] and \
            "application/json" in ext_response['headers'].get('Content-Type','').lower():
            ext_response["result_json"] = self.env['ata.exchange.json'].loads(ext_response["result"])
        
    @api.model
    def get_url(self,
            ext_request: ExtRequest,
            resource_address: str = '',
            add_method_name: bool = False) -> str:

        def format_resource_address(address: str|None = '') -> str:
            return '' if not address else f"/{address.lstrip('/')}"

        server_address = self.server_address.strip('/')
        server_port = self.server_port
        is_secure_connection = self.is_secure_connection

        # calculate url
        http_protocol = 'http' + ('s' if is_secure_connection else '')
        url_http_protocol = ''
        if not server_address.startswith('http'):
            url_http_protocol = f'{http_protocol}://'
        url_port = f':{server_port}' if server_port else ''
        resource_address = format_resource_address(resource_address or self.resource_address)
        method_address = format_resource_address(ext_request["method_name"]) if add_method_name else ''
        
        return f'{url_http_protocol}{server_address}{url_port}{resource_address}{method_address}'

    def calc_headers_and_auth(self, ext_request: ExtRequest) -> HTTPBasicAuth|None:
        # calculate headers and auth
        params = ext_request["method_params"]
        headers = ext_request["method_params"]['headers']
        
        if ext_request["method_params"]["http_method"] == 'POST' and params["params"]:
            multipart_data = MultipartEncoder(fields=params["params"])
            headers['Content-Type'] = multipart_data.content_type
            params["params"] = multipart_data

        login = self.login
        password = self.password
        
        if params['token']:
            headers['Authorization'] = f'Bearer {params["token"]}'
        elif login:
            headers['Authorization'] = "Basic " + self.base64encodestring(
                f'{login}:{password}')
            params['auth'] = HTTPBasicAuth(username=login, password=password)

    def create_exchange_log(self, ext_request: ExtRequest):
        if ext_request["method_name"]:
            log_vals = {
                'name': f'{ext_request["exchange_id"]}',
                'system_id': self["id"],
                'server_address': self.server_address,
                'server_port': self.server_port,
                #'headers': ext_request["method_params"]["headers"],
                'method_name': ext_request["method_name"],
                'request': ext_request["method_params"]["url"],
                'request_body': ext_request["method_params"]["request_body"],
                'is_executed': ext_request["is_executed"],
                'execution_date': ext_request["execution_date"],
                'is_processed': ext_request["is_processed"],
                'processing_date': ext_request["processing_date"],
            }
            if (ext_response:=ext_request["response"]):
                if ext_response['error']:
                    log_vals.update({
                        'response': f"Error. {ext_response['error_msg']}",
                    })
                else:
                    log_vals.update({
                        'status_code': ext_response["status_code"],
                        'response': ext_response["result"],
                        'start_date': ext_response["start_date"],
                        'finish_date': ext_response["finish_date"],
                    })
            
            self.env['ata.exchange.log'].create(log_vals)

    def action_test_connection(self):
        answers = []
        methods_http = ['GET', 'POST']

        for record in self:
            # check POST and GET query resource /check on ext. system
            for method_http in methods_http:
                exchange_id = f'Model: {record._name}, Id: {record.id}'
                ext_request = record.get_init_extrequest()
                ext_request: ExtRequest = {
                    **ext_request,
                    'exchange_id': exchange_id,
                    'name': 'Test',
                    'method_name': 'check',
                    'method_params': {
                        **ext_request['method_params'],                        
                        'http_method': method_http,                        
                    }
                }

                ext_response = record.execute(ext_request)

                result = False
                error = f'Error undefined'

                if ext_response:
                    error = ext_response['error']
                    if not error:
                        if (result_json:=ext_response['result_json']) and isinstance(result_json, dict):
                            result = result_json.get("status", False)
                        else:
                            result = True if ext_response['result'] == 'True' else False
                    else:
                        answers.append(f'Test {method_http} method ext. system {record.name} is False\n'
                            f'Error: {str(error)}')

                answers.append(f'Test {method_http} method "{record.name}" is {str(result)}')
                if error:
                    answers.append(f'Error: {str(error)}')             

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Result test connection',
                'type': 'info',
                'message': '; '.join(answers),
                'sticky': False
            }
        }

    # --- synchronization ---
    def action_synchronization(self):
        exchange_id = f'Synchronization: {self.name}'
        ext_request = self.get_init_extrequest()
        ext_request: ExtRequest = {
            **ext_request,
            'exchange_id': exchange_id,
            'name': 'Synchronization',
            'method_name': 'sync',
            'method_params': {
                **ext_request['method_params'],                        
                'http_method': 'POST',
                'request_body': {
                    'meta': {
                        'db_name': self.env.cr.dbname,
                    },
                    'data': {
                        'id': self.id,
                        'name': self.name,
                    }
                }
            }
        }

        ext_response = self.execute(ext_request)

        result = False
        if ext_response and ext_response['result_json']:
            if not (error := ext_response['error']):
                if self.content_type == 'json' and isinstance(ext_response['result_json'], dict):
                    result = ext_response['result_json'].get("status", False)
                else:
                    result = (ext_response['result'] == 'True')
            else:
                result = error

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Result synchronization',
                'type': 'info',
                'message': f'Synchronization: {str(result)}',
                'sticky': False
            }
        }

class AtaExtSystemParams(models.Model):
    _name = "ata.exchange.system.parameters"
    _description = "Exchange system parameters"

    system_id = fields.Many2one('ata.exchange.system', 'System', required=True)
    param = fields.Char('Parameter', required=True)
    value = fields.Char('Value', default='')
