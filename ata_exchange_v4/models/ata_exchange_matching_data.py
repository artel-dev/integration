from odoo import api, fields, models

from .ata_exchange_model_handler_mixin import RecordHandlerParams, SearchRecordHandlerParams
from .ata_exchange_base_incomingrequest_types import IncomingResponseParamMatching

class AtaExchangeIncomingMatchingData(models.Model):
    _name = "ata.exchange.matching.data"
    _description = "Matching data in Exchange (v4)"
    
    # в таблиці співставлення (зовнішні id методів обмінів + зовнішня система)
    # з внутрішніми моделями і їх id об'єктів
    
    method_id = fields.Many2one(
        comodel_name='ata.exchange.method',
        string='Method',
        required=True,
        ondelete='cascade')
    ext_system_id = fields.Many2one(
        comodel_name='ata.exchange.system',
        string='External system',
        required=True,
        ondelete='cascade')
    key_object = fields.Char(
        string="Key (ID) of object",
        required=True)
    stage = fields.Char(
        string="Stage")
    matching_data = fields.Json(
        string="Matching data",
        required=True)

    _sql_constraints = [(
        'method_ext_system_object_stage_unique',
        'unique(method_id, stage, ext_system_id, key_object)',
        'to search for records on incoming request'
    )]

    @api.model
    def get_matching_data(self,
        params: SearchRecordHandlerParams,
        key_matching: str) -> 'AtaExchangeIncomingMatchingData | None':
        
        if params.ext_system_id and params.method_id:
            return self.search([
                ('ext_system_id', '=', params.ext_system_id.id),
                ('method_id', '=', params.method_id.id),            
                ('key_object', '=', key_matching),
                ('stage', '=', params.stage)
            ], limit=1)
        else:
            return None

    @api.model
    def save_matching_data(self,
        record_params: RecordHandlerParams,
        key_object: str,
        records: models.BaseModel) -> IncomingResponseParamMatching|None:

        search_params = record_params.search_params
        add_matching_data = {records._name: records[0].id}

        if (method_id := search_params.method_id) and (ext_system_id := search_params.ext_system_id):
            matching_id = self.get_matching_data(search_params, key_object)
            if matching_id:
                matching_data = {
                    **matching_id.matching_data,
                    **add_matching_data
                }
            else:
                matching_data = add_matching_data

            vals = {
                'method_id': method_id.id,
                'ext_system_id': ext_system_id.id,
                'key_object': key_object,
                'stage': search_params.stage,
                'matching_data': matching_data
            }
            
            if matching_id:
                matching_id.write(vals)
            else:
                matching_id = self.create([vals])

            return IncomingResponseParamMatching(
                method = search_params.method_id,
                id_ext = key_object,
                model_name = records._name,
                model_id = records[0].id
            )

            # need to be commit, because after write we need will use new record of matching data
            # self.env.cr.commit()
