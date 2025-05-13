from odoo import fields, models, api

from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import AtaExchangeSystem


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
    def get_matching_data(self, method: AtaExchangeMethod, ext_system: AtaExchangeSystem | None, id_data: str) \
        -> 'AtaExchangeIncomingMatchingData':
        
        return self.search([
            ('method_id', '=', method.id),
            ('ext_system_id', '=', ext_system.id if ext_system else False),
            ('ext_object_id', '=', id_data)
        ], limit=1)

    @api.model
    def save_matching_data(self, method: AtaExchangeMethod, ext_system: AtaExchangeSystem | None, id_data: str, matching_data: dict) \
        -> 'AtaExchangeIncomingMatchingData':
        
        vals = {
            'method_id': method.id,
            'ext_system_id': ext_system.id if ext_system else False,
            'ext_object_id': id_data,
            'matching_data': matching_data
        }
        matching_data_id = self.get_matching_data(method, ext_system, id_data)
        if matching_data_id:
            matching_data_id.write(vals)
        else:
            matching_data_id = self.create([vals])

        return matching_data_id
