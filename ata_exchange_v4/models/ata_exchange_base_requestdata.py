from odoo import models, api, _

from abc import abstractmethod
import logging

from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import AtaExchangeSystem

_logger = logging.getLogger(__name__)


class AtaExchangeBaseRequestdata(models.AbstractModel):
    _name = "ata.exchange.base.requestdata"
    _description = "Request data base model"

    @abstractmethod
    def ata_exchange_requestdata_run(self, methods: AtaExchangeMethod, ext_system: AtaExchangeSystem):
        pass

    def ata_exchange_requestdata(self, methods: AtaExchangeMethod):
        for method in methods:
            if method.model_id:
                model_handler = self.env[method.model_id.model] # type: ignore
                if isinstance(model_handler, AtaExchangeBaseRequestdata):
                    # get ext.systems for request
                    ext_systems = self.env["ata.exchange.domain"].get_ext_systems(None, method)
                    for ext_system in ext_systems:
                        model_handler.ata_exchange_requestdata_run(method, ext_system)
            else:
                _logger.exception(f"Method {method.name} has no model_id")

    @api.model
    def ata_exchange_requestdata_action(self, methods: AtaExchangeMethod):
        try:
            self.ata_exchange_requestdata(methods)
            result_msg = _("Processing completed successfully")
            type = 'info'
        except ValueError as ve:
            result_msg = f"ValueError: {str(ve)}"
            type = 'warning'
        except Exception as ex:
            result_msg = f"Error: {str(ex)}"
            type = 'warning'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Execution result'),
                'type': type,
                'message': result_msg,
                'sticky': False
            }
        }

    