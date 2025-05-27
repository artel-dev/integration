from odoo import api, models, _

from .ata_exchange_base_incomingrequest_types import IncomingRequestParam
from .ata_exchange_model_handler_mixin import AtaExchangeModelHandlerMixin, RecordHandlerParams


class AtaExchangeModelHandler(models.AbstractModel):
    _name = "ata.exchange.model.handler"
    _description = "Exchange model handler"

    @api.model
    def model_handler(self,
        record_params: RecordHandlerParams,
        inc_req_params: IncomingRequestParam|None = None) -> models.BaseModel:

        Model = record_params['model']
        records = self.search_records(record_params, inc_req_params)
        if (not records and record_params['create_record']) or record_params['write_record']:
            if isinstance(Model, AtaExchangeModelHandlerMixin):
                vals = Model.ata_exchange_prepare_vals(record_params, inc_req_params)
            else:
                vals = record_params['data']
            
            if vals:
                if records:
                    records.write(vals)
                else:
                    records = Model.create([vals])

                self.save_matching_data(records, record_params, inc_req_params)
            
        return records

    @api.model
    def search_records(self,
        record_params: RecordHandlerParams,
        inc_req_params: IncomingRequestParam|None = None) -> models.BaseModel:

        Model = record_params['model']
        records = Model.browse(None)
        
        if (search_domain:=record_params['search_params']['search_domain']):
            records = Model.search(search_domain)

        if not records and inc_req_params and record_params['search_params']['use_matching_data']:
            # get matching data
            id_matching: str = inc_req_params['req_body_data'].get('id_matching', False)
            matching_id = self.env['ata.exchange.incoming.matching.data'].get_matching_data(inc_req_params, id_matching)
            matching_data: dict = matching_id.matching_data if matching_id else {}
            
            # search record in matching data
            search_id = matching_data.get(record_params['model_name'], False)
            records = Model.browse(search_id).exists()

        if not records and (search_domain_second:=record_params['search_params']['search_domain_second']):
            records = Model.search(search_domain_second)
        
        return records

    def save_matching_data(self,
        records: models.BaseModel,
        record_params: RecordHandlerParams,
        inc_req_params: IncomingRequestParam|None = None) -> None:

        if inc_req_params and record_params['search_params']['use_matching_data']:
            id_object: str = inc_req_params['req_body_data'].get('id_matching', False)
            self.env['ata.exchange.incoming.matching.data'].save_matching_data(
                inc_req_params,
                id_object,
                {records._name: records[0].id})        
