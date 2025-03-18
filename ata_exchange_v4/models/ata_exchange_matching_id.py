from odoo import fields, models, api

from .ata_exchange_handler import AtaExchangeHandler as Handler
from odoo.addons.product.models.product_product import ProductProduct as Product


class AtaExchangeMatchingId(models.Model):
    _name = "ata.exchange.matching.id"
    _description = "Id matching in Exchange (v3)"
    
    # в таблиці співставлення (зовнішні id методів обмінів + зовнішня система)
    # з внутрішніми моделями і їх id об'єктів
    # при цьому внітрішні id носять допоміжний характер і можуть бути віртуальними об'єктами
    # або просто унікальними номерами (тому не використовую .Reference())

    method_id = fields.Many2one(
        comodel_name='ata.exchange.method',
        string='Method',
        required=True)
    ext_system_id = fields.Many2one(
        comodel_name='ata.exchange.system',
        string='External system',
        required=True)
    ext_object_id = fields.Char(
        string="ID in ext. systems",
        required=True)
    object_id = fields.Integer(
        string="Record ID",)
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string="Model",)

    _sql_constraints = [(
            'method_ext_system_object_unique',
            'unique(method_id, ext_system_id, ext_object_id)',
            'to search for records on incoming request'
        )]

    def _auto_init(self):
        super()._auto_init()
        self.env.cr.execute("""
            CREATE INDEX IF NOT EXISTS ata_exchange_matching_id_model_object_idx
            ON ata_exchange_matching_id(model_id,object_id);
        """)

    @api.model
    def create_from_handler(self, handler: Handler, external_id: str, product: Product):
        self.create([{
            'method_id': handler.method_id.id,
            'ext_system_id': handler.ext_system_id.id,
            'ext_object_id': external_id,
            'model_id': self.env['ir.model'].search([('model', '=', product._name)], limit=1).id,
            'object_id': product.id,
        }])
