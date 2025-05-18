from odoo import api, models, _

from .ata_exchange_base_incomingrequest_types import IncomingRequestParam
from .ata_exchange_model_handler_mixin import AtaExchangeModelHandlerMixin, RecordHandlerParams


class AtaExchangeModelHandler(models.AbstractModel):
    _name = "ata.exchange.model.handler"
    _description = "Exchange model handler"

    @api.model
    def model_handler(self, params: RecordHandlerParams) -> models.BaseModel:
        if params['model']:
            Model = self.env[params['model']]
            
            records = self.search_records(params, Model)
            if (not records and params['create_record']) or params['write_record']:
                if isinstance(Model, AtaExchangeModelHandlerMixin):
                    vals = Model.ata_exchange_prepare_vals(params)
                
                    if records:
                        records.write(vals)
                    else:
                        records = Model.create([vals])

                    self.save_matching_data(params, records)
                else:
                    raise ValueError("Model is not instance of AtaExchangeModelHandlerMixin")

            return records
        else:
            raise ValueError("Data or model name is undefined")

    @api.model
    def search_records(self, params: RecordHandlerParams, Model: models.BaseModel) -> models.BaseModel:
        records = Model.browse(None)
        
        if params['search_domain']:
            records = Model.search(params['search_domain'])

        if not records and params['use_matching_data']:
            # get matching data
            id_object: str = params['incoming_request_params']['req_body_data'].get('id', False)
            matching_id = self.env['ata.exchange.incoming.matching.data'].get_matching_data(params['incoming_request_params'], id_object)
            matching_data: dict = matching_id.matching_data if matching_id else {}
            
            # search record in matching data
            search_id = matching_data.get(Model._name, False)
            records = Model.browse(search_id)

        if not records and params['search_domain_second']:
            records = Model.search(params['search_domain_second'])
        
        return records

    def save_matching_data(self, params: RecordHandlerParams, records: models.BaseModel) -> None:
        if params['use_matching_data']:
            id_object: str = params['incoming_request_params']['req_body_data'].get('id', False)
            self.env['ata.exchange.incoming.matching.data'].save_matching_data(
                params['incoming_request_params'],
                id_object,
                {records._name: records[0].id})        
