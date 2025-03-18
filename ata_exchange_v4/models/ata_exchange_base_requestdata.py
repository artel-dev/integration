from odoo import api, models, fields, Command

from abc import abstractmethod
from typing import Type, Dict, Any, Optional
import types
import logging

from pydantic import BaseModel, ValidationError

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
                model_handler = self.env[method.model_id.model]
                if isinstance(model_handler, AtaExchangeBaseRequestdata):
                    #get ext.systems for request
                    ext_systems = self.env["ata.exchange.domain"].get_ext_systems(None, method)
                    for ext_system in ext_systems:
                        model_handler.ata_exchange_requestdata_run(method, ext_system)
            else:
                _logger.exception(f"Method {method.name} has no model_id")
