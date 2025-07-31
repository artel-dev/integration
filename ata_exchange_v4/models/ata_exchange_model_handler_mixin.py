from odoo import api, models
from odoo.exceptions import UserError, ValidationError

from typing import TypedDict, Any
from pydantic import BaseModel as BaseModelPydantic, ValidationError as ValidationErrorPydantic

from .ata_exchange_base_incomingrequest_types import IncomingRequestParam
from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import AtaExchangeSystem


class SearchRecordHandlerParams(TypedDict):
    search_domain: list[tuple[str, str, Any]] | None  # domain for primary search record
    search_domain_second: list[tuple[str, str, Any]] | None  # domain for secondary search record (after matching)
    use_matching_data: bool  # use matching data for save pointer for record from external systems
    key_matching_data: str  # field of object data for search matching data ('id_matching' by default)
    ext_system_id: AtaExchangeSystem | None  # external system for search record
    method_id: AtaExchangeMethod | None  # method for search record    


class RecordHandlerParams(TypedDict):
    data: dict
    model_name: str
    model: models.BaseModel
    create_record: bool                     # create record if not found
    write_record: bool                      # write data in record if found
    search_params: SearchRecordHandlerParams


class RecordHandlerResult(TypedDict):
    record: models.Model | None
    error: str | None


class AtaExchangeModelHandlerMixin(models.AbstractModel):
    _name = "ata.exchange.model.handler.mixin"
    _description = "Exchange model handler methods"

    @api.model
    def ata_exchange_get_default_record_handler_params(self,
        model_name: str,
        inc_req_params: IncomingRequestParam|None = None) -> RecordHandlerParams:

        return {
            'data': {},
            'model_name': model_name,
            'model': self.env[model_name],
            'create_record': False,
            'write_record': False,
            'search_params': {
                'search_domain': None,
                'search_domain_second': None,
                'use_matching_data': False,
                'key_matching_data': 'id_matching',
                'ext_system_id': inc_req_params['ext_system_id'] if inc_req_params else None,
                'method_id': inc_req_params['method_id'] if inc_req_params else None
            }
        }

    @api.model
    def ata_exchange_get_model_record(self,        
        record_params: RecordHandlerParams) -> models.BaseModel:

        records = self.env['ata.exchange.model.handler'].model_handler(record_params)

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
            error_message = f"Validation error data for sale.order: {str(e)}"
            raise ValidationError(error_message) from e

    @api.model
    def ata_exchange_check_record_params(self, record_params: RecordHandlerParams):
        return True

    @api.model
    def ata_exchange_prepare_vals(self,
        record_params: RecordHandlerParams) -> dict:

        return {}
