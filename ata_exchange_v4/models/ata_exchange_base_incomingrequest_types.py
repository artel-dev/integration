from typing import TypedDict, Optional

from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import AtaExchangeSystem


class IncomingRequestParam(TypedDict):
    method_id: AtaExchangeMethod
    ext_system_id: Optional[AtaExchangeSystem]
    req_body: dict
    req_body_data: dict
