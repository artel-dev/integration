from odoo import fields, models, api

from .ata_exchange_model_handler_mixin import SearchRecordHandlerParams

class AtaExchangeIncomingMatchingData(models.Model):
    _name = "ata.exchange.matching.data"
    _description = "Matching data in Exchange (v4)"
    
    # в таблиці співставлення (зовнішні id методів обмінів + зовнішня система)
    # з внутрішніми моделями і їх id об'єктів
    
    method_id = fields.Many2one(
        comodel_name='ata.exchange.method',
        string='Method',
        required=True)
    ext_system_id = fields.Many2one(
        comodel_name='ata.exchange.system',
        string='External system',
        required=True)
    key_object = fields.Char(
        string="Key (ID) of object",
        required=True)
    matching_data = fields.Json(
        string="Matching data",
        required=True)

    _sql_constraints = [(
        'method_ext_system_object_unique',
        'unique(method_id, ext_system_id, key_object)',
        'to search for records on incoming request'
    )]

    @api.model
    def get_matching_data(self,
        params: SearchRecordHandlerParams,
        key_matching: str) -> 'AtaExchangeIncomingMatchingData | None':
        
        if params['ext_system_id'] and params['method_id']:
            return self.search([
                ('ext_system_id', '=', params['ext_system_id'].id),
                ('method_id', '=', params['method_id'].id),            
                ('key_object', '=', key_matching)
            ], limit=1)
        else:
            return None

    @api.model
    def save_matching_data(self,
        params: SearchRecordHandlerParams,
        key_object: str,
        add_matching_data: dict) -> None:

        if (method_id := params['method_id']) and (ext_system_id := params['ext_system_id']):
            matching_id = self.get_matching_data(params, key_object)
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
                'matching_data': matching_data
            }
            
            if matching_id:
                matching_id.write(vals)
            else:
                self.create([vals])
