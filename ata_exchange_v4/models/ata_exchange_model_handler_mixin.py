from odoo import api, models

from typing import TypedDict, Any

from .ata_exchange_base_incomingrequest_types import IncomingRequestParam


class RecordHandlerParams(TypedDict):
    incoming_request_params: IncomingRequestParam
    data: dict
    model: str | None
    create_record: bool                     # create record if not found
    write_record: bool                      # write data in record if found
    use_matching_data: bool                 # use matching data for save pointer for record from external systems
    search_domain: list[tuple[str, str, Any]] | None  # domain for primary search record
    search_domain_second: list[tuple[str, str, Any]] | None  # domain for secondary search record (after matching)
    

class RecordHandlerResult(TypedDict):
    record: models.Model | None
    error: str | None


class AtaExchangeModelHandlerMixin(models.AbstractModel):
    _name = "ata.exchange.model.handler.mixin"
    _description = "Exchange model handler methods"

    @api.model
    def ata_exchange_get_default_record_handler_params(self,
        incoming_request_params: IncomingRequestParam,
        data: dict = {}) -> RecordHandlerParams:

        return {
            'incoming_request_params': incoming_request_params,
            'data': data,
            'model': None,
            'create_record': True,
            'write_record': False,
            'use_matching_data': False,
            'search_domain': None,
            'search_domain_second': None,
        }

    def ata_exchange_get_clone_record_handler_params(self,
        params: RecordHandlerParams,
        data: dict = {}) -> RecordHandlerParams:
        
        return self.ata_exchange_get_default_record_handler_params(
            incoming_request_params=params['incoming_request_params'],
            data=data,
        )

    @api.model
    def ata_exchange_get_model_record(self, params: RecordHandlerParams) -> models.BaseModel:
        records = self.env['ata.exchange.model.handler'].model_handler(params)
        return next(iter(records), records)

    @api.model
    def ata_exchange_prepare_vals(self, params: RecordHandlerParams) -> dict:
        return {}