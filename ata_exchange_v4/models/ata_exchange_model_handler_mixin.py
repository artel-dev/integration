from odoo import api, models
from odoo.exceptions import UserError, ValidationError

from typing import TypedDict, Any
from pydantic import BaseModel as BaseModelPydantic, ValidationError as ValidationErrorPydantic

from .ata_exchange_base_incomingrequest_types import IncomingRequestParam


class SearchRecordHandlerParams(TypedDict):
    search_domain: list[tuple[str, str, Any]] | None  # domain for primary search record
    search_domain_second: list[tuple[str, str, Any]] | None  # domain for secondary search record (after matching)
    use_matching_data: bool  # use matching data for save pointer for record from external systems
    matching_id: str | None


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
        model_name: str) -> RecordHandlerParams:

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
                'matching_id': None
            }
        }

    @api.model
    def ata_exchange_get_model_record(self,        
        record_params: RecordHandlerParams,
        inc_req_params: IncomingRequestParam|None = None) -> models.BaseModel:

        records = self.env['ata.exchange.model.handler'].model_handler(record_params, inc_req_params)

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
    def ata_exchange_prepare_vals(self,
        record_params: RecordHandlerParams,
        inc_req_params: IncomingRequestParam|None = None) -> dict:

        return {}
