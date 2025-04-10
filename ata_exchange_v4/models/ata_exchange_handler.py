from odoo import models, api
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.addons.ata_exchange_v4.models.ata_exchange_system import AtaExchangeSystem as ExSystem
from odoo.addons.ata_exchange_v4.models.ata_exchange_method import AtaExchangeMethod as ExMethod
from odoo.addons.ata_exchange_v4.models.ata_exchange_base_incomingrequest import AtaExchangeBaseIncomingrequest

import logging
from werkzeug.exceptions import InternalServerError, BadRequest, NotFound, Forbidden

_logger = logging.getLogger(__name__)

class AtaExchangeHandler(models.AbstractModel):
    _name = "ata.exchange.handler"
    _description = "Exchange Handler Dispatcher"

    @api.model
    def process_incoming_request(self, method: ExMethod, ext_system: ExSystem | None, req_body: dict) -> dict:
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
            _logger.error(f"Method '{method.name}' does not have a target model (model_id) defined.")
            raise InternalServerError(f"Configuration error: Target model not defined for method '{method.name}'.")

        target_model_name = method.model_id.model
        
        if target_model_name not in self.env:
            _logger.error(f"Target handler model '{target_model_name}' not found in environment.")
            raise InternalServerError(f"Configuration error: Target model '{target_model_name}' not found.")

        target_model_instance = self.env[target_model_name]

        # Verify the target model inherits from the expected base class
        if not isinstance(target_model_instance, AtaExchangeBaseIncomingrequest):
            _logger.error(f"Target model '{target_model_name}' does not inherit from 'ata.exchange.base.incomingrequest'.")
            raise InternalServerError(f"Configuration error: Target model '{target_model_name}' has incorrect base class for incoming requests.")

        # Call the ata_exchange_incomingrequest method on the target model instance
        try:
            # Use sudo() for potential broad access needs within the run method.
            response_data = target_model_instance.sudo().ata_exchange_incomingrequest_run(
                method=method,
                ext_system=ext_system,
                req_body=req_body
            )

            _logger.debug(f"ata_exchange_incomingrequest for method '{method.name}' executed successfully.")
            return response_data
        except AccessError as e:
             _logger.warning(f"Access Error during run for method '{method.name}': {e}")
             raise Forbidden(str(e))
        except (ValidationError, UserError) as e:
            _logger.warning(f"Validation/User Error during run for method '{method.name}': {e}")
            raise BadRequest(f"Invalid data or operation for method '{method.name}': {e}")
        except NotImplementedError: 
            _logger.error(f"Method 'ata_exchange_incomingrequest_run' not implemented in {target_model_name} for method '{method.name}'.")
            raise InternalServerError(f"Processing logic not implemented for method '{method.name}'.")
        except TypeError as e:
             if "ata_exchange_incomingrequest_run() takes" in str(e) or "positional argument but" in str(e):
                 _logger.exception(f"Signature mismatch calling {target_model_name}.ata_exchange_incomingrequest_run: {e}")
                 raise InternalServerError(f"Internal configuration error calling handler for method '{method.name}'.")
             else:
                 _logger.exception(f"Unexpected TypeError during run for method '{method.name}': {e}")
                 raise InternalServerError(f"An unexpected error occurred processing method '{method.name}'.")
        except Exception as e:
             _logger.exception(f"Unexpected error during run for method '{method.name}': {e}")
             raise InternalServerError(f"An unexpected error occurred processing method '{method.name}'.")
