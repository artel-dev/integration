from odoo import models
from .ata_exchange_base_incomingrequest_types import IncomingRequestParam, IncomingResponseParam


class AtaExchangeBaseIncomingrequest(models.AbstractModel):
    """
    Abstract base model for handling incoming API requests.
    Specific handlers for different incoming methods should inherit from this class.
    """
    _name = "ata.exchange.base.incomingrequest"
    _description = "Base Model for Incoming API Request Handlers"

    # override
    def ata_exchange_incomingrequest_run(self, params: IncomingRequestParam) -> IncomingResponseParam:
        """
        Abstract method to be implemented by specific incoming request handlers.
        Processes the data received in an incoming API request.

        :param params: A TypedDict containing the necessary parameters:
                       - method: The 'ata.exchange.method' record.
                       - ext_system: The 'ata.exchange.system' record (can be None).
                       - req_body: The parsed JSON body of the incoming request.
        :return: A dictionary representing the JSON response body.
        """
        error_msg = ['Not implemented incoming request handlers'] \
            if self._name == 'ata.exchange.base.incomingrequest' else []
        
        return IncomingResponseParam(error=error_msg)
