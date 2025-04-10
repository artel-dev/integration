import logging
import werkzeug.exceptions

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)


class AtaExchangeIncomingController(http.Controller):
    @http.route('/api/ata_exchange_v4/<string:method_name>', type='json', auth='public', methods=['POST'], csrf=False)
    def method_request(self, method_name=None, **kwargs):
        """Handles incoming JSON requests for specific methods."""
        env = request.env
        api_key_header = request.httprequest.headers.get('X-API-Key')
        if not api_key_header:
            _logger.warning("API Key missing")
            raise werkzeug.exceptions.Unauthorized("API Key is required.")

        # Search for the active API key
        # Using sudo() as auth='public', access rights checked logically later or via handler's user
        api_key_record = env['ata.exchange.api.key'].sudo().search([
            ('api_key', '=', api_key_header),
            ('active', '=', True) # Key itself must be active
        ], limit=1)

        if not api_key_record:
            _logger.warning(f"Invalid or inactive API Key received.")
            raise werkzeug.exceptions.Forbidden("Invalid or inactive API Key.")

        ext_system = api_key_record.system_id # Can be empty

        # Find the corresponding method (removed active check as requested)
        # Using sudo() as specific method access isn't tied to public user
        method = env['ata.exchange.method'].sudo().search([
            ('name', '=', method_name),
            ('type', '=', 'incoming_request'),
        ], limit=1)

        if not method:
            _logger.warning(f"Incoming method '{method_name}' (type='incoming_request') not found.")
            raise werkzeug.exceptions.NotFound(f"Method '{method_name}' not found for incoming requests.")

        try:
            req_body = env['ata.exchange.json'].sudo().loads(request.httprequest.data)
        except Exception as e:
            _logger.error(f"Failed to parse request body for method '{method_name}': {e}")
            raise werkzeug.exceptions.BadRequest("Invalid JSON request body.")

        try:
            # Handler is expected to find the specific model and call its run method
            response_body = env['ata.exchange.handler'].sudo().process_incoming_request(
                method=method,
                ext_system=ext_system,
                req_body=req_body
            )
            return response_body
        except (AccessError, ValidationError) as e:
             # Handle specific Odoo exceptions, potentially mapping to HTTP errors
             _logger.warning(f"Error processing request for method '{method_name}': {e}")
             if isinstance(e, AccessError):
                 raise werkzeug.exceptions.Forbidden(str(e))
             else: # ValidationError
                 raise werkzeug.exceptions.BadRequest(f"Invalid data for method '{method_name}': {e}")
        except werkzeug.exceptions.HTTPException as e:
             # Re-raise HTTP exceptions from the handler
             _logger.warning(f"HTTP Exception during processing for method '{method_name}': {e}")
             raise e
        except Exception as e:
            _logger.exception(f"Unexpected error processing request for method '{method_name}': {e}")
            raise werkzeug.exceptions.InternalServerError(f"An error occurred while processing the request for method '{method_name}'.")
