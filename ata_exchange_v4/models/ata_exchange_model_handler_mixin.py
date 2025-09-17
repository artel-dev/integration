from odoo import api, models
from odoo.exceptions import UserError, ValidationError

from dataclasses import dataclass, field
from typing import Any
from pydantic import BaseModel as BaseModelPydantic, ValidationError as ValidationErrorPydantic

from .ata_exchange_base_incomingrequest_types import (
    IncomingParam, IncomingResponseParam
)
from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import AtaExchangeSystem


@dataclass
class SearchRecordHandlerParams:
    search_ref: str | None = None  # search record by XML ID
    search_domain: list[tuple[str, str, Any]] | None = None  # domain for primary search record
    search_domain_second: list[tuple[str, str, Any]] | None = None  # domain for secondary search record (after matching)
    use_matching_data: bool = False  # use matching data for save pointer for record from external systems
    key_matching_data: str = 'id_matching'  # field of object data for search matching data ('id_matching' by default)
    ext_system_id: AtaExchangeSystem | None = None  # external system for search record
    method_id: AtaExchangeMethod | None = None  # method for search record

    @classmethod
    def build(cls, inc_params: IncomingParam | None = None) -> 'SearchRecordHandlerParams':
        return cls(
            ext_system_id = inc_params.ext_system_id if inc_params else None,
            method_id     = inc_params.method_id if inc_params else None
        )

@dataclass
class RecordHandlerParams:
    model: models.BaseModel
    model_name: str
    data: dict = field(default_factory=dict)
    search_params: SearchRecordHandlerParams = field(default_factory=SearchRecordHandlerParams)
    incoming_params: IncomingParam | None = None
    response_data: IncomingResponseParam = field(default_factory=IncomingResponseParam)
    create_record: bool = False # create record if not found
    write_record: bool = False  # write data in record if found
    add_to_queue: bool = False  # add record to queue exchange to ext. system

    @classmethod
    def build_from_class(cls, env, model_name: str, inc_params: IncomingParam|None = None) -> 'RecordHandlerParams':
        """Create a new instance directly from the class.
        Args:
            env: Odoo environment
            model_name: Name of the model
            inc_params: Incoming parameters for the exchange
        Returns:
            A new instance of RecordHandlerParams
        """
        return cls._build_params(env, model_name,
            IncomingParam.build(inc_params),
            SearchRecordHandlerParams.build(inc_params))

    def build(self, env, model_name: str, method: AtaExchangeMethod|None = None) -> 'RecordHandlerParams':
        """Build a new instance based on current instance with optional method override.
        Args:
            env: Odoo environment
            model_name: Name of the model
            method: Optional exchange method to override
        Returns:
            A new instance of RecordHandlerParams
        """
        final_inc_params = IncomingParam(
            method_id = method,
            ext_system_id = self.incoming_params.ext_system_id if self.incoming_params else None
        ) if method else self.incoming_params
        
        return RecordHandlerParams._build_params(env, model_name,
            final_inc_params,
            SearchRecordHandlerParams.build(final_inc_params),
            self.response_data)

    @staticmethod
    def _build_params(env, model_name: str,
        incoming_params: IncomingParam|None,
        search_params: SearchRecordHandlerParams,
        response_data: IncomingResponseParam|None = None) -> 'RecordHandlerParams':
        
        return RecordHandlerParams(
            model           = env[model_name],
            model_name      = model_name,
            incoming_params = incoming_params,
            search_params   = search_params,
            response_data   = response_data if response_data else IncomingResponseParam()
        )
 

class AtaExchangeModelHandlerMixin(models.AbstractModel):
    _name = "ata.exchange.model.handler.mixin"
    _description = "Exchange model handler methods"

    @api.model
    def ata_exchange_get_model_record(self,
        record_params: RecordHandlerParams,
        only_search: bool = False) -> models.BaseModel:

        self.ata_exchange_check_record_params(record_params)
        if only_search:
            records = self.env['ata.exchange.model.handler'].search_records(record_params)
        else:
            records = self.env['ata.exchange.model.handler'].get_records(record_params)
        
        return next(iter(records), records)

    @api.model
    def ata_exchange_get_settings(self, param_name: str, block: str, Model: models.BaseModel) -> models.BaseModel:
        if not (sett_id:=self.env['ir.config_parameter'].get_param(param_name)):
            raise UserError(f"Setting '{param_name}' in {block} is not defined")
        else:
            return Model.browse(int(sett_id))

    def ata_exchange_process_data_with_pydantic(self, data: dict, pydantic_model: type[BaseModelPydantic]) -> BaseModelPydantic:
        try:
            return pydantic_model(**data)
        except ValidationErrorPydantic as e:
            error_message = f"Validation error data: {str(e)}"
            raise ValidationError(error_message) from e

    @api.model
    def ata_exchange_check_record_params(self, record_params: RecordHandlerParams):
        return True

    @api.model
    def ata_exchange_prepare_vals(self, record_params: RecordHandlerParams) -> dict:
        return record_params.data

    @api.model
    def ata_exchange_after_write(self, record_params: RecordHandlerParams):
        pass