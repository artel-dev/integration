from odoo import fields, models, api

from odoo.addons.ata_exchange_v4.models.ata_exchange_base_incomingrequest_types import IncomingRequestParam

class AtaExchangeIncomingMatchingData(models.Model):
    _name = "ata.exchange.incoming.matching.data"
    _description = "Incoming matching data in Exchange (v4)"
    
    # в таблиці співставлення (зовнішні id методів обмінів + зовнішня система)
    # з внутрішніми моделями і їх id об'єктів
    
    method_id = fields.Many2one(
        comodel_name='ata.exchange.method',
        string='Method',
        required=True)
    ext_system_id = fields.Many2one(
        comodel_name='ata.exchange.system',
        string='External system')
    ext_object_id = fields.Char(
        string="ID in ext. systems",
        required=True)
    matching_data = fields.Json(
        string="Matching data",
        required=True)

    _sql_constraints = [(
        'method_ext_system_object_unique',
        'unique(method_id, ext_system_id, ext_object_id)',
        'to search for records on incoming request'
    )]

    @api.model
    def get_matching_data(self,
        params: IncomingRequestParam,
        id_object: str) -> 'AtaExchangeIncomingMatchingData':
        
        return self.search([
            ('method_id', '=', params['method'].id),
            ('ext_system_id', '=', params['ext_system'].id if params['ext_system'] else False),
            ('ext_object_id', '=', id_object)
        ], limit=1)

    @api.model
    def save_matching_data(self,
        params: IncomingRequestParam,
        id_object: str,
        add_matching_data: dict) -> None:

        matching_id = self.get_matching_data(params, id_object)
        if matching_id:
            matching_data = {
                **matching_id.matching_data,
                **add_matching_data
            }
        else:
            matching_data = add_matching_data

        vals = {
            'method_id': params['method'].id,
            'ext_system_id': params['ext_system'].id if params['ext_system'] else False,
            'ext_object_id': id_object,
            'matching_data': matching_data
        }
        
        if matching_id:
            matching_id.write(vals)
        else:
            self.create([vals])
