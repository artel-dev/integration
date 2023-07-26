import base64
from datetime import datetime
import logging
import requests
from requests.auth import HTTPBasicAuth
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ExternalSystem(models.Model):
    """
    External system keeps datas about a connection to the server
    """
    _name = 'ata.external.system'
    _description = 'External system'

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
        selection=[("json", "JSON")],
        default="json"
    )

    @staticmethod
    def base64encodestring(s: str):
        return base64.b64encode(s.encode('ascii')).decode()

    @staticmethod
    def get_date_iso(date_str: str):
        date_str = date_str.split('.')[0]
        return datetime.fromisoformat(date_str)

    def execute(self, ext_service):
        result = False
        ext_request = self.create_request(ext_service)
        if self.execute_request(ext_request):
            result = self.read_request(ext_request)
        self.create_exchange_log(ext_request)
        return result

    @api.model
    def create_request(self, ext_service):
        if self.content_type == "json":
            request_body = self.env['ata_external_connection.ata_json'].dumps(ext_service["request_body"])
        else:
            request_body = ext_service["request_body"]

        ext_request = {
            'exchange_id': ext_service["exchange_id"],
            'name': ext_service["name"],
            'method_name': ext_service["method_name"],
            'http_method': ext_service["http_method"],
            'params': ext_service["params"],
            'request_body': request_body,
            'result': '',
            'headers': '',
            'create_date': datetime.now(),
            'is_executed': False,
            'execution_date': False,
            'is_processed': False,
            'processing_date': False,
            'number_of_attempts': 0,
        }
        return ext_request

    @api.model
    def execute_request(self, ext_request):
        # source data for request
        http_method = ext_request["http_method"]
        params = ext_request["params"]
        request_body = ext_request["request_body"]

        msg_prefix = f'External service {ext_request["name"]}:'

        timeout = 60

        if http_method not in ['GET', 'POST']:
            msg = f'{msg_prefix} unknown HTTP method {http_method}'
            ext_request['result'] = msg
            raise UserError(msg)

        url = self.get_url(ext_request)
        headers, auth = self.get_headers_auth(ext_request)

        start_date = datetime.now()

        # execute request
        if http_method == 'GET':
            try:
                response = requests.get(
                    url=url,
                    params=params,
                    headers=headers,
                    auth=auth,
                    timeout=timeout
                )
            except Exception as e:
                msg = f'{msg_prefix} Can’t execute the request from URL {url}'
                ext_request['result'] = msg
                _logger.warning(msg)
                logging.exception(e)
                return False

        elif http_method == 'POST':
            try:
                response = requests.post(
                    url=url,
                    data=request_body,
                    headers=headers,
                    auth=auth,
                    timeout=timeout
                )
            except Exception as e:
                msg = f'{msg_prefix} Can’t execute the request from URL {url}'
                ext_request['result'] = msg
                _logger.warning(msg)
                logging.exception(e)
                return False
        else:
            return False

        finish_date = datetime.now()

        vals = {
            'url': url,
            'status_code': response.status_code,
            'result': response.text,
            'headers': response.headers,
            'is_executed': True,
            'execution_date': datetime.now(),
            'number_of_attempts': ext_request["number_of_attempts"] + 1,
            'start_date': start_date,
            'finish_date': finish_date,
        }

        for key, value in vals.items():
            ext_request[key] = value

        return True

    @api.model
    def read_request(self, ext_request):
        result = False
        if not ext_request["is_executed"]:
            return result
        if not ext_request["status_code"] == 200:
            return result
        if not ext_request["result"]:
            return result

        if self.content_type == "json":
            result = self.env['ata_external_connection.ata_json'].loads(ext_request["result"])
        else:
            result = ext_request["result"]

        vals = {
            'is_processed': True,
            'processing_date': datetime.now()
        }
        for key, value in vals.items():
            ext_request[key] = value

        return result

    @api.model
    def get_url(self, ext_request, method_name=''):
        server_address = self.server_address
        server_port = self.server_port
        is_secure_connection = self.is_secure_connection

        if not method_name:
            method_name = ext_request["method_name"]

        # calculate url
        http_protocol = 'http' + ('s' if is_secure_connection else '')
        url_http_protocol = ''
        if not server_address.startswith('http'):
            url_http_protocol = f'{http_protocol}://'
        url_port = f':{server_port}' if server_port else ''
        resource_address = self.format_resource_address()
        method_name_prefix = '' if method_name.startswith('/') else '/'
        url_method_name = f'{method_name_prefix}{method_name}'
        url = f'{url_http_protocol}{server_address}{url_port}{resource_address}{url_method_name}'

        return url

    def format_resource_address(self):
        return '' if not self.resource_address else '/' + self.resource_address.strip('/')

    def get_headers_auth(self, ext_request):
        # source data for request
        login = self.login
        password = self.password
        is_token_authentication = self.is_token_authentication

        method_name = ext_request["method_name"]

        # calculate headers and auth
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        auth = False
        apikey_not_in_method = (method_name.find('apikey') == -1)
        if is_token_authentication and password and apikey_not_in_method:
            headers['Authorization'] = f'Bearer {password}'
        elif login and password:
            auth_header = "Basic " + self.base64encodestring(
                f'{login}:{password}')
            headers['Authorization'] = auth_header
            auth = HTTPBasicAuth(username=login, password=password)
        return headers, auth

    def create_exchange_log(self, ext_request):
        exchange_id = ext_request["exchange_id"]

        exchange_log_manager = self.env['ata.exchange.log']
        log_vals = {
            'name': f'Exchange id: {exchange_id}, service: {ext_request["name"]}',
            'exchange_id': exchange_id,
            'system_id': self["id"],
            'server_address': self.server_address,
            'server_port': self.server_port,
            'method_name': ext_request["method_name"],
            'request_body': ext_request["request_body"],
            'request': ext_request["url"],
            'response': ext_request["result"],
            'headers': ext_request["headers"],
            'status_code': ext_request["status_code"],
            'create_date': ext_request["create_date"],
            'is_executed': ext_request["is_executed"],
            'execution_date': ext_request["execution_date"],
            'is_processed': ext_request["is_processed"],
            'processing_date': ext_request["processing_date"],
            'number_of_attempts': ext_request["number_of_attempts"],
            'start_date': ext_request["start_date"],
            'finish_date': ext_request["finish_date"],
        }
        exchange_log_manager.create(log_vals)
