import logging
from odoo.exceptions import ValidationError, UserError

from odoo import fields, http
from odoo.http import request
from datetime import datetime

from odoo.addons.ata_exchange_v4.models.ata_exchange_log import ExchangeLog

from .jsonrpc_errors import (
    ApiKeyMissingError,
    ApiKeyInvalidError,
    MethodNotFoundError,
    InvalidJsonError,
    ServerError
)

_logger = logging.getLogger(__name__)


class AtaExchangeIncomingController(http.Controller):
    @http.route('/api/ata_exchange_v4/<string:method_incoming>', type='ata_json', auth='public', csrf=False, methods=['POST'])
    def method_request(self, method_incoming=None, **kwargs):
        # start logging incoming request
        log_id = self.create_exchange_log()

        """Handles incoming JSON requests for specific methods."""
        env = request.env

        # Find the corresponding method (removed active check as requested)
        # Using sudo() as specific method access isn't tied to public user
        try:
            request_body = env['ata.exchange.json'].sudo().loads(request.httprequest.data)
            log_id.write({
                'request_body': request_body,
            }, use_new_cursor = True)
            #TODO check structure fields of request body
        except Exception as e:
            raise InvalidJsonError(method_incoming, e, log_id = log_id)

        if method_incoming == 'jsonrpc':
            method_exchange_name = request_body.get('method')
            request_data = request_body.get('params')
        else:
            method_exchange_name = method_incoming
            request_data = request_body
        
        method = env['ata.exchange.method'].sudo().search([
            ('name', '=', method_exchange_name),
            ('type', '=', 'incoming_request'),
        ], limit=1)

        if not method:
            raise MethodNotFoundError(method_exchange_name, log_id=log_id)
        else:
            log_id.write({
                'method_name': method_exchange_name,
            }, use_new_cursor = True)

        if method.need_api_key:
            api_key_header = request.httprequest.headers.get('X-API-Key')
            if not api_key_header:
                raise ApiKeyMissingError(method, log_id=log_id)

            # Search for the active API key
            # Using sudo() as auth='public', access rights checked logically later or via handler's user
            api_key_record = env['ata.exchange.api.key'].sudo().search([
                ('api_key', '=', api_key_header),
                ('active', '=', True),
                ('methods_ids', 'in', method.id)
            ], limit=1)

            if not api_key_record:
                raise ApiKeyInvalidError(method, log_id=log_id)

            ext_system = api_key_record.system_id
        else:
            ext_system = None

        try:
            response_body = env['ata.exchange.handler'].sudo().process_incoming_request(
                method=method,
                ext_system=ext_system,
                req_body=request_data
            )
            
            log_id.write({
                'method_name': method_exchange_name,
                'system_id': ext_system.id if ext_system else None,
                'response': response_body,
                'finish_date': datetime.now(),
            })
            return response_body
        except ValidationError as e:
            raise InvalidJsonError(method_exchange_name, error_parsing=e, log_id=log_id)
        except UserError as e:
            raise ServerError(str(e), log_id=log_id)
        except Exception as e:
            # _logger.exception(f"Unexpected error processing request for method '{method_exchange_name}': {e}")
            raise ServerError(f"Unexpected error processing request for method '{method_exchange_name}': {e}.", log_id=log_id)

    def create_exchange_log(self) -> ExchangeLog:
        log_vals = {
            'name': 'Incoming request',
            'start_date': datetime.now(),
        }
        return request.env['ata.exchange.log'].create([log_vals], use_new_cursor=True)
