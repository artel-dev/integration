# /home/gnezamay/odoo/odoo-18.0-ee/custom_addons_cons/ata_exchange_v4/models/ata_exchange_base_incomingrequest.py
from odoo import models
from abc import abstractmethod
import logging

# Import necessary types
from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import AtaExchangeSystem

_logger = logging.getLogger(__name__)

class AtaExchangeBaseIncomingrequest(models.AbstractModel):
    """
    Abstract base model for handling incoming API requests.
    Specific handlers for different incoming methods should inherit from this class.
    """
    _name = "ata.exchange.base.incomingrequest"
    _description = "Base Model for Incoming API Request Handlers"

    @abstractmethod
    def ata_exchange_incomingrequest_run(
            self, method: AtaExchangeMethod,
            ext_system: AtaExchangeSystem | None,
            req_body: dict) -> dict:
        """
        Abstract method to be implemented by specific incoming request handlers.
        Processes the data received in an incoming API request.

        :param method: The ata.exchange.method record that triggered this handler.
        :param ext_system: The ata.exchange.system record identified by the API key (or None).
        :param req_body: The parsed JSON body of the incoming request.
        :return: A dictionary representing the JSON response body.
        :raises: Implementation specific exceptions (e.g., ValidationError, UserError, werkzeug exceptions).
        """
        _logger.warning(f"Abstract method 'ata_exchange_incomingrequest_run' called for model {self._name}. Implementation missing.")
        raise NotImplementedError("Specific handlers must implement 'ata_exchange_incomingrequest_run'.")
