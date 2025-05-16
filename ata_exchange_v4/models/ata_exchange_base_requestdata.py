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
    