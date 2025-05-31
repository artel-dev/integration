from odoo import api, fields, _, models
from odoo.exceptions import UserError

import base64
from datetime import datetime
from requests_toolbelt import MultipartEncoder
import requests
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
import logging

_logger = logging.getLogger(__name__)

from .ata_exchange_system_types import ExtResponse, ExtRequest, ExtRequestMethodParameters
from .ata_exchange_method import AtaExchangeMethod


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
    use_proxy = fields.Boolean()
    proxy_login = fields.Char()
    proxy_password = fields.Char()
    token_provider_method = fields.Selection(
        selection=[('none_available', 'No provider configured')], 
        string='Token Provider Method',
        help="Select the method to obtain the token. This will be populated by 'selection_add' from other modules.",
        default='none_available'
    )
    authentication_type = fields.Selection(
        selection=[
            ('none', 'No Authentication'),
            ('basic', 'Basic Authentication'),
            ('token', 'Token Authentication')
        ],
        string='Authentication Type',
        default='none',
        required=True
    )
    content_type = fields.Selection(
        selection=[
            ("json", "JSON"),
            ("jsonrpc", "JSONRPC 2.0"),
            ("html", "HTML")
        ],
        default="json"
    )
    api_key_ids = fields.One2many(
        'ata.exchange.api.key',
        'system_id',
        string="API Keys",
        help="API Keys associated with this system."
    )
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
            'method':           None,
            'method_name':      '',
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
            'http_method': 'POST',
            'url': '',
            'params': {},
            'request_body': '',
            'headers': headers,
            'auth_type': self.authentication_type,
            'auth': None,
            'token': '',
            'valid_codes': [200],
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

    def execute(self, ext_request: ExtRequest) -> None:
        self.execute_request(ext_request)
        if ext_request['response'] and ext_request['is_executed']:
            # self.read_request(ext_request['response'])
            
            ext_request['is_processed'] = True
            ext_request['processing_date'] = datetime.now()
        self.create_exchange_log(ext_request)        

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

        self.calc_headers_and_auth(ext_request)
        
        #for json-rpc 2.0 forming structure
        if self.content_type == 'jsonrpc':
            method_params['request_body'] = {
                'jsonrpc': '2.0',
                'method': ext_request["method"].id if ext_request["method"] else "",
                'params': method_params['request_body'],
                'id': None
            }
        # convert request_body to json
        if isinstance(method_params["request_body"], dict) and 'application/json' in method_params['headers']['Content-Type']:
            data_post = self.env['ata.exchange.json'].dumps(method_params["request_body"])
        else:
            data_post = method_params["request_body"] or method_params["params"]    # for multipart data

        start_date = datetime.now()

        # execute request
        try:
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
                **self.get_init_extresponse(),
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
        if not ext_response["status_code"] in [200]:
            ext_response["error"] = True
            ext_response["error_msg"] = f'Status code is {ext_response["status_code"]}. {ext_response["result"]}'
        if not ext_response["result"]:
            ext_response["error"] = True
            ext_response["error_msg"] = 'Result is empty'

        if not ext_response["error"] and \
            "application/json" in ext_response['headers'].get('Content-Type','').lower():
            
            result_json = self.env['ata.exchange.json'].loads(ext_response["result"])
        
            if isinstance(result_json, dict) and \
                result_json.get("jsonrpc") == "2.0":
                if (error_jsonrpc := result_json.get('error', False)):
                    ext_response["error"] = True
                    ext_response["error_msg"] = error_jsonrpc
                else:
                    ext_response["result_json"] = result_json.get("result", False)
            else:
                ext_response["result_json"] = result_json
        
    @api.model
    def calc_url(self, ext_request: ExtRequest, resource_address: str = ""):

        def format_resource_address(address: str|None = '') -> str:
            return '' if not address else f"/{address.lstrip('/')}"

        server_address = self.server_address.strip('/')
        url_http_protocol = ''
        if not server_address.startswith('http'):
            url_http_protocol = f"http{'s' if self.is_secure_connection else ''}://"
        url_port = f':{self.server_port}' if self.server_port else ''
        
        # resource url priority calculate
        # 1. resource_address from parameters this function
        # 2. resource_url from method
        # 3. resource_address from system add method`s url
        resource_url = format_resource_address(resource_address or self.calc_resource_address(ext_request))
        
        ext_request['method_params']['url'] = f'{url_http_protocol}{server_address}{url_port}{resource_url}'

    def calc_resource_address(self, ext_request: ExtRequest):
        if (method:=ext_request["method"]) and method.resource_url:
            return method.resource_url
        
        resource_prefix = (self.resource_address or '').strip('/')
        
        if self.content_type == 'jsonrpc':
            method_url = 'jsonrpc'
        else:
            method_url = ext_request["method"].name if ext_request["method"] else ext_request["method_name"]

        return "/".join([resource_prefix, method_url])
        

    def _handle_multipart_data(self, ext_request: ExtRequest, headers: CaseInsensitiveDict, params: ExtRequestMethodParameters):
        """Handles multipart form data encoding if applicable."""
        if ext_request["method_params"].get("http_method") == 'POST' and "params" in params and params["params"]:
            if isinstance(params["params"], dict):
                try:
                    # Filter out None values, as MultipartEncoder might not handle them well depending on usage.
                    fields_for_encoder = {k: v for k, v in params["params"].items() if v is not None}
                    if fields_for_encoder:
                        multipart_data = MultipartEncoder(fields=fields_for_encoder)
                        headers['Content-Type'] = multipart_data.content_type
                        params["params"] = multipart_data
                except TypeError as e:
                    _logger.error(f"Error creating MultipartEncoder: {e}. Params: {params.get('params')}")                    
            else:
                _logger.warning(
                    f"params['params'] is not a dictionary, skipping multipart encoding. Type: {type(params.get('params'))}"
                )

    def _handle_basic_auth(self, headers: CaseInsensitiveDict, params: ExtRequestMethodParameters) -> HTTPBasicAuth | None:
        """
        Handles Basic authentication.
        Returns an HTTPBasicAuth object for use with requests library, or None if login is not set.
        """
        if 'Authorization' in headers:
            del headers['Authorization']

        if self.login:
            return HTTPBasicAuth(username=self.login, password=self.password)
        else:
            _logger.warning(f"Basic authentication selected for system '{self.name}' (ID: {self.id}) but login is not set.")
            return None

    def _handle_token_auth(self, headers: CaseInsensitiveDict):
        """Handles Token authentication by fetching a token using the registered provider and adding it to headers."""
        if 'Authorization' in headers:
            del headers['Authorization']

        if not (token_method := self.token_provider_method) or token_method == 'none_available':
            _logger.warning(
                f"Token authentication selected for system '{self.name}' (ID: {self.id}), "
                f"but no token provider method is configured or available. Selected: '{token_method}'"
            )
            return

        _logger.debug(f"Attempting to use token provider method '{token_method}' on system '{self.name}'.")

        token = None
        if hasattr(self, token_method):
            try:
                token_fetcher_method = getattr(self, token_method)
                token = token_fetcher_method()
                _logger.debug(f"Token fetched via '{token_method}' for system '{self.name}': {'********' if token else 'None'}")
            except Exception as e:
                _logger.error(
                    f"Error calling token provider method '{token_method}' for system '{self.name}' (ID: {self.id}): {e}",
                    exc_info=True
                )
                return
        else:
            _logger.error(
                f"Method '{token_method}' not found on system '{self.name}' (ID: {self.id})."
            )
            return

        if token:
            headers['Authorization'] = f'Bearer {token}'
            _logger.debug(f"Token successfully added to headers for system '{self.name}' using provider '{token_method}'.")
        else:
            if 'Authorization' in headers:
                 del headers['Authorization']
            _logger.warning(
                f"Failed to obtain token for system '{self.name}' using provider '{token_method}'. "
                f"Authorization header not set."
            )

    def _handle_no_auth(self, headers: CaseInsensitiveDict):
        if 'Authorization' in headers:
            del headers['Authorization']
        _logger.debug(f"No authentication selected for system '{self.name}' (ID: {self.id}).")        

    def calc_headers_and_auth(self, ext_request: ExtRequest) -> HTTPBasicAuth | None:
        """
        Prepares headers (e.g., Content-Type for multipart) and
        determines the authentication object for the request.
        This method dispatches to specific auth handlers based on self.authentication_type.
        Modifies ext_request.method_params['headers'] and ext_request.method_params['params'] (for multipart).
        Returns an HTTPBasicAuth object if basic authentication is used, otherwise None.
        Token authentication is applied directly to headers.
        """
        params = ext_request["method_params"]
        # Ensure headers dict exists and is case-insensitive.
        current_headers = params.get('headers', {})
        if not isinstance(current_headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(current_headers)
            params['headers'] = headers
        else:
            headers = current_headers

        self._handle_multipart_data(ext_request, headers, params)

        auth_type = ext_request['method_params']['auth_type']
        auth_object = None

        if auth_type == 'basic':
            auth_object = self._handle_basic_auth(headers, params)
        elif auth_type == 'token':
            # Token auth modifies headers directly, does not return an auth object for requests' `auth` param.
            self._handle_token_auth(headers) 
        elif auth_type == 'none':
            self._handle_no_auth(headers)
        else:
            _logger.error(f"Unknown authentication type: {auth_type} for system '{self.name}' (ID: {self.id})")
            
        return auth_object

    def create_exchange_log(self, ext_request: ExtRequest):
        if ext_request["method"]:
            log_val = {
                'name': f'{ext_request["exchange_id"]}',
                'system_id': self["id"],
                'server_address': self.server_address,
                'server_port': self.server_port,
                #'headers': ext_request["method_params"]["headers"],
                'method_name': ext_request["method"].name or ext_request["method_name"],
                'request': ext_request["method_params"]["url"],
                'request_body': ext_request["method_params"]["request_body"],
                'is_executed': ext_request["is_executed"],
                'execution_date': ext_request["execution_date"],
                'is_processed': ext_request["is_processed"],
                'processing_date': ext_request["processing_date"],
            }
            if (ext_response:=ext_request["response"]):
                log_val.update({
                    'status_code': ext_response["status_code"],
                    'start_date': ext_response["start_date"],
                    'finish_date': ext_response["finish_date"],
                    'response': ext_response["result"],
                })

            self.env['ata.exchange.log'].create([log_val])
            self.env.cr.commit()

    def action_test_connection(self):
        answers = []
        
        for record in self:
            methods_http = ['POST'] if record.content_type == 'jsonrpc' else ['GET', 'POST']
            # check POST and GET query resource /check on ext. system
            for method_http in methods_http:
                exchange_id = f'Model: {record._name}, Id: {record.id}'
                ext_request = record.get_init_extrequest()
                ext_request['exchange_id'] = exchange_id
                ext_request['name'] = 'Test'
                ext_request['method_name'] = 'check'
                ext_request['method_params']['http_method'] = method_http
                ext_request['method_params']['auth_type'] = 'none'
                self.calc_url(ext_request)

                record.execute(ext_request)

                if (ext_response := self.env['ata.exchange.method'].read_response_standart(ext_request)):
                    if ext_response['error']:
                        result = ext_response['error_msg']
                    elif (response_data := ext_response['result_json']) and isinstance(response_data, dict):
                        result = response_data.get('status', False)
                    else:
                        result = "Invalid response data"
                else:
                    result = "No connection or undefined error"
                
                answers.append(f'Test {method_http} method "{record.name}": {str(result)}')

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
        ext_request['name'] = 'Synchronization'
        ext_request['method_name'] = 'sync'
        ext_request['exchange_id'] = exchange_id
        ext_request['method_params']['request_body'] = {
            'meta': {
                'db_name': self.env.cr.dbname,
            },
            'data': {
                'id': self.id,
                'name': self.name,
            }
        }
        ext_request['method_params']['auth_type'] = 'none'

        self.execute(ext_request)

        if (ext_response := self.env['ata.exchange.method'].read_response_standart(ext_request)):
            if ext_response['error']:
                result = ext_response['error_msg'].get('message', False) \
                    if isinstance(ext_response['error_msg'], dict) else ext_response['error_msg']
                # result = ext_response['error_msg']
            elif (response_data := ext_response['result_json']) and isinstance(response_data, dict):
                result = response_data.get('status', False)
            else:
                result = "Invalid response data"
        else:
            result = "No connection or undefined error"

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Result synchronization',
                'type': 'info',
                'message': str(result),
                'sticky': False
            }
        }

class AtaExtSystemParams(models.Model):
    _name = "ata.exchange.system.parameters"
    _description = "Exchange system parameters"

    system_id = fields.Many2one('ata.exchange.system', 'System', required=True)
    param = fields.Char('Parameter', required=True)
    value = fields.Char('Value', default='')
