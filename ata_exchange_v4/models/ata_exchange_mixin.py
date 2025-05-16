from odoo import api, models, _

import logging

from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_base_requestdata import AtaExchangeBaseRequestdata

_logger = logging.getLogger(__name__)


class AtaExchangeMixin(models.AbstractModel):
    _name = "ata.exchange.mixin"
    _description = "Exchange mixin"

    @api.model
    def get_meta_data(self, *kwargs) -> dict:
        return {
            'meta': {
                'db_name': self._cr.dbname,
            },
        }

    def cron_exchange(self):
        #start outgoing queue
        self.env['ata.exchange.queue'].exchange()
        
        #start request_data
        methods = self.env['ata.exchange.method'].search([
            ('type', '=', 'request_data'),
            ('start_over_cron', '=', True)
        ])
        self.ata_exchange_requestdata(methods)

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
                    raise Exception(f"Method exchange '{method.name}' has a type other than 'request_data'")
            else:
                raise Exception(f"Method exchange '{method.name}' has no model_id")

    @api.model
    def ata_exchange_requestdata_action(self, methods: AtaExchangeMethod):
        try:
            self.ata_exchange_requestdata(methods)
            result_msg = _("Processing completed successfully")
            type = 'info'
        except ValueError as ve:
            _logger.warning(str(ve))
            result_msg = f"ValueError: {str(ve)}"
            type = 'warning'
        except Exception as ex:
            _logger.warning(str(ex))
            result_msg = str(ex)
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