from odoo import models, api
from odoo.exceptions import UserError
from odoo.addons.ata_exchange_v4.controllers.jsonrpc_errors import ServerError

from .ata_exchange_system import AtaExchangeSystem
from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_base_incomingrequest import AtaExchangeBaseIncomingrequest
from .ata_exchange_base_incomingrequest_types import IncomingRequestParam, IncomingResponseParam

import logging


_logger = logging.getLogger(__name__)

class AtaExchangeHandler(models.AbstractModel):
    _name = "ata.exchange.handler"
    _description = "Exchange Handler Dispatcher"

    @api.model
    def process_incoming_request(self, method: AtaExchangeMethod, ext_system: AtaExchangeSystem | None, req_body: dict) -> dict|list[dict]:
        """
        Processes an incoming request by finding the correct handler model
        (defined in method.model_id) and calling its ata_exchange_incomingrequest_run method.

        :param method: The ata.exchange.method record for the request.
        :param ext_system: The ata.exchange.system record from API key (or None).
        :param req_body: The parsed JSON request body.
        :return: Dictionary or list representing the JSON response body.
        :raises werkzeug.exceptions.*: For various processing errors.
        """
        if not method.model_id or not method.model_id.model:
            raise ServerError(f"Configuration error: Target model not defined for exchange method '{method.name}'.")

        target_model_name = method.model_id.model
        
        if target_model_name not in self.env:
            raise ServerError(f"Configuration error: Target model '{target_model_name}' not found.")

        target_model_instance = self.env[target_model_name]

        # Verify the target model inherits from the expected base class
        if not isinstance(target_model_instance, AtaExchangeBaseIncomingrequest):
            raise ServerError(f"Configuration error: Target model '{target_model_name}' has incorrect base class for incoming requests.")

        # Call the ata_exchange_incomingrequest method on the target model instance
        try:
            incoming_param = IncomingRequestParam(
                method_id     =method,
                ext_system_id =ext_system,
                req_body      =req_body,
                req_body_data =req_body.get('data', {}) if isinstance(req_body, dict) else {}
            )
            # Use sudo() for potential broad access needs within the run method.
            response_param = target_model_instance.sudo().ata_exchange_incomingrequest_run(incoming_param)
            if response_param.has_error:
                raise UserError('\n'.join(response_param.error))
            else:
                _logger.debug(f"ata_exchange_incomingrequest for exchange method '{method.name}' executed successfully.")

                return response_param.get_data_json()
        except UserError:
            raise
        except NotImplementedError: 
            raise ServerError(f"Function 'ata_exchange_incomingrequest_run' not implemented in '{target_model_name}' for exchange method '{method.name}'.")
        except TypeError as e:
            if "ata_exchange_incomingrequest_run() takes" in str(e) or "positional argument but" in str(e):
                raise ServerError(f"Signature mismatch calling {target_model_name}.ata_exchange_incomingrequest_run: {e}")
            else:
                raise ServerError(f"Unexpected TypeError during run for exchange method '{method.name}': {e}")
