from dataclasses import dataclass, field, asdict

from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import AtaExchangeSystem
from typing import Any


@dataclass
class IncomingParam:
    method_id: AtaExchangeMethod
    ext_system_id: AtaExchangeSystem | None

    @classmethod
    def build(cls, source: Any) -> 'IncomingParam | None':
        if not source:
            return None

        if type(source) is cls:
            return source

        base_keys = cls.__annotations__.keys()
        source_data = asdict(source)
        filtered_data = {k: v for k, v in source_data.items() if k in base_keys}
        return cls(**filtered_data)


@dataclass
class IncomingRequestParam(IncomingParam):
    req_body: dict
    req_body_data: dict

@dataclass
class IncomingResponseParamMatching:
    method: AtaExchangeMethod | None
    id_ext: int|str
    model_name: str
    model_id: int

    def get_data_json(self) -> dict|list[dict]:
        return {
            "method": self.method.name if self.method else '',
            "id_ext": self.id_ext,
            "model_name": self.model_name,
            "model_id": self.model_id
        }

@dataclass
class IncomingResponseParam:
    data: dict|list[dict] = field(default_factory=dict)
    matching_data: list[IncomingResponseParamMatching] = field(default_factory=list)
    error: list[str] = field(default_factory=list)

    @property
    def has_error(self) -> bool:
        return bool(self.error)

    def get_data_json(self) -> dict|list[dict]:
        return {
            "data": self.data,
            "matching_data": [md.get_data_json() for md in self.matching_data],
        }
