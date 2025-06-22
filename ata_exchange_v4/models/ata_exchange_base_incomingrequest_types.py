from typing import TypedDict, Optional

from .ata_exchange_method import AtaExchangeMethod
from odoo.addons.ata_exchange_v4.models.ata_exchange_system import AtaExchangeSystem


class IncomingRequestParam(TypedDict):
    method: AtaExchangeMethod
    ext_system: Optional[AtaExchangeSystem]
    req_body: dict
    req_body_data: dict
