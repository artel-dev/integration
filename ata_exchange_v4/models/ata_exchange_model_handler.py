from odoo import api, models, _

from .ata_exchange_model_handler_mixin import AtaExchangeModelHandlerMixin, RecordHandlerParams


class AtaExchangeModelHandler(models.AbstractModel):
    _name = "ata.exchange.model.handler"
    _description = "Exchange model handler"

    @api.model
    def model_handler(self,
        record_params: RecordHandlerParams) -> models.BaseModel:

        Model = record_params['model']
        records = self.search_records(record_params)
        if (not records and record_params['create_record']) or (records and record_params['write_record']):
            if isinstance(Model, AtaExchangeModelHandlerMixin):
                vals = Model.ata_exchange_prepare_vals(record_params)
            else:
                vals = record_params['data']
            
            if vals:
                with self.env['ata.exchange.queue'].disable_add_temporarily(not record_params['add_to_queue']):
                    if records:
                        records.write(vals)
                    else:
                        records = Model.create([vals])

                self.save_matching_data(records, record_params)
            
        return records

    @api.model
    def search_records(self,
        record_params: RecordHandlerParams) -> models.BaseModel:

        Model = record_params['model']
        records = Model.browse(None)
        search_params = record_params['search_params']
        
        if (search_domain := search_params['search_domain']):
            records = Model.search(search_domain)

        if not records and search_params['use_matching_data']:
            # get matching data
            key_matching: str = record_params['data'].get(search_params['key_matching_data'], False)
            matching_id = self.env['ata.exchange.matching.data'].get_matching_data(search_params, key_matching)
            matching_data: dict = matching_id.matching_data if matching_id else {}
            
            # search record in matching data
            search_id = matching_data.get(record_params['model_name'], False)
            records = Model.browse(search_id).exists()

        if not records and (search_domain_second := search_params['search_domain_second']):
            records = Model.search(search_domain_second)
        
        return records

    def save_matching_data(self,
        records: models.BaseModel,
        record_params: RecordHandlerParams) -> None:

        search_params = record_params['search_params']

        if search_params['use_matching_data']:
            key_object: str = record_params['data'].get(search_params['key_matching_data'], False)
            self.env['ata.exchange.matching.data'].save_matching_data(
                search_params,
                key_object,
                {records._name: records[0].id})        
